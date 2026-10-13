# terraform-s3-demo

Creates an S3 bucket with Terraform: versioning, AES256 server-side encryption, public access block, and one object (`hello.txt`).

| File | Purpose |
|---|---|
| `provider.tf` | Terraform + AWS provider version, provider settings (LocalStack endpoint), default tags |
| `variables.tf` | Input variables (region, bucket name, environment, versioning flag) |
| `terraform.tfvars` | Values for the variables |
| `main.tf` | Resources: bucket, versioning, encryption, public access block, object |
| `outputs.tf` | Bucket name, ARN, region, versioning status |

> I don't have an AWS account set up, so the provider points to **LocalStack** (an AWS API emulator on `localhost:4566`) with dummy keys. Same code works on real AWS after removing the `endpoints` / `skip_*` lines and the dummy keys.

```bash
docker run -d --name localstack -p 4566:4566 localstack/localstack:4.4
terraform init
terraform fmt
terraform validate
terraform plan -out=tfplan
terraform apply tfplan
terraform show
terraform output
terraform destroy
```

Full walkthrough with screenshots: [../README.md](../README.md)
