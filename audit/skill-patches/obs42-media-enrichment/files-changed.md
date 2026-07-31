# Files Changed

| File | Before SHA-256 | After SHA-256 | Purpose |
|---|---|---|---|
| `media-enrichment/scripts/run_media_enrichment.py` | `824de0a4677f60cacfa74c096bdab4d180857539b7f556473446ac55f6efb0e3` | `0f86838f57b02eb0d970404a072609d7bf4fa98e807f0f64d67607df7a0dedbd` | continue读取冻结本地字节并镜像required outputs |
| `media-enrichment/tests/test_single_asset_e2e.py` | `07de60bf7be20fc2d64e6e3cd4b838fb3d43653fc9486b484c4b63d749f902b8` | `c758dd627fb931034d4f60368b667c882363452e0b7994d64f76db3522c4c69a` | 更新/新增冻结字节、安全失败闭合与根输出回归测试 |

测试：`283 passed, 6 skipped`。


## Re-lock evidence

- Official algorithm: `wxgzh_pipeline.skill_discovery.compute_root_sha()` and `_file_sha()`; runtime files only, text newlines normalized.
- Before lock file SHA-256: `ff64e8ae3b5e80e2c45a5a86e8945c223ac6b1b6ca823a41a2d7b8fc45eef53b`
- After lock file SHA-256: `c3f9a4ce07921e9ce5271faec92723bae4b90861af835c42cf3c0a72d8a3f16c`
- media skill_root_sha256: `e982b757f37050b0a92cbb4378b106a4f3637224ad3de4abc8b3389e6196a4f7`
- media entrypoint_sha256: `c99d5f505f8c9bc2aca064546ff91ffcae64a9667af00beb3121fe16d47a4641`
- runtime_manifest_sha256 unchanged: `172aa1b8082c6bb80822e56e201732ba5a118c6a53d7472f34b911f4a891e996`
- runtime_file_count unchanged: `57`

Doctor result: `skills_locked_ok=true`, `EXTERNAL_DEPENDENCY_AIHOT=INSTALLED`, `LIVE_PIPELINE_ALLOWED=true`, `wechat_config_present=true`, `FAIL_CLOSED=false`, `doctor=PASS`.
