# wxgzh-pipeline Integration Lock

This repository is an **independent Skill** consumed by the
[`wxgzh-pipeline`](https://github.com/Amer-CN/wxgzh-pipeline) orchestrator as a
locked dependency. The orchestrator pins this Skill by version **and** a
deterministic root hash, and never modifies its business logic.

| Field | Value |
| --- | --- |
| Skill | `zh-human-writing` |
| Locked version | `0.1.0` |
| Locked root SHA-256 | `ecd1db3e8eddc8ad943469ef1a73fe1b730eef5f7725450ba24eb5ffdaf57af8` |
| Hash algorithm | sha256 over sorted `relpath:sha256(content)`, excluding `__pycache__/.git/.pytest_cache/.github` |

**Documented entrypoints**
  - `scripts/fidelity_guard.py`
  - `scripts/pattern_audit.py`
  - `scripts/change_report.py`

**Output contract consumed by wxgzh-pipeline**
  - `final_article.md`
  - `final_article_sha256`
  - `fidelity_report.json`

_Additive integration metadata only — this file does not change Skill behavior._
_Origin: wxgzh-pipeline 0.1.0-dev2 Phase A repository synchronization._
