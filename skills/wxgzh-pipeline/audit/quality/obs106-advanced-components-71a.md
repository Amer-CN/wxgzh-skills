# OBS-106：高级组件协议接线可行性取证（档 71A + 71A′ 合并报告）

- 日期：2026-08-05
- 范围：纯只读取证（+ 报告写入）；未改任何生产文件 / RUN 产物；未 relock / bundle / 安装器 / 微信 / RUN
- 本报告容纳档 71A 与 71A′ 全部实测数据

---

## 1. 安装侧一致性（71A 第 1 步）

- doctor `--require-wechat`：**PASS**；四锁 hash_ok 全 true（super-writer `46a00a1b` / zh-human-writing `18491b36` / media-enrichment `181752eb` / gzh-design `0dd8d317`）
- OBS_68（71A 时）：**648/649 DIFF**，缺 `audit/quality/obs99-cover-path-70.md`（归因见第 5 步）
- skills.lock.json 双侧 sha：`0CD0EBC35CF516BD0BD74DA515C74D50F929948F1D0E1FDD772D80D56C6B1CF9`（与预期一致）

## 2. manifest 归属重核（71A′ 第 1 步，指定代码逐字执行）

原始输出（节选关键行，76 项完整清单见附录 A）：

```
COUNT 76
ROOT_SHA 0dd8d31756318773e8e927fde6735a97e5dd64fb0fe59228b8913f2fcf574300 76
MANIFEST_SHA ced841439195453497e67a63186823f60eee7155b9de472e936c3d4d767e33b2 76
MEMBER references/advanced-components.md True
MEMBER scripts/generate_advanced_html.py True
MEMBER scripts/lint_advanced_components.py True
MEMBER scripts/render_article.py True
MEMBER scripts/validate_gzh_html.py True
ADV_DIR_COUNT 18
TESTS_COUNT 0
REFERENCES_TOTAL 31
SCRIPTS_TOTAL 25
```

- b. 与 lock 比对：ROOT_SHA == skill_root_sha256 **True**；MANIFEST_SHA == runtime_manifest_sha256 **True**；COUNT == runtime_file_count(76) **True**
- c. **71A 第 2 步为何两次结论相反（机制说明）**：71A 当时代码是
  `posix = str(f).replace("\\", "/")` 后与 `"references/advanced-components.md"` 比较——
  `_runtime_files()` 返回**绝对路径**，`str(f)` 得到 `F:/AIXM/wxgzh/.agents/skills/gzh-design/references/advanced-components.md`，
  与相对路径字面比较恒 False。71A′ 用 `p.relative_to(root).as_posix()` 得到相对路径后比较 → True。
  这是**取证代码 bug（绝对/相对路径比较错误）**，不是 manifest 内容变化；审核者依源码判定 71A 第 2 步结论不成立，正确。
- d. **结论句式**：那 21 个文件（`references/advanced-components.md` + `references/advanced/` 18 个 +
  `scripts/generate_advanced_html.py` + `scripts/lint_advanced_components.py`）**在** gzh-design 的
  runtime_manifest 内，依据 = `SD._runtime_files(root)` 相对路径逐项成员判定 + ROOT/MANIFEST/COUNT 三比对全 True。

## 3. 入口零解析举证（71A 第 3 步，已裁决放行）

- a. `:::` = 0；b. `advanced` = 1；c. `generate_advanced_html` = 1；d. `[^` = 0
- b/c 命中同一行 L4 docstring：`Unlike generate_advanced_html.py / generate_hammer_upgrade_samples.py (which emit FIXED acceptance samples), this is a real article renderer…`——纯注释，非解析/调用
- e. import 清单：`from __future__` / argparse / json / os / re / sys / pathlib / `import generate_hammer_upgrade_samples as H` / `from validate_gzh_html import validate`——无任何 advanced 相关 import
- 结论：入口零解析零调用（71A′ 裁决放行，取证意图达成）

## 4. builder 可调用性（71A 第 4 步，隔离目录 `.temp\obs106-check\`）

- `generate_advanced_html.py`：exit 0，生成 **63 份 HTML**（9 组件 × 7 主题）→ `tests\advanced-components\expected\`
- 9 份 hammer 全齐：alert 660 / code-compare 1173 / dialogue 1445 / footnotes 585 / gallery 1302 / long-image 415 / media-text 641 / quote 297 / resources 891 字节
- 特征扫描（9 份逐份）：`class=`/`id=`/`<div`/`white-space:pre`/`position:`/`display:grid`/`@media`/`var(--` 全 **0**；`<span leaf="">` 各 2–7 处；`#B3593B` 0–2 处（主题色正当用途）
- `validate_gzh_html.py` 9/9：exit 0，全部「完全合规」（0 ERROR 0 WARNING）
- `lint_advanced_components.py .`：exit 0，18/18 干净，ERROR×0 WARN×0

## 5. THEME_IDENTITY 指纹碰撞实测（71A′ 第 2 步，增量差分）

### 5a. 9×7 fingerprint 计数表

| component | cover_brea | toc_scroll | chapter_ti | signature | footer_cta | image_2a_s | image_medi |
|---|---|---|---|---|---|---|---|
| alert | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| code-compare | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| dialogue | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| footnotes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| gallery | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| long-image | 0 | 0 | 0 | 0 | 0 | 0 | **1** |
| media-text | 0 | 0 | 0 | 0 | 0 | 0 | **1** |
| quote | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| resources | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

### 5b. `image_media_text_card` 指纹碰撞

- 指纹原文 `"0 4px 16px -4px rgba(179,89,59,0.10)"` 命中 **long-image-hammer.html（1 次）** 与 **media-text-hammer.html（1 次）**
- 即：高级组件 media-text / long-image 的卡片容器与官方 image_media_text_card 共享同一 box-shadow 令牌 → **指纹碰撞实锤**

### 5c. 增量差分（基线 = 当前 RUN final.html 只读副本，expected_chapters=4）

- 基线：cover=1 / toc=1 / chapter=4 / signature=1 / footer=1 / image_types=2 / structure_ok=True
- 追加 alert / quote / media-text / gallery 四个组件后：**全部 8 个结构键 Δ = 0**（无任何键变化）

### 5d. 极端样本（零真实正文图）

- 构造：基线删除全部 `<img>` section（0 img、0 指纹）后追加一个 media-text 组件：
  - `OFFICIAL_IMAGE_COMPONENT_TYPES = 1`、`image_types_present = ['image_media_text_card']`、`structure_ok = False`
- **结论：出现「无真实图片却满足图片组件类型计数」的假满足**——组件指纹被计入图片门禁；当前 structure_ok 仍 False 只因类型数 1 < 2，若未来 2a 也共享令牌，门禁可被凑满（71C 必修项 d 的实证依据）
- 对照组（无 media-text）：image_types=0、structure_ok=False

### 5e. `chapter_title` 指纹

- `"font-size:28px;font-weight:900;color:"` 在 9 份组件中 **0 命中**（无碰撞）

## 6. 导语内容保真守卫（71A′ 第 3 步）

### 6a. 定位

- 实现在 **`wxgzh_pipeline/stages/gzh_design.py` L131**（`_intro_content_fidelity`），挂在 gzh_design 阶段 content_validate（L49-56），FAIL → `INTRO_GUARD=FAIL` 阻断
- 不在 validate_theme_identity.py 内（与审核者判断一致）

### 6b. 认可形态（_body_plain_text 匹配）

- `_PARA_RE`：`<p style="margin-bottom:16px;font-size:14px;line-height:1.9;text-align:justify;[^"]*">(.*?)</p>`（hammer_para 段落）
- `_PRE_RE`：`<pre[^>]*>(.*?)</pre>`（代码块）
- 匹配后去标签 + `html.unescape` + 空白归一化，逐段全文包含判定

### 6c. 反事实（:::alert 渲染导语）

- 构造：导语首段渲染为 alert 组件（`<p style="margin:0 0 6px;">` 形态）→ `_intro_content_fidelity` 返回 **ok=False**，missing_text=导语全文
- 对照组 hammer_para 渲染 → ok=True
- **结论：若导语首段改由高级组件渲染，守卫必然 FAIL → 71C 必修项**

## 7. writing_contract 门禁（71A′ 第 4 步，本档最关键）

### 7a. 真实触发证据

- 注入 items：`aihot/items_file.injected.json`（4 条素材，deny/ask 提取来源）
- super_writer stage_result.json：`OBS88_CODEBLOCK: PASS`（validator_report），`SUPER_WRITER: PASS`，FULL_MODE_VALIDATOR_EXIT 0
- `extract_deny_ask_lines` 实测：deny_ask_total = **16**（MIN_DENY_ASK_COVERAGE = 10）

### 7b. 现状复现（validate_codeblock_fidelity(final_article.md, items.json)）

```json
{"deny_ask_total": 16, "covered_in_codeblocks": 16, "min_coverage": 10,
 "deny_prefix_present": true, "ask_prefix_present": true,
 "missing_lines": [], "OBS88_CODEBLOCK": "PASS"}
ok: True
```

### 7c. ★反事实（副本：```bash 围栏 → :::alert 围栏，16 行内容逐字不动）

```json
{"deny_ask_total": 16, "covered_in_codeblocks": 0, "min_coverage": 10,
 "deny_prefix_present": false, "ask_prefix_present": false,
 "missing_lines": [全部 16 条], "OBS88_CODEBLOCK": "FAIL"}
ok: False
```

### 7d. 对照（副本：bash → text 语言标签，载体仍是代码围栏）

```json
{"deny_ask_total": 16, "covered_in_codeblocks": 16, "min_coverage": 10,
 "deny_prefix_present": true, "ask_prefix_present": true,
 "missing_lines": [], "OBS88_CODEBLOCK": "PASS"}
ok: True
```

- 语言标签**不参与判据**（`_FENCE_RE` 只匹配围栏载体与内容）

### 7e. 结论句式

**若 71D 把那 16 行改为语义组件而不同步修改 validate_codeblock_fidelity，流水线会在 stage 02（super_writer）会 FAIL_CLOSED，依据 = 反事实实验 7c：covered_in_codeblocks 16→0、deny/ask prefix 双 false、OBS88_CODEBLOCK=FAIL（ok=False）。**

## 8. OBS_68 DIFF 归因（71A′ 第 5 步，只举证不修）

- 5a. obs99-cover-path-70.md commit：`adf9ea63` @ **2026-08-05 12:11:20 +0800**
- 5b. bundle MANIFEST mtime：**2026-08-05 12:09:22**；安装侧 install receipts `installed_at`：**2026-08-05T04:09:26Z/27Z**（= 12:09:26/27 本地）
- 5c. 时间线：bundle 重建（12:09:22）→ 安装器（12:09:26）→ 报告 commit（12:11:20）
- **归因成立**：报告文件在安装器同步之后才写入 repo，因此不在自身核验范围内；OBS_68 的 1 文件 DIFF 是「核验先跑、报告后写」的时序产物。修复（bundle 重建 + 安装器）按指令排到 71B，本档不执行。

## 9. 71C 接线所需改动清单（71A′ 第 6 步，设计不实施）

| 文件 | 要改什么 | 触发 relock？ | 回归断言 |
|---|---|---|---|
| gzh-design/scripts/render_article.py | 增加 `:::` 围栏解析（parse_article）+ 分发到高级 builder + usage 新增键（`alert/quote/code_compare/media_text/gallery/long_image/resources/footnotes/dialogue` 及 Stage B 10 键 + `code_block`） | **是**（manifest 已含 advanced 文件，改 render_article 即改哈希） | 兼容性铁律：零 `:::` 文章输出逐字节不变（见 §10） |
| gzh-design/scripts/generate_advanced_html.py | 9 个构造函数抽成可导入模块（如 `advanced_components.py`）；★去掉 import 时副作用（L9-10 `OUT` 硬编码 + `os.makedirs` + 写盘；main 保护下移） | **是**（新增/移动文件进 manifest） | import 后无写盘副作用（断言 `tests/advanced-components/expected` 无新文件） |
| wxgzh_pipeline/writing_contract.py | `validate_codeblock_fidelity` 载体判据扩展：代码围栏 **或** 已批准语义组件（如 `:::alert`）内的逐字保真；`deny_prefix/ask_prefix` 扫描范围同步扩展 | 否（Pipeline 侧） | 7c 反事实样本必须 PASS（语义组件载体）；7b/7d 仍 PASS |
| validators/validate_theme_identity.py | `image_media_text_card`/`image_2a_standard` 指纹去碰撞：换用不与组件通用令牌重合的判据（如容器结构 + 图片 URL 属性组合） | 否（Pipeline 侧） | 5d 极端样本 `OFFICIAL_IMAGE_COMPONENT_TYPES` 必须为 0（组件不冒充图片） |
| contracts/05_gzh_design.yaml | `required_components` 新增键（建议：`alert/quote/code_compare/media_text/gallery/long_image/resources/footnotes/dialogue` + Stage B `facts/decision/steps/compare/annotated_image/faq/timeline/checklist/case/cta`），语义为「出现即计数、可零出现」 | 否（Pipeline 侧） | 契约校验器可解析新键；零组件文章契约仍 PASS |
| 兼容性铁律断言 | 见 §10 | — | — |
| OBS-105 docstring 陈旧 | 见 §11 文案 | 否 | — |

## 10. 兼容性铁律的自动化断言设计（71A′ 第 8f）

目标：断言「不含 `:::` 的文章渲染输出与接线前**逐字节相同**」。

- **fixture 存放**：`wxgzh-pipeline/tests/fixtures/obs106/`（冻结，不引用实时文件）
  - `article.zero-advanced.md`：从当前 RUN final_article.md 提取的**去高级语法子集**（或另写等价的零 `:::` 文章，含 `#`/`##`/代码围栏/普通段落/2a 图片/media-text 卡片各至少 1 例）
  - `expected/final.html` / `expected/final_runtime.html`：接线前 render_article.py 输出（sha256 固化）
- **比对方式**：测试内以子进程调用当前（接线后）render_article.py → 输出与 fixture 期望文件**字节级相等**（`assert out_bytes == expected_bytes`，不做任何归一化）；同时断言 fixture 期望文件 sha256 与仓库记录一致（防 fixture 被静默重写）
- **穷举覆盖**：`#`/`##` 标题、代码围栏（含语言标签）、普通段落、2a 图片、media-text 卡片——5 类语法各 1 例以上，全部逐字节比对
- **反向断言**：`:::` 围栏文章必须产生与零 `:::` 文章不同的输出（证明解析确实生效）

## 11. OBS-105 两处 docstring 陈旧修正文案（仅文案，不改文件）

1. `wxgzh_pipeline/writing_contract.py` 模块 docstring 第 2 条：
   - 现文：「guard-bash.sh 的 8 deny + 7 ask，⛔/⚠️ 前缀模板在 _common.sh」至少 10 条……
   - 修正为：「guard-bash.sh 的 deny/ask 拦截文案（本 RUN 实测 16 条，⛔/⚠️ 前缀模板在 _common.sh）至少 10 条必须以 fenced code block 逐字进入文章……」
   - 依据：`extract_deny_ask_lines` 实测 deny_ask_total=16（8 deny + 8 ask），docstring 写「8 deny + 7 ask」为陈旧值。
2. `wxgzh_pipeline/writing_contract.py` `validate_codeblock_fidelity` 函数 docstring：
   - 现文：「≥10 条 deny/ask 文案必须以 fenced code block 逐字进入文章……」
   - 修正为：「≥10 条 deny/ask 文案必须以 fenced code block（或 71D 后的已批准语义组件载体）逐字进入文章……」——本档不改文件，仅登记 71C 实施时同步。

## 12. 未覆盖与不确定项

- **未覆盖**：高级组件在微信编辑器内的真实粘贴呈现（需人工预览，本档只读不可执行）
- **未覆盖**：Stage B 的 10 个组件（facts/decision/steps/compare/annotated-image/faq/timeline/checklist/case/cta）的 HTML 构造与指纹碰撞（本档只测了 A 组 9 个 hammer 模板；B 组在 generate_advanced_html.py 中存在但 71A 生成样本仅覆盖 A 组——实际 `tests/advanced-components/expected` 只列出 9 组件 × 7 主题，B 组无模板文件，标记未覆盖）
- **未覆盖**：`:::` 解析器在 render_article.py 中的插入点与错误处理设计（71C 决定）
- 本档所有反事实实验均在 `.temp\obs106-check\counterfactual\` 副本上完成，RUN 原件未动

## 附录 A：76 项 runtime_manifest 完整清单

见本 commit 的取证输出（`COUNT 76` 全清单）：含 CONTRIBUTING.md / LICENSE / README*.md / RELEASE_NOTES.md / SHA256SUMS / SKILL.md / assets/* / docs/*（8）/ references/*（31，含 advanced-components.md + advanced/ 18 个）/ requirements.txt / scripts/*（25）/ tests/*（0）。完整 76 项清单：

```
CONTRIBUTING.md
LICENSE
README.en.md
README.md
RELEASE_NOTES.md
SHA256SUMS
SKILL.md
assets/preview-template.html
assets/sample-article.md
assets/theme-previews/theme-mono-blue-editorial.html
docs/all-themes.md
docs/gallery/graphite-minimal.html
docs/gallery/index.html
docs/gallery/moyu-green.html
docs/gallery/moyu-ticket.html
docs/gallery/olive-journal.html
docs/gallery/red-white.html
docs/gallery/sample-article.md
docs/gallery/zen-whitespace.html
references/advanced-components.md
references/advanced/alerts.md
references/advanced/annotated-image.md
references/advanced/case.md
references/advanced/checklist.md
references/advanced/code-compare.md
references/advanced/compare.md
references/advanced/cta.md
references/advanced/decision.md
references/advanced/dialogue.md
references/advanced/facts.md
references/advanced/faq.md
references/advanced/footnotes.md
references/advanced/links-resources.md
references/advanced/media.md
references/advanced/quotes.md
references/advanced/steps.md
references/advanced/theme-adapters.md
references/advanced/timeline.md
references/common-components.md
references/eval-cases.md
references/format-normalize.md
references/theme-generator.md
references/theme-graphite-minimal.md
references/theme-hammer.md
references/theme-index.md
references/theme-moyu-green.md
references/theme-moyu-ticket.md
references/theme-olive-journal.md
references/theme-red-white.md
references/theme-zen-whitespace.md
requirements.txt
scripts/check_links.py
scripts/component_lint.py
scripts/extract_docx.py
scripts/fix_html_quotes.py
scripts/generate_advanced_html.py
scripts/generate_article_html.py
scripts/generate_b_articles.py
scripts/generate_b_html.py
scripts/generate_dialogue_hotfix_samples.py
scripts/generate_dialogue_screenshot.py
scripts/generate_hammer_upgrade_samples.py
scripts/lint_advanced_components.py
scripts/make_b_assets.py
scripts/make_b_docs.py
scripts/make_review_zip.py
scripts/make_test_assets.py
scripts/publish_wechat_draft.py
scripts/render_article.py
scripts/run_b_agent.py
scripts/run_real_agent.py
scripts/scan_color_residual.py
scripts/screenshot_hammer_upgrade.py
scripts/update_component_docs.py
scripts/validate_gzh_html.py
scripts/wrap_preview.py
```

## 附录 B：commit 信息

- 报告：`audit/quality/obs106-advanced-components-71a.md`
- commit：见汇报（g 项）
