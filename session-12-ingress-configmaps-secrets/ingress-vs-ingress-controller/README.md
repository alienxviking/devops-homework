# Task 4: Ingress vs Ingress Controller

## What is Ingress?

An **Ingress** is a Kubernetes API object (`networking.k8s.io/v1`) that defines **rules for routing external HTTP/HTTPS traffic** to Services inside the cluster.

With an Ingress you can:

- Route by **host** (`api.example.com` -> api Service, `shop.example.com` -> shop Service).
- Route by **path** (`/api` -> backend, `/` -> frontend).
- Terminate **TLS** using a certificate stored in a Secret.
- Expose many Services through **one** external IP / load balancer instead of one LoadBalancer Service each.

An Ingress by itself is just configuration stored in etcd. It does not open any port or proxy any traffic.

## What is an Ingress Controller?

An **Ingress Controller** is the actual software that makes Ingress rules work. It:

1. Runs in the cluster (usually as a Deployment or DaemonSet), or as a cloud integration.
2. **Watches** Ingress objects (plus Services, EndpointSlices, Secrets) through the API server.
3. Turns the rules into real config for a proxy or load balancer (nginx config, Envoy config, an AWS ALB, a Google Cloud load balancer, etc.).
4. Receives the external traffic and forwards it to the right Pods.

The controller itself is usually exposed with a `LoadBalancer` or `NodePort` Service, which is the single entry point into the cluster.

Unlike Deployment or ReplicaSet controllers, an Ingress controller is **not** part of kube-controller-manager. You have to install one.

## Difference

| Point | Ingress | Ingress Controller |
|-------|---------|-------------------|
| What it is | API object / resource (YAML) | Running application (Pods) or cloud integration |
| Role | Declares routing rules ("what should happen") | Implements the rules ("makes it happen") |
| Created by | You, with `kubectl apply` | Installed separately (Helm, manifests, cloud add-on) |
| Comes with Kubernetes? | Yes, the API type is built in | No, must be installed |
| Handles traffic? | No | Yes |
| Example | `kind: Ingress` with host `shop.example.com` | ingress-nginx, Traefik, AWS Load Balancer Controller |
| Analogy | Routing table written on paper | The router that reads and applies it |

## Why both are required

- If you create an Ingress **without a controller**, it is accepted and stored, but nothing happens. `kubectl get ingress` will show no `ADDRESS` and requests never reach the app.
- If you install a controller **without any Ingress**, it runs but has no rules, so it usually returns 404 for everything (default backend).
- The split lets Kubernetes keep one standard API while different vendors implement it in different ways. You can switch controllers without rewriting your Ingress objects (except controller-specific annotations).

## Common Ingress Controllers

| Controller | Notes |
|------------|-------|
| **ingress-nginx** | Community controller based on NGINX. Was the most widely used. The Kubernetes project announced its retirement in 2025 and stopped maintaining it in March 2026, so new setups should pick something else or move to Gateway API. |
| **NGINX Ingress Controller (F5/NGINX)** | Separate controller maintained by NGINX/F5. Different annotations from ingress-nginx. |
| **Traefik** | Automatic config discovery, built-in Let's Encrypt support, default in k3s. |
| **HAProxy Ingress** | Based on HAProxy, good performance and fine-grained load balancing options. |
| **AWS Load Balancer Controller** | Creates an AWS **Application Load Balancer** for each Ingress (or a shared one using groups). Traffic can go directly to Pod IPs. |
| **GKE Ingress** | Built into Google Kubernetes Engine. Creates a Google Cloud HTTP(S) Load Balancer. |
| Others | Contour (Envoy), Istio ingress gateway, Kong, Azure Application Gateway for Containers. |

## IngressClass

A cluster can have more than one controller. **IngressClass** tells Kubernetes which controller should handle which Ingress.

```yaml
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: nginx
  annotations:
    ingressclass.kubernetes.io/is-default-class: "true"
spec:
  controller: k8s.io/ingress-nginx
```

- The Ingress picks a class with `spec.ingressClassName: nginx`.
- If an Ingress has no class and one IngressClass is marked default, the default is used.
- The old annotation `kubernetes.io/ingress.class` is deprecated; use `ingressClassName`.

```bash
kubectl get ingressclass
```

## Example Ingress: host + path routing

Two hosts. `shop.example.com` sends `/api` to the backend and everything else to the frontend. `admin.example.com` goes to the admin Service. TLS is enabled for the shop host.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: shop-ingress
  namespace: shop
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - shop.example.com
      secretName: shop-tls        # kubernetes.io/tls Secret
  rules:
    - host: shop.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: backend
                port:
                  number: 8080
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 80
    - host: admin.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: admin
                port:
                  number: 80
```

Notes:

- `pathType` is required: `Prefix`, `Exact`, or `ImplementationSpecific`.
- The longest matching path wins, so `/api` is matched before `/`.
- The backend Services must be in the **same namespace** as the Ingress.

Useful commands:

```bash
kubectl apply -f shop-ingress.yaml
kubectl get ingress -n shop
kubectl describe ingress shop-ingress -n shop

# test without real DNS, using the controller's external IP
curl -H "Host: shop.example.com" http://<INGRESS-IP>/api
```

## Gateway API: the successor

The Ingress API is stable but **frozen**; no new features are being added. Its limits (HTTP only, lots of controller-specific annotations, one object mixing infrastructure and app config) led to the **Gateway API**, which reached GA (v1.0) in 2023.

| Gateway API resource | Role |
|----------------------|------|
| `GatewayClass` | Type of gateway / which controller (like IngressClass). Set up by the infra provider. |
| `Gateway` | The actual entry point: listeners, ports, TLS. Managed by cluster operators. |
| `HTTPRoute` (also `GRPCRoute`, `TLSRoute`, `TCPRoute`) | Routing rules to Services. Managed by app teams. |

Main advantages: role separation, header/method matching, traffic splitting (canary) and more protocols, all in the spec instead of annotations. Gateway API is installed as CRDs and still needs a controller implementation (Envoy Gateway, Istio, Cilium, NGINX Gateway Fabric, Traefik, cloud providers, etc.).

Ingress isn't removed and still works, but Gateway API is the recommended direction for new clusters.

## Summary

- **Ingress** = rules (a YAML object). **Ingress Controller** = the thing that applies them and moves the traffic.
- You need both; an Ingress alone does nothing.
- `ingressClassName` / IngressClass decides which controller handles an Ingress.
- Gateway API is the newer, more flexible replacement for Ingress.
