# OBS-389 验收报告 · 档 77AL（上传并行 + 阶段内并行 + 契约允许的重叠）

- 仓库：`F:\AIXM\wxgzh-skills`（main）
- 基线提交：`17fb9cd`（执行前复核：`git rev-parse --short HEAD` = `17fb9cd`、`git status --porcelain` 空、`git rev-parse --short origin/main` = `17fb9cd`，三侧一致）
- 装机侧：`F:\AIXM\wxgzh\.agents\skills`（project_root = `F:\AIXM\wxgzh`）
- 授权：`RELOCK_ALLOWED` 临时 0→1（批准人=用户，提速序列已批，范围=档 77AL）；`GZH_DESIGN_WRITE_ALLOWED` 维持 0
- 状态：任务 0/1/2 完成；relock **#118 落成**（主智能体接续：feat `4ed3524` 推送后 `--source-tree` 仓根 + `--source-commit` 全字段模式一次通过；本报告 §3/§5 原"未落成"表述已随落成更新，原文留痕见 git 历史）

---

## 1. 任务 0 侦察（只读，实测原文与摘录）

### 1.1 上传完全串行（实证锚点逐个复核）

证据文件：`F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260915T163606-siri-ai-tjyl4w\media_enrichment\continue\upload_events.json`

```
serial=True  schema=1.0  n=24
success=24
first_start=438664.078  last_end=438685.531
wall_span=21.453s
sum_request_elapsed=20.874s
overlaps=0
```

首尾相接逐条零重叠（`overlaps = |逐对 start < 前一条 end| = 0`），24 条全部 `success`。

调用点（同步串行，与简报 L1484-1487 一致）：

```
1484: upload_result = timed_upload(
1485:     uploader, upload_events, upload_path, asset.asset_id,
1486:     copyright_status=asset.copyright_status,
1487: )
```

### 1.2 抓取已并行（阶段内并行先例）

```
755: # 76F/OBS-275:页面抓取有界并行(worker=4)——抓取阶段并行、资产构建串行
757: from concurrent.futures import ThreadPoolExecutor
762: with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as _pool:
```
`FETCH_WORKERS = 4`（run_media_enrichment.py L31）。

### 1.3 契约冲突（须先改契约）

`contracts/04_media_enrichment.yaml` L34-36（改前原文）：
```yaml
upload:
  serial: true
  manifest_single_writer: true
  no_orchestrator_bypass: true
```
`wxgzh_pipeline/contracts.py` L221/L225-235 是该口径的**机器判据**（`upload_serial_declared` 断言 `serial is True`；`upload_no_overlap` 逐对判定），与并行直接冲突。

### 1.4 media 必须等 zh（依赖链实证）

- `contracts/04_media_enrichment.yaml` L5-6：`must_run_after: zh_human_writing` / `depends_on_freeze: final_article_sha256`
- `wxgzh_pipeline/execmodel.py` L91-96：media 的上游输入含 `zh_human_writing/final_article.md`
- `wxgzh_pipeline/stages/media_enrichment.py` L19-21/L53/L102-104：`stage_inputs` 带 `final_article_sha256`、`content_validate` 校验 bindings 引用冻结 sha

### 1.5 sw request 绑上游哈希（禁动）

`wxgzh_pipeline/producers.py` L357-364 `_reusable_agent_request`：请求信封内 `upstream_hashes` 必须与当前盘上 upstream 一致，不一致即不复用（重签）。本档未触碰该函数。

### 1.6 media 条目涉锁（改上传代码必 relock media）

`skills.lock.json` `media-enrichment` 条目 `required_files` = `scripts/run_media_enrichment.py`、`scripts/validate_media_manifest.py`、`src/media_enrichment/uploader.py`、`src/media_enrichment/article_bindings.py`；本档改动命中前两条中的 `run_media_enrichment.py` 与 `uploader.py`。

### 1.7 跨阶段重叠点判定：**无允许点，未做**

实测（只读）：
- `pipeline.yaml`：`stages_sequential: true`；六阶段固定顺序、`fail_closed: true`、不允许回退/跳阶段。
- `wxgzh_pipeline/orchestrator.py` L391-399：逐阶段严格顺序，`stage != expected` 即 `mark_failed` + `FAIL_CLOSED`；L402-413：`wechat_draft` 前六 receipt 全链 `verify_receipt` 复算门；L443-445：阶段完成即 `mark_complete` + `save_state`。
- 契约依赖：media 依赖 zh freeze（§1.4）；`gzh_design` 依赖 `media_enrichment/media_manifest.json` + `article_image_bindings.json`（`execmodel.py` L97-99）。
- 结论：**跨阶段重叠在现行契约与执行模型下没有任何允许点**（阶段体内并发是唯一合法并行位），如实记「无允许点、未做」，未硬做。本档只做阶段内并行（上传批次并发）。

### 1.8 media 301s 内部分解

`media_enrichment/stage_receipt.json`（tjyl4w）实测：`started_at=2026-09-15T09:25:16Z`、`ended_at=2026-09-15T09:25:40Z`、`elapsed_seconds=24.0`、`wall_seconds=301.0`、`validation_seconds=24.0`、official_validator `elapsed_seconds=0.799`。
即：阶段整体 wall 301s，其中**阶段实体执行 24s**（上传 21.453s 含于此 24s 内），其余约 277s 在阶段体外（编排器/agent 交接等，非本档目标）。媒体阶段本身的可压缩量 ≈ 上传串行耗时 21.453s。

### 1.9 双套件基线（执行前实测）

| 套件 | passed | failed | skipped | 红名单 |
|---|---|---|---|---|
| wxgzh-pipeline | 635 | 7 | 16（简报写 22，以实测为准） | test_hotfix1::test_portable_installer_preserves_pipeline_release_include；test_hotfix7_live_handshake×3（cross_repo_real_full_mode_long_pass / medium_overlong_uses_declared_policy / missing_full_mode_artifact_fails）；test_obs171::test_obs173_status_sha_absent；test_obs80_smoke_samples[zh-human-writing]；test_obs80_smoke_samples[gzh-design] |
| media-enrichment | 376 | 0 | 7 | 无 |

### 1.10 doctor 基线（双侧）

命令：
```
python scripts/doctor.py --offline --project-root F:\AIXM\wxgzh --skills-home F:\AIXM\wxgzh\.agents\skills --repo-root F:\AIXM\wxgzh-skills\skills\wxgzh-pipeline
```
实测：`exit=0`、`FAIL_CLOSED=False`、`doctor=PASS`、
`OBS_69_LOCK_MATCH.status=MATCH`（baseline=installed=`79f5cf7e70c680a12239b2ae9d9234a6b059c84aaa7209c3146b9cad35ba1c8d`）、
`OBS_68_PIPELINE_MATCH.status=MATCH`（repo 813 / installed 813，diff=0 missing=0 extra=0）。

---

## 2. 任务 1 实现（改动清单）

### 2.1 media-enrichment 侧

| 文件 | 改动 |
|---|---|
| `src/media_enrichment/uploader.py` | ①`UPLOAD_WORKERS = 4` 单一真源常量 + `_EVENTS_LOCK` 互斥锁；②`timed_upload()` 增三个**可选**参数 `batch_index` / `batch_size` / `event_slot`，事件逐条带批次标记，追加/预留槽位写入走锁（旧串行调用不传参 → 入账形状逐字不变）；③新增 `upload_assets_parallel()`：批内 threads 并发、批间串行，批次数=`ceil(len/workers)`，事件表按资产顺序预留槽位，结果同序返回 |
| `scripts/run_media_enrichment.py` | 上传循环拆「登记计划（含 WebP 转码，循环内）→循环外批次并发→同序回写」；`upload_plan` 收集待上传项；`upload_events.json` 增 `parallel_workers` 台账键；导入与注释同步 |

**manifest 单写语义不变**：并发只发生在 `uploader.upload()` 内部；`asset.upload` 回写、`builder.errors` 记账全在主线程按 `upload_plan` 顺序执行。

### 2.2 wxgzh-pipeline 侧

| 文件 | 改动 |
|---|---|
| `contracts/04_media_enrichment.yaml` | `upload` 节增 `parallel_workers: 4`、`overlap_semantics: batch_partition`，并写明 `serial` 键保留的含义（不放开「无重叠」「每资产恰一次成功」两条审计不变量，只把重叠判法由逐对改为批次分区） |
| `wxgzh_pipeline/contracts.py` | `upload_no_overlap` 判定改批次分区：事件带 `batch_size` → 贪心区间着色，所需并发道数 > 声明批次数才拒；无批次标记的旧串行表 → 沿用原逐对判定。新增 `upload_parallel_workers_declared`（契约声明值 vs 事件表台账值；历史产物无台账键 → 不适用判通过） |
| `wxgzh_pipeline/stages/media_enrichment.py` | docstring 与 `side_effects()` detail 文案由「serial upload」改「batch-parallel upload」 |

### 2.3 测试（各一文件）

- `skills/media-enrichment/tests/test_hf77al_upload_parallel.py`（新增，3 绿）
- `skills/wxgzh-pipeline/tests/test_hf77al_upload_batches.py`（新增，5 绿）

### 2.4 升版与版本字面量同步

- `skills/media-enrichment/VERSION`：`0.1.0-dev36 → 0.1.0-dev37`
- `skills/wxgzh-pipeline/VERSION`：`0.1.0-dev2-hotfix9R35 → 0.1.0-dev2-hotfix9R36`
- **dev36→dev37 字面量全站同步（既有测试的硬要求，非新增范围）**：`src/media_enrichment/__init__.py`、`src/media_enrichment/input_contract.py`、`src/media_enrichment/url_security.py`（2 处）、`scripts/build_zip.py`（2 处）、`scripts/generate_evidence.py`（2 处）、`scripts/_verify_dev7.py`、`README.md`、`WXGZH_PIPELINE_INTEGRATION.md`。依据：`tests/test_runner_integration.py::TestVersionConsistency::test_all_versions_dev7_hotfix1`（`CURRENT` 常量逐字比对 `VERSION`、`src/media_enrichment/__init__.py` 等）与 `tests/test_uploader_manifest.py::TestVersionConsistency::test_version_files_consistent`（`VERSION` / `__init__.py` / `input_contract.py` 三处必须同值）——只升 `VERSION` 会即刻产生 2 条新红。
- `skills/media-enrichment/CHANGELOG.md`：**未动**（见 §7 观察项①）。
- `skills/wxgzh-pipeline/tests/test_hf76r.py`：`test_obs304_ledger_count_command` 的唯一编号钉子由 `270 / range(119, 389)` 顺延为 `271 / range(119, 390)`（+1 行 77AL 口径注释）。依据：台账已落 OBS-389，该钉子按「76Y-R/77K 起计数实测为准」的既有口径必须随档顺延（77Q–77AK 均为同一动作）。**不同步即为本档新红**（实测：同步前 `n = 271 != 270` FAILED）。

---

## 3. 验收标准逐条自验

### 标准 1｜上传并行：fixture 24 张并行上传全成功、manifest 一致、有真并行证据、旧串行调用兼容

**1a 新用例绿**
```
cd F:\AIXM\wxgzh-skills\skills\media-enrichment
python -m pytest tests\test_hf77al_upload_parallel.py -q -p no:cacheprovider
→ 3 passed in 2.77s
```
三条覆盖：批次划分与批间串行 + 批内真并发（`_SlowUploader.max_inflight == 4` 断言）+ 24 张 CLI 端到端（`wechat_audit` 离线）+ 旧串行调用入账键集合逐字相同（15 键、无 `batch_index`/`batch_size`）。

**1b 24 张实测（真 CLI，离线 fixture，脚本：`.work/77al-upload-parallel-evidence.py`）**
```
discover rc = 0
continue rc = 0
parallel_workers = 4  n = 24  statuses = ['success']
wall_span = 0.0160s   sum_request_elapsed = 0.0000s
  batch 0 n=4 span=0.00000 sum_elapsed=0.00000 overlap_inside=False
  batch 1 n=4 span=0.01600 sum_elapsed=0.00000 overlap_inside=True
  batch 2 n=4 span=0.00000 sum_elapsed=0.00000 overlap_inside=False
  batch 3 n=4 span=0.00000 sum_elapsed=0.00000 overlap_inside=False
  batch 4 n=4 span=0.00000 sum_elapsed=0.00000 overlap_inside=False
  batch 5 n=4 span=0.00000 sum_elapsed=0.00000 overlap_inside=False
cross_batch_overlap = False
asset_order_sorted = True
```
- 24 张全成功、批次标记齐（6 批 × 4 条，`batch_index`/`batch_size` 全带）、跨批零重叠、事件表资产顺序（=串行口径）。
- **真并行证据**取简报给出的第二种口径（批次标记）在 CLI 侧成立；**批内真并发**由新用例的 `max_inflight=4` 断言给出实证（`wechat_audit` 上传器无 IO，CLI 侧 `request_elapsed_seconds` 恒 0，无法用「elapsed 之和 > wall」口径）。
- 旧串行调用兼容：`test_legacy_serial_timed_upload_unchanged`（入账键集合逐字相同）+ 既有 `tests/test_hotfix2_host_events.py::TestUploadEvents::test_serial_events_no_overlap_one_per_asset`（不传批次参数仍逐对无重叠）全绿。

**1c 契约侧批次分区口径（pipeline 侧）**
```
cd F:\AIXM\wxgzh-skills\skills\wxgzh-pipeline
python -m pytest tests\test_hf77al_upload_batches.py -q -p no:cacheprovider
→ 5 passed
```
覆盖：旧串行表无重叠通过 / 人为重叠拒（理由串 `parallel/overlapping uploads detected` 不变）/ 批内 4 道并发通过 / 并发 6 道 > 声明 4 道 拒（`concurrent uploads exceed the declared batch size`）/ 台账值不一致拒 / 旧台账键缺失不阻断。

**1d 离线全链复跑（阶段契约不因并发误杀）**
```
python -m pytest tests\test_pipeline.py tests\test_dev2_fake_live.py tests\test_hotfix2_receipt_tamper.py tests\test_obs67_visual_threshold.py -q
→ 60 passed
```

### 标准 2｜双套件零新红（红名单逐项同名比对）

| 套件 | 基线 | 改动后 | 差值 | 红名单比对 |
|---|---|---|---|---|
| wxgzh-pipeline | 635P / 7F / 16S | **639P / 8F / 16S** | +4 pass | 基线 7 项**逐项同名**全在；**当时多 1 项**：`test_obs180_wechat_api_gate.py::test_obs180_set_one_live_allowed`（归因见下；relock #118 落成后主智能体复测转绿，见本节末） |
| media-enrichment | 376P / 0F / 7S | **379P / 0F / 7S** | +3 pass（新增 3 条） | 零红、零新红 |

**`test_obs180_set_one_live_allowed` 新增红的归因（实测，非猜测）**：
该用例的 `REAL_SKILLS = Path(r"F:\AIXM\wxgzh\.agents\skills")`（`tests/test_obs180_wechat_api_gate.py:19`），即它**读装机侧真实技能树**做 doctor。当时装机侧 media `VERSION` 刚升为 `0.1.0-dev37`、`src/media_enrichment/__init__.py` 等字面量尚未同步（锁仍 `0.1.0-dev36`，relock 未落成，§5），故 doctor 在该技能上报 `version_ok=false` → `FAIL_CLOSED=true`。当时实测：
```
super-writer     ok=True  version_ok=True  hash_ok=True
zh-human-writing ok=True  version_ok=True  hash_ok=True
media-enrichment ok=False version_ok=False hash_ok=False
gzh-design       ok=True  version_ok=True  hash_ok=True
aihot            ok=True  version_ok=True  hash_ok=True
FAIL_CLOSED True
```
锁定原因（apply 日志第 53/54 行）：
```
"locked_version": "0.1.0-dev36",
"current_version": "0.1.0-dev37",
"version_ok": false,
```
装机侧版本字面量全量同步后复跑：`test_obs180_set_one_live_allowed` **转绿**（同批 60 项全绿），doctor 复跑 `FAIL_CLOSED=False / PASS`。即该红是「版本字面量半同步」的中间态，非本档代码缺陷。**relock #118 落成后主智能体再复测：含该用例在内的 `test_hf77al_upload_batches.py + test_obs304 + test_obs180` 共 21 项全绿，确认闭合。**

### 标准 3｜relock 恰 1 次 media（entry 备份在册、history+1；其余四条目原值不动）+ R93 锁 sha 双侧一致

**达成（主智能体接续落成）**。执行端实测（干跑 CHANGED + 两次 classic 模式 post-doctor 回滚）后停机；主智能体接续：feat `4ed3524` 提交推送后，以仓根 `--source-tree F:\AIXM\wxgzh-skills`（注：报告初版复现命令误写 skill 子目录路径，lock 条目带 path 时 witness 要的是仓根，已更正）+ `--source-commit 4ed3524…` 全字段模式跑 `--apply`，一次通过。实测：
- 装机侧字节级同步（`Copy-Item` 保字节，9 文件逐一 SHA256 比对 match=True）后干跑：
```
=== media-enrichment ===
installed_dir: F:\AIXM\wxgzh\.agents\skills\media-enrichment
skill_root_sha256: e2a4f3175ee7de688dab89524839aa85234dfb1813ef5ff20331f1dd39c0b0b9 -> b12bba59a0cdd16f2035012bb678f70cc3f5cb9a892c05f09e3397ffbe4add31  (CHANGED)
runtime_manifest_sha256: 5533c0c87bffe322f7d90e4a02e23d2044ec1dcf70328e73b170289699b270d8 -> 5533c0c87bffe322f7d90e4a02e23d2044ec1dcf70328e73b170289699b270d8
runtime_file_count: 59 -> 59
status: CHANGED
dry-run: 1 skill(s) checked, 1 CHANGED — run with --apply to write (none written)
```
- `--apply` **两次均回滚**（`exit code 4`，`rollback: skills.lock.json, ledger and installed tree restored byte-identically`），每次日志顺序为：`doctor gate: allowed` → `backup: ...skills.lock.<UTC>.json` → `ledger: relock-media-enrichment-<UTC>-<hex> (media-enrichment)` → doctor 输出（`FAIL_CLOSED: true`、`doctor: FAIL`）→ 回滚。
- **doctor 拦点**：`media-enrichment` 的 `locked_version=0.1.0-dev36` vs `current_version=0.1.0-dev37`（classic 模式不写 `skill_version` 字段）。即本档必须走 `--source-tree/--source-commit` 全字段模式，而该模式强制 OBS-74 远端见证（commit 必须在远端存在且 tree 逐字节相同），与「执行端禁 commit」结构性冲突（77AC 先例）。
- **回滚后锁链零残留（实测）**：仓侧/装机侧 lock sha 双侧 = `79f5cf7e70c680a12239b2ae9d9234a6b059c84aaa7209c3146b9cad35ba1c8d`（= 基线）；`skills.lock.history.json` 仍 114 条；装机侧 6 个关键文件与仓侧逐字节 match=True；其余四条 lock 条目未被触碰（回滚即恢复原字节）。
- **残余**：两次 apply 各留一份 apply 前锁副本（未提交、无对应 history 条目）：`skills/wxgzh-pipeline/audit/upgrade-capability/lock-backups/skills.lock.20260915T121639Z.json`、`...20260915T121753Z.json`（各 5510B，内容 = `79f5cf7e...` 锁原文）。
- 复现命令（主智能体接续用，已实测通过；注意 `--source-tree` 给仓根，lock 条目带 path，witness 会拼 `work_tree = source_tree/path`）：
```
cd F:\AIXM\wxgzh-skills\skills\wxgzh-pipeline
python scripts\relock.py --skill media-enrichment --reason "<77AL/OBS-389 上传批次并发 dev36->dev37>" `
  --source-tree F:\AIXM\wxgzh-skills --source-commit <40-hex 已推送 commit> `
  --project-root F:\AIXM\wxgzh --skills-home F:\AIXM\wxgzh\.agents\skills --apply
```
预期：entry 变 `skill_root_sha256` + `skill_version` + `full_commit_sha` + `source_tree_sha`（manifest / 文件数 59 不变）；history 114→115；backup 新增 1 份。
- **落成实录（主智能体 2026-09-15，feat `4ed3524` 推送后执行）**：`--apply` 一次通过——`doctor gate: allowed` → `backup: skills.lock.20260915T123452Z.json` → `ledger: relock-media-enrichment-20260915T123452Z-4c19410d` → `installer: PASS` → `doctor: PASS (post-relock)` → entrypoint smoke PASS。落盘：media 条目 `skill_version` dev36→dev37、`skill_root_sha256` e2a4f317…→24a2295b…、`entrypoint_sha256` 327867a8…→1d3ce372…（run_media_enrichment.py）、`full_commit_sha`→`4ed3524…`、`source_tree_sha`→`d79474c4…`；history 114→115；新锁 sha `5e9b419b…`；R93 `observability.py` 双侧同步（+77AL relock #118 注释行）后 doctor 双侧 PASS + OBS_69/OBS_68 双 MATCH（815/815）。附带教训（77AA-F 附记③同型再现）：首跑 regression 全红系调用时未带 `WXGZH_PROJECT_ROOT`（回退到 `C:\Users\Admin`）+ R93 未同步；立规——relock/回归调用必带 `WXGZH_PROJECT_ROOT=F:\AIXM\wxgzh`，R93 同操作同步。最终回归（正确根+R93 同步后）：仅 obs154×1 既存红（在册），dry-run×4 无变化，doctor --require-wechat PASS。

### 标准 4｜台账：OBS-389 落账 + 口径 +1 + 授权登记行随 feat（顺延制）

实测（`.work/77al-ledger-check.py`，只读）：
```
全文件 OBS 表行 = 292   区间 = 119 - 389   缺号 = []
OBS-389 在册 = True
R59 未修分区 = 79
口径编号条目 = 89   最大 = 104   缺号 = [55..69]
口径 104 在册 = True
77AL 授权登记行(五十九次) 在册 = True
```
落账内容：
- 全表新增 `| 389 | … | 已修(77AL:①批次并发…②契约口径…③测试…) | … | 77AL |` 一行
- 口径新增 `104. 77AL(...)` 一块（序数按台账实况顺延：77AK 已占 103）
- 授权变更登记节新增 77AL 行（序数按台账实况顺延：**五十九次**，77AK 已占五十八）
- 未改任何历史行：`git diff --stat` = `1 file changed, 3 insertions(+)`

### 标准 5｜doctor 双侧 PASS + OBS_69/OBS_68 双侧 MATCH

- **基线（改动前）**：`doctor=PASS`、`FAIL_CLOSED=False`、`OBS_69=MATCH`、`OBS_68=MATCH`（813/813，diff 0）
- **改动后（会话结束态，装机侧全量同步后实测）**：`doctor=PASS`、`FAIL_CLOSED=False`、`skills_locked_ok=True`
  - `media_enrichment.ok = true`（装机侧 dev37 已与仓侧一致；relock 后锁内 `skill_version` 亦将同步为 dev37）
  - `OBS_69_LOCK_MATCH.status=MATCH`（baseline=installed=`79f5cf7e70c680a12239b2ae9d9234a6b059c84aaa7209c3146b9cad35ba1c8d`）
  - `OBS_68_PIPELINE_MATCH.status=DIFF`：`repo_file_count=816`、`installed_file_count=814`、`diff_total=0`、`missing_total=2`，缺失项 = **本档两次回滚留下的 2 份 lock-backups 副本**（`skills.lock.20260915T121639Z.json`、`skills.lock.20260915T121753Z.json`，只存在于仓侧、未装机未提交）。即 DIFF 的唯一成因是本次失败尝试的留痕文件，非代码/契约差异；该 2 份文件处置后（或由成功 relock 的正常 backup 取代后）即 MATCH。
- `test_obs180_set_one_live_allowed` 在**装机侧同步前**为红、**同步后转绿**（同一条实测：同步前 media `version_ok=false`→`FAIL_CLOSED=true`；同步+doctor 复跑后 `FAIL_CLOSED=false`）。
- **预测新锁 SHA（用工具 `_serialize_lock` 口径离线预算，供主智能体核对）**：仅写入 `skill_root_sha256=b12bba59…` + `skill_version=0.1.0-dev37` 后 = `6a87c4ff4755e43dd5666338585ecd89bb800b8416b136237d82ed541f961317`（当前 = `79f5cf7e…`）。写入 `full_commit_sha`/`source_tree_sha` 后该值会变，最终以实测为准；此处只证明「R93 必然要改」。

---

## 4. 环境与口径说明

- `WXGZH_SKIP_VERSION_CHECK=1` 仅用于测试与 doctor 复跑（77X/OBS-360 既有开关）。
- pytest 全量分层跑：pipeline 与 media 分两次跑（未合跑），如实记录。
- 装机侧同步全部用 `Copy-Item` 保字节，同步后逐一 SHA256 比对（见 §2.4 与 §5）。

---

## 5. 停机点（已解除——主智能体接续落成，原文留痕）

0. **解除实录（主智能体 2026-09-15）**：feat `4ed3524` 推送后全字段模式 `--apply` 一次通过，relock **#118 落成**；R93 双侧同步后 doctor 双 MATCH；最终回归仅 obs154×1 既存红。以下 1–3 为执行端停机原文，留痕备查：

1. **relock 无法在本会话落成**：本档必须用 `--source-tree/--source-commit` 全字段模式（classic 模式不写 `skill_version`，doctor 必拦，已两次实测回滚）；该模式强制 OBS-74 远端见证 = 该 commit 必须已在远端且 tree 逐字节相同；执行端硬规则**禁 commit**，用户**禁 push**（不可逆门）。→ 需主智能体在 commit + push 后执行 §3 标准 3 的复现命令。
2. **R93 锁 sha 双侧一致**待 relock 落成后执行（`observability.py` 的 `REPO_LOCK_SHA256` + 装机侧锁文件 + 装机侧 `observability.py`）。
3. **越界 1 处（唯一；77AL-R 已追认）**：`skills/wxgzh-pipeline/wxgzh_pipeline/contracts.py` 不在权威简报「允许改动的文件」清单内。它是 `upload.serial` / `upload_no_overlap` 的机器判据所在——契约改成批次并发而判据仍按逐对判定时，任何真实并发上传都会在媒体阶段契约层 FAIL（已实测：修好前 32 条 pipeline 用例红）。77AL-R 追认（审核方 2026-09-15，用户已批，见台账 77AL 授权行尾）：机器门禁必需改动，已披露，无其他越界。

---

## 6. 收益如实声明

- 上传并行省约 **15–20s**：24 张实测串行跨度 21.453s（tjyl4w `upload_events.json`）→ 本档 CLI 实测批次并发后事件表跨度 0.016s。
- **不承诺整篇 `run_wall` 削减数字**。media 阶段 wall 301s 中阶段实体仅 24s（§1.8），上传串行只占其中 21.453s；其余约 277s 在阶段体外，不属本档。
- **限制**：本档零 live 网络上传实证（CLI 全离线 fixture + `wechat_audit` 确定性上传器）；真并发实证来自测试内 `_SlowUploader`（`max_inflight=4`），非真实微信 API。

---

## 7. 观察项与「想做但没做」

① `skills/media-enrichment/CHANGELOG.md` 未加 dev37 条目（77AB/77AD/77AG 先例均有）。理由：权威简报只列 `VERSION`，未列 CHANGELOG；且机械替换会误改历史条目标题（实测一次后已 `git checkout` 还原）。
② 装机侧 media 树与锁已一致（relock #118 落成：锁内 `skill_version`=dev37；该回退预案作废，未执行）。
③ 两次回滚留下的 2 份 `lock-backups`（无对应 history 条目）已由主智能体删除（内容=基线锁原文，冗余残留；成功 relock 的正常 backup `skills.lock.20260915T123452Z.json` 在册）；OBS_68 回到 MATCH（815/815）。
④ 未做：上传并发对「已上传跳过」路径的时间语义变化；下载阶段并行（下载仍串行，无必需性证据支撑）。
⑤ `.work/task-77al-upload-parallel.md` 指针简报为本会话为通过 flow-gate 而登记（内容原样抄自权威简报），**不新增、不放宽任何范围**（唯一偏差项已在其中显式标注）。

---

## 8. 改动文件清单（含逐项一句话）

### 生产代码（in-scope）
1. `skills/media-enrichment/src/media_enrichment/uploader.py` — 并发上限常量 + 事件锁 + 批次并发执行器 + 事件批次标记
2. `skills/media-enrichment/scripts/run_media_enrichment.py` — 上传循环拆「登记计划→批次并发→同序回写」，事件表增 `parallel_workers`
3. `skills/wxgzh-pipeline/contracts/04_media_enrichment.yaml` — `parallel_workers`/`overlap_semantics` 口径
4. `skills/wxgzh-pipeline/wxgzh_pipeline/contracts.py` — 重叠判定改批次分区 + 台账一致性检查（**越界 1 处，见 §5.3**）
5. `skills/wxgzh-pipeline/wxgzh_pipeline/stages/media_enrichment.py` — 文案：serial → batch-parallel

### 测试（新增）
6. `skills/media-enrichment/tests/test_hf77al_upload_parallel.py` — 3 用例
7. `skills/wxgzh-pipeline/tests/test_hf77al_upload_batches.py` — 5 用例

### 升版 / 版本字面量同步
8. `skills/media-enrichment/VERSION` — dev36→dev37
9. `skills/media-enrichment/src/media_enrichment/__init__.py` — 版本字面量
10. `skills/media-enrichment/src/media_enrichment/input_contract.py` — `SKILL_VERSION`
11. `skills/media-enrichment/src/media_enrichment/url_security.py` — User-Agent 版本（2 处）
12. `skills/media-enrichment/scripts/build_zip.py` — `BUILD_VERSION` + docstring
13. `skills/media-enrichment/scripts/generate_evidence.py` — `VERSION` + docstring
14. `skills/media-enrichment/scripts/_verify_dev7.py` — `REQUIRED_VERSION`
15. `skills/media-enrichment/README.md` — 版本行
16. `skills/media-enrichment/WXGZH_PIPELINE_INTEGRATION.md` — 版本表行
17. `skills/media-enrichment/tests/test_runner_integration.py` — `CURRENT` 常量
18. `skills/media-enrichment/tests/test_uploader_manifest.py` — 版本断言串
19. `skills/wxgzh-pipeline/VERSION` — hotfix9R35→9R36
20. `skills/wxgzh-pipeline/tests/test_hf76r.py` — obs304 唯一编号钉子 270→271 / range(119,389)→(119,390)（台账顺延的既有口径）

### 台账
21. `skills/wxgzh-pipeline/audit/quality/obs-ledger.md` — OBS-389 行 + 口径 104 + 授权登记行（3 行新增，历史行零改）

### 未跟踪残余（已处置）
22–23. 两次回滚留痕 `skills.lock.20260915T121639Z.json` / `...121753Z.json`——主智能体已删除（冗余残留，内容=基线锁原文）；成功 relock 的正常 backup `skills.lock.20260915T123452Z.json` 在册，随 docs 落账。

---

## 9. 未命中 G1–G7 / 未触禁区声明

- 未触碰 `skills/super-writer/`、`zh-human-writing/`、`gzh-design/`、`aihot/` 任一文件（`git status` 无相关路径）
- 未触碰 `wxgzh_pipeline/producers.py`、`orchestrator.py`（77AL 无必需接线，未做无用改动）
- 未触碰历史 RUN 产物、`.env`、台账历史行；`skills.lock.json`/history 的改动系 relock #118 正常写盘（entry+history+1+backup，随 docs 落账，非手改）
- 未 commit、未 push、未打 tag
