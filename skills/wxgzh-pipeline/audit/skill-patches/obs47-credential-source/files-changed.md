# Files Changed

| Tree/File | Before SHA-256 | After SHA-256 |
|---|---|---|
| `media-enrichment/scripts/run_media_enrichment.py` | `7ff4caa8a1ffffc14d2fbe1bc18b3b3cd7367e50c0b6fe3535200ea6000e34c4` | `79117b7e32a2b1cfe0505fe6f626db45ee504b78c06671af02bd26ad66cde57c` |
| `media-enrichment/src/media_enrichment/uploader.py` | `e00b125d79db0e2fa77c082e259cd80a0d1731a6d04c6e09534efa0e294db0d2` | `31ff33f6a328eadb1eeb69fba7109651f5514b67ecb7ce0c0d540ed9c6dfd357` |
| `media-enrichment/tests/test_uploader_manifest.py` | `28ee4b11d1eaf66ccf215476bb87e04e70de875d9b3dfe187d5565b0a3a9b41a` | `f847a64fc8c2fde0554c157c307a512ec7870df580b96064ab9185e0f0d2bfe8` |
| `wxgzh-pipeline/wxgzh_pipeline/producers.py` | `47653d4aa1fc81b077d626a809dbf6c33fcb5788b70679895286e98376542cf5` | `b06fdd6885ac13feea5219956886650c246e0e0072cfa8bd939ae343589e9964` |

## Lock inputs
- media root `1dab61844d364f2ca401b0516a6a118cfa80a9b14c9f29379d0a76ab5149953b`, manifest `172aa1b8082c6bb80822e56e201732ba5a118c6a53d7472f34b911f4a891e996`, count `57`, entry `a54deef36cefd952cffa88c404858948150e383636a74ac7f996fe791aa9541e`
- pipeline runtime root evidence `bc5009621c4b0ffeebaf19f239d27c7ea38805ab0cf934379b6358e195c8843a`, manifest `38692c0c8e011c1080594fecf3079864ad996c193ce117cee1c441b258cc84fc`, count `113`
- media tests: `286 passed, 6 skipped, 0 failed`
- Pipeline tests: all code tests passed; one portable-installer Git fixture failed because copied fixture lacked `.git`.

- New test `wxgzh-pipeline/tests/test_obs47_credential_source.py`: `78a3be6831fda44871883b2a59a12e2a85bc8ff234dede313cb681d2babddbd9`
- Direct credential-source assertion: `PASS` (pytest retry intentionally not used after safe-delete denial).
