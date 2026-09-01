# OBS-345/346/347/348 —— 77S 灵犀安装安检合规验收报告（字节级落盘）

- 档号：77S（灵犀安装安检修复：全仓库可安装性合规）。
- 授权：RELOCK_ALLOWED 临时 0→1（批准人=用户，2026-09-01，范围=档 77S 六子树合规改动）；GZH_DESIGN_WRITE_ALLOWED 维持 0（未触发）。
- 来源报告：灵犀 skill inspect 静态安全审查（super-writer，仅审查未安装），结论 DO_NOT_INSTALL / HIGH / score=54 / 45 项，2026-09-01。
- feat 提交：def95c8（27 文件内容修复）；锁链与本报告随 docs 提交落库。

## 1. 45 项逐条映射与定性（任务 0，以报告逐条核实为准）

| 类别 | 数量 | 定性 | 处置 |
|---|---|---|---|
| AST4 子进程 ×31 | 全部 tests/ | 扫描器噪声：命令均为 sys.executable + 仓库内固定脚本路径，不拼接外部输入；生产 scripts/ 实测 0 处 subprocess | SECURITY.md 基线说明，代码不动 |
| AST7 动态属性 ×1 | validate_article_length.py:1350 | 真问题 | 显式分派表（四字段全字面量），行为不变 |
| RP1 npx 无锁 ×4 | fixture article.md:23、semantic-map.yaml:156/158、test_length_material.py:601 | 真问题 | 全部锁 `npx skills@1.5.23 add gzh-design`（npm 实测 skills 最新版 1.5.23），四处逐字一致 |
| MP2 填充 ×7 | validator:712/713/718/719 + test_hf77e:54 + test_length_material:772 + test_semantic_handoff:750 | 扫描器噪声：多行表达式续行片段误判（实测定性：非内联大表） | 7 处续行改单行，零语义变化 |
| LP3 权限声明 ×1 | SKILL.md | 文档缺口 | 六技能 SKILL.md 头部加「权限与范围声明（最小权限）」 |
| EA3 过度自主 ×1 | LICENSE:16 | 扫描器误报：MIT 正文 "FITNESS FOR A PARTICULAR PURPOSE…" 被当行为声明；许可证文本不可更改 | 维持不动，SECURITY.md 记基线 |

## 2. 修复文件清单（feat def95c8，27 文件）

super-writer 12：scripts/validate_article_length.py、tests/test_length_material.py、tests/test_semantic_handoff.py、tests/test_hf77e_registry_consistency.py、tests/fixtures/semantic/fixture-b-tutorial/{article.md,semantic-map.yaml}、tests/test_hf77s_runtime_policy_dispatch.py（新增，2 用例：profile 默认填入 unset 字段/显式传参不被覆盖）、SKILL.md、VERSION、CHANGELOG.md、MANIFEST.sha256（重算 109 条目，check OK:109 FAIL:0）；
zh-human-writing 5：SKILL.md、VERSION（0.1.12）、RELEASE_NOTES.md、SHA256SUMS（重算）、verify_release.py（VERSION_EXPECTED 0.1.11→0.1.12，77R 同一做法）；
media-enrichment 3：SKILL.md、VERSION（0.1.0-dev28）、CHANGELOG.md；
gzh-design 3：SKILL.md、RELEASE_NOTES.md（顶部 v2026.09.01-hammer.20，实测 `_read_version` 读此文件）、SHA256SUMS（重算）；
wxgzh-pipeline 4：SKILL.md、VERSION（hotfix9R23）、audit/quality/SECURITY.md（新增七节）、audit/quality/obs-ledger.md（OBS-345/346/347/348 + 口径 84）；
gzh-title-review 1：SKILL.md（无 VERSION 文件不升版）。

## 3. 测试证据（第一轮实测）

- sw：`pytest tests/ -q` → 289 passed / 2 skipped / 1 failed（唯一失败=test_dist_lite_exists_and_under_2000_hanzi，既存 dist 环境红，在册）；新增 2 条全绿；VERSION test_count=292 实测。
- zh：`tests/run_tests.py` → 92/92；`verify_release.py` → 全 PASS（VERSION=0.1.12、SHA256SUMS 64 files verified）。
- gzh：`pytest -q` → 249 passed / 21 skipped，零新红。

## 4. relock 记录（#93–#96，doctor_result 全 PASS）

| # | skill | entry_id | old_root | new_root | 落锁 version |
|---|---|---|---|---|---|
| 93 | super-writer | relock-super-writer-20260901T154532Z-1ee31123 | 7131318716bc… | 957e616c53b6… | 0.4.17-rc1 |
| 94 | zh-human-writing | relock-zh-human-writing-20260901T154609Z-bc1b996a | 5d6365da3ae6… | 405de4dcc75b… | 0.1.12 |
| 95 | media-enrichment | relock-media-enrichment-20260901T154640Z-964ac023 | cc43771c4cfa… | 618c0ccdbc6b… | 0.1.0-dev28 |
| 96 | gzh-design | relock-gzh-design-20260901T154728Z-3e4dadd3 | a7e33a7c7c3f… | f19e6595b69d… | v2026.09.01-hammer.20 |

- 锁备份 ×4：audit/upgrade-capability/lock-backups/skills.lock.20260901T154532Z / 154609Z / 154640Z / 154728Z.json。
- pipeline / gzh-title-review 无锁条目：pipeline 仅升版 hotfix9R22→hotfix9R23；title-review 无 VERSION 文件不升版。

## 5. 锁 sha 与 R93

- 旧：fb7b845f2f0f34a51a6b9bb70b45f985dfb0355cc9371104820d8e48f85e4462
- 新：09e13ccb4be334481014a2a3b86ef0a2018e7c53bbd4e7eacc1c75e04fdbb9fd
- REPO_LOCK_SHA256 双侧一致（源码侧与装机侧 observability.py 均=新锁 sha）。

## 6. doctor 与回归

- 源码侧 doctor --require-wechat：PASS（FAIL_CLOSED=False，OBS_68 repo=installed=778、diff 0）。
- 装机侧 doctor：PASS（OBS_69_LOCK_MATCH MATCH，baseline=installed=09e13ccb…；OBS_68 MATCH）。
- upgrade_regression：唯一红=test_obs154_anchors_json_renderer_sha_matches_installed（obs154 既有红，在册，未授权不顺手修）；relock dry-run ×4 全部「无变化 OK」。
- test_obs304_ledger_count_command 随档更新：226→230、119..344→119..348（77Q/77R 起该测试既定随档更新模式，注释在册）。

## 7. 复扫预期（供任何 agent 下次扫描解释）

- 应清零：AST7×1、RP1×4、MP2×7、LP3×1。
- 预期残留（噪声基线，依据同目录 SECURITY.md）：AST4×31（全 tests/，正当测试夹具）、EA3×1（LICENSE 正文误报）。
- 预期评级：LOW/CAUTION 以下；最终以灵犀复扫报告实证（复扫由用户侧执行）。

## 8. 装机侧同步（实测核验）

- 装机侧 skills.lock.json sha=09e13ccb…（与源码侧一致）；observability.py R93 一致；super-writer/wxgzh-pipeline SKILL.md 权限声明、SECURITY.md、本报告均已同步装机侧；装机侧 doctor PASS 为最终凭据。
