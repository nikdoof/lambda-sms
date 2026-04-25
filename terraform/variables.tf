variable "name" {
  description = "Name applied to all created resources. Must be unique within the AWS account/region — set distinct values when deploying multiple instances."
  type        = string

  validation {
    condition     = length(var.name) > 0 && can(regex("^[A-Za-z0-9_-]+$", var.name))
    error_message = "name must be non-empty and contain only letters, digits, hyphens, or underscores."
  }
}

variable "ssm_path_prefix" {
  description = "Path prefix for SSM Parameter Store entries. Parameters are created with placeholder values; populate them out-of-band (e.g. via the AWS CLI) after apply."
  type        = string
  default     = "/smsbot"
}

variable "kms_key_id" {
  description = "Optional KMS key ID for encrypting SecureString SSM parameters. Leave null to use the default AWS-managed key (alias/aws/ssm)."
  type        = string
  default     = null
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention for the Lambda log group and API Gateway access logs."
  type        = number
  default     = 30

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653], var.log_retention_days)
    error_message = "log_retention_days must be one of the values supported by CloudWatch Logs."
  }
}

variable "lambda_memory_mb" {
  description = "Memory size for the Lambda function."
  type        = number
  default     = 256

  validation {
    condition     = var.lambda_memory_mb >= 128 && var.lambda_memory_mb <= 10240
    error_message = "lambda_memory_mb must be between 128 and 10240."
  }
}

variable "lambda_timeout_seconds" {
  description = "Lambda execution timeout. Twilio's webhook timeout is 15s, so values above that have no effect."
  type        = number
  default     = 10

  validation {
    condition     = var.lambda_timeout_seconds >= 1 && var.lambda_timeout_seconds <= 15
    error_message = "lambda_timeout_seconds must be between 1 and 15 (Twilio's webhook timeout)."
  }
}

variable "reserved_concurrency" {
  description = "Reserved concurrent executions for the Lambda. Caps blast radius and isolates the function from other workloads. Set to -1 to disable reservation."
  type        = number
  default     = 5

  validation {
    condition     = var.reserved_concurrency == -1 || var.reserved_concurrency >= 0
    error_message = "reserved_concurrency must be -1 (unreserved) or a non-negative integer."
  }
}

variable "log_level" {
  description = "Log level for the Lambda runtime."
  type        = string
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "log_level must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL."
  }
}

variable "tags" {
  description = "Tags to apply to all resources."
  type        = map(string)
  default     = {}
}
