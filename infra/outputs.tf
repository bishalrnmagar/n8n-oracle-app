output "instance_public_ip" {
  description = "Public IP of the finance bot VM"
  value       = oci_core_instance.finance_vm.public_ip
}

output "instance_id" {
  description = "OCID of the compute instance"
  value       = oci_core_instance.finance_vm.id
}

output "n8n_url" {
  description = "n8n dashboard URL"
  value       = "https://${var.duckdns_subdomain}.duckdns.org"
}

output "webhook_url" {
  description = "Telegram webhook URL for n8n"
  value       = "https://${var.duckdns_subdomain}.duckdns.org/webhook/telegram"
}

output "ssh_command" {
  description = "SSH into the instance"
  value       = "ssh ubuntu@${oci_core_instance.finance_vm.public_ip}"
}
