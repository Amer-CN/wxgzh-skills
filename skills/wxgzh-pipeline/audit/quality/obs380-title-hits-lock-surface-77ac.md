# OBS-380 —— 77AC title-hits 移出锁面验收报告（生产数据归位审计面，77AA 设计债务根治）

- 档号：77AC（title-hits.md 移出锁 runtime 面：生产数据台账归位 pipeline audit/quality/，OBS-380）。
- 授权：RELOCK_ALLOWED 临时 0→1（五十次，批准人=用户，范围=子树 super-writer——references/title-hits.md 移出+VERSION+CHANGELOG+MANIFEST 重算+锚点测试；wxgzh-pipeline 无锁条目不涉锁，producers 指令面与 tests 随档）；GZH_DESIGN_WRITE_ALLOWED 维持 0。授权登记行随 feat 落账；归位微档 77AC-F 另发。
- feat 提交：**待落**——executor 硬规则禁 commit（改动留工作区），归主智能体验证后提交推送；relock 链（#112/R93/装机侧同步/装机侧生产模拟/relock 后回归）随之执行（见 §5 命令清单）。
- 用户裁决日期：2026-09-10（77AB-F 补记②已预告本档，流程内机制修复）。

## 1. 证据背景

- 77AB 实战：relock media 首跑被 doctor gate 拒——锁基线 sw root bcd7d526… vs 装机侧 46e373c1…，漂移源=装机侧 references/title-hits.md 被 m9coc1 生产 RUN 追加一行（源码侧 root==锁基线，dry-run 实证）。executor 回流处置合法（fail-closed 下唯一正路）但不可持续——每次生产发文都会重演。
- 方案权衡（审核方已侦察）：EXCLUDE_FILES 按文件名豁免系锁校验判定面改动，安全敏感面不轻易扩（已否决）；77R 同族先例（ai-tone-calibration.jsonl 生产累积数据居 pipeline audit/quality/ 无锁面）语义更干净——生产数据本不属于 skill 静态资源面。取后者物理移位。

## 2. 任务 0 坐实摘录（存档）

- 引用点三处现行原文：
  - producers.py:73（改前）：`AGENT_INSTRUCTIONS["super_writer"] += "77AA/OBS-377:发文后将本篇选定标题追入 references/title-hits.md 台账（日期/RUN_ID/标题/组/五维分/风险标记/表现回填位,验证状态=待回填;轻义务,不阻断流水线）。"`
  - tests/test_hf77aa_title_patterns.py:14-17（改前）：`REF_DIR = Path(__file__).resolve().parents[1] / "references"`；`HITS = (REF_DIR / "title-hits.md").read_text(encoding="utf-8")`；另 :100 `assert "title-hits.md" in instr`（改后仍过，指令句含新路径）。
  - 77AA 档文 obs377:4/:23 路径表述（references/title-hits.md）——历史档文记录当时事实，不改；同性质历史行（obs-ledger OBS-377 行/口径 93/77AB-F 补记/sw CHANGELOG 77AA 条目/lock history #110 reason）均系历史记录不动。
- ai-tone-calibration.jsonl 先例实证：audit/quality/ 下 106 行 JSONL 生产累积数据；装机侧同路径存在且与源码侧逐字节一致（cmp 实证）——audit/ 不在 zipping EXCLUDE_DIRS（{__pycache__,.git,.pytest_cache,.github,.temp,.pytest}），copy_tree 全量分发；TT3「audit 档案随技能分发」系用户风险裁决基线（obs-ledger 口径 91 后段，2026-09-02 裁决原文入 SECURITY.md §9⑥）。
- install.py 装机语义实证（install() :432-438）：每个技能 destination 整目录 move 至备份 → staging 新树 move 进位 → 成功后 finally rmtree(transaction) 销毁备份——**装机侧旧 references/title-hits.md 随整个旧目录消失，installer 清除，无需显式删除**。分发链唯一入口=relock --apply source-tree mode 内建 official installer（_build_install_bundle/_run_official_installer，先 relock 后安装）；standalone install.py 需源证明 HEAD==lock full_commit_sha，当前（HEAD af2069e≠lock b944486）本就不可跑。
- 台账数据双侧比对：title-hits.md 源码侧与装机侧逐字节一致（cmp 实证，恰 3bhpi2+m9coc1 两行）——无未回流生产数据，移位零丢失风险。

## 3. 实现（OBS-380）

- **移位**：`git mv skills/super-writer/references/title-hits.md skills/wxgzh-pipeline/audit/quality/title-hits.md`——纯重命名 0 增删（git diff --cached -M --stat 实证），3bhpi2 种子行+m9coc1 回流行逐字节保留；sw references/ 下无残留、无指针文件（防双真源）。
- **引用同步**：producers.py 77AA 句路径 references/→audit/quality/（措辞其余不动），sw 指令实测 2913≤3000（上限门 test_hf76r/test_hf77aa 双在册）；tests/test_hf77aa_title_patterns.py hits 锚改指 `parents[2]/"wxgzh-pipeline"/"audit"/"quality"/"title-hits.md"`（与该文件既有 producers import 路径同基）。
- **升版**：sw 0.4.21-rc2→**0.4.21-rc3**（VERSION：version/previous_version/hotfix_date 2026-09-10/hotfix_name 77AC/release_notes；CHANGELOG 新增 rc3 条目；MANIFEST.sha256 重算——references/ 少一文件 119→**118 条目**，check_manifest `OK: 118, FAIL: 0`；重算序=路径组件元组序（目录作前缀先于长名同胞文件），与 77AB 产物同序，diff 恰 4 行=CHANGELOG/VERSION/test_hf77aa 三 sha 变+title-hits 行删除）。
- **锁面清零论证**：移出后 title-hits.md 不在任何锁哈希面——sw root hash（不在树内）/runtime manifest（同）/装机侧 OBS_68 runtime 比对（audit/quality/**/*.md 报告类按 OBS-107 排除，.jsonl 同族文件不受此排除，.md 受——两者均无锁面）。

## 4. 验收五条实测结论

1. **唯一真身**：✓ title-hits.md 真身居 skills/wxgzh-pipeline/audit/quality/（m9coc1 行在册）；sw references/ 无残留（grep 零命中）。
2. **两处测试全绿**：✓ test_hf77aa_title_patterns.py 7 绿（新锚点路径）；sw 全套 1 failed/302 passed/2 skipped 与 HEAD 基线逐字同（1=既有 dist 环境红 test_dist_lite_exists_and_under_2000_hanzi，dist/ 缺构建产物，零新红）；pipeline upgrade_regression 实测仅 obs154×1 既有红+relock dry-run ×4 无变化+doctor PASS，与 HEAD 基线逐字同（obs304 钉子 261→262/119–380 随档后 test_hf76r 绿）。
3. **生产模拟**：✓（仓侧）——audit/quality/title-hits.md 追加测试行前后 compute_root_sha(sw) 完全一致（root 5061f494…/manifest 6444c081…/文件数 57 三不变），测试行已删、文件复原字节一致；**装机侧模拟待 relock 装机同步后补**（装机侧现仍旧布局，见 §5）。
4. **relock #112/R93/doctor 双侧/relock 后回归**：**待执行**——OBS-74 远端见证三步（a/b/c）在任何写操作前强制、无跳过开关（设计明文），relock 升版路径必须 --source-tree/--source-commit（经典模式只写 3 hash 字段、不写 skill_version）；executor 禁 commit 故见证 (b) 必拒，dry-run 实证原文：`relock: ERROR: 远端见证 (b) 未通过: 本地 --source-tree 缺少远端树中的文件: references/title-hits.md。升级前请先将改动 push 到远端。`（77AB 先例 relock #110 同法：先独立 commit b944486 并 push，再 --source-commit 见证）。
5. **落账与计数**：✓ OBS-380 落账；口径 95；唯一编号实测 `262 119 380 True`（119–380 连续无缺号）；R59 实测 main=21 partition_active=21 双差集空；obs304 钉子 261→262 随档；授权登记行（五十次）随 feat。

## 5. 如实登记：简报矛盾与 relock 链命令清单（归主智能体）

- **简报矛盾（如实登记，不扩案）**：任务 3 要求「relock sw（#112）…装机侧同步…生产模拟（装机侧）」，而回报要求末段「改动留工作区不 commit，主智能体验证后提交推送」。relock --apply 升版路径需 --source-tree/--source-commit 且远端见证 (a) commit 已 push (b) 远端树==本地树——无 commit 无以通过；executor 硬规则禁 commit，故 relock 链整段（#112/装机侧同步/装机侧生产模拟/R93/doctor 双侧 MATCH/relock 后回归）时序上只能在 commit+push 之后执行。77AB 先例 executor 自行 commit（b944486）后 relock；本档按简报末段口径移交主智能体。
- **命令清单（commit+push 后）**（repo=F:\AIXM\wxgzh-skills，env：WXGZH_PROJECT_ROOT=F:\AIXM\wxgzh，python -X utf8 + PYTHONUTF8=1）：
  1. `git push` 后取 feat 提交 sha；
  2. dry-run：`python -X utf8 scripts/relock.py --skill super-writer --source-tree F:\AIXM\wxgzh-skills --source-commit <feat_sha> --reason "77AC/OBS-380: title-hits 移出锁面 sw 0.4.21-rc3"`；
  3. `--apply` 同参数（内建 official installer 装机侧整目录换新——装机侧旧 references/title-hits.md 随旧目录消失；备份/history/doctor gate/冒烟随链）；
  4. R93：sha256(skills.lock.json) 新值写入 wxgzh_pipeline/observability.py REPO_LOCK_SHA256（同 commit 落锁，test_observability 钉子随动）并同步装机侧 observability.py → doctor 双侧 OBS_69 MATCH；
  5. 复核装机侧：sw references/ 无 title-hits.md、audit/quality/ 有（内容双侧一致）；
  6. 装机侧生产模拟（验收 3 补全）：装机侧 audit/quality/title-hits.md 追加测试行 → compute_root_sha(装机侧 sw) 不变 → 删行复原；
  7. 最终回归（77Y-F 新规，relock/锁同步后跑）：upgrade_regression 应只剩 obs154×1 既有红；doctor OBS_69/OBS_68 双侧 MATCH（OBS_68 现存 DIFF×2=8bfb0c1 两测试文件装机侧未同步残差，随 3 装机换新自愈）；
  8. docs 提交：锁链文件+R93+口径 95 relock 段补记；tag v2026.09.10-77ac + gh release create（归位微档 77AC-F 任务）。
- 附记：装机侧 OBS_68 基线残差×2（tests/test_hf76r.py+test_hf77ab_guard.py，8bfb0c1 审核方修复未同步装机侧）与 OBS_69 双侧 MATCH、doctor 双侧 PASS 为本档起点实测态，已在回归输出在案。

## 6. 基线链

`af2069e（77AB-F）→ <feat 77AC：git mv+引用同步+rc3 升版+MANIFEST+台账 OBS-380/口径 95/obs304 262+授权行（待主智能体 commit）> → <docs 77AC：relock #112+R93+补记（待）> → <77AC-F：RELOCK 1→0+归位+tag/release>`
