# 档 30 —— 收敛升级回归排除清单:停机上报版

> **状态:按第 3c 条停机上报。** 27 项实测无一 PASS;26 项根因为环境缺失(可保留+写恢复条件),**1 项(序号 20,portable installer)根因指向代码/发布工程常量问题** → 按指令不自行修复、不收敛定稿、不 commit/push。本报告为完整事实记录,待裁决后继续。

## 1. env 取值(第 1 步要求记录)

| 变量 | 取值 |
| --- | --- |
| `AGENT_SKILLS_HOME` | 无值(未设置) |
| `WXGZH_PROJECT_ROOT` | 无值(未设置) |
| python 进程内两者 | 均为 None |

## 2. 第 1 步代码修改(已完成,工作树未提交)

- `scripts/upgrade_regression.py`:`step_pytest(env)` 改为使用 `_child_env()` 返回的同一份 env(同样 pop `AGENT_SKILLS_HOME`、同样设置 `WXGZH_PROJECT_ROOT`),不再用 `dict(os.environ)`;`main` 中三个 step 共用同一 env。
- `_child_env()` 返回类型注解由 `-> dict` 修正为 `-> tuple[dict, Path]`。
- 影响实测:当前 shell 两变量均无值,故轮次 1(修改前语义,继承 os.environ)与轮次 2(修改后语义,_child_env)对 27 项结果**完全一致**(下表)。

## 3. 两轮逐项实测结果(27 项,不带任何 deselect,单独执行)

| # | 节点 | 轮次1 | 轮次2 | 根因分类 |
| --- | --- | --- | --- | --- |
| 01 | `test_fake_live_six_stages` | FAIL | FAIL | media |
| 02 | `test_receipt_tamper` | FAIL | FAIL | media |
| 03 | `test_dynamic_chapter_gate` | ERROR | ERROR | media |
| 04 | `test_resume_tamper_media_manifest_invalidates_media_and_later` | FAIL | FAIL | media |
| 05 | `test_resume_tamper_upstream_article_invalidates_media_gzh_wechat` | FAIL | FAIL | media |
| 06 | `test_receipt_tamper_fails_verify_and_resume[a_empty_object]` | FAIL | FAIL | media |
| 07 | `test_receipt_tamper_fails_verify_and_resume[b_del_input_hash]` | FAIL | FAIL | media |
| 08 | `test_receipt_tamper_fails_verify_and_resume[c_del_output_hash]` | FAIL | FAIL | media |
| 09 | `test_receipt_tamper_fails_verify_and_resume[d_del_entrypoint_sha]` | FAIL | FAIL | media |
| 10 | `test_receipt_tamper_fails_verify_and_resume[e_del_official_validators]` | FAIL | FAIL | media |
| 11 | `test_receipt_tamper_fails_verify_and_resume[f_validator_exit_1]` | FAIL | FAIL | media |
| 12 | `test_receipt_tamper_fails_verify_and_resume[g_official_exit_1]` | FAIL | FAIL | media |
| 13 | `test_wechat_gate_blocks_on_tampered_prior_receipt` | FAIL | FAIL | media |
| 14 | `test_c_material_scope_only_that_material` | FAIL | FAIL | media |
| 15 | `test_d_source_url_scope_no_inheritance` | FAIL | FAIL | media |
| 16 | `test_e_unknown_scope_not_known_allowed` | FAIL | FAIL | media |
| 17 | `test_bad_evidence_hash_ignored` | FAIL | FAIL | media |
| 18 | `test_material_scope_missing_binding_ignored` | FAIL | FAIL | media |
| 19 | `test_source_url_for_unknown_url_approves_nobody` | FAIL | FAIL | media |
| 20 | `test_portable_installer_preserves_pipeline_release_include` | ERROR | ERROR | const |
| 21 | `test_cross_repo_real_full_mode_long_pass` | FAIL | FAIL | env |
| 22 | `test_cross_repo_medium_overlong_uses_declared_policy` | FAIL | FAIL | env |
| 23 | `test_cross_repo_missing_full_mode_artifact_fails` | FAIL | FAIL | env |
| 24 | `test_02_03_defaults_and_draft` | FAIL | FAIL | media |
| 25 | `test_08_no_stage_skip` | FAIL | FAIL | media |
| 26 | `test_10_resume_no_rerun` | FAIL | FAIL | media |
| 27 | `test_full_run_delivery` | FAIL | FAIL | media |

分类:media = 环境缺失(sibling checkout);const = 代码/发布工程常量问题;env = 环境变量缺失。

### 3.1 失败输出最后 5 行(轮次 1 原样;轮次 2 逐项一致,关键错误行已逐项比对)

两轮输出文件已留存于 `%TEMP%\deselect-audit-30\round{1,2}\NN.txt`(沙箱外,不随 commit 归档);下方粘贴每项轮次 1 的最后 5 行,轮次 2 与之逐字一致。

**[01] tests/test_dev2_fake_live.py::test_fake_live_six_stages — 轮次1=FAIL / 轮次2=FAIL**
```
E         + STAGE_FAILED

tests\test_dev2_fake_live.py:28: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_dev2_fake_live.py::test_fake_live_six_stages - AssertionErr...
```

**[02] tests/test_dev2_fake_live.py::test_receipt_tamper — 轮次1=FAIL / 轮次2=FAIL**
```
E       assert (False)

tests\test_dev2_fake_live.py:69: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_dev2_fake_live.py::test_receipt_tamper - assert (False)
```

**[03] tests/test_dev2_fake_live.py::test_dynamic_chapter_gate — 轮次1=ERROR / 轮次2=ERROR**
```
E       FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\Admin\\AppData\\Local\\Temp\\pytest-of-Admin\\pytest-291\\test_dynamic_chapter_gate0\\.temp\\wxgzh-pipeline\\20260801T230842-t-ug3bwx\\gzh_design\\theme_identity_report.json'

C:\Users\Admin\AppData\Local\Programs\Python\Python310\lib\pathlib.py:1119: FileNotFoundError
=========================== short test summary info ===========================
FAILED tests/test_dev2_fake_live.py::test_dynamic_chapter_gate - FileNotFound...
```

**[04] tests/test_hotfix1.py::test_resume_tamper_media_manifest_invalidates_media_and_later — 轮次1=FAIL / 轮次2=FAIL**
```
E         + STAGE_FAILED

tests\test_hotfix1.py:35: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_hotfix1.py::test_resume_tamper_media_manifest_invalidates_media_and_later
```

**[05] tests/test_hotfix1.py::test_resume_tamper_upstream_article_invalidates_media_gzh_wechat — 轮次1=FAIL / 轮次2=FAIL**
```
E         + STAGE_FAILED

tests\test_hotfix1.py:51: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_hotfix1.py::test_resume_tamper_upstream_article_invalidates_media_gzh_wechat
```

**[06] tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[a_empty_object] — 轮次1=FAIL / 轮次2=FAIL**
```
E         + STAGE_FAILED

tests\test_hotfix2_receipt_tamper.py:25: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[a_empty_object]
```

**[07] tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[b_del_input_hash] — 轮次1=FAIL / 轮次2=FAIL**
```
E         + STAGE_FAILED

tests\test_hotfix2_receipt_tamper.py:25: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[b_del_input_hash]
```

**[08] tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[c_del_output_hash] — 轮次1=FAIL / 轮次2=FAIL**
```
E         + STAGE_FAILED

tests\test_hotfix2_receipt_tamper.py:25: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[c_del_output_hash]
```

**[09] tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[d_del_entrypoint_sha] — 轮次1=FAIL / 轮次2=FAIL**
```
E         + STAGE_FAILED

tests\test_hotfix2_receipt_tamper.py:25: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[d_del_entrypoint_sha]
```

**[10] tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[e_del_official_validators] — 轮次1=FAIL / 轮次2=FAIL**
```
E         + STAGE_FAILED

tests\test_hotfix2_receipt_tamper.py:25: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[e_del_official_validators]
```

**[11] tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[f_validator_exit_1] — 轮次1=FAIL / 轮次2=FAIL**
```
E         + STAGE_FAILED

tests\test_hotfix2_receipt_tamper.py:25: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[f_validator_exit_1]
```

**[12] tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[g_official_exit_1] — 轮次1=FAIL / 轮次2=FAIL**
```
E         + STAGE_FAILED

tests\test_hotfix2_receipt_tamper.py:25: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[g_official_exit_1]
```

**[13] tests/test_hotfix2_receipt_tamper.py::test_wechat_gate_blocks_on_tampered_prior_receipt — 轮次1=FAIL / 轮次2=FAIL**
```
E         + STAGE_FAILED

tests\test_hotfix2_receipt_tamper.py:25: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_hotfix2_receipt_tamper.py::test_wechat_gate_blocks_on_tampered_prior_receipt
```

**[14] tests/test_hotfix3_approved_scope.py::test_c_material_scope_only_that_material — 轮次1=FAIL / 轮次2=FAIL**
```
E           wxgzh_pipeline.producers.MediaRequestError: fixed media validate_request unavailable: F:\AIXM\wxgzh\repos\media-enrichment\src\media_enrichment\input_contract.py

wxgzh_pipeline\producers.py:395: MediaRequestError
=========================== short test summary info ===========================
FAILED tests/test_hotfix3_approved_scope.py::test_c_material_scope_only_that_material
```

**[15] tests/test_hotfix3_approved_scope.py::test_d_source_url_scope_no_inheritance — 轮次1=FAIL / 轮次2=FAIL**
```
E           wxgzh_pipeline.producers.MediaRequestError: fixed media validate_request unavailable: F:\AIXM\wxgzh\repos\media-enrichment\src\media_enrichment\input_contract.py

wxgzh_pipeline\producers.py:395: MediaRequestError
=========================== short test summary info ===========================
FAILED tests/test_hotfix3_approved_scope.py::test_d_source_url_scope_no_inheritance
```

**[16] tests/test_hotfix3_approved_scope.py::test_e_unknown_scope_not_known_allowed — 轮次1=FAIL / 轮次2=FAIL**
```
E           wxgzh_pipeline.producers.MediaRequestError: fixed media validate_request unavailable: F:\AIXM\wxgzh\repos\media-enrichment\src\media_enrichment\input_contract.py

wxgzh_pipeline\producers.py:395: MediaRequestError
=========================== short test summary info ===========================
FAILED tests/test_hotfix3_approved_scope.py::test_e_unknown_scope_not_known_allowed
```

**[17] tests/test_hotfix3_approved_scope.py::test_bad_evidence_hash_ignored — 轮次1=FAIL / 轮次2=FAIL**
```
E           wxgzh_pipeline.producers.MediaRequestError: fixed media validate_request unavailable: F:\AIXM\wxgzh\repos\media-enrichment\src\media_enrichment\input_contract.py

wxgzh_pipeline\producers.py:395: MediaRequestError
=========================== short test summary info ===========================
FAILED tests/test_hotfix3_approved_scope.py::test_bad_evidence_hash_ignored
```

**[18] tests/test_hotfix3_approved_scope.py::test_material_scope_missing_binding_ignored — 轮次1=FAIL / 轮次2=FAIL**
```
E           wxgzh_pipeline.producers.MediaRequestError: fixed media validate_request unavailable: F:\AIXM\wxgzh\repos\media-enrichment\src\media_enrichment\input_contract.py

wxgzh_pipeline\producers.py:395: MediaRequestError
=========================== short test summary info ===========================
FAILED tests/test_hotfix3_approved_scope.py::test_material_scope_missing_binding_ignored
```

**[19] tests/test_hotfix3_approved_scope.py::test_source_url_for_unknown_url_approves_nobody — 轮次1=FAIL / 轮次2=FAIL**
```
E           wxgzh_pipeline.producers.MediaRequestError: fixed media validate_request unavailable: F:\AIXM\wxgzh\repos\media-enrichment\src\media_enrichment\input_contract.py

wxgzh_pipeline\producers.py:395: MediaRequestError
=========================== short test summary info ===========================
FAILED tests/test_hotfix3_approved_scope.py::test_source_url_for_unknown_url_approves_nobody
```

**[20] tests/test_hotfix1.py::test_portable_installer_preserves_pipeline_release_include — 轮次1=ERROR / 轮次2=ERROR**
```
E        +  where 1 = CompletedProcess(args=['C:\\Users\\Admin\\AppData\\Local\\Programs\\Python\\Python310\\python.exe', 'C:\\Users\\Admin\...t_portable_installer_preser0\\build-staging'], returncode=1, stdout='', stderr='unexpected pipeline file count: 446\n').returncode

tests\test_hotfix1.py:301: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_hotfix1.py::test_portable_installer_preserves_pipeline_release_include
```

**[21] tests/test_hotfix7_live_handshake.py::test_cross_repo_real_full_mode_long_pass — 轮次1=FAIL / 轮次2=FAIL**
```
E               AssertionError: set WXGZH_REAL_SUPER_WRITER_ROOT or WXGZH_REAL_SKILLS_HOME

tests\test_hotfix7_live_handshake.py:35: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_hotfix7_live_handshake.py::test_cross_repo_real_full_mode_long_pass
```

**[22] tests/test_hotfix7_live_handshake.py::test_cross_repo_medium_overlong_uses_declared_policy — 轮次1=FAIL / 轮次2=FAIL**
```
E               AssertionError: set WXGZH_REAL_SUPER_WRITER_ROOT or WXGZH_REAL_SKILLS_HOME

tests\test_hotfix7_live_handshake.py:35: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_hotfix7_live_handshake.py::test_cross_repo_medium_overlong_uses_declared_policy
```

**[23] tests/test_hotfix7_live_handshake.py::test_cross_repo_missing_full_mode_artifact_fails — 轮次1=FAIL / 轮次2=FAIL**
```
E               AssertionError: set WXGZH_REAL_SUPER_WRITER_ROOT or WXGZH_REAL_SKILLS_HOME

tests\test_hotfix7_live_handshake.py:35: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_hotfix7_live_handshake.py::test_cross_repo_missing_full_mode_artifact_fails
```

**[24] tests/test_pipeline.py::test_02_03_defaults_and_draft — 轮次1=FAIL / 轮次2=FAIL**
```
E         + STAGE_FAILED

tests\test_pipeline.py:40: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_pipeline.py::test_02_03_defaults_and_draft - AssertionError...
```

**[25] tests/test_pipeline.py::test_08_no_stage_skip — 轮次1=FAIL / 轮次2=FAIL**
```
E       KeyError: 'completed_stages'

tests\test_pipeline.py:104: KeyError
=========================== short test summary info ===========================
FAILED tests/test_pipeline.py::test_08_no_stage_skip - KeyError: 'completed_s...
```

**[26] tests/test_pipeline.py::test_10_resume_no_rerun — 轮次1=FAIL / 轮次2=FAIL**
```
E       TypeError: 'NoneType' object is not subscriptable

tests\test_pipeline.py:118: TypeError
=========================== short test summary info ===========================
FAILED tests/test_pipeline.py::test_10_resume_no_rerun - TypeError: 'NoneType...
```

**[27] tests/test_pipeline.py::test_full_run_delivery — 轮次1=FAIL / 轮次2=FAIL**
```
E       assert (1 == 0)

tests\test_pipeline.py:200: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_pipeline.py::test_full_run_delivery - assert (1 == 0)
```

## 4. 根因判定(具体到缺失路径/环境变量)

- **01–19、24–27(共 23 项):** 缺失路径 `F:\AIXM\wxgzh\repos\media-enrichment`(整个 sibling checkout 缺失;producers._validate_with_fixed_media 解析自 skills_home(`F:\AIXM\wxgzh\repos`)/media-enrichment,缺 `src\media_enrichment\input_contract.py`)。链:conftest `orch` fixture 的 `media_root = SKILL_ROOT.parent/media-enrichment` 不存在 → `env={}`;`producers._validate_with_fixed_media` 回退 `skills_home/media-enrichment`(`skills_home = F:\AIXM\wxgzh\repos`)同样不存在 → `MediaRequestError: fixed media validate_request unavailable: F:\AIXM\wxgzh\repos\media-enrichment\src\media_enrichment\input_contract.py`;fake_live 六阶段在 media_enrichment 阶段 STAGE_FAILED(01/04/05/24–27),gzh_design 输出随之缺失(03),media_enrichment receipt 无效(02),hotfix2/hotfix3 在 `_complete()`/`_build()` 即失败(06–19)。
- **20(portable installer):** 缺失的不是环境,而是 `scripts/build_portable_bundle.py` 写死常量 `EXPECTED_PIPELINE_FILE_COUNT = 130`(commit `4163811`「fix: include CI workflow in release artifacts」引入后未再更新);当前 release 树实际 446 个文件(447 tracked − 1 excluded `.gitattributes`),`verify_release_artifacts` 第 74–75 行断言 `len(skill_tree) != 130` 触发 `unexpected pipeline file count: 446`。git clone/checkout 步骤均成功,与「缺 git checkout 上下文」的原注释不符。**根因指向代码/发布工程常量 → 按 3c 停机,不自行修复。**
- **21–23(hotfix7):** 缺失环境变量 `WXGZH_REAL_SUPER_WRITER_ROOT` 或 `WXGZH_REAL_SKILLS_HOME`(`test_hotfix7_live_handshake.py:35` 显式断言);随后还要求 `scripts/validate_article_length.py` 存在且 sha256 == `f2f878b14a94692fd301db197a612923cf2d9b5a8d38825b4169fe372e3d9a92`。

## 5. 四组安全核心测试单独结论(全部 18 项在 27 项内)

- **test_hotfix2_receipt_tamper.py:** 实际 8 项(参数化 a–g 共 7 项 + `test_wechat_gate_blocks_on_tampered_prior_receipt` 1 项;指令口径「9 项」与清单/文件不符,以实测 8 项为准)。当前全部**无法运行**(FAIL):根因同一缺失路径 `F:\AIXM\wxgzh\repos\media-enrichment\src\media_enrichment\input_contract.py`,`_complete()` 在 media_enrichment 阶段即 STAGE_FAILED,篡改逻辑从未执行。
- **test_hotfix3_approved_scope.py:** 6 项。当前全部**无法运行**(FAIL):`_build()` 内 `producers._build_media_request → _validate_with_fixed_media` 直接抛 `MediaRequestError`,同上缺失路径。
- **test_hotfix1.py 两项 resume tamper:** 当前**无法运行**(FAIL):`orch.run("t")` 在 media_enrichment 阶段 STAGE_FAILED(exit 2,FAIL_CLOSED),未进入 resume/tamper 断言。
- **test_dev2_fake_live.py::test_receipt_tamper:** 当前**无法运行**(FAIL):同一根因,media_enrichment 阶段失败导致 receipt 无效,`verify_receipt` 返回 False(第 69 行断言失败),tamper 逻辑未执行。

> 安全结论:这 18 项的安全断言(篡改检测、范围批准)在两轮实测中**均未得到执行**;补齐 media-enrichment sibling 前,这些保护逻辑处于「回归未覆盖」状态,建议优先补齐。

## 6. 补齐环境可行性评估(只评估,未实施)

- **测试期望的 sibling checkout 位置:** `F:\AIXM\wxgzh\repos\media-enrichment`(conftest `SKILL_ROOT.parent / "media-enrichment"`,以及 producers 默认回退路径 `skills_home/media-enrichment`,二者同一路径)。
- **本机已有可用的 media-enrichment 源:** 是。已安装 `.agents\skills\media-enrichment` 为完整源树(含 `src/media_enrichment/input_contract.py`,sha `7c2ad629…`、tests、fixtures、schemas、scripts),另 `.temp\` 下还有 dev5/dev6/dev6-hotfix1/dev7-hotfix1/oss 五个历史构建目录。`F:\AIXM\wxgzh\repos\media-enrichment` 当前**不存在**。
- **恢复路径(评估):** ① 在 `F:\AIXM\wxgzh\repos\media-enrichment` 放置完整源(如复制已安装树,`__pycache__` 由 hash 排除);或 ② 运行回归时设 `WXGZH_FIXED_MEDIA_ROOT=F:\AIXM\wxgzh\.agents\skills\media-enrichment`(producers 读取 os.environ 的该变量)。
- **hotfix7 恢复条件:** 设 `WXGZH_REAL_SUPER_WRITER_ROOT=F:\AIXM\wxgzh\.agents\skills\super-writer`(或 `WXGZH_REAL_SKILLS_HOME=F:\AIXM\wxgzh\.agents\skills`);已实测该树 `scripts/validate_article_length.py` sha = `F2F878B1…` 与锁定值一致,validator 断言可满足。
- **若补齐(评估结论):** 23 项(media 组)预期转 PASS,3 项(hotfix7)设变量后预期转 PASS,**清单可从 27 项收缩到 1 项(仅 20 号 portable installer)**,前提是 20 号常量问题另行裁决。

## 7. 停机声明

按档 30 第 3c 条:序号 20 `test_portable_installer_preserves_pipeline_release_include` 实测 FAIL 且根因指向代码/发布工程常量(`EXPECTED_PIPELINE_FILE_COUNT=130` 陈旧 vs 实际 446),**立即停机上报,未自行修复**。

因停机,以下步骤**未执行**:
- 收敛后清单定稿(26 项环境缺失按 b 保留+恢复条件,20 号待裁决;清单条目数不变——27 项无一 PASS,无 a 类移除)
- 第 6 步收敛后重跑 `upgrade_regression.py`
- 报告 commit/push(工作树仅含第 1 步已完成的 `scripts/upgrade_regression.py` 修改,未提交)

## 8. 待裁决问题

1. 序号 20 的处置:更新 `EXPECTED_PIPELINE_FILE_COUNT`(及 `EXPECTED_MANIFEST_FILE_COUNT`/`EXPECTED_BUNDLE_ZIP_FILE_COUNT`)是否授权?(属发布工程门禁常量,`RELEASE_ENGINEERING_FROZEN=true` 下需明确授权;或由发布流程统一处理。)
2. 收敛清单定稿:是否按「26 项环境缺失保留并逐条写恢复条件 + 20 号按裁决结果处理」继续,并完成第 6 步重跑与 commit/push?
