// frontend/src/components/KSIManager/KSIManager.js - Enterprise Edition with Enhanced Data Parsing
import React, { useState, useEffect, useCallback } from 'react';
import { ksiService } from '../../services/ksiService';

const KSIManager = () => {
    const [loading, setLoading] = useState(false);
    const [selectedTenant, setSelectedTenant] = useState('riskuity-production');
    const [availableTenants, setAvailableTenants] = useState([]);
    const [tenantsLoading, setTenantsLoading] = useState(false);
    const [executionHistory, setExecutionHistory] = useState([]);
    const [validationResults, setValidationResults] = useState([]);
    const [error, setError] = useState(null);
    const [lastExecution, setLastExecution] = useState(null);
    const [selectedExecutionId, setSelectedExecutionId] = useState(null);
    const [complianceOverview, setComplianceOverview] = useState(null);

    // KSI categories for display
    const ksiCategories = {
        'CNA': { name: 'Configuration & Network Architecture', icon: '🏗️', color: 'blue' },
        'SVC': { name: 'Service Configuration', icon: '⚙️', color: 'green' },
        'IAM': { name: 'Identity & Access Management', icon: '🔐', color: 'purple' }, 
        'MLA': { name: 'Monitoring, Logging & Alerting', icon: '📊', color: 'orange' },
        'CMT': { name: 'Configuration Management & Tracking', icon: '📋', color: 'indigo' }
    };

    // Load available tenants from API
    const loadTenants = useCallback(async () => {
        try {
            setTenantsLoading(true);
            setError(null);
            
            console.log('🏢 Loading tenants from API...');
            const response = await ksiService.getTenants();
            
            console.log('🏢 Tenants loaded:', response);
            
            if (response.success && response.tenants) {
                const formattedTenants = response.tenants.map(tenant => ({
                    id: tenant.tenant_id,
                    name: tenant.display_name || tenant.tenant_id.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                    ksiCount: tenant.ksi_count || 0
                }));
                
                setAvailableTenants(formattedTenants);
                console.log('✅ Formatted tenants:', formattedTenants);
            } else {
                // Fallback to default tenants
                setAvailableTenants([
                    { id: 'riskuity-production', name: 'Riskuity Production', ksiCount: 5 },
                    { id: 'real-test', name: 'Real Test', ksiCount: 5 }
                ]);
            }
        } catch (error) {
            console.error('❌ Failed to load tenants:', error);
            setError(`Failed to load tenants: ${error.message}`);
            // Fallback to default tenants
            setAvailableTenants([
                { id: 'riskuity-production', name: 'Riskuity Production', ksiCount: 5 },
                { id: 'real-test', name: 'Real Test', ksiCount: 5 }
            ]);
        } finally {
            setTenantsLoading(false);
        }
    }, []);

    // Load KSI execution history with enhanced parsing
    const loadExecutionHistory = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            
            console.log(`📊 Loading execution history for tenant: ${selectedTenant}`);
            
            const response = await ksiService.getExecutionHistory(selectedTenant, 10);
            console.log('📊 Raw execution history response:', response);
            
            if (response.success && response.data) {
                const executions = response.data.executions || [];
                console.log('📊 Processing executions:', executions);
                
                setExecutionHistory(executions);
                
                // Set the most recent execution for detailed view
                if (executions.length > 0) {
                    const latest = executions[0];
                    setLastExecution(latest);
                    setSelectedExecutionId(latest.execution_id);
                    
                    // Calculate compliance overview from latest execution
                    if (latest.validation_results && latest.validation_results.length > 0) {
                        const overview = ksiService.calculateComplianceOverview(latest.validation_results);
                        setComplianceOverview(overview);
                        console.log('📊 Calculated compliance overview:', overview);
                    }
                }
            } else {
                console.warn('No execution data found in response');
                setExecutionHistory([]);
            }
        } catch (error) {
            console.error('❌ Failed to load execution history:', error);
            setError(`Failed to load execution history: ${error.message}`);
            setExecutionHistory([]);
        } finally {
            setLoading(false);
        }
    }, [selectedTenant]);

    // Load detailed validation results
    const loadValidationResults = useCallback(async (executionId = null) => {
        try {
            setLoading(true);
            setError(null);
            
            const targetExecutionId = executionId || selectedExecutionId;
            console.log(`🔍 Loading validation results for execution: ${targetExecutionId}`);
            
            const response = await ksiService.getValidationResults(selectedTenant, targetExecutionId);
            console.log('🔍 Raw validation results response:', response);
            
            if (response.success && response.data) {
                let results = [];
                
                // Try multiple possible data structures
                if (response.data.results && response.data.results.length > 0) {
                    results = response.data.results;
                    console.log('🔍 Found results in response.data.results');
                } else if (response.data.validation_results && response.data.validation_results.length > 0) {
                    results = response.data.validation_results;
                    console.log('🔍 Found results in response.data.validation_results');
                } else if (Array.isArray(response.data)) {
                    results = response.data;
                    console.log('🔍 Response.data is array of results');
                } else {
                    console.warn('🔍 No validation results found in expected locations, checking execution history...');
                    
                    // Fallback: get results from the execution history
                    const execution = executionHistory.find(ex => ex.execution_id === targetExecutionId);
                    if (execution && execution.validation_results) {
                        results = execution.validation_results;
                        console.log('🔍 Using validation_results from execution history');
                    }
                }
                
                console.log('🔍 Processing validation results:', results);
                setValidationResults(results);
                
                // Calculate compliance overview if not already set
                if (results.length > 0 && !complianceOverview) {
                    const overview = ksiService.calculateComplianceOverview(results);
                    setComplianceOverview(overview);
                    console.log('📊 Calculated compliance overview from results:', overview);
                }
            } else {
                console.warn('No validation results found in response');
                setValidationResults([]);
            }
        } catch (error) {
            console.error('❌ Failed to load validation results:', error);
            setError(`Failed to load validation results: ${error.message}`);
            setValidationResults([]);
        } finally {
            setLoading(false);
        }
    }, [selectedTenant, selectedExecutionId, executionHistory, complianceOverview]);

    // Trigger KSI validation
    const triggerValidation = async () => {
        try {
            setLoading(true);
            setError(null);
            
            console.log(`🚀 Triggering validation for tenant: ${selectedTenant}`);
            
            const response = await ksiService.triggerValidation(selectedTenant, 'manual');
            console.log('🚀 Validation triggered:', response);
            
            if (response.success) {
                // Refresh the execution history after a short delay
                setTimeout(() => {
                    loadExecutionHistory();
                }, 3000);
            } else {
                setError(`Validation failed: ${response.message || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('❌ Failed to trigger validation:', error);
            setError(`Failed to trigger validation: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Handle tenant selection change
    const handleTenantChange = (tenantId) => {
        console.log(`🏢 Changing tenant to: ${tenantId}`);
        setSelectedTenant(tenantId);
        setSelectedExecutionId(null);
        setComplianceOverview(null);
        setValidationResults([]);
        setExecutionHistory([]);
    };

    // Handle execution selection
    const handleExecutionSelect = (execution) => {
        console.log(`📊 Selecting execution: ${execution.execution_id}`);
        setSelectedExecutionId(execution.execution_id);
        setLastExecution(execution);
        
                // Parse execution data for compliance overview
                const parsedExecution = ksiService.parseExecutionData(execution);
                if (parsedExecution && parsedExecution.compliance_overview) {
                    setComplianceOverview(parsedExecution.compliance_overview);
                }
        
        // Load detailed results for this execution
        loadValidationResults(execution.execution_id);
    };

    // Initial load
    useEffect(() => {
        loadTenants();
    }, [loadTenants]);

    // Load data when tenant changes
    useEffect(() => {
        if (selectedTenant) {
            loadExecutionHistory();
        }
    }, [selectedTenant, loadExecutionHistory]);

    // Format timestamp for display
    const formatTimestamp = (timestamp) => {
        if (!timestamp) return 'N/A';
        try {
            return new Date(timestamp).toLocaleString();
        } catch (error) {
            return timestamp;
        }
    };

    // Get execution status display
    const getExecutionStatusDisplay = (execution) => {
        const status = execution.status || 'UNKNOWN';
        const statusColors = {
            'COMPLETED': 'bg-green-100 text-green-800',
            'RUNNING': 'bg-blue-100 text-blue-800',
            'FAILED': 'bg-red-100 text-red-800',
            'PENDING': 'bg-yellow-100 text-yellow-800'
        };
        
        return (
            <span className={`px-2 py-1 text-xs font-semibold rounded ${statusColors[status] || 'bg-gray-100 text-gray-800'}`}>
                {status}
            </span>
        );
    };

    return (
        <div className="max-w-7xl mx-auto p-6 space-y-6">
            {/* Header with Tenant Selection */}
            <div className="bg-white shadow rounded-lg p-6">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">
                            🛡️ KSI Validator Dashboard
                        </h1>
                        <p className="text-gray-600 mt-1">
                            FedRAMP 20X Compliance Validation Platform
                        </p>
                    </div>
                    
                    <div className="flex space-x-4">
                        {/* Tenant Selection */}
                        <div className="flex items-center space-x-2">
                            <label htmlFor="tenant-select" className="text-sm font-medium text-gray-700">
                                Tenant:
                            </label>
                            <select
                                id="tenant-select"
                                value={selectedTenant}
                                onChange={(e) => handleTenantChange(e.target.value)}
                                className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                disabled={tenantsLoading}
                            >
                                {tenantsLoading ? (
                                    <option>Loading tenants...</option>
                                ) : (
                                    availableTenants.map((tenant) => (
                                        <option key={tenant.id} value={tenant.id}>
                                            {tenant.name} ({tenant.ksiCount} KSIs)
                                        </option>
                                    ))
                                )}
                            </select>
                            
                            <button
                                onClick={loadTenants}
                                disabled={tenantsLoading}
                                className="px-3 py-2 text-xs bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50"
                            >
                                {tenantsLoading ? '🔄' : '🔄 Reload'}
                            </button>
                        </div>
                        
                        {/* Trigger Validation */}
                        <button
                            onClick={triggerValidation}
                            disabled={loading}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                        >
                            {loading ? (
                                <>
                                    <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                                    <span>Running...</span>
                                </>
                            ) : (
                                <>
                                    <span>🚀 Run Validation</span>
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {/* Error Display */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex">
                        <div className="flex-shrink-0">
                            <span className="text-red-400 text-xl">⚠️</span>
                        </div>
                        <div className="ml-3">
                            <h3 className="text-sm font-medium text-red-800">Error</h3>
                            <div className="mt-1 text-sm text-red-700">{error}</div>
                        </div>
                        <div className="ml-auto">
                            <button
                                onClick={() => setError(null)}
                                className="text-red-400 hover:text-red-600"
                            >
                                ✕
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Compliance Overview Dashboard */}
            {complianceOverview && (
                <div className="bg-gradient-to-br from-blue-50 to-indigo-100 border border-blue-200 rounded-lg p-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">
                        📊 Real-time Compliance Overview
                    </h2>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {/* Overall Compliance */}
                        <div className="bg-white rounded-lg p-4 shadow-sm">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-600">Overall Compliance</p>
                                    <p className="text-3xl font-bold text-green-600">{complianceOverview.overallPassRate}%</p>
                                    <p className="text-xs text-gray-500">
                                        {complianceOverview.passedValidators}/{complianceOverview.totalValidators} validators passed
                                    </p>
                                </div>
                                <div className="text-3xl">🏆</div>
                            </div>
                        </div>

                        {/* AWS Resources Summary */}
                        <div className="bg-white rounded-lg p-4 shadow-sm">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-600">AWS Resources</p>
                                    <div className="text-sm space-y-1 mt-2">
                                        <div>Subnets: <span className="font-semibold">{complianceOverview.awsResources.subnets}</span></div>
                                        <div>KMS Keys: <span className="font-semibold">{complianceOverview.awsResources.kmsKeys}</span></div>
                                        <div>IAM Users: <span className="font-semibold">{complianceOverview.awsResources.iamUsers}</span></div>
                                        <div>IAM Roles: <span className="font-semibold">{complianceOverview.awsResources.iamRoles}</span></div>
                                    </div>
                                </div>
                                <div className="text-3xl">☁️</div>
                            </div>
                        </div>

                        {/* Security Resources */}
                        <div className="bg-white rounded-lg p-4 shadow-sm">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-600">Security & Monitoring</p>
                                    <div className="text-sm space-y-1 mt-2">
                                        <div>CloudTrail: <span className="font-semibold">{complianceOverview.awsResources.cloudtrailTrails}</span></div>
                                        <div>CloudWatch: <span className="font-semibold">{complianceOverview.awsResources.cloudwatchAlarms}</span></div>
                                        <div>Secrets: <span className="font-semibold">{complianceOverview.awsResources.secretsManagerSecrets}</span></div>
                                        <div>SNS Topics: <span className="font-semibold">{complianceOverview.awsResources.snsTopics}</span></div>
                                    </div>
                                </div>
                                <div className="text-3xl">🔒</div>
                            </div>
                        </div>

                        {/* Infrastructure */}
                        <div className="bg-white rounded-lg p-4 shadow-sm">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm font-medium text-gray-600">Infrastructure</p>
                                    <div className="text-sm space-y-1 mt-2">
                                        <div>Hosted Zones: <span className="font-semibold">{complianceOverview.awsResources.hostedZones}</span></div>
                                        <div>IAM Policies: <span className="font-semibold">{complianceOverview.awsResources.iamPolicies}</span></div>
                                        <div>CloudFormation: <span className="font-semibold">{complianceOverview.awsResources.cloudformationStacks}</span></div>
                                    </div>
                                </div>
                                <div className="text-3xl">🏗️</div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* KSI Categories Status */}
            <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                    📋 Validator Status
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(ksiCategories).map(([code, info]) => {
                        const result = complianceOverview?.categoryResults[code.toLowerCase()];
                        const isWorking = result && (result.passed || result.assertion === true || result.pass_rate === 100);
                        
                        return (
                            <div key={code} className={`border rounded-lg p-4 ${isWorking ? 'border-green-200 bg-green-50' : 'border-gray-200'}`}>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <div className="font-semibold text-lg text-blue-600">{code}</div>
                                        <div className="text-sm text-gray-600">{info.name}</div>
                                        {result && (
                                            <div className="text-xs mt-1">
                                                <span className={`px-2 py-1 rounded-full ${isWorking ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                                    {isWorking ? '✅ Passed' : '❌ Issues'}
                                                </span>
                                                {result.pass_rate !== undefined && (
                                                    <span className="ml-2 text-gray-600">
                                                        {result.pass_rate}% pass rate
                                                    </span>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                    <div className="text-2xl">{info.icon}</div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Execution History */}
            <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                    📈 Recent Executions
                </h2>
                
                {loading && executionHistory.length === 0 ? (
                    <div className="flex items-center justify-center py-8">
                        <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
                        <span className="ml-3 text-gray-600">Loading execution history...</span>
                    </div>
                ) : executionHistory.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                        No execution history found. Try running a validation first.
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Execution
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Status
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Validators
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Timestamp
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {executionHistory.map((execution) => (
                                    <tr 
                                        key={execution.execution_id} 
                                        className={`hover:bg-gray-50 cursor-pointer ${selectedExecutionId === execution.execution_id ? 'bg-blue-50' : ''}`}
                                        onClick={() => handleExecutionSelect(execution)}
                                    >
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-medium text-gray-900">
                                                {execution.execution_id?.slice(0, 8)}...
                                            </div>
                                            <div className="text-sm text-gray-500">
                                                {execution.tenant_id}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {getExecutionStatusDisplay(execution)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm text-gray-900">
                                                {execution.validators_completed?.length || 0} / 5
                                            </div>
                                            <div className="text-xs text-gray-500">
                                                {execution.validators_completed?.join(', ') || 'None'}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {formatTimestamp(execution.timestamp)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleExecutionSelect(execution);
                                                }}
                                                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                                                    selectedExecutionId === execution.execution_id
                                                        ? 'bg-blue-100 text-blue-800 border border-blue-200'
                                                        : 'text-blue-600 hover:text-blue-900 hover:bg-blue-50'
                                                }`}
                                            >
                                                {selectedExecutionId === execution.execution_id ? '✅ Selected' : 'View Details'}
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Detailed Validation Results */}
            {selectedExecutionId && (
                <div className="bg-white shadow rounded-lg p-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-4">
                        🔍 Detailed Validation Results
                        <span className="text-sm font-normal text-gray-500 ml-2">
                            ({selectedExecutionId.slice(0, 8)}...)
                        </span>
                    </h2>
                    
                    {loading ? (
                        <div className="flex items-center justify-center py-8">
                            <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
                            <span className="ml-3 text-gray-600">Loading detailed results...</span>
                        </div>
                    ) : validationResults.length > 0 ? (
                        <div className="space-y-6">
                            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                                <div className="flex items-center">
                                    <span className="text-green-600 text-xl mr-2">✅</span>
                                    <span className="font-medium text-green-800">
                                        Found {validationResults.length} validator result{validationResults.length !== 1 ? 's' : ''}
                                    </span>
                                </div>
                            </div>
                            
                            {validationResults.map((result, index) => (
                            <div key={index} className="border border-gray-200 rounded-lg p-6">
                                {/* Result Header */}
                                <div className="flex justify-between items-start mb-4">
                                    <div>
                                        <h3 className="text-lg font-semibold text-gray-900">
                                            {result.category || result.validator_name || `Validator ${index + 1}`}
                                        </h3>
                                        <p className="text-sm text-gray-600">
                                            Tenant: {result.tenant_id} | Execution: {result.execution_id?.slice(0, 8)}...
                                        </p>
                                    </div>
                                    <div className="flex space-x-2">
                                        <span className={`px-3 py-1 text-sm font-semibold rounded ${
                                            result.assertion === true || result.pass_rate === 100 ? 
                                            'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                        }`}>
                                            {result.assertion === true || result.pass_rate === 100 ? '✅ PASSED' : '❌ FAILED'}
                                        </span>
                                        {result.pass_rate !== undefined && (
                                            <span className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded">
                                                {result.pass_rate}% Pass Rate
                                            </span>
                                        )}
                                    </div>
                                </div>

                                {/* Summary Statistics */}
                                {result.summary && (
                                    <div className="bg-gray-50 rounded-lg p-4 mb-4">
                                        <h4 className="font-medium text-gray-900 mb-2">Summary</h4>
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                            <div>
                                                <span className="text-gray-500">Total KSIs:</span>
                                                <span className="ml-2 font-semibold">{result.summary.total_ksis || 0}</span>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Passed:</span>
                                                <span className="ml-2 font-semibold text-green-600">{result.summary.passed || 0}</span>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Failed:</span>
                                                <span className="ml-2 font-semibold text-red-600">{result.summary.failed || 0}</span>
                                            </div>
                                            <div>
                                                <span className="text-gray-500">Pass Rate:</span>
                                                <span className="ml-2 font-semibold">{result.summary.pass_rate || 0}%</span>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {/* Individual KSI Results */}
                                {result.individual_results && result.individual_results.length > 0 && (
                                    <div className="mb-4">
                                        <h4 className="font-medium text-gray-900 mb-3">
                                            Individual KSI Results ({result.individual_results.length})
                                        </h4>
                                        <div className="space-y-3">
                                            {result.individual_results.slice(0, 5).map((ksi, ksiIndex) => (
                                                <div key={ksiIndex} className="border border-gray-100 rounded-lg p-3">
                                                    <div className="flex justify-between items-center mb-2">
                                                        <div>
                                                            <span className="font-semibold">{ksi.ksi_id}</span>
                                                            {ksi.assertion_reason && (
                                                                <p className="text-sm text-gray-600 mt-1">{ksi.assertion_reason}</p>
                                                            )}
                                                        </div>
                                                        <span className={`px-2 py-1 text-xs font-semibold rounded ${
                                                            ksi.assertion ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                                        }`}>
                                                            {ksi.assertion ? 'PASS' : 'FAIL'}
                                                        </span>
                                                    </div>
                                                    
                                                    {/* AWS CLI Commands */}
                                                    {ksi.aws_cli_commands && ksi.aws_cli_commands.length > 0 && (
                                                        <div className="mt-2">
                                                            <p className="text-xs font-medium text-gray-700 mb-2">
                                                                AWS Resources ({ksi.aws_cli_commands.length}):
                                                            </p>
                                                            <div className="space-y-1">
                                                                {ksi.aws_cli_commands.slice(0, 3).map((cmd, cmdIndex) => (
                                                                    <div key={cmdIndex} className="bg-gray-50 rounded p-2">
                                                                        {cmd.response && (
                                                                            <div className="text-xs space-y-1">
                                                                                {Object.entries(cmd.response).slice(0, 3).map(([key, value]) => (
                                                                                    <div key={key}>
                                                                                        <span className="text-gray-600">{key}:</span>
                                                                                        <span className="ml-2 font-mono">
                                                                                            {Array.isArray(value) ? value.join(', ') : String(value).slice(0, 50)}
                                                                                        </span>
                                                                                    </div>
                                                                                ))}
                                                                            </div>
                                                                        )}
                                                                        <div className="text-xs text-gray-500 mt-1 font-mono">
                                                                            {cmd.command?.slice(0, 80)}...
                                                                        </div>
                                                                    </div>
                                                                ))}
                                                                {ksi.aws_cli_commands.length > 3 && (
                                                                    <div className="text-xs text-gray-500 text-center py-1">
                                                                        ... and {ksi.aws_cli_commands.length - 3} more commands
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                            {result.individual_results.length > 5 && (
                                                <div className="text-sm text-gray-500 text-center py-2">
                                                    ... and {result.individual_results.length - 5} more KSI results
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Raw Details (Collapsible) */}
                                {result.details && (
                                    <details className="mt-4">
                                        <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                                            🔍 View Raw Details
                                        </summary>
                                        <div className="mt-2 p-3 bg-gray-50 rounded text-xs overflow-x-auto">
                                            <pre className="whitespace-pre-wrap">
                                                {JSON.stringify(result.details, null, 2)}
                                            </pre>
                                        </div>
                                    </details>
                                )}
                            </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8">
                            <div className="text-gray-400 text-4xl mb-2">📋</div>
                            <p className="text-gray-600 mb-2">No detailed validation results available</p>
                            <p className="text-sm text-gray-500">
                                This execution may not have completed successfully or detailed results may not be stored.
                            </p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default KSIManager;
