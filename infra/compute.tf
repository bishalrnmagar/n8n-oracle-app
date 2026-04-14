# --- Availability Domain ---

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

# --- Shape selection ---

locals {
  shape     = var.use_amd_fallback ? "VM.Standard.E2.1.Micro" : "VM.Standard.A1.Flex"
  is_flex   = !var.use_amd_fallback
  ad_index  = min(var.availability_domain_index, length(data.oci_identity_availability_domains.ads.availability_domains) - 1)
}

# --- Ubuntu 22.04 Image (matches selected shape) ---

data "oci_core_images" "ubuntu" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                    = local.shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

# --- Compute Instance (Always Free) ---

resource "oci_core_instance" "finance_vm" {
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[local.ad_index].name
  display_name        = "finance-bot"
  shape               = local.shape

  dynamic "shape_config" {
    for_each = local.is_flex ? [1] : []
    content {
      ocpus         = 1
      memory_in_gbs = 6
    }
  }

  source_details {
    source_type             = "image"
    source_id               = data.oci_core_images.ubuntu.images[0].id
    boot_volume_size_in_gbs = 50
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.finance_subnet.id
    assign_public_ip = true
    display_name     = "finance-bot-vnic"
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data           = base64encode(templatefile("${path.module}/cloud-init.yaml", {
      duckdns_subdomain       = var.duckdns_subdomain
      duckdns_token           = var.duckdns_token
      n8n_basic_auth_user     = var.n8n_basic_auth_user
      n8n_basic_auth_password = var.n8n_basic_auth_password
      n8n_db_password         = var.n8n_db_password
    }))
  }

  lifecycle {
    ignore_changes = [source_details[0].source_id]
  }
}
