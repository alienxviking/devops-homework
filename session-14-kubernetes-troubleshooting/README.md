# Session 14 - Kubernetes Troubleshooting

Cluster: kind (1 control plane + 2 workers). Broken manifests are from the course repo (`devops-heros/session-14-kubernetes-troubleshooting`). The `fixed*.yaml` files for the scenarios and the extra folders `10-containercreating` and `11-pod-networking` are mine.

My order for every problem: **get → describe (events) → logs → exec → root cause → fix → verify**.

---

## Task 1: Troubleshooting commands

| Command | Use it to |
|---|---|
| `kubectl get` | See status/phase/restarts quickly (`-o wide`, `-o yaml`, `-o jsonpath`, `--show-labels`, `-A`) |
| `kubectl describe` | Full object details + **Events** (scheduling, pulling, probes, mounts) |
| `kubectl logs` | App output (`--previous` for the crashed container, `-f`, `--tail`, `--since`, `-c` container) |
| `kubectl exec` | Run commands inside the container (curl localhost, env, files, DNS) |
| `kubectl events` / `get events` | Cluster events, filter with `--for` or `--types=Warning` |
| `kubectl explain` | Built-in docs for any field |
| `kubectl top` | CPU/memory usage (needs metrics-server) |
| `kubectl get -o wide` | Pod IP + node, useful for networking problems |

| | |
|---|---|
| ![](screenshots/01-kubectl-get.png) | ![](screenshots/02-kubectl-describe.png) |
| ![](screenshots/03-kubectl-logs.png) | ![](screenshots/04-kubectl-exec.png) |
| ![](screenshots/05-kubectl-events.png) | ![](screenshots/06-kubectl-explain-top.png) |

---

## Task 2: Troubleshoot common issues

Started with the course "triage gauntlet" (`scenarios/triage_all.sh`), which deploys 5 broken pods at once:

![gauntlet](screenshots/07-gauntlet-overview.png)

### 1. CrashLoopBackOff - [06-crashloopbackoff](06-crashloopbackoff)

| | |
|---|---|
| **Problem** | `crash-demo` keeps restarting, status `CrashLoopBackOff` |
| **Investigate** | `describe` → Last State Terminated, Exit Code 1, restart count growing. Events → `Back-off restarting failed container`. `logs --previous` → "Something went wrong!" |
| **Root cause** | The container's command exits with code 1. With `restartPolicy: Always` kubelet restarts it with an increasing back-off |
| **Fix** | Fixed the command (`fixed-pod.yaml`) so the process keeps running |
| **Verify** | `Running`, 0 restarts, healthy log |

![crashloop](screenshots/08-crashloop-investigate.png)
![crashloop fix](screenshots/09-crashloop-fix.png)

### 2 & 3. ErrImagePull / ImagePullBackOff - [07-imagepullbackoff](07-imagepullbackoff)

| | |
|---|---|
| **Problem** | Pod never starts |
| **Investigate** | `--watch` shows `ErrImagePull` → `ImagePullBackOff` → `ErrImagePull`... Events: `Failed to pull image "nginx:this-image-does-not-exist": ... not found` |
| **Root cause** | Tag does not exist. **ErrImagePull** = the pull just failed, **ImagePullBackOff** = kubelet is waiting before the next try |
| **Fix** | `image: nginx:1.27` |
| **Verify** | Running, `Image ID` shows the pulled digest |

![imagepull](screenshots/10-imagepull-investigate.png)
![imagepull fix](screenshots/11-imagepull-fix.png)

Other causes of the same error: typo in the repo name, private registry without `imagePullSecrets`, Docker Hub rate limit.

### 4. Pending - [08-pending-pods](08-pending-pods) + scenario 3

| | |
|---|---|
| **Problem** | Pod stays `Pending`, `Node: <none>` |
| **Investigate** | Events: `FailedScheduling: 0/3 nodes are available ... didn't match Pod's node affinity/selector` |
| **Root cause** | `nodeSelector: kubernetes.io/hostname=node-that-does-not-exist`. My nodes are `devops-control-plane`, `devops-worker`, `devops-worker2` |
| **Fix / Verify** | Removed the nodeSelector → scheduled and Running |

![pending](screenshots/12-pending-investigate.png)
![pending fix](screenshots/13-pending-fix.png)

Second Pending case (gauntlet scenario 3): requests `cpu: 500`, `memory: 1000Gi` → `Insufficient cpu, Insufficient memory` (nodes have 32 CPUs). Fixed with realistic requests.

![pending resources](screenshots/13b-pending-resources.png)

### 5. ContainerCreating - [10-containercreating](10-containercreating)

| | |
|---|---|
| **Problem** | Pod stuck in `ContainerCreating` |
| **Investigate** | Events: `FailedMount: MountVolume.SetUp failed for volume "app-config": configmap "app-settings" not found` |
| **Root cause** | The pod mounts a ConfigMap that was never created, so kubelet can't prepare the volume and won't start the container |
| **Fix / Verify** | Created the ConfigMap → pod starts by itself, file is mounted |

![containercreating](screenshots/14-containercreating-investigate.png)
![containercreating fix](screenshots/15-containercreating-fix.png)

Other ContainerCreating causes: missing Secret, PVC not bound, CNI problems, slow image pull.

### 6. Service connectivity - [09-service-dns-troubleshooting](09-service-dns-troubleshooting)

Extra problem I found first: the course `dns-test-pod.yaml` used `registry.k8s.io/e2e-test-images/dnsutils:1.3`, which doesn't exist (ImagePullBackOff). The Kubernetes DNS debugging docs use `jessie-dnsutils:1.3`, so I changed the image.

![dns-test pod broken](screenshots/16-service-investigate.png)
![dns-test pod fix](screenshots/16b-dns-test-image-fix.png)

| | |
|---|---|
| **Problem** | `curl http://web-service` fails (connection refused) |
| **Investigate** | DNS works (resolves to the ClusterIP), but the EndpointSlice has **no endpoints**. `describe svc` → `Selector: app=web-ahsgdf`, pods have `app=web` |
| **Root cause** | Service selector doesn't match the pod labels |
| **Fix / Verify** | `selector: app: web` → endpoints filled with the 2 pod IPs, nginx page returned |

![service](screenshots/16c-service-investigate.png)
![service fix](screenshots/17-service-fix.png)

### 7. DNS issue - scenario 4

| | |
|---|---|
| **Problem** | Pod is Running but the app can't reach its backend |
| **Investigate** | The app calls `postgres-db-wrong-name.production.svc.cluster.local`. `nslookup` → NXDOMAIN, namespace `production` doesn't exist, the real service is `web-service` in `default` |
| **Root cause** | Wrong service name + namespace in the app config |
| **Fix / Verify** | Correct FQDN `web-service.default.svc.cluster.local` → HTTP 200 |

![dns](screenshots/18-dns-investigate.png)
![dns fix](screenshots/19-dns-fix.png)

### 8. Pod networking issue - [11-pod-networking](11-pod-networking)

| | |
|---|---|
| **Problem** | `frontend-client` → `payments` worked (200), then started timing out |
| **Investigate** | DNS ok, endpoints ok, but even the **pod IP directly** times out (not refused), which points to something dropping packets. `kubectl get networkpolicy` → `default-deny-ingress` with an empty podSelector |
| **Root cause** | A default-deny NetworkPolicy isolates every pod in the namespace for ingress |
| **Fix / Verify** | Added `allow-frontend-to-payments` (only `role=frontend` → `app=payments:80`). Frontend gets 200, a pod without the label is still blocked |

![network](screenshots/20-network-investigate.png)
![network fix](screenshots/21-network-fix.png)

### 9. Configuration issue - scenario 1

| | |
|---|---|
| **Problem** | `CrashLoopBackOff` |
| **Investigate** | `logs --previous` → `[FATAL ERROR]: DATABASE_URL environment variable is MISSING!`. The pod spec has no `env` (exec doesn't work because the container keeps dying) |
| **Root cause** | Missing required configuration |
| **Fix / Verify** | Added `DATABASE_URL` env (in a real app from a ConfigMap/Secret) → "Application started successfully!" |

![config](screenshots/22-config-investigate.png)
![config fix](screenshots/23-config-fix.png)

### Extra: OOMKilled - scenario 5

`Last State: Terminated, Reason: OOMKilled, Exit Code: 137` → the app allocates far more than the `20Mi` limit. Fixed the memory request/limit to match real usage (256Mi) → `Completed`.

![oom](screenshots/24-oomkilled.png)

### All gauntlet pods fixed

![summary](screenshots/25-gauntlet-imagepull-and-summary.png)

---

## Task 3: Mini project - [mini-project](mini-project)

### Deploy and check the application

![mini deploy](screenshots/26-mini-deploy-and-check.png)
![mini service](screenshots/27-mini-service-endpoints.png)

### Broken pod

![mini broken](screenshots/28-mini-broken-pod.png)

**Q1. What is the Pod status?** `ImagePullBackOff` (alternating with `ErrImagePull`), READY 0/1.

**Q2. What is the actual error?** `Failed to pull image "nginx:this-tag-does-not-exist": ... not found`.

**Q3. Which command helped find the reason?** `kubectl describe pod project-broken-pod` (the Events section).

**Q4. What is wrong with the image?** The image `nginx` exists but the tag `this-tag-does-not-exist` doesn't exist on Docker Hub.

**Q5. How to fix it?** Use a valid tag (`nginx:1.27`), delete and re-create the pod (the image of a running pod can't be changed). In a Deployment, `kubectl set image` would do a rolling update.

![mini broken fix](screenshots/29-mini-broken-pod-fix.png)

### Service selector challenge

Changed the selector to `app: wrong-app` → `ENDPOINTS <none>`, service not reachable. `kubectl get pods --show-labels` (`app=troubleshooting-app`) vs `describe service` (`Selector: app=wrong-app`) shows the mismatch. Re-applied the correct selector → endpoints back, nginx page returned.

![selector challenge](screenshots/30-mini-selector-challenge.png)

### Final checklist

```bash
kubectl get pods                     # status / restarts
kubectl describe pod <pod>           # events!
kubectl logs <pod> [--previous]      # app errors
kubectl exec -it <pod> -- sh         # check from inside
kubectl get events --sort-by=.lastTimestamp
kubectl get endpoints <svc>          # empty = selector/readiness problem
kubectl get networkpolicy            # timeouts between pods
```
