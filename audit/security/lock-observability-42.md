# 档 42 — OBS-68/69 可观测性建设(只做检测,不做阻断)

- 报告编号:lock-observability-42
- 执行日期:2026-08-02(Asia/Shanghai)
- 前置:档 41 全部通过并 push(`720cff5`),按 R1 进入本档。
- 范围:仅 Pipeline 侧代码 + 测试 + 报告;未修改 `.agents\skills` 下任何被锁 skill(同步经正式安装器,内容逐字未变);未 relock --apply;未改任何 lock;未调微信接口;未跑完整 Pipeline;未删除任何文件;TEMP_CLEANUP_ALLOWED=false。
- 工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(dev/0.1.0-dev2,起点 HEAD `720cff5`)

## 设计边界(先读)

本档只让 doctor「看见」两个问题并如实报告:**未接入任何运行期阻断**;新增检查项一律 WARN 级,不参与 doctor 的 PASS/FAIL 结论,不改变退出码。是否阻断由审核者看过真实数据后另行裁决。

## 第一 OBS-69 检测:安装侧 lock 与仓库侧 lock 的一致性

1. 内嵌常量:新模块 `wxgzh_pipeline/observability.py` `REPO_LOCK_SHA256 = "a9e07ef42017cff225158466213253baf1155f34a7c2f1bdaf62a87dbbc751d6"`(仓库侧 skills.lock.json 当前值),注释标明更新时机(每次仓库 lock 变更须同 commit 更新;测试 `test_embedded_baseline_pins_repo_lock` 将该常量钉死到仓库 lock,作为常量自身的完整性守卫)。
2. doctor 检查:`check_lock_consistency(installed_lock, repo_lock)` 实算安装侧 `skills_home/wxgzh-pipeline/skills.lock.json` 的 sha256,与内嵌基线比对。
3. 三种输出:`MATCH`(两 sha 一致)/ `MISMATCH`(打印两个 sha + 逐 skill 字段差异摘要,repo lock 可读时)/ `NO_BASELINE`(常量缺失或格式非法)。
4. 以 `report["observability"]["OBS_69_LOCK_MATCH"]` 输出,**不改 doctor 退出码**。
5. 必须诚实记录的局限(不夸大):内嵌常量本身位于可被修改的 Pipeline 源码中,同时修改代码与 lock 仍可绕过此检查。本检查的价值在于让不一致「显形」,不在于阻止篡改。

## 第二 OBS-68 检测:安装侧 Pipeline 与仓库 HEAD 的一致性

6. doctor 新增 `check_pipeline_consistency(installed_pipeline, repo_root)`:按与正式安装器一致的 release-include 规则(zipping `_skip` + PIPELINE_RELEASE_INCLUDES/EXCLUDES,与 `copy_tree` 同口径)枚举两侧 runtime 文件,输出文件数、逐文件 sha 差异清单、缺失清单、多余清单。
7. 仓库路径:`--repo-root` 参数或 `WXGZH_REPO_ROOT` 环境变量;取不到 → `SKIPPED_NO_REPO`(非报错)。
8. WARN 级,不改退出码。
9. 正确性验收:档 37/40 人工做过「安装侧与 repo HEAD 逐字一致」,本检查自动复现(本档同步后 568 文件、0 差异,见第四步)。

## 第三 测试

新测试 `tests/test_observability.py`(9 项,全部 PASS,`9 passed in 0.58s`):

| 测试 | 覆盖 |
|---|---|
| test_lock_check_match | 一致 → MATCH |
| test_lock_check_mismatch_reports_both_shas_and_field_diff | 人为改 lock 中 media root → MISMATCH + 两个 sha + diff_summary 含 `media-enrichment.skill_root_sha256` |
| test_lock_check_no_baseline | 常量被改为非法值 → NO_BASELINE |
| test_embedded_baseline_pins_repo_lock | 内嵌常量 == 仓库 lock 实算 sha(常量防漂移) |
| test_pipeline_check_match | 两侧相同 → MATCH,文件数一致 |
| test_pipeline_check_mismatch_lists_diff_missing_extra | 改一个/删一个/加一个 → DIFF,三清单逐字正确 |
| test_pipeline_check_skipped_no_repo | repo_root=None → SKIPPED_NO_REPO |
| test_doctor_exit_code_unchanged_with_mismatches | **重要**:构造 OBS-69 MISMATCH + OBS-68 DIFF,子进程跑 doctor → 退出码仍为 0、`doctor=PASS`、observability 如实报告 MISMATCH/DIFF(安全边界显式断言) |
| test_doctor_observability_skipped_without_repo_root | 无 repo root → SKIPPED_NO_REPO,退出码 0 |

- 不一致场景全部在 pytest `tmp_path` 沙箱中构造,沙箱随测试结束自动清理;真实 `.agents\skills` 未被制造任何不一致。

## 第四 真实环境实测

同步前(仅改完代码、未安装器同步)跑 doctor(`--repo-root F:\AIXM\wxgzh\repos\wxgzh-pipeline`):
- `OBS_69_LOCK_MATCH`: **MATCH**(两侧 `a9e07ef4…`)
- `OBS_68_PIPELINE_MATCH`: **DIFF** —— 如实记录,原因明确:档 42 自身新增/修改的 4 个文件(observability.py、test_observability.py、两份审计报告)与 2 个改动文件(doctor.py、orchestrator.py)尚未同步到安装侧;检查精确列出 `diff_files=[scripts/doctor.py, wxgzh_pipeline/orchestrator.py]`、`missing_files=[audit/quality/intro-guard-40.md, audit/quality/material-injection-survey-41.md, tests/test_observability.py, wxgzh_pipeline/observability.py]`、`extra_files=[]`。这是本档自身改动造成的预期中间态,不是环境异常。

正式安装器同步后(见第五步),双侧复测:
- 安装侧 doctor:`OBS_69_LOCK_MATCH=MATCH`、`OBS_68_PIPELINE_MATCH=MATCH`(repo 568 / installed 568,diff/missing/extra 全 0),`doctor=PASS`,退出码 0。
- 仓库侧 doctor:同上,`doctor=PASS`,退出码 0。
- 完整输出见附件 A(安装侧,同步后)。

## 第五 回归与同步

15. `scripts/upgrade_regression.py`:**ALL PASS**,排除清单仍 1 项(portable installer 常量项,未扩大);四锁 relock dry-run 全部「无变化」。
16. 四锁 relock dry-run:super-writer / zh-human-writing / media-enrichment / gzh-design 全部「无变化」。
17. doctor `--require-wechat` 双侧 PASS,退出码 0(与本档前一致)。
18. 正式安装器同步:构建 `F:\AIXM\wxgzh\bundle-staging-42\portable-bundle`(568 文件镜像 + 24S 基线四锁;密钥扫描 `secrets_detected=false`);dry-run `ok=true`,实装 `ok=true`(四锁 commit/source_tree/repository/runtime_root/runtime_manifest/receipt/verify_all 全 true);安装侧与 repo HEAD **568 文件逐字一致**(0 差异、无缺失无多余)。
19. 两侧 `skills.lock.json` sha256 均 `a9e07ef4…`(本档前后一致,逐字未动);`skills.lock.history.json`(台账)不存在(未动);证据目录(bundle-staging-37/40、24S 暂存、incident 副本)完好。

## 附件 A:安装侧 doctor 完整输出(同步后,2026-08-02)

```json
{
  "wxgzh_pipeline_version": "0.1.0-dev2-hotfix7R4",
  "project_root": "F:\\AIXM\\wxgzh",
  "skills_home": "F:\\AIXM\\wxgzh\\.agents\\skills",
  "network_mode": "live",
  "skills_locked_ok": true,
  "skills": {
    "super-writer": {"version_ok": true, "hash_ok": true, "entrypoints_ok": true, "ok": true},
    "zh-human-writing": {"version_ok": true, "hash_ok": true, "entrypoints_ok": true, "ok": true},
    "media-enrichment": {"version_ok": true, "hash_ok": true, "entrypoints_ok": true, "ok": true,
                         "current_root_sha256": "0d8aea2169cec17c4e9f95af66b6b4da3c532554a0a316fe3fb604bd0b7ab3a3"},
    "gzh-design": {"version_ok": true, "hash_ok": true, "entrypoints_ok": true, "ok": true,
                   "current_root_sha256": "9a8cd7f548c2186f789a5e24235001308fc6a868e0f57d74fc06c8919b4ff79b"},
    "aihot": {"EXTERNAL_DEPENDENCY_AIHOT": "INSTALLED", "live_pipeline_allowed": true, "ok": true}
  },
  "EXTERNAL_DEPENDENCY_AIHOT": "INSTALLED",
  "LIVE_PIPELINE_ALLOWED": true,
  "wechat_config_present": true,
  "FAIL_CLOSED": false,
  "doctor": "PASS",
  "observability": {
    "OBS_69_LOCK_MATCH": {
      "status": "MATCH",
      "baseline_sha256": "a9e07ef42017cff225158466213253baf1155f34a7c2f1bdaf62a87dbbc751d6",
      "installed_sha256": "a9e07ef42017cff225158466213253baf1155f34a7c2f1bdaf62a87dbbc751d6"
    },
    "OBS_68_PIPELINE_MATCH": {
      "status": "MATCH",
      "repo_file_count": 568,
      "installed_file_count": 568,
      "diff_files": [],
      "missing_files": [],
      "extra_files": [],
      "diff_total": 0,
      "missing_total": 0,
      "extra_total": 0
    }
  }
}
```

(注:上为 doctor 输出的可读摘要;完整 JSON 已落盘 `.temp\doctor-42-installed.txt`,字段与摘要一致;`aihot.note` 中文在控制台为显示问题,文件内容正常。)

## 风险点与说明

1. 两项检查均为 WARN,当前不阻断;若日后要接入阻断,需审核者另行授权,并把检查并入 `ok` 判定与 `FAIL_CLOSED`。
2. OBS-69 内嵌常量需与仓库 lock 同 commit 更新;测试已钉死,lock 变更未同步常量会导致 pytest 失败(有意为之)。
3. OBS-68 只覆盖 release-include 文件集(.git/.github 排除、tests 排除的规则与安装器一致);若 repo 出现未提交改动,检查会如实报 DIFF(本次实测已证明其灵敏度)。
