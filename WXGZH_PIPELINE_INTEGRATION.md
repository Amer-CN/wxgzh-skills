# wxgzh-pipeline Integration Lock

This repository is an **independent Skill** consumed by the
[`wxgzh-pipeline`](https://github.com/Amer-CN/wxgzh-pipeline) orchestrator as a
locked dependency. The orchestrator pins this Skill by version **and** a
deterministic root hash, and never modifies its business logic.

| Field | Value |
| --- | --- |
| Skill | `gzh-design` |
| Locked version | `v2026.08.02-hammer.2` |
| Locked root SHA-256 | `802350c131ed537b33e874490749b8b6f71d8bb6c83c4038d678d548c31daafc` |
| Hash algorithm | sha256 over sorted `relpath:sha256(content)`, excluding `__pycache__/.git/.pytest_cache/.github` |

**Documented entrypoints**
  - `scripts/generate_hammer_upgrade_samples.py`
  - `scripts/generate_advanced_html.py`
  - `scripts/validate_gzh_html.py`
  - `scripts/publish_wechat_draft.py`

**Output contract consumed by wxgzh-pipeline**
  - `final.html`
  - `theme_identity_report.json`

_Additive integration metadata only — this file does not change Skill behavior._
_Origin: wxgzh-pipeline 0.1.0-dev2 Phase A repository synchronization._
