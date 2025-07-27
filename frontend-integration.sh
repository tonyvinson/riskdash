#!/bin/bash

echo "🎨 Integrating Tenant Management Frontend with Existing KSI Validator"
echo "=================================================================="

# Check if we're in the right directory
if [ ! -d "frontend/src/components/KSIManager" ]; then
    echo "❌ Please run this script from your project root directory"
    echo "   (the directory containing frontend/src/components/KSIManager/)"
    exit 1
fi

echo "✅ Found existing KSI Manager component"

# 1. First, update the ksiService to include tenant management APIs
echo "📝 Updating ksiService.js to include tenant management..."
cat > frontend/src/services/ksiService.js << 'EOF'
// frontend/src/services/ksiService.js - Enhanced with Tenant Management
import axios from 'axios';

// API Configuration
const API_CONFIG = {
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:3001',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
};

// Create axios instance
const apiClient = axios.create(API_CONFIG);

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`, config.data);
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status}`, response.data);
    return response;
  },
  (error) => {
    console.error('❌ API Error:', error.response?.data || error.message);
    
    // Handle common error scenarios
    if (error.response?.status === 429) {
      throw new Error('Too many requests. Please try again later.');
    } else if (error.response?.status === 500) {
      throw new Error('Server error. Please try again later.');
    } else if (error.response?.status === 403) {
      throw new Error('Access forbidden. Check your permissions.');
    }
    
    throw error;
  }
);

// KSI Service Methods
export const ksiService = {
  /**
   * Trigger KSI validation for a tenant
   */
  triggerValidation: async (tenantId = 'default', triggerSource = 'manual', executionId = null) => {
    try {
      const payload = {
        tenant_id: tenantId,
        trigger_source: triggerSource
      };
      
      if (executionId) {
        payload.execution_id = executionId;
      }
      
      const response = await apiClient.post('/api/ksi/validate', payload);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to trigger validation: ${error.message}`);
    }
  },

  /**
   * Get KSI execution history
   */
  getExecutionHistory: async (tenantId = 'all', limit = 10, startKey = null) => {
    try {
      const params = new URLSearchParams();
      
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
      const response = await apiClient.get(url);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch execution history: ${error.message}`);
    }
  },

  /**
   * Get detailed KSI validation results
   */
  getValidationResults: async (tenantId = null, executionId = null, ksiId = null, category = null) => {
    try {
      const params = new URLSearchParams();
      
      if (tenantId) params.append('tenant_id', tenantId);
      if (executionId) params.append('execution_id', executionId);
      if (ksiId) params.append('ksi_id', ksiId);
      if (category) params.append('category', category);

      const url = `/api/ksi/results${params.toString() ? '?' + params.toString() : ''}`;
      const response = await apiClient.get(url);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch validation results: ${error.message}`);
    }
  },

  /**
   * Get available tenants with metadata
   */
  getTenants: async () => {
    try {
      const response = await apiClient.get('/api/tenant/list');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch tenants: ${error.message}`);
    }
  },

  /**
   * Generate IAM role setup instructions for new tenant
   */
  generateRoleInstructions: async (tenantData) => {
    try {
      const response = await apiClient.post('/api/tenant/generate-role-instructions', {
        action: 'generate_role_instructions',
        ...tenantData
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to generate role instructions: ${error.message}`);
    }
  },

  /**
   * Test connection to customer AWS account
   */
  testTenantConnection: async (roleArn, externalId) => {
    try {
      const response = await apiClient.post('/api/tenant/test-connection', {
        action: 'test_connection',
        roleArn,
        externalId
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to test connection: ${error.message}`);
    }
  },

  /**
   * Complete tenant onboarding
   */
  onboardTenant: async (tenantData) => {
    try {
      const response = await apiClient.post('/api/tenant/onboard', {
        action: 'onboard',
        ...tenantData
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to onboard tenant: ${error.message}`);
    }
  },

  /**
   * Get KSI definitions (for reference)
   */
  getKSIDefinitions: async () => {
    return {
      categories: {
        'CNA': 'Configuration & Network Architecture',
        'SVC': 'Service Configuration', 
        'IAM': 'Identity & Access Management',
        'MLA': 'Monitoring, Logging & Alerting',
        'CMT': 'Configuration Management & Tracking'
      }
    };
  },

  /**
   * Test API connectivity
   */
  testConnection: async () => {
    try {
      await apiClient.get('/api/ksi/executions?limit=1');
      return {
        status: 'connected',
        timestamp: new Date().toISOString(),
        apiUrl: API_CONFIG.baseURL
      };
    } catch (error) {
      throw new Error(`API connection test failed: ${error.message}`);
    }
  }
};

export default ksiService;
EOF

echo "✅ Updated ksiService.js with tenant management APIs"

# 2. Create the TenantOnboarding component
echo "📁 Creating TenantOnboarding component..."
mkdir -p frontend/src/components/TenantOnboarding

cat > frontend/src/components/TenantOnboarding/TenantOnboarding.js << 'EOF'
import React, { useState, useEffect } from 'react';
import { ChevronRight, ChevronLeft, CheckCircle, AlertCircle, Copy, ExternalLink } from 'lucide-react';
import { ksiService } from '../../services/ksiService';

const TenantOnboarding = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    organization: {},
    contacts: {},
    awsAccounts: {},
    compliance: {},
    preferences: {}
  });
  const [roleInstructions, setRoleInstructions] = useState(null);
  const [connectionTest, setConnectionTest] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const steps = [
    { id: 1, title: 'Organization Info', description: 'Basic organization details' },
    { id: 2, title: 'Contact Information', description: 'Primary and technical contacts' },
    { id: 3, title: 'AWS Configuration', description: 'AWS account setup' },
    { id: 4, title: 'AWS IAM Role', description: 'Cross-account access setup' },
    { id: 5, title: 'Compliance Profile', description: 'FedRAMP and compliance settings' },
    { id: 6, title: 'Preferences', description: 'Validation and notification settings' },
    { id: 7, title: 'Review & Submit', description: 'Final review and activation' }
  ];

  const updateFormData = (section, data) => {
    setFormData(prev => ({
      ...prev,
      [section]: { ...prev[section], ...data }
    }));
  };

  const generateRoleInstructions = async () => {
    if (formData.awsAccounts.primaryAccountId) {
      try {
        setError(null);
        const instructions = await ksiService.generateRoleInstructions({
          tenantId: `temp-${Date.now()}`,
          accountId: formData.awsAccounts.primaryAccountId
        });
        setRoleInstructions(instructions);
        
        // Auto-populate external ID
        if (instructions.external_id) {
          updateFormData('awsAccounts', { externalId: instructions.external_id });
        }
      } catch (error) {
        console.error('Error generating role instructions:', error);
        setError(`Failed to generate role instructions: ${error.message}`);
      }
    }
  };

  const testConnection = async () => {
    if (formData.awsAccounts.roleArn && formData.awsAccounts.externalId) {
      try {
        setError(null);
        const result = await ksiService.testTenantConnection(
          formData.awsAccounts.roleArn,
          formData.awsAccounts.externalId
        );
        setConnectionTest(result);
      } catch (error) {
        console.error('Error testing connection:', error);
        setError(`Connection test failed: ${error.message}`);
        setConnectionTest({ connection_status: 'FAILED', error: error.message });
      }
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const submitOnboarding = async () => {
    try {
      setIsSubmitting(true);
      setError(null);
      
      const result = await ksiService.onboardTenant(formData);
      
      if (onComplete) {
        onComplete(result);
      } else {
        alert(`Tenant onboarding completed! Tenant ID: ${result.tenant_id}`);
      }
    } catch (error) {
      console.error('Error submitting onboarding:', error);
      setError(`Onboarding failed: ${error.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Organization Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Organization Name *</label>
            <input
              type="text"
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              value={formData.organization.name || ''}
              onChange={(e) => updateFormData('organization', { name: e.target.value })}
              placeholder="e.g., Acme Corporation"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Organization Type *</label>
            <select
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              value={formData.organization.type || ''}
              onChange={(e) => updateFormData('organization', { type: e.target.value })}
            >
              <option value="">Select type...</option>
              <option value="federal_agency">Federal Agency</option>
              <option value="private_company">Private Company</option>
              <option value="nonprofit">Non-Profit</option>
              <option value="state_local">State/Local Government</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Industry *</label>
            <input
              type="text"
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              value={formData.organization.industry || ''}
              onChange={(e) => updateFormData('organization', { industry: e.target.value })}
              placeholder="e.g., Financial Services, Healthcare"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Organization Size *</label>
            <select
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              value={formData.organization.size || ''}
              onChange={(e) => updateFormData('organization', { size: e.target.value })}
            >
              <option value="">Select size...</option>
              <option value="small">Small (1-50 employees)</option>
              <option value="medium">Medium (51-500 employees)</option>
              <option value="large">Large (501-5000 employees)</option>
              <option value="enterprise">Enterprise (5000+ employees)</option>
            </select>
          </div>
        </div>
        
        <div className="mt-4 flex items-center">
          <input
            type="checkbox"
            id="federalEntity"
            checked={formData.organization.federalEntity || false}
            onChange={(e) => updateFormData('organization', { federalEntity: e.target.checked })}
            className="mr-2"
          />
          <label htmlFor="federalEntity" className="text-sm">This is a federal entity</label>
        </div>
        
        {formData.organization.federalEntity && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">DUNS Number</label>
              <input
                type="text"
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                value={formData.organization.dunsNumber || ''}
                onChange={(e) => updateFormData('organization', { dunsNumber: e.target.value })}
                placeholder="9-digit DUNS number"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">CAGE Code</label>
              <input
                type="text"
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                value={formData.organization.cageCode || ''}
                onChange={(e) => updateFormData('organization', { cageCode: e.target.value })}
                placeholder="5-character CAGE code"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold mb-4">Contact Information</h3>
      
      {['primary', 'technical', 'billing'].map((contactType, index) => (
        <div key={contactType} className={`p-4 border rounded-md ${index === 2 ? 'border-gray-200' : 'border-blue-200'}`}>
          <h4 className="font-medium mb-3 capitalize">
            {contactType} Contact {index < 2 && <span className="text-red-500">*</span>}
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Name</label>
              <input
                type="text"
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                value={formData.contacts[`${contactType}Name`] || ''}
                onChange={(e) => updateFormData('contacts', { [`${contactType}Name`]: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Email</label>
              <input
                type="email"
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                value={formData.contacts[`${contactType}Email`] || ''}
                onChange={(e) => updateFormData('contacts', { [`${contactType}Email`]: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Phone</label>
              <input
                type="tel"
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                value={formData.contacts[`${contactType}Phone`] || ''}
                onChange={(e) => updateFormData('contacts', { [`${contactType}Phone`]: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Role/Title</label>
              <input
                type="text"
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                value={formData.contacts[`${contactType}Role`] || ''}
                onChange={(e) => updateFormData('contacts', { [`${contactType}Role`]: e.target.value })}
                placeholder="e.g., CISO, DevOps Manager"
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold mb-4">AWS Account Configuration</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Primary AWS Account ID *</label>
          <input
            type="text"
            className="w-full border border-gray-300 rounded-md px-3 py-2"
            value={formData.awsAccounts.primaryAccountId || ''}
            onChange={(e) => updateFormData('awsAccounts', { primaryAccountId: e.target.value })}
            placeholder="123456789012"
            maxLength="12"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Primary Region *</label>
          <select
            className="w-full border border-gray-300 rounded-md px-3 py-2"
            value={formData.awsAccounts.primaryRegion || ''}
            onChange={(e) => updateFormData('awsAccounts', { primaryRegion: e.target.value })}
          >
            <option value="">Select region...</option>
            <option value="us-east-1">US East (N. Virginia)</option>
            <option value="us-west-2">US West (Oregon)</option>
            <option value="us-gov-east-1">AWS GovCloud (US-East)</option>
            <option value="us-gov-west-1">AWS GovCloud (US-West)</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Account Purpose *</label>
        <select
          className="w-full border border-gray-300 rounded-md px-3 py-2"
          value={formData.awsAccounts.purpose || ''}
          onChange={(e) => updateFormData('awsAccounts', { purpose: e.target.value })}
        >
          <option value="">Select purpose...</option>
          <option value="production">Production</option>
          <option value="staging">Staging</option>
          <option value="development">Development</option>
          <option value="testing">Testing</option>
        </select>
      </div>

      <div className="mt-6">
        <button
          onClick={generateRoleInstructions}
          disabled={!formData.awsAccounts.primaryAccountId}
          className="bg-blue-600 text-white px-4 py-2 rounded-md disabled:bg-gray-400"
        >
          Generate IAM Role Instructions
        </button>
      </div>
    </div>
  );

  const renderStep4 = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold mb-4">AWS IAM Role Setup</h3>
      
      {roleInstructions && (
        <div className="space-y-6">
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <h4 className="font-medium mb-2">📋 Setup Instructions</h4>
            <p className="text-sm text-gray-600 mb-4">
              Create an IAM role in your AWS account to allow Riskuity secure, read-only access for security validations.
            </p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">AWS CLI Command:</label>
                <div className="relative">
                  <pre className="bg-gray-900 text-green-400 p-3 rounded text-xs overflow-x-auto">
{roleInstructions.cli_commands && roleInstructions.cli_commands[0]}
                  </pre>
                  <button
                    onClick={() => copyToClipboard(roleInstructions.cli_commands && roleInstructions.cli_commands[0])}
                    className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
                  >
                    <Copy size={16} />
                  </button>
                </div>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                <h5 className="font-medium text-sm mb-2">🔒 Security Information</h5>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>• <strong>External ID:</strong> {roleInstructions.external_id}</li>
                  <li>• <strong>Access Type:</strong> Read-only security validation</li>
                  <li>• <strong>Logging:</strong> All actions logged in your CloudTrail</li>
                  <li>• <strong>Revocation:</strong> Delete role anytime to revoke access</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">IAM Role ARN *</label>
              <input
                type="text"
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                value={formData.awsAccounts.roleArn || ''}
                onChange={(e) => updateFormData('awsAccounts', { roleArn: e.target.value })}
                placeholder="arn:aws:iam::123456789012:role/RiskuityKSIValidatorRole"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">External ID *</label>
              <input
                type="text"
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                value={formData.awsAccounts.externalId || ''}
                onChange={(e) => updateFormData('awsAccounts', { externalId: e.target.value })}
                placeholder="riskuity-xxx-xxxxxxxx"
                readOnly
              />
            </div>
          </div>

          <div>
            <button
              onClick={testConnection}
              disabled={!formData.awsAccounts.roleArn || !formData.awsAccounts.externalId}
              className="bg-green-600 text-white px-4 py-2 rounded-md disabled:bg-gray-400 mr-4"
            >
              Test Connection
            </button>
            
            {connectionTest && (
              <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm ${
                connectionTest.connection_status === 'SUCCESS' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {connectionTest.connection_status === 'SUCCESS' ? (
                  <>
                    <CheckCircle size={16} className="mr-1" />
                    Connection Successful
                  </>
                ) : (
                  <>
                    <AlertCircle size={16} className="mr-1" />
                    Connection Failed
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  const renderStep5 = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold mb-4">Compliance Profile</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Target FedRAMP Level *</label>
          <select
            className="w-full border border-gray-300 rounded-md px-3 py-2"
            value={formData.compliance.fedrampLevel || ''}
            onChange={(e) => updateFormData('compliance', { fedrampLevel: e.target.value })}
          >
            <option value="">Select level...</option>
            <option value="Low">Low Impact</option>
            <option value="Moderate">Moderate Impact</option>
            <option value="High">High Impact</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Current Status</label>
          <select
            className="w-full border border-gray-300 rounded-md px-3 py-2"
            value={formData.compliance.currentStatus || ''}
            onChange={(e) => updateFormData('compliance', { currentStatus: e.target.value })}
          >
            <option value="">Select status...</option>
            <option value="none">Not Started</option>
            <option value="planning">Planning Phase</option>
            <option value="in_progress">In Progress</option>
            <option value="authorized">Authorized</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Authorization Boundary *</label>
        <textarea
          className="w-full border border-gray-300 rounded-md px-3 py-2"
          rows="3"
          value={formData.compliance.authorizationBoundary || ''}
          onChange={(e) => updateFormData('compliance', { authorizationBoundary: e.target.value })}
          placeholder="Describe your system's authorization boundary..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Required Frameworks</label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {['FedRAMP', 'NIST 800-53', 'SOC 2', 'FISMA', 'DISA STIG', 'PCI DSS'].map(framework => (
            <label key={framework} className="flex items-center">
              <input
                type="checkbox"
                checked={formData.compliance.frameworks?.includes(framework) || false}
                onChange={(e) => {
                  const frameworks = formData.compliance.frameworks || [];
                  if (e.target.checked) {
                    updateFormData('compliance', { frameworks: [...frameworks, framework] });
                  } else {
                    updateFormData('compliance', { frameworks: frameworks.filter(f => f !== framework) });
                  }
                }}
                className="mr-2"
              />
              <span className="text-sm">{framework}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );

  const renderStep6 = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold mb-4">Validation & Notification Preferences</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Validation Frequency *</label>
          <select
            className="w-full border border-gray-300 rounded-md px-3 py-2"
            value={formData.preferences.validationFrequency || ''}
            onChange={(e) => updateFormData('preferences', { validationFrequency: e.target.value })}
          >
            <option value="">Select frequency...</option>
            <option value="hourly">Hourly</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
          </select>
        </div>
        <div className="flex items-center">
          <input
            type="checkbox"
            id="automatedRemediation"
            checked={formData.preferences.automatedRemediation || false}
            onChange={(e) => updateFormData('preferences', { automatedRemediation: e.target.checked })}
            className="mr-2"
          />
          <label htmlFor="automatedRemediation" className="text-sm">Enable automated remediation (where possible)</label>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Notification Email *</label>
        <input
          type="email"
          className="w-full border border-gray-300 rounded-md px-3 py-2"
          value={formData.preferences.notificationEmail || ''}
          onChange={(e) => updateFormData('preferences', { notificationEmail: e.target.value })}
          placeholder="security@yourcompany.com"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Additional Notification Emails</label>
        <input
          type="text"
          className="w-full border border-gray-300 rounded-md px-3 py-2"
          value={formData.preferences.additionalEmails || ''}
          onChange={(e) => updateFormData('preferences', { additionalEmails: e.target.value })}
          placeholder="email1@company.com, email2@company.com"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Slack Webhook (Optional)</label>
        <input
          type="url"
          className="w-full border border-gray-300 rounded-md px-3 py-2"
          value={formData.preferences.slackWebhook || ''}
          onChange={(e) => updateFormData('preferences', { slackWebhook: e.target.value })}
          placeholder="https://hooks.slack.com/services/..."
        />
      </div>
    </div>
  );

  const renderStep7 = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold mb-4">Review & Submit</h3>
      
      <div className="bg-gray-50 rounded-md p-4 space-y-4">
        <div>
          <h4 className="font-medium">Organization</h4>
          <p className="text-sm text-gray-600">{formData.organization.name} ({formData.organization.type})</p>
        </div>
        <div>
          <h4 className="font-medium">AWS Account</h4>
          <p className="text-sm text-gray-600">{formData.awsAccounts.primaryAccountId} - {formData.awsAccounts.primaryRegion}</p>
        </div>
        <div>
          <h4 className="font-medium">Compliance</h4>
          <p className="text-sm text-gray-600">FedRAMP {formData.compliance.fedrampLevel} - {formData.compliance.currentStatus}</p>
        </div>
        <div>
          <h4 className="font-medium">Validation</h4>
          <p className="text-sm text-gray-600">{formData.preferences.validationFrequency} validations to {formData.preferences.notificationEmail}</p>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <h4 className="font-medium mb-2">🚀 Next Steps</h4>
        <ol className="text-sm text-gray-600 space-y-1">
          <li>1. Your tenant account will be created</li>
          <li>2. Initial KSI validation will begin within 1 hour</li>
          <li>3. You'll receive a welcome email with dashboard access</li>
          <li>4. Compliance reports will be available immediately</li>
        </ol>
      </div>

      <button
        onClick={submitOnboarding}
        disabled={isSubmitting}
        className="w-full bg-blue-600 text-white py-3 rounded-md disabled:bg-gray-400"
      >
        {isSubmitting ? 'Creating Your Account...' : 'Complete Onboarding'}
      </button>
    </div>
  );

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1: return renderStep1();
      case 2: return renderStep2();
      case 3: return renderStep3();
      case 4: return renderStep4();
      case 5: return renderStep5();
      case 6: return renderStep6();
      case 7: return renderStep7();
      default: return renderStep1();
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          🛡️ Riskuity KSI Validator Onboarding
        </h1>
        <p className="text-gray-600">
          Set up your organization for automated FedRAMP 20x compliance validation
        </p>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertCircle className="text-red-400 mr-2" size={20} />
            <div className="text-red-700 text-sm">{error}</div>
          </div>
        </div>
      )}

      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
                currentStep === step.id 
                  ? 'bg-blue-600 text-white' 
                  : currentStep > step.id 
                    ? 'bg-green-600 text-white' 
                    : 'bg-gray-300 text-gray-600'
              }`}>
                {currentStep > step.id ? <CheckCircle size={16} /> : step.id}
              </div>
              <div className="ml-2 hidden md:block">
                <div className="text-sm font-medium">{step.title}</div>
                <div className="text-xs text-gray-500">{step.description}</div>
              </div>
              {index < steps.length - 1 && (
                <ChevronRight className="mx-4 text-gray-400" size={16} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
        {renderCurrentStep()}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
          disabled={currentStep === 1}
          className="flex items-center px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50"
        >
          <ChevronLeft size={16} className="mr-1" />
          Previous
        </button>
        
        {currentStep < 7 && (
          <button
            onClick={() => setCurrentStep(Math.min(7, currentStep + 1))}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md"
          >
            Next
            <ChevronRight size={16} className="ml-1" />
          </button>
        )}
      </div>
    </div>
  );
};

export default TenantOnboarding;
EOF

echo "✅ Created TenantOnboarding component"

# 3. Update the main App.js to include routing
echo "📝 Updating App.js with tenant management routing..."
cat > frontend/src/App.js << 'EOF'
import React, { useState } from 'react';
import KSIManager from './components/KSIManager/KSIManager';
import TenantOnboarding from './components/TenantOnboarding/TenantOnboarding';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [notification, setNotification] = useState(null);

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000);
  };

  const handleOnboardingComplete = (result) => {
    showNotification(`Tenant onboarded successfully! Tenant ID: ${result.tenant_id}`);
    setCurrentView('dashboard');
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'onboarding':
        return <TenantOnboarding onComplete={handleOnboardingComplete} />;
      case 'dashboard':
      default:
        return <KSIManager />;
    }
  };

  return (
    <div className="App min-h-screen bg-gray-50">
      {/* Navigation Header */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                🛡️ Riskuity KSI Validator
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setCurrentView('dashboard')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  currentView === 'dashboard'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setCurrentView('onboarding')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  currentView === 'onboarding'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                New Tenant
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 max-w-sm p-4 rounded-md shadow-lg z-50 ${
          notification.type === 'success' 
            ? 'bg-green-50 border border-green-200 text-green-700'
            : 'bg-red-50 border border-red-200 text-red-700'
        }`}>
          {notification.message}
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto">
        {renderCurrentView()}
      </main>
    </div>
  );
}

export default App;
EOF

echo "✅ Updated App.js with navigation and routing"

# 4. Add required dependencies
echo "📦 Adding required dependencies..."
cd frontend
npm install lucide-react
cd ..

echo ""
echo "🎉 Frontend Integration Complete!"
echo ""
echo "📋 What was added:"
echo "   ✅ Updated ksiService.js with tenant management APIs"
echo "   ✅ Created TenantOnboarding component with 7-step workflow"
echo "   ✅ Updated App.js with navigation between Dashboard and Onboarding"
echo "   ✅ Added lucide-react for icons"
echo ""
echo "🔗 API Endpoints the frontend now uses:"
echo "   • POST /api/tenant/generate-role-instructions"
echo "   • POST /api/tenant/test-connection"
echo "   • POST /api/tenant/onboard"
echo "   • GET /api/tenant/list"
echo ""
echo "🚀 Next Steps:"
echo "1. Make sure your API Gateway routes these endpoints to the tenant management Lambda"
echo "2. Start your frontend: cd frontend && npm start"
echo "3. Navigate to 'New Tenant' to test the onboarding flow"
echo ""
echo "✨ Your KSI Validator now has complete tenant management!"
