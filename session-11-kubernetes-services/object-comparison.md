# Task 2: Comparing Kubernetes Objects

## (a) Deployment vs ReplicaSet

### Purpose

- **ReplicaSet (RS)**: keeps a fixed number of identical Pods running. If a Pod dies or is deleted, the RS creates a new one. That is all it does.
- **Deployment**: a higher-level object that manages ReplicaSets. It adds rolling updates, rollbacks, pause/resume and revision history on top of what an RS does.

In practice, you almost never create a ReplicaSet yourself. You create a Deployment and it creates the ReplicaSet for you.

### Comparison

| Point | ReplicaSet | Deployment |
|-------|-----------|------------|
| Main job | Keep N Pods running | Manage app versions through ReplicaSets |
| Manages | Pods directly | ReplicaSets (which manage Pods) |
| Scaling | `kubectl scale rs <name> --replicas=5` | `kubectl scale deploy <name> --replicas=5` (passed down to the current RS) |
| Updating the image | Changing the template does **not** touch existing Pods. Only new Pods get the new template. You'd have to delete old Pods manually. | Changing the template triggers a **rolling update** automatically |
| Rollback | Not supported | `kubectl rollout undo` |
| Revision history | No | Yes (old ReplicaSets kept, `revisionHistoryLimit` default 10) |
| Update strategies | None | `RollingUpdate` (default) or `Recreate` |
| Typical use | Used internally by Deployments | Stateless apps (web servers, APIs) |

### How they relate

- A Deployment **owns** one or more ReplicaSets (you can see this in the RS's `metadata.ownerReferences`).
- Each ReplicaSet created by a Deployment gets a **`pod-template-hash`** label. It is a hash of the Pod template, and it is added to the RS's selector and to every Pod it creates. This stops ReplicaSets of different versions from fighting over each other's Pods.
- Names follow the pattern: Deployment `web` -> ReplicaSet `web-<hash>` -> Pod `web-<hash>-<random>`.

### Rolling update flow

When the image changes (`kubectl set image deploy/web nginx=nginx:1.27`):

1. Deployment creates a **new ReplicaSet** with the new template (new hash).
2. It scales the new RS up and the old RS down step by step.
3. `maxSurge` (default 25%) = how many extra Pods can exist above desired count during the update.
4. `maxUnavailable` (default 25%) = how many Pods can be unavailable during the update.
5. The old RS is kept with `replicas: 0` so it can be used for rollback.

```yaml
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

```bash
kubectl rollout status deploy/web
kubectl rollout history deploy/web
kubectl rollout undo deploy/web
kubectl get rs -l app=web      # shows old and new ReplicaSets
kubectl get pods --show-labels # shows pod-template-hash
```

## (b) Deployment vs DaemonSet vs StatefulSet

### Short description

- **Deployment**: runs N interchangeable Pods anywhere in the cluster. Pods have random names and no identity. Good for stateless apps.
- **DaemonSet**: runs **one Pod on every node** (or every node matching a selector). When a node joins, a Pod is added; when a node leaves, the Pod is removed.
- **StatefulSet**: runs Pods that each have a **stable identity**: fixed names (`db-0`, `db-1`), stable DNS names, and their own persistent volume that sticks to them across restarts and rescheduling.

### Comparison table

| Point | Deployment | DaemonSet | StatefulSet |
|-------|-----------|-----------|-------------|
| Use case | Stateless apps | Node-level agents | Stateful / clustered apps |
| Number of Pods | `replicas: N` | One per (matching) node | `replicas: N` |
| Pod names | Random (`web-7d9f8-abcde`) | Random per node (`fluentd-x2k9p`) | Ordered and stable (`db-0`, `db-1`, `db-2`) |
| Pod creation order | All in parallel | One per node as nodes become eligible | In order 0, 1, 2... each waits for the previous to be Ready (`OrderedReady` default; `Parallel` optional) |
| Scaling | Change replicas, Pods added/removed in any order | Add/remove nodes (or change node selector) | Change replicas; scale down removes highest ordinal first |
| Updates | RollingUpdate / Recreate | RollingUpdate / OnDelete | RollingUpdate (highest ordinal to lowest) / OnDelete; `partition` for canary |
| Networking | Accessed through a normal Service; Pods are interchangeable | Often uses `hostNetwork` or hostPort; can be reached per node | Needs a **headless Service** (`serviceName`); each Pod gets its own DNS: `db-0.db-svc.ns.svc.cluster.local` |
| Storage | Usually none, or one shared PVC | Often `hostPath` to read node files (logs, metrics) | `volumeClaimTemplates`: a separate PVC per Pod (`data-db-0`, `data-db-1`), kept when the Pod is rescheduled |
| On Pod deletion | New Pod with new name and IP | New Pod on the same node | New Pod with **same name** and same PVC |
| Examples | nginx, REST APIs, frontends | Fluent Bit, Prometheus node-exporter, kube-proxy, CNI agents (Calico, Cilium) | MySQL, PostgreSQL, MongoDB, Kafka, ZooKeeper, Elasticsearch, Redis cluster |

### Notes

- DaemonSet Pods are scheduled by the default scheduler (using node affinity), and they respect taints. To run on control plane nodes you add a toleration for `node-role.kubernetes.io/control-plane`.
- StatefulSet PVCs are **not deleted** when you scale down or delete the StatefulSet (by default). This protects data but means you clean them up manually. This can be changed with `persistentVolumeClaimRetentionPolicy`.
- A StatefulSet does not make an app "clustered" by itself. The app (e.g. MySQL replication) still has to handle that. StatefulSet just gives it stable names and storage.

### Minimal StatefulSet example

```yaml
apiVersion: v1
kind: Service
metadata:
  name: db
spec:
  clusterIP: None        # headless
  selector:
    app: db
  ports:
    - port: 5432
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: db
spec:
  serviceName: db
  replicas: 3
  selector:
    matchLabels:
      app: db
  template:
    metadata:
      labels:
        app: db
    spec:
      containers:
        - name: postgres
          image: postgres:16
          env:
            - name: POSTGRES_PASSWORD
              value: example
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 1Gi
```

## (c) ReplicaSet vs Service

These two are not alternatives. They solve different problems and are used together (usually Deployment + Service).

### ReplicaSet responsibility

- Keep the desired number of Pods **running**.
- Replace Pods that crash, get deleted, or are lost with a node.
- It does **not** handle networking at all. It has no IP and doesn't route traffic.

### Service responsibility

- Give a **stable virtual IP (ClusterIP)** and **DNS name** to a group of Pods.
- Find the Pods using a **label selector**.
- **Load balance** traffic across the healthy (Ready) Pods.
- Optionally expose Pods outside the cluster (NodePort, LoadBalancer).

| Point | ReplicaSet | Service |
|-------|-----------|---------|
| Layer | Workload / compute | Networking |
| Answers | "Are enough Pods running?" | "How do I reach those Pods?" |
| Uses labels for | Counting/owning its Pods | Choosing which Pods receive traffic |
| Has an IP / DNS | No | Yes (ClusterIP + `svc.ns.svc.cluster.local`) |
| Reacts to Pod failure | Creates a replacement Pod | Removes the failed Pod from endpoints, adds the new one |

### Why a Service is required

Pod IPs are **ephemeral**:

- Every new Pod gets a new IP. When a RS replaces a crashed Pod, or a Deployment rolls out a new version, all the IPs change.
- Scaling up/down changes the set of IPs.
- Clients can't keep track of this list themselves.

The Service gives one address that never changes for the life of the Service, while the Pods behind it come and go.

### How traffic reaches the Pods

```
client Pod
   |  1. resolve "web" -> CoreDNS returns ClusterIP (e.g. 10.96.12.34)
   v
ClusterIP:80 (virtual, no real interface)
   |  2. kube-proxy rules on the client's node (iptables / IPVS / nftables)
   |     pick one backend and DNAT to it
   v
Pod IP:targetPort (e.g. 10.244.2.7:8080)
```

In more detail:

1. The **Service** has a `selector` (e.g. `app: web`).
2. The **EndpointSlice controller** watches Pods matching that selector and writes their IPs and ports into **EndpointSlice** objects. Only Pods that are Ready are marked as ready endpoints.
3. **kube-proxy** on every node watches Services and EndpointSlices and programs rules (iptables by default on Linux; IPVS or nftables are other modes).
4. When a Pod sends traffic to the ClusterIP, the kernel rules on that node DNAT it to one of the Pod IPs.
5. The **CNI** network delivers the packet to the Pod, even if it is on another node.

```bash
kubectl get svc web
kubectl get endpointslices -l kubernetes.io/service-name=web
kubectl describe svc web
```

If `kubectl get endpointslices` shows no endpoints, the selector usually doesn't match the Pod labels, or the Pods are not Ready.

## Summary

- Deployment manages ReplicaSets; ReplicaSet manages Pods. Use Deployments, not bare ReplicaSets.
- Deployment = stateless, DaemonSet = one per node, StatefulSet = stable identity and storage.
- ReplicaSet keeps Pods alive; Service makes them reachable at a stable address.
