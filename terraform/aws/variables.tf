variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnets" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnets" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

variable "instance_type" {
  description = "EC2 instance type for optimizer instances"
  type        = string
  default     = "t3.medium"
}

variable "key_name" {
  description = "AWS Key Pair name for EC2 instances"
  type        = string
  default     = ""
}

variable "enable_auto_scaling" {
  description = "Enable auto scaling for optimizer instances"
  type        = bool
  default     = true
}

variable "min_size" {
  description = "Minimum number of instances in auto scaling group"
  type        = number
  default     = 1
}

variable "max_size" {
  description = "Maximum number of instances in auto scaling group"
  type        = number
  default     = 3
}

variable "desired_capacity" {
  description = "Desired number of instances in auto scaling group"
  type        = number
  default     = 1
}

variable "enable_rds" {
  description = "Enable RDS database for storing optimization data"
  type        = bool
  default     = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "enable_s3_bucket" {
  description = "Enable S3 bucket for storing reports and artifacts"
  type        = bool
  default     = true
}

variable "s3_bucket_prefix" {
  description = "Prefix for S3 bucket name"
  type        = string
  default     = "dataiku-optimizer"
}

variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring and logging"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 30
}