# Session 15 - Helm

Helm v3.18 on the kind cluster (ingress-nginx installed).

```
session-15-helm/
├── webapp/                 # chart made with `helm create` (Task 1 + Task 2)
└── mini-project/
    └── yatri-webapp/       # my own chart (Task 3)
        ├── Chart.yaml
        ├── values.yaml         # defaults
        ├── values-dev.yaml     # dev overrides
        ├── values-prod.yaml    # prod overrides (3 replicas, HPA, WARN logs)
        └── templates/
            ├── _helpers.tpl        # name + labels helpers
            ├── configmap.yaml      # app config + index.html generated from values
            ├── secret.yaml         # DB password (b64enc)
            ├── frontend.yaml       # nginx Deployment + Service (config checksum annotation)
            ├── backend.yaml        # API Deployment + Service
            ├── ingress.yaml        # /  -> frontend, /api -> backend   (if ingress.enabled)
            ├── hpa.yaml            # only if autoscaling.enabled
            ├── NOTES.txt
            └── tests/test-connection.yaml   # `helm test`
```

**Helm in one line:** a package manager for Kubernetes. A *chart* is a folder of templated YAML + default `values.yaml`, and installing a chart creates a *release* that Helm tracks with revisions (stored as Secrets in the namespace).

---

## Task 1: Helm commands

### `helm create`

![create](screenshots/01-helm-create.png)

`helm lint` checks the chart, `helm template` renders the YAML locally without installing (good for reviewing what will be applied):

![lint template](screenshots/02-helm-lint-template.png)

### `helm install`

![install](screenshots/03-helm-install.png)

### `helm list` / `helm status`

![list status](screenshots/04-helm-list-status.png)

### `helm get`

`get values` (what I overrode), `get values --all` (merged), `get manifest` (rendered YAML Helm applied), `get notes`. The release history itself is stored in `sh.helm.release.v1.<name>.v<revision>` Secrets.

![get](screenshots/05-helm-get.png)

### `helm repo` / `helm search`

![repo search](screenshots/06-helm-repo-search.png)

| Command | What it does |
|---|---|
| `helm create <name>` | Scaffold a new chart |
| `helm install <release> <chart> -n ns --create-namespace -f/--set` | Install a chart as a release |
| `helm list [-A]` | List releases |
| `helm status <release>` | Release state + notes |
| `helm get values/manifest/notes/all <release>` | Inspect what was deployed |
| `helm upgrade <release> <chart> [--reuse-values] [--install]` | New revision with new chart/values |
| `helm history <release>` | All revisions |
| `helm rollback <release> <revision>` | Go back to a revision (creates a new one) |
| `helm uninstall <release>` | Delete all resources of the release |
| `helm repo add/update/list` | Manage chart repositories |
| `helm search repo/hub <keyword>` | Find charts in added repos / Artifact Hub |
| `helm lint`, `helm template`, `helm package`, `helm test` | Check, render, package (.tgz), run test hooks |

---

## Task 2: Helm rollback workflow

```
Install (rev 1) → Upgrade (rev 2) → Verify → Upgrade again (rev 3, broken) → Verify → Rollback to 2 (rev 4) → Verify
```

**1. Install - revision 1:** nginx `1.26-alpine`, 1 replica, `Server: nginx/1.26.x`

![rev1](screenshots/07-rollback-1-install-verify.png)

**2. Upgrade - revision 2 + verify:** nginx `1.27-alpine`, 3 replicas, `Server: nginx/1.27.x`

![rev2](screenshots/08-rollback-2-upgrade-verify.png)

**3. Upgrade again - revision 3 + verify:** tag `1.99-broken` does not exist. The new pod is in `ImagePullBackOff`, but the 3 old pods keep serving (rolling update). Note that Helm still says `STATUS: deployed`, because without `--wait` Helm only checks that the objects were accepted by the API, not that the pods work.

![rev3](screenshots/09-rollback-3-bad-upgrade-verify.png)

**4. Rollback + verify:** `helm rollback webapp-release 2` creates **revision 4** ("Rollback to 2") with the values of revision 2 → `nginx:1.27-alpine`, 3 replicas, broken pod terminated.

![rollback](screenshots/10-rollback-4-rollback-verify.png)

**Cleanup:** `helm uninstall` removes every resource of the release.

![uninstall](screenshots/11-helm-uninstall.png)

> Lesson: use `helm upgrade --wait --timeout 2m` (or `--atomic`, which rolls back automatically if the upgrade fails) in CI/CD.

---

## Task 3: Mini project - one chart, two environments

Chart [`yatri-webapp`](mini-project/yatri-webapp): frontend (nginx serving a page generated from values) + backend API + ConfigMap + Secret + Ingress + optional HPA + `helm test`.

| | dev ([values-dev.yaml](mini-project/yatri-webapp/values-dev.yaml)) | prod ([values-prod.yaml](mini-project/yatri-webapp/values-prod.yaml)) |
|---|---|---|
| Namespace / release | `dev` / `yatri-dev` | `prod` / `yatri-prod` |
| Frontend replicas | 1 | 3 (HPA 3-6) |
| Backend replicas | 1 | 2 |
| LOG_LEVEL | DEBUG | WARN |
| Host | yatri-dev.local | yatri-prod.local |

### Chart, lint, package

![structure](screenshots/12-mini-chart-structure.png)

### Install the same chart twice with different values

(dev from the folder, prod from the packaged `yatri-webapp-0.1.0.tgz`)

![install](screenshots/13-mini-install-dev-prod.png)

### helm test + upgrade prod

`helm test` runs the test pod from `templates/tests/` (it checks that the frontend shows the right environment and that the backend answers). Then prod was upgraded with a new backend message → revision 2.

![test upgrade](screenshots/15-mini-helm-test-upgrade.png)

### Result - both environments side by side

![compare](screenshots/14-mini-compare-envs.png)

| dev | prod |
|---|---|
| ![](screenshots/16-browser-dev.png) | ![](screenshots/17-browser-prod.png) |

Template features used: `include` helpers, `range` over a map, `if` blocks, `toYaml | nindent`, `b64enc`, `quote`, `.Release.*` / `.Chart.*` built-ins, a `checksum/config` annotation (pods restart automatically when the ConfigMap changes), test hook.
