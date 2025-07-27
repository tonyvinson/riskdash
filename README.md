# Riskuity KSI Validator Platform

A complete FedRAMP 20X Key Security Indicator (KSI) validation platform built on AWS GovCloud infrastructure.

## 🏗️ Architecture

This platform provides automated validation of FedRAMP 20X compliance requirements through:

- **Terraform Infrastructure**: Complete AWS GovCloud infrastructure as code
- **Lambda Orchestration**: Serverless validation engine with category-specific validators
- **DynamoDB Storage**: Scalable storage for KSI definitions, configurations, and execution history
- **EventBridge Scheduling**: Automated daily compliance validation runs
- **React Frontend**: Dashboard for monitoring and managing validation processes

## 📋 Components

### Infrastructure (Terraform)
- **DynamoDB Tables**: 
  - `ksi-definitions`: KSI validation rule definitions
  - `tenant-ksi-configurations`: Tenant-specific KSI configurations
  - `ksi-execution-history`: Historical validation results
- **Lambda Functions**: Orchestrator + 5 category validators (CNA, SVC, IAM, MLA, CMT)
- **EventBridge Rules**: Daily scheduling at 6 AM UTC
- **IAM Roles**: Least-privilege access for all components

### Lambda Functions
- **Orchestrator**: Coordinates validation workflows across all validators
- **CNA Validator**: Configuration & Network Architecture compliance
- **SVC Validator**: Service Configuration compliance
- **IAM Validator**: Identity & Access Management compliance
- **MLA Validator**: Monitoring, Logging & Alerting compliance
- **CMT Validator**: Configuration Management & Tracking compliance

### Frontend
- **React Dashboard**: Real-time validation monitoring and control
- **KSI Manager**: Interface for triggering validations and viewing results
- **Execution History**: Complete audit trail of validation runs

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured for GovCloud (`us-gov-west-1`)
- Terraform >= 1.4
- Python 3.9+
- Node.js 16+ (for frontend)

### 1. Bootstrap Infrastructure
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Bootstrap the platform (creates S3 backend, packages Lambdas)
./scripts/bootstrap.sh

# Deploy infrastructure
cd terraform
terraform plan
terraform apply
```

### 2. Deploy Lambda Functions
```bash
# Package and deploy all Lambda functions
./scripts/deploy_lambdas.sh
```

### 3. Populate KSI Data
```bash
# Load your existing FedRAMP 20X validation engine data into DynamoDB
python3 scripts/populate_ksi_data.py
```

### 4. Setup Frontend
```bash
cd frontend
npm install
npm start
```

## 📊 KSI Categories

The platform validates the following FedRAMP 20X KSI categories:

| Category | Full Name | Purpose |
|----------|-----------|---------|
| **CNA** | Configuration & Network Architecture | Network security, VPC configuration, security groups |
| **SVC** | Service Configuration | Application services, databases, compute resources |
| **IAM** | Identity & Access Management | User management, roles, policies, authentication |
| **MLA** | Monitoring, Logging & Alerting | CloudWatch, CloudTrail, log management |
| **CMT** | Configuration Management & Tracking | Infrastructure as Code, change tracking |

## 🔧 Configuration

### Environment Variables
```bash
export ENVIRONMENT=production
export AWS_REGION=us-gov-west-1
export PROJECT_NAME=riskuity-ksi-validator
```

### Terraform Variables
Create `terraform/terraform.tfvars`:
```hcl
environment = "production"
aws_region = "us-gov-west-1"
project_name = "riskuity-ksi-validator"
lambda_timeout = 300
lambda_memory_size = 256
```

## 📝 Usage

### Manual Validation Trigger
```bash
# Trigger validation for all tenants
aws lambda invoke \
  --function-name riskuity-ksi-validator-orchestrator-production \
  --payload '{"tenant_id": "all", "source": "manual"}' \
  output.json

# View results
cat output.json
```

## 🔒 Security Features

- **GovCloud Deployment**: FedRAMP authorized cloud environment
- **Encryption**: All data encrypted at rest and in transit
- **IAM**: Least-privilege access controls
- **Audit Logging**: Complete audit trail of all validations
- **State Locking**: Terraform state locking prevents concurrent modifications

## 📈 Monitoring

The platform includes comprehensive monitoring:

- **CloudWatch Logs**: Structured logging from all Lambda functions
- **CloudWatch Metrics**: Custom metrics for validation success rates
- **DynamoDB Insights**: Performance monitoring for data operations

## 🛠️ Development

### Local Testing
```bash
# Test Lambda function locally
cd lambdas/orchestrator
python3 -c "
import orchestrator_handler
result = orchestrator_handler.lambda_handler({'tenant_id': 'test'}, {})
print(result)
"
```

### Adding New Validators
1. Create new validator directory: `lambdas/validators/ksi-validator-newtype/`
2. Implement `handler.py` with validation logic
3. Update `deploy_lambdas.sh` to include new validator
4. Add Terraform resources in `terraform/modules/lambda/main.tf`

## 📚 Documentation

- [FedRAMP 20X Requirements](https://www.fedramp.gov/modernization/)
- [AWS GovCloud Documentation](https://docs.aws.amazon.com/govcloud-us/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-validator`
3. Commit changes: `git commit -am 'Add new validator'`
4. Push to branch: `git push origin feature/new-validator`
5. Submit a Pull Request

## 📄 License

This project is proprietary to Riskuity and intended for internal use in FedRAMP 20X compliance validation.

## 🆘 Support

For technical support or questions:
- Internal Documentation: [Confluence Link]
- Slack Channel: #ksi-validator-support
- Email: devops@riskuity.com

---

**Built with ❤️ by the Riskuity Engineering Team**
# riskdash
# riskdash
# riskdash
