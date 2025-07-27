# Tenant Management API Integration Instructions

## 1. Update your main terraform/main.tf

Add these variables to your API Gateway module call:

```hcl
module "api_gateway" {
  source = "./modules/api_gateway"
  
  # ... existing variables ...
  
  # Add these new variables for tenant management
  tenant_onboarding_lambda_function_name = module.tenant_management.tenant_onboarding_api_function_name
  tenant_onboarding_lambda_invoke_arn    = module.tenant_management.tenant_onboarding_api_function_arn
}
```

## 2. Update your outputs.tf

Add tenant API endpoints to your outputs:

```hcl
output "tenant_api_endpoints" {
  description = "Tenant management API endpoints"
  value       = module.api_gateway.tenant_api_endpoints
}
```

## 3. Deploy the changes

```bash
cd terraform
terraform plan
terraform apply
```

## 4. Test the new endpoints

After deployment, test the new tenant management endpoints:

```bash
# Get the API URL
terraform output tenant_api_endpoints

# Test role instructions generation
curl -X POST "https://your-api-gateway-url/api/tenant/generate-role-instructions" \
  -H "Content-Type: application/json" \
  -d '{"tenantId": "test-tenant", "accountId": "123456789012"}'
```

## 5. Update frontend API URL

Make sure your frontend environment is pointing to the correct API Gateway URL:

```bash
# In frontend/.env
REACT_APP_API_URL=https://your-api-gateway-url
```
