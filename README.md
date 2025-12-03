# Probe Timeout Operator

A custom Kubernetes operator built with [Kopf](https://kopf.readthedocs.io/en/stable/) that automatically patches `livenessProbe` and `readinessProbe` configurations in `Deployment` and `StatefulSet` resources. If any container has a probe with `timeoutSeconds: 1`, it updates it to `timeoutSeconds: 5`.

---

## Features

- Watches `apps/v1` Deployments and StatefulSets
- Runs every 60 seconds using Kopf timers
- Automatically patches probes with `timeoutSeconds: 1` to `5`
- Designed to run inside a Kubernetes cluster

---

## Project Structure

| File            | Description                                      |
|-----------------|--------------------------------------------------|
| `operator.py`   | Main operator logic using Kopf                   |
| `Dockerfile`    | Container image definition                       |
| `requirements.txt` | Python dependencies (`kopf`, `kubernetes`)     |
| `healthz.sh`    | Health check script for container readiness      |
| `README.md`     | Project documentation                            |

---

## Build and Push

```bash
docker build -t registry.*********/devops/probe-timeout-operator:latest .
docker login registry.******** -u <username> -p <token>
docker push registry.************/devops/probe-timeout-operator:latest


note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
