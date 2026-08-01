# 档 27 — P0-1 一键重锁工具(relock.py)实现报告

日期:2026-08-01
范围:Pipeline 侧新增 `scripts/relock.py` + `tests/test_relock.py` + 升级台账定义。
未触碰:任何被锁 skill、skills.lock.json(仅 dry-run 读取)、已有 receipt、微信接口、完整 Pipeline;未删除任何文件。

## 1. 实现说明

### 新增文件
- `scripts/relock.py` — 一键重锁工具(dry-run 为默认行为)
- `tests/test_relock.py` — 11 个 pytest 用例
- 台账文件 `skills.lock.history.json` 由工具在 `--apply` 时按需创建(本轮未创建)

### 用法
```
python scripts\relock.py --skill <name> --reason "<变更原因>" [--apply]
python scripts\relock.py --all --reason "<变更原因>" [--apply]
```
不带 `--apply` 时只计算/比对/报告,零写入。

### 哈希复用(第 2 项)
- `wxgzh_pipeline.skill_discovery.compute_root_sha(root) -> (sha256|None, int)`:
  签名与用途匹配,直接复用,返回的第二个值即 runtime file_count。
- `compute_runtime_manifest_sha(root) -> (sha256|None, list[str])`:
  签名匹配,直接复用(第二个值 rels 用于 file_count 交叉核对)。
- `_file_sha`:被 `compute_root_sha`/`compute_runtime_manifest_sha` 内部调用,
  属于传递复用;relock 不直接调用它。
- 三个函数本身**零改动**,签名无需适配。

### 行为实现(第 3 项)
- a. 对目标 skill 的已安装目录实算 root_sha / manifest sha / file_count。
- b. 与 skills.lock.json 当前值逐字段比对,输出 `旧 -> 新` + `(CHANGED)` 或 `无变化`。
- c. `--apply` 时先按原始字节备份到
  `audit/upgrade-capability/lock-backups/skills.lock.<UTC时间戳>.json`,再写入新值。
  写入用与现有文件相同的序列化(CRLF + 尾换行 + indent=2,已验证可逐字复现),
  保证成功路径 diff 最小。
- d. `--apply` 时向台账追加记录(每条 = 一个变更 skill)。
- e. `--apply` 时先后跑两次真实 doctor(子进程 `scripts/doctor.py --project-root … --require-wechat`):
  写前门禁 + 写后复验;写后 FAIL 则从字节级快照还原 skills.lock.json 与台账
  (台账文件为本轮新建时直接删除),保证失败后状态与执行前逐字一致,退出码 4。
  还原本身失败时退出码 5 并大声告警(绝不假装成功)。

### 台账格式(第 4 项)
`skills.lock.history.json`(仓库根,JSON 数组),每条记录:
`entry_id / skill / old_root_sha256 / new_root_sha256 / old_manifest_sha256 /
new_manifest_sha256 / old_file_count / new_file_count / reason / recorded_at(UTC ISO-8601)
/ doctor_result(PASS|ROLLED_BACK)`。
- 只追加;既有记录永不改写。回滚只删除本轮刚追加的记录(或本轮新建的整个文件)。
- 例外兜底:若回滚时删除/还原失败,把本轮刚追加记录的 `doctor_result` 改为
  `ROLLED_BACK` 并退出 5(保证台账不留下虚假 PASS)。

### 安全约束(第 5 项)
- `--reason` 缺失(argparse 拒绝,退出 2)或全空白(显式校验,退出 2)均拒绝执行。
- 只读已安装目录;只写 skills.lock.json、台账、备份文件;代码路径中无任何对
  被锁 skill 目录的写操作。
- `--apply` 前置 doctor 门禁:FAIL_CLOSED 时拒绝执行且零写入(退出 3)。
- aihot(agent_invoked_skill,无树哈希)拒绝单独 re-lock;`--all` 时跳过并提示。
- 目标 skill 目录缺失、未知 skill 名、lock/台账损坏均 fail-closed(退出 2)。

### 可测试性钩子
`--project-root / --skills-home / --lock-path / --history-path / --backup-dir`
默认值与 doctor 一致(env `WXGZH_PROJECT_ROOT`/`AGENT_SKILLS_HOME` 生效),仅用于
隔离测试;生产路径始终指向仓库根。

## 2. 测试结果

`python -m pytest tests\test_relock.py -q` → **11 passed**。

| 用例 | 覆盖 |
|---|---|
| test_dry_run_writes_nothing | a. dry-run 零写入(全树字节快照前后一致) |
| test_apply_doctor_fail_rolls_back | b. 既有台账场景:doctor 写后 FAIL → lock 与台账逐字还原,既有记录不动 |
| test_apply_doctor_fail_rolls_back_created_history | b'. 本轮新建台账场景 → 整个文件被删除 |
| test_reason_missing_refused | c. --reason 缺失 → argparse 退出 2 |
| test_reason_empty_refused | c'. --reason 全空白 → 退出 2,零写入 |
| test_apply_ledger_format | d. 台账格式逐字段断言;无变化 apply 为 no-op;二次变更 apply 只追加不改旧记录 |
| test_apply_refused_when_doctor_fail_closed | 门禁:前置 doctor FAIL → 退出 3,零写入 |
| test_apply_no_change_is_noop | 无变化 --apply → 不备份/不写/不记录,退出 0 |
| test_unknown_skill_refused | 未知 skill → 退出 2 |
| test_aihot_refused | aihot 单独 re-lock → 退出 2 |
| test_all_dry_run_skips_aihot | --all dry-run 跳过 aihot,零写入 |

全量套件 `python -m pytest -q` 中 5 个失败均为预存在的全流程/live 握手类测试
(`test_hotfix7_live_handshake.py::test_cross_repo_missing_full_mode_artifact_fails`、
`test_pipeline.py` 的 02/08/10/14),需要真实 agent 握手或完整 live 环境,与本次
新增文件无关(新增两个文件均为未跟踪新文件,不参与这些测试路径);其余全部通过。

## 3. 验收实测:四 skill dry-run(原样输出)

环境:`AGENT_SKILLS_HOME` 置空、`WXGZH_PROJECT_ROOT=F:\AIXM\wxgzh`,从仓库副本执行。

### super-writer
```
=== super-writer ===
installed_dir: F:\AIXM\wxgzh\.agents\skills\super-writer
skill_root_sha256: 46a00a1bcdd5eeafae1ce6723241f97a6c1cd92f14f7baf8dc3625c9aed3018a -> 46a00a1bcdd5eeafae1ce6723241f97a6c1cd92f14f7baf8dc3625c9aed3018a
runtime_manifest_sha256: 4e5ed52520ec123378543271143489f2842b24fc7109fdbc2e15c0ee02d5a8b6 -> 4e5ed52520ec123378543271143489f2842b24fc7109fdbc2e15c0ee02d5a8b6
runtime_file_count: 50 -> 50
status: 无变化

dry-run: 1 skill(s) checked, 无变化 — nothing to write
```

### zh-human-writing
```
=== zh-human-writing ===
installed_dir: F:\AIXM\wxgzh\.agents\skills\zh-human-writing
skill_root_sha256: 18491b361060a28d5eaf228f58b9b75e6ebde697eaa1149573bf468e0daea786 -> 18491b361060a28d5eaf228f58b9b75e6ebde697eaa1149573bf468e0daea786
runtime_manifest_sha256: 022e62c54a4e4d544e3ecc7b2ce4ff8484ccb6927009db236db619286bf076f6 -> 022e62c54a4e4d544e3ecc7b2ce4ff8484ccb6927009db236db619286bf076f6
runtime_file_count: 53 -> 53
status: 无变化

dry-run: 1 skill(s) checked, 无变化 — nothing to write
```

### media-enrichment
```
=== media-enrichment ===
installed_dir: F:\AIXM\wxgzh\.agents\skills\media-enrichment
skill_root_sha256: 0d8aea2169cec17c4e9f95af66b6b4da3c532554a0a316fe3fb604bd0b7ab3a3 -> 0d8aea2169cec17c4e9f95af66b6b4da3c532554a0a316fe3fb604bd0b7ab3a3
runtime_manifest_sha256: 172aa1b8082c6bb80822e56e201732ba5a118c6a53d7472f34b911f4a891e996 -> 172aa1b8082c6bb80822e56e201732ba5a118c6a53d7472f34b911f4a891e996
runtime_file_count: 57 -> 57
status: 无变化

dry-run: 1 skill(s) checked, 无变化 — nothing to write
```

### gzh-design
```
=== gzh-design ===
installed_dir: F:\AIXM\wxgzh\.agents\skills\gzh-design
skill_root_sha256: 9a8cd7f548c2186f789a5e24235001308fc6a868e0f57d74fc06c8919b4ff79b -> 9a8cd7f548c2186f789a5e24235001308fc6a868e0f57d74fc06c8919b4ff79b
runtime_manifest_sha256: ced841439195453497e67a63186823f60eee7155b9de472e936c3d4d767e33b2 -> ced841439195453497e67a63186823f60eee7155b9de472e936c3d4d767e33b2
runtime_file_count: 76 -> 76
status: 无变化

dry-run: 1 skill(s) checked, 无变化 — nothing to write
```

验收结论:四个 skill 的 root_sha / manifest_sha / file_count 与 skills.lock.json
现有值**逐字相同,全部报告「无变化」**;未出现任何差异,无需停机。dry-run 后
`git status` 无任何新增写入(仅本次新增的两个源码文件)。

## 4. 风险点

1. **前置 doctor 门禁与 re-lock 场景存在张力**:`--apply` 要求写前 doctor PASS,
   而典型的 re-lock 场景(如 OBS-42/58:改完被锁 skill 后 lock 已失配)doctor 恰恰
   处于 FAIL。按档 27 要求原样实现了门禁;若后续需要「已知差异、受控重锁」路径,
   需审核者另行授权 `--force` 类开关,本轮未实现。
2. **doctor 复验路径固定为仓库根 skills.lock.json**:`--lock-path` 等覆盖参数仅
   供测试隔离;生产 apply 时 doctor 读的是仓库真实 lock,两者天然一致。若将来
   lock 路径可配置,需同步打通 doctor。
3. **备份文件留存策略未定义**:每次 apply 在
   `audit/upgrade-capability/lock-backups/` 留一份历史 lock,长期会累积;建议日后
   纳入归档/清理规则(本轮不删任何文件)。
4. **写入中途崩溃的兜底**:lock 写入与台账追加之间的 OSError 会走同一回滚路径;
   若还原本身失败,工具退出 5 并明示状态可能不一致,不自动重试——人工介入。
5. **控制台编码**:中文输出在 GBK 控制台可能显示乱码(仅显示层,文件均为 UTF-8)。
6. **entry_id/备份时间戳为秒级 + uuid8 后缀**,并发同秒执行也不会撞号。
7. **台账为仓库新文件**,首条记录在首次真实 apply 时产生;本轮仅 dry-run,台账
   未创建,skills.lock.json 未动。
