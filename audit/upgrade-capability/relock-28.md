# 档 28 — 修补 relock 门禁 + 序列化保真测试 + P0-2 三态判定

日期:2026-08-01
范围:Pipeline 侧。未触碰:被锁 skill、skills.lock.json(仅 dry-run 读取)、
已有 receipt、微信接口、完整 Pipeline;未删除任何文件。

## 1. 门禁分类实现说明(Part 1)

### 改动
`scripts/relock.py` 新增 `classify_gate(doctor_passed, doctor_output, target_skills)`,
`--apply` 写前门禁从「非 PASS 即拒绝」改为按 doctor 报告 JSON 分类:

| 情形 | 判定 | 结果 |
|---|---|---|
| doctor exit 0(PASS) | — | 放行 |
| 报告不可解析 / 非对象 / FAIL_CLOSED != true | 视为环境性问题 | 拒绝,退出 3 |
| project_writable=false / wechat_config_present=false / LIVE_PIPELINE_ALLOWED=false | 环境性问题(1a) | 拒绝,退出 3 |
| 任一 skill(含目标)exists=false(目录缺失) | 环境性问题(1a) | 拒绝,退出 3 |
| 任一 skill entrypoints_ok=false 或 missing_files 非空 | 环境性问题(1a) | 拒绝,退出 3 |
| 非目标 skill 的 hash_ok=false 或 version_ok=false | 越权重锁(1c) | 拒绝,退出 3 |
| 目标 skill 健康(无 hash/version 失配)而 doctor 失败 | 无法归因 | 拒绝,退出 3 |
| 目标 skill 的 hash_ok=false 或 version_ok=false,且其余全部健康 | 正是 re-lock 要解决的态(1b) | **放行** |

- 放行时打印 `doctor gate: allowed — target hash/version mismatch only (re-lockable state)`。
- 写后 doctor 复验维持不变:必须 PASS,否则字节级回滚(退出 4)。
- 说明:doctor 报告的 `FAIL_CLOSED` 是聚合标志(doctor 失败时恒为 true),
  因此 1a 中的「FAIL_CLOSED=true」按原因分类执行——环境性/越权原因即拒绝,
  仅目标 hash/version 失配时放行;报告缺失或不可解析一律拒绝(不猜)。

### 测试(新增 3 个)
- `test_apply_allowed_when_only_target_mismatch` — 仅目标失配 → 放行、写入、台账 PASS。
- `test_apply_refused_when_non_target_mismatch` — 非目标失配 → 拒绝,零写入。
- `test_gate_refused_on_unparsable_doctor_output` — 报告不可解析 → 拒绝,零写入。
- 既有 `test_apply_refused_when_doctor_fail_closed` 改为环境性失败(凭据缺失)场景。

## 2. 序列化保真测试(Part 2)

### 新增测试(2 个)
- `test_serialize_lock_reproduces_real_lock_bytes` — 只读属性测试:对**真实**
  skills.lock.json 执行 load→dump,断言与原始字节逐字相同(CRLF + 尾换行)。
- `test_full_write_roundtrip_byte_fidelity` — fixture 结构取自真实 skills.lock.json
  (含 aihot 非 ASCII 字段、CRLF、尾换行),执行「改一个值再改回原值」的完整
  `--apply` 写入路径两次,断言最终字节与初始 fixture 逐字相同。

### 测试抓出的真实缺陷(已在实现中修复)
- 原 `_serialize_lock` 先做 `\n→\r\n` 替换、后补尾换行,导致尾行是 LF、文件混行尾。
- 更严重:`--apply` 写入用 `Path.write_text`——Windows 上它会把文本中的 `\n`
  再次翻译为 `\r\n`,使 CRLF 模板变成 `\r\r\n`(双回车)。该缺陷自档 27 就存在,
  只是此前测试只比较解析后 JSON。修复:lock 与台账写入全部改为 `write_bytes`
  显式编码,不做换行翻译。
- 修后:round-trip 两次写入后字节与原始逐字相同(测试通过)。

## 3. P0-2 三态判定(Part 3)

### 改动
`wxgzh_pipeline/receipts.py`:
- 新增 `_history_path()`:台账固定为仓库根 `skills.lock.history.json`。
- 新增 `_find_upgrade_chain(skill_name, receipt_root, current_root)`:
  台账逐条要求 dict + 合法 `old_root_sha256/new_root_sha256/entry_id`,skill 名
  必须等于 receipt 的 skill_name;DFS 从 receipt 值链到当前值,允许多跳,
  按路径防环;任一跳缺失、台账缺失/为空/非数组/JSON 非法 → 一律 `None`(TAMPERED)。
- `verify_receipt()` L222-228 附近改为三态:
  - 一致 → `skill_root_state="OK"`,正常续跑
  - 不一致 + 完整台账链 → `"SKILL_UPGRADED"` + `upgrade_entry_ids`(命中记录按序),
    不加入 mismatch(不阻断)
  - 不一致 + 无链 → `"TAMPERED"`,维持原有严格 FAIL
- 返回签名扩展为 `(ok, mism, extra)`,`extra={"skill_root_state", "upgrade_entry_ids"}`。

调用点全部更新(3 元解包):
- `orchestrator.py` resume:`SKILL_UPGRADED` 时 ok=True 但不计入 kept,
  从该阶段起整体标为「需重跑」(broken=该阶段,`verify_reports` 记录
  `skill_root_state` 与 `upgrade_entry_ids`,输出 `invalidated_from`)。
- `orchestrator.py` wechat_draft 门禁、`contracts.py` must_run_after、
  `scripts/run_cross_repo_integration.py`、`tests/test_dev2_fake_live.py`、
  `tests/test_hotfix2_receipt_tamper.py` 均按 3 元解包更新。

### 测试(新增 11 个,`tests/test_p0_2_three_state.py`)
- 三态各一例:OK / SKILL_UPGRADED(单跳)/ TAMPERED(无链)。
- 多跳链命中:`old→mid→cur`,entry_ids=[e1,e2]。
- 链中断:mid→other(当前不可达)→ TAMPERED。
- 台账缺失 / 为空 / JSON 非法 / 非数组 → 一律 TAMPERED。
- 台账被篡改成任意值(错 skill、错 old、反向、非 dict、坏字段)→ 不得洗成
  SKILL_UPGRADED。
- 纯环(无法到达当前值)→ TAMPERED;真实链旁存在无关环记录 → 仍判 SKILL_UPGRADED
  (任意多余记录不得破坏真实完整链)。

### 结果
`python -m pytest tests\test_relock.py tests\test_p0_2_three_state.py -q`
→ **27 passed**(relock 16 + 三态 11)。

全量套件:本工作树 8 个失败,均为环境依赖(缺 sibling 仓库
`F:\AIXM\wxgzh\repos\media-enrichment`、缺 `WXGZH_REAL_SKILLS_HOME` 等 env);
在干净 HEAD(fa23a2a)worktree 复跑为 12 个失败 —— 本档改动**零回归**。

## 4. 四 skill dry-run 复验(第 8 项,原样输出)

环境:`AGENT_SKILLS_HOME` 置空、`WXGZH_PROJECT_ROOT=F:\AIXM\wxgzh`。

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

结论:四个 skill 全部「无变化」;doctor 复验 `skills_locked_ok=true`、
四 skill `hash_ok=true`、`FAIL_CLOSED=false`、`doctor=PASS` —— 本档改动未污染环境。

## 5. 仍存在的风险点

1. **台账信任边界**:三态判定信任 skills.lock.history.json 的内容;台账的
   完整性由 relock 的只追加写入 + git 历史保证。若攻击者同时伪造一条
   old→current 的合法记录,系统无法区分(超出本档范围;可后续用
   entry_id 签名/只读源校验加固)。
2. **SKILL_UPGRADED 的 resume 语义**:从升级点起整段「需重跑」;若升级发生在
   wechat_draft(复用 gzh-design),已创建草稿的 RUN 会被重置 `draft_created`
   并重跑该阶段——按「需重跑」指令实现,但重跑前请人工确认草稿箱状态。
3. **门禁归因依赖 doctor 报告字段**:若未来 doctor 增加新的失败维度而
   classify_gate 未覆盖,会落到「unclassified reason」拒绝(安全侧),
   需要随 doctor 一起维护。
4. **全量套件环境失败**:8 个失败(本树)/12 个(干净 HEAD)均为缺少
   media-enrichment sibling 仓库与 `WXGZH_REAL_*` env 所致,与代码无关;
   CI 化时需提供这些环境。
5. **verify_receipt 签名变更**:3 元返回已同步全部 5 处调用点;第三方/未来代码
   若按 2 元解包会报错——这是有意的破坏性变更,已在报告中声明。
6. **序列化保真依赖 json 确定性**:`json.dumps(ensure_ascii=False, indent=2)`
   对当前 lock 逐字复现(含 aihot 非 ASCII 字段);若将来 lock 中出现
   ensure_ascii 敏感内容或不同格式,保真测试会第一时间失败。
