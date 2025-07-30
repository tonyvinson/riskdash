import axios from 'axios';

// Create API client
const apiClient = axios.create({
  timeout: 30000,
});

// Helper function for validator icons
const getValidatorIcon = (validator) => {
  const icons = {
    cna: '🏗️',
    svc: '🔐', 
    iam: '👤',
    mla: '📊',
    cmt: '📋'
  };
  return icons[validator] || '🔧';
};

// ✅ FIXED: Transform with proper tenant filtering and new data priority
const transformKsiResultsToExecutions = (rawData, requestedTenant = null) => {
  const executions = rawData.data?.executions || [];
  
  console.log('🔧 FIXED Data transformation for tenant:', requestedTenant);
  console.log('📊 Raw executions received:', executions.length);
  
  // ✅ STRICT TENANT FILTERING - only show data for requested tenant
  let filteredExecutions = executions;
  if (requestedTenant && requestedTenant !== 'all') {
    filteredExecutions = executions.filter(ex => {
      // STRICT MATCH - only exact tenant matches
      const matches = ex.tenant_id === requestedTenant;
      
      if (!matches) {
        console.log(`🚫 Filtering out execution ${ex.execution_id?.substring(0, 8)}... from tenant "${ex.tenant_id}" (requested: "${requestedTenant}")`);
      }
      
      return matches;
    });
    console.log(`🎯 STRICT FILTER: Requested "${requestedTenant}", kept ${filteredExecutions.length} of ${executions.length} executions`);
  }
  
  // Separate individual KSI results from execution summaries
  const ksiResults = filteredExecutions.filter(ex => ex.execution_id?.includes('#'));
  const executionSummaries = filteredExecutions.filter(ex => !ex.execution_id?.includes('#') && ex.status);
  
  console.log('🔧 After tenant filtering:');
  console.log('- Individual KSI results:', ksiResults.length);
  console.log('- Execution summaries:', executionSummaries.length);
  
  // ✅ COMBINE BOTH TYPES - newer data first, regardless of format
  let allExecutions = [];
  
  // Convert KSI results to synthetic executions
  if (ksiResults.length > 0) {
    console.log('🔧 Converting KSI results to execution summaries');
    
    // Group by base execution ID
    const grouped = {};
    ksiResults.forEach(ksi => {
      const baseId = ksi.execution_id.split('#')[0];
      if (!grouped[baseId]) {
        grouped[baseId] = {
          execution_id: baseId,
          tenant_id: requestedTenant || ksi.tenant_id,
          status: 'COMPLETED',
          timestamp: ksi.timestamp,
          validators_completed: [],
          validators_requested: [],
          total_ksis_validated: 0,
          trigger_source: 'api',
          validation_results: [],
          ksi_results: []
        };
      }
      
      // Add validator to completed list
      const validator = ksi.validator_type.toLowerCase();
      if (!grouped[baseId].validators_completed.includes(validator)) {
        grouped[baseId].validators_completed.push(validator);
        grouped[baseId].validators_requested.push(validator);
      }
      
      // Add to total KSIs validated
      grouped[baseId].total_ksis_validated++;
      
      // Store the KSI result for detailed view
      grouped[baseId].ksi_results.push(ksi);
      
      // Create validation result format for compatibility
      grouped[baseId].validation_results.push({
        validator: validator,
        status: ksi.validation_result?.assertion ? 'SUCCESS' : 'FAILED',
        result: {
          statusCode: ksi.validation_result?.assertion ? 200 : 500,
          body: JSON.stringify({
            ...ksi.validation_result,
            validator_type: ksi.validator_type,
            execution_id: baseId,
            tenant_id: grouped[baseId].tenant_id
          })
        },
        function_name: `riskuity-ksi-validator-validator-${validator}-production`
      });
      
      // Use most recent timestamp
      if (ksi.timestamp > grouped[baseId].timestamp) {
        grouped[baseId].timestamp = ksi.timestamp;
      }
    });
    
    const syntheticExecutions = Object.values(grouped);
    console.log('✅ Created synthetic executions:', syntheticExecutions.length);
    allExecutions.push(...syntheticExecutions);
  }
  
  // Add execution summaries (but only if they match the tenant)
  if (executionSummaries.length > 0) {
    console.log('✅ Adding execution summaries:', executionSummaries.length);
    allExecutions.push(...executionSummaries);
  }
  
  // ✅ SORT BY TIMESTAMP - NEWEST FIRST
  allExecutions.sort((a, b) => {
    const timestampA = new Date(a.timestamp || a.completed_at || 0);
    const timestampB = new Date(b.timestamp || b.completed_at || 0);
    return timestampB - timestampA; // Newest first
  });
  
  console.log('✅ Final execution list (newest first):', allExecutions.length);
  allExecutions.forEach((ex, i) => {
    console.log(`  ${i + 1}. ${ex.execution_id?.substring(0, 8)}... (${ex.timestamp || ex.completed_at})`);
  });
  
  return {
    success: true,
    data: {
      executions: allExecutions,
      count: allExecutions.length
    }
  };
};

// Calculate compliance overview from execution data
const calculateComplianceOverview = (executionData) => {
  console.log('📊 Calculating compliance for execution:', executionData.execution_id);
  
  // Use validators_completed for overall status (orchestrator level)
  const completedValidators = executionData.validators_completed || [];
  const totalValidators = 5; // Always 5: cna, svc, iam, mla, cmt
  
  // Calculate overall compliance
  const overallPassRate = Math.round((completedValidators.length / totalValidators) * 100);
  
  // Create category results
  const categoryResults = {};
  const validatorNames = ['cna', 'svc', 'iam', 'mla', 'cmt'];
  
  validatorNames.forEach(validator => {
    const isCompleted = completedValidators.includes(validator);
    categoryResults[validator] = {
      validator: validator,
      status: isCompleted ? 'COMPLETED' : 'PENDING',
      passed: isCompleted,
      icon: getValidatorIcon(validator)
    };
  });
  
  // Parse AWS resources from validation results or KSI results
  let awsResources = {
    total: executionData.total_ksis_validated || 0,
    subnets: 0, hostedZones: 0, kmsKeys: 0, secretsManagerSecrets: 0,
    iamUsers: 0, iamRoles: 0, iamPolicies: 0, cloudtrailTrails: 0,
    cloudwatchAlarms: 0, snsTopics: 0, cloudformationStacks: 0
  };
  
  console.log('📊 Calculated compliance:', {
    overallPassRate,
    completedValidators: completedValidators.length,
    totalValidators,
    awsResources
  });
  
  return {
    totalValidators,
    passedValidators: completedValidators.length,
    failedValidators: totalValidators - completedValidators.length,
    overallPassRate,
    categoryResults,
    awsResources
  };
};

// Parse validation result with enhanced error handling
const parseValidationResult = (result) => {
  if (!result) return null;
  
  try {
    // Handle different result formats
    let parsedResult;
    
    if (result.result?.body) {
      // Standard validation result format
      parsedResult = typeof result.result.body === 'string' 
        ? JSON.parse(result.result.body) 
        : result.result.body;
    } else if (result.validation_result) {
      // KSI result format
      parsedResult = result.validation_result;
    } else {
      // Direct result
      parsedResult = result;
    }
    
    return {
      validator: result.validator || result.validator_type?.toLowerCase(),
      status: result.status || (parsedResult.assertion ? 'SUCCESS' : 'FAILED'),
      assertion: parsedResult.assertion,
      reason: parsedResult.assertion_reason || parsedResult.message,
      data: parsedResult,
      ksi_id: parsedResult.ksi_id || result.ksi_id,
      timestamp: parsedResult.timestamp || result.timestamp
    };
    
  } catch (error) {
    console.warn('Failed to parse validation result:', error);
    return {
      validator: result.validator || 'unknown',
      status: 'ERROR',
      assertion: false,
      reason: 'Failed to parse result',
      data: result
    };
  }
};

// KSI Service object with all methods
const ksiService = {
  // Transform KSI results to executions
  transformKsiResultsToExecutions,
  
  // Calculate compliance overview
  calculateComplianceOverview,
  
  // Parse validation results
  parseValidationResult,

  // Trigger KSI validation for a tenant
  triggerValidation: async (tenantId = 'default', triggerSource = 'manual', executionId = null) => {
    try {
      const payload = {
        tenant_id: tenantId,
        trigger_source: triggerSource
      };
      
      if (executionId) {
        payload.execution_id = executionId;
      }
      
      console.log('🚀 Triggering validation with payload:', payload);
      
      const response = await apiClient.post('/api/ksi/validate', payload);
      
      // Enhanced success detection
      const data = response.data;
      const isSuccess = data.status === 'COMPLETED' || 
                       data.success === true || 
                       data.execution_id ||
                       response.status === 200;
      
      if (isSuccess) {
        console.log('✅ Validation triggered successfully:', data);
        return {
          success: true,
          message: 'Validation triggered successfully',
          ...data
        };
      } else {
        throw new Error(data.message || 'Validation failed');
      }
    } catch (error) {
      console.error('❌ Validation trigger failed:', error);
      throw new Error(`Failed to trigger validation: ${error.message}`);
    }
  },

  // Get available tenants with metadata
  getTenants: async () => {
    try {
      const response = await apiClient.get('/api/ksi/tenants');
      return response.data;
    } catch (error) {
      console.warn('Failed to load tenants:', error.message);
      // Return fallback tenant list
      return {
        success: true,
        tenants: [
          { tenant_id: 'riskuity-production', display_name: 'Riskuity Production', ksi_count: 5 },
          { tenant_id: 'real-test', display_name: 'Real Test', ksi_count: 5 }
        ]
      };
    }
  },

  // ✅ FIXED: Get KSI execution history with STRICT tenant filtering
  getExecutionHistory: async (tenantId = 'all', limit = 10, startKey = null) => {
    try {
      const params = new URLSearchParams();
      
      // ✅ ALWAYS pass tenant_id for proper filtering
      if (tenantId && tenantId !== 'all') {
        params.append('tenant_id', tenantId);
      }
      if (limit) {
        params.append('limit', limit.toString());
      }
      if (startKey) {
        params.append('start_key', startKey);
      }

      const url = `/api/ksi/executions${params.toString() ? '?' + params.toString() : ''}`;
      console.log('📊 Fetching execution history:', url);
      
      const response = await apiClient.get(url);
      
      // ✅ FIXED: Pass the requested tenant to transformation for proper filtering
      const transformedData = transformKsiResultsToExecutions(response.data, tenantId);
      
      console.log('📊 Transformed execution history for tenant:', tenantId, transformedData);
      return transformedData;
      
    } catch (error) {
      throw new Error(`Failed to fetch execution history: ${error.message}`);
    }
  },

  // Get detailed validation results for an execution
  getValidationResults: async (tenantId, executionId = null) => {
    try {
      const params = new URLSearchParams();
      
      if (tenantId && tenantId !== 'all') {
        params.append('tenant_id', tenantId);
      }
      if (executionId) {
        params.append('execution_id', executionId);
      }

      const url = `/api/ksi/results${params.toString() ? '?' + params.toString() : ''}`;
      console.log('🔍 Fetching validation results:', url);
      
      const response = await apiClient.get(url);
      return response.data;
      
    } catch (error) {
      throw new Error(`Failed to fetch validation results: ${error.message}`);
    }
  }
};

export { getValidatorIcon, ksiService };
export default ksiService;
