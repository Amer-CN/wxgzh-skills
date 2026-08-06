# 档71E — OBS-175~179 载体放宽 + 语义拆分 + 章节亲和判据 + 重出草稿

## ① 本档修的是上一档的什么错

| 项 | 上一档(71D)的错误 | 本档修复 |
|---|---|---|
| OBS-175 | 配图位置无机器判据:bindings placement anchor 空、confidence=0.0,chart-003(自检 19→25)落在第二章而数字线在第一章 | 新建 validators/validate_image_section_affinity.py(独立 CLI+tests);3e 在 71D RUN 上实测抓出 A-007 与 A-009 跨章;6h 在新 RUN 上三图全部同章 |
| OBS-176 | validate_codeblock_fidelity 只认 fenced code block,16 条护栏文案同一批出现两遍(alert + bash 围栏) | 载体放宽 = fenced code block ∪ 已批准 A 组组件块(R48 单一来源导入);MIN_DENY_ASK_COVERAGE=10 未动;新 RUN 16 行只在两个 alert 块出现一次 |
| OBS-177 | 8 条 ⛔ 与 8 条 ⚠️ 压平进同一 alert type=warning(OBS-127 修复的能力没用上) | 指令拆两块:caution=8 条 ⛔ / warning=8 条 ⚠️;新 RUN 实测两块渲染产物仅标签字符不同(CAUTION/WARNING),R50 满足 |
| OBS-178 | closeout 报告被 71D 就地改成跨档混合文档,同文件三处过期陈述 | 三处加「71E 更正」标注(不改旧文);本档新建独立报告文件 |
| OBS-179 | OBS-131 行引用无出处直引「71D 不换载体,等 71C-R 修 alert 多行」 | 删除无出处直引,改写为「审核方 71E 判定:OBS-129 已修,alert 结构位成立且语义最近」口径 |

## ② 每条「已覆盖」声明 → 测试函数名 + 断言行原文（R36/R49）

| 声明 | 测试函数 | 断言行(原文) |
|---|---|---|
| alert 载体可承载 16 行 | test_obs176_a_alert_block_true | `assert ok is True, rep` / `assert rep["covered_in_codeblocks"] == 16` / `assert rep["carrier_kinds"] == ["alert"]` |
| fence 载体向后兼容 | test_obs176_b_fence_true | `assert ok is True, rep` / `assert rep["carrier_kinds"] == ["fence"]` |
| 跨载体合并计数 | test_obs176_c_split_across_carriers_true | `assert rep["covered_in_codeblocks"] == 16` / `assert rep["carrier_kinds"] == ["alert", "fence"]` |
| 普通段落不计数(反例 D) | test_obs176_d_plain_paragraphs_false | `assert ok is False, rep` / `assert rep["covered_in_codeblocks"] == 0` / `assert rep["carrier_block_count"] == 0` |
| 未批准组件不计数(反例 E) | test_obs176_e_unapproved_component_false | `assert ok is False, rep` / `assert rep["covered_in_codeblocks"] == 0` |
| 改写/散文化 FAIL(反例 F) | test_obs176_f_rewritten_prose_false | `assert ok is False, rep` / `assert rep["covered_in_codeblocks"] < 16` |
| 9 条 FAIL;⛔ 无 ⚠️ FAIL(反例 G) | test_obs176_g_nine_lines_and_prefix_gap_false | `assert ok9 is False, rep9` / `assert rep9["covered_in_codeblocks"] == 9` / `assert repd["ask_prefix_present"] is False` |
| 组件块状态机口径(未配对/嵌套不计) | test_obs176_carrier_blocks_unpaired_and_nested_ignored | `assert blocks == ["闭合块", "未配对块"], blocks` / `assert kinds == ["alert", "alert"], kinds` |
| 亲和正例(同章 PASS) | test_obs175_positive_same_chapter_pass | `assert rep["ok"] is True, rep` / `assert rep["per_image"][0]["same_chapter"] is True` |
| 亲和反例(挪章 FAIL+reason) | test_obs175_negative_cross_chapter_fails | `assert rep["ok"] is False` / `assert rep["reason"] == REASON` / `assert img["same_chapter"] is False` |
| 缺 chart_group 边界 FAIL | test_obs175_boundary_missing_chart_group_fails | `assert "missing field: chart_group" in rep["per_image"][0]["reason"]` |
| CLI 退出码 0/1 | test_obs175_main_exit_codes | `assert code_ok == 0` / `assert code_bad == 1` / `assert REASON in capsys.readouterr().out` |
| 旧 16 条测试不回归 | test_obs88_writing_contract.py(11 项) | 全量 junit 0 failed(见第 5 步) |

## ③ 台账数字

- 总行数 **96**(1d 后实测重数)
- 状态列「未修」**5** 行(OBS-122/131/148/158/159)
- 未修清单分区 **8** 行(5 未修 OBS + 微信端【已关闭】+ fake_live + 键测试执行层覆盖【未覆盖】)
- 「待查」**5** 行(OBS-134/141/142/149/150)
- 空号 **1** 行(OBS-169,附证据)
- 「已关闭」**1** 行(微信端渲染,R51 证据:2026-08-07 02:18 用户人工预览三项全过,原话「1 过 2 过 3 过」)

## ④ 所有空集与归零结论 → 各自反证物（R32）

| 结论 | 反证物 |
|---|---|
| 载体放宽后普通段落不计数 | test_obs176_d_plain_paragraphs_false(16 行逐字在段落 → ok False) |
| 载体放宽不是取消门禁 | 反例 D/F 实测 FAIL(S66 未触发);G 的 9 条 FAIL 证明阈值仍在 |
| 亲和判据能抓跨章 | 3e:71D RUN 上 A-007/A-009 抓出 section mismatch(原始输出已贴) |
| 两块 alert 视觉可区分(R50) | 1d 探针 + 第 6 步实测:容器 style 相同,标签字符 CAUTION≠WARNING 逐字不同 |
| 16 行全文只出现一次 | 第 6 步 6g:⛔ 8 行 + ⚠️ 8 行,每行唯一,::: 总行数 = 4(2 开 2 闭) |

## ⑤ 第 1–7 步逐步实测

### 第 1 步 取证(1a–1e)

- 1a 图片位置机制:安装侧 gzh-design scripts/render_article.py L222-253——`render()` 用
  `_distribute(len(img_queue), len(chapters))` 按 img_queue 顺序 round-robin 分配章节,
  `img = img_queue.pop(0)` 顺序消费;bindings 的 placement(anchor/position/confidence)
  字段完全不被读取。① 位置由「bindings 顺序 + 章节数取模」决定;② anchor 空 /
  confidence=0.0 无回落分支(字段未参与);③ 渲染器内不存在可注入位置控制点
  → **S65 成立**,按 3d 例外条款执行:判据不挂主门禁,保留独立 CLI+测试,第 6 步仍实测。
- 1b 71D RUN bindings 全文已贴(3 张图均无 chart_group/metric_name/numbers 字段,
  placement.anchor="" / confidence=0.0 / position="after")。
- 1c 章节标题形态:`<p style="font-size:17px;font-weight:900;color:#555555;letter-spacing:0.3px;"><span leaf="">一、…</span></p>`
  + `PART NN` 副行;章节边界 = 标题文本在 HTML 中的最后一次出现(TOC 在前,章节标题组件在后)。
- 1d caution vs warning:两段完整 HTML 已贴(.temp\71e-alert-probe\final.html),容器
  `<section style="margin:0 0 24px;background:#FAF9F5;border-radius:0 12px 12px 0;border-left:4px solid #E3C6B9;padding:16px 20px;">`
  逐字相同,标签字符 CAUTION vs WARNING 逐字不同 → **S64 未触发**,R50 满足。
- 1e 归属:pipeline 侧 wxgzh_pipeline/producers.py AGENT_INSTRUCTIONS["super_writer"]
  组装写作指令(stages/super_writer.py 挂载 OBS-88 合同);拆两块只需改指令文本,
  super-writer 技能文件零改动 → **S67 未触发**。

### 第 2 步 载体放宽(OBS-176)

- 2a `_carrier_blocks()`:fence(_FENCE_RE)+ 已批准组件块(状态机与安装侧 parse_article
  in_component 同口径:strip 后 ::: 开头进入,下一条 ::: 行关闭,无嵌套;未配对不计)。
- 2b 已批准集合从 validators/validate_component_visibility.APPROVED_CARRIER_COMPONENTS
  importlib 加载(R48);S63 未触发(实测 import 成功,9 类清单已贴)。
- 2c validate_codeblock_fidelity 只在 block_text 内判 covered/前缀;MIN=10 未动;
  report 新增 carrier_kinds/carrier_block_count。
- 2d 七条正反例(A–G)+ 2 条辅助,函数名与断言见 ② 表;S66 未触发。
- 2e 已贴。

### 第 3 步 章节亲和判据(OBS-175)

- 3a docstring 判据 + 排除项依据已写;3b CLI(--article/--html/--bindings/--out-dir,
  exit 0/1,reason 常量 OBS175_IMAGE_SECTION_AFFINITY=FAIL);3c 正例/反例/边界三测试。
- 3d S65 成立 → 不挂主门禁(3d 例外条款),独立 CLI + 测试。
- 3e 71D RUN 实测(原始输出已贴):A-005 同章但缺 chart_group FAIL;A-007 图在第二章、
  数字线在第一章 → **跨章被抓出**;A-009 图在第三章、数字线在第一章 → 跨章被抓出。

### 第 4 步 台账与报告更正

- 4a obs-ledger.md:微信端渲染→已关闭(R51 证据);OBS-131 删无出处直引;新增 175–179 五行;
  口径加 R51;4b closeout 三处「71E 更正」标注;4c 本报告文件(新建,不就地改旧档)。

### 第 5 步 回归与安装

- 5a pytest(junit 权威,.temp\71e-pytest-junit.xml / 71e-pytest-junit-after.xml):
  装前 **421/419/0/0/1/1**,装后 **421/419/0/0/1/1**(基线 408 + 13 新增 = 421,逐位对上)。
- 5b bundle 重建 exit 0 → 便携安装器 exit 0 → post-doctor PASS。
- 5c OBS_68:647(基线)+ 3(validate_image_section_affinity.py + 2 测试)= **650**;
  实测 repo=650 / installed=650 / diff=0 / missing=0 / extra=0(报告文件按
  audit/quality/*.md 口径不计入)。
- 5d OBS_69 MATCH(baseline=installed=f2b5f390…);5e upgrade_regression ALL PASS
  (relock dry-run x4 无变化;cross-side SKIP)。
- 5f 三处锁文件 git diff --stat 空;两仓 git status --porcelain 空(收尾复核)。

### 第 6 步 重出文章

- RUN `20260807T031036-vibe-coding-guide-16-m0zejx`;final_article.md sha256
  `d6f692f07c171189ad96fd8cf200ff64de382931ce03ab788c8932de7d4bcbde`(57 行 / 3370 字符)。
- 16 行:8 条 ⛔(L20-27)+ 8 条 ⚠️(L31-38)逐字,全文各出现一次;bash 围栏副本已删;
  ::: 总行数 = 4(两个块的开/闭);两个 fenced text block 保留(安装/关闭命令,可复制)。
- 两块 alert HTML 片段已贴(见 6g):CAUTION 块 <br>=0、</p>=10;WARNING 块 <br>=0、</p>=10;
  容器 style 逐字相同、标签 CAUTION/WARNING 可区分(R50)。
- 亲和判据新 RUN 实测:三图全部「图所在章节 == 数字线所在章节」(same_chapter=true,
  chart-003 跨章消失);judge 整体 exit 1 仅因 bindings 缺 chart_group 字段
  (OBS-175 边界判据;S65/3d 例外下 FAIL 不阻塞,已在 l 项写明)。
- 门禁逐条:PASS(见 6f 清单;OBS88 数字 3 组、OBS88 代码块 16/16、media visual_units=5/5)。

### 第 7 步 微信草稿

- 7a uploadimg ×3:http_status=200,wechat_errcode=null;7b draft/add ercode 非 0 → S61 未触发;
- 7c media_id `Y3aIagws[REDACTED]`;标题 `vibe-coding-guide 护栏插件：16 条命令护栏文案全清单`;
  草稿数 10→11(delta=1);7d 71D 草稿未动;7e 停机等用户肉眼验收。

## ⑥ 没证明什么

- OBS-175 判据未挂主门禁(S65/3d 例外):未来渲染器接入位置控制点前,亲和仅独立 CLI+测试。
- bindings 缺 chart_group 是结构性缺口(media-enrichment 为锁内 skill,本档未改):
  亲和判据在缺字段时只能 FAIL,无法全绿。
- 微信端两块 alert 的实际呈现未经本档人工预览(验收在 7e 之后由用户执行)。
- 组件载体之外的正文不计数,但「正文含 16 行改写版」这类反例只覆盖到改写不逐字,
  未覆盖「逐字但混入正文其他载体形态」(如表格)的场景。
- B 组 10 类仍未接线;fake_live 仍不过语法门禁;gzh-design 版本仍 hammer.8,未 relock。

## ⑦ 新发现但没修

- media-enrichment placement_planner.find_anchors 对 chart claim_text 的
  [:30] 子串匹配几乎必然落空(claim 用半角冒号、文章用全角逗号),图表锚点实际
  依赖人工/驱动侧补写 —— 与 OBS-175 同根,建议后续由媒体侧图表 spec 携带
  chart_group + start/end 直接产出锚点(需动锁内 skill,待 relock 档)。
- validate_syntax_gate.py 存在 DeprecationWarning(invalid escape sequence),
  与语法门禁行为无关,属历史遗留。
- 71D 的 RUN(9m2li7)与 71E 第一个 RUN(yayrgl,无箭头数字对导致 A-009 无法批准)
  均为 incomplete,保留作取证,不清理。
