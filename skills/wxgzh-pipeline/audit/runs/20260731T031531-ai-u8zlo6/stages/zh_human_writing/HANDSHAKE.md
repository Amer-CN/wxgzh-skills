# Agent handshake — zh_human_writing

Skill: `zh-human-writing`

De-AI the Super Writer article only; freeze final_article.md (no new facts).

Produce these files in this directory, then write `agent_handshake.json`:
- `final_article.md`
- `fidelity_report.json`

Write the ACK with the supported command:

```bash
python -m wxgzh_pipeline.ack_cli --stage-dir "F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260731T031531-ai-u8zlo6\zh_human_writing"
```

The command reads this request; do not repeat stage or outputs. The ACK token binds the request bytes + upstream input hashes + the produced file hashes; any post-ACK edit invalidates the handshake.
