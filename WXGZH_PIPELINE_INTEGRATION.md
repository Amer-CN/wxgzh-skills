# wxgzh-pipeline Integration Lock

This repository is an **independent Skill** consumed by the
[`wxgzh-pipeline`](https://github.com/Amer-CN/wxgzh-pipeline) orchestrator as a
locked dependency. The orchestrator pins this Skill by version **and** a
deterministic root hash, and never modifies its business logic.

| Field | Value |
| --- | --- |
| Skill | `super-writer` |
| Locked version | `0.3.6-rc1` |
| Locked root SHA-256 | `b822c24a6027c462e04936924f43b0bdee9e7170b11b471e53817ae1c29ce8f0` |
| Hash algorithm | sha256 over sorted `relpath:sha256(content)`, excluding `__pycache__/.git/.pytest_cache/.github` |

**Documented entrypoints**
  - `scripts/material_ingestion.py`
  - `scripts/validate_article_length.py`
  - `scripts/validate_semantic_map.py`

**Output contract consumed by wxgzh-pipeline**
  - `writing-brief`
  - `material-readiness`
  - `material-ledger`
  - `evidence-map`
  - `canonical_claim_registry.json`
  - `core-card`
  - `outline.md`
  - `semantic-map`
  - `article.md`
  - `editor-report`
  - `full_mode_validator_report.json`

_Additive integration metadata only — this file does not change Skill behavior._
_Origin: wxgzh-pipeline 0.1.0-dev2 Phase A repository synchronization._
