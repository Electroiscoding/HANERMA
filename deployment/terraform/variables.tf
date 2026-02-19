variable "aws_region" {
  description = "AWS region for deployment"
  default     = "us-east-1"
}

variable "subnet_ids" {
  description = "List of private subnet IDs for EKS"
  type        = list(string)
}

variable "cluster_name" {
  description = "Name of the EKS resource"
  default     = "hanerma-prod"
}

variable "node_instance_type" {
  description = "EC2 instance size for GraphRAG workloads"
  default     = "t3.xlarge"
}
