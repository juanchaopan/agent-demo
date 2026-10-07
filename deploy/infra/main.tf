terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}

variable "bundle_id" { default = "micro_3_0" } # $7 1GB; small_3_0 = $12 2GB

provider "aws" { region = "ca-central-1" }

resource "aws_lightsail_key_pair" "deploy" {
  name       = "agent-demo-key"
  public_key = file(pathexpand("~/.ssh/agent-demo.pub"))
}

resource "aws_lightsail_instance" "app" {
  name              = "agent-demo"
  availability_zone = "ca-central-1a"
  blueprint_id      = "ubuntu_24_04"
  bundle_id         = var.bundle_id
  key_pair_name     = aws_lightsail_key_pair.deploy.name
  user_data         = file("${path.module}/cloud-init.sh")
}

resource "aws_lightsail_static_ip" "app" { name = "agent-demo-ip" }

# replace_triggered_by: a new instance keeps the old name, so Terraform would
# otherwise not notice that the IP and ports were dropped with the old one.
resource "aws_lightsail_static_ip_attachment" "app" {
  static_ip_name = aws_lightsail_static_ip.app.name
  instance_name  = aws_lightsail_instance.app.name
  lifecycle { replace_triggered_by = [aws_lightsail_instance.app] }
}

resource "aws_lightsail_instance_public_ports" "app" {
  instance_name = aws_lightsail_instance.app.name
  dynamic "port_info" {
    for_each = [22, 80, 443]
    content {
      protocol  = "tcp"
      from_port = port_info.value
      to_port   = port_info.value
    }
  }
  lifecycle { replace_triggered_by = [aws_lightsail_instance.app] }
}

output "public_ip" { value = aws_lightsail_static_ip.app.ip_address }
