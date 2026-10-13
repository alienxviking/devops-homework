# Amazon S3 (Simple Storage Service)

## What is S3?

S3 is AWS's object storage service. Instead of files in folders or blocks on a disk, data is stored as **objects** inside **buckets**, and accessed over HTTPS using an API.

Key points:

- Practically unlimited storage, pay for what you store and transfer.
- Designed for 99.999999999% (11 nines) durability by storing data across multiple AZs (except One Zone classes).
- Strong read-after-write consistency for all PUT and DELETE operations.
- Used as a backend by many other AWS services (CloudTrail logs, EBS snapshots, Terraform state, etc.).

## Buckets

A bucket is a container for objects.

- Bucket names must be **globally unique** across all AWS accounts (general purpose buckets share one namespace).
- Naming rules: 3-63 characters, lowercase letters, numbers, hyphens and dots; must start and end with a letter or number.
- A bucket is created in a **specific region**, and data stays in that region unless you replicate it.
- The S3 console looks global, but each bucket belongs to one region.
- Default limit is 10,000 general purpose buckets per account (can be raised).

```bash
aws s3 mb s3://snehangshu-devops-demo-2026 --region ap-south-1
aws s3 ls
```

## Objects

An object is the actual data plus information about it.

| Part        | Description                                                         |
|-------------|---------------------------------------------------------------------|
| Key         | The full name/path of the object, e.g. `logs/2026/10/app.log`       |
| Value       | The data (bytes)                                                    |
| Metadata    | System metadata (Content-Type, Last-Modified) and user metadata (`x-amz-meta-*`) |
| Version ID  | Present when versioning is enabled                                  |
| Tags        | Up to 10 key-value tags, useful for lifecycle rules and access control |

Notes:

- S3 has a flat structure. "Folders" are just key prefixes (`logs/2026/`).
- Max object size is **5 TB**.
- A single PUT upload is limited to 5 GB. For anything over ~100 MB, **multipart upload** is recommended (the AWS CLI does this automatically).

```bash
aws s3 cp app.log s3://snehangshu-devops-demo-2026/logs/app.log
aws s3 sync ./site s3://snehangshu-devops-demo-2026/site/
```

## Storage Classes

| Storage class                 | AZs | Min storage duration | Retrieval      | Typical use                          |
|-------------------------------|-----|----------------------|----------------|--------------------------------------|
| S3 Standard                   | 3+  | None                 | Milliseconds   | Frequently accessed data             |
| S3 Intelligent-Tiering        | 3+  | None                 | Milliseconds (archive tiers optional) | Unknown or changing access patterns |
| S3 Express One Zone           | 1   | None (hourly)        | Single-digit ms| Very low latency, high request rates |
| S3 Standard-IA                | 3+  | 30 days              | Milliseconds   | Infrequent access, needs fast retrieval |
| S3 One Zone-IA                | 1   | 30 days              | Milliseconds   | Re-creatable infrequent data         |
| S3 Glacier Instant Retrieval  | 3+  | 90 days              | Milliseconds   | Archive accessed about once a quarter |
| S3 Glacier Flexible Retrieval | 3+  | 90 days              | Minutes to hours | Backups, archives                  |
| S3 Glacier Deep Archive       | 3+  | 180 days             | Up to 12-48 hours | Long-term compliance archives     |

As you move down the table, storage cost generally goes down and retrieval cost/time goes up.

## Versioning

- Keeps multiple versions of an object in the same bucket.
- Protects against accidental overwrite and delete. A delete just adds a **delete marker**; older versions can still be restored.
- Bucket states: unversioned (default), versioning-enabled, versioning-suspended. Once enabled it can only be suspended, not fully turned off.
- Each version is billed as a separate object, so combine with lifecycle rules.
- Required for replication (CRR/SRR). MFA Delete can be added for extra protection.

```bash
aws s3api put-bucket-versioning \
  --bucket snehangshu-devops-demo-2026 \
  --versioning-configuration Status=Enabled
```

## Lifecycle Policies

Lifecycle rules automatically move objects to cheaper classes or delete them after a set time.

- **Transition actions**: move to another storage class.
- **Expiration actions**: delete objects (or old versions).

Example: move logs to Standard-IA after 30 days, Glacier after 90, delete after 365, and clean up old versions and incomplete uploads.

```json
{
  "Rules": [
    {
      "ID": "logs-archive-rule",
      "Status": "Enabled",
      "Filter": { "Prefix": "logs/" },
      "Transitions": [
        { "Days": 30, "StorageClass": "STANDARD_IA" },
        { "Days": 90, "StorageClass": "GLACIER" }
      ],
      "Expiration": { "Days": 365 },
      "NoncurrentVersionExpiration": { "NoncurrentDays": 30 },
      "AbortIncompleteMultipartUpload": { "DaysAfterInitiation": 7 }
    }
  ]
}
```

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket snehangshu-devops-demo-2026 \
  --lifecycle-configuration file://lifecycle.json
```

## Encryption

**In transit**: use HTTPS (TLS). You can enforce it with a bucket policy condition `aws:SecureTransport`.

**At rest**:

| Option       | Who manages keys                  | Notes                                                       |
|--------------|-----------------------------------|-------------------------------------------------------------|
| SSE-S3       | S3 (AES-256)                      | **Default** for all new objects since January 2023, no extra cost |
| SSE-KMS      | AWS KMS (AWS managed or customer managed key) | Key usage logged in CloudTrail, fine-grained key policies; use S3 Bucket Keys to reduce KMS cost |
| DSSE-KMS     | AWS KMS                           | Two layers of encryption, for strict compliance needs       |
| SSE-C        | You provide the key on every request | AWS does not store the key; lose it and the data is lost  |
| Client-side  | You, before upload                | Data is already encrypted when it reaches S3 (e.g. AWS Encryption SDK) |

## Bucket Policies

A bucket policy is a **resource-based** JSON policy attached to the bucket. It can grant access to other accounts, services or (rarely) the public, and can enforce rules for everyone.

Example: allow read access for a specific IAM role and deny any request not using HTTPS.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowAppRoleRead",
      "Effect": "Allow",
      "Principal": { "AWS": "arn:aws:iam::123456789012:role/app-role" },
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::snehangshu-devops-demo-2026/*"
    },
    {
      "Sid": "DenyInsecureTransport",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::snehangshu-devops-demo-2026",
        "arn:aws:s3:::snehangshu-devops-demo-2026/*"
      ],
      "Condition": { "Bool": { "aws:SecureTransport": "false" } }
    }
  ]
}
```

Note: ACLs are disabled by default on new buckets (Object Ownership = "Bucket owner enforced"), so access is controlled with IAM and bucket policies.

## Block Public Access

Block Public Access (BPA) is a safety switch that overrides any policy or ACL that would make data public.

Four settings:

1. `BlockPublicAcls` - reject new public ACLs.
2. `IgnorePublicAcls` - ignore existing public ACLs.
3. `BlockPublicPolicy` - reject bucket policies that grant public access.
4. `RestrictPublicBuckets` - restrict access to buckets with public policies to AWS services and authorized users only.

All four are **on by default** for new buckets, and can also be set at the account level. Keep them on unless the bucket really needs to be public (for a public website, CloudFront with Origin Access Control is the better approach).

## Terraform Example

```hcl
resource "aws_s3_bucket" "demo" {
  bucket = "snehangshu-devops-demo-2026"
}

resource "aws_s3_bucket_versioning" "demo" {
  bucket = aws_s3_bucket.demo.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_public_access_block" "demo" {
  bucket                  = aws_s3_bucket.demo.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}
```

## Common Use Cases

- Storing application assets, user uploads, images and videos.
- Static website hosting (usually behind CloudFront).
- Backups and disaster recovery, archives with Glacier classes.
- Log storage (ALB, CloudTrail, VPC Flow Logs).
- Data lake for analytics with Athena, Glue, EMR.
- Terraform remote state backend (with native S3 state locking, or DynamoDB in older setups).
- Storing build artifacts from CI/CD pipelines.
