# Amazon VPC (Virtual Private Cloud)

## What is a VPC?

A VPC is a logically isolated private network inside AWS where you launch resources like EC2, RDS and EKS. You control the IP address range, subnets, routing, gateways and firewall rules, similar to a traditional data center network.

Key points:

- A VPC is **regional** and spans all AZs in that region.
- Each region comes with a **default VPC** (172.31.0.0/16) with public subnets in every AZ. For real workloads it is better to create a custom VPC.
- Default limit is 5 VPCs per region (can be increased).

## CIDR Blocks

The VPC's IP range is defined with CIDR notation (Classless Inter-Domain Routing).

- The VPC CIDR must be between **/16** (65,536 addresses) and **/28** (16 addresses).
- Use private ranges from RFC 1918: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`.
- Avoid overlapping CIDRs with other VPCs or on-prem networks you may want to connect later (peering / VPN).
- Secondary CIDRs and IPv6 can be added later.

### Subnet Math Example

VPC: `10.0.0.0/16`

- Host bits = 32 - 16 = 16, so 2^16 = **65,536** addresses.
- Split into /24 subnets: 24 - 16 = 8 extra network bits, so 2^8 = **256** possible /24 subnets.
- Each /24 has 2^8 = **256** addresses.

| Subnet         | Range                      | Use           |
|----------------|----------------------------|---------------|
| 10.0.1.0/24    | 10.0.1.0 - 10.0.1.255      | Public, AZ-a  |
| 10.0.2.0/24    | 10.0.2.0 - 10.0.2.255      | Public, AZ-b  |
| 10.0.11.0/24   | 10.0.11.0 - 10.0.11.255    | Private, AZ-a |
| 10.0.12.0/24   | 10.0.12.0 - 10.0.12.255    | Private, AZ-b |

### AWS Reserved IPs

AWS reserves **5 IP addresses** in every subnet. For `10.0.1.0/24`:

| Address    | Reserved for                         |
|------------|--------------------------------------|
| 10.0.1.0   | Network address                      |
| 10.0.1.1   | VPC router                           |
| 10.0.1.2   | Amazon-provided DNS                  |
| 10.0.1.3   | Reserved for future use              |
| 10.0.1.255 | Network broadcast (not supported, but reserved) |

So a /24 gives 256 - 5 = **251 usable** addresses. A /28 gives only 16 - 5 = 11.

## Subnets

- A subnet is a range of IPs inside the VPC.
- Each subnet lives in **exactly one Availability Zone** and cannot span AZs.
- For high availability, create subnets in at least two AZs.
- Whether a subnet is "public" or "private" depends only on its route table.

## Route Tables

A route table has rules (routes) that decide where network traffic goes.

- Every VPC has a **main route table**; you can create custom ones.
- Each subnet is associated with exactly one route table (main table if not set explicitly).
- Every route table has a `local` route for the VPC CIDR that cannot be removed.
- The most specific route (longest prefix) wins.

Public route table:

| Destination | Target        |
|-------------|---------------|
| 10.0.0.0/16 | local         |
| 0.0.0.0/0   | igw-xxxxxxxx  |

Private route table:

| Destination | Target        |
|-------------|---------------|
| 10.0.0.0/16 | local         |
| 0.0.0.0/0   | nat-xxxxxxxx  |

## Internet Gateway (IGW)

- Allows communication between the VPC and the internet.
- Horizontally scaled, redundant and highly available; no bandwidth limit to manage.
- One IGW per VPC.
- For an instance to be reachable from the internet it needs: a route to the IGW **and** a public IP or Elastic IP **and** security group / NACL rules allowing the traffic.

## NAT Gateway

- Lets instances in **private subnets** reach the internet (e.g. for OS updates, pulling images) while preventing inbound connections from the internet.
- Placed in a **public subnet** and uses an Elastic IP (public NAT).
- AZ-scoped: for high availability, create one NAT Gateway per AZ and point each private subnet's route table to the NAT in its own AZ.
- Charged per hour plus per GB processed, so it is often one of the bigger costs in a VPC.
- VPC endpoints (Gateway endpoints for S3 and DynamoDB) can reduce NAT traffic and cost.

## Security Groups vs Network ACLs

| Feature            | Security Group                         | Network ACL                                  |
|--------------------|----------------------------------------|----------------------------------------------|
| Level              | Instance / network interface (ENI)     | Subnet                                       |
| State              | **Stateful** - return traffic allowed automatically | **Stateless** - return traffic must be explicitly allowed |
| Rules              | Allow rules only                       | Allow and Deny rules                         |
| Rule evaluation    | All rules evaluated together           | Rules evaluated in number order, first match wins |
| Default            | Deny all inbound, allow all outbound   | Default NACL allows all in and out; custom NACL denies all until rules are added |
| Applies to         | Only instances it is attached to       | All instances in the associated subnets      |
| Typical use        | Main firewall for app/DB access        | Extra layer, e.g. block a specific IP range  |

Because NACLs are stateless, outbound rules must allow **ephemeral ports** (1024-65535) for response traffic.

## Public vs Private Subnet

| Public subnet                                  | Private subnet                                  |
|------------------------------------------------|-------------------------------------------------|
| Route `0.0.0.0/0` -> Internet Gateway           | No route to IGW; `0.0.0.0/0` -> NAT Gateway (optional) |
| Instances can have public IPs                  | Instances have only private IPs                 |
| Reachable from internet (if SG allows)         | Not directly reachable from internet            |
| Load balancers, bastion hosts, NAT Gateways    | App servers, databases, EKS worker nodes        |

## 2-AZ VPC Architecture

```
                               Internet
                                  |
                         +------------------+
                         | Internet Gateway |
                         +------------------+
                                  |
+---------------------------------|----------------------------------+
| VPC 10.0.0.0/16                 |                                  |
|                +----------------+-----------------+                |
|                |                                  |                |
|                v                                  v                |
|  +----------- AZ-a ----------+    +----------- AZ-b ----------+    |
|  | Public subnet 10.0.1.0/24 |    | Public subnet 10.0.2.0/24 |    |
|  |  [ALB node]   [NAT GW-a]  |    |  [ALB node]   [NAT GW-b]  |    |
|  |                   ^       |    |                   ^       |    |
|  |-------------------|-------|    |-------------------|-------|    |
|  | Private 10.0.11.0/24      |    | Private 10.0.12.0/24      |    |
|  |  [EC2 app]  [RDS primary] |    |  [EC2 app]  [RDS standby] |    |
|  +---------------------------+    +---------------------------+    |
|                                                                    |
|  Public RT : 10.0.0.0/16 -> local, 0.0.0.0/0 -> IGW                |
|  Private RT: 10.0.0.0/16 -> local, 0.0.0.0/0 -> NAT GW (same AZ)   |
+--------------------------------------------------------------------+
```

## Terraform Example

```hcl
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = { Name = "main-vpc" }
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "ap-south-1a"
  map_public_ip_on_launch = true
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}
```

## Common Use Cases

- Hosting a multi-tier web app (public load balancer, private app and DB tiers).
- Isolating environments (dev, staging, prod) in separate VPCs.
- Connecting to on-prem networks with Site-to-Site VPN or Direct Connect.
- Connecting VPCs with VPC Peering or Transit Gateway.
- Private access to AWS services using VPC endpoints (PrivateLink).
- Running EKS clusters with worker nodes in private subnets.
