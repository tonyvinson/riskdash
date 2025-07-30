import axios from 'axios';

// Create API client
const apiClient = axios.create({
  baseURL: process.env.NODE_ENV === 'production' ? process.env.REACT_APP_API_URL : '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request/response interceptors for debugging
apiClient.interceptors.request.use(request => {
  console.log('🌐 API Request:', request.method?.toUpperCase(), request.url);
  return request;
});

apiClient.interceptors.response.use(response => {
  console.log('🌐 API Response:', response.status, response.config.url);
  return response;
}, error => {
  console.error('🌐 API Error:', error.response?.status, error.config?.url, error.message);
  return Promise.reject(error);
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

// ✅ COMPLETELY FIXED: Transform function for YOUR ACTUAL DATA STRUCTURE
const transformKsiResultsToExecutions = (rawData, requestedTenant = null) => {
  console.log('🔄 Transforming KSI results to executions for tenant:', requestedTenant);
  console.log('🔄 Raw data received:', rawData);
  
  const executions = rawData.data?.executions || [];
  console.log('📊 Raw executions found:', executions.length);
  
  if (executions.length === 0) {
    console.log('🔄 No executions found in API response');
    return {
      success: true,
      data: {
        executions: [],
        count: 0,
        tenant_id: requestedTenant
      }
    };
  }
  
  // ✅ TENANT FILTERING - only show data for requested tenant
  let filteredExecutions = executions;
  if (requestedTenant && requestedTenant !== 'all') {
    filteredExecutions = executions.filter(ex => {
      const matches = ex.tenant_id === requestedTenant;
      if (!matches) {
        console.log(`🚫 Filtering out execution from tenant "${ex.tenant_id}" (requested: "${requestedTenant}")`);
      }
      return matches;
    });
    console.log(`🎯 Tenant filtering: kept ${filteredExecutions.length} of ${executions.length} executions`);
  }
  
  // ✅ YOUR DATA IS ALREADY IN EXECUTION SUMMARY FORMAT - just return it!
  const transformedExecutions = filteredExecutions.map(execution => ({
    execution_id: execution.execution_id,
    tenant_id: execution.tenant_id,
    status: execution.status || 'UNKNOWN',
    timestamp: execution.timestamp || execution.completed_at,
    validators_completed: execution.validators_completed || [],
    validators_requested: execution.validators_requested || [],
    total_ksis_validated: execution.total_ksis_validated || 0,
    trigger_source: execution.trigger_source || 'unknown',
    validation_results: execution.validation_results || [],
    // Add computed fields for UI
    started_at: execution.timestamp || execution.completed_at,
    completed_at: execution.completed_at || execution.timestamp,
    duration: 'N/A', // Could calculate if start/end times available
    success_rate: execution.validators_completed ? 
      (execution.validators_completed.length / (execution.validators_requested?.length || 5)) * 100 : 0
  }));
  
  // Sort by timestamp (newest first)
  transformedExecutions.sort((a, b) => {
    const timeA = new Date(a.timestamp || 0);
    const timeB = new Date(b.timestamp || 0);
    return timeB - timeA;
  });
  
  console.log(`🔄 Transformation complete: ${transformedExecutions.length} executions for tenant ${requestedTenant}`);
  
  return {
    success: true,
    data: {
      executions: transformedExecutions,
      count: transformedExecutions.length,
      tenant_id: requestedTenant
    }
  };
};

// ✅ NEW: Calculate compliance overview from CLI details (real data)
const calculateComplianceFromCLIDetails = (cliDetails) => {
  if (!cliDetails || cliDetails.length === 0) {
    return {
      totalValidators: 5,
      completedValidators: 0,
      successfulValidators: 0,
      overallCompliance: 0,
      validatorsWithCLI: 0
    };
  }

  const validatorsWithCLI = cliDetails.length;
  const successfulValidators = cliDetails.filter(detail => {
    return detail.assertion === true || 
           (detail.cli_command_details && detail.cli_command_details.some(cmd => cmd.success === true));
  }).length;

  const overallCompliance = Math.round((validatorsWithCLI / 5) * 100);

  return {
    totalValidators: 5,
    completedValidators: validatorsWithCLI,
    successfulValidators,
    overallCompliance,
    validatorsWithCLI,
    pendingValidators: 5 - validatorsWithCLI
  };
};

// Calculate compliance overview from validation results
const calculateComplianceOverview = (validationResults) => {
  if (!validationResults || validationResults.length === 0) {
    return {
      totalKsis: 0,
      passedKsis: 0,
      failedKsis: 0,
      compliancePercentage: 0,
      lastUpdated: new Date().toISOString()
    };
  }
  
  const totalKsis = validationResults.length;
  const passedKsis = validationResults.filter(result => 
    result.status === 'SUCCESS' || result.assertion === true
  ).length;
  const failedKsis = totalKsis - passedKsis;
  const compliancePercentage = totalKsis > 0 ? (passedKsis / totalKsis) * 100 : 0;
  
  return {
    totalKsis,
    passedKsis,
    failedKsis,
    compliancePercentage: Math.round(compliancePercentage),
    lastUpdated: new Date().toISOString()
  };
};

// Parse individual validation result
const parseValidationResult = (result) => {
  try {
    let parsedResult = result;
    
    // Handle nested result structure
    if (result.result && result.result.body) {
      parsedResult = typeof result.result.body === 'string' ? 
        JSON.parse(result.result.body) 
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
  
  // ✅ NEW: Calculate compliance from CLI details (real data)
  calculateComplianceFromCLIDetails,
  
  // Parse validation results
  parseValidationResult,

  // Trigger KSI validation for a tenant
  triggerValidation: async (tenantId = 'riskuity-production', triggerSource = 'manual', executionId = null) => {
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
    console.log('🏢 Fetching tenants from API...');
    try {
      const response = await apiClient.get('/api/ksi/tenants');
      console.log('🏢 Tenants API response:', response.data);
      return response.data;
    } catch (error) {
      console.warn('Failed to load tenants:', error.message);
      // Return fallback tenant list
      return {
        success: true,
        tenants: [
          { tenant_id: 'riskuity-production', tenant_name: 'Riskuity Production', ksi_count: 5 },
          { tenant_id: 'riskuity-internal', tenant_name: 'Riskuity Internal', ksi_count: 5 }
        ]
      };
    }
  },

  // Get KSI execution history with proper tenant filtering
  getExecutionHistory: async (tenantId = 'riskuity-production', limit = 20, startKey = null) => {
    try {
      const params = new URLSearchParams();
      
      // Always pass tenant_id for proper filtering
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
      
      // Transform the response data
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
  },

  // ✅ NEW: Get individual validator record with CLI command details
  getValidatorDetails: async (executionId, ksiId) => {
    try {
      // ✅ FIXED: Clean execution ID first (remove any existing #KSI- suffix)
      const cleanExecutionId = executionId.split('#')[0];
      const validatorRecordId = `${cleanExecutionId}#${ksiId}`;
      
      const params = new URLSearchParams();
      params.append('execution_id', validatorRecordId);
      
      const url = `/api/ksi/results?${params.toString()}`;
      console.log('🔍 Fetching validator CLI details:', url);
      console.log('🔍 Clean execution ID:', cleanExecutionId, '+ KSI ID:', ksiId, '= Record ID:', validatorRecordId);
      
      const response = await apiClient.get(url);
      
      if (response.data.success && response.data.data.validation_results.length > 0) {
        const validatorRecord = response.data.data.validation_results[0];
        
        // Extract CLI command details from the correct path
        const cliDetails = validatorRecord.validation_result?.cli_command_details || [];
        
        console.log('✅ Found CLI command details:', cliDetails.length, 'commands');
        
        return {
          success: true,
          data: {
            validator_record: validatorRecord,
            cli_command_details: cliDetails,
            ksi_id: validatorRecord.ksi_id,
            validator_type: validatorRecord.validator_type,
            assertion: validatorRecord.validation_result?.assertion,
            assertion_reason: validatorRecord.validation_result?.assertion_reason
          }
        };
      } else {
        throw new Error('Validator record not found');
      }
      
    } catch (error) {
      console.error('❌ Failed to fetch validator details:', error);
      throw new Error(`Failed to fetch validator CLI details: ${error.message}`);
    }
  },

  // ✅ NEW: Get all validator details for an execution with CLI commands
  getAllValidatorDetails: async (executionId, validators = ['cna', 'svc', 'iam', 'mla', 'cmt']) => {
    try {
      console.log('🔍 Fetching all validator details for execution:', executionId);
      
      const validatorPromises = validators.map(async (validator) => {
        try {
          const ksiId = `KSI-${validator.toUpperCase()}-01`;
          const details = await ksiService.getValidatorDetails(executionId, ksiId);
          
          return {
            validator: validator,
            ksi_id: ksiId,
            ...details.data
          };
        } catch (error) {
          console.warn(`Failed to fetch details for ${validator}:`, error.message);
          return {
            validator: validator,
            ksi_id: `KSI-${validator.toUpperCase()}-01`,
            error: error.message,
            cli_command_details: []
          };
        }
      });
      
      const allDetails = await Promise.all(validatorPromises);
      
      // ✅ Filter out validators with errors for cleaner results
      const successfulDetails = allDetails.filter(detail => !detail.error && detail.cli_command_details?.length > 0);
      
      console.log('✅ Fetched details for', allDetails.length, 'validators,', successfulDetails.length, 'successful');
      
      return {
        success: true,
        data: successfulDetails
      };
      
    } catch (error) {
      console.error('❌ Failed to fetch all validator details:', error);
      throw new Error(`Failed to fetch all validator details: ${error.message}`);
    }
  }
};

export { getValidatorIcon, ksiService };
export default ksiService;
