# 档 44 — 扩展 relock 支持完整 lock 字段 + 远端见证约束(沙箱演练,不碰真实环境)

- 报告编号:relock-full-fields-44
- 执行日期:2026-08-02(Asia/Shanghai)
- 范围:仅 `scripts/relock.py` + 测试 + 报告;沙箱中执行 relock --apply;未在真实 `.agents\skills` 上执行任何 relock --apply;未修改真实两侧 skills.lock.json;未修改任何被锁 skill;其余禁令维持,TEMP_CLEANUP_ALLOWED=false(仅沙箱按指令 20 删除)。
- 工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(dev/0.1.0-dev2,起点 HEAD `676fa2b`)

## 第一 字段能力补全

1. relock 现支持的完整字段集(`_ALL_FIELDS`):
   - 原三字段:`skill_root_sha256 / runtime_manifest_sha256 / runtime_file_count`
   - 档 44 新增:`full_commit_sha / source_tree_sha / entrypoint_sha256 / render_entry_sha256`
2. 逐字段核查结果(据实,一并纳入):
   - **纳入 `validator_sha256`、`component_source_sha256`**:与 entrypoint 同类的文件哈希字段,升版时文件可能变化,必须一并重算(由 lock 中声明路径在源树上实算;文件缺失即拒绝)。
   - **纳入 `branch`**:锁定的 commit 所在远端分支;源树为 git checkout 时从 `symbolic-ref` 派生,非 git 目录则保持原值。
   - **不纳入 `skill_version`**(据实说明):它是声明式发布字符串,无法从树内容可靠推导;版本号由技能文档显式升版后,走常规三字段 relock 即可。
   - 不纳入:`repository_url`(仓库不变)、`entrypoint/validator/render_entry/component_source`(路径,移动属 P2 类迁移,需 required_files 移除开关)、`required_files`(已有 `--allow-required-files-removal` 开关,语义不变)。
3. 不为新增字段提供开关(它们是升级的必然伴随,非危险操作);dry-run 逐项打印 旧值 → 新值,一个不漏(print_rows 遍历全部字段)。

## 第二 远端见证约束(本档核心安全设计)

- 新参数:`--source-tree <path>` + `--source-commit <sha>`(必须同时提供;单 `--skill` 目标,不支持 `--all`;commit 必须 40-hex)。
- 写 lock 前强制三项验证(任一不过即拒绝、退出 2、零写入):
  - (a) commit 在远端仓库真实存在:`git ls-remote <repository_url>` 全量引用中必须含该 sha(裸 sha 会被 ls-remote 当作 ref 名模式,故用全量列表)。
  - (b) 远端 commit 的树与 `--source-tree` 本地树逐字一致:临时仓库 fetch 远端 commit → `FETCH_HEAD^{tree}`;本地用 `add -A`(尊重源 `.gitignore`,镜像源 `.gitattributes` 与 `core.autocrlf`)→ 按远端文件清单 force-add 被忽略的已跟踪文件(如 `*.png`)→ `write-tree` 与远端树 sha 相等;本地含远端没有的文件也判 (b) 不过。
  - (c) 待写入 lock 的 `source_tree_sha` 等于远端实算值(显式断言)。
- 错误信息明确指出哪一项未通过,并提示「升级前请先将改动 push 到远端」。
- **无任何跳过远端验证的开关/环境变量/参数**;网络不可用(OSError/超时)一律拒绝执行,不降级为本地校验。
- 代码注释写明来由:OBS-74(四轮本地热修从未回流,lock 长期指向无远端副本的树)。

## 第三 原子性与顺序

- 实现「先 relock 后安装」顺序(仅 `--source-tree` 模式):
  a. 远端见证验证 → b. 对 `--source-tree` 计算全部新字段值 → c. 备份 lock → d. 写入新 lock + 台账 → e. 自动构建正式 bundle(新 lock + locked-skills 中目标=源树、其余=当前安装树 + source-proofs 取自新 lock + MANIFEST)并调用正式安装器(`--target <skills-home>`)→ f. post-doctor 复验。
- d 与 e 之间无任何对外暴露点(installer 立即调用),不存在「lock 已更新但代码未装」的可见中间态。
- 任一环节失败:lock 与台账逐字还原(既有 `_rollback`),安装树由预装快照(`backup_dir/skills-tree.<name>.preinstall`)+ receipts 字节快照一并还原;回滚成功退出 4,回滚失败退出 5;lock 备份文件保留。
- 非 `--source-tree` 模式行为与档 27-33 完全一致(回归保证)。

## 第四 台账扩展

- 记录包含本次变更的全部字段,逐字段 `old_<field> / new_<field>`(三哈希字段沿用既有短名 `old_root_sha256` 等,确保 receipts.py `_find_upgrade_chain` 的 `old_root_sha256 → new_root_sha256` 追溯不变;新增字段用全名:`old_full_commit_sha / new_source_tree_sha / old_entrypoint_sha256 / old_branch` 等)。
- 新增字段:`source_commit_verified`(远端见证结果)、`remote_repo`(远端仓库标识)。
- `entry_id` 格式与链式结构不变;测试 `test_upgrade_chain_traces_with_new_record_shape` 用新记录形态直接跑 `_find_upgrade_chain` 验证追溯仍命中(未改动 receipts.py)。

## 第五 测试

新增 `tests/test_relock_full_fields.py`(12 项,全部 PASS;既有 relock 测试 25 项不受影响):

| 要求 | 测试 |
|---|---|
| a. 四个新字段各自正确更新 | test_source_tree_updates_all_new_fields(含 validator/component 不变、branch 更新) |
| b. 见证三项各自失败拒绝且零写入 | test_witness_a/b/c_fail_refuses_zero_write |
| c. 网络不可用拒绝、不降级 | test_network_unavailable_refuses |
| d. 安装失败 lock 字节级回滚 | test_install_failure_rolls_back_lock_and_tree |
| e. post-doctor 失败 lock+安装树一起回滚 | test_post_doctor_failure_rolls_back_lock_and_tree |
| f. 台账含全部变更字段 | test_ledger_contains_all_changed_fields |
| g. required_files 开关行为不变 | test_required_files_switch_still_works_without_source_tree |
| h. 三字段路径回归 | test_three_field_path_regression + 既有 test_relock.py 全量 |
| 14. 链式追溯不破坏 | test_upgrade_chain_traces_with_new_record_shape |
| 参数校验 | test_source_tree_without_commit_refused |

未放宽任何既有断言;全量 pytest:新文件 12 过;既有 `test_relock.py`/`test_relock_reqfiles.py` 全过。

## 第六 沙箱演练(档 43 真实场景,真实远端见证)

沙箱:`F:\AIXM\wxgzh\repos\relock44-sandbox`(演练后已按指令彻底删除);源 = `Amer-CN/gzh-design-skill @ 7c0c06f…`(fix/obs73-codeblock-docs 分支,档 43 产物)。

### dry-run 输出(节选,完整见 `.temp\relock44-dryrun.txt`)

```
远端见证 PASS (a/b/c)
=== gzh-design ===
installed_dir: F:\AIXM\wxgzh\repos\gzh-design-skill-43r-build
skill_root_sha256: 9a8cd7f5… -> 4d68cd90…  (CHANGED)
runtime_manifest_sha256: ced84143… -> ced84143…        # 不变
runtime_file_count: 76 -> 76                           # 不变
entrypoint_sha256: e4023726… -> ca599b64…  (CHANGED)
validator_sha256: b986ae77… -> b986ae77…               # 不变
render_entry_sha256: e4023726… -> ca599b64…  (CHANGED)
component_source_sha256: 02c0d884… -> 02c0d884…        # 不变
full_commit_sha: 0007d7e6… -> 7c0c06f…  (CHANGED)
source_tree_sha: a1f40820… -> b0d81ef7…  (CHANGED,=远端实算)
branch: chore/wxgzh-pipeline-dev2-integration -> fix/obs73-codeblock-docs  (CHANGED)
status: CHANGED
dry-run: 1 skill(s) checked, 1 CHANGED — run with --apply to write (none written)
```

预期核对:**root 9a8cd7f5 → 4d68cd90、manifest/count 不变(76 / ced84143)** —— 与档 41/43 预演一致。

### 远端见证验证过程(实测)

- (a) `git ls-remote https://github.com/Amer-CN/gzh-design-skill` → 含 `7c0c06f…` ✓(已 push 的分支可达)
- (b) 临时仓库 fetch 远端 commit → `FETCH_HEAD^{tree}` = `b0d81ef7…`;本地 `add -A` + 按远端清单 force-add 2 个被 `*.png` 忽略的已跟踪文件 → `write-tree` = `b0d81ef7…` 一致 ✓(此过程中修复了两个真实问题:裸 sha 的 ls-remote 匹配、CRLF/autocrlf 镜像、tracked-but-ignored 文件、非 ASCII 路径的 `-z` 列出)
- (c) 待写入值 == 远端实算值 ✓

### 写入前后 lock sha 与台账

- 沙箱 lock sha:写入前 `A9E07EF4…` → 写入后 `DCF41BE2…`
- 台账新增记录全文(第一条真实结构记录):

```json
{
  "entry_id": "relock-gzh-design-20260802T105655Z-695b7901",
  "skill": "gzh-design",
  "reason": "档44 沙箱演练:gzh-design 升版全字段 relock + 先relock后安装",
  "removed_required_files": [],
  "recorded_at": "2026-08-02T10:56:55Z",
  "doctor_result": "PASS",
  "old_root_sha256": "9a8cd7f5…",
  "new_root_sha256": "4d68cd90…",
  "old_entrypoint_sha256": "e4023726…",
  "new_entrypoint_sha256": "ca599b64…",
  "old_render_entry_sha256": "e4023726…",
  "new_render_entry_sha256": "ca599b64…",
  "old_full_commit_sha": "0007d7e6…",
  "new_full_commit_sha": "7c0c06f…",
  "old_source_tree_sha": "a1f40820…",
  "new_source_tree_sha": "b0d81ef7…",
  "old_branch": "chore/wxgzh-pipeline-dev2-integration",
  "new_branch": "fix/obs73-codeblock-docs",
  "source_commit_verified": true,
  "remote_repo": "https://github.com/Amer-CN/gzh-design-skill"
}
```

### 安装与 post-doctor

- `installer: PASS (source-tree install)` — 正式安装器以新 lock 校验新树,沙箱内 gzh-design 装为 7c0c06f 树;receipt 记录 `full_commit_sha=7c0c06f / source_tree_sha=b0d81ef7 / root=4d68cd90`,与 lock 一致(诚实记录)。
- 沙箱安装树实算:`root=4d68cd90…(76)`、`manifest=ced84143…`、`entry=ca599b64…` == 新 lock 值。
- `doctor: PASS (post-relock)`(--skills-home 沙箱 + --lock-path 沙箱新 lock;OBS_69 因沙箱内 pipeline 锁为旧副本报 MISMATCH,纯 WARN 不影响)。
- 演练走通到底,exit 0。

### 沙箱清理与真实环境未变证明

- 沙箱已彻底删除(`relock44-sandbox` 不存在)。
- 真实 `.agents\skills` 四锁 root 逐字未变(super-writer `46a00a1b…`/zh-human-writing `18491b36…`/media-enrichment `0d8aea21…`/gzh-design `9a8cd7f5…`);
- 真实两侧 lock sha 均 `a9e07ef4…`(未动);真实台账 `skills.lock.history.json` 不存在(未动)。

## 第七 复核

21. `upgrade_regression.py`:**ALL PASS**,排除清单仍 1 项。
22. 四锁 relock dry-run:super-writer / zh-human-writing / media-enrichment / gzh-design 全部「无变化」。
23. doctor `--require-wechat` 双侧 PASS(退出码 0),档 42 两项 WARN:`OBS_69_LOCK_MATCH=MATCH`、`OBS_68_PIPELINE_MATCH=MATCH`(repo 571 / installed 571,0 差异)。
24. 正式安装器同步(`bundle-staging-44`):安装侧与 repo HEAD **571 文件逐字一致**(0 差异,`scripts/relock.py` 两侧 sha 相同);两侧 lock sha `a9e07ef4…` 未变,台账不存在。

## 风险点与说明

1. 远端见证依赖网络与 GitHub 可达性;按设计网络不可用即拒绝(不降级),离线环境下无法使用 `--source-tree` 模式(三字段模式不受影响)。
2. (b) 校验对 `--source-tree` 的「本地树含远端没有的文件」严格失败(如残留 `__pycache__` 之外的非忽略垃圾文件);这是 fail-closed 方向,需清理源目录。
3. `branch` 从源 checkout 的 `symbolic-ref` 派生;非 git 目录的源树保持原 branch 值(报告中如实记录)。
4. `skill_version` 不自动更新(声明式字符串),升版时若版本号变化需单独处理(见第一.2)。
5. 台账新增字段为纯追加,`_find_upgrade_chain` 只依赖 `old_root_sha256/new_root_sha256/entry_id/skill`,已用测试证明追溯不受影响。
