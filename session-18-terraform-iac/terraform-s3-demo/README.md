# terraform-s3-demo

Creates an S3 bucket with Terraform: versioning, AES256 server-side encryption, public access block, and one object (`hello.txt`).

| File | Purpose |
|---|---|
| `provider.tf` | Terraform + AWS provider version, region, default tags |
| `variables.tf` | Input variables (region, bucket name, environment, versioning flag) |
| `terraform.tfvars` | Values for the variables |
| `main.tf` | Resources: bucket, versioning, encryption, public access block, object |
| `outputs.tf` | Bucket name, ARN, region, versioning status |

> Runs on real AWS (`ap-south-1`). Credentials come from `aws configure` (IAM user, not root) - never put keys in `.tf` files.

```bash
aws configure            # access key of the IAM user, region ap-south-1
aws sts get-caller-identity
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
