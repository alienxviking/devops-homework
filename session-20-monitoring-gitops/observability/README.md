# Observability - Task 2

## What is Observability?

Observability is the ability to understand the internal state of a system by looking at the data it produces. If a system is observable, I should be able to answer "why is this happening?" without shipping new code to debug it.

This data is usually grouped into **three pillars**: metrics, logs and traces.

## The Three Pillars

### 1. Metrics

Metrics are **numeric measurements collected over time** (time series). They are cheap to store, fast to query and good for dashboards and alerts.

Examples:

- CPU and memory usage of a pod
- HTTP requests per second
- Error rate (5xx responses / total requests)
- Request latency p95 / p99
- Queue length, disk usage

Example Prometheus metric and query:

```
http_requests_total{service="checkout", method="POST", status="500"} 42
```

```promql
# Error rate for the checkout service over 5 minutes
sum(rate(http_requests_total{service="checkout", status=~"5.."}[5m]))
/
sum(rate(http_requests_total{service="checkout"}[5m]))
```

Metric types in Prometheus: counter, gauge, histogram, summary.

### 2. Logs

Logs are **timestamped records of discrete events**. They give detailed context about what happened at a specific moment.

Examples:

- Application errors and stack traces
- Access logs from Nginx or a load balancer
- Audit logs (who did what)
- Kubernetes events and container stdout/stderr

Structured (JSON) logs are much easier to search and filter than plain text:

```json
{
  "timestamp": "2026-10-12T10:15:32Z",
  "level": "ERROR",
  "service": "payment",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "message": "card authorization failed",
  "order_id": "O-55821"
}
```

### 3. Traces

A trace follows **one request as it travels through multiple services**. Each step is a **span** (with a start time, duration and metadata), and spans are linked by a shared trace ID.

Example trace for a checkout request:

```
Trace 4bf92f35...  (total 820 ms)
|-- api-gateway        GET /checkout        820 ms
    |-- cart-service   getCart               45 ms
    |-- payment-service charge              690 ms
    |   |-- bank-api   POST /authorize      650 ms   <-- slow
    |-- order-service  createOrder           60 ms
```

Traces are very useful in microservices to find which service is slow or failing.

### Summary

| Pillar  | Answers                         | Data type          | Example tool        |
|---------|---------------------------------|--------------------|---------------------|
| Metrics | Is something wrong? How much?   | Numbers over time  | Prometheus          |
| Logs    | What exactly happened?          | Event records      | Loki, Elasticsearch |
| Traces  | Where in the request path?      | Linked spans       | Jaeger, Tempo       |

The real value comes from **correlating** them: an alert fires on a metric, I jump to the traces for slow requests, then to the logs for that trace ID.

## Why Observability is Required

Modern systems (microservices, containers, Kubernetes, cloud) are distributed and dynamic. Pods come and go, requests cross many services, and failures are often partial.

### Monitoring vs Observability

| Monitoring                                       | Observability                                         |
|--------------------------------------------------|-------------------------------------------------------|
| Watches **known-unknowns**: problems we expected and created checks for | Helps investigate **unknown-unknowns**: problems nobody predicted |
| "Is CPU above 80%?" "Is the site up?"            | "Why are only users in one region seeing slow checkout?" |
| Predefined dashboards and alerts                 | Explore high-cardinality data and ask new questions   |
| Tells you **that** something is wrong            | Helps you find **why** it is wrong                    |

Monitoring is part of observability, not a replacement for it.

Benefits:

- Faster detection and resolution of incidents (lower MTTD and MTTR).
- Understanding performance and user impact.
- Defining and tracking SLIs, SLOs and error budgets.
- Capacity planning and cost optimization.
- Safer deployments (comparing metrics before/after a release).

## Common Tools

| Tool                 | Category                | Notes                                                  |
|----------------------|-------------------------|--------------------------------------------------------|
| Prometheus           | Metrics                 | Pull-based scraping, time-series DB, PromQL, Alertmanager |
| Grafana              | Visualization           | Dashboards for Prometheus, Loki, Tempo, CloudWatch and more |
| Loki                 | Logs                    | Indexes only labels, not full text, so it is cheap to run |
| ELK / EFK            | Logs                    | Elasticsearch + Logstash (or Fluentd/Fluent Bit) + Kibana; full-text search |
| Jaeger               | Traces                  | Open-source distributed tracing (CNCF)                 |
| Grafana Tempo        | Traces                  | Trace storage on object storage, integrates with Grafana |
| OpenTelemetry (OTel) | Instrumentation standard| Vendor-neutral APIs/SDKs and Collector for metrics, logs and traces |
| Datadog              | SaaS (all-in-one)       | Commercial; metrics, logs, APM, traces in one platform |
| Amazon CloudWatch    | AWS native              | Metrics, logs, alarms, Container Insights, X-Ray/Application Signals for traces |

## Kubernetes Observability

Kubernetes needs observability at several levels: cluster, nodes, pods/containers and applications.

| Component            | What it does                                                                 |
|----------------------|------------------------------------------------------------------------------|
| metrics-server       | Collects basic CPU/memory from kubelets; powers `kubectl top` and HPA. Not for long-term storage |
| kube-state-metrics   | Exposes the state of Kubernetes objects (deployments, pod status, restarts, replicas) as metrics |
| node-exporter        | Runs as a DaemonSet and exposes node-level hardware/OS metrics (CPU, disk, network) |
| cAdvisor             | Built into the kubelet; provides per-container resource usage metrics       |
| kube-prometheus-stack| Helm chart that installs Prometheus Operator, Prometheus, Alertmanager, Grafana, node-exporter, kube-state-metrics and default dashboards/alerts |
| Fluent Bit           | Lightweight DaemonSet log collector that ships container logs to Loki, Elasticsearch, CloudWatch, etc. |
| Promtail             | Log agent for Loki (now deprecated in favour of Grafana Alloy)               |
| OpenTelemetry Collector | Receives, processes and exports metrics, logs and traces to any backend   |

Quick install of the monitoring stack:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

kubectl top nodes
kubectl top pods -A
```

A typical Kubernetes observability flow:

```
 Pods / Nodes
   |-- metrics --> Prometheus (scrapes) ----------+
   |-- logs -----> Fluent Bit / Alloy --> Loki ---+--> Grafana --> Dashboards
   |-- traces ---> OTel Collector --> Tempo ------+         |
                                                           +--> Alertmanager --> Slack / PagerDuty
```

## Golden Signals, RED and USE Methods

These are frameworks for deciding **what to measure**.

### Four Golden Signals (Google SRE book)

| Signal     | Meaning                                       |
|------------|-----------------------------------------------|
| Latency    | Time taken to serve a request (track errors separately) |
| Traffic    | Demand on the system, e.g. requests/sec       |
| Errors     | Rate of failed requests                       |
| Saturation | How "full" the service is (CPU, memory, queue depth) |

### RED Method (for request-driven services)

- **Rate** - requests per second
- **Errors** - failed requests per second
- **Duration** - distribution of request latency

Best for microservices and APIs.

### USE Method (for resources)

- **Utilization** - % of time the resource is busy
- **Saturation** - extra work queued that it cannot service yet
- **Errors** - count of error events

Best for infrastructure like CPU, memory, disks and network.

**In practice**: use RED for services, USE for infrastructure, and the golden signals as the overall checklist for alerts and dashboards.
