# Session 10 - Pods, ReplicaSets & Deployments

Cluster: local 3-node kind cluster ([kind-cluster.yaml](kind-cluster.yaml)) - 1 control plane + 2 workers.

![kind cluster](screenshots/00-kind-cluster.png)
![nodes ready](screenshots/00b-nodes-ready.png)

A `curl-client` pod is used to send requests to the services from inside the cluster.

---

# Task 1: Deployment strategies

| Strategy | How | Downtime | Extra resources | Rollback |
|---|---|---|---|---|
| Rolling update | Replace pods gradually (`maxSurge`, `maxUnavailable`) | No | Small (+maxSurge) | `kubectl rollout undo` |
| Blue-Green | Two full versions, Service selector switches | No | 2x | Switch selector back |
| Canary | Small number of new pods behind the same Service | No | Small | Scale canary to 0 |
| Recreate | Delete all old pods, then create new ones | **Yes** | None | Redeploy old version |

## 01. Rolling Update - [01-rolling-update/](01-rolling-update)

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1          # at most 1 extra pod above 4
    maxUnavailable: 1    # at most 1 pod down at a time
```

**Create the deployment** (4 replicas, nginx 1.26):

![rolling create](screenshots/01a-rolling-create.png)

**Update to nginx 1.27 and watch the pods.** New pods (hash `5c6bcdcb67`) are created while old pods (hash `bf44b9fd8`) terminate, a few at a time. The old ReplicaSet ends with 0 pods, the new one with 4, and the Service now returns `Server: nginx/1.27.5`.

![rolling update](screenshots/01b-rolling-update.png)

**Events + rollback** with `kubectl rollout undo --to-revision=1`:

![rolling describe undo](screenshots/01c-rolling-describe-undo.png)

## 02. Blue-Green - [02-blue-green/](02-blue-green)

Both versions run at the same time. The Service selector decides which one gets traffic (`version: blue` or `version: green`).

![blue green deploy](screenshots/02a-blue-green-deploy.png)

**Switch traffic** by patching the selector. The endpoints change to the green pod IPs and all responses come from GREEN. Rollback is just patching the selector back.

```bash
kubectl patch service myapp-service -p '{"spec":{"selector":{"app":"myapp","version":"green"}}}'
```

![blue green switch](screenshots/02b-blue-green-switch.png)

## 03. Canary - [03-canary/](03-canary)

The Service selects only `app: shop`, so it sends traffic to both `track: stable` (9 pods) and `track: canary` (1 pod).

![canary deploy](screenshots/03a-canary-deploy.png)

**Traffic split:** with 9 stable + 1 canary, 14 of 200 requests (7%, close to the expected 10%) went to the canary. After scaling to 5 + 5, about half the traffic goes to the canary. Once happy, stable is scaled to 0 (or updated to v2).

![canary traffic](screenshots/03b-canary-traffic.png)

> With replica-based canary the percentage depends on pod count. For exact weights an ingress controller (nginx `canary-weight` annotation) or a service mesh is used.

## 04. Recreate - [04-recreate/](04-recreate)

![recreate deploy](screenshots/04a-recreate-deploy.png)

**Update:** all 3 old pods go to `Terminating` at the same time, and the new pods are only `ADDED` after the old ones are `DELETED`. The events show "scaled down ... from 3 to 0" and then "scaled up ... from 0 to 3". There is a gap where no pod serves traffic, which is the downtime.

![recreate update](screenshots/04b-recreate-update.png)

---

# Task 2: Pod lifecycle

Phases: `Pending → Running → Succeeded / Failed` (and `Unknown` if the node is lost). `ContainerCreating`, `CrashLoopBackOff`, `ImagePullBackOff`, `Init:0/1`, `Completed`, `Terminating` are **statuses/reasons** shown by kubectl, not phases.

YAML files: [pod-lifecycle/](pod-lifecycle)

### 01-running-pod.yaml
Normal flow: `ContainerCreating → Running`. Events: Scheduled → Pulled → Created → Started.

![running](screenshots/05-lifecycle-01-running.png)

**Observed:** the scheduler assigned a node, kubelet pulled the image and started the container, pod got an IP and became Ready.

### 02-pending-pod.yaml
Requests 64 CPUs.

![pending](screenshots/06-lifecycle-02-pending.png)

**Observed:** stays `Pending` with `Node: <none>`. Event `FailedScheduling: 2 Insufficient cpu` (and the control-plane node is tainted). Fix = lower the request or add bigger nodes.

### 03-succeeded-pod.yaml
Runs a job that exits 0 with `restartPolicy: Never`.

![succeeded](screenshots/07-lifecycle-03-succeeded.png)

**Observed:** `Running → Completed`, phase `Succeeded`, exit code 0.

### 04-failed-pod.yaml
Exits 1 with `restartPolicy: Never`.

![failed](screenshots/08-lifecycle-04-failed.png)

**Observed:** status `Error`, phase `Failed`, exit code 1, restart count 0 (not restarted because of the restart policy).

### 05-crashloop-pod.yaml
Exits 1 with `restartPolicy: Always`.

![crashloop](screenshots/09-lifecycle-05-crashloop.png)

**Observed:** `Running → Error → CrashLoopBackOff → Running ...`. Restart count keeps increasing, and the wait between restarts grows (back-off: 10s, 20s, 40s, ... max 5 min). `kubectl logs --previous` shows the logs of the crashed container.

### 06-init-container-pod.yaml

![init container](screenshots/10-lifecycle-06-init-container.png)

**Observed:** `Init:0/1` for ~10 s while the init container runs, then `PodInitializing → Running`. The app container reads the file the init container wrote to the shared `emptyDir`.

### 07-image-pull-error-pod.yaml

![image pull](screenshots/11-lifecycle-07-image-pull-error.png)

**Observed:** `ErrImagePull → ImagePullBackOff`. The pod stays in phase `Pending` because the container never started. The event shows "not found" for the tag.

### 08-graceful-termination-pod.yaml

![graceful](screenshots/12-lifecycle-08-graceful-termination.png)

**Observed:** the `postStart` hook wrote `hook.txt`. On delete, the pod showed `Terminating` while the `preStop` hook (`sleep 8`) ran, and it was removed after ~8 s (well within `terminationGracePeriodSeconds: 20`). After the grace period kubelet would send SIGKILL.

### 09-readiness-probe-pod.yaml

![readiness](screenshots/13-lifecycle-09-readiness.png)

**Observed:** `Running` but `0/1` Ready for ~15 s until `/tmp/ready` existed, then `1/1`. A pod that is not Ready is removed from Service endpoints.

### Summary

![summary](screenshots/14-lifecycle-summary.png)
