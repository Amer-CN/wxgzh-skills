# OBS-382 —— 77AE hits 台账防覆盖根治验收报告（字节级落盘）

- 档号：77AE（hits 台账防覆盖根治——fmq9km 行丢失的第二次咬）。
- 授权：RELOCK_ALLOWED 临时 0→1（批准人=用户，范围=wxgzh-pipeline scripts/install.py+tests；pipeline 无锁条目不涉锁；GZH 维持 0）。授权登记行随 feat 落账（序数按台账实况=五十二次，77AD 已占五十一）。
- 背景证据：fmq9km 生产行（装机侧 hits，9-11 亲验在册）被 77AD relock #113 内建 installer 整目录换新覆盖丢失（装机 hits mtime 9-12 17:52:58 = relock 窗口）；仓侧副本 2 行幸存；用户已按 RUN 档案恢复（装机 title-hits.md:39 在册，任务 2 复核通过）。
- feat 提交：3aa8911（6 文件）。

## 1. 任务 0 证据（只读贴回存档）

- 覆盖面钉死（整目录换新，双路径同果）：standalone `scripts/install.py:432-438`（目标 skill 目录整体 move 进 backups，staging 整体移入，含 pipeline `audit/quality/` 全量；仅 `.install-receipts` 移出保留 429-431/440-443）；relock 内建 `scripts/relock.py:486-503`（`copy_tree` 除 EXCLUDE 外全量打 bundle）→ 调同一 `install.py`（532-538 `_run_official_installer`）→ 同上整目录 switch。
- 保留机制清单（均不保生产行）：`zipping.EXCLUDE_DIRS/SUFFIXES/FORBIDDEN`、`PIPELINE_RELEASE_EXCLUDES`（.gitattributes/.installed-from）、`skill_discovery` root 面 EXCLUDE（不含 audit）、OBS-107 豁免位（`observability.check_pipeline_consistency` 排除 `audit/quality/**/*.md`——只是 doctor 比对豁免，不阻止覆盖）。
- ai-tone 同命运：`.jsonl` 不在任何排除集；装机侧 `audit/quality/ai-tone-calibration.jsonl` mtime 2026-09-12 17:52（= relock #113 窗口）被覆盖，与仓侧同字节 36455——生产若有追加同样会丢。
- 漂移容忍实证（合并 hash 安全）：恢复行在册的装机 hits 与仓侧 2 行不一致，doctor 仍 PASS/OBS_69 MATCH/OBS_68 MATCH——doctor 不对 pipeline 自身做 root 比对（skills 项为 None）、OBS_68 排除 audit、锁值由仓侧源树计算。结论：装机侧 audit 生产合并**不污染任何哈希判定面**。
- relock 判据：`skills.lock.json` skills 键无 `wxgzh-pipeline`（仅 aihot/gzh-design/media-enrichment/super-writer/zh-human-writing）→ **本档不动锁条目，不 relock**。

## 2. 实现（任务 1，小方案）

- `scripts/install.py` 新增标定清单 `PRESERVED_PRODUCTION_DATA = ("audit/quality/title-hits.md", "audit/quality/ai-tone-calibration.jsonl")`（相对 pipeline 根，注释注明纪律）。
- 纯函数：`_production_run_id`（RUN_ID 取键）/`_split_ledger_table`/`_merge_title_hits_text`（new 顺序为底、new 赢同键、backup 独有追加；非台账形态回退整行并集）/`_merge_jsonl_text`（整行精确并集）/`_merge_production_file`（kept-new/restored-backup/merged/identical 四动作词）。
- 挂点：`install()` 内 complete_lock_ok 门通过后、`_write_installed_from` 之前（此时 `backups` 仍在作用域、transaction 未清理；final verify 已在合并前跑干净树）；仅 `backups.get("wxgzh-pipeline")` 存在时执行；动作记入顶层返回 `production_data_preserved` 键。relock 调同一 install.py 自动继承。
- 取舍如实记：未做全链路 install e2e（需伪造锁链/收据，超最小改动）；合并后不重跑 verify（简报既定，doctor 面天然排除 audit）；relock 路径未单测（同一文件自动继承）。

## 3. 测试实测

- 新增 `tests/test_hf77ae_preserve.py` 8 绿（纯 IO + tmp 树，无 subprocess）：装机独有行保留（含 fmq9km 原形）/仓新行分发同键新赢/jsonl 并集去重/四回退（kept-new/restored-backup/双缺/identical）/清单钉死。
- 既有 installer 相关：hotfix3/4/5 + obs107 共 58 绿；hotfix1 10 绿 1 跳过，1 失败系联网 clone 外部仓（`github.com/Amer-CN/super-writer.git` Repository not found）属环境除外。
- `test_hf76r.py` 19 绿（含 obs304 钉子 264/119–382；obs288 白名单零改动——本档未加指令规则）。

## 4. 升版/回归/台账

- 升版：pipeline 9R32→**9R33**（动 installer 脚本，release_date 2026-09-12）；根 README 版本表同步（77X 成规）。
- 不 relock（判据见 §1 末），R93 无变化（5256ec28…）。
- doctor：双侧 PASS、OBS_69/OBS_68 双侧 MATCH（装机同步：install.py/VERSION/两测试/ledger/根 README）。
- 最终回归：见 §6（`F:\AIXM\wxgzh\.temp\upgrade_regression_77ae.log`）。
- 台账：OBS-382 + 口径 97 + 授权登记行（五十一次→五十二次）；唯一编号 `264 119 382 True`；R59 21=21 双差集空。

## 5. 基线链

`ce35123（77AD-F）→ 3aa8911（feat 77AE，含授权登记行+obs304/obs288/README 随档）→ <docs 本报告>`

## 6. 执行过程如实记

- 并行会话落地 77AD-F（ce35123，归位+口径 96）与本档执行交错，两边工作区文件无交集（本档基线重核对后执行）。
- executor 本轮可用（沙箱已放开），2 文件改动（install.py +152/-0 纯新增逻辑 + 新测试 8 用例），既有测试断言零同步。
