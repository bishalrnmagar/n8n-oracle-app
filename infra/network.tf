# --- VCN ---

resource "oci_core_vcn" "finance_vcn" {
  compartment_id = var.compartment_ocid
  display_name   = "finance-bot-vcn"
  cidr_blocks    = ["10.0.0.0/16"]
  dns_label      = "financevcn"
}

# --- Internet Gateway ---

resource "oci_core_internet_gateway" "finance_igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.finance_vcn.id
  display_name   = "finance-bot-igw"
  enabled        = true
}

# --- Route Table ---

resource "oci_core_route_table" "finance_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.finance_vcn.id
  display_name   = "finance-bot-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.finance_igw.id
  }
}

# --- Security List ---

resource "oci_core_security_list" "finance_sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.finance_vcn.id
  display_name   = "finance-bot-sl"

  # Allow all egress
  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
    stateless   = false
  }

  # SSH
  ingress_security_rules {
    source    = "0.0.0.0/0"
    protocol  = "6" # TCP
    stateless = false

    tcp_options {
      min = 22
      max = 22
    }
  }

  # HTTP
  ingress_security_rules {
    source    = "0.0.0.0/0"
    protocol  = "6"
    stateless = false

    tcp_options {
      min = 80
      max = 80
    }
  }

  # HTTPS
  ingress_security_rules {
    source    = "0.0.0.0/0"
    protocol  = "6"
    stateless = false

    tcp_options {
      min = 443
      max = 443
    }
  }

  # n8n (5678)
  ingress_security_rules {
    source    = "0.0.0.0/0"
    protocol  = "6"
    stateless = false

    tcp_options {
      min = 5678
      max = 5678
    }
  }

  # ICMP (ping)
  ingress_security_rules {
    source    = "0.0.0.0/0"
    protocol  = "1" # ICMP
    stateless = false

    icmp_options {
      type = 3
      code = 4
    }
  }
}

# --- Public Subnet ---

resource "oci_core_subnet" "finance_subnet" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.finance_vcn.id
  display_name               = "finance-bot-subnet"
  cidr_block                 = "10.0.1.0/24"
  dns_label                  = "finsub"
  route_table_id             = oci_core_route_table.finance_rt.id
  security_list_ids          = [oci_core_security_list.finance_sl.id]
  prohibit_public_ip_on_vnic = false
}
