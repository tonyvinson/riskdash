import React, { useState, useEffect, useCallback } from 'react';
import ksiService from '../../services/ksiService';

const KSIManager = () => {
    const [availableTenants, setAvailableTenants] = useState([]);
    const [selectedTenant, setSelectedTenant] = useState('');
    const [executionHistory, setExecutionHistory] = useState([]);
    const [validationResults, setValidationResults] = useState([]);
    const [complianceOverview, setComplianceOverview] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isValidating, setIsValidating] = useState(false);
    const [expandedExecution, setExpandedExecution] = useState(null);

    // ✅ FIXED: Robust API Response Parsing Utility
    const parseApiResponse = (response, possiblePaths = []) => {
        console.log('🔍 Parsing API response:', response);
        
        // Check success flag first
        if (!response.success) {
            console.warn('⚠️ API response indicated failure:', response);
            return [];
        }

        // Try multiple possible data locations
        const dataPaths = [
            'data.validation_results',
            'data.validators_completed', 
            'data.results',
            'data.executions',
            'data',
            'validation_results',
            'validators_completed',
            'results',
            'executions',
            ...possiblePaths
        ];

        for (const path of dataPaths) {
            const pathArray = path.split('.');
            let value = response;
            
            // Navigate through the path
            for (const key of pathArray) {
                if (value && typeof value === 'object' && key in value) {
                    value = value[key];
                } else {
                    value = null;
                    break;
                }
            }
            
            // Check if we found valid data
            if (Array.isArray(value) && value.length > 0) {
                console.log(`✅ Found data at path: ${path}`, value);
                return value;
            } else if (value && typeof value === 'object' && !Array.isArray(value)) {
                // Handle single object responses
                console.log(`✅ Found object at path: ${path}`, value);
                return [value];
            }
        }

        console.log('ℹ️ No data found in API response');
        return [];
    };

    // ✅ FIXED: Enhanced JSON body parsing with error handling
    const parseValidationBody = (result) => {
        try {
            console.log('📊 Parsing validation body for:', result?.validator);
            
            let resultBody = result?.result?.body;
            
            // Handle different body formats
            if (typeof resultBody === 'string') {
                try {
                    const parsed = JSON.parse(resultBody);
                    console.log(`✅ Successfully parsed JSON body for ${result?.validator}:`, parsed);
                    return parsed;
                } catch (parseError) {
                    console.warn(`⚠️ Could not parse JSON body for ${result?.validator}:`, parseError);
                    return { 
                        raw: resultBody, 
                        error: 'JSON parse error',
                        parseError: parseError.message 
                    };
                }
            } else if (resultBody && typeof resultBody === 'object') {
                console.log(`✅ Body already parsed for ${result?.validator}:`, resultBody);
                return resultBody;
            } else {
                console.log(`ℹ️ No body found for ${result?.validator}`);
                return { 
                    error: 'No result body found',
                    status: result?.result?.status || 'Unknown',
                    statusCode: result?.result?.statusCode || null
                };
            }
        } catch (error) {
            console.error('❌ Error parsing validation body:', error);
            return { 
                error: 'Parse error', 
                raw: result,
                errorMessage: error.message 
            };
        }
    };

    // ✅ FIXED: Robust compliance overview calculation
    const calculateComplianceOverview = (results) => {
        try {
            console.log('📊 Calculating compliance overview for', results.length, 'results');
            
            if (!results || results.length === 0) {
                setComplianceOverview(null);
                return;
            }

            let totalKsis = 0;
            let passedKsis = 0;
            let failedKsis = 0;
            const validatorSummary = {};

            results.forEach(result => {
                const parsedBody = parseValidationBody(result);
                const validator = result.validator?.toUpperCase() || 'UNKNOWN';

                // Extract summary data
                if (parsedBody.summary) {
                    totalKsis += parsedBody.summary.total_ksis || 0;
                    passedKsis += parsedBody.summary.passed || 0;
                    failedKsis += parsedBody.summary.failed || 0;
                    
                    validatorSummary[validator] = {
                        total: parsedBody.summary.total_ksis || 0,
                        passed: parsedBody.summary.passed || 0,
                        failed: parsedBody.summary.failed || 0,
                        pass_rate: parsedBody.summary.pass_rate || 0
                    };
                } else {
                    // Fallback: analyze individual results
                    const individualResults = parsedBody.results || [];
                    const validatorTotal = individualResults.length;
                    const validatorPassed = individualResults.filter(r => r.assertion === true).length;
                    const validatorFailed = validatorTotal - validatorPassed;

                    totalKsis += validatorTotal;
                    passedKsis += validatorPassed;
                    failedKsis += validatorFailed;

                    validatorSummary[validator] = {
                        total: validatorTotal,
                        passed: validatorPassed,
                        failed: validatorFailed,
                        pass_rate: validatorTotal > 0 ? (validatorPassed / validatorTotal) * 100 : 0
                    };
                }
            });

            const overallPassRate = totalKsis > 0 ? (passedKsis / totalKsis) * 100 : 0;

            const overview = {
                total_validators: results.length,
                total_ksis: totalKsis,
                passed_ksis: passedKsis,
                failed_ksis: failedKsis,
                overall_pass_rate: overallPassRate,
                validator_breakdown: validatorSummary,
                last_updated: new Date().toISOString()
            };

            console.log('✅ Compliance overview calculated:', overview);
            setComplianceOverview(overview);

        } catch (error) {
            console.error('❌ Error calculating compliance overview:', error);
            setComplianceOverview(null);
        }
    };

    // ✅ FIXED: Enhanced tenant loading
    const loadTenants = useCallback(async () => {
        try {
            console.log('🏢 Loading available tenants...');
            const response = await ksiService.getTenants();
            
            const tenants = parseApiResponse(response, ['tenants']);
            
            if (tenants.length > 0) {
                setAvailableTenants(tenants);
                
                // Auto-select riskuity-production if available, otherwise first tenant
                const preferredTenant = tenants.includes('riskuity-production') 
                    ? 'riskuity-production' 
                    : tenants[0];
                    
                setSelectedTenant(preferredTenant);
                console.log(`✅ Loaded ${tenants.length} tenants, selected: ${preferredTenant}`);
            } else {
                console.log('ℹ️ No tenants found');
                setAvailableTenants([]);
            }
            
        } catch (err) {
            console.error('❌ Error loading tenants:', err);
            setError('Failed to load tenants');
            setAvailableTenants([]);
        }
    }, []);

    // ✅ FIXED: Enhanced execution history fetching
    const fetchExecutionHistory = useCallback(async () => {
        if (!selectedTenant) return;

        try {
            console.log(`📅 Fetching execution history for tenant: ${selectedTenant}`);
            const response = await ksiService.getExecutionHistory(selectedTenant);
            
            const executions = parseApiResponse(response, ['data.executions', 'executions']);
            
            // Sort by timestamp (newest first)
            const sortedExecutions = executions
                .filter(exec => exec && exec.execution_id)
                .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            
            setExecutionHistory(sortedExecutions);
            console.log(`✅ Loaded ${sortedExecutions.length} executions`);
            
        } catch (err) {
            console.error('❌ Error fetching execution history:', err);
            setError('Failed to load execution history');
            setExecutionHistory([]);
        }
    }, [selectedTenant]);

    // ✅ FIXED: Enhanced current KSI data fetching with multiple fallbacks
    const fetchCurrentKSIData = useCallback(async () => {
        if (!selectedTenant) return;

        try {
            console.log(`🔍 Fetching current KSI data for tenant: ${selectedTenant}`);
            const response = await ksiService.getValidationResults(selectedTenant);
            
            // Use enhanced parsing with multiple possible paths
            const results = parseApiResponse(response, [
                'data.validation_results',
                'data.validators_completed',
                'validation_results',
                'validators_completed'
            ]);
            
            if (results.length > 0) {
                console.log(`📊 Processing ${results.length} validation results`);
                
                // Process and enrich the results
                const processedResults = results.map(result => {
                    const parsedBody = parseValidationBody(result);
                    
                    return {
                        ksi_id: `${result.validator?.toUpperCase() || 'UNKNOWN'} Validator`,
                        description: `${result.validator?.toUpperCase() || 'UNKNOWN'} Category Validation`,
                        status: result.result?.status || 'Unknown',
                        validator: result.validator,
                        function_name: result.function_name,
                        details: parsedBody,
                        ksis_validated: parsedBody.ksis_validated || 0,
                        summary: parsedBody.summary || null,
                        individual_results: parsedBody.results || [],
                        raw_result: result // Keep raw data for debugging
                    };
                });
                
                setValidationResults(processedResults);
                calculateComplianceOverview(processedResults);
                console.log(`✅ Successfully processed ${processedResults.length} validation results`);
                
            } else {
                console.log('ℹ️ No current KSI data found for this tenant');
                setValidationResults([]);
                setComplianceOverview(null);
            }
            
        } catch (err) {
            console.error('❌ Error fetching current KSI data:', err);
            // Don't show error for background loading
            setValidationResults([]);
            setComplianceOverview(null);
        }
    }, [selectedTenant]);

    // Load tenants on component mount
    useEffect(() => {
        loadTenants();
    }, [loadTenants]);

    // Load data when selected tenant changes
    useEffect(() => {
        if (selectedTenant && availableTenants.length > 0) {
            fetchExecutionHistory();
            fetchCurrentKSIData();
        }
    }, [selectedTenant, availableTenants.length, fetchExecutionHistory, fetchCurrentKSIData]);

    // ✅ CRITICAL FIX: Enhanced validation result fetching for specific execution
    const fetchValidationResults = async (executionId) => {
        try {
            setLoading(true);
            console.log(`🔍 Fetching detailed results for execution: ${executionId}`);
            
            // ✅ FIXED: Use correct method name with proper parameters
            const response = await ksiService.getValidationResults(null, executionId);
            const results = parseApiResponse(response, [
                'data.validation_results',
                'data.results',
                'validation_results',
                'results'
            ]);
            
            if (results.length > 0) {
                const processedResults = results.map(result => {
                    const parsedBody = parseValidationBody(result);
                    
                    return {
                        ksi_id: `${result.validator?.toUpperCase() || 'UNKNOWN'} Validator`,
                        description: `${result.validator?.toUpperCase() || 'UNKNOWN'} Category Validation`,
                        status: result.result?.status || 'Unknown',
                        validator: result.validator,
                        function_name: result.function_name,
                        details: parsedBody,
                        ksis_validated: parsedBody.ksis_validated || 0,
                        summary: parsedBody.summary || null,
                        individual_results: parsedBody.results || []
                    };
                });
                
                setValidationResults(processedResults);
                calculateComplianceOverview(processedResults);
                console.log(`✅ Loaded detailed results for execution ${executionId}`);
            } else {
                console.log(`ℹ️ No results found for execution ${executionId}`);
                setValidationResults([]);
                setComplianceOverview(null);
            }
            
        } catch (err) {
            console.error('❌ Error fetching validation results:', err);
            setError(`Failed to fetch results for execution ${executionId}`);
            setValidationResults([]);
            setComplianceOverview(null);
        } finally {
            setLoading(false);
        }
    };

    // ✅ FIXED: Enhanced validation triggering with polling
    const triggerValidation = async () => {
        try {
            setIsValidating(true);
            setError(null);
            
            console.log(`🚀 Triggering validation for tenant: ${selectedTenant}`);
            const response = await ksiService.triggerValidation(selectedTenant);
            
            if (response.success) {
                console.log('✅ Validation triggered successfully:', response);
                
                // Start polling for updates
                const pollInterval = setInterval(async () => {
                    await fetchExecutionHistory();
                    await fetchCurrentKSIData();
                }, 5000); // Poll every 5 seconds
                
                // Stop polling after 2 minutes
                setTimeout(() => {
                    clearInterval(pollInterval);
                    setIsValidating(false);
                }, 120000);
                
            } else {
                throw new Error(response.message || 'Validation trigger failed');
            }
            
        } catch (err) {
            console.error('❌ Error triggering validation:', err);
            setError(`Failed to trigger validation: ${err.message}`);
            setIsValidating(false);
        }
    };

    // Handle tenant selection change
    const handleTenantChange = (event) => {
        const newTenant = event.target.value;
        console.log(`🏢 Switching to tenant: ${newTenant}`);
        setSelectedTenant(newTenant);
        setValidationResults([]);
        setComplianceOverview(null);
        setExecutionHistory([]);
        setError(null);
    };

    // Toggle execution details
    const toggleExecutionDetails = (executionId) => {
        if (expandedExecution === executionId) {
            setExpandedExecution(null);
        } else {
            setExpandedExecution(executionId);
            fetchValidationResults(executionId);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-white shadow rounded-lg px-6 py-4">
                <h1 className="text-2xl font-bold text-gray-900">KSI Validator Platform</h1>
                <p className="text-gray-600">Monitor and manage FedRAMP compliance validation</p>
            </div>

            {/* Error Display */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex">
                        <div className="flex-shrink-0">
                            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <div className="ml-3">
                            <h3 className="text-sm font-medium text-red-800">Error</h3>
                            <div className="text-sm text-red-700">{error}</div>
                        </div>
                        <div className="ml-auto">
                            <button 
                                onClick={() => setError(null)}
                                className="text-red-400 hover:text-red-600"
                            >
                                <span className="sr-only">Dismiss</span>
                                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Controls */}
            <div className="bg-white shadow rounded-lg px-6 py-4">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
                    <div className="flex-1 max-w-md">
                        <label htmlFor="tenant-select" className="block text-sm font-medium text-gray-700 mb-2">
                            Select Tenant
                        </label>
                        <select
                            id="tenant-select"
                            value={selectedTenant}
                            onChange={handleTenantChange}
                            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value="">Select a tenant...</option>
                            {availableTenants.map(tenant => (
                                <option key={tenant} value={tenant}>{tenant}</option>
                            ))}
                        </select>
                    </div>
                    
                    <div className="flex space-x-3">
                        <button
                            onClick={() => {
                                fetchExecutionHistory();
                                fetchCurrentKSIData();
                            }}
                            disabled={!selectedTenant || loading}
                            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Refreshing...' : 'Refresh'}
                        </button>
                        
                        <button
                            onClick={triggerValidation}
                            disabled={!selectedTenant || isValidating}
                            className="px-4 py-2 bg-blue-600 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isValidating ? 'Validating...' : 'Trigger Validation'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Compliance Overview */}
            {complianceOverview && (
                <div className="bg-white shadow rounded-lg px-6 py-4">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Compliance Overview</h2>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="text-center">
                            <div className="text-2xl font-bold text-blue-600">{complianceOverview.total_validators}</div>
                            <div className="text-sm text-gray-500">Total Validators</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-green-600">{complianceOverview.passed_ksis}</div>
                            <div className="text-sm text-gray-500">Passed KSIs</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-red-600">{complianceOverview.failed_ksis}</div>
                            <div className="text-sm text-gray-500">Failed KSIs</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-purple-600">{complianceOverview.overall_pass_rate.toFixed(1)}%</div>
                            <div className="text-sm text-gray-500">Pass Rate</div>
                        </div>
                    </div>
                </div>
            )}

            {/* Execution History */}
            {executionHistory.length > 0 && (
                <div className="bg-white shadow rounded-lg px-6 py-4">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Executions</h2>
                    <div className="space-y-3">
                        {executionHistory.slice(0, 5).map((execution, index) => (
                            <div key={index} className="border border-gray-200 rounded-lg p-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <div className="font-medium text-gray-900">
                                            Execution {execution.execution_id?.substring(0, 8)}...
                                        </div>
                                        <div className="text-sm text-gray-500">
                                            {new Date(execution.timestamp).toLocaleString()}
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                            execution.status === 'COMPLETED' 
                                                ? 'bg-green-100 text-green-800' 
                                                : execution.status === 'FAILED'
                                                ? 'bg-red-100 text-red-800'
                                                : 'bg-yellow-100 text-yellow-800'
                                        }`}>
                                            {execution.status}
                                        </span>
                                        <div className="text-xs text-gray-500 mt-1">
                                            {execution.validators_completed?.length || 0}/5 validators
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Current Validation Results */}
            {validationResults.length > 0 && (
                <div className="bg-white shadow rounded-lg px-6 py-4">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Validation Results</h2>
                    <div className="space-y-4">
                        {validationResults.map((result, index) => (
                            <div key={index} className="border border-gray-200 rounded-lg p-4">
                                <div className="flex items-center justify-between mb-3">
                                    <div>
                                        <h3 className="font-medium text-gray-900">{result.ksi_id}</h3>
                                        <p className="text-sm text-gray-500">{result.description}</p>
                                    </div>
                                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                        result.status === 'SUCCESS' 
                                            ? 'bg-green-100 text-green-800' 
                                            : 'bg-red-100 text-red-800'
                                    }`}>
                                        {result.status}
                                    </span>
                                </div>
                                
                                {result.summary && (
                                    <div className="grid grid-cols-4 gap-4 text-sm mb-3">
                                        <div>
                                            <span className="text-gray-500">KSIs:</span>
                                            <span className="ml-1 font-medium">{result.summary.total_ksis}</span>
                                        </div>
                                        <div>
                                            <span className="text-gray-500">Passed:</span>
                                            <span className="ml-1 font-medium text-green-600">{result.summary.passed}</span>
                                        </div>
                                        <div>
                                            <span className="text-gray-500">Failed:</span>
                                            <span className="ml-1 font-medium text-red-600">{result.summary.failed}</span>
                                        </div>
                                        <div>
                                            <span className="text-gray-500">Pass Rate:</span>
                                            <span className="ml-1 font-medium">{result.summary.pass_rate}%</span>
                                        </div>
                                    </div>
                                )}
                                
                                {/* Individual KSI Results */}
                                {result.individual_results && result.individual_results.length > 0 && (
                                    <div className="border-t border-gray-100 pt-3">
                                        <h4 className="font-medium text-gray-900 mb-3">Detailed Results</h4>
                                        {result.individual_results.map((ksi, ksiIndex) => (
                                            <div key={ksiIndex} className="mb-3 p-3 bg-gray-50 rounded">
                                                <div className="flex justify-between items-center mb-2">
                                                    <span className="font-semibold">{ksi.ksi_id}</span>
                                                    <span className={`px-2 py-1 text-xs font-semibold rounded ${
                                                        ksi.assertion ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                                    }`}>
                                                        {ksi.assertion ? 'PASS' : 'FAIL'}
                                                    </span>
                                                </div>
                                                {ksi.assertion_reason && (
                                                    <p className="text-sm text-gray-600 mb-2">{ksi.assertion_reason}</p>
                                                )}
                                                
                                                {/* Command Details */}
                                                {ksi.cli_command_details && ksi.cli_command_details.length > 0 && (
                                                    <div className="space-y-2">
                                                        <h5 className="text-xs font-medium text-gray-700 uppercase tracking-wide">
                                                            Command Details
                                                        </h5>
                                                        {ksi.cli_command_details.map((cmd, cmdIndex) => (
                                                            <div key={cmdIndex} className="bg-white border rounded p-2">
                                                                <div className="flex justify-between items-start mb-1">
                                                                    <code className="text-xs text-blue-600 flex-1">
                                                                        {cmd.command}
                                                                    </code>
                                                                    <span className={`ml-2 px-1 py-0.5 text-xs rounded ${
                                                                        cmd.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                                                                    }`}>
                                                                        {cmd.success ? '✓' : '✗'}
                                                                    </span>
                                                                </div>
                                                                {cmd.note && (
                                                                    <p className="text-xs text-gray-500 mb-1">{cmd.note}</p>
                                                                )}
                                                                {cmd.data && (
                                                                    <div className="text-xs bg-gray-100 rounded p-1 mt-1">
                                                                        <strong>Results:</strong>
                                                                        <pre className="mt-1 whitespace-pre-wrap">
                                                                            {JSON.stringify(cmd.data, null, 2)}
                                                                        </pre>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Empty State */}
            {!selectedTenant && (
                <div className="bg-white shadow rounded-lg px-6 py-8 text-center">
                    <p className="text-gray-500">Please select a tenant to view validation results.</p>
                </div>
            )}

            {selectedTenant && !loading && executionHistory.length === 0 && validationResults.length === 0 && (
                <div className="bg-white shadow rounded-lg px-6 py-8 text-center">
                    <p className="text-gray-500">
                        No validation data available for {selectedTenant}. 
                        <br />
                        Click "Trigger Validation" to start a new validation run.
                    </p>
                </div>
            )}
        </div>
    );
};

export default KSIManager;
