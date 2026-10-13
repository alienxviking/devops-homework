# Kubernetes Architecture - Notes

A Kubernetes cluster has two parts:

- **Control plane**: the "brain". Stores cluster state, makes decisions (scheduling, scaling), and exposes the API.
- **Worker nodes**: machines that actually run the application containers.

Everything talks through the **kube-apiserver**. Components don't talk to etcd or to each other directly; they watch the API server and react to changes. This is the "desired state vs current state" model: you declare what you want, and controllers keep working to make reality match it.

## Diagram

```
                          +---------------------------------------------+
   kubectl / CI / UI ---> |               CONTROL PLANE                 |
        (HTTPS)           |                                             |
                          |   +-----------------+        +---------+    |
                          |   | kube-apiserver  |<------>|  etcd   |    |
                          |   +-----------------+        +---------+    |
                          |     ^     ^      ^                          |
                          |     |     |      |                          |
                          | +---------+  +--------------------------+   |
                          | |scheduler|  | kube-controller-manager  |   |
                          | +---------+  +--------------------------+   |
                          |              | cloud-controller-manager |   |
                          |              +--------------------------+   |
                          +-----|---------------------|-----------------+
                                |  watch / update     |
              +-----------------+                     +-----------------+
              v                                                         v
   +----------------------------+                      +----------------------------+
   |         WORKER NODE 1      |                      |         WORKER NODE 2      |
   |  +---------+ +----------+  |                      |  +---------+ +----------+  |
   |  | kubelet | |kube-proxy|  |                      |  | kubelet | |kube-proxy|  |
   |  +---------+ +----------+  |                      |  +---------+ +----------+  |
   |       | CRI                |                      |       | CRI                |
   |  +-----------------------+ |                      |  +-----------------------+ |
   |  | containerd (runtime)  | |                      |  | containerd (runtime)  | |
   |  +-----------------------+ |                      |  +-----------------------+ |
   |  [Pod] [Pod]  CNI network  |                      |  [Pod] [Pod]  CNI network  |
   +----------------------------+                      +----------------------------+
```

## Control plane components

| Component | Role |
|-----------|------|
| **kube-apiserver** | Front door of the cluster. Every request (kubectl, other components) goes through it. Handles authentication, authorization (RBAC), admission control and validation, then reads/writes etcd. Scales horizontally. |
| **etcd** | Consistent, distributed key-value store. Holds all cluster data (objects, state). Only the API server talks to it. Must be backed up. |
| **kube-scheduler** | Watches for Pods with no node assigned and picks a node. Filters out nodes that don't fit (resources, taints, affinity, node selectors), scores the rest, then binds the Pod to the best one. |
| **kube-controller-manager** | Runs the built-in controllers in one process: Deployment, ReplicaSet, Node, Job, EndpointSlice, ServiceAccount, Namespace, etc. Each is a control loop that compares desired vs actual state and fixes the difference. |
| **cloud-controller-manager** | Cloud-specific controllers (only on cloud clusters). Creates cloud load balancers for `type: LoadBalancer` Services, sets up routes, and checks if a deleted VM means a node should be removed. |

## Node components

| Component | Role |
|-----------|------|
| **kubelet** | Agent on every node. Watches the API server for Pods assigned to its node, tells the container runtime to start them, runs probes, and reports Pod and node status back. |
| **kube-proxy** | Implements Services on each node. Watches Services and EndpointSlices and programs iptables / IPVS / nftables rules so traffic to a Service IP is sent to a backend Pod. (Some CNIs like Cilium can replace it.) |
| **Container runtime** | Actually pulls images and runs containers. Kubernetes talks to it through the **CRI** (Container Runtime Interface). Common ones: **containerd**, CRI-O. Docker Engine as a runtime (dockershim) was removed in v1.24, but images built with Docker still work. |

## Add-ons

- **CoreDNS**: cluster DNS. Gives Services names like `my-svc.my-ns.svc.cluster.local`. Runs as a Deployment in `kube-system`, behind a Service named `kube-dns`.
- **CNI plugin** (Calico, Flannel, Cilium, Weave, etc.): gives each Pod its own IP and makes Pod-to-Pod traffic work across nodes. Nodes stay `NotReady` until a CNI is installed.
- Others: metrics-server (for `kubectl top` and HPA), Ingress controller, dashboard, logging/monitoring stacks.

## What happens when you run `kubectl create deployment`

Example:

```bash
kubectl create deployment web --image=nginx --replicas=3
```

Step by step:

1. **kubectl** reads `~/.kube/config` for the cluster address and credentials, builds a Deployment object, and sends an HTTPS `POST` to the API server (`/apis/apps/v1/namespaces/default/deployments`).
2. **kube-apiserver** authenticates the user, checks RBAC (is this user allowed to create deployments in `default`?), runs mutating and validating admission controllers, validates the object, and then **writes it to etcd**. It returns success to kubectl at this point. Nothing is running yet.
3. **Deployment controller** (in kube-controller-manager) is watching Deployments. It sees the new one and creates a **ReplicaSet** with the same pod template and `replicas: 3`.
4. **ReplicaSet controller** sees the ReplicaSet has 0 of 3 Pods and creates **3 Pod objects**. These Pods have no `nodeName` yet (status `Pending`).
5. **kube-scheduler** sees the unscheduled Pods, filters and scores nodes, and **binds** each Pod to a node (sets `spec.nodeName`).
6. **kubelet** on each chosen node sees a Pod assigned to it. It calls the **container runtime** (containerd) via CRI to create the Pod sandbox; the **CNI plugin** sets up the network and assigns the Pod IP; then the runtime pulls `nginx` and starts the container.
7. **kubelet** reports status back to the API server (Pod becomes `Running`, then `Ready` once probes pass). The status is saved in etcd.
8. If a Service selects these Pods, the **EndpointSlice controller** adds the Pod IPs, and **kube-proxy** on every node updates its rules so traffic can reach them.

Check it with:

```bash
kubectl get deployment web
kubectl get rs
kubectl get pods -o wide
kubectl describe deployment web
kubectl get events --sort-by=.metadata.creationTimestamp
```

## Basic objects

| Object | What it is |
|--------|-----------|
| **Pod** | Smallest deployable unit. One or more containers sharing network (same IP) and volumes. Pods are disposable; if one dies, it is replaced by a new Pod with a new IP. |
| **ReplicaSet** | Makes sure N copies of a Pod are always running. Usually not created directly. |
| **Deployment** | Manages ReplicaSets. Adds rolling updates, rollback and revision history. The normal way to run stateless apps. |
| **Service** | Stable virtual IP and DNS name in front of a set of Pods (chosen by label selector). Types: ClusterIP, NodePort, LoadBalancer, ExternalName. |
| **Namespace** | Logical partition of the cluster. Used to separate teams/environments and to scope names, RBAC and resource quotas. Defaults: `default`, `kube-system`, `kube-public`, `kube-node-lease`. |
| **ConfigMap** | Non-sensitive config as key-value pairs or files. Injected as env vars or mounted as a volume. |
| **Secret** | Same idea as ConfigMap but for sensitive data (passwords, tokens, TLS certs). Stored base64-encoded; only encrypted at rest if encryption is configured for etcd. |

Small example tying a few together:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          ports:
            - containerPort: 80
          envFrom:
            - configMapRef:
                name: web-config
---
apiVersion: v1
kind: Service
metadata:
  name: web
  namespace: demo
spec:
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 80
```

## Key points to remember

- The API server is the only component that talks to etcd.
- Components work by **watching** the API server, not by calling each other.
- `kubectl create` only stores desired state; controllers, scheduler and kubelet do the actual work afterwards.
- Pods are temporary; Deployments keep them running and Services give them a stable address.
