data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["amazon", "099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-*"]
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-EOT
    #!/bin/bash
    apt-get update -y && apt-get install -y nginx
    echo "<h1>${local.name} web server - provisioned by Terraform</h1>" > /var/www/html/index.html
  EOT

  # explicit dependency: the instance needs the internet route before user_data runs apt-get
  depends_on = [aws_route_table_association.public]

  tags = { Name = "${local.name}-web" }
}
