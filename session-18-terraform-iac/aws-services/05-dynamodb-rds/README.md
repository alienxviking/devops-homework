# Amazon DynamoDB and Amazon RDS

AWS offers both NoSQL and relational managed databases. This page covers DynamoDB (NoSQL, serverless) and RDS (managed relational), and ends with a comparison.

---

## Part 1: Amazon DynamoDB

### What is DynamoDB?

DynamoDB is a fully managed, serverless **NoSQL key-value and document database**. There are no servers to manage, it scales automatically, and it gives consistent single-digit millisecond latency at almost any scale.

- Data is replicated across 3 AZs in a region automatically.
- No fixed schema, other than the primary key.
- Accessed via API (HTTPS) and authorized with IAM, not database users.
- Global Tables provide multi-region, multi-active replication.

### Core Concepts

| Concept    | Meaning                                    | Relational equivalent |
|------------|--------------------------------------------|-----------------------|
| Table      | Collection of items                        | Table                 |
| Item       | A single record, max size **400 KB**       | Row                   |
| Attribute  | A key-value field of an item               | Column                |

Items in the same table can have different attributes. Supported types include String, Number, Binary, Boolean, Null, List, Map and Sets.

### Primary Key

Every table must have a primary key, chosen at creation time:

- **Partition key only (simple key)**: e.g. `UserId`. Must be unique per item. DynamoDB hashes this value to decide which physical partition stores the item.
- **Partition key + sort key (composite key)**: e.g. `CustomerId` + `OrderDate`. Many items can share a partition key, sorted by the sort key. The combination must be unique.

Choose a partition key with **high cardinality** (many distinct values) so traffic spreads evenly and you avoid "hot partitions".

Example item in an `Orders` table (PK = `CustomerId`, SK = `OrderDate`):

```json
{
  "CustomerId": "C1001",
  "OrderDate": "2026-10-10T14:30:00Z",
  "OrderId": "O-55821",
  "Total": 1499,
  "Status": "SHIPPED",
  "Items": ["keyboard", "mouse"]
}
```

### Capacity Modes

| Mode        | How it works                                              | Best for                          |
|-------------|-----------------------------------------------------------|-----------------------------------|
| On-demand   | Pay per read/write request, scales instantly, no planning | New or unpredictable workloads (default for new tables) |
| Provisioned | Set RCUs/WCUs, optional auto scaling, reserved capacity available | Steady, predictable traffic, cost optimization |

- 1 RCU = one strongly consistent read (or two eventually consistent reads) per second for an item up to 4 KB.
- 1 WCU = one write per second for an item up to 1 KB.

### Secondary Indexes (brief)

| Index | Keys                                        | When created           | Notes                                     |
|-------|---------------------------------------------|------------------------|-------------------------------------------|
| GSI (Global Secondary Index) | Different partition key and optional sort key | Any time | Own capacity, eventually consistent reads only, default up to 20 per table |
| LSI (Local Secondary Index)  | Same partition key, different sort key        | Only at table creation | Strongly consistent reads allowed, max 5 per table, 10 GB per partition key value |

Indexes let you query by attributes other than the primary key without scanning the whole table.

### Other Features

- **DynamoDB Streams**: ordered change log of item modifications, often used to trigger Lambda.
- **TTL**: automatically delete expired items at no cost.
- **PITR**: continuous backups with restore to any second in the recovery window (up to 35 days).
- **DAX**: in-memory cache for microsecond read latency.
- **Encryption at rest** is always on (AWS owned, AWS managed or customer managed KMS key).

```bash
aws dynamodb create-table \
  --table-name Orders \
  --attribute-definitions AttributeName=CustomerId,AttributeType=S AttributeName=OrderDate,AttributeType=S \
  --key-schema AttributeName=CustomerId,KeyType=HASH AttributeName=OrderDate,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```

### Use Cases

- User sessions, shopping carts, user profiles.
- Gaming leaderboards and player state.
- IoT and event data with high write rates.
- Serverless apps (API Gateway + Lambda + DynamoDB).
- Metadata store, e.g. Terraform state locking in older setups.

---

## Part 2: Amazon RDS

### What is RDS?

Amazon RDS (Relational Database Service) is a managed service for running relational (SQL) databases. AWS handles provisioning, OS and engine patching, backups, monitoring and failover. You still choose the instance size, storage and configuration, and you design the schema.

### Supported Engines

| Engine            | Notes                                                       |
|-------------------|-------------------------------------------------------------|
| MySQL             | Popular open-source engine                                  |
| PostgreSQL        | Open source, advanced features and extensions               |
| MariaDB           | Community fork of MySQL                                     |
| Oracle            | Commercial; License Included or BYOL                        |
| Microsoft SQL Server | Commercial; several editions                             |
| IBM Db2           | Commercial; added in 2023                                   |
| Amazon Aurora     | AWS-built, MySQL- and PostgreSQL-compatible, storage replicated 6 ways across 3 AZs, up to 15 replicas, Serverless v2 option |

### DB Instances and Classes

- A **DB instance** is an isolated database environment running one engine, with its own endpoint.
- The **DB instance class** sets compute and memory, similar to EC2 types:
  - `db.t4g` / `db.t3` - burstable, for dev/test and small apps
  - `db.m6g` / `db.m7g` - general purpose
  - `db.r6g` / `db.r7g` - memory optimized, for heavy production databases
- Storage uses EBS: gp3 (general purpose) or io1/io2 (provisioned IOPS), with optional storage autoscaling.

### Security

- **Network isolation**: launch in a VPC using a **DB subnet group** (private subnets in at least 2 AZs). Keep "Publicly accessible" set to No.
- **Security groups**: allow the DB port (e.g. 3306 for MySQL, 5432 for PostgreSQL) only from the application's security group.
- **Encryption at rest** with KMS (must be enabled at creation; covers storage, backups, snapshots and replicas).
- **Encryption in transit** using SSL/TLS.
- **IAM database authentication** (MySQL, MariaDB, PostgreSQL): connect with a short-lived token instead of a password.
- **Secrets Manager** integration to store and rotate the master password.

### Backups

| Type               | Details                                                                 |
|--------------------|-------------------------------------------------------------------------|
| Automated backups  | Daily snapshot + transaction logs, retention 1-35 days, deleted with the instance by default |
| Point-in-time recovery (PITR) | Restore to any second within the retention period (typically up to the last ~5 minutes) |
| Manual snapshots   | Taken on demand, kept until you delete them, can be copied across regions/accounts |

A restore always creates a **new DB instance** with a new endpoint.

### Multi-AZ

- Provides **high availability**, not read scaling (for the classic setup).
- **Multi-AZ DB instance**: a synchronous standby in another AZ. On failure, RDS fails over automatically by updating the DNS endpoint (usually 1-2 minutes). The standby does not serve reads.
- **Multi-AZ DB cluster** (MySQL/PostgreSQL): one writer and two readable standbys in three AZs, faster failover.

### Read Replicas

- Used for **read scaling**: asynchronous copies that serve read-only queries.
- Up to 15 read replicas for MySQL, MariaDB and PostgreSQL (fewer for Oracle and SQL Server).
- Can be in the same region or **cross-region** (also useful for DR).
- Can be promoted to a standalone database.
- The app must send reads to the replica endpoint explicitly.

```bash
aws rds create-db-instance \
  --db-instance-identifier app-db \
  --engine postgres \
  --db-instance-class db.t4g.micro \
  --allocated-storage 20 \
  --master-username dbadmin \
  --manage-master-user-password \
  --multi-az \
  --storage-encrypted \
  --backup-retention-period 7 \
  --no-publicly-accessible
```

### Use Cases

- Web and mobile application backends (e-commerce, CMS).
- Applications needing transactions, joins and strong consistency (banking, ERP, CRM).
- Migrating existing on-prem MySQL/PostgreSQL/Oracle/SQL Server databases.
- Reporting with read replicas to offload the primary.

---

## DynamoDB vs RDS

| Feature            | DynamoDB                                     | RDS                                            |
|--------------------|----------------------------------------------|------------------------------------------------|
| Database type      | NoSQL (key-value / document)                 | Relational (SQL)                               |
| Schema             | Flexible, only primary key is fixed          | Fixed schema with tables, columns, constraints |
| Query language     | API calls, PartiQL; no joins                 | Full SQL with joins, aggregations              |
| Server management  | Serverless, nothing to size                  | Choose instance class and storage              |
| Scaling            | Automatic horizontal scaling                 | Vertical (bigger instance) + read replicas     |
| Performance        | Single-digit ms at any scale                 | Depends on instance size, queries and indexes  |
| Transactions       | Supported (ACID across up to 100 items)      | Full ACID transactions                         |
| High availability  | Built in across 3 AZs; Global Tables for multi-region | Multi-AZ deployment option              |
| Backups            | On-demand + PITR (up to 35 days)             | Automated (1-35 days) + manual snapshots       |
| Authentication     | IAM only                                     | DB users/passwords, optional IAM auth          |
| Pricing            | Per request or provisioned capacity + storage| Per instance-hour + storage + I/O (engine dependent) |
| Best for           | High-scale, simple access patterns, serverless apps | Complex queries, relationships, existing SQL apps |

**Rule of thumb**: if the access patterns are known and simple (get by key) and scale matters most, use DynamoDB. If the data is relational and needs flexible queries and joins, use RDS or Aurora.
