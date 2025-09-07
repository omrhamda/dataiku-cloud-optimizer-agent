output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.networking.private_subnet_ids
}

output "optimizer_instance_ids" {
  description = "IDs of the optimizer instances"
  value       = module.compute.instance_ids
}

output "auto_scaling_group_arn" {
  description = "ARN of the auto scaling group"
  value       = module.compute.auto_scaling_group_arn
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = var.enable_rds ? module.storage.rds_endpoint : null
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = var.enable_s3_bucket ? module.storage.s3_bucket_name : null
}

output "iam_role_arn" {
  description = "ARN of the IAM role for optimizer instances"
  value       = aws_iam_role.optimizer_role.arn
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = var.enable_monitoring ? aws_cloudwatch_log_group.optimizer_logs[0].name : null
}