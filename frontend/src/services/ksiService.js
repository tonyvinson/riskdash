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
