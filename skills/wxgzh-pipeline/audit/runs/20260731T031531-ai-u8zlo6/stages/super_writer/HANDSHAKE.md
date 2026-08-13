# Agent handshake — super_writer

Skill: `super-writer`

Run Super Writer Material-Heavy Full Mode. Generate every requested product, then run the locked official validate_article_length.py with --full-mode --json and save its exact JSON stdout as full_mode_validator_report.json before ACK.

Produce these files in this directory, then write `agent_handshake.json`:
- `generation-profile.yaml`
- `writing-brief.md`
- `material-readiness.yaml`
- `material-ingestion-report.json`
- `material-ledger.yaml`
- `evidence-map.md`
- `canonical_claim_registry.json`
- `core-card.md`
- `outline.md`
- `semantic-map.yaml`
- `article.md`
- `editor-report.md`
- `full_mode_validator_report.json`

Write the ACK with the supported command:

```bash
python -m wxgzh_pipeline.ack_cli --stage-dir "F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260731T031531-ai-u8zlo6\super_writer"
```

The command reads this request; do not repeat stage or outputs. The ACK token binds the request bytes + upstream input hashes + the produced file hashes; any post-ACK edit invalidates the handshake.
