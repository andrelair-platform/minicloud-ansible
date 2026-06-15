# Helm values — source of truth

Snapshot of Helm chart values files used by workloads that are **directly Helm-managed** on the cluster (i.e., NOT yet migrated to ArgoCD's app-of-apps in `minicloud-gitops`).

Stored here so they survive a full controller wipe. Without this, the only copy lives in the controller's filesystem at `/home/ktayl/minicloud-ktaylorganisation/`.

## Files

| File | Chart | Cluster release | Notes |
|---|---|---|---|
| `backstage-values.yaml` | `backstage/backstage` (chart `backstage-2.7.0`) | `backstage/backstage` | Pinned to image tag `1.51.2` after `:latest` hit a `NotImplementedError: plugin.notifications.service`. Postgres subchart in standalone mode on Longhorn (1 GiB PVC). |

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
