# 档71C-R2 — 硬化 + 判据分裂 + 锚实测导出 + 第十二次 relock

- 授权: GZH_DESIGN_WRITE_ALLOWED=1, RELOCK_ALLOWED=1(其余 7 键 0)
- 事实源: references/(含 references/advanced/*.md 输入语法 + 生产 HTML 模板)
- gzh-design: 69ed868 → ea2fb70;pipeline: 本档多文件 + 第十二次 relock

---

## 第 0 步 文档化槽清单

0b 落成 `validators/component_slots.py`(纯数据结构,每条带 references 行号,不 import 渲染器)。
0c 全表: **30 槽(模式展开)**、必填 20 槽。

| 组件 | 槽(模式展开) | references 行号 |
|---|---|---|
| alert | title(可选) + body×5(note/tip/important/warning/caution) | alerts.md L8/L9/L17-21 |
| quote | text×3(normal/highlight/sourced) + source(可选) | quotes.md L10/L15/L20/L19 |
| code-compare | title(可选)×2 + before×2 + after×2 + lang(可选) | code-compare.md L8/L9-11/L12-14 |
| media-text | cap(必填) + exp(必填) | media.md L10/L11 |
| gallery | title(可选) + caption×N(必填) | media.md L17/L18-19 |
| long-image | image(必填,URL 槽) + caption(可选) | media.md L25 |
| resources | title(可选) + link_text×N + url×N | links-resources.md L8/L9-10 |
| footnotes | fn_text×N(必填) | footnotes.md L11 |
| dialogue | title(可选) + msg×N(必填) + name(可选) | dialogue.md L8/L9-12/L20-21 |

0d 欠测清单: **30/30 槽全部欠测**(旧探针用通用 SENTINEL_S1-3,无按槽独立哨兵)→ 2a 重建。

## 第 1 步 硬化(OBS-145)

- 1a alert() 显式枚举 `if typ not in {note,tip,important,warning,caution}: typ="warning"`(alerts.md L17-21)
- 1b quote() 同口径(quotes.md L9-21)
- 1c `_render_component` 未知 type 记入 `usage["unknown_component_args"]`,不影响退出码
- 1d 三份负样本(`type="warn"`/`type="xxx"`/缺 type):returncode=0 + 哨兵可见 + 前两份 unknown_component_args 有记录
- 1e 语法门禁 type 枚举校验(未定义值 → FAIL + 源稿行号),正负样本各一
- 1f grep 全表: 唯一作者可控下标 = alert `at[typ]`(已硬化);其余 `T[tid]` 的 tid 由 render_article 固定传 "hammer" → **S35 不触发**

## 第 2 步 判据分裂 + 位 3 v2

- 2b render_ok = 全部必填槽哨兵在渲染 HTML 原文(只问渲染器)
- 2c anchor_ok = 全部槽哨兵(必填+可选)在 _body_plain_text(只问 pipeline 锚)
- 2d per_item_ok v2 = N=3 哨兵最近 `<p>` 祖先起始偏移两两不同且数 == N;**已删 _BASE_EL_COUNT/_measure_base_el_count/魔数 3**(OBS-140/147)
- 2e docstring 与实现一致(OBS-139),测试校验

### ★2f 预期翻转表(跑前写)vs 实测

| 预测 | 实测 | 结果 |
|---|---|---|
| footnotes per_item_ok False→True | True | ✓ |
| MULTILINE {alert,media-text,quote}→空集 | 空集 | ✓ |
| QUARANTINED {code-compare,long-image}→空集 | 空集 | ✓ |
| ANCHOR_GAP 含 7 类(title/caption/after 等缺口) | 8 类(7 类全中 + quote sourced 新缺口) | ✓(方向一致,quote 为新暴露槽) |

## 第 3 步 锚实测导出

- 3a `export_body_anchors_from_measurement`: 27 哨兵、NO_P_ANCHOR=0(**S37 不触发**);URL 槽(image/url)记 URL_SLOT
- 3b `build_component_para_regexes` 从锚导出生成;`_COMPONENT_PARA_RES` 快照测试焊死(R19)
- 3c 防放宽阀一: 导出锚 ∩ {封面/目录/章节/署名/页脚} 完整 style = ∅;既有负对照测试仍过
- 3d 防放宽阀二: 见 6d(现 RUN fixture 逐字节不变,intro guard/字数/fidelity 结论不变)
- 3e 锚只来自 0b 文档化槽哨兵实测(R33 不触发)

## 第 4 步 渲染遗留定案

- 4a code-compare title「(lang)」: references 无依据 → **删除**(code-compare.md L8-15 的 lang 仅是 @before 行内属性)
- 4b long-image 缺 caption: references 无「空 <p>」依据 → **缺省不产出说明行**(media.md L25 caption 可选)
- 4c quote source=: references/quotes.md L19 定义 → **接线**;延伸 dialogue name=(dialogue.md L20-21)同步接线
- 4d footnotes [^N] 字面: footnotes.md L8 + L52 微信铁律(禁 href 内部锚、保留可见文字)→ **字面保留是规定形态,已实现**

## 第 5 步 四名单 + 矩阵 v2

- 5a ANCHOR_GAP = render_ok 且 not anchor_ok(不拦作者,CLI/报告打印缺 style)
- 5b QUARANTINED 语义收紧为 not render_ok(注释写明)
- 5c 四名单全部现场导出;常量快照 = 实测值
- 5d 矩阵 JSON criteria_version="v2" + criteria_changelog(OBS-147)
- 5e OBS-138 测试翻转(两种语法 footnotes 都 =1)

实测导出(仓内渲染器 437fb8aa):
```
QUARANTINED: []   MULTILINE: []   ANCHOR_GAP: [alert code-compare dialogue gallery long-image media-text quote resources]   APPROVED: [footnotes]
```

## 第 6 步 relock + 安装

- 6a 第十二次 relock: 远端见证 a/b/c PASS;root `a51a551b→795b5ea2`、entrypoint `cb2e186c→4b6fc20e`、commit `5791e637→ea2fb70`、tree `b81b7e8d→19258b83`、version `hammer.7→hammer.8`、file_count 76→76;lock 双侧 `F2B5F390AE4BABF969AF3F01AFD98099436649FD57BD6DEAE8F35A5B7B6D11C6`
- 6b 安装侧: installer PASS(四锁 hash 全 true)+ post-doctor PASS;OBS-69 基线同步 observability.py
- 6c 台账: `audit/upgrade-capability/lock-backups/skills.lock.20260806T122316Z.json`;ledger `relock-gzh-design-20260806T122316Z-003f86f3`
- 6d fixture 重渲染(.temp/71cr2-rerun/): final.html `AE8DB428…`、final_runtime `21437B66…` **逐字节一致**(该文章不含 ::: → 行为不变铁律)**,S31 不触发**
- 6e OBS_68 算式: 631 + 2(component_slots.py + lock-backup json)− 0 = **633**;实测 repo=633/installed=633 MATCH、diff=0;OBS_69 MATCH(双侧 F2B5F390)
- 6f 全量 pytest: **381 collected / 378 passed / 0 failed / 0 error / 1 skipped / 1 deselected**(新增 5 用例,翻转 2 用例,2f 预测内;无预测外失败)
- 6g upgrade_regression: **ALL PASS**(真锁后)

## 第 7 步 提交

- gzh-design `ea2fb70`(2 文件 +60/−21,已 push fix/obs73-codeblock-docs)
- pipeline 本档 commit(见 git show --numstat)

## 本档没证明什么

- 锚集扩大后 intro guard/字数/fidelity 结论逐项对照:现 RUN 无 ::: 组件 → 结论不变(见 6d 字节一致)
- 微信端渲染未验证(需人工预览)
- B 组 10 类未接线;fake_live 仍不过语法门禁
- ANCHOR_GAP 8 类的缺失 style 串已在 CLI/报告打印,但 pipeline 锚未补(设计如此:不拦作者)
- writing_contract / contracts/* 未动

## 本档新发现但没修

- quote sourced 模式 text 锚(`font-size:15px;font-weight:600`)与 resources url 锚(`margin:2px 0 0;font-size:12px`)为 ANCHOR_GAP 新暴露,未补锚(设计:ANCHOR_GAP 只打印)
- relock 首次 apply 时 upgrade_regression 因 OBS-69 基线未同步而 FAIL(relock 不自动同步 observability.py,需配套手动同步)——已在同档修复,但 relock 流程本身未内置该检查
