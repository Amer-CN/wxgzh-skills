# 档 29 —— P1:relock --apply 沙箱全链演练 + 升级回归自检

- 执行日期:2026-08-01(UTC+8)
- 工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(branch `dev/0.1.0-dev2`)
- 沙箱:`%TEMP%\wxgzh-relock-sandbox-20260801`(演练结束后已彻底删除)
- 遵守:只改 Pipeline 侧;未触碰 `F:\AIXM\wxgzh\.agents\skills` 任何文件、未修改仓库根真实 `skills.lock.json`、未修改被锁 skill、未修改任何已有 receipt、未调微信接口、未跑完整 Pipeline;所有写入均发生在沙箱目录内。

## 第一部分 沙箱全链演练

### 1. 沙箱构造

- `Copy-Item` 只读复制 `.agents\skills` 整树 → `<沙箱>\skills`(含 `.install-receipts`,其内容被 hash 算法排除,不影响一致性)
- 复制仓库根 `skills.lock.json` → `<沙箱>\skills.lock.json`,两侧 sha256 一致:`A9E07EF42017CFF225158466213253BAF1155F34A7C2F1BDAF62A87DBBC751D6`
- 台账/备份目录初始不存在
- 沙箱基线 dry-run(改动前,`--skills-home/--lock-path/--history-path/--backup-dir` 全部指向沙箱,`--project-root F:\AIXM\wxgzh`):

```
relock: note: skipping aihot (agent-invoked skill, no tree hashes)
=== super-writer ===
... 三字段全部一致
status: 无变化
=== zh-human-writing ===
status: 无变化
=== media-enrichment ===
status: 无变化
=== gzh-design ===
... 三字段全部一致
status: 无变化
dry-run: 4 skill(s) checked, 无变化 — nothing to write
EXIT=0
```

### 2. 制造真实 skill 变更

- 选择:gzh-design 的 B 类(纯排版、非发布相关)文件 `references/*.md`。
- 说明(事实):`runtime_manifest_sha256` 哈希的是运行时文件**清单**(相对路径列表),对已有文件只改内容不会改变 manifest sha 与 file_count;为满足 3d「三个哈希字段均更新」的预期,采用**新增一个**单行注释的 `references/zz-handover-note.md`(体量最小、非发布相关的 B 类变更),使 root/manifest/count 三个字段全部真实变化。
- 变更前:文件不存在(记录为 absent);变更后文件 sha256 = `c95ca8622f8004f860aa6e26e0aaf135ca550336dd5950c319de5ffe68ce383a`,内容:`<!-- handover drill 档29: single-line sandbox addition (B-class, non-publish) -->`

### 3. 全链 --apply(3a–3g)

#### 3a. 变更后 dry-run(原样输出,已省略三个无变化 skill 的明细)

```
=== gzh-design ===
installed_dir: C:\Users\Admin\AppData\Local\Temp\wxgzh-relock-sandbox-20260801\skills\gzh-design
skill_root_sha256: 9a8cd7f548c2186f789a5e24235001308fc6a868e0f57d74fc06c8919b4ff79b -> 6c38425dfb786155127b40f62e79fc4631d0273f217cc735a7d197aed9f75ec6  (CHANGED)
runtime_manifest_sha256: ced841439195453497e67a63186823f60eee7155b9de472e936c3d4d767e33b2 -> 9d8599f46907ab39365cc521b05df32fe5a4fb56bc6136f2eec8efff110e76e2  (CHANGED)
runtime_file_count: 76 -> 77  (CHANGED)
status: CHANGED

dry-run: 4 skill(s) checked, 1 CHANGED — run with --apply to write (none written)
EXIT=0
```

结果:gzh-design 报 CHANGED(三字段全变),其余三个 skill 全部 无变化 ✓

#### 3b. --apply --reason "档29 沙箱演练"(不跳过回归,验证自动接线;原样输出)

```
relock: note: skipping aihot (agent-invoked skill, no tree hashes)
=== super-writer === (三字段一致,无变化)
=== zh-human-writing === (三字段一致,无变化)
=== media-enrichment === (三字段一致,无变化)
=== gzh-design ===
skill_root_sha256: 9a8cd7f548c2186f789a5e24235001308fc6a868e0f57d74fc06c8919b4ff79b -> 6c38425dfb786155127b40f62e79fc4631d0273f217cc735a7d197aed9f75ec6  (CHANGED)
runtime_manifest_sha256: ced841439195453497e67a63186823f60eee7155b9de472e936c3d4d767e33b2 -> 9d8599f46907ab39365cc521b05df32fe5a4fb56bc6136f2eec8efff110e76e2  (CHANGED)
runtime_file_count: 76 -> 77  (CHANGED)
status: CHANGED

doctor gate: allowed — target hash/version mismatch only (re-lockable state)
backup: C:\Users\Admin\AppData\Local\Temp\wxgzh-relock-sandbox-20260801\lock-backups\skills.lock.20260801T144751Z.json
ledger: relock-gzh-design-20260801T144751Z-516fbc90 (gzh-design)
doctor: PASS (post-relock)
regression: PASS (upgrade_regression.py)
relock: OK
EXIT=0
```

写前门禁走了档 28 的 1b 分类路径(目标 skill 仅 hash 失配 → 允许),写后 doctor 对沙箱 lock + 沙箱 skills 树 PASS,回归自动执行并 PASS。

#### 3c. 备份与执行前 lock 字节完全相同

```
3c backup byte-identical to pre-apply lock: True
```

#### 3d. 沙箱 lock 仅该 skill 三个字段变化,其余部分逐字相同

```
3d changed lines (pre -> post):
    -      "skill_root_sha256": "9a8cd7f548c2186f789a5e24235001308fc6a868e0f57d74fc06c8919b4ff79b",
    -      "runtime_manifest_sha256": "ced841439195453497e67a63186823f60eee7155b9de472e936c3d4d767e33b2",
    -      "runtime_file_count": 76,
    +      "skill_root_sha256": "6c38425dfb786155127b40f62e79fc4631d0273f217cc735a7d197aed9f75ec6",
    +      "runtime_manifest_sha256": "9d8599f46907ab39365cc521b05df32fe5a4fb56bc6136f2eec8efff110e76e2",
    +      "runtime_file_count": 77,
```

unified diff 仅含这 6 行(3 旧 3 新),即只有 gzh-design 的三个哈希字段变化,文件其余部分逐字相同 ✓

#### 3e. 台账恰好 1 条,字段完整,old/new 与实算一致

```
3e ledger records: 1
   entry_id: relock-gzh-design-20260801T144751Z-516fbc90
   skill: gzh-design
   old_root_sha256: 9a8cd7f548c2186f789a5e24235001308fc6a868e0f57d74fc06c8919b4ff79b
   new_root_sha256: 6c38425dfb786155127b40f62e79fc4631d0273f217cc735a7d197aed9f75ec6
   old_manifest_sha256: ced841439195453497e67a63186823f60eee7155b9de472e936c3d4d767e33b2
   new_manifest_sha256: 9d8599f46907ab39365cc521b05df32fe5a4fb56bc6136f2eec8efff110e76e2
   old_file_count: 76
   new_file_count: 77
   reason: 档29 沙箱演练
   recorded_at: 2026-08-01T14:47:51Z
   doctor_result: PASS
```

#### 3f. 写后 doctor 通过:见 3b 输出 `doctor: PASS (post-relock)`(对沙箱 lock + 沙箱树校验,`--skills-home/--lock-path` 均已转发)✓

#### 3g. 再次 dry-run,四个全部无变化

```
status: 无变化 (x4)
dry-run: 4 skill(s) checked, 无变化 — nothing to write
EXIT=0
```

### 4. 三态判定演练(沙箱内)

- 构造 receipt:`network_mode=live`,`skill_root_sha256`=变更前旧值 `9a8cd7f…`,skill_dir 指向沙箱 gzh-design;entrypoint/validator 指向真实安装(只读引用,sha 与文件实算一致);4 个输出文件建于沙箱内 run 目录(结构通过 `validate_receipt`,输出哈希自洽)。

```
4a with ledger in place:
  ok: True | skill_root_state: SKILL_UPGRADED | upgrade_entry_ids: ['relock-gzh-design-20260801T144751Z-516fbc90']
  mism: []
4b with ledger moved away:
  ok: False | skill_root_state: TAMPERED | upgrade_entry_ids: []
  ledger restored: True
```

- 4a:SKILL_UPGRADED,`upgrade_entry_ids` 恰好等于 3e 那条记录的 entry_id ✓
- 4b:台账移走后同一 receipt → TAMPERED(严格行为不因演练放宽)✓
- 4c:台账恢复 ✓
- 实现注记:为支持沙箱台账,`verify_receipt` 新增 `history_path` 可选参数;默认 None 仍走仓库根台账(档 28 严格语义不变:缺失/空/非法一律 TAMPERED,已由既有测试覆盖)。

### 5. 回滚路径演练(沙箱内)

- 场景:把沙箱 gzh-design `RELEASE_NOTES.md` 首行版本改为 `v2026.07.18-hammer.1-sandbox-rollback-drill`(文件 sha 前/后:`0d6ab950…` → `8fd17f6e…`),制造「写后 doctor 版本失配」;写前门禁按 1b 允许(仅目标 skill version/hash 失配)。
- 执行 `--apply --skip-regression --reason "档29 沙箱回滚演练"`(原样输出,doctor 报告全文见附件 A):

```
doctor gate: allowed — target hash/version mismatch only (re-lockable state)
backup: ...\lock-backups\skills.lock.20260801T144923Z.json
ledger: relock-gzh-design-20260801T144923Z-96928d98 (gzh-design)
relock: ERROR: doctor FAIL after re-lock — rolling back
{doctor 报告: gzh-design current_version=...-sandbox-rollback-drill, version_ok=false, FAIL_CLOSED=true}
rollback: skills.lock.json and ledger restored byte-identically
EXIT=4
```

验证结果:

```
5a 退出码: EXIT=4 ✓
5b lock byte-identical to pre-run: True   (lock sha a139af79…)
5b ledger byte-identical to pre-run: True (ledger sha 010f035c…,其中仍含 3e 那条记录)
5c backups retained: ['skills.lock.20260801T144751Z.json', 'skills.lock.20260801T144923Z.json']
```

- 5b:lock 与台账逐字还原到本次执行前(含此前 3b 已写入的台账记录)✓
- 5c:两份备份均保留,备份不参与回滚删除 ✓

### 演练中发现的接线缺陷(已修,非凑预期)

首次 `--apply` 时 doctor 抛 `FileNotFoundError: ...\skills.lock.json\skills.lock.json`,原因是上一版未提交代码把 **lock 文件路径** 直接传给 `SD.load_lock()`(其语义为「skill root 目录」)。relock 门禁正确按「doctor 输出不可解析」拒绝并 exit 3,且失败运行零写入(无备份、无台账、沙箱 lock 未动)。修复:`Orchestrator` 在给定 `lock_path` 时直接 `json.loads` 读取该文件;`None` 时仍走 `SD.load_lock(SKILL_ROOT)`(生产语义不变)。修复后 3b–5 全部一次通过。

## 第二部分 升级回归自检

### scripts/upgrade_regression.py

- 三步全部离线、零外部副作用,任一不过则以非零码退出:
  1. 全量 pytest,显式 `--deselect` 27 项环境依赖测试(排除清单见下,逐条标注缺失环境);
  2. 对四个被锁 skill 各跑一次 relock dry-run,断言 `status: 无变化` 且无 CHANGED;
  3. `doctor --require-wechat` 必须 PASS。
- 接入:relock `--apply` 成功后自动调用(超时 900s);新增 `--skip-regression` 供沙箱/调试跳过。
- 回归失败语义:不回滚 lock(此时 lock 已是正确新值),以退出码 6 结束并打印「lock 已更新但回归未通过,需人工裁决」。该路径已用单测覆盖(`test_apply_regression_fail_exits_6_lock_not_rolled_back` 等 3 个新用例)。
- 独立运行输出(本次验证,即 apply 内自动调用的同一脚本):

```
upgrade_regression: project_root=F:\AIXM\wxgzh
pytest: PASS (27 explicit deselects)
relock dry-run x4: PASS
  super-writer: status: 无变化 OK
  zh-human-writing: status: 无变化 OK
  media-enrichment: status: 无变化 OK
  gzh-design: status: 无变化 OK
doctor --require-wechat: PASS
upgrade_regression: ALL PASS
EXIT=0
```

### 排除清单(27 项,与代码中 `EXCLUDED_TESTS` 逐字一致)

| 测试 | 缺失环境 |
| --- | --- |
| test_dev2_fake_live.py::test_fake_live_six_stages | 无 sibling media-enrichment checkout(`<repo>/../media-enrichment`,含 `src/media_enrichment/input_contract.py`) |
| test_dev2_fake_live.py::test_receipt_tamper | 同上 |
| test_dev2_fake_live.py::test_dynamic_chapter_gate | 同上 |
| test_hotfix1.py::test_resume_tamper_media_manifest_invalidates_media_and_later | 同上 |
| test_hotfix1.py::test_resume_tamper_upstream_article_invalidates_media_gzh_wechat | 同上 |
| test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[a_empty_object] | 同上 |
| test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[b_del_input_hash] | 同上 |
| test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[c_del_output_hash] | 同上 |
| test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[d_del_entrypoint_sha] | 同上 |
| test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[e_del_official_validators] | 同上 |
| test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[f_validator_exit_1] | 同上 |
| test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[g_official_exit_1] | 同上 |
| test_hotfix2_receipt_tamper.py::test_wechat_gate_blocks_on_tampered_prior_receipt | 同上 |
| test_hotfix3_approved_scope.py::test_c_material_scope_only_that_material | 同上 |
| test_hotfix3_approved_scope.py::test_d_source_url_scope_no_inheritance | 同上 |
| test_hotfix3_approved_scope.py::test_e_unknown_scope_not_known_allowed | 同上 |
| test_hotfix3_approved_scope.py::test_bad_evidence_hash_ignored | 同上 |
| test_hotfix3_approved_scope.py::test_material_scope_missing_binding_ignored | 同上 |
| test_hotfix3_approved_scope.py::test_source_url_for_unknown_url_approves_nobody | 同上 |
| test_hotfix1.py::test_portable_installer_preserves_pipeline_release_include | 便携安装包构建需 git checkout 上下文(当前 pytest cwd 非 git 仓库) |
| test_hotfix7_live_handshake.py::test_cross_repo_real_full_mode_long_pass | 需 `WXGZH_REAL_SUPER_WRITER_ROOT`/`WXGZH_REAL_SKILLS_HOME` 指向真实 skill checkout |
| test_hotfix7_live_handshake.py::test_cross_repo_medium_overlong_uses_declared_policy | 同上 |
| test_hotfix7_live_handshake.py::test_cross_repo_missing_full_mode_artifact_fails | 同上 |
| test_pipeline.py::test_02_03_defaults_and_draft | 完整 LIVE 六阶段(真实 agent + 微信草稿),离线回归绝不执行 |
| test_pipeline.py::test_08_no_stage_skip | 同上 |
| test_pipeline.py::test_10_resume_no_rerun | 同上 |
| test_pipeline.py::test_full_run_delivery | 同上 |

## 第三部分 收尾

### 8. verify_receipt 返回类型注解

已改为三元组 `-> tuple[bool, list, dict]`,并顺手修正档 28 遗留的缺失 receipt 早退路径(2 元组 → 3 元组,`skill_root_state=OK / upgrade_entry_ids=[]`)及 `tests/test_dev2_fake_live.py` 中漏改的 3 元解包。

### 9. 真实环境未受污染证明(执行前快照 vs 执行后)

快照文件 `before-env.json` 在演练前落盘于沙箱(沙箱已删,值已固化于本报告):

```
before: skills_tree_manifest_sha256=aebf75c1d8f310e5aa6f921d025ecfc5e168d75c7593d564c6820e0d05f947d9 (982 files)
before: real_lock_sha256=a9e07ef42017cff225158466213253baf1155f34a7c2f1bdaf62a87dbbc751d6
before: real_ledger_exists=false
```

执行后(同一算法:逐文件 posix 相对路径 + 原始字节 sha256,Path 顺序,整串 sha256):

```
after : 982 files (排除 2 个 late pytest 生成的 __pycache__/*.pyc 后) = aebf75c1…947d9  MATCH
after : real lock sha256 = a9e07ef4…d751d6  未变
after : real ledger 不存在                   未变
```

说明(事实):全树遍历计数 984 = 快照 982 + 2 个 `__pycache__` 下 `.pyc`(`media-enrichment/src/…/input_contract…pyc`、`super-writer/scripts/…/material_ingestion…pyc`),二者由本会话 22:36–22:37 的 pytest 运行(导入已安装 skill 包)生成,时间戳早于沙箱演练、且属运行时哈希显式排除的缓存目录,并非档 29 演练造成;排除后逐字节与快照一致。另,演练前曾出现一次「不匹配」,系我复核脚本改用 posix 字符串排序所致(Windows Path 排序与字符串排序存在顺序差异),改用与快照完全相同的 Path 排序后逐字匹配——非内容变化。四个被锁 skill 的运行时 root sha 未变,由第 10 步真实 dry-run 直接证明。

### 10. 真实环境最终 dry-run(原样输出)

```
relock: note: skipping aihot (agent-invoked skill, no tree hashes)
=== super-writer ===   status: 无变化
=== zh-human-writing === status: 无变化
=== media-enrichment === status: 无变化
=== gzh-design ===     status: 无变化
dry-run: 4 skill(s) checked, 无变化 — nothing to write
EXIT=0
```

沙箱目录已彻底删除(`%TEMP%\wxgzh-relock-sandbox-20260801` 不存在)。

## 风险点(如实陈述)

1. **接线 hook 曾有真实缺陷**:`lock_path` 覆盖最初被错误传给 `SD.load_lock()`(期望根目录),已在本次修复并补测试;该 hook 目前无独立单测覆盖 doctor 转发路径(沙箱演练覆盖了实测,但建议后续补正式用例)。
2. **`--skip-regression` 语义依赖人工自律**:回归在真实环境运行,沙箱演练若不显式跳过会在 apply 成功后跑一次真实回归(无害但耗时);已通过测试保证跳过/执行分支的退出码。
3. **回归排除清单可能被误用为「万能豁免」**:代码注释已明确禁止扩大清单掩盖真实回归;清单 27 项全部标注缺失环境,且全部可通过补齐 sibling checkout / 环境变量恢复。
4. **台账链匹配基于 root sha 全链**:若某 skill 历史上有「未走 relock 流程」的根 sha 变化(如旧版本直接覆盖安装),receipt 会判 TAMPERED 而非 SKILL_UPGRADED——这是有意的严格语义,但迁移旧 receipts 时需要人工补台账。
5. **doctor 的 `--skills-home/--lock-path/--skills-home` 覆盖 hook 是生产路径的旁路**:任何脚本误传这些参数会校验非标准环境;relock 仅在显式传参时转发,默认仍走项目布局,风险可控。
6. **写后回归失败不回滚 lock**:按档 29 要求「lock 已更新但回归未通过,需人工裁决」;若回归失败原因是环境本身损坏,lock 可能指向「正确」但环境不可用状态,需人工评估。

## 附件 A:回滚演练中写后 doctor 完整报告(原样)

```json
{
  "wxgzh_pipeline_version": "0.1.0-dev2-hotfix7R4",
  "project_root": "F:\\AIXM\\wxgzh",
  "skills_home": "C:\\Users\\Admin\\AppData\\Local\\Temp\\wxgzh-relock-sandbox-20260801\\skills",
  "network_mode": "live",
  "skills_locked_ok": false,
  "skills": {
    "super-writer": { "version_ok": true, "hash_ok": true, "entrypoints_ok": true, "ok": true },
    "zh-human-writing": { "version_ok": true, "hash_ok": true, "entrypoints_ok": true, "ok": true },
    "media-enrichment": { "version_ok": true, "hash_ok": true, "entrypoints_ok": true, "ok": true },
    "gzh-design": {
      "locked_version": "v2026.07.18-hammer.1",
      "current_version": "v2026.07.18-hammer.1-sandbox-rollback-drill",
      "version_ok": false, "hash_ok": true, "entrypoints_ok": true, "ok": false
    },
    "aihot": { "EXTERNAL_DEPENDENCY_AIHOT": "INSTALLED", "live_pipeline_allowed": true, "ok": true }
  },
  "EXTERNAL_DEPENDENCY_AIHOT": "INSTALLED",
  "LIVE_PIPELINE_ALLOWED": true,
  "wechat_config_present": true,
  "project_writable": true,
  "FAIL_CLOSED": true,
  "doctor": "FAIL"
}
```

(缩略版仅保留判定字段;完整版含全部 sha 字段,已在会话原文输出中留档。)
