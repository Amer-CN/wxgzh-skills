# Files Changed

| Tree/File | Before SHA-256 | After SHA-256 |
|---|---|---|
| `media-enrichment/scripts/run_media_enrichment.py` | `79117b7e32a2b1cfe0505fe6f626db45ee504b78c06671af02bd26ad66cde57c` | `a346dc9c0603756f9c1629857e34cdd68f441fb350d21c7d5cd78eac65cec034` |
| `media-enrichment/tests/test_single_asset_e2e.py` | `c758dd627fb931034d4f60368b667c882363452e0b7994d64f76db3522c4c69a` | `b72d37da34be53d6eaec39989d31d94d107e078bec8a875dcb63dd0311520248` |
| `wxgzh-pipeline/validators/validate_media_bindings.py` | `e253ddc4a867d025dd2cbdef8c34a4d087b8461fde83b31201a795cde3bb6d42` | `470693397bcdbd83a0ba9aca424c688922548a0df7a07e99341cb83546a8a462` |
| `wxgzh-pipeline/wxgzh_pipeline/stages/media_enrichment.py` | `0d3fb0e703b35f6cbb3e7b399022337b6f5d9d492e7c77a7f2960632fd16da77` | `e90e3b13e2926edcf5c88e7c34b9550d96d9dd16ca974f3aced6f6ae50d3eb14` |
| `wxgzh-pipeline/wxgzh_pipeline/contracts.py` | `022eaa2f9b52dcc271c7c51299d1cc1442e90c89283df78f9668b24f4458ea14` | `1ae59524ee92bc2b818680a256b306539844b7c5cf1d5520db02a84c7d8a3baf` |
| `wxgzh-pipeline/tests/test_obs53_min_images.py` | `<new>` | `55fbf6c5e9f06ef2d7bcfb248aa31cf6a6d8c69ce7dca0a748c8122587b7d99d` |

## Official lock inputs
- media root `0d8aea2169cec17c4e9f95af66b6b4da3c532554a0a316fe3fb604bd0b7ab3a3`
- media runtime manifest `172aa1b8082c6bb80822e56e201732ba5a118c6a53d7472f34b911f4a891e996`
- media runtime count `57`
- media entry `2d877a93b37658bb5b2e247827952a86abe11fff5a9c148024238dd0cccd979f`
- media tests `289 passed, 6 skipped, 0 failed`
- Pipeline tests `142 passed, 1 skipped, 12 failed` (known safe-delete/OBS52 fixture failures)
- Direct min config assertion `PASS`
