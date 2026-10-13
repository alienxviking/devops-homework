# Amazon EC2 (Elastic Compute Cloud)

## What is EC2?

EC2 provides resizable virtual servers (called **instances**) in the AWS cloud. You choose the OS, CPU, memory, storage and networking, and you pay only for what you use. It is the basic compute building block in AWS and is regional (instances run in a specific Availability Zone).

## AMI (Amazon Machine Image)

An AMI is a template used to launch an instance. It contains:

- The root volume snapshot (OS + any pre-installed software)
- Launch permissions (who can use it)
- Block device mapping (which volumes to attach)

Types of AMIs:

- **AWS provided**: Amazon Linux 2023, Ubuntu, Windows Server, etc.
- **Marketplace**: third-party images, sometimes with license cost.
- **Custom**: created from your own configured instance (useful for "golden images", often built with Packer).

AMIs are region-specific. To use one in another region, copy it.

## Instance Types

Instance types define the hardware (vCPU, memory, network, storage).

### Naming

```
  t 3 a . micro
  | | |   |
  | | |   +-- size (nano, micro, small, medium, large, xlarge, 2xlarge ...)
  | | +------ extra attribute (a = AMD, g = Graviton/ARM, n = network, d = local NVMe)
  | +-------- generation
  +---------- family
```

So `t3.micro` is family **t** (burstable), generation **3**, size **micro**. `m7g.large` is general purpose, 7th generation, Graviton (ARM), large.

### Families

| Family | Category                  | Examples        | Typical use                          |
|--------|---------------------------|-----------------|--------------------------------------|
| T      | Burstable general purpose | t3, t4g         | Dev/test, small web apps             |
| M      | General purpose           | m6i, m7g        | App servers, balanced workloads      |
| C      | Compute optimized         | c6i, c7g        | Batch processing, high-performance web |
| R, X   | Memory optimized          | r6i, x2idn      | In-memory DBs, caches, analytics     |
| I, D   | Storage optimized         | i4i, d3         | High IOPS databases, data warehouses |
| P, G, Inf, Trn | Accelerated computing | p5, g5, inf2 | ML training/inference, graphics      |

## Key Pairs

- Used to log in securely (SSH for Linux, password decryption for Windows).
- AWS stores the **public key**; you download the **private key** (`.pem`) once.
- If you lose the private key, you cannot recover it from AWS.
- Alternatives that avoid managing keys: **EC2 Instance Connect** and **Systems Manager Session Manager**.

```bash
aws ec2 create-key-pair --key-name my-key \
  --query 'KeyMaterial' --output text > my-key.pem
chmod 400 my-key.pem
ssh -i my-key.pem ec2-user@<public-ip>
```

## Security Groups

A security group is a virtual firewall attached to an instance's network interface.

- **Stateful**: if inbound traffic is allowed, the response is automatically allowed out (and vice versa).
- Only **allow** rules; there are no deny rules.
- By default: all inbound denied, all outbound allowed.
- Rules can reference CIDR ranges or other security groups.
- An instance can have multiple security groups; rules are combined.

Example: allow SSH from my IP and HTTP from anywhere.

| Type | Protocol | Port | Source          |
|------|----------|------|-----------------|
| SSH  | TCP      | 22   | 203.0.113.10/32 |
| HTTP | TCP      | 80   | 0.0.0.0/0       |

## EBS (Elastic Block Store)

EBS provides network-attached block storage volumes for instances.

- A volume lives in one AZ and attaches to instances in the same AZ.
- Data persists independently of the instance (unless "delete on termination" is set, which is the default for root volumes).

| Volume type | Kind | Notes                                                      |
|-------------|------|------------------------------------------------------------|
| gp3         | SSD  | Default general purpose; 3,000 IOPS / 125 MB/s baseline, can be scaled independently of size |
| gp2         | SSD  | Older; IOPS tied to volume size                            |
| io2 Block Express | SSD | Provisioned IOPS, high durability, for critical DBs   |
| st1         | HDD  | Throughput optimized, big sequential data                  |
| sc1         | HDD  | Cold HDD, lowest cost                                      |

**Snapshots**:

- Point-in-time backups of EBS volumes stored in S3 (managed by AWS).
- Incremental: only changed blocks are saved after the first snapshot.
- Can be copied across regions and used to create new volumes or AMIs.
- Can be automated with Amazon Data Lifecycle Manager or AWS Backup.

Instance store is a different option: physically attached temporary disks whose data is lost when the instance stops.

## Public IP, Private IP and Elastic IP

| Type        | Description                                                                 |
|-------------|-----------------------------------------------------------------------------|
| Private IP  | From the subnet CIDR; used inside the VPC; stays the same for the life of the instance |
| Public IP   | Auto-assigned (if enabled on the subnet); **changes** when the instance is stopped and started |
| Elastic IP  | Static public IPv4 you allocate to your account and associate with an instance |

Note: AWS charges for all public IPv4 addresses (including Elastic IPs), whether in use or not.

## Instance Lifecycle

```
    launch
      |
      v
 +---------+             start              +---------+
 | pending |<-------------------------------| stopped |
 +---------+                                +---------+
      |                                       ^      |
      v                                       |      |
 +---------+                            +----------+ |
 | running |---- stop / hibernate ----->| stopping | |
 +---------+                            +----------+ |
      |   (reboot keeps it running)                  |
      | terminate                          terminate |
      v                                              |
 +---------------+                                   |
 | shutting-down |<----------------------------------+
 +---------------+
      |
      v
 +------------+
 | terminated |
 +------------+
```

| State          | Billing for compute | Notes                                          |
|----------------|---------------------|------------------------------------------------|
| pending        | No                  | Instance is being prepared                     |
| running        | Yes                 | Ready for use                                  |
| stopping       | No (unless hibernating) | Preparing to stop                          |
| stopped        | No                  | EBS storage still billed                       |
| shutting-down  | No                  | Preparing to terminate                         |
| terminated     | No                  | Permanently deleted, cannot be restarted       |

**Hibernate**: saves the contents of RAM to the encrypted EBS root volume, then stops. On start, RAM is restored, so applications resume where they left off. It must be enabled at launch and is supported only on certain instance types and AMIs.

## Pricing Models

| Model              | Description                                               | Good for                         |
|--------------------|-----------------------------------------------------------|----------------------------------|
| On-Demand          | Pay per second/hour, no commitment                        | Short-term, unpredictable loads  |
| Savings Plans      | Commit to $/hour for 1 or 3 years, up to ~72% off         | Steady usage, flexible types     |
| Reserved Instances | Commit to a specific instance config for 1 or 3 years     | Steady, predictable workloads    |
| Spot               | Spare capacity, up to ~90% off, can be interrupted with 2-minute notice | Batch, CI runners, stateless jobs |
| Dedicated Hosts    | Physical server dedicated to you                          | Licensing / compliance needs     |

## Terraform Example

```hcl
resource "aws_instance" "web" {
  ami                    = "ami-0abcdef1234567890"
  instance_type          = "t3.micro"
  key_name               = "my-key"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]

  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true
  }

  tags = { Name = "web-server" }
}
```

## Common Use Cases

- Hosting web applications and APIs.
- Running self-managed databases or legacy apps (lift-and-shift).
- Jenkins / CI build agents (often on Spot).
- Batch processing and HPC workloads.
- GPU instances for ML training and inference.
- Worker nodes for Kubernetes (EKS) clusters, usually through Auto Scaling Groups.
