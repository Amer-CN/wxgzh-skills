# 档71C-R1 — 渲染器修复落地（不重锁）+ 锚缺口取证

- 授权锁: GZH_DESIGN_WRITE_ALLOWED=1, RELOCK_ALLOWED=0(其余 7 键 0)
- 工作区: 保留上一档(71C-R)未提交改动继续;gzh-design 4 文件、pipeline 1 文件
- 未 relock、未装安装侧、未改 pipeline 生产码/判据/锚/references

---

## 0c 文档 vs 实现差异表（七条）

| # | 组件 | 文档要求（references/advanced/*.md） | 实现现状（改动前） | 差异一句话 |
|---|---|---|---|---|
| 1 | alert | alerts.md L8-10 `type="warning"` + 正文 | render_article L364-368 只读 `typ=`、body 单 `<p>` | OBS-127 type= 未读；OBS-129 多行塌 |
| 2 | quote | quotes.md L9-21 `type=normal/highlight/sourced` | L369-372 只读 `qt=`、单 `<p>` | OBS-127/132 |
| 3 | code-compare | code-compare.md L8-15 `@before lang= 多行到 @end` | L373-382 只取同一行、lang 串入 | OBS-124 |
| 4 | media-text | media.md L9-12 `![说明](url)` + 解释段 | L383-387 `![]` 原文串入 exp | OBS-126 |
| 5 | long-image | media.md L25 `image= caption=` | L393-396 只读 url=、cap 硬编码默认 | OBS-125 |
| 6 | footnotes | footnotes.md L8-11 正文散落 `[^N]`+定义 | L402-405 只认 `:::footnotes` 块 | OBS-128 |
| 7 | (OBS-132) | — | quote 多行塌 | 同 #2 |

## 0d footnotes 位 3 三组数字（对照）

| 组件 | ① _BASE_EL_COUNT | ② 3 项输入 total | ③ Δ | per_item_ok |
|---|---|---|---|---|
| footnotes | 60 | 62 | **+2** | False |
| gallery | 60 | 69 | +9 | True |
| resources | 60 | 69 | +9 | True |
| dialogue | 60 | 69 | +9 | True |

★上档「Δ=+3 未命中」表述有误，实际 Δ=+2；判据 ≥3 下 False 是正确判定。

## 0e hammer.7 全仓（字节级）

- 真实版本号 = `v2026.08.02-hammer.7`（lock 现值）；此前 rg 显示 `n` 是显示层伪影
- 出现位置：RELEASE_NOTES 历史 section（67A/67C/67D）+ lock skill_version + lock history + audit 文档
- 本档升版仅改 2 处当前标识（RELEASE_NOTES 首行→hammer.8、WXGZH_PIPELINE_INTEGRATION.md）→ ≤5 不触发 S26

## 1a 色值回滚（OBS-143）diff

`generate_advanced_html.py code_compare()` after 段：
```
- background:#1E293B / 标签条 #0F172A / 标签字 #64748B / 代码字 #E2E8F0  (71C-R 误改)
+ background:#1a3a2a / 标签条 #0a2a1a / 标签字 #6BCB77 / 代码字 #C8E6C9  (references/advanced/code-compare.md L54-57 生产模板逐字)
```
回滚依据：code-compare.md L54-57（生产模板深绿 after 段）。

## 1b 八色值 grep 全表

生产码中八色值仅 `generate_advanced_html.py code_compare()` 一处（L93-99）；
`generate_hammer_upgrade_samples.py hammer_code_block` L763-792 是 67D 既有 1a 深色（非本轮）；
references/expected 为文档与验收产物。**S33 不触发**。

## 1c 正面回答

回滚后 code-compare `text_ok` 会变回 **False**——after 段 `color:#C8E6C9` 不在
pipeline `_CODE_ROW_RE`（仅 `#E2E8F0`）匹配范围，S3 取不到。这是预期的
**ANCHOR_GAP（pipeline 锚缺口）**，不是渲染器回退，不构成 S27。

## 2a-2h 六处修复自查（含 references 依据）

- 2a alert：`_p_lines()` 逐有效行一个 `<p>`，style 逐字复用（alerts.md L68 正文 p style）
- 2b quote：同口径；三分支正文 style 原文：normal `margin:0;font-size:14px;color:{tx};line-height:1.8;` / highlight `margin:0;font-size:16px;font-weight:800;color:{pd};line-height:1.7;` / sourced `margin:0;font-size:15px;font-weight:600;color:{tc};line-height:1.8;`
- 2c media-text：`![]()` 解析为 url+cap，剩余行逐行 p（media.md L9-11）
- 2d code-compare：续行到 @end + lang= 解析为 title 后缀（code-compare.md L8-15）
- 2e long-image：image=/caption= 优先，兼容 url=/cap=，**已删 `setdefault("cap","完整流程图")`**（media.md L25）
- 2f alert/quote type= 优先（兼容 typ/qt）；枚举来自 alerts.md L17-21（note/tip/important/warning/caution）+ quotes.md L9-21（normal/highlight/sourced）→ **S25 不触发**
- 2g footnotes：正文散落 `[^N]`+定义 与 `:::footnotes` 块双语法，parse_article 收集散落定义自动追加（footnotes.md L8-11）
- 2h hammer.7→hammer.8，改动 2 处 → **S26 不触发**；★无新增手写 HTML 常量（_p_lines 复用既有 style 串）→ **S34 不触发**

## 3a 九类三位全表（回滚后，仓内渲染器）

| 组件 | text_ok | struct_ok | per_item_ok |
|---|---|---|---|
| alert | True | True | None |
| code-compare | **False** | False | None |
| dialogue | True | True | True |
| footnotes | True | True | False |
| gallery | True | True | True |
| long-image | **False** | False | None |
| media-text | True | True | None |
| quote | True | True | None |
| resources | True | True | True |

★code-compare/long-image text_ok=False 为预期（ANCHOR_GAP），未翻绿、未改判据、未加锚。

## 3b 全哨兵三列表（71C-R2 输入，一个哨兵一行）

| 哨兵 | ①渲染原文 | ②body | ③最近 <p> 祖先 style |
|---|---|---|---|
| S_ALERT_TITLE | True | False | `margin:0 0 8px;font-size:15px;font-weight:700;color:#B3593B;line-height:1.5;` |
| S_ALERT_BODY | True | True | `margin:0;font-size:14px;color:#555555;line-height:1.8;` |
| S_QUOTE_TEXT | True | True | `margin:0;font-size:16px;font-weight:800;color:#8A4530;line-height:1.7;` |
| S_CMP_TITLE | True | False | `margin:0 0 12px;font-size:15px;font-weight:700;color:#555555;line-height:1.5;` |
| S_CMP_BEFORE | True | True | `margin:0;font-family:'SF Mono',...;font-size:13px;line-height:1.6;color:#E2E8F0;` |
| S_CMP_AFTER | True | False | `margin:0;font-family:'SF Mono',...;font-size:13px;line-height:1.6;color:#C8E6C9;` |
| S_MT_CAP | True | False | `margin:0 0 8px;font-size:12px;color:#737373;text-align:center;` |
| S_MT_EXP | True | True | `margin:0 0 24px;font-size:14px;color:#555555;line-height:1.8;` |
| S_GAL_TITLE | True | False | `margin:0 0 14px;font-size:15px;font-weight:700;color:#555555;line-height:1.5;` |
| S_GAL_CAP1/2 | True | True | `margin:0 0 16px;font-size:12px;color:#737373;text-align:center;` |
| S_LI_CAP | True | False | `margin:0 0 24px;font-size:12px;color:#737373;text-align:center;` |
| S_FN_1/2 | True | True | `margin:0 0 6px;font-size:12px;color:#737373;line-height:1.7;` |
| S_DIA_TITLE | True | False | `margin:0 0 12px;font-size:15px;font-weight:700;color:#555555;line-height:1.5;` |
| S_DIA_U1/A1 | True | True | `margin:0;font-size:14px;color:#555555;line-height:1.8;` |
| S_RES_TITLE | True | False | `margin:0 0 12px;font-size:15px;font-weight:700;color:#555555;line-height:1.5;` |
| S_RES_L1/2 | True | True | `margin:0;font-size:14px;color:#555555;font-weight:600;line-height:1.6;` |

## 3c expected 逐份 diff

**变动份数：0/182**。原因：generate_advanced_html.py main() 生成的是默认单行参数的
验收样例；六类修复只在多行输入时改变输出，默认样例不触发 → 逐字节一致（R22 已报）。

## 3d footnotes 双语法 usage 原文

- 文档语法（正文散落）：`components: {"footnotes": 1}`、unknown=0、paragraph=2
- 实现语法（:::块）：`components: {"footnotes": 1}`、unknown=0、paragraph=1
- 两种都走 footnotes 分支；SENTINEL 均进 HTML

## 4a/4b 两笔 commit

- gzh-design `69ed868`：4 文件 +119/−30（RELEASE_NOTES +15/−1、WXGZH_PIPELINE_INTEGRATION +1/−1、generate_advanced_html +36/−10、render_article +67/−18）
- pipeline `1b0c332`：1 文件 +3/−3（探针样本：alert type=warn→warning、code-compare 三行哨兵分布）

## 5a-5e 回归

- 5a gzh-design 仓内：**220 passed / 21 skipped**（既有环境性 skip）
- 5b pipeline 全量：**376 collected / 374 passed / 0 failed / 0 error / 1 skipped / 1 deselected**（与 71C-2A′ 一致）
- 5c fixture sha：final.html `AE8DB428…` ✓、final_runtime `21437B66…` ✓（安装侧未变）
- 5d OBS_68 算式：631 + 0（本档无新增文件）− 0 = **631**；实测 repo=631/installed=631、**diff=1**（`validate_component_visibility.py`，安装侧未同步——本档明令不装，预期）；OBS_69 MATCH
- 5e upgrade_regression：**ALL PASS**（relock dry-run x4 无变化、doctor PASS、cross-side SKIP）

## 本档没证明什么

- 未 relock → 安装侧仍是旧渲染器（hammer.7 旧实现）；新渲染器仅仓内验证
- code-compare/long-image 的 ANCHOR_GAP 未修（pipeline 锚缺口，留 71C-R2/后续）
- footnotes 位 3（per_item）判据未改（Δ=+2 < 3，判定 False 正确，判据是否调整待 71C-2B）
- 微信端渲染未验证（需人工预览）
- B 组 10 类未接线；fake_live 仍不过语法门禁
- 位 3 判据、_COMPONENT_PARA_RES、writing_contract、contracts/* 均未动
