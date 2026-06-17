# Helm values — source of truth

Snapshot of Helm chart values files used by workloads that are **directly Helm-managed** on the cluster (i.e., NOT yet migrated to ArgoCD's app-of-apps in `minicloud-gitops`).

Stored here so they survive a full controller wipe. Without this, the only copy lives in the controller's filesystem at `/home/ktayl/minicloud-ktaylorganisation/`.

## Files

| File | Chart | Cluster release | Notes |
|---|---|---|---|
| `backstage-values.yaml` | `backstage/backstage` (chart `backstage-2.7.0`) | `backstage/backstage` | Pinned to image tag `1.51.2` after `:latest` hit a `NotImplementedError: plugin.notifications.service`. Postgres subchart in standalone mode on Longhorn (1 GiB PVC). |
| `ollama-values.yaml` | `ollama/ollama` (chart `ollama-1.56.0`) | `ollama/ollama` | Pinned to image tag `0.23.2` to lock the validated llama3.2:3b + Open WebUI integration. CPU-only inference on ThinkPads, 10 GiB Longhorn PVC for model storage. |
| `authentik-values.yaml` | `authentik/authentik` (chart `2026.5.3`) | `authentik/authentik` | Phase 23 SSO + IAM identity provider. Single server + worker, Postgres on Longhorn (1 GiB PVC). Secret_key + Postgres password use `{{PLACEHOLDER}}` substitution (the chart's `existingSecret.secretName` mechanism doesn't preserve non-secret postgres host/port/etc. fields). See the file header for the substitution one-liner. |

## Workflow

When a values file changes on the controller, copy it here and commit:

```bash
cp /home/ktayl/minicloud-ktaylorganisation/<name>-values.yaml \
   /home/ktayl/minicloud-ktaylorganisation/ansible/helm-values/<name>-values.yaml
git -C /home/ktayl/minicloud-ktaylorganisation/ansible add helm-values/<name>-values.yaml
git -C /home/ktayl/minicloud-ktaylorganisation/ansible commit -m "chore(helm-values): update <name>-values.yaml"
git -C /home/ktayl/minicloud-ktaylorganisation/ansible push origin main
```

## Future migration

The eventual target architecture is for every workload to live in `minicloud-gitops` and be reconciled by ArgoCD (the Phase 12 pattern already used for `homer`, `whoami`, `platform-demo`, `event-demo`). Each migration is its own focused work block because the workload usually has live state (PVCs, databases) that must survive the cut-over.

Until each migration ships, this directory is the durable backup.
