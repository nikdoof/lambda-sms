locals {
  ssm_prefix = trimsuffix(var.ssm_path_prefix, "/")

  ssm_secure_params = {
    "telegram/bot_token" = {}
    "twilio/auth_token"  = {}
  }

  ssm_string_params = {
    "telegram/subscribers" = {
      description = "Comma-separated list of Telegram chat IDs to forward messages to."
    }
  }
}

resource "aws_ssm_parameter" "secure" {
  for_each = local.ssm_secure_params

  name        = "${local.ssm_prefix}/${each.key}"
  type        = "SecureString"
  value       = "REPLACE_ME"
  key_id      = var.kms_key_id
  description = "Managed by smsbot Terraform module — value populated out-of-band."
  tags        = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "plain" {
  for_each = local.ssm_string_params

  name        = "${local.ssm_prefix}/${each.key}"
  type        = "String"
  value       = "REPLACE_ME"
  description = each.value.description
  tags        = var.tags

  lifecycle {
    ignore_changes = [value]
  }
}
