# OBS-383 —— 77AF 体检报告一致性机械校验验收报告（字节级落盘）

- 档号：77AF（体检报告一致性机械校验 + 提示词取证升级）。
- 授权：RELOCK_ALLOWED 临时 0→1（批准人=用户，范围=pipeline scripts/新增校验脚本+tests；pipeline 无锁条目不涉锁；GZH 维持 0）。授权登记行随 feat 落账（序数按台账实况=五十三次，77AE 已占五十二）。
- 背景证据：RUN imwq5d 报告 §3 六族 zeros vs 文件 18、§3/§4 advisory 0 vs 文件 36+2、§6 basis 引文出自请求侧手填串（落账文件为机械 False，77AD 已救对）；hits 行总分笔误 21≠22（审核方按档修正）。
- feat 提交：654ec94（6 文件）。

## 1. 任务 0 证据（只读贴回存档）

- 文件侧实测：imwq5d `pattern_audit.stdout.json` ai_tone.count=18 / advisory_only.count=36 / strong_contextual.count=2 / hard_residue.count=0（报告写 zeros/0）；jla535：14/40/0/0；fmq9km：13/26/0/0。
- 落账 `copyright_approval.json` 19 条 auto_rule 全机械值 `USER_BLANKET_APPROVAL=False`；请求 19 条为手填串（小写 `true`，模板不同）；报告 §6 引请求侧——77AD 落账已救对、报告引错源。
- 标题：imwq5d 首候选五维 4/5/5/4/4 自加总 22；reason 逐候选形态（77Z 门后）。
- `scripts/` 并列结构：`install.py --target/--project-root/--skills-src/--dry-run` 为部署正门；`pipeline_state.json` version_check.status=current；6 份 `stage_receipt.json` 在册；`wall_self_check.json` 字段 `stage_wall_total_seconds/run_wall_seconds/delta_seconds/stages`。
- 体检提示词 v2026-09-10：仓内无此版本文件（grep 零命中），系用户侧文本；任务 3 文本交付用户合并，本轮不碰。

## 2. 实现（任务 1–2）

- 新增 `scripts/verify_report_consistency.py`（495 行，纯 stdlib+仓内既有模块，只读）：七项——receipt 六份存在性/verify_receipt 全绿（版本漂移容忍：仅 entrypoint/validator 脚本哈希漂移容忍，输出/输入/结构问题仍 FAIL）/pattern_audit 三层计数自描述一致+fidelity 交叉（含 advisory/strong 缺席 omission）/fidelity 四数+六 gate+six_family（声称 ai_tone 0 却申报改写即矛盾）/approval basis 落账==机械重算（调 media `_mechanical_basis`，禁字符串比对；时代感知：77AD+ 有 provenance 时代落账须==机械且请求手填即 FAIL，前 77AD 落账==请求一致即可）/标题首候选五维加总==宣称总分/wall 分段加总==total。stdout JSON，overall PASS exit 0 否则 exit 1。
- 回放定级（只读归档 `.temp/verify_77af_{imwq5d,jla535,fmq9km}.json`）：imwq5d **FAIL**（精确命中已知三处：pattern ai_tone 0≠18 / six_family 矛盾 / 请求侧手填残留 19/19）；jla535 **PASS**（前 77AD 落账==请求 4 条一致）；fmq9km **PASS**（15 条一致）。历史报告信用回溯，不改历史结论。
- 测试：新增 `tests/test_hf77af_consistency.py` 10 绿（干净合成 PASS/标题-wall-fidelity 伪造 FAIL/omission/six_family 矛盾/前后时代 basis/漂移分类）。

## 3. 升版/部署/回归/台账

- 升版：pipeline 9R33→**9R34**（动 scripts，release_date 2026-09-13）；根 README 版本表同步（77X 成规）。
- 不 relock（pipeline 无锁条目，77AE 先例）；R93 无变化。
- 部署：standalone install.py 正门在本环境不可行（locked skill sources 不可用：super-writer 等外部源仓缺失，实测 `locked skill sources unavailable`）→ 按既有惯例 cp 同步 6 文件；77AE hits 保留机制首次 live-fire 复核：装机 5 行 × 仓侧 2 行合并 → 5 行全保留（3bhpi2/m9coc1/fmq9km/jla535/imwq5d），action=merged。
- doctor：双侧 PASS、OBS_69/OBS_68 双侧 MATCH。
- 最终回归：见 §6（`.temp/upgrade_regression_77af.log`）。
- 台账：OBS-383 + 口径 98 + 授权登记行（五十二→五十三）；唯一编号 `265 119 383 True`；R59 21=21 双差集空。

## 4. 基线链

`ba4b4b5（77AE-F）→ 654ec94（feat 77AF，含授权登记行+obs304/obs288/README 随档）→ <docs 本报告>`

## 5. 执行过程如实记

- executor 通道连续被取消三次，主智能体降级直接执行（77AD 先例：主智能体收回）。
- 残留复用：工作区两份未跟踪新文件系被取消轮次的产出，经审查（495 行实现 + 350 行测试）符合简报后收编补齐。
