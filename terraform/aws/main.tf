terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "dataiku-cloud-optimizer"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# VPC and Networking
module "networking" {
  source = "../modules/networking/aws"
  
  environment    = var.environment
  vpc_cidr       = var.vpc_cidr
  public_subnets = var.public_subnets
  private_subnets = var.private_subnets
  
  tags = local.common_tags
}

# Compute Resources
module "compute" {
  source = "../modules/compute/aws"
  
  environment     = var.environment
  instance_type   = var.instance_type
  key_name        = var.key_name
  vpc_id          = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  
  enable_auto_scaling = var.enable_auto_scaling
  min_size           = var.min_size
  max_size           = var.max_size
  desired_capacity   = var.desired_capacity
  
  tags = local.common_tags
}

# Storage Resources
module "storage" {
  source = "../modules/storage/aws"
  
  environment = var.environment
  
  # RDS for storing optimization history
  enable_rds           = var.enable_rds
  db_instance_class    = var.db_instance_class
  db_allocated_storage = var.db_allocated_storage
  db_subnet_group_name = module.networking.db_subnet_group_name
  
  # S3 for reports and artifacts
  enable_s3_bucket = var.enable_s3_bucket
  s3_bucket_prefix = var.s3_bucket_prefix
  
  tags = local.common_tags
}

# IAM Roles and Policies
resource "aws_iam_role" "optimizer_role" {
  name = "${var.environment}-dataiku-optimizer-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
  
  tags = local.common_tags
}

resource "aws_iam_role_policy" "optimizer_policy" {
  name = "${var.environment}-dataiku-optimizer-policy"
  role = aws_iam_role.optimizer_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ce:GetCostAndUsage",
          "ce:GetUsageReport",
          "ce:GetRightsizingRecommendation",
          "ec2:DescribeInstances",
          "ec2:DescribeVolumes",
          "rds:DescribeDBInstances",
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "optimizer_profile" {
  name = "${var.environment}-dataiku-optimizer-profile"
  role = aws_iam_role.optimizer_role.name
  
  tags = local.common_tags
}

# CloudWatch Monitoring (Optional)
resource "aws_cloudwatch_log_group" "optimizer_logs" {
  count = var.enable_monitoring ? 1 : 0
  
  name              = "/aws/dataiku-optimizer/${var.environment}"
  retention_in_days = var.log_retention_days
  
  tags = local.common_tags
}

# Local values
locals {
  common_tags = {
    Project     = "dataiku-cloud-optimizer"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}