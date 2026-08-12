# wxgzh-pipeline Integration Lock

This repository is an **independent Skill** consumed by the
[`wxgzh-pipeline`](https://github.com/Amer-CN/wxgzh-pipeline) orchestrator as a
locked dependency. The orchestrator pins this Skill by version **and** a
deterministic root hash, and never modifies its business logic.

| Field | Value |
| --- | --- |
| Skill | `media-enrichment` |
| Skill version | `0.1.0-dev13` |
| Pipeline lock | Computed from the complete committed tree and pinned externally in `wxgzh-pipeline/skills.lock.json` |
| Hash algorithm | sha256 over sorted `relpath:sha256(content)`, excluding `__pycache__/.git/.pytest_cache/.github` |

**Documented entrypoints**
  - `scripts/run_media_enrichment.py`
  - `scripts/validate_media_manifest.py`
  - `src/media_enrichment/uploader.py`

**Output contract consumed by wxgzh-pipeline**
  - `media_manifest.json`
  - `article_image_bindings.json`

_Additive integration metadata only — this file does not change Skill behavior._
_Origin: wxgzh-pipeline 0.1.0-dev2 Phase A repository synchronization._
