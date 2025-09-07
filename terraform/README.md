# Multi-Cloud Infrastructure for Dataiku Cloud Optimizer Agent

This directory contains Terraform configurations for deploying the infrastructure needed to run the Dataiku Cloud Optimizer Agent across multiple cloud providers.

## Structure

```
terraform/
├── aws/                 # AWS-specific configurations
├── azure/              # Azure-specific configurations  
├── gcp/                # GCP-specific configurations
└── modules/            # Reusable Terraform modules
    ├── compute/        # Compute resources (VMs, containers)
    ├── storage/        # Storage resources (databases, object storage)
    └── networking/     # Networking resources (VPCs, subnets)
```

## Quick Start

### Prerequisites

1. Install Terraform:
   ```bash
   # On macOS
   brew install terraform
   
   # On Ubuntu/Debian
   sudo apt-get update && sudo apt-get install terraform
   
   # On CentOS/RHEL
   sudo yum install terraform
   ```

2. Configure cloud provider credentials:
   - **AWS**: `aws configure` or set environment variables
   - **Azure**: `az login` or set service principal credentials
   - **GCP**: `gcloud auth application-default login` or set service account key

### Deploy to AWS

```bash
cd terraform/aws
terraform init
terraform plan
terraform apply
```

### Deploy to Azure

```bash
cd terraform/azure
terraform init
terraform plan
terraform apply
```

### Deploy to GCP

```bash
cd terraform/gcp
terraform init
terraform plan
terraform apply
```

## Configuration

Each cloud provider directory contains:

- `main.tf` - Main Terraform configuration
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `terraform.tfvars.example` - Example variable values

Copy `terraform.tfvars.example` to `terraform.tfvars` and customize the values for your environment.

## Modules

The `modules/` directory contains reusable Terraform modules:

### Compute Module

Provisions compute resources for running the optimizer agent:
- Virtual machines or container instances
- Auto-scaling groups
- Load balancers

### Storage Module

Provisions storage resources for data and logs:
- Databases for storing optimization history
- Object storage for reports and artifacts
- File systems for temporary data

### Networking Module

Provisions networking infrastructure:
- Virtual networks and subnets
- Security groups and firewalls
- VPN connections for hybrid setups

## Best Practices

1. **Use remote state**: Configure remote state storage (S3, Azure Storage, GCS)
2. **Version control**: Keep Terraform configurations in version control
3. **Environment separation**: Use workspaces or separate directories for dev/staging/prod
4. **Security**: Never commit sensitive values to version control
5. **Testing**: Use `terraform plan` before applying changes

## Examples

### Basic Deployment

Deploy a minimal setup for testing:

```bash
cd terraform/aws
terraform apply -var="environment=dev" -var="instance_type=t3.micro"
```

### Production Deployment

Deploy a production-ready setup:

```bash
cd terraform/aws
terraform apply -var="environment=prod" -var="instance_type=t3.large" -var="enable_monitoring=true"
```

### Multi-Region Deployment

Deploy across multiple regions:

```bash
cd terraform/aws
terraform apply -var="regions=[\"us-east-1\",\"us-west-2\"]"
```

## Monitoring and Logging

The Terraform configurations include optional monitoring and logging resources:

- CloudWatch/Azure Monitor/Cloud Monitoring for metrics
- Log aggregation and storage
- Alerting rules for cost anomalies
- Dashboards for visualization

## Cost Optimization

The infrastructure itself is designed with cost optimization in mind:

- Spot instances where appropriate
- Auto-scaling based on demand
- Reserved capacity for predictable workloads
- Lifecycle policies for data retention

## Troubleshooting

### Common Issues

1. **Authentication errors**: Verify cloud provider credentials
2. **Resource conflicts**: Check for existing resources with same names
3. **Permission errors**: Ensure sufficient IAM permissions
4. **Network connectivity**: Verify firewall and security group rules

### Debugging

Enable Terraform debug logging:

```bash
export TF_LOG=DEBUG
terraform apply
```

### Getting Help

- Check Terraform documentation for your provider
- Review cloud provider-specific error messages
- Use `terraform validate` to check configuration syntax
- Use `terraform plan` to preview changes before applying