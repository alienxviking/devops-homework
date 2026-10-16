# DevOps Homework

DevOps course homework - Snehangshu Roy

Every session folder has a `README.md` with the commands, the real output (screenshots) and notes.

| Session | Topic | README |
|---|---|---|
| 01 & 02 | Linux Fundamentals | [session-01-02-linux-fundamentals](session-01-02-linux-fundamentals/README.md) |
| 03 | Shell Scripting | [session-03-shell-scripting](session-03-shell-scripting/README.md) |
| 04 | Networking | [session-04-networking](session-04-networking/README.md) |
| 05 | Git and GitHub | [session-05-git](session-05-git/README.md) |
| 06 | Docker Fundamentals | [session-06-docker-fundamentals](session-06-docker-fundamentals/README.md) |
| 07 | Docker Images (multi-stage) | [session-07-docker-images](session-07-docker-images/README.md) |
| 08 | Docker Networking & Volumes | [session-08-docker-networking](session-08-docker-networking/README.md) |
| 09 | Kubernetes Fundamentals | [session-09-kubernetes-fundamentals](session-09-kubernetes-fundamentals/README.md) |
| 10 | Pods, ReplicaSets & Deployments | [session-10-pods-replicasets-deployments](session-10-pods-replicasets-deployments/README.md) |
| 11 | Kubernetes Networking & Services | [session-11-kubernetes-services](session-11-kubernetes-services/README.md) |
| 12 | Ingress, ConfigMaps & Secrets | [session-12-ingress-configmaps-secrets](session-12-ingress-configmaps-secrets/README.md) |
| 13 | Storage, HPA & Probes | [session-13-storage-hpa-probes](session-13-storage-hpa-probes/README.md) |
| 14 | Kubernetes Troubleshooting | [session-14-kubernetes-troubleshooting](session-14-kubernetes-troubleshooting/README.md) |
| 15 | Helm | [session-15-helm](session-15-helm/README.md) |
| 16 | CI/CD & GitHub Actions | [session-16-cicd-github-actions](session-16-cicd-github-actions/README.md) |
| 17 | Complete CI/CD & DevSecOps | [session-17-devsecops](session-17-devsecops/README.md) |
| 18 | Terraform & Infrastructure as Code | [session-18-terraform-iac](session-18-terraform-iac/README.md) |
| 19 | Cloud & Terraform in Action | [session-19-terraform-cloud](session-19-terraform-cloud/README.md) |
| 20 | Monitoring, Observability & GitOps | [session-20-monitoring-gitops](session-20-monitoring-gitops/README.md) |
| 21 | Final DevOps Project & Troubleshooting | [final-devops-project](final-devops-project/README.md) |

## Setup used

- Windows 11 + Docker Desktop
- An Ubuntu 24.04 container (`devops-lab`) as the Linux workstation for the Linux/shell/networking/git labs and as the CLI box for docker, kubectl, helm, terraform, aws
- Kubernetes: Minikube (session 9), kind multi-node clusters (sessions 10-21)
- AWS: real AWS account, region ap-south-1 (sessions 18, 19 - destroyed after the screenshots); LocalStack emulator for the session 21 project
- CI/CD: GitHub Actions in this repo ([workflows](.github/workflows)), images in GHCR
