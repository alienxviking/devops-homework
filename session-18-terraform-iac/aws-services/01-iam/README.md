# AWS IAM (Identity and Access Management)

## What is IAM?

IAM is the AWS service that controls **who** can access your AWS account (authentication) and **what** they are allowed to do (authorization). It is a global service, so it is not tied to a single region, and there is no extra charge for using it.

Every API call made to AWS, whether from the console, the CLI, an SDK or Terraform, is checked against IAM before it is allowed.

## Core Components

### Users

- An IAM user represents a single person or application that needs long-term access.
- A user can have a console password and/or access keys (access key ID + secret access key) for CLI/API use.
- New users have **no permissions** by default.
- For human users, AWS now recommends IAM Identity Center (federated access) instead of creating many IAM users.

### Groups

- A group is a collection of users. Policies attached to a group apply to every user in it.
- Example groups: `Developers`, `Admins`, `ReadOnly`.
- Groups cannot be nested, and a group is not an identity that can be referenced as a principal in a policy.

### Roles

- A role is an identity with permissions but **no long-term credentials**.
- Someone or something *assumes* the role and receives temporary credentials from AWS STS.
- Each role has a **trust policy** (who can assume it) and **permission policies** (what it can do).
- Common uses: EC2 instance profiles, Lambda execution roles, cross-account access, federated users.

Example trust policy that lets EC2 assume a role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "ec2.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Policies

A policy is a JSON document that defines permissions. Each statement has:

| Element     | Meaning                                         |
|-------------|-------------------------------------------------|
| `Effect`    | `Allow` or `Deny`                               |
| `Action`    | API actions, e.g. `s3:GetObject`                |
| `Resource`  | ARN(s) the action applies to                    |
| `Condition` | Optional extra checks (IP, MFA, tags, etc.)     |
| `Principal` | Only in resource-based / trust policies         |

Example identity-based policy giving read access to one bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListBucket",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::my-app-bucket"
    },
    {
      "Sid": "ReadObjects",
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::my-app-bucket/*"
    }
  ]
}
```

## Policy Types

### Identity-based vs Resource-based

| Identity-based                                  | Resource-based                                    |
|-------------------------------------------------|---------------------------------------------------|
| Attached to a user, group or role               | Attached to a resource (S3 bucket, SQS queue, KMS key) |
| No `Principal` element (the identity is implied)| Must specify a `Principal`                        |
| "What can this identity do?"                    | "Who can access this resource?"                   |
| Example: policy on `Developers` group           | Example: S3 bucket policy                         |

### Managed vs Inline

| Type                    | Description                                                         |
|-------------------------|---------------------------------------------------------------------|
| AWS managed             | Created and maintained by AWS, e.g. `ReadOnlyAccess`, `AmazonS3ReadOnlyAccess` |
| Customer managed        | Created by you, reusable across many identities, versioned          |
| Inline                  | Embedded directly in one user/group/role, deleted along with it     |

Customer managed policies are usually preferred because they are reusable and easier to audit. Inline policies are useful when a permission must strictly belong to one identity.

Other policy types worth knowing: **permission boundaries** (max permissions an identity can have), **SCPs** in AWS Organizations, and **session policies**.

## Permission Evaluation Logic

When a request is made, AWS evaluates all applicable policies:

1. By default, everything is **implicitly denied**.
2. If any policy has an **explicit Deny** that matches, the request is denied. Explicit deny always wins.
3. If there is no explicit deny and at least one **Allow** matches, the request is allowed (subject to SCPs, permission boundaries and session policies also allowing it).
4. Otherwise the implicit deny applies.

```
Request -> Explicit Deny? --yes--> DENY
              | no
              v
         Any Allow? ---no---> DENY (implicit)
              | yes
              v
            ALLOW
```

Example: a user in `Admins` has `AdministratorAccess`, but another attached policy denies `s3:DeleteBucket`. The user still cannot delete buckets.

## Principle of Least Privilege

Grant only the permissions needed for the task, nothing more.

- Start with minimal permissions and add as required.
- Scope `Resource` to specific ARNs instead of `"*"` where possible.
- Use conditions (e.g. `aws:SourceIp`, `aws:MultiFactorAuthPresent`).
- Use IAM Access Analyzer policy generation to build policies from CloudTrail activity.
- Review "last accessed" data and remove unused permissions.

## IAM Best Practices

- **Protect the root user**: enable MFA, do not create root access keys, use it only for the few tasks that require it.
- **Enable MFA** for all human users.
- **Use IAM Identity Center** (formerly AWS SSO) for workforce access with temporary credentials.
- **Use roles for workloads**: EC2 instance profiles, Lambda execution roles, ECS task roles. Never hard-code access keys in code or AMIs.
- **Prefer temporary credentials** over long-term access keys.
- **Rotate access keys** regularly if they must exist, and delete unused ones.
- **Use groups** to assign permissions instead of attaching policies to individual users.
- **Use IAM Access Analyzer** to find resources shared outside the account and to validate policies.
- **Strong password policy** for any remaining IAM users.
- **Monitor with CloudTrail** to log all IAM and API activity.

## Useful AWS CLI Commands

```bash
# Create a group and attach a managed policy
aws iam create-group --group-name Developers
aws iam attach-group-policy --group-name Developers \
  --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess

# Create a user and add to group
aws iam create-user --user-name snehangshu
aws iam add-user-to-group --user-name snehangshu --group-name Developers

# Check who you are
aws sts get-caller-identity
```

## Terraform Example

```hcl
resource "aws_iam_role" "ec2_role" {
  name = "ec2-s3-read-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "s3_read" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "ec2-s3-read-profile"
  role = aws_iam_role.ec2_role.name
}
```

## Common Use Cases

- Giving developers read-only access to production and full access to dev.
- Allowing an EC2 instance to read from S3 without storing keys on the instance.
- Lambda execution role to write logs to CloudWatch and read from DynamoDB.
- Cross-account access (e.g. a CI/CD account deploying into a prod account).
- CI/CD pipelines (GitHub Actions) using OIDC federation to assume a role instead of static keys.
- Enforcing MFA for sensitive actions using policy conditions.
