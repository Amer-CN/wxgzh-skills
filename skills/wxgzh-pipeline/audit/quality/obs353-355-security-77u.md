# OBS-353/354/355 —— 77U 灵犀复扫第三轮合规验收报告（锁链与验收）

- 档号：77U（灵犀复扫第三轮。第一轮=内容修复 25 文件 + obs304 随档（feat 5bc3944 已推送，主智能体执行）；第二轮=锁链与验收，本报告）。
- 授权：RELOCK / GZH_DESIGN_WRITE_ALLOWED 持续 1（批准人=用户，沿用未动、未新开未归位）。
- 来源报告：灵犀第三轮复扫（2026-09-02）+ 任务 0 四项对质（结论落 SECURITY.md ⑨）。
- 基线链：5bc3944（一轮 feat 26 文件，已推送，remote main 一致）→ 本轮锁链改动（observability.py R93 一行 + skills.lock.json + history +3 + 锁备份×3 + 本报告，留工作区——本档禁 git 写操作，由主智能体收口提交）。

## 1. 任务 0：四项对质结论（第 3 轮复扫报告 vs 仓库事实，细节见 SECURITY.md ⑨）

1. **CVE 读取面 + gzh 补线**：仓库三份依赖声明清单逐份实测——media requirements.txt（77T 已达线，灵犀 clone 同内容原文）、gzh requirements.txt requests>=2.32.4,<3（77U 一轮补齐 77T 漏项，原 >=2.31）、wxgzh-pipeline/requirements.lock 钉 requests==2.32.3（锁链禁触，如实登记留用户裁决）；本机实测 requests 2.34.2 / Pillow 12.2.0 均在线上。扫描器判「未修复」=判定读取面（缓存/未重算），仓库事实如上。
2. **exec 误述证据**：全仓 grep `exec(` 仅 `wxgzh-pipeline/tests/test_hf76r.py:6`（docstring 自述）与 `:83`（测试解析自身源码片段）两处；编排器 `wxgzh_pipeline/` 包零命中；sw/gzh/media scripts 零命中。第 3 轮报告「编排器内 exec()」系综述误述（灵犀 clone 复核一致）。
3. **TM1 自指清洗**：zh test_hf77t_run_script_safety.py 危险字面量改分段构造 + docstring 卫生注记，pattern 消失，测试语义零变化（1 passed 与改前同数）。
4. **P2/LP3/YR1 pattern 判定面**：P2 两行（theme-hammer.md:158、theme-zen-whitespace.md:446）03a8310 已英文中性且本档 git diff 零漂移、第 3 轮报告行号未漂移=未重扫证据；LP3 六份 SKILL.md frontmatter `permissions:` 本档逐份 grep 全在（报告报缺=字段名不匹配，第 4 轮复扫实测）；YR1 gzh 两测试文件（test_intro_paras_and_code_block.py、test_render_article_cli.py）改模块级常量 `_RM`/`_GP`/`_DENY_RM` 分段构造，夹具与断言引同一常量，渲染输出逐字不变，16 passed 与改前同数。

## 2. 修复文件清单

**第一轮 feat 5bc3944（26 文件 = 25 内容修复 + obs304 随档）：**

- zh-human-writing 5：VERSION（0.1.13→0.1.14）、RELEASE_NOTES.md、SHA256SUMS（重算 4 行）、verify_release.py（VERSION_EXPECTED 0.1.13→0.1.14）、tests/test_hf77t_run_script_safety.py（TM1 分段构造清洗）。
- media-enrichment 13：VERSION（0.1.0-dev29→dev30）+ CHANGELOG/README/WXGZH_PIPELINE_INTEGRATION.md/scripts/_verify_dev7.py/build_zip.py/generate_evidence.py/src __init__.py/input_contract.py/url_security.py（77J 全站同步口径）、tests/test_hf77t_url_security_guard.py（mapped-IPv6 URL/元数据分段清洗）、tests/test_runner_integration.py + test_uploader_manifest.py（dev30 版本字面量钉子同步）。
- gzh-design 4：RELEASE_NOTES.md（hammer.22）、requirements.txt（requests 下限补线）、tests/test_intro_paras_and_code_block.py + test_render_article_cli.py（YR1/TM1 常量分段构造）。
- wxgzh-pipeline 4：VERSION（hotfix9R24→9R25）、audit/quality/SECURITY.md（⑨ 第 3 轮对质基线 + ⑤ 卫生新规立规）、audit/quality/obs-ledger.md（口径 86，OBS-353/354/355 落账）、tests/test_hf76r.py（obs304 计数 234→237、119..352→119..355，随档）。

**第二轮锁链（本轮，工作区未提交）：** wxgzh_pipeline/observability.py（R93 一行）、skills.lock.json、skills.lock.history.json（97→100 条）、锁备份×3、本报告（源码侧+装机侧同路径）。

## 3. 测试实测

- 第一轮（主智能体取证）：zh `tests/run_tests.py` 92/92 + TM1 钉子 pytest 1 passed（防御 1 绿）+ `verify_release.py` 全 PASS（65 files）；media 全套 `pytest -q` **349 passed / 7 skipped / 0 failed**（dev30 全站一致）+ SSRF 守卫 3 绿；gzh `pytest -q` **249 passed / 0 failed**（与 77T 同数）+ 两清洗文件 16 passed（与改前同数）；pipeline `test_hf76r.py` 19 passed（obs304 唯一编号实测 237、119..355 连续无缺号）。sw 触及=0 不升。
- 第二轮（本档实测）：relock dry-run ×3 远端见证 (a/b/c) PASS、apply ×3 doctor gate PASS（pre-write）/ installer PASS（source-tree install）/ doctor PASS（post-relock）/ entrypoint smoke PASS（CLI subprocess，production path）×3。

## 4. relock 记录（#101–#103）

| # | skill | entry_id | old_root | new_root | 落锁 version |
|---|---|---|---|---|---|
| 101 | zh-human-writing | relock-zh-human-writing-20260902T110659Z-bcf345c0 | a33053ee6320… | aeb395028990… | 0.1.13 → 0.1.14 |
| 102 | media-enrichment | relock-media-enrichment-20260902T110747Z-1baeb6b6 | 53d5b42b0d9b… | e9d57c01f652… | 0.1.0-dev29 → 0.1.0-dev30 |
| 103 | gzh-design | relock-gzh-design-20260902T110854Z-aa0e8f65 | 990c51c49b4e… | 0c3a520c5495… | v2026.09.02-hammer.21 → v2026.09.02-hammer.22 |

- 三条 full_commit_sha 均 = 5bc3944e0c5150ea8c9438026957e271a5b86948；远端见证 (a/b/c) 全 PASS。
- source_tree_sha：zh 43ec7723…、media 05048505…、gzh 9dc2d3ad…。branch 均 main。
- 锁备份 ×3：audit/upgrade-capability/lock-backups/skills.lock.20260902T110659Z / 110747Z / 110854Z.json。
- 编号口径：承 77T 报告 #97–#100 续计（skills.lock.history.json 现存 100 条记录，本轮 3 条即上表 entry_id；条数与编号既有偏移在册）。
- sw 未触及不升不 relock（本档既定）；pipeline 不在锁表只升版本（9R25）。

## 5. 锁 sha 与 R93

- 旧：ed3286548220a3a7bca718ccc1891cfd05dff3c69524433216c535277469126b（77T 落）
- 新：217a5c377f425a4de4b2bfb911f2a851745baf7e8b430714e8c46754be5dd162
- R93 双侧：沿 77S/77T 实证口径只改 sha 行、不追加基线注释行；源码侧与装机侧 observability.py `cmp` 逐字一致，REPO_LOCK_SHA256 均 = 新 sha。

## 6. doctor 与回归

- 源码侧 doctor（--repo-root=源码侧 pipeline 目录 --require-wechat）：**PASS**、FAIL_CLOSED=False；OBS_69_LOCK_MATCH **MATCH**（baseline=installed=217a5c37…）；OBS_68_PIPELINE_MATCH **MATCH**（785/785，diff/missing/extra 全 0）。
- 装机侧 doctor（同命令形态 + --skills-home/--lock-path 装机侧）：**PASS**、OBS_69 **MATCH**（217a5c37…）、OBS_68 **MATCH**（785/785 全 0）。
- upgrade_regression：**FAIL (1 explicit deselects)** —— 唯一 FAILED `test_obs154_anchors_json_renderer_sha_matches_installed`（obs154 既有红，在册，未授权不顺手修）；同轮 relock dry-run ×4 全部「无变化 OK」（锁已稳）、doctor --require-wechat PASS、validate_gzh_html cross-side SKIP（P2 未落地，防漂移守卫将在 P2 落地后自动生效）。obs304 已随档绿（237）。

## 7. 装机同步（实测核验）

- relock apply 内建 official installer（source-tree bundle）×3 逐次落装机侧：zh/media/gzh 新树 + pipeline release 树 + 新锁（装机侧 skills.lock.json 实测 217a5c37… 与源码侧一致）；R93 一行随后 cp 同步装机侧。
- **install.py 标准调用（--project-root F:\AIXM\wxgzh --skills-src F:\AIXM\wxgzh-skills）FAIL_CLOSED，ok=false，零写入**：super-writer 锁条目 full_commit_sha=53c8f7a0（77T 落）≠ 本仓 HEAD 5bc3944e（本档 sw 不 relock），source proof commit_match=false → `super-writer: source proof does not match skills.lock`，整计划中止。该模式的结构性前提是「全部锁技能在当前 HEAD relock」，与本档「sw 不 relock」互斥；同步改由 relock 内建 installer 达成，以双侧 OBS_68 MATCH 为最终凭据。skills-src 模式安装何时可用留待用户裁决（全锁技能同 HEAD relock 或 sw 升版档）。
- 无锁文件核验（diff -rq 全量对照）：五锁技能 + pipeline 双侧仅 .github / .gitattributes 差异（发行排除项）；gzh-title-review/SKILL.md 双侧 SAME（references/tests 不入发行，设计使然）；pipeline SKILL.md / VERSION / SECURITY.md / obs-ledger.md / tests/test_hf76r.py 双侧 SAME。
- 本报告落盘后 cp 装机侧同路径 audit/quality/obs353-355-security-77u.md。
- 装机侧 doctor PASS 为最终凭据。

## 8. 卫生新规立规说明

SECURITY.md ⑨⑤ 立规：**测试文件禁含危险字面量**（payload / 内网 URL / 特征字节一律编码或数据文件化）。同类第二发生（SSRF 夹具 77T、TM1 payload 77U）入档根治；zh/media/gzh 本轮清洗即按此规执行，77T 夹具头注（定性注释）与本规并行有效。

## 9. 第四轮复扫预期（供任何 agent 下次扫描解释，仅参照）

- 应清零：TM1/YR1 危险字面量 pattern（清洗后实测消失）、gzh CVE 读取面（requirements 已达线）。
- 预期残留按 SECURITY.md ⑧⑨ 与 77S ②-④ 解释：TT3 六端点（凭据仅流向 api.weixin.qq.com）、SSRF1 ×12（守卫实现本体+测试样本）、RA1 路径 dirname 链误判、MP2 多行续行、EA2 ×56 auto_approve 决策链、AST4×31 tests/ 夹具、EA3×1 LICENSE 正文误报、audit/ 历史运行记录牵连、OH1 run_tests.py 列表参数无 shell；P2 两行（03a8310 已中性，若报告行号仍与 77T 相同即未重扫证据）；LP3 六份 frontmatter `permissions:` 全在（第 3 轮字段名不匹配，第 4 轮实测字段名）；wxgzh-pipeline/requirements.lock requests==2.32.3 如实登记留用户裁决。
- 最终以灵犀第四轮复扫报告实证（复扫由用户侧执行）。
