# Agent handshake — aihot

Skill: `aihot`

Query AI HOT (anonymous read-only), aggregate + dedup; do not write the article.

Produce these files in this directory, then write `agent_handshake.json`:
- `raw_items.json`
- `deduplicated_items.json`
- `fetch_log.json`

Write the ACK with the supported command:

```bash
python -m wxgzh_pipeline.ack_cli --stage-dir "F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260730T222605-ai-9je33o\aihot"
```

The command reads this request; do not repeat stage or outputs. The ACK token binds the request bytes + upstream input hashes + the produced file hashes; any post-ACK edit invalidates the handshake.
