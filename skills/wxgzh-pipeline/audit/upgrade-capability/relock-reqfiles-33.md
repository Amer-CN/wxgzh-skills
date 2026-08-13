# 档 33 — relock required_files 能力扩展(relock-reqfiles-33)

日期:2026-08-02
状态:**停机上报(FAIL-STOP)** — 第 5 步沙箱演练 5d 与预期不符;已停止,未做任何自行修复。
工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(branch `dev/0.1.0-dev2`)

---

## 0. 结论摘要

- 【第一部分 能力扩展】与【第二部分 防漂移守卫】已实现并加测试,单元测试全部通过。
- 【第三部分 沙箱演练】5c 通过(exit 3、零写入);**5d 与预期不符**:带开关执行 --apply 时,
  写前门禁以 `media-enrichment: non-target skill hash_ok=false` 拒绝(exit 3、零写入),
  未能进入移除/写入路径。按指令「若第 5 步任一环节与预期不符,立即停机上报,不要调整实现去凑预期」停机。
- 根因(与本档代码无关,档 33 开始前已存在):**真实环境 FAIL_CLOSED** —
  `.agents\skills\media-enrichment` 安装树与 skills.lock.json 锁定值不一致
  (实算 root `0c2d676b…` ≠ lock `0d8aea21…`)。该不一致发生于 2026-08-01 23:52:38
  (档 31 的 PASS 提交 `52cf80f` 于 23:36:08 之后),属外部改动,本会话全程零写入 `.agents\skills`。
- 沙箱树是真实树的复制,因此把真实环境的 media-enrichment 失配一并带入沙箱,
  使 5d 的写前 doctor 出现「非目标 skill hash_ok=false」→ 按档 28/33 门禁语义正确拒绝。
- 未执行 5e/5f 与第四部分最终验收(需先恢复环境基线,由审核者裁决)。

---

## 第一部分 能力扩展(已实现)

### 1. relock.py 新增 `--allow-required-files-removal`(默认关闭)

- 开关关闭:行为与档 28/29 完全一致(required_files 永不触碰)。
- 开关开启时仅允许**移除**:
  - 移除候选 = lock `required_files` 中在安装树上**确实不存在**的条目,
    且不属于该 skill 的 lock 声明入口文件(`entrypoint` / `validator` /
    `render_entry` / `component_source`,任一命中即受保护,绝不移除)。
  - **严禁新增**:检测「lock 声明的入口文件存在于安装树、但未被 required_files 覆盖」,
    打印 `NOTE: … 需人工裁决 (relock 不会自动新增)`;dry-run 只报告(exit 0),
    `--apply` 拒绝执行(exit 2),零写入。
- 实现在 `build_rows()`(新增 `remove_required_files` / `uncovered_entries` 两个行字段)、
  `print_rows()`(打印移除候选与 NOTE)、`main()`(apply 前拒绝 uncovered)。

### 2. 写前门禁调整(档 28 分类基础上)

- `classify_gate()` 新增参数 `allow_required_files_removal` / `removable_req`:
  - 开关关闭:`entrypoints_ok=false` 仍归拒绝类(exit 3),维持现状。
  - 开关开启:目标 skill 的 `entrypoints_ok=false` 仅当 doctor 报告的
    `missing_files` **全部**落在「本次将移除的 required_files 条目」内时才放行;
    存在其他缺失(含受保护入口文件缺失)→ 拒绝。
  - 非目标 skill 的任何问题(含 hash 失配)→ 一律拒绝(exit 3)。
- 写入路径:对 `_HASH_FIELDS` 三个字段之外,仅当开关开启且存在移除候选时,
  从目标 skill 的 `required_files` 中移除对应条目;其余字段逐字不动。

### 3. 台账新字段与链路追溯判断

- `append_history()` 每条记录新增 `removed_required_files`(数组,未移除时为 `[]`)。
- **据实判断:该字段不参与档 28 的链路追溯。** 依据:
  `_find_upgrade_chain()`(receipts.py)的匹配键只有 `skill` / `old_root_sha256` /
  `new_root_sha256` / `entry_id`;required_files 移除必然改变 runtime 文件集,
  root sha 的旧→新链路已完整刻画该变化;再为 `removed_required_files` 增加匹配条件
  只会引入新的严格性维度且无追溯增益。该字段仅作审计信息。receipts.py 未做任何修改。

---

## 第二部分 防漂移守卫(已实现)

- `upgrade_regression.py` 新增步骤 `step_validate_gzh_consistency()`:
  比对 Pipeline 侧 `scripts/validate_gzh_html.py` 与 gzh-design 安装侧同名文件的 sha256。
- 本档执行时 Pipeline 侧**不存在**该文件 → 打印
  `validate_gzh_html cross-side: SKIP — Pipeline 侧尚不存在 scripts/validate_gzh_html.py (P2 未落地;防漂移守卫将在 P2 落地后自动生效)`,
  按通过处理(不得因缺失误判为通过);P2 落地后自动生效,不一致即 FAIL。
- 实测输出见第 8 节(正确 SKIP)。

---

## 第三部分 沙箱演练(5a-5c 完成;5d 停机)

### 5a/5b 沙箱构造

- 沙箱:`%TEMP%\relock33-sandbox`
  - `skills\` = `F:\AIXM\wxgzh\.agents\skills` 整树复制(含四个被锁 skill 与 aihot)
  - `skills.lock.json` = 仓库根真实 lock 复制(sha256 `a9e07ef4…`)
- 模拟迁出:删除沙箱内 `gzh-design\scripts\publish_wechat_draft.py` 与
  `gzh-design\requirements.txt`。
- 实算(沙箱 gzh-design):
  - root `9a8cd7f5…` → `623d54f3…`(CHANGED)
  - manifest `ced84143…` → `c33c1738…`(CHANGED)
  - file_count 76 → 74(CHANGED)
- 事实注记:真实 lock 的 gzh-design `required_files` 只含
  `scripts/render_article.py`、`scripts/validate_gzh_html.py`、
  `scripts/publish_wechat_draft.py`、`scripts/generate_hammer_upgrade_samples.py`
  —— **`requirements.txt` 不在 required_files 内**。因此迁移模拟中
  「required_files 恰好移除」的对象是 1 项(`scripts/publish_wechat_draft.py`);
  `requirements.txt` 的迁出体现在 manifest/file_count(76→74)与哈希上。
  指令 5d 所述「移除这两项」在真实 lock 结构下不成立,此为本档记录的事实。

### 5c 不带开关 --apply(结果符合预期)

- 命令:`relock.py --skill gzh-design --reason "档33 沙箱演练(迁移模拟,无开关)" --apply --skip-regression --project-root F:\AIXM\wxgzh --skills-home <沙箱>\skills --lock-path <沙箱>\skills.lock.json --history-path <沙箱>\skills.lock.history.json --backup-dir <沙箱>\backups`
- 结果:**EXIT=3**,拒绝信息:
  `relock: ERROR: doctor gate refused --apply: media-enrichment: non-target skill hash_ok=false (only the named target may be re-locked); gzh-design: entrypoints_ok=false`
- 零写入验证:沙箱 lock sha 仍 `a9e07ef4…`;history 不存在;backups 目录不存在。
- 注:预期拒绝原因本应仅为 `gzh-design: entrypoints_ok=false`;实际还带上了
  `media-enrichment: non-target skill hash_ok=false`(真实环境既有失配被沙箱继承),
  退出码与零写入行为符合预期。

### 5d 带开关 --apply(与预期不符 → 停机)

- 命令:同上加 `--allow-required-files-removal`
- 结果:**EXIT=3**,拒绝信息:
  `relock: ERROR: doctor gate refused --apply: media-enrichment: non-target skill hash_ok=false (only the named target may be re-locked)`
- 零写入验证:沙箱 lock sha 仍 `a9e07ef4…`;history 不存在;backups 目录不存在。
- 预期应为:门禁放行 → 写 lock(required_files 移除 publish 条目、三哈希更新、
  file_count=74)→ 台账 +1 条(removed_required_files 含且仅含该条目)→ 写后 doctor PASS
  → 二次 dry-run 无变化。实际被既有非目标失配阻断。
- 门禁行为本身符合档 28/33 语义(非目标问题 → 拒绝);阻塞来自沙箱继承的真实环境失配。
- **按指令停机**:未调整实现、未绕过门禁、未在沙箱内“修复” media-enrichment 副本去凑预期,
  未执行 5e/5f。

### 5e/5f(未执行)

因 5d 停机,三态演练与回滚演练未进行;实现路径已由单元测试覆盖
(`test_relock_reqfiles.py` 含回滚逐字还原用例),真实演练待环境基线恢复后补做。

---

## 第六部分要求的测试(已加,全部通过)

新增 `tests/test_relock_reqfiles.py`,6 项:

| 测试 | 覆盖 | 结果 |
|---|---|---|
| `test_switch_off_refuses_entrypoints_missing` | 开关默认关闭时的拒绝行为(exit 3、零写入) | PASS |
| `test_switch_on_removes_only_missing_entries` | 仅移除缺失条目、不新增;三哈希更新;台账字段 | PASS |
| `test_switch_on_refuses_protected_entry_missing` | 受保护入口文件缺失 → 拒绝(其他原因) | PASS |
| `test_uncovered_entry_reports_and_refuses_apply` | 未覆盖新入口:dry-run 报告、apply 拒绝(exit 2)零写入 | PASS |
| `test_ledger_field_empty_when_no_removal` | 无移除时台账 `removed_required_files == []` | PASS |
| `test_rollback_restores_required_files` | 写后 doctor FAIL → lock(含 required_files)与台账逐字还原 | PASS |

执行:`python -m pytest tests/test_relock_reqfiles.py tests/test_relock.py -q` → 全部通过;
回归套件内全量 pytest 亦 PASS(见第 8 节,排除清单仍为 1 项)。

---

## 第四部分 验证(部分完成,其余被停机条件阻断)

### 7. 沙箱清理与真实环境未受污染证明

- 沙箱 `%TEMP%\relock33-sandbox` 已彻底删除(rmdir 后 Test-Path 确认不存在)。
- 真实 `.agents\skills`、真实 `skills.lock.json`、真实台账在档 33 执行前后比对
  (前置快照 `relock33-before.json` vs 后置复算):
  - `skills.lock.json` sha256:前后均 `a9e07ef42017cff225158466213253baf1155f34a7c2f1bdaf62a87dbbc751d6`
  - `skills.lock.history.json`:前后均不存在
  - 四锁 skill root/manifest/file_count:super-writer / zh-human-writing /
    media-enrichment / gzh-design 全部前后一致(逐字未变)
  - 结论:**三者本档执行前后逐字未变**;本档对 `.agents\skills` 只有读操作。

### 8. upgrade_regression.py 输出(完整,截尾部)

```
upgrade_regression: project_root=F:\AIXM\wxgzh
pytest: PASS (1 explicit deselects)
relock dry-run x4: FAIL
  super-writer: status: 无变化 OK
  zh-human-writing: status: 无变化 OK
  media-enrichment: status: CHANGED FAIL
  gzh-design: status: 无变化 OK
doctor --require-wechat: FAIL
validate_gzh_html cross-side: SKIP — Pipeline 侧尚不存在 scripts/validate_gzh_html.py (P2 未落地;防漂移守卫将在 P2 落地后自动生效)
upgrade_regression: FAILED
```

- 排除清单**仍为 1 项**(portable installer,与档 30/31 一致),未被扩大。
- FAIL 点全部来自既有环境失配(media-enrichment dry-run CHANGED、doctor FAIL),
  与本档改动无关;pytest 全量(含本档新增 6 项)通过。

### 9. 真实 dry-run 四锁(受停机条件阻断,给出实际状态)

- super-writer / zh-human-writing / gzh-design:无变化
- **media-enrichment:CHANGED**(既有失配)——与「必须全部无变化」不符,即停机条件之一。
- 依据指令未对真实环境做任何写入或修复。

---

## 环境取证(停机根因,档 33 之前已存在)

### 时间线(均为外部改动,非本会话所为)

| 时间 | 事件 |
|---|---|
| 2026-08-01 23:36:08 | 档 31 提交 `52cf80f`(其报告记录:doctor PASS、四锁 dry-run 无变化、树快照 `27bcace3…`) |
| 2026-08-01 23:52:38 | `.agents\skills\media-enrichment\scripts\run_media_enrichment.py` 被修改 |
| 2026-08-01 23:52:56 | `.agents\skills\wxgzh-pipeline\skills.lock.json` 副本、`.install-receipts\media-enrichment.json` 被重写 |
| 2026-08-01 23:53:06 | media-enrichment `.pytest_cache` 生成(安装目录内跑过 pytest) |
| 2026-08-02 00:11:44 | `.agents\skills\wxgzh-pipeline\wxgzh_pipeline\producers.py` 被修改 |
| 2026-08-02 00:12-00:13 | wxgzh-pipeline 安装副本 `.pytest_cache` 生成 |
| 2026-08-02(本档) | 档 33 开始,前置快照即已 FAIL_CLOSED |

### 失配内容(安装树 vs 锁定 commit)

- 对照源:`F:\AIXM\wxgzh\repos\media-enrichment`(档 31 建立的 sibling,HEAD=`cedf92ca45b0cdb7e010d489e9da67dd28ef6e59` == lock `full_commit_sha`)。
- 57 个 runtime 文件中恰有 2 个不一致:
  - `scripts/run_media_enrichment.py`:安装 `afc2e5a5…` vs 锁定 `824de0a4…`
  - `src/media_enrichment/uploader.py`:安装 `31ff33f6…` vs 锁定 `b15c0d61…`
- 该两个文件与档 31 勘察记录(「run_media_enrichment.py/uploader.py 不一致」)同名,
  即安装树长期携带本地热修;本次(23:52:38)热修再次改写后与 lock 彻底失配。
- 安装侧 root 实算 `0c2d676b…` ≠ lock `0d8aea21…` → `hash_ok=false` → doctor FAIL_CLOSED。
- `.temp` 现有 5 个 media-enrichment 构建目录中均无与安装侧完全一致的对应文件
  (dev5/dev6/dev6-hotfix1/dev7-hotfix1 无同路径文件;`media-enrichment-oss-20260727T1547`
  两文件均与安装侧不同)——即当前安装侧内容不匹配任何可定位的历史构建,来源无法判定。

### 本会话无责证明

- 档 33 前置快照(任何沙箱操作之前)即显示 media-enrichment root=`0c2d676b…`;
- 档 32(只读)与档 33 均未对 `.agents\skills` 发出任何写操作(仅读取/复制);
- 仓库 `git status` 仅含本档 3 个文件(relock.py / upgrade_regression.py /
  test_relock_reqfiles.py),无其他改动。

---

## 风险与建议(事实,不替决策)

- 恢复路径(需审核者裁决):核实安装侧 run_media_enrichment.py/uploader.py 热修内容
  是否应被正式接受——若接受:走正式安装流程 + relock --apply(media-enrichment 为 target)
  建立台账链路;若拒绝:用锁定 commit 重装恢复基线。两者均触碰 `.agents\skills` 或 lock,
  超出档 33 授权,故本档未执行。
- 环境恢复后,档 33 的 5d/5e/5f 与第四部分验收即可直接补跑
  (实现与测试已就绪;5d 的「required_files 恰好移除」按真实 lock 应为 1 项,
  见第 5a/5b 节事实注记)。
- 安装副本 `.agents\skills\wxgzh-pipeline` 的 skills.lock.json 副本与 producers.py
  亦被外部改动(与仓库不同步),虽不在四锁 hash 范围,建议一并纳入审核关注。
- 台账首条真实记录风险(档 32 已述,本档再次确认):真实 `skills.lock.history.json`
  尚不存在;任何先于 P2 的 root 变化都会影响两篇历史 RUN receipt 的三态判定,
  relock --apply 的首条记录 old_root 必须是当前锁值。
*** End Patch