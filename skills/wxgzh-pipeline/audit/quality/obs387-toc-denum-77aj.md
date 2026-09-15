# OBS-387 —— 77AJ toc 卡片标题去序号显示验收报告（字节级落盘）

- 档号：77AJ（toc 卡片标题去序号显示：PART 序号与"一、二、"双重编号不同框）。
- 授权：RELOCK_ALLOWED 临时 0→1（批准人=用户，范围=gzh-design：hammer_toc 显示层脱序号+tests；pipeline 无锁条目不涉锁；GZH_DESIGN_WRITE_ALLOWED 维持 0——显示裁剪，主题设计值零触碰）。授权登记行随 feat 落账（序数按台账实况=五十七次，77AI 已占五十六）。
- 背景证据：生产截图——PART 序号与"一、二、"双重编号挤占单行卡片，标题有效信息被省略号吃掉。
- 用户裁决日期：2026-09-14（转发即批准）。
- feat 提交：427fccf（7 文件）。

## 1. 任务 0 证据（只读贴回存档）

- 现行 `hammer_toc`（77AI 后形态，`generate_hammer_upgrade_samples.py:718`）：`def hammer_toc(theme_key, chapter_titles, subtitles=None)`；docstring 载 77AI 语义（等长对齐、缺省回退 `""`）；循环 `for i, title in enumerate(chapter_titles, 1)` 取 `sub` 后 `cards.append(_toc_card(t, f"PART {i:02d}", title, sub, highlight=(i == 1)))`；末卡 `_toc_card(t, "PART ///", "写在最后", "署名与 CTA", highlight=False)` 写死。
- 唯一调用点 `render_article.py:309`：`parts.append(H.hammer_toc(theme_key, chapter_titles, chapter_subtitles))`；`chapter_titles = [c["title"] for c in chapters]`（:284）；章节体 `H.hammer_chapter(theme_key, f"{i:02d}", ch["title"], ...)`（:325，原标题直通）。
- 野生章节号形态普查（正则覆盖集）：本档脱两式——`^[一二三四五六七八九十]+[、．.]` / `^\d+[、.．\s]`；仓内同族口径 `format-normalize.md:40`（`一、`/`二/`1.`/`01`/`第X章/节/部分`/`Part N`/`PART N`）与 `pattern_audit.py:731` LT-004 判定式；括号式（`(1)`/`【一】`）、`第X章`、`Part N` 野生存在但本档不脱（档文只给两式，不扩案）。
- LT-004 锚点约束重申：`ai-tone.md:19` 最小改法"只删编号；标题文字/顺序/层级不动"→ 77AJ 对应章节数据只读，脱序号只许在卡片显示副本上做；副标题/章节数据/正文/锚点不动；`PART ///` 不动。

## 2. 任务 1 实现

- `generate_hammer_upgrade_samples.py`：顶部 `import re`（原仅 os/sys）；新增 `_toc_display_title()`（两式 `re.sub` 逐式试脱，命中即 `strip`，脱空回退原文）；`hammer_toc` 循环改传 `_toc_display_title(title)`，签名/副标题/末卡不动，docstring 追加 77AJ 两行。
- 测试：新增 `tests/test_hf77aj_toc_denum.py` 4 绿（带序号脱号+单行 clamp 在行/无序号原样/脱空回退原文/章节体仍带编号；末卡 `写在最后` 不动并入第 1 条断言）；gzh 全套 `259 passed/21 skipped/0 failed` 零新红；toc 三件套 10 绿（77AJ 4 + 77AI 4 + 单行 2）。

## 3. 升版/锁链/回归

- 升版：gzh hammer.24→**hammer.25**（RELEASE_NOTES 条目 + SHA256SUMS 精选集 surgical 原行不动+新测试 1 行 `553c497a…` + README 根版本表 2 行同步；#102 版本号以实测口径为准）。
- relock **#117**（gzh hammer.25：`relock-gzh-design-20260915T045435Z-050d343e`，dry-run 远端见证 PASS(a/b/c) + root/component_source/version/commit/tree CHANGED、manifest/entrypoint/validator 不变 → `--apply` 写锁+history+备份在册；锁 sha `32568218…→79f5cf7e…`，R93 双侧一致；history 113→**114 条**）。
- 装机同步：cp 惯例 8 文件（gzh 脚本/测试/RELEASE_NOTES/SHA256SUMS + pipeline observability/锁/test_hf76r + 根 README）；装机侧 `_toc_display_title` grep 命中（:704/738/747）；装机侧锁 gzh 条目 hammer.25/component `83c0cea2`/commit `427fccf`。
- doctor：双侧 PASS、OBS_69/OBS_68 双侧 MATCH（仓侧与装机侧同口径复验）。
- 最终回归（relock 后）：`upgrade_regression.py` 在本环境 120s 超时未落盘（装机双侧 doctor 已 PASS 为证）→ 改按分层回归等效覆盖：gzh 全套 259 passed/21 skipped 零新红 + pipeline 门禁 `test_hf76r+test_observability` 全绿 + relock dry-run ×4 无变化 + suspect 7 红基线比对（stash 还原预 relock 态同 7 红逐项一致，零新增；7 红=hotfix1 portable×1 + hotfix7×3 + obs171×1 + obs80×2，既有环境红）。

## 4. 台账

- OBS-387 + 口径 102（含审核方追记逐字落点）+ 授权登记行（五十六→五十七）；唯一编号 `269 119 387 True`；R59 21=21 双差集空；obs304 钉子 268→269 随档。

## 5. 执行过程如实记

- executor 通道不可用，主智能体降级直接执行（77AD/77AF/77AG/77AH/77AI 先例）。
- flow-gate 过渡文件 2 个（`.temp/probe77aj.py` 锚点定位 + `.temp/ledger_77aj.py` 落账脚手架），简报登记后写入、用后删；`E:\Temp\reg77aj_*.txt` 系仓外 pytest 输出中转，用后删。
- `--apply` 首跑 120s 超时按中断计（bare exit 1），查验锁/history/备份三件均已落盘且 dry-run×4 无变化，属写后回归段超时非锁链中断；pytest 全量同因超时改分层跑，基线比对法等效。
- R59 口径：`main=21 partition_active=21` 双差集空沿 77V–77AI 同口径如实报（分区表结构见 obs-ledger 未修清单分区；本档新增 OBS-387 为已修不入分区）。

## 6. 基线链

`e748277（77AI-F）→ 427fccf（feat 77AJ，含授权登记行+obs304/README 随档）→ <docs 本报告+锁链>`
