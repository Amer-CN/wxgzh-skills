# OBS-58 Draft Cover Wiring — Stage 21 Blocked Diagnosis

## Status
`BLOCKED_INSTRUCTION_CONTRADICTION_GZH_RUNTIME_RECEIPT_ROOT`

No cover upload, draft call, code modification, lock modification, route modification, receipt modification, or stage rerun was performed.

## Stage 1 self-check and backup
- OBS-42 frozen bytes present.
- OBS-17 upload observability and approval count cap present.
- OBS-18 credential bridge and token cache present.
- OBS-19 upload idempotency and dual body-images-min wiring present.
- OBS-56 stage failure persistence present.
- Backup `pre-obs58-20260801`: Pipeline 181 files/46 dirs (46 pyc/cache; 135 excluding them); gzh-design 297 files/15 dirs (2 pyc/cache; 295 excluding them).

## Stage A answers
### A-1 / A-2
`gzh-design/scripts/publish_wechat_draft.py:163-180` opens the local cover file and POSTs `UPLOAD_MATERIAL_URL` with query `type=image` and multipart field `media`; response field `media_id` is returned. `:524-526` declares mutually exclusive `--thumb-media-id` and `--cover`. `:481-489` uploads when cover is supplied, otherwise directly uses thumb-media-id.

### A-3
A-003 frozen local file: `F:/AIXM/wxgzh/.temp/wxgzh-pipeline/20260731T135947-ai-bbg4al/media_enrichment/discover/images/418d841fed238ad485cfc959555d518e5e1d6d005efd35080ce3a9035f2b87cf.png`. Actual SHA, manifest SHA and explicit single-asset approval SHA all equal `418d841fed238ad485cfc959555d518e5e1d6d005efd35080ce3a9035f2b87cf`.

### A-4
Endpoint: `POST /cgi-bin/material/add_material?type=image&access_token=<REDACTED>` with multipart media. Success returns permanent `media_id`, not only URL.

### A-5
The draft script contains no freepublish, masssend, scheduled-send or preview-mass-send call path.

### A-6
The intended choice was `--cover`: Pipeline would pass only the verified frozen A-003 path; gzh-design would own permanent upload, cover event and idempotent reuse. No code was retained because the instruction conflict below blocks implementation.

## Blocking contradiction
1. Stage 21 requires editing `gzh-design/scripts/publish_wechat_draft.py` and then re-locking gzh-design.
2. Official runtime manifest includes this file (`runtime_file_count=76`). Any edit changes the gzh-design root SHA.
3. `receipts.py:222-228` recomputes the current entire sub-skill root for every completed live-stage receipt and rejects a different root.
4. The existing completed `gzh_design/stage_receipt.json` records the pre-edit gzh-design root. Current verification is PASS with zero mismatches.
5. After the required edit/re-lock, that receipt necessarily fails `skill_root_sha256 mismatch`, so resume invalidates/re-runs `gzh_design`.
6. Stage 21 simultaneously requires only `wechat_draft`, forbids modifying/forging receipts and forbids rerunning other stages.

Therefore there is no permitted execution path. Continuing would require weakening receipt verification, rewriting a receipt, or rerunning gzh_design. All are forbidden. This triggers blocker 23 (“internal contradiction; obey stricter requirement and stop”).
