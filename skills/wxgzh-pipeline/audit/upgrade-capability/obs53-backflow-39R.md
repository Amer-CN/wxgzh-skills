# 档 39R — OBS-53/47/44-46/42-43 四轮补丁回流 media-enrichment

- 报告编号:obs53-backflow-39R
- 执行日期:2026-08-02(Asia/Shanghai)
- 授权状态:media-enrichment push 仅限新分支;RELOCK_APPLY_ALLOWED=false / SKILLS_TREE_WRITE_ALLOWED=false / P2_START_ALLOWED=false / TEMP_CLEANUP_ALLOWED=false
- 遵守:未修改任何 skills.lock.json(两侧);未执行 relock;未执行安装器;未动 main/chore 分支;未建 PR;未合并;未 force push;未删除 bundle-staging-37、24S 暂存、证据副本;未调微信接口;未跑 Pipeline。
- 工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(dev/0.1.0-dev2,起点 HEAD `c339b36`)

---

## 第一步 建分支

- 全新 clone:`F:\AIXM\wxgzh\repos\media-enrichment-39r-build`
- 基准:远端 `chore/wxgzh-pipeline-dev2-integration` = `cedf92ca45b0cdb7e010d489e9da67dd28ef6e59`(建分支前 ls-remote 确认)
- 新分支:`restore/local-patches-obs42-53`,从 cedf92ca 创建
- 本档全部 git 写操作仅在该分支;main(`68076ed`)与 chore(`cedf92ca`)事后 ls-remote 复核未变。

## 第二步 按补丁拆分提交(时间顺序)

四个补丁包依次 `git apply -p2`(自 wxgzh-pipeline `audit/skill-patches/*/changes.diff` 提取 media 文件部分;obs47 排除 `wxgzh-pipeline/producers.py`、obs53 排除 wxgzh-pipeline 侧文件),每包一个 commit。**全部干净拆分,无跨补丁交织,未触发「合并进相邻 commit」的兜底条款**。

| # | commit sha | 内容 | relock commit(写入 message) |
|---|---|---|---|
| 1 | `963294faceed51adeefa615341c2d0a278bb71cf` | OBS-42/43:continue 冻结 discovery 消费、跳过发现循环、输出镜像 | `4c6416d1b79531171bdf259b8db3c33b56b5e485` |
| 2 | `57fee5110dfa84eb0d1c9ead10c660f6f44133c7` | obs44-46:uploader 观测字段 + 上传候选数封顶 | `dd880c04839f776d101e884ad6b1867b8734b1e1` |
| 3 | `3fa065dbc0163901f3aa71835922a7115f5babf4` | obs47:token 缓存 / 统一凭据来源 | `f5eb6b37ff151283a39faf9fb212eb631261d529` |
| 4 | `2595e01465399eb34a10a56b190399039578da9e` | OBS-53:idempotency(跳过既有 success 上传) | `7c914899772216261d4f895f4a3c2c86c3416ade` |

每条 message 均含:OBS 编号与内容摘要、对应 wxgzh-pipeline relock commit sha、统一事实说明(逐字):
> 此改动此前仅存在于本地安装树,从未推送;
> skills.lock.json 的 root_sha256 长期指向无远端副本的本地树。

### 拆分正确性的历史值逐级验证(强校验)

每提交一个补丁后,用 Pipeline 侧 `compute_root_sha` / `_file_sha`(同一算法,CRLF 归一)实算中间树,与历史上各 relock commit 写入 lock 的值逐字比对:

| 步骤 | 树 root(实算) | 历史 lock 记录值(来源 commit) | entrypoint(实算 vs 记录) | 结果 |
|---|---|---|---|---|
| cedf92ca 基准 | `b8257469…` | 4c6416d 前值 | `6429e4db…` | — |
| +obs42/43 | `e982b757…` | 4c6416d 新值 | `c99d5f50…` | 一致 |
| +obs44-46 | `a8500e7e…` | dd880c0 新值 | `4e081051…` | 一致 |
| +obs47 | `1dab6184…` | f5eb6b3 新值 | `a54deef3…` | 一致 |
| +obs53 | `0d8aea21…` | 7c91489 新值 = 当前 lock | `2d877a93…` | 一致 |

四个中间态全部命中历史锁定值,证明拆分与原始补丁施加顺序逐字等价,不是「凑哈希」。

## 第三步 树哈希验证(本档关卡)

- push 后全新 clone:`F:\AIXM\wxgzh\repos\media-enrichment-39r-verify`(branch `restore/local-patches-obs42-53`,HEAD `2595e01…`)
- 实算(Pipeline 侧 `compute_root_sha` / `compute_runtime_manifest_sha` / `_file_sha`):

| 项 | clone 实算 | lock 记录 | 结果 |
|---|---|---|---|
| root_sha256 | `0d8aea2169cec17c4e9f95af66b6b4da3c532554a0a316fe3fb604bd0b7ab3a3` | 同左 | 逐字一致 |
| runtime_manifest_sha256 | `172aa1b8082c6bb80822e56e201732ba5a118c6a53d7472f34b911f4a891e996` | 同左 | 逐字一致 |
| runtime_file_count | 57 | 57 | 一致 |
| entrypoint_sha256 | `2d877a93…` | `2d877a93…` | 一致 |

- 附加:clone 树与安装树(runtime 范围,排除 .git/.github/tests/__pycache__)逐文件内容比对 = **0 差异**。
- 结论:新分支树与 lock 指向的补丁态树逐字等价。未为凑哈希修改任何补丁内容、未补提交。

## 第四步 现状记录(未做修改)

1. media-enrichment 新分支 HEAD:`2595e01465399eb34a10a56b190399039578da9e`(`restore/local-patches-obs42-53`),已 push,远端确认存在。
2. lock 的 `full_commit_sha` 当前值:`cedf92ca45b0cdb7e010d489e9da67dd28ef6e59`(仍指向旧基准,本档未动)。
3. **lock 内部不一致尚未修复,留待后续单独处理**(commit sha ↔ root sha 指向不同树;现 root `0d8aea21` 已有远端权威副本,后续仅需把 full_commit_sha 更新为 `2595e01…`,需确认 relock 是否支持仅更新该字段,不支持则先做能力扩展并另行授权)。
4. OBS-74 描述已更新(新建 `audit/upgrade-capability/obs74.md`):「四轮补丁曾长期未回流;代码已回流至 restore/local-patches-obs42-53;lock 的 full_commit_sha 仍指向 cedf92ca,待修」。原描述仅存在于档 39 指令的 --apply reason 字符串,无其他既有文件,故新建。

## 第五步 复核

1. 真实环境逐字未变:
   - 两侧 skills.lock.json sha256 均 `A9E07EF42017CFF225158466213253BAF1155F34A7C2F1BDAF62A87DBBC751D6`(本档前后一致)
   - `skills.lock.history.json`(台账)两侧均不存在(本档前后一致)
   - 安装树 media root 实算 `0d8aea21…`(doctor 输出 current==locked)
   - 证据目录均在:`bundle-staging-37`、`.temp\obs62s-build-staging`、`F:\AIXM\wxgzh-incident-20260802\skills-asfound`、事件 RUN 归档
2. doctor --require-wechat(安装副本)仍 **PASS**:`skills_locked_ok=true`、四锁 `hash_ok=true`(super-writer/zh-human-writing/media-enrichment/gzh-design)、`EXTERNAL_DEPENDENCY_AIHOT=INSTALLED`、`LIVE_PIPELINE_ALLOWED=true`、`wechat_config_present=true`、`FAIL_CLOSED=false`、`doctor=PASS`(完整输出见附件 A)。

## 两个仓库 SHA

- Amer-CN/media-enrichment:`restore/local-patches-obs42-53` HEAD = `2595e01465399eb34a10a56b190399039578da9e`
- wxgzh-pipeline:本报告 commit = 见提交输出(档 39R 报告 commit)

## 附注

- 临时目录(未删除,TEMP_CLEANUP_ALLOWED=false):`F:\AIXM\wxgzh\repos\media-enrichment-39r-build`、`F:\AIXM\wxgzh\repos\media-enrichment-39r-verify`、`F:\AIXM\wxgzh\repos\media-enrichment-39r-patches`(拆分用 patch 文件)。
- 风险点:lock 不一致仍未修(预期,本档禁改);修复时 relock 需具备「仅更新 full_commit_sha/source_tree_sha」能力,否则需扩展;media 仓库 chore 分支与 main 未受任何影响。


## 附件 A:doctor 完整输出(安装副本,2026-08-02)

````json
{
  "wxgzh_pipeline_version": "0.1.0-dev2-hotfix7R4",
  "project_root": "F:\\AIXM\\wxgzh",
  "skills_home": "F:\\AIXM\\wxgzh\\.agents\\skills",
  "network_mode": "live",
  "skills_locked_ok": true,
  "skills": {
    "super-writer": {
      "skill_name": "super-writer",
      "skill_dir": "F:\\AIXM\\wxgzh\\.agents\\skills\\super-writer",
      "exists": true,
      "locked_version": "0.3.2-rc1",
      "current_version": "0.3.2-rc1",
      "locked_root_sha256": "46a00a1bcdd5eeafae1ce6723241f97a6c1cd92f14f7baf8dc3625c9aed3018a",
      "current_root_sha256": "46a00a1bcdd5eeafae1ce6723241f97a6c1cd92f14f7baf8dc3625c9aed3018a",
      "file_count": 50,
      "version_ok": true,
      "hash_ok": true,
      "entrypoints_ok": true,
      "missing_files": [],
      "ok": true
    },
    "zh-human-writing": {
      "skill_name": "zh-human-writing",
      "skill_dir": "F:\\AIXM\\wxgzh\\.agents\\skills\\zh-human-writing",
      "exists": true,
      "locked_version": "0.1.0",
      "current_version": "0.1.0",
      "locked_root_sha256": "18491b361060a28d5eaf228f58b9b75e6ebde697eaa1149573bf468e0daea786",
      "current_root_sha256": "18491b361060a28d5eaf228f58b9b75e6ebde697eaa1149573bf468e0daea786",
      "file_count": 53,
      "version_ok": true,
      "hash_ok": true,
      "entrypoints_ok": true,
      "missing_files": [],
      "ok": true
    },
    "media-enrichment": {
      "skill_name": "media-enrichment",
      "skill_dir": "F:\\AIXM\\wxgzh\\.agents\\skills\\media-enrichment",
      "exists": true,
      "locked_version": "0.1.0-dev7-hotfix4",
      "current_version": "0.1.0-dev7-hotfix4",
      "locked_root_sha256": "0d8aea2169cec17c4e9f95af66b6b4da3c532554a0a316fe3fb604bd0b7ab3a3",
      "current_root_sha256": "0d8aea2169cec17c4e9f95af66b6b4da3c532554a0a316fe3fb604bd0b7ab3a3",
      "file_count": 57,
      "version_ok": true,
      "hash_ok": true,
      "entrypoints_ok": true,
      "missing_files": [],
      "ok": true
    },
    "gzh-design": {
      "skill_name": "gzh-design",
      "skill_dir": "F:\\AIXM\\wxgzh\\.agents\\skills\\gzh-design",
      "exists": true,
      "locked_version": "v2026.07.18-hammer.1",
      "current_version": "v2026.07.18-hammer.1",
      "locked_root_sha256": "9a8cd7f548c2186f789a5e24235001308fc6a868e0f57d74fc06c8919b4ff79b",
      "current_root_sha256": "9a8cd7f548c2186f789a5e24235001308fc6a868e0f57d74fc06c8919b4ff79b",
      "file_count": 76,
      "version_ok": true,
      "hash_ok": true,
      "entrypoints_ok": true,
      "missing_files": [],
      "ok": true
    },
    "aihot": {
      "skill_name": "aihot",
      "kind": "agent_invoked_skill",
      "exists": true,
      "registration": "C:\\Users\\Admin\\.agents\\skills\\aihot\\registration.json",
      "EXTERNAL_DEPENDENCY_AIHOT": "INSTALLED",
      "live_pipeline_allowed": true,
      "version_ok": true,
      "hash_ok": true,
      "entrypoints_ok": true,
      "ok": true,
      "note": "external dependency (���ȿ�); capability checked for real (registration + output contract); never copied/modified/republished"
    }
  },
  "EXTERNAL_DEPENDENCY_AIHOT": "INSTALLED",
  "LIVE_PIPELINE_ALLOWED": true,
  "aihot_registration": "C:\\Users\\Admin\\.agents\\skills\\aihot\\registration.json",
  "aihot_checked_locations": [
    "F:\\AIXM\\wxgzh\\.agents\\skills\\aihot",
    "C:\\Users\\Admin\\.agents\\skills\\aihot"
  ],
  "wechat_config_present": true,
  "wechat_credential_detail": {
    "WECHAT_APP_ID_nonempty": true,
    "WECHAT_APP_SECRET_nonempty": true
  },
  "wechat_required": true,
  "project_writable": true,
  "FAIL_CLOSED": false,
  "doctor": "PASS"
}
````
