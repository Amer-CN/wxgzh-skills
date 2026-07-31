# Files Changed

| File | Before SHA-256 | After SHA-256 |
|---|---|---|
| `wxgzh_pipeline/stages/__init__.py` | `64e02c538f951f88d07b9c71216c6295632141792bf576794c51aafbb53c98e9` | `ef687a315c54bb9532dbda7af04b4acaceb5bb38b897d12f6d6b7b6fc763d799` |
| `wxgzh_pipeline/producers.py` | `b06fdd6885ac13feea5219956886650c246e0e0072cfa8bd939ae343589e9964` | `129af865de658280485557bfec206550477b678d348e99292fe4e87fa69c43ec` |
| `tests/test_obs56_stage_failure.py` | `<new>` | `4746218e6a839d9543c6cf56caa266c187ed6d919796b8a66b7651429cc2adf6` |

## Backup scope
- source and backup: 181 files / 46 directories each
- includes 46 pyc/cache files; excluding them: 135 files

## Lock evidence
- Official generation/verification: `compute_root_sha()` + `compute_runtime_manifest_sha()` + locked entrypoint SHA checks.
- All four locked external Skills match root/manifest/count.
- `skills.lock.json` before/after SHA-256: `a9e07ef42017cff225158466213253baf1155f34a7c2f1bdaf62a87dbbc751d6` (unchanged).
- Reason: this patch changes Pipeline source only; `skills.lock.json` locks external Skills, not Pipeline itself.
- doctor: `PASS`, `skills_locked_ok=true`, `wechat_config_present=true`.
