# minicloud — Ansible

Codifies the **post-MAAS, pre-k3s node bootstrap** for the 3-node minicloud
cluster, plus a rolling-upgrade playbook for Day-2 maintenance.

This repo is *not* responsible for installing k3s. The cluster is live and
healthy (Phases 1–9); changing it via Ansible is unnecessarily risky. These
roles cover only the OS-level prerequisites that need to be re-applied if a
node is reimaged.

**Live docs:** <https://andrelair-platform.github.io/minicloud-platform-docs/>
— see [Phase 10 — Ansible](https://andrelair-platform.github.io/minicloud-platform-docs/platform-roadmap/phase-10-ansible) for the full
walkthrough including the `--check --diff` drift audit and the rolling
upgrade playbook.

**Sibling repos in the [andrelair-platform](https://github.com/andrelair-platform) org:**
[docs](https://github.com/andrelair-platform/minicloud-platform-docs) ·
[opentofu](https://github.com/andrelair-platform/minicloud-opentofu) ·
[gitops](https://github.com/andrelair-platform/minicloud-gitops) ·
[platform-demo](https://github.com/andrelair-platform/platform-demo)

---

## Layout

```
ansible/
  ansible.cfg            # inventory path, callback format, ssh pipelining
  inventory.yml          # 3 nodes grouped: control_plane / workers / cluster
  playbooks/
    site.yml             # bootstrap: common + longhorn-prereq + k3s-registries + network
    upgrade.yml          # Day-2: rolling apt upgrade with drain/uncordon
  roles/
    common/              # base utilities (htop vim curl jq net-tools traceroute rsync)
    longhorn-prereq/     # open-iscsi installed, iscsid enabled+started
    k3s-registries/      # /etc/rancher/k3s/registries.yaml (Harbor mirror)
    network/             # /etc/netplan/99-default-gateway.yaml (default route)
```

---

## Prerequisites

* `ansible-core` 2.18 or later — install via `pipx install --include-deps ansible`
* SSH key auth from this controller to `ubuntu@10.0.0.{2,4,7}` (already in place)
* `ubuntu` user has passwordless sudo on each node (already in place)

---

## Verify connectivity

```bash
cd ansible/
ansible all -m ping
```

Expected: `pong` from `set-hog`, `fast-skunk`, `fast-heron`.

---

## Bootstrap a node (or check current state)

**Check mode** — show what *would* change without applying:

```bash
ansible-playbook playbooks/site.yml --check --diff
```

Read the `PLAY RECAP`. If `changed=0` for every host, our codified state
matches reality. If any host reports `changed > 0`, that's drift — investigate
the diff before proceeding.

**Apply** — make the nodes match the playbook:

```bash
ansible-playbook playbooks/site.yml --diff
```

**Verify idempotency** — run a second time:

```bash
ansible-playbook playbooks/site.yml --diff
```

Second run must report `changed=0`. Anything else means a task isn't
idempotent and should be fixed.

---

## Day-2: rolling apt upgrade

`upgrade.yml` runs `serial: 1` — one node at a time:

1. `kubectl drain` from the controller (delegated to localhost)
2. `apt update` + `apt upgrade safe`
3. reboot only if `/var/run/reboot-required` exists
4. wait for kubelet to mark the node Ready
5. `kubectl uncordon`

Pre-flight before running for real:

* Every workload should have ≥ 2 replicas with anti-affinity across workers
  (Phase 9's podinfo satisfies this).
* Longhorn volumes should have ≥ 2 healthy replicas — drain will fail-safe
  if it cannot relocate volumes.
* Always `--check` first.

```bash
# Validate playbook structure
ansible-playbook playbooks/upgrade.yml --syntax-check
ansible-playbook playbooks/upgrade.yml --list-tasks

# One node only (recommended for first real run)
ansible-playbook playbooks/upgrade.yml --limit fast-heron

# Full cluster — control plane will go last because workers come first
# alphabetically; reorder via `serial:` and host_vars if you want a
# different sequence.
ansible-playbook playbooks/upgrade.yml
```

---

## Why no k3s install task

The minicloud k3s cluster is live and stateful (etcd, Longhorn replicas,
Harbor registry data, monitoring TSDB). Rerunning a "k3s install" task
against a healthy node has no upside and a real risk of damaging cluster
state if anything in the curl-pipe-sh installer drifts. If a fresh node is
ever provisioned, the install command is documented in the Phase 1 doc:

```bash
curl -sfL https://get.k3s.io | sh -          # control plane
curl -sfL https://get.k3s.io | K3S_URL=… sh - # worker
```

Run that *manually* once on a fresh node, then run `site.yml` to apply the
prerequisites and config files this repo manages.

---

## Adding a new role

1. `mkdir -p roles/<name>/{tasks,files,handlers,defaults}`
2. Write `tasks/main.yml` describing the desired state (idempotent).
3. Add the role to `playbooks/site.yml` after any roles it depends on.
4. Run `ansible-playbook playbooks/site.yml --check --diff` and verify the
   diff matches expectations.
5. Apply, then run again to confirm idempotency.

A role is ready to ship when it reports `changed=0` on a second run.

---

## Troubleshooting

### `sudo: a password is required`

The `ubuntu` user on the target node lacks passwordless sudo. Either fix the
node (`/etc/sudoers.d/90-ubuntu` with `NOPASSWD:ALL`) or run with
`--ask-become-pass`.

### `community.general.yaml callback plugin has been removed`

Old `ansible.cfg` setting — use `callback_result_format = yaml` in
`[defaults]` instead of `stdout_callback = yaml`. Already fixed in this
repo's config.

### `--check` reports unexpected drift

Either the role doesn't match reality (rewrite the task) or the node has
drifted (decide whether to apply and reconcile, or update the role to match
node state). Investigate before applying — `--check --diff` shows you what
would change.

### Netplan task failed but node is unreachable

The handler runs `netplan generate` first to validate syntax; if `generate`
succeeds, `netplan apply` runs. If a node loses connectivity after a real
apply, console-login and run `netplan apply` against the previous file.
