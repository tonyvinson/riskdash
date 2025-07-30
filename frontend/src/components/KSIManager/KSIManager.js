import React, { useState, useEffect, useCallback, useRef } from 'react';
import ksiService, { getValidatorIcon } from '../../services/ksiService';
import './KSIManager.css';

const KSIManager = () => {
    // ✅ FIXED: Add ref to prevent React Strict Mode double execution
    const hasLoadedTenants = useRef(false);
    
    // State management
    const [selectedTenant, setSelectedTenant] = useState(''); // ✅ Start empty, set after tenants load
    const [availableTenants, setAvailableTenants] = useState([]);
    const [executionHistory, setExecutionHistory] = useState([]);
    const [currentKSIData, setCurrentKSIData] = useState(null);
    const [complianceOverview, setComplianceOverview] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);
    const [expandedExecutionId, setExpandedExecutionId] = useState(null);
    
    // ✅ NEW: State for CLI command details
    const [validatorDetails, setValidatorDetails] = useState({});
    const [loadingValidatorDetails, setLoadingValidatorDetails] = useState({});
    const [expandedValidatorId, setExpandedValidatorId] = useState(null);

    // ✅ FIXED: Real-time compliance calculation based on actual CLI details
    const updateComplianceFromCLIDetails = useCallback((executionId, cliDetails) => {
        if (!cliDetails || cliDetails.length === 0) return;

        const validatorsWithCLI = cliDetails.length;
        const successfulValidators = cliDetails.filter(detail => {
            return detail.assertion === true || 
                   (detail.cli_command_details && detail.cli_command_details.some(cmd => cmd.success === true));
        }).length;

        const realCompliance = Math.round((validatorsWithCLI / 5) * 100);

        console.log('✅ FIXED: Updated compliance from CLI details:', {
            validatorsWithCLI,
            successfulValidators,
            realCompliance,
            executionId
        });

        setComplianceOverview(prev => ({
            ...prev,
            totalValidators: 5,
            completedValidators: validatorsWithCLI,
            pendingValidators: 5 - validatorsWithCLI,
            overallCompliance: realCompliance,
            passedValidators: successfulValidators,
            lastValidation: new Date().toISOString(),
            cliDetailsLoaded: true
        }));
    }, []);

    // ✅ FIXED: Load tenants with proper deduplication
    const loadTenants = useCallback(async () => {
        // ✅ PREVENT React Strict Mode double execution
        if (hasLoadedTenants.current) {
            console.log('🏢 Tenants already loaded, skipping...');
            return;
        }
        hasLoadedTenants.current = true;
        
        try {
            setLoading(true);
            setError(null);
            console.log('🏢 Loading tenants from API...');
            
            const response = await ksiService.getTenants();
            console.log('🏢 Tenants response:', response);
            
            // ✅ FIXED: Parse the actual API response structure
            let tenants = [];
            if (response && response.tenants && Array.isArray(response.tenants)) {
                tenants = response.tenants;
                console.log('✅ Found tenants array with', tenants.length, 'tenants');
                
                // ✅ FIXED: Format tenants and DEDUPLICATE by tenant_id
                const formattedTenants = tenants.map(tenant => ({
                    tenant_id: tenant.tenant_id,
                    display_name: tenant.tenant_name || formatTenantDisplayName(tenant.tenant_id),
                    ksi_count: tenant.ksi_count || tenant.total_ksis || 5
                }));
                
                // ✅ CRITICAL: Deduplicate by tenant_id to prevent React key warnings
                const uniqueTenants = formattedTenants.filter((tenant, index, self) => 
                    index === self.findIndex(t => t.tenant_id === tenant.tenant_id)
                );
                
                setAvailableTenants(uniqueTenants);
                console.log('✅ Loaded', uniqueTenants.length, 'unique tenants with correct field mapping');
                
                // ✅ Set initial tenant if none selected
                if (!selectedTenant && uniqueTenants.length > 0) {
                    // Try to find riskuity-production first, otherwise use first tenant
                    const productionTenant = uniqueTenants.find(t => t.tenant_id.includes('production') || t.tenant_id.includes('riskuity'));
                    const initialTenant = productionTenant || uniqueTenants[0];
                    setSelectedTenant(initialTenant.tenant_id);
                    console.log('✅ Set initial tenant to:', initialTenant.tenant_id);
                }
                
            } else if (response && Array.isArray(response)) {
                tenants = response;
                console.log('✅ Response is array of tenants');
                const formattedTenants = tenants.map(tenant => ({
                    tenant_id: tenant.tenant_id,
                    display_name: tenant.tenant_name || formatTenantDisplayName(tenant.tenant_id),
                    ksi_count: tenant.ksi_count || tenant.total_ksis || 5
                }));
                
                // ✅ Deduplicate here too
                const uniqueTenants = formattedTenants.filter((tenant, index, self) => 
                    index === self.findIndex(t => t.tenant_id === tenant.tenant_id)
                );
                
                setAvailableTenants(uniqueTenants);
            } else {
                console.log('🏢 No valid tenants in API response, using fallback');
                // ✅ ONLY use fallback if API actually failed - NO duplicates
                setAvailableTenants([
                    { tenant_id: 'riskuity-production', display_name: 'Riskuity Production', ksi_count: 5 }
                ]);
            }
            
        } catch (err) {
            console.error('❌ Error loading tenants:', err);
            setError(`Failed to load tenants: ${err.message}`);
            // ✅ Only use fallback on actual API errors - NO duplicates
            const fallbackTenants = [
                { tenant_id: 'riskuity-production', display_name: 'Riskuity Production', ksi_count: 5 }
            ];
            setAvailableTenants(fallbackTenants);
            if (!selectedTenant) {
                setSelectedTenant('riskuity-production');
            }
        } finally {
            setLoading(false);
        }
    }, []); // ✅ FIXED: Empty dependency array to prevent multiple calls

    // Format tenant display names
    const formatTenantDisplayName = (tenantId) => {
        if (!tenantId) return 'Unknown Tenant';
        
        // Convert kebab-case to Title Case
        return tenantId
            .split('-')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    };

    // Fetch current KSI validation data
    const fetchCurrentKSIData = useCallback(async () => {
        if (!selectedTenant || selectedTenant === '') return;
        
        try {
            setLoading(true);
            setError(null);
            console.log(`🔍 Loading execution history for tenant: ${selectedTenant}`);
            
            // ✅ FIXED: Use the correct method with strict tenant filtering
            const response = await ksiService.getExecutionHistory(selectedTenant, 20); // Get more recent data
            console.log('📊 API Response:', response);
            
            if (response.success && response.data) {
                const executions = response.data.executions || [];
                console.log(`✅ Found ${executions.length} executions for tenant: ${selectedTenant}`);
                
                setExecutionHistory(executions);
                setCurrentKSIData(response.data);
                
                // ✅ FIXED: Create INITIAL compliance overview (will be updated by CLI details)
                if (executions.length > 0) {
                    const latestExecution = executions[0]; // Already sorted newest first
                    
                    console.log('📊 Creating INITIAL compliance overview from execution:', latestExecution.execution_id);
                    
                    // ✅ FIXED: Don't rely on validators_completed - use placeholder until CLI loads
                    const overview = {
                        totalValidators: 5, // CNA, SVC, IAM, MLA, CMT
                        completedValidators: 0, // Will be updated by CLI details
                        pendingValidators: 5, // Will be updated by CLI details
                        totalKSIs: latestExecution.total_ksis_validated || 0,
                        passedKSIs: latestExecution.total_ksis_validated || 0,
                        lastValidation: latestExecution.timestamp,
                        overallCompliance: 0, // Will be updated by CLI details
                        cliDetailsLoaded: false,
                        latestExecutionId: latestExecution.execution_id
                    };
                    
                    setComplianceOverview(overview);
                    console.log('📊 INITIAL compliance overview created (will be updated by CLI):', overview);
                    
                    // ✅ FIXED: Auto-load CLI details for latest execution to get real compliance
                    if (!expandedExecutionId) {
                        setExpandedExecutionId(latestExecution.execution_id);
                        // CLI details will be fetched automatically when expandedExecutionId changes
                    }
                } else {
                    console.log('📊 No executions found, creating empty overview');
                    setComplianceOverview({
                        totalValidators: 5,
                        completedValidators: 0,
                        pendingValidators: 5,
                        totalKSIs: 0,
                        passedKSIs: 0,
                        lastValidation: 'Never',
                        overallCompliance: 0,
                        cliDetailsLoaded: false
                    });
                }
            } else {
                console.log('⚠️ No execution data found');
                setExecutionHistory([]);
                setCurrentKSIData(null);
                setComplianceOverview({
                    totalValidators: 5,
                    completedValidators: 0,
                    pendingValidators: 5,
                    totalKSIs: 0,
                    passedKSIs: 0,
                    lastValidation: 'Never',
                    overallCompliance: 0,
                    cliDetailsLoaded: false
                });
            }
            
        } catch (err) {
            console.error('❌ Error fetching execution history:', err);
            setError(`Failed to fetch execution data: ${err.message}`);
            setExecutionHistory([]);
            setComplianceOverview(null);
        } finally {
            setLoading(false);
        }
    }, [selectedTenant, expandedExecutionId]);

    // ✅ FIXED: Fetch validator CLI command details and UPDATE COMPLIANCE
    const fetchValidatorDetails = async (executionId, validators = null) => {
        const detailsKey = executionId;
        
        if (validatorDetails[detailsKey]) {
            console.log('✅ Validator details already loaded for:', executionId);
            // Still update compliance if details exist
            updateComplianceFromCLIDetails(executionId, validatorDetails[detailsKey]);
            return;
        }
        
        try {
            setLoadingValidatorDetails(prev => ({...prev, [detailsKey]: true}));
            
            // ✅ FIXED: Always try ALL validators, not just completed ones
            const allValidators = ['cna', 'svc', 'iam', 'mla', 'cmt'];
            
            console.log('🔍 Fetching validator CLI details for execution:', executionId);
            console.log('🔍 Trying all validators:', allValidators);
            
            const response = await ksiService.getAllValidatorDetails(executionId, allValidators);
            
            if (response.success) {
                // Filter out validators that had errors
                const successfulValidators = response.data.filter(v => !v.error && v.cli_command_details?.length > 0);
                
                setValidatorDetails(prev => ({
                    ...prev,
                    [detailsKey]: successfulValidators
                }));
                console.log('✅ Loaded CLI details for', successfulValidators.length, 'validators:', 
                          successfulValidators.map(v => v.validator.toUpperCase()));
                
                // ✅ FIXED: Update compliance overview with real CLI data
                updateComplianceFromCLIDetails(executionId, successfulValidators);
            }
            
        } catch (error) {
            console.error('❌ Failed to fetch validator details:', error);
            setError(`Failed to load CLI details: ${error.message}`);
        } finally {
            setLoadingValidatorDetails(prev => ({...prev, [detailsKey]: false}));
        }
    };

    // ✅ FIXED: Trigger validation with proper success handling
    const triggerValidation = async () => {
        if (!selectedTenant || selectedTenant === '') {
            setError('Please select a tenant first');
            return;
        }
        
        try {
            setLoading(true);
            setError(null);
            setSuccessMessage(null);
            
            console.log(`🚀 Triggering validation for tenant: ${selectedTenant}`);
            
            const response = await ksiService.triggerValidation(selectedTenant);
            console.log('🚀 Validation response:', response);
            
            // ✅ FIXED: Check for success properly
            if (response.success || response.execution_id) {
                setSuccessMessage(`✅ Validation started successfully! Execution ID: ${response.execution_id || 'N/A'}`);
                
                // ✅ FIXED: Show optimistic loading state
                setComplianceOverview({
                    totalValidators: 5,
                    completedValidators: 0, // Will be updated when CLI details load
                    pendingValidators: 5,
                    totalKSIs: response.total_ksis || 5,
                    passedKSIs: 0, // Will be updated when CLI details load
                    lastValidation: new Date().toISOString(),
                    overallCompliance: 0, // Will be updated when CLI details load
                    cliDetailsLoaded: false
                });

                // Add the new execution to history immediately
                const newExecution = {
                    execution_id: response.execution_id,
                    tenant_id: response.tenant_id || selectedTenant,
                    timestamp: response.timestamp || new Date().toISOString(),
                    status: response.status || 'COMPLETED',
                    trigger_source: 'manual',
                    validators_completed: [], // Will be updated by CLI details
                    total_ksis_validated: response.total_ksis || 5
                };
                
                setExecutionHistory(prev => [newExecution, ...prev]);
                
                // Auto-expand the new execution to load CLI details
                setExpandedExecutionId(response.execution_id);
                
                // Also refresh from API in background after delay
                setTimeout(() => {
                    fetchCurrentKSIData();
                }, 5000);
            } else {
                throw new Error(response.message || 'Validation failed with unknown error');
            }
            
        } catch (err) {
            console.error('🚀 Validation error:', err);
            setError(`Failed to trigger validation: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Handle tenant change
    const handleTenantChange = (newTenant) => {
        console.log('🔄 Tenant changed to:', newTenant);
        setSelectedTenant(newTenant);
        setError(null);
        setSuccessMessage(null);
        setExecutionHistory([]);
        setComplianceOverview(null);
        setCurrentKSIData(null);
        setValidatorDetails({}); // ✅ Clear CLI details on tenant change
        setExpandedExecutionId(null);
        setExpandedValidatorId(null);
    };

    // ✅ FIXED: Load tenants on component mount - ONCE only
    useEffect(() => {
        loadTenants();
    }, []); // ✅ Empty dependency array - load only once

    // Load data when tenant changes
    useEffect(() => {
        if (selectedTenant && selectedTenant !== '' && availableTenants.length > 0) {
            fetchCurrentKSIData();
        }
    }, [selectedTenant, availableTenants.length, fetchCurrentKSIData]);

    // ✅ FIXED: Auto-fetch CLI details when execution is expanded
    useEffect(() => {
        if (expandedExecutionId) {
            fetchValidatorDetails(expandedExecutionId);
        }
    }, [expandedExecutionId]);

    // Auto-clear messages after 5 seconds
    useEffect(() => {
        if (successMessage) {
            const timer = setTimeout(() => setSuccessMessage(null), 5000);
            return () => clearTimeout(timer);
        }
    }, [successMessage]);

    const formatTimestamp = (timestamp) => {
        if (!timestamp || timestamp === 'Never') return timestamp;
        try {
            return new Date(timestamp).toLocaleString();
        } catch (e) {
            return timestamp;
        }
    };

    const getStatusColor = (status) => {
        switch (status?.toLowerCase()) {
            case 'completed': case 'success': case 'passed':
                return 'text-green-600 bg-green-100';
            case 'failed': case 'error':
                return 'text-red-600 bg-red-100';
            case 'running': case 'in_progress':
                return 'text-blue-600 bg-blue-100';
            default:
                return 'text-gray-600 bg-gray-100';
        }
    };

    const toggleExecutionDetails = async (executionId) => {
        const isExpanding = expandedExecutionId !== executionId;
        setExpandedExecutionId(isExpanding ? executionId : null);
        
        // CLI details will be fetched automatically via useEffect when expandedExecutionId changes
    };

    const toggleValidatorDetails = (validatorId) => {
        setExpandedValidatorId(expandedValidatorId === validatorId ? null : validatorId);
    };

    // ✅ NEW: Render CLI command details
    const renderCliCommandDetails = (cliDetails, validatorType) => {
        if (!cliDetails || cliDetails.length === 0) {
            return (
                <div className="text-sm text-gray-500 italic">
                    No CLI command details available
                </div>
            );
        }

        return (
            <div className="space-y-3">
                {cliDetails.map((cmd, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-4 border">
                        <div className="flex items-center justify-between mb-2">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                cmd.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                                {cmd.success ? '✅ SUCCESS' : '❌ FAILED'}
                            </span>
                            <span className="text-xs text-gray-500">
                                {validatorType} Validation
                            </span>
                        </div>
                        
                        <div className="mb-3">
                            <label className="text-xs font-medium text-gray-700">Command:</label>
                            <div className="bg-gray-800 text-green-400 p-2 rounded text-sm font-mono mt-1">
                                {cmd.command}
                            </div>
                        </div>
                        
                        {cmd.note && (
                            <div className="mb-3">
                                <label className="text-xs font-medium text-gray-700">Purpose:</label>
                                <div className="text-sm text-gray-600 mt-1">{cmd.note}</div>
                            </div>
                        )}
                        
                        {cmd.data && (
                            <div>
                                <label className="text-xs font-medium text-gray-700">AWS Resources Discovered:</label>
                                <div className="mt-1 p-3 bg-white rounded border">
                                    {cmd.data.log_group_count && (
                                        <div className="mb-2">
                                            <span className="font-medium text-green-600">
                                                {cmd.data.log_group_count} CloudWatch Log Groups Found
                                            </span>
                                        </div>
                                    )}
                                    
                                    {cmd.data.log_group_names && cmd.data.log_group_names.length > 0 && (
                                        <div>
                                            <details className="text-sm">
                                                <summary className="cursor-pointer font-medium text-gray-700 hover:text-gray-900">
                                                    View Log Groups ({cmd.data.log_group_names.length})
                                                </summary>
                                                <div className="mt-2 max-h-32 overflow-y-auto">
                                                    <ul className="space-y-1 text-xs">
                                                        {cmd.data.log_group_names.slice(0, 10).map((logGroup, idx) => (
                                                            <li key={idx} className="font-mono text-gray-600">
                                                                {logGroup}
                                                            </li>
                                                        ))}
                                                        {cmd.data.log_group_names.length > 10 && (
                                                            <li className="text-gray-500 italic">
                                                                ... and {cmd.data.log_group_names.length - 10} more
                                                            </li>
                                                        )}
                                                    </ul>
                                                </div>
                                            </details>
                                        </div>
                                    )}
                                    
                                    {/* Handle other data types */}
                                    {!cmd.data.log_group_count && (
                                        <pre className="text-xs text-gray-600 whitespace-pre-wrap max-h-32 overflow-y-auto">
                                            {JSON.stringify(cmd.data, null, 2)}
                                        </pre>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
            {/* Header */}
            <div className="bg-white shadow-sm border-b">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="py-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <h1 className="text-3xl font-bold text-gray-900">🛡️ Enterprise KSI Validator</h1>
                                <p className="text-gray-600 mt-1">FedRAMP 20x Key Security Indicator Validation Platform</p>
                            </div>
                            <div className="text-sm text-gray-500">
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                    ✅ Production Ready
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Tenant Selection & Actions */}
                <div className="bg-white rounded-lg shadow mb-8 p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-semibold text-gray-900">Tenant Management</h2>
                        <div className="flex space-x-3">
                            <button
                                onClick={() => {
                                    hasLoadedTenants.current = false; // ✅ Reset flag for manual refresh
                                    loadTenants();
                                }}
                                disabled={loading}
                                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                            >
                                {loading ? '🔄' : '🔄 Refresh'}
                            </button>
                            
                            {/* Trigger Validation */}
                            <button
                                onClick={triggerValidation}
                                disabled={loading}
                                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                            >
                                {loading ? (
                                    <>
                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                        <span>Running...</span>
                                    </>
                                ) : (
                                    <>
                                        <span>🚀 Trigger Validation</span>
                                    </>
                                )}
                            </button>
                        </div>
                    </div>

                    {/* Tenant Selector */}
                    <div className="flex items-center space-x-4">
                        <label htmlFor="tenant-select" className="text-sm font-medium text-gray-700">
                            Select Tenant:
                        </label>
                        <select
                            id="tenant-select"
                            value={selectedTenant}
                            onChange={(e) => handleTenantChange(e.target.value)}
                            className="block w-full max-w-xs rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        >
                            {!selectedTenant && <option value="">Select a tenant...</option>}
                            {availableTenants.map((tenant) => (
                                <option key={tenant.tenant_id} value={tenant.tenant_id}>
                                    {tenant.display_name} ({tenant.ksi_count} KSIs)
                                </option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* Error Display */}
                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
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

                {/* Success Display */}
                {successMessage && (
                    <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-6">
                        <div className="flex">
                            <div className="flex-shrink-0">
                                <span className="text-green-400 text-xl">✅</span>
                            </div>
                            <div className="ml-3">
                                <h3 className="text-sm font-medium text-green-800">Success</h3>
                                <div className="mt-1 text-sm text-green-700">{successMessage}</div>
                            </div>
                            <div className="ml-auto">
                                <button
                                    onClick={() => setSuccessMessage(null)}
                                    className="text-green-400 hover:text-green-600"
                                >
                                    ✕
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* ✅ FIXED: Real-time Compliance Overview based on CLI Details */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div className="bg-white overflow-hidden shadow rounded-lg">
                        <div className="p-5">
                            <div className="flex items-center">
                                <div className="flex-shrink-0">
                                    <div className="text-2xl">📊</div>
                                </div>
                                <div className="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt className="text-sm font-medium text-gray-500 truncate">Overall Compliance</dt>
                                        <dd className="text-3xl font-bold text-gray-900">
                                            {complianceOverview?.overallCompliance || 0}%
                                        </dd>
                                        {complianceOverview?.cliDetailsLoaded && (
                                            <dd className="text-xs text-green-600">✅ Real-time data</dd>
                                        )}
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white overflow-hidden shadow rounded-lg">
                        <div className="p-5">
                            <div className="flex items-center">
                                <div className="flex-shrink-0">
                                    <div className="text-2xl">✅</div>
                                </div>
                                <div className="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt className="text-sm font-medium text-gray-500 truncate">Completed Validators</dt>
                                        <dd className="text-3xl font-bold text-green-600">
                                            {complianceOverview?.completedValidators || 0}
                                        </dd>
                                        <dd className="text-sm text-gray-500">of {complianceOverview?.totalValidators || 5} total</dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white overflow-hidden shadow rounded-lg">
                        <div className="p-5">
                            <div className="flex items-center">
                                <div className="flex-shrink-0">
                                    <div className="text-2xl">⏳</div>
                                </div>
                                <div className="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt className="text-sm font-medium text-gray-500 truncate">Pending Validators</dt>
                                        <dd className="text-3xl font-bold text-yellow-600">
                                            {complianceOverview?.pendingValidators || 5}
                                        </dd>
                                        <dd className="text-sm text-gray-500">Awaiting validation</dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white overflow-hidden shadow rounded-lg">
                        <div className="p-5">
                            <div className="flex items-center">
                                <div className="flex-shrink-0">
                                    <div className="text-2xl">🕐</div>
                                </div>
                                <div className="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt className="text-sm font-medium text-gray-500 truncate">Last Validation</dt>
                                        <dd className="text-lg font-bold text-gray-900">
                                            {complianceOverview?.lastValidation === 'Never' ? 'Never' : 
                                             formatTimestamp(complianceOverview?.lastValidation)?.split(' ')[0] || 'N/A'}
                                        </dd>
                                        <dd className="text-sm text-gray-500">
                                            {complianceOverview?.lastValidation === 'Never' ? 'No validation data' : 
                                             formatTimestamp(complianceOverview?.lastValidation)?.split(' ')[1] || ''}
                                        </dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* ✅ FIXED: KSI Categories Status - shows real completion from CLI */}
                <div className="bg-white shadow rounded-lg mb-8">
                    <div className="px-6 py-4 border-b border-gray-200">
                        <h3 className="text-lg font-medium text-gray-900">KSI Validation Status</h3>
                        <p className="text-sm text-gray-500">FedRAMP 20x Key Security Indicators by Category</p>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 divide-y sm:divide-y-0 sm:divide-x divide-gray-200">
                        {['CNA', 'SVC', 'IAM', 'MLA', 'CMT'].map((category) => {
                            // ✅ FIXED: Check if validator has CLI details (real completion)
                            const latestExecutionId = complianceOverview?.latestExecutionId;
                            const hasCliDetails = latestExecutionId && 
                                                 validatorDetails[latestExecutionId]?.some(v => 
                                                     v.validator.toUpperCase() === category);
                            
                            return (
                                <div key={category} className="px-6 py-5">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <div className="flex items-center">
                                                <span className="text-lg mr-2">{getValidatorIcon(category.toLowerCase())}</span>
                                                <span className="font-medium text-gray-900">{category}</span>
                                            </div>
                                            <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-2 ${
                                                hasCliDetails ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                                            }`}>
                                                {hasCliDetails ? '✅ COMPLETED' : '⏳ PENDING'}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Execution History */}
                <div className="bg-white shadow rounded-lg">
                    <div className="px-6 py-4 border-b border-gray-200">
                        <h3 className="text-lg font-medium text-gray-900">Validation Execution History</h3>
                        <p className="text-sm text-gray-500">Recent validation runs for {selectedTenant}</p>
                    </div>
                    <div className="overflow-hidden">
                        {executionHistory.length === 0 ? (
                            <div className="px-6 py-12 text-center">
                                <div className="text-gray-400 text-4xl mb-4">📋</div>
                                <h3 className="text-lg font-medium text-gray-900 mb-2">No execution history found</h3>
                                <p className="text-gray-500 mb-4">No validation runs have been executed for this tenant yet.</p>
                                <button
                                    onClick={triggerValidation}
                                    disabled={loading}
                                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                                >
                                    🚀 Run First Validation
                                </button>
                            </div>
                        ) : (
                            <div className="divide-y divide-gray-200">
                                {executionHistory.slice(0, 10).map((execution) => (
                                    <div key={execution.execution_id} className="px-6 py-4">
                                        <div className="flex items-center justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center space-x-3">
                                                    <span className="text-sm font-medium text-gray-900">
                                                        {execution.execution_id?.substring(0, 8)}...
                                                    </span>
                                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(execution.status)}`}>
                                                        {execution.status || 'UNKNOWN'}
                                                    </span>
                                                    <span className="text-sm text-gray-500">
                                                        {formatTimestamp(execution.timestamp)}
                                                    </span>
                                                </div>
                                                <div className="mt-1 text-sm text-gray-600">
                                                    {/* ✅ FIXED: Show CLI-based validator count if available */}
                                                    {validatorDetails[execution.execution_id] ? 
                                                        `${validatorDetails[execution.execution_id].length} validators with CLI details` :
                                                        `${execution.validators_completed?.length || 0} validators completed`
                                                    }
                                                    {execution.total_ksis_validated ? ` • ${execution.total_ksis_validated} KSIs validated` : ''}
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => toggleExecutionDetails(execution.execution_id)}
                                                className="text-indigo-600 hover:text-indigo-900 text-sm font-medium"
                                            >
                                                {expandedExecutionId === execution.execution_id ? 'Hide Details' : 'View Details'}
                                            </button>
                                        </div>
                                        
                                        {expandedExecutionId === execution.execution_id && (
                                            <div className="mt-4 p-4 bg-gray-50 rounded-md">
                                                <h4 className="text-sm font-medium text-gray-900 mb-2">Execution Details</h4>
                                                <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                                                    <div>
                                                        <span className="font-medium">Execution ID:</span> {execution.execution_id}
                                                    </div>
                                                    <div>
                                                        <span className="font-medium">Tenant:</span> {execution.tenant_id}
                                                    </div>
                                                    <div>
                                                        <span className="font-medium">Trigger Source:</span> {execution.trigger_source || 'manual'}
                                                    </div>
                                                    <div>
                                                        <span className="font-medium">Timestamp:</span> {formatTimestamp(execution.timestamp)}
                                                    </div>
                                                </div>
                                                
                                                {/* ✅ FIXED: Show CLI details if available, fallback to completed validators */}
                                                {validatorDetails[execution.execution_id] && validatorDetails[execution.execution_id].length > 0 ? (
                                                    <div className="mb-4">
                                                        <span className="text-sm font-medium text-gray-900">Validators with CLI Details:</span>
                                                        <div className="mt-1 flex flex-wrap gap-2">
                                                            {validatorDetails[execution.execution_id].map(validator => (
                                                                <span
                                                                    key={validator.validator}
                                                                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                                                                >
                                                                    {getValidatorIcon(validator.validator)} {validator.validator.toUpperCase()}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                ) : execution.validators_completed && execution.validators_completed.length > 0 && (
                                                    <div className="mb-4">
                                                        <span className="text-sm font-medium text-gray-900">Completed Validators:</span>
                                                        <div className="mt-1 flex flex-wrap gap-2">
                                                            {execution.validators_completed.map(validator => (
                                                                <span
                                                                    key={validator}
                                                                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                                                                >
                                                                    {getValidatorIcon(validator)} {validator.toUpperCase()}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* CLI Command Details Section */}
                                                {(validatorDetails[execution.execution_id] && validatorDetails[execution.execution_id].length > 0) && (
                                                    <div className="border-t pt-4">
                                                        <h5 className="text-sm font-medium text-gray-900 mb-3">
                                                            🔍 CLI Command Details & AWS Resource Discovery
                                                        </h5>
                                                        
                                                        <div className="space-y-4">
                                                            {validatorDetails[execution.execution_id].map((validator) => (
                                                                <div key={validator.validator} className="border rounded-lg">
                                                                    <div className="px-4 py-3 bg-gray-100 border-b">
                                                                        <button
                                                                            onClick={() => toggleValidatorDetails(validator.validator)}
                                                                            className="flex items-center justify-between w-full text-left"
                                                                        >
                                                                            <div className="flex items-center space-x-2">
                                                                                <span>{getValidatorIcon(validator.validator)}</span>
                                                                                <span className="font-medium text-gray-900">
                                                                                    {validator.validator.toUpperCase()} Validator
                                                                                </span>
                                                                                <span className="text-sm text-gray-500">
                                                                                    ({validator.ksi_id})
                                                                                </span>
                                                                                {validator.cli_command_details?.length > 0 && (
                                                                                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                                                                        {validator.cli_command_details.length} Commands
                                                                                    </span>
                                                                                )}
                                                                            </div>
                                                                            <span className="text-gray-400">
                                                                                {expandedValidatorId === validator.validator ? '▼' : '▶'}
                                                                            </span>
                                                                        </button>
                                                                    </div>
                                                                    
                                                                    {expandedValidatorId === validator.validator && (
                                                                        <div className="p-4">
                                                                            {validator.assertion !== undefined && (
                                                                                <div className="mb-3">
                                                                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                                                                        validator.assertion ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                                                                    }`}>
                                                                                        {validator.assertion ? '✅ PASSED' : '❌ FAILED'}
                                                                                    </span>
                                                                                    {validator.assertion_reason && (
                                                                                        <div className="text-sm text-gray-600 mt-1">
                                                                                            {validator.assertion_reason}
                                                                                        </div>
                                                                                    )}
                                                                                </div>
                                                                            )}
                                                                            
                                                                            {validator.error ? (
                                                                                <div className="text-sm text-red-600">
                                                                                    Error: {validator.error}
                                                                                </div>
                                                                            ) : (
                                                                                renderCliCommandDetails(validator.cli_command_details, validator.validator.toUpperCase())
                                                                            )}
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* ✅ Success indicator for CLI details */}
                                                {validatorDetails[execution.execution_id] && validatorDetails[execution.execution_id].length > 0 && (
                                                    <div className="mt-3 p-2 bg-green-50 rounded border border-green-200">
                                                        <div className="text-sm text-green-800">
                                                            ✅ Found CLI command details for {validatorDetails[execution.execution_id].length} validators
                                                        </div>
                                                    </div>
                                                )}

                                                {/* ✅ Loading state for CLI details */}
                                                {loadingValidatorDetails[execution.execution_id] && (
                                                    <div className="border-t pt-4">
                                                        <div className="flex items-center justify-center py-4">
                                                            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mr-3"></div>
                                                            <span className="text-sm text-gray-600">Loading CLI command details...</span>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default KSIManager;
