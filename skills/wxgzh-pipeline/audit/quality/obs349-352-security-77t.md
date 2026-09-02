# OBS-349/350/351/352 —— 77T 灵犀复扫第二轮合规验收报告（字节级落盘）

- 档号：77T（灵犀复扫第二轮。第一轮=内容修复 34 文件，feat 377620d 已推送；第二轮=锁链与验收，本报告）。
- 授权：RELOCK 沿用 77S=1（批准人=用户）；GZH_DESIGN_WRITE_ALLOWED 本档 0→1，范围=P2 两行注释（theme-hammer.md:158、theme-zen-whitespace.md:446 注释改写，已随一轮落库）。
- 来源报告：灵犀第二轮复扫 5 技能 633 项（2026-09-02，逐条定性=第一轮完成）。
- 基线链：377620d（一轮 feat，已推送）→ 53c8f7a（二轮：media dev29 全站同步 + obs304 随档，11 文件，已推送）→ 本轮 docs 锁链提交（observability.py R93 一行 + skills.lock.json + history +4 + 锁备份×4 + 本报告，待主智能体收）。

## 1. 第二轮复扫 633 项定性汇总（真修 / 设计使然 / 噪声基线分列）

**真修 3 类：**

| 类别 | 位置 | 处置（OBS 台账） |
|---|---|---|
| CVE 依赖收紧 | media-enrichment requirements.txt | requests>=2.32.4,<4（CVE-2024-35195 / CVE-2024-47081）、Pillow>=10.3,<13（CVE-2023-50447 ARCE / CVE-2023-44271 / CVE-2024-28219）；本机实测 requests 2.34.2 / Pillow 12.2.0 均达标（OBS-349） |
| AST5 os.system ×2 | gzh-design scripts/screenshot_hammer_upgrade.py | 两处 os.system 改列表式 subprocess.run([sys.executable,…], check=False)，try/except ImportError 上下文不动，py_compile 过（OBS-350） |
| LP3 声明格式不被扫描器识别 | 六份 SKILL.md（sw/zh/media/gzh/pipeline/title-review） | frontmatter 加机器可读 `permissions:` 块×6，正文「权限与范围声明」节保留（OBS-351） |

**设计使然声明 1 类**（SECURITY.md ⑧「第 2 轮复扫基线（77T）」节，配四处夹具头注 + 守卫/防御钉子）：

- **TT3 六端点（=6 项）= 凭据仅流向 api.weixin.qq.com，零第三方**：六端点常量全部位于
  `gzh-design/scripts/publish_wechat_draft.py:120-125`——TOKEN_URL（/cgi-bin/token）、ADD_DRAFT_URL（/cgi-bin/draft/add）、BATCHGET_DRAFT_URL（/cgi-bin/draft/batchget）、GET_DRAFT_URL（/cgi-bin/draft/get）、UPLOAD_MATERIAL_URL（/cgi-bin/material/add_material）、UPLOADIMG_URL（/cgi-bin/media/uploadimg）；E2/PE3 同性质（凭据仅用于微信 API 所需）。
- **SSRF1 ×12 = 守卫实现本体误报**：`media-enrichment/src/media_enrichment/url_security.py` 的 BLOCKED_RANGES 常量表 + `media-enrichment/fixtures/html/malicious-ssrf.html` 测试样本（页面里的恶意 URL 是断言对象，非运行时内容）。守卫能力清单：黑名单段族（0.0.0.0/8、10/8、100.64/10 CGN、127/8、169.254/16 含云元数据 169.254.169.254、172.16/12、192.168/16、224/4 组播、240/4、::1、fc00::/7、fe80::/10、ff00::/8、2001:db8::/32 等）/ 每跳重定向复检 / DNS 解析后复检（含 IPv4-mapped IPv6 还原）/ scheme 白名单（仅 http/https）/ 下载尺寸上限；回归钉子 `tests/test_hf77t_url_security_guard.py`（77T 新增）。
- **YR1 夹具定性 = 渲染器逐字输出正例夹具**：`gzh-design/tests/test_intro_paras_and_code_block.py:115` 的 `rm -rf /tmp/x`、`git push --force origin main` 字符串是断言预期输出（验证渲染器逐字保留恶意字符串）；media `tests/fixtures/obs71/`（media_discovery_request.obs71.json、final_article.obs71.md）同理——`rm -rf` 等是文章正文样本内容，非运行命令。夹具头注四处：gzh-design test_intro_paras_and_code_block.py、media malicious-ssrf.html、zh examples/03-technical/input.txt、zh examples/samples/C-technical/input.md。
- **RA1 = 路径 dirname 链误判**（扫描器噪声）；**MP2 = 多行续行误判形态**（沿 77S 基线③）。
- **EA2 ×56 = auto_approve 决策链设计使然**，决策边界表（media SKILL.md「自动决策边界」节）：

  | 边界 | 规则 |
  |---|---|
  | 自动批 | 零图降级；auto_approve 开启（WXGZH_MEDIA_AUTO_APPROVE=1，默认关）且单图证据链齐全（76R/OBS-289 口径） |
  | 必须人工 | 图片审批（默认道）、restricted 资产、上传微信前终审 |
  | 逐条对应 | `scripts/run_media_enrichment.py` 决策点 ×56 |

- **audit/ 目录命中 = 历史运行记录牵连**：命中项均为历史运行的审计产物记录，非运行时行为；audit/ 是否剥离发行版留待后续裁决，本档不动。
- **OH1 = run_tests.py 列表参数无 shell**：zh-human-writing `tests/run_tests.py` 的 `run_script` 以 `cmd = [PYTHON, script] + args` 列表式调用 subprocess、无 shell=True；防御测试 `tests/test_hf77t_run_script_safety.py` 钉住（77T 新增）。

**噪声基线**：照同目录 SECURITY.md ⑧ 与 77S ②-④ 节（AST4×31 全 tests/ 正当测试夹具、EA3×1 LICENSE MIT 正文误报）。

## 2. media 升版脱节补齐（77S / 77T 一轮漏跑 → 77T 二轮按 77J 模式补齐）

- git 实证 ec9f97f（77J 升 dev27）的既定升版模式 = VERSION + 8 源文件 + 2 钉子测试 + CHANGELOG 全站同步。
- 77S 升 dev28 时漏跑该套（只动 VERSION/CHANGELOG/SKILL.md）；77T 一轮升 dev29 延续遗漏 → media 全套 2 failed（test_all_versions_dev7_hotfix1 / test_version_files_consistent，基线同红，一轮误诊为「版本钉子红」）。
- 77T 二轮实测根因：VERSION 已 0.1.0-dev29，而 STRICT_FILES 中 6 个源文件残留 dev27（src/media_enrichment/__init__.py、src/media_enrichment/input_contract.py、README.md、scripts/build_zip.py、scripts/generate_evidence.py、src/media_enrichment/url_security.py）。
- 按裁决（主智能体 2026-09-02）补齐 0.1.0-dev27→0.1.0-dev29 共 10 文件（上列 6 源文件 + WXGZH_PIPELINE_INTEGRATION.md + scripts/_verify_dev7.py 两处残留 + 2 钉子测试），仅版本字面量；CHANGELOG 不动（77T 条目一轮已落）。
- 补齐后 media 全套 349 passed / 7 skipped / 0 failed；残留 grep 仅 CHANGELOG.md:13（77J 历史条目，设计豁免）。

## 3. 修复文件清单

**第一轮 feat 377620d（34 文件）：**

- media-enrichment 6：requirements.txt（CVE 收紧，OBS-349）、SKILL.md（permissions frontmatter）、VERSION（0.1.0-dev29）、CHANGELOG.md（dev29 条目）、fixtures/html/malicious-ssrf.html（SSRF 样本头注）、tests/test_hf77t_url_security_guard.py（新增守卫回归钉子）。
- gzh-design 10：scripts/screenshot_hammer_upgrade.py（AST5×2）、SKILL.md（permissions frontmatter + 凭据声明补端点白名单）、README.en.md（RP1 npx skills@1.5.23 锁版×2）、common-components.md:43（RP1）、tests/hammer-all-components-showcase.html（RP1×2）、theme-hammer.md:158（P2 注释改写）、theme-zen-whitespace.md:446（P2 注释改写）、tests/test_intro_paras_and_code_block.py（YR1 头注）、RELEASE_NOTES.md（hammer.21）、SHA256SUMS（重算）。
- super-writer 4：SKILL.md（permissions frontmatter）、VERSION（0.4.18-rc1）、CHANGELOG.md、MANIFEST.sha256（重算）。
- zh-human-writing 8：SKILL.md（permissions frontmatter）、VERSION（0.1.13）、RELEASE_NOTES.md、SHA256SUMS（重算）、verify_release.py（VERSION_EXPECTED 0.1.12→0.1.13）、tests/test_hf77t_run_script_safety.py（新增 OH1 防御钉子）、examples/03-technical/input.txt + examples/samples/C-technical/input.md（夹具头注）。
- wxgzh-pipeline 5：SKILL.md（permissions frontmatter）、VERSION（hotfix9R24）、audit/quality/SECURITY.md（⑧ 第 2 轮基线节）、audit/quality/obs-ledger.md（OBS-349~352 + 口径 85）、tests/test_hf76r.py（头注版）。
- gzh-title-review 1：SKILL.md（permissions frontmatter，无 VERSION 文件不升版）。

**第二轮 53c8f7a（11 文件）：** media-enrichment 10（上节 8 个版本字面量文件 + tests/test_runner_integration.py:184、tests/test_uploader_manifest.py:214 两行钉子）+ wxgzh-pipeline tests/test_hf76r.py（obs304 计数钉子 230→234、119..348→119..352、77T 注释追加）。

**本轮 docs 锁链（待提交）：** wxgzh_pipeline/observability.py（R93 一行）、skills.lock.json、skills.lock.history.json（+4）、锁备份×4、本报告（源码侧+装机侧同路径）。

## 4. 测试实测

- media：`pytest -q` → **349 passed / 7 skipped / 0 failed**（含 2 行钉子更新后原 2 红转绿；SSRF 守卫新增 3 用例绿）。
- pipeline：`pytest tests/test_hf76r.py` → **19 passed**（obs304 唯一编号实测 234、119..352 连续无缺号）。
- zh（一轮实测）：`tests/run_tests.py` → 92/92；新增 OH1 守卫 1 绿；`verify_release.py` 全 PASS。
- gzh（一轮实测）：`pytest -q` → 249 passed / 21 skipped，零新红。
- sw（一轮实测）：`pytest tests/ -q` → 289 passed / 2 skipped / 1 failed（唯一失败=test_dist_lite_exists_and_under_2000_hanzi，既存 dist 环境红，在册）。

## 5. relock 记录（#97–#100，doctor gate / post 全 PASS，entrypoint smoke 全 PASS）

| # | skill | entry_id | old_root | new_root | 落锁 version |
|---|---|---|---|---|---|
| 97 | super-writer | relock-super-writer-20260902T083558Z-11bce29f | 957e616c53b6… | 9e7adb23c99c… | 0.4.17-rc1 → 0.4.18-rc1 |
| 98 | zh-human-writing | relock-zh-human-writing-20260902T083620Z-b9b6685c | 405de4dcc75b… | a33053ee6320… | 0.1.12 → 0.1.13 |
| 99 | media-enrichment | relock-media-enrichment-20260902T083646Z-da149d7e | 618c0ccdbc6b… | 53d5b42b0d9b… | 0.1.0-dev28 → 0.1.0-dev29 |
| 100 | gzh-design | relock-gzh-design-20260902T083722Z-9b0fd8d7 | f19e6595b69d… | 990c51c49b4e… | v2026.09.01-hammer.20 → v2026.09.02-hammer.21 |

- 四条 full_commit_sha 均 = 53c8f7a0cb882e8d50f8e7a224caa31e27c9b306；远端见证 (a/b/c) 全 PASS。
- source_tree_sha：sw 1829575a…、zh 33fda216…、media 2d6fc368…、gzh 30bffb71…。
- 锁备份 ×4：audit/upgrade-capability/lock-backups/skills.lock.20260902T083558Z / 083620Z / 083646Z / 083722Z.json。
- 编号口径：承 77S 报告 #93–#96 续计（与简报预测 #97–#100 一致）；skills.lock.history.json 现存 97 条记录，本轮 4 条即上表 entry_id。

## 6. 锁 sha 与 R93

- 旧：09e13ccb4be334481014a2a3b86ef0a2018e7c53bbd4e7eacc1c75e04fdbb9fd（77S 落）
- 新：ed3286548220a3a7bca718ccc1891cfd05dff3c69524433216c535277469126b
- R93 双侧：源码侧与装机侧 observability.py 的 REPO_LOCK_SHA256 均一行更新为新 sha（沿 77S 实证口径：只改 sha 行、不追加基线注释行），实测两侧一致。

## 7. doctor 与回归

- 源码侧 doctor（--repo-root=源码侧 pipeline 目录）：PASS、FAIL_CLOSED=False；OBS_69_LOCK_MATCH MATCH（baseline=installed=ed328654…）；OBS_68_PIPELINE_MATCH MATCH（repo=installed=782，diff/missing/extra 全 0）。
- 装机侧 doctor（同命令形态）：PASS、OBS_69 MATCH、OBS_68 MATCH（782/782 全 0）。
- upgrade_regression：pytest FAIL(1 explicit deselects)=唯一 FAILED test_obs154_anchors_json_renderer_sha_matches_installed（obs154 既有红，在册，未授权不顺手修）；relock dry-run ×4 全部「无变化 OK」；doctor --require-wechat PASS；validate_gzh_html cross-side SKIP（P2 未落地，防漂移守卫将在 P2 落地后自动生效）。

## 8. 装机同步（实测核验）

- install.py 标准调用（--project-root F:\AIXM\wxgzh --skills-src F:\AIXM\wxgzh-skills）：ok=true；5 技能 installed=true；4 锁技能 commit/source_tree/repository/runtime_root/runtime_manifest 全 match，receipt 落盘 .install-receipts/，hash_verification 全 true；pipeline_release_include ci.yml sha=751294ac…。
- 无锁文件：pipeline SKILL.md / VERSION / audit/quality/obs-ledger.md / tests/test_hf76r.py / audit/quality/SECURITY.md 双侧实测 SAME（install.py 覆盖）；gzh-title-review/SKILL.md install.py 不覆盖（无锁条目技能），手动 cp 同步（补齐 77T 一轮 permissions frontmatter）。
- 本报告落盘后同步装机侧同路径 audit/quality/obs349-352-security-77t.md。
- 装机侧 doctor PASS 为最终凭据。

## 9. 第三轮复扫预期（供任何 agent 下次扫描解释）

- 应清零（CRITICAL/HIGH）：CVE（requests/Pillow 下限已收紧）、AST5（os.system 已除）；LP3 frontmatter `permissions:` 块扫描器识别情况第 3 轮实证（正文节+frontmatter 双通道已布）。
- 预期残留按本目录 SECURITY.md ⑧（TT3/SSRF1/YR1/RA1/MP2/EA2/audit 牵连/OH1 定性）与 77S ②-④（AST4×31、EA3×1）解释。
- 最终以灵犀第三轮复扫报告实证（复扫由用户侧执行）。
