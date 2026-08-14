---
id: intro
title: Overview
sidebar_label: Overview
slug: /
---

# minicloud Ansible

Ansible collection managing the **full lifecycle of minicloud bare-metal nodes** — from post-MAAS provisioning to Day-2 rolling upgrades across the 5-node k3s cluster.

## Responsibility

| In scope | Out of scope |
|---|---|
| Post-MAAS node bootstrap (OS hardening, k3s install) | MAAS provisioning (minicloud-opentofu) |
| Day-2 operations (k3s upgrades, rolling drain) | Helm values and GitOps (minicloud-gitops) |
| Common roles: NTP, sysctl, multipath, UFW | Application deployment (ArgoCD) |
| GRUB / efibootmgr NVMe boot fixes | |

## Stack

| Concern | Choice |
|---|---|
| Engine | Ansible 9.x + ansible-core 2.16 |
| Target OS | Ubuntu 22.04 LTS (x86\_64) |
| k3s | v1.32.x |
| Linting | ansible-lint 24.x |

## Cluster nodes

| Node | IP | Role |
|---|---|---|
| set-hog | 10.0.0.2 | k3s control plane |
| fast-skunk | 10.0.0.4 | k3s worker |
| fast-heron | 10.0.0.7 | k3s worker |
| star-kitten | 10.0.0.8 | k3s worker |
| swift-mac | 10.0.0.10 | k3s worker (MacBook Pro 2012) |

## Key playbooks

| Playbook | Purpose |
|---|---|
| `playbooks/install-k3s.yml` | Bootstrap k3s cluster (server + agents) |
| `playbooks/upgrade-k3s.yml` | Rolling k3s version upgrade |
| `playbooks/bootstrap-node.yml` | Common post-MAAS hardening |

## Links

- [GitHub repository](https://github.com/andrelair-platform/minicloud-ansible)
- [Platform documentation](https://andrelair-platform.github.io/minicloud-platform-docs/)
