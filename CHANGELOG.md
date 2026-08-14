# Changelog

## [0.1.1](https://github.com/andrelair-platform/minicloud-ansible/compare/minicloud-ansible-v0.1.0...minicloud-ansible-v0.1.1) (2026-08-14)


### Features

* add Authentik OIDC + LANGFUSE_INIT_* env vars for Langfuse ([309ea42](https://github.com/andrelair-platform/minicloud-ansible/commit/309ea42c207002f9cd6476025ee72c5ef80ec08f))
* add Langfuse v3 Helm values ([03ef4e3](https://github.com/andrelair-platform/minicloud-ansible/commit/03ef4e39ff04413ea5a9176d960eb8b4e964c7e1))
* **ai:** add llama3.2:1b to LiteLLM ConfigMap model list ([f9b0a7e](https://github.com/andrelair-platform/minicloud-ansible/commit/f9b0a7edfb7d4e9341b6a2db2f682ec69258fc2c))
* **ai:** deploy LiteLLM AI Gateway with PostgreSQL persistence ([a35a77a](https://github.com/andrelair-platform/minicloud-ansible/commit/a35a77a1c3461038aee1891a1a768ed1d9380fbb))
* **argocd:** disable local admin account ([665a103](https://github.com/andrelair-platform/minicloud-ansible/commit/665a1039c42d7501b753a2a5fb6447ef7105b491))
* **argocd:** enable GPG commit verification with AndreLiar public key ([278e620](https://github.com/andrelair-platform/minicloud-ansible/commit/278e620bcfd29fa17c6c4f5d13e70b71ab008154))
* **authentik:** replace {{SECRET_KEY}} template with ESO envFrom injection ([d14dba5](https://github.com/andrelair-platform/minicloud-ansible/commit/d14dba5925385737c3036cc4814c8e1ae7f9113c))
* **catalog:** add Backstage catalog-info.yaml (Phase 18) ([5643846](https://github.com/andrelair-platform/minicloud-ansible/commit/5643846f3f1d7fc75e94acadb11c57242f615fae))
* **cis:** CIS k3s-cis-1.7 kubelet hardening — 16/16 PASS on all workers ([87e777f](https://github.com/andrelair-platform/minicloud-ansible/commit/87e777f6c75a9e44b054d2e05436c84a1c14db35))
* **common:** add sqlite3 for Phase 14 k3s state.db online backup ([0f3b5cf](https://github.com/andrelair-platform/minicloud-ansible/commit/0f3b5cf7914ba3f1567c43b2d02723fe67112c3d))
* enable Falco Sidekick → Alertmanager + add Polaris workload scorer ([1947ccc](https://github.com/andrelair-platform/minicloud-ansible/commit/1947ccca108476433b0104089c31ec22148a40e0))
* enable RAG re-ranking via cross-encoder/ms-marco-MiniLM-L-6-v2 ([2fc03f7](https://github.com/andrelair-platform/minicloud-ansible/commit/2fc03f75f3f88bde9e80b6e3a55968562c08b672))
* **helm-values:** mirror authentik-values.yaml (Phase 23 Stage 1 deployed) ([66bcaeb](https://github.com/andrelair-platform/minicloud-ansible/commit/66bcaeb8c8c7d8841c8aac49073f5ba4f60fab48))
* **helm-values:** mirror open-webui-values.yaml with Authentik OIDC (Phase 23 Stage 5) ([005c6ba](https://github.com/andrelair-platform/minicloud-ansible/commit/005c6ba5a16c8516782edf1556748caacdf533df))
* **inventory:** add star-kitten and swift-mac worker nodes ([bc7e814](https://github.com/andrelair-platform/minicloud-ansible/commit/bc7e8141bda46434947207729108cbcf5b31d045))
* **k3s-registries:** point at HTTPS Harbor + distribute root CA cert (Phase 15) ([5d3c112](https://github.com/andrelair-platform/minicloud-ansible/commit/5d3c11232ffd1194bb0fc8e7e1b41a3abf7b7618))
* **k3s-registries:** route all upstream pulls through Harbor proxy cache (Phase 16) ([1d4aa4a](https://github.com/andrelair-platform/minicloud-ansible/commit/1d4aa4a909ed06831d86f68d5c61c4491ddf4916))
* **monitoring:** add Prometheus and Alertmanager ingresses, fix duplicate alertmanager key ([1cd6e30](https://github.com/andrelair-platform/minicloud-ansible/commit/1cd6e30c8ac2a206b18cefcf6d324bc3d352d0c1))
* **networking:** Flannel → Cilium rolling migration playbook ([#2](https://github.com/andrelair-platform/minicloud-ansible/issues/2)) ([4e22bcf](https://github.com/andrelair-platform/minicloud-ansible/commit/4e22bcf5e680546421e7751290d25aa1443de6e8))
* **nextcloud:** add Helm values for Nextcloud 33 ([5c09b33](https://github.com/andrelair-platform/minicloud-ansible/commit/5c09b3313f45cde77e8499393746d54760a2b0ac))
* **nextcloud:** persist allow_local_remote_servers for Authentik OIDC ([404e4cf](https://github.com/andrelair-platform/minicloud-ansible/commit/404e4cfff24c0f9ab378bd34858a6f0fb77e41b1))
* **open-webui:** CA bundle init container, phi3-financial default model, devandre.sbs OIDC URL ([01650a0](https://github.com/andrelair-platform/minicloud-ansible/commit/01650a00bf6b8dcf547fbfc46a6c2e244e24bac6))
* **open-webui:** enable Docling OCR extraction engine ([d8a4bf6](https://github.com/andrelair-platform/minicloud-ansible/commit/d8a4bf6f2257e303a805c1afcf364632e888c309))
* **open-webui:** enable native hybrid search with explicit BM25 weight ([7a2e75e](https://github.com/andrelair-platform/minicloud-ansible/commit/7a2e75ebee2c69fe29b7f62ca847e2632e521c73))
* **open-webui:** French BM25 preprocessor via init container patch ([0373fe2](https://github.com/andrelair-platform/minicloud-ansible/commit/0373fe2a0a31d35e04aaa79c56193706e7e614d1))
* **phase-10:** initial ansible bootstrap repo ([b869d22](https://github.com/andrelair-platform/minicloud-ansible/commit/b869d2203a16ce484a35305ac70777a51f4fdf69))
* **phase25:** add devandre.sbs Ingress hosts to ArgoCD and Grafana helm values ([be2213d](https://github.com/andrelair-platform/minicloud-ansible/commit/be2213dd33c47e274cb6486d2dbbca98cbcf3a9d))
* **playbooks:** add k3s cluster bootstrap playbook ([08a8fc8](https://github.com/andrelair-platform/minicloud-ansible/commit/08a8fc8ea9626f171d3703be67fe0ed630cf3eec))
* **rbac:** Phase 33 — Authentik department RBAC + ArgoCD/Grafana role mappings ([74dba46](https://github.com/andrelair-platform/minicloud-ansible/commit/74dba46b81e6fb758d02d77595b902c07079425d))
* **scripts:** add Authentik group membership and Grafana dashboard import utilities ([4cb4634](https://github.com/andrelair-platform/minicloud-ansible/commit/4cb463468896244a78e923895e2c562ca92abe4f))
* **scripts:** add authentik-apps-create.sh (Phase 23 Stage 2) ([90d901c](https://github.com/andrelair-platform/minicloud-ansible/commit/90d901cfdb1c2263c483e44e24ac964eed903371))
* **scripts:** add bs-catalog.sh — Backstage UI bug workaround ([ef28749](https://github.com/andrelair-platform/minicloud-ansible/commit/ef287495c386d6f11ec874f40c8714848675159f))
* **scripts:** add pin-audit.sh + fix shell-pollution bug in bs-catalog.sh ([c15e475](https://github.com/andrelair-platform/minicloud-ansible/commit/c15e475f08e6dd0c0f57aad974dd94d44bfdba1b))
* **security:** Gap 12 — HSTS + rate limiting + Authentik forward-auth on monitoring ([40ff61d](https://github.com/andrelair-platform/minicloud-ansible/commit/40ff61ddf0593ca0c732993678ca4bc047758b7e))
* **vault:** add AWS KMS auto-unseal (eu-west-1) ([2a1eab9](https://github.com/andrelair-platform/minicloud-ansible/commit/2a1eab9b94f7e89c325f515abe4aa823b009e7b1))
* **vault:** add Helm values for GitOps migration ([62b137d](https://github.com/andrelair-platform/minicloud-ansible/commit/62b137d15f9e99584deac3a4dd397009cba4590d))
* **velero:** exclude monitoring and harbor from daily backups ([afeaac6](https://github.com/andrelair-platform/minicloud-ansible/commit/afeaac671e1a82ee59b93a6a11cc518534a50b44))


### Bug Fixes

* add devandre.sbs TLS entries to ArgoCD and Grafana ingress values ([94d12ca](https://github.com/andrelair-platform/minicloud-ansible/commit/94d12cab922dd6ae038c6fbf75ac8e8b7c37eb80))
* add required langfuse.salt secretKeyRef ([2757b99](https://github.com/andrelair-platform/minicloud-ansible/commit/2757b99c24e5276961bb6d55466458886ad07b3d))
* align postgresql existingSecretKey.userPasswordKey with 'password' ([9838a82](https://github.com/andrelair-platform/minicloud-ansible/commit/9838a82786ada70c36380d6695c3f215efabeb02))
* **backstage:** set prompt=login on OIDC provider to fix login_required loop ([48de901](https://github.com/andrelair-platform/minicloud-ansible/commit/48de90115ed52b48ea4f276305a3a892ed70d9fe))
* bypass web page scraping for web search — use SearXNG snippets directly ([22a98a3](https://github.com/andrelair-platform/minicloud-ansible/commit/22a98a39a3683c199653f9df06cbe9cb79473bf6))
* **certs:** add explicit duration/renewBefore to prometheus and alertmanager ingress certs ([560f8e1](https://github.com/andrelair-platform/minicloud-ansible/commit/560f8e12857e9e76109465d4f0c6c03c4f3bb172))
* **cilium-migration:** add --context minicloud to all kubectl delegate_to:localhost calls ([#3](https://github.com/andrelair-platform/minicloud-ansible/issues/3)) ([5e246c3](https://github.com/andrelair-platform/minicloud-ansible/commit/5e246c38097fb9c2b0cf971f3c3654b8a94c5d49))
* **cilium-migration:** use k8s-app=cilium label — Cilium 1.19 uses cilium-agent not cilium in app.kubernetes.io/name ([#5](https://github.com/andrelair-platform/minicloud-ansible/issues/5)) ([65cf2e4](https://github.com/andrelair-platform/minicloud-ansible/commit/65cf2e4eba5aff7649b6ac0e2aaadcbe19082dec))
* **cilium-migration:** use minicloud-break-glass context — minicloud context doesn't exist on Mac ([#4](https://github.com/andrelair-platform/minicloud-ansible/issues/4)) ([59c9079](https://github.com/andrelair-platform/minicloud-ansible/commit/59c9079be62f77f06a750eadc0b474c4f1a7a81d))
* ClickHouse resourcesPreset nano→medium (OOMKilled with 192Mi) ([eb46003](https://github.com/andrelair-platform/minicloud-ansible/commit/eb46003f32f3c6e56aeae7a7d9d0a2138cd079b8))
* correct ArgoCD OIDC provider slug (argocd -&gt; argo-cd) ([81dca87](https://github.com/andrelair-platform/minicloud-ansible/commit/81dca8718d8dda02f8afede7f8675e2c6612cbd2))
* correct Open WebUI web search env var names (ENABLE_WEB_SEARCH, WEB_SEARCH_ENGINE) ([dc711e6](https://github.com/andrelair-platform/minicloud-ansible/commit/dc711e6b99cebb8052f1e2d5e2bf412c493ad1b1))
* disable Redis auth (WRONGPASS), increase langfuse memory limit to 2Gi ([76d1dd9](https://github.com/andrelair-platform/minicloud-ansible/commit/76d1dd9ef7fb85936e0033e48a4cf8ad19a90458))
* **grub:** add efibootmgr Ubuntu UEFI entry creation step ([#9](https://github.com/andrelair-platform/minicloud-ansible/issues/9)) ([4f1a836](https://github.com/andrelair-platform/minicloud-ansible/commit/4f1a8362e711071a1851ffbd874ded36223936d5))
* **grub:** add fix-grub-timeout playbook for NVMe boot loop on ThinkPads ([df7e530](https://github.com/andrelair-platform/minicloud-ansible/commit/df7e530a5f92282161e436bf469d2c3643f0d421))
* **nextcloud:** set usernameKey in existingSecret — chart requires non-empty key ([b8c12b1](https://github.com/andrelair-platform/minicloud-ansible/commit/b8c12b17ca463f00f0c8b0a29e645ba29de443f8))
* **oidc:** migrate ArgoCD, Grafana, Backstage OIDC issuer URLs to auth.devandre.sbs ([a8ac021](https://github.com/andrelair-platform/minicloud-ansible/commit/a8ac021c450cf4a5feb0b356b3eab2d85b990e41))
* **ollama:** pin to fast-heron + migrate PVC to local-path ([a1f3171](https://github.com/andrelair-platform/minicloud-ansible/commit/a1f3171aac9396c2e56784870ead7755aac870e1))
* polaris values — resources under dashboard.resources, chart version 6.* ([96a7f22](https://github.com/andrelair-platform/minicloud-ansible/commit/96a7f221c493bbea06ffea61d1eac2f8991f1f61))
* **security:** add allowPrivilegeEscalation: false to own workloads — close Gatekeeper warnings ([3ec59be](https://github.com/andrelair-platform/minicloud-ansible/commit/3ec59be6e5510c96ee8558c5d2f5eeedd59bd9d4))
* **supply-chain:** add Dependabot for GitHub Actions weekly updates ([1c233df](https://github.com/andrelair-platform/minicloud-ansible/commit/1c233df00a0c0dc5f957bd5e573996f269fabc73))
* **supply-chain:** explicit docker.io prefix for vault-agent injector image ([ebf96b1](https://github.com/andrelair-platform/minicloud-ansible/commit/ebf96b146ca555a08247074671ec4863dc8b1aa8))
* switch OIDC issuer/auth URLs from nip.io to auth.devandre.sbs ([22affdc](https://github.com/andrelair-platform/minicloud-ansible/commit/22affdc4cb4ffb7414bba9143e564be54c0a5143))
* use nip.io OIDC issuer with CA trust instead of devandre.sbs ([bb43411](https://github.com/andrelair-platform/minicloud-ansible/commit/bb43411f2cffb8277fde5ecd5781f585b4a4bd41))

## Changelog

All notable changes to minicloud-ansible are documented here.

This file is maintained by [release-please](https://github.com/googleapis/release-please).
