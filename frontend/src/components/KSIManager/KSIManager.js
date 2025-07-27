// frontend/src/components/KSIManager/KSIManager.js - Enhanced with CLI Commands Display
import React, { useState, useEffect, useCallback } from 'react';
import { ksiService } from '../../services/ksiService';

const KSIManager = () => {
    const [loading, setLoading] = useState(false);
    const [selectedTenant, setSelectedTenant] = useState('default');
    const [executionHistory, setExecutionHistory] = useState([]);
    const [validationResults, setValidationResults] = useState([]);
    const [error, setError] = useState(null);
    const [lastExecution, setLastExecution] = useState(null);
    const [selectedExecutionId, setSelectedExecutionId] = useState(null);

    // KSI categories for display
    const ksiCategories = {
        'CNA': 'Configuration & Network Architecture',
        'SVC': 'Service Configuration',
        'IAM': 'Identity & Access Management', 
        'MLA': 'Monitoring, Logging & Alerting',
        'CMT': 'Configuration Management & Tracking'
    };

    const fetchExecutionHistory = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            
            const response = await ksiService.getExecutionHistory(selectedTenant, 10);
            console.log('Execution History Response:', response);
            
            setExecutionHistory(response.executions || response.items || []);
        } catch (err) {
            console.error('Error fetching execution history:', err);
            setError(`Failed to fetch execution history: ${err.message}`);
        } finally {
            setLoading(false);
        }
    }, [selectedTenant]);

    useEffect(() => {
        fetchExecutionHistory();
    }, [fetchExecutionHistory]);

    const fetchValidationResults = async (executionId) => {
        try {
            setLoading(true);
            setError(null);
            setSelectedExecutionId(executionId);
            
            console.log('🔍 Fetching results for execution:', executionId);
            
            // Find the execution in our current data first
            const execution = executionHistory.find(exec => exec.execution_id === executionId);
            
            if (execution && execution.validation_results) {
                console.log('🎯 Found validation results in execution data:', execution.validation_results);
                
                // Parse the nested validation results
                const resultsData = execution.validation_results.map(validationResult => {
                    let resultBody = validationResult.result?.body;
                    let parsedBody = null;
                    
                    // Try to parse the JSON body if it's a string
                    if (typeof resultBody === 'string') {
                        try {
                            parsedBody = JSON.parse(resultBody);
                        } catch (e) {
                            console.warn('Could not parse result body:', resultBody);
                            parsedBody = { raw: resultBody };
                        }
                    } else {
                        parsedBody = resultBody || {};
                    }
                    
                    return {
                        ksi_id: `${validationResult.validator?.toUpperCase()} Validator`,
                        description: `${validationResult.validator?.toUpperCase()} Category Validation`,
                        status: validationResult.status || 'Unknown',
                        validator: validationResult.validator,
                        function_name: validationResult.function_name,
                        details: parsedBody,
                        ksis_validated: parsedBody.ksis_validated || 0,
                        summary: parsedBody.summary || null,
                        individual_results: parsedBody.results || []
                    };
                });
                
                console.log('📊 Processed Results Data:', resultsData);
                setValidationResults(resultsData);
            } else {
                // Try to fetch from API if not in current data
                const response = await ksiService.getValidationResults(selectedTenant, executionId);
                console.log('🎯 API Validation Results Response:', response);
                
                let resultsData = response.results || response.items || [];
                setValidationResults(resultsData);
                
                if (resultsData.length === 0) {
                    setError('No validation results found for this execution');
                }
            }
            
        } catch (err) {
            console.error('Error fetching validation results:', err);
            setError(`Failed to fetch validation results: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const parseCliCommand = (cliCommand) => {
        if (!cliCommand || cliCommand === 'No command information') {
            return { summary: 'No commands', commands: [] };
        }

        // Parse command string like "4 commands (3 successful): aws iam list-users --output json; aws iam list-mfa-devices --output json (+2 more)"
        const match = cliCommand.match(/(\d+) commands \((\d+) successful\): (.+)/);
        if (match) {
            const [, total, successful, commandsStr] = match;
            const commands = commandsStr.split(';').map(cmd => cmd.trim());
            
            return {
                total: parseInt(total),
                successful: parseInt(successful),
                failed: parseInt(total) - parseInt(successful),
                commands: commands
            };
        }

        // Handle single command case or different format
        return {
            summary: cliCommand,
            commands: [cliCommand]
        };
    };

    const triggerValidation = async () => {
        try {
            setLoading(true);
            setError(null);
            
            console.log(`Triggering validation for tenant: ${selectedTenant}`);
            
            const response = await ksiService.triggerValidation(
                selectedTenant, 
                'manual'
            );
            
            console.log('Validation Triggered:', response);
            setLastExecution(response);
            
            // Show success message
            alert(`✅ KSI validation triggered successfully!\nExecution ID: ${response.execution_id}`);
            
            // Refresh execution history after a brief delay
            setTimeout(() => {
                fetchExecutionHistory();
            }, 2000);
            
        } catch (err) {
            console.error('Error triggering validation:', err);
            setError(`Failed to trigger validation: ${err.message}`);
            alert(`❌ Failed to trigger validation: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const formatTimestamp = (timestamp) => {
        if (!timestamp) return 'N/A';
        return new Date(timestamp).toLocaleString();
    };

    const getStatusColor = (status) => {
        switch (status?.toLowerCase()) {
            case 'pass': case 'passed': case 'success': case 'completed':
                return 'text-green-600 bg-green-100';
            case 'fail': case 'failed': case 'error':
                return 'text-red-600 bg-red-100';
            case 'running': case 'in_progress': case 'triggered':
                return 'text-blue-600 bg-blue-100';
            case 'warning': case 'partial':
                return 'text-yellow-600 bg-yellow-100';
            default:
                return 'text-gray-600 bg-gray-100';
        }
    };

    const closeResults = () => {
        setValidationResults([]);
        setSelectedExecutionId(null);
    };

    return (
        <div className="max-w-7xl mx-auto p-6 space-y-6">
            {/* Header */}
            <div className="bg-white shadow rounded-lg p-6">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">
                            KSI Validator Dashboard
                        </h1>
                        <p className="mt-1 text-sm text-gray-500">
                            FedRAMP 20x Key Security Indicator Validation Platform
                        </p>
                    </div>
                    <div className="text-right">
                        <div className="text-sm text-gray-500">Environment</div>
                        <div className="font-semibold text-blue-600">
                            {process.env.REACT_APP_ENVIRONMENT || 'development'}
                        </div>
                    </div>
                </div>
            </div>

            {/* Controls */}
            <div className="bg-white shadow rounded-lg p-6">
                <div className="flex flex-wrap items-center gap-4">
                    <div className="flex-1 min-w-48">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Tenant ID
                        </label>
                        <select
                            value={selectedTenant}
                            onChange={(e) => setSelectedTenant(e.target.value)}
                            className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value="default">Default Tenant</option>
                            <option value="tenant-001">Tenant 001</option>
                            <option value="tenant-002">Tenant 002</option>
                            <option value="all">All Tenants</option>
                        </select>
                    </div>
                    
                    <div className="flex gap-2">
                        <button
                            onClick={triggerValidation}
                            disabled={loading}
                            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-2 rounded-md font-medium transition-colors"
                        >
                            {loading ? 'Triggering...' : '🔍 Trigger Validation'}
                        </button>
                        
                        <button
                            onClick={fetchExecutionHistory}
                            disabled={loading}
                            className="bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 text-white px-6 py-2 rounded-md font-medium transition-colors"
                        >
                            {loading ? 'Refreshing...' : '🔄 Refresh'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Error Display */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex">
                        <div className="flex-shrink-0">
                            <span className="text-red-400">❌</span>
                        </div>
                        <div className="ml-3">
                            <h3 className="text-sm font-medium text-red-800">Error</h3>
                            <div className="mt-2 text-sm text-red-700">{error}</div>
                        </div>
                        <div className="ml-auto pl-3">
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

            {/* Last Execution Info */}
            {lastExecution && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center">
                        <span className="text-green-400 mr-3">✅</span>
                        <div>
                            <h3 className="text-sm font-medium text-green-800">
                                Validation Triggered Successfully
                            </h3>
                            <p className="text-sm text-green-700">
                                Execution ID: <code className="bg-green-100 px-1 rounded">{lastExecution.execution_id}</code>
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* KSI Categories Overview */}
            <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                    KSI Categories
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(ksiCategories).map(([code, name]) => (
                        <div key={code} className="border border-gray-200 rounded-lg p-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <div className="font-semibold text-lg text-blue-600">{code}</div>
                                    <div className="text-sm text-gray-600">{name}</div>
                                </div>
                                <div className="text-2xl">🔒</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Execution History */}
            <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                    Execution History
                </h2>
                
                {loading && executionHistory.length === 0 ? (
                    <div className="text-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                        <p className="mt-2 text-gray-500">Loading execution history...</p>
                    </div>
                ) : executionHistory.length === 0 ? (
                    <div className="text-center py-8">
                        <div className="text-gray-400 text-4xl mb-2">📊</div>
                        <p className="text-gray-500">No execution history found</p>
                        <p className="text-sm text-gray-400">Trigger a validation to see results here</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Execution ID
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Tenant
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Status
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Timestamp
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        KSIs
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {executionHistory.map((execution, index) => (
                                    <tr key={execution.execution_id || index} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                                            {execution.execution_id ? execution.execution_id.substring(0, 8) + '...' : `exec-${index}`}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {execution.tenant_id || 'Unknown'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(execution.status)}`}>
                                                {execution.status || 'Unknown'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {formatTimestamp(execution.timestamp || execution.start_time)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {execution.total_ksis_validated || 0}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                            <button
                                                onClick={() => fetchValidationResults(execution.execution_id)}
                                                className="text-blue-600 hover:text-blue-900"
                                                disabled={loading}
                                            >
                                                {loading && selectedExecutionId === execution.execution_id ? 'Loading...' : 'View Results'}
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Validation Results */}
            {validationResults.length > 0 && (
                <div className="bg-white shadow rounded-lg p-6">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-semibold text-gray-900">
                            Validation Results for Execution: {selectedExecutionId?.substring(0, 8)}...
                        </h2>
                        <button
                            onClick={closeResults}
                            className="text-gray-400 hover:text-gray-600 text-sm"
                        >
                            ✕ Close
                        </button>
                    </div>
                    
                    <div className="space-y-6">
                        {validationResults.map((result, index) => (
                            <div key={index} className="border border-gray-200 rounded-lg p-6">
                                <div className="flex justify-between items-start mb-4">
                                    <div>
                                        <h3 className="font-semibold text-xl text-blue-600">{result.ksi_id}</h3>
                                        <p className="text-gray-600 mt-1">{result.description}</p>
                                        {result.function_name && (
                                            <p className="text-xs text-gray-500 mt-1">Function: {result.function_name}</p>
                                        )}
                                    </div>
                                    <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(result.status)}`}>
                                        {result.status}
                                    </span>
                                </div>

                                {/* Summary */}
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
                                        <h4 className="font-medium text-gray-900 mb-3">Individual KSI Results & CLI Commands</h4>
                                        <div className="space-y-4">
                                            {result.individual_results.map((ksi, ksiIndex) => {
                                                const cmdInfo = parseCliCommand(ksi.cli_command);
                                                return (
                                                    <div key={ksiIndex} className="border border-gray-100 rounded-lg p-4">
                                                        {/* KSI Header */}
                                                        <div className="flex justify-between items-center mb-3">
                                                            <div>
                                                                <span className="font-semibold text-lg">{ksi.ksi_id}</span>
                                                                {ksi.assertion_reason && (
                                                                    <p className="text-sm text-gray-600 mt-1">{ksi.assertion_reason}</p>
                                                                )}
                                                            </div>
                                                            <span className={`px-2 py-1 text-xs font-semibold rounded ${ksi.assertion ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                                                {ksi.assertion ? 'PASS' : 'FAIL'}
                                                            </span>
                                                        </div>

                                                        {/* CLI Commands Section */}
                                                        <div className="bg-gray-50 rounded-lg p-3 mb-3">
                                                            <div className="flex items-center justify-between mb-2">
                                                                <h5 className="font-medium text-gray-800 text-sm">🖥️ CLI Commands Executed</h5>
                                                                <div className="text-xs text-gray-600">
                                                                    <span className="mr-3">✅ {ksi.successful_commands || 0} Success</span>
                                                                    <span>❌ {ksi.failed_commands || 0} Failed</span>
                                                                </div>
                                                            </div>
                                                            
                                                            {cmdInfo.commands && cmdInfo.commands.length > 0 ? (
                                                                <div className="space-y-1">
                                                                    {cmdInfo.commands.map((cmd, cmdIdx) => (
                                                                        <div key={cmdIdx} className="font-mono text-xs bg-white p-2 rounded border">
                                                                            {cmd.includes('(+') ? (
                                                                                <span className="text-blue-600">{cmd}</span>
                                                                            ) : (
                                                                                <span className="text-gray-800">{cmd}</span>
                                                                            )}
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            ) : (
                                                                <div className="text-xs text-gray-500 italic">
                                                                    {ksi.cli_command || 'No command information available'}
                                                                </div>
                                                            )}

                                                            {/* CLI Output Interpretation */}
                                                            {ksi.cli_output_interpretation && (
                                                                <div className="mt-2 pt-2 border-t border-gray-200">
                                                                    <div className="text-xs text-gray-600">
                                                                        <span className="font-medium">Output Analysis:</span> {ksi.cli_output_interpretation}
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </div>

                                                        {/* Requirement/Description */}
                                                        {ksi.requirement && (
                                                            <div className="text-sm text-gray-700 bg-blue-50 p-2 rounded">
                                                                <span className="font-medium">Requirement:</span> {ksi.requirement}
                                                            </div>
                                                        )}
                                                    </div>
                                                );
                                            })}
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
                </div>
            )}

            {/* API Endpoints Reference */}
            <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    API Endpoints
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                        <div className="font-medium text-blue-600">Validate</div>
                        <div className="font-mono text-xs text-gray-600 break-all">
                            POST /api/ksi/validate
                        </div>
                    </div>
                    <div>
                        <div className="font-medium text-green-600">Executions</div>
                        <div className="font-mono text-xs text-gray-600 break-all">
                            GET /api/ksi/executions
                        </div>
                    </div>
                    <div>
                        <div className="font-medium text-purple-600">Results</div>
                        <div className="font-mono text-xs text-gray-600 break-all">
                            GET /api/ksi/results
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default KSIManager;
