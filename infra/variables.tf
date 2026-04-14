variable "tenancy_ocid" {
  description = "OCI tenancy OCID"
  type        = string
}

variable "user_ocid" {
  description = "OCI user OCID"
  type        = string
}

variable "fingerprint" {
  description = "API key fingerprint"
  type        = string
}

variable "private_key_path" {
  description = "Path to OCI API private key PEM file"
  type        = string
}

variable "region" {
  description = "OCI region (e.g., ap-mumbai-1)"
  type        = string
  default     = "ap-mumbai-1"
}

variable "compartment_ocid" {
  description = "Compartment OCID (use tenancy OCID for root compartment)"
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key for VM access"
  type        = string
}

variable "duckdns_subdomain" {
  description = "DuckDNS subdomain (without .duckdns.org)"
  type        = string
}

variable "duckdns_token" {
  description = "DuckDNS token for dynamic DNS updates"
  type        = string
  sensitive   = true
}

variable "telegram_bot_token" {
  description = "Telegram Bot API token"
  type        = string
  sensitive   = true
}

variable "n8n_basic_auth_user" {
  description = "n8n basic auth username"
  type        = string
  default     = "admin"
}

variable "n8n_basic_auth_password" {
  description = "n8n basic auth password"
  type        = string
  sensitive   = true
}

variable "n8n_db_password" {
  description = "PostgreSQL password for n8n database"
  type        = string
  sensitive   = true
}

variable "availability_domain_index" {
  description = "Index of the availability domain to use (0, 1, or 2). Try different values if you get 'Out of host capacity'"
  type        = number
  default     = 0
}

variable "use_amd_fallback" {
  description = "Set to true to use AMD VM.Standard.E2.1.Micro (Always Free) instead of ARM A1.Flex when ARM capacity is unavailable"
  type        = bool
  default     = false
}
