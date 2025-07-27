#!/bin/bash
set -e

# Riskuity KSI Validator - Project Bootstrap Script
echo "🏗️  Bootstrapping KSI Validator Platform..."

# Configuration
PROJECT_NAME="riskuity-ksi-validator"
ENVIRONMENT="${ENVIRONMENT:-production}"
AWS_REGION="${AWS_REGION:-us-gov-west-1}"
TERRAFORM_BUCKET="riskuity-ksi-tfstate"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create S3 bucket for Terraform state
create_terraform_backend() {
    log_info "Setting up Terraform backend with S3 native state locking..."
    
    # Create S3 bucket
    if aws s3 ls "s3://$TERRAFORM_BUCKET" 2>&1 | grep -q 'NoSuchBucket'; then
        aws s3 mb "s3://$TERRAFORM_BUCKET" --region "$AWS_REGION"
        log_success "Created S3 bucket: $TERRAFORM_BUCKET"
        
        # Enable versioning
        aws s3api put-bucket-versioning \
            --bucket "$TERRAFORM_BUCKET" \
            --versioning-configuration Status=Enabled
        log_success "Enabled versioning on $TERRAFORM_BUCKET"
        
        # Enable encryption
        aws s3api put-bucket-encryption \
            --bucket "$TERRAFORM_BUCKET" \
            --server-side-encryption-configuration '{
                "Rules": [
                    {
                        "ApplyServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "AES256"
                        }
                    }
                ]
            }'
        log_success "Enabled encryption on $TERRAFORM_BUCKET"
    else
        log_info "S3 bucket $TERRAFORM_BUCKET already exists"
    fi
    
    log_info "Using S3 native state locking (no DynamoDB table required)"
}

# Initialize Terraform
init_terraform() {
    log_info "Initializing Terraform..."
    cd terraform
    terraform init
    terraform validate
    cd ..
    log_success "Terraform initialized and validated"
}

# Package Lambda functions
package_lambdas() {
    log_info "Packaging Lambda functions..."
    chmod +x scripts/deploy_lambdas.sh
    ./scripts/deploy_lambdas.sh package-only
    log_success "Lambda functions packaged"
}

main() {
    log_info "Starting KSI Validator platform bootstrap..."
    log_info "Project: $PROJECT_NAME"
    log_info "Environment: $ENVIRONMENT"
    log_info "Region: $AWS_REGION"
    
    create_terraform_backend
    package_lambdas
    init_terraform
    
    log_success "🎉 KSI Validator platform bootstrap completed!"
    echo ""
    log_info "Next steps:"
    log_info "1. Review terraform/terraform.tfvars (create if needed)"
    log_info "2. Run: cd terraform && terraform plan"
    log_info "3. Run: cd terraform && terraform apply"
    log_info "4. Test: ./scripts/deploy_lambdas.sh"
}

main
