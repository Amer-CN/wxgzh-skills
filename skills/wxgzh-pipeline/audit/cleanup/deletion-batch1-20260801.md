# 删除批次 1 — 2026-08-01

## 执行摘要

- 实删条目:**131**(inventory A 类 133 − 指令排除 2)
- 跳过条目:**0**(执行期无失败跳过)
- 释放字节:**61,652,119**(约 58.8 MB);释放文件数:**15,397**
- 删除后复核:131 条全部不存在;B/C 类条目 0 缺失;受保护 2 目录仍在
- doctor:`PASS`(完整输出见下)

## 前置校验结果

### 1. 早期 RUN 归档完整性(20260730T222605-ai-9je33o / 20260731T031531-ai-u8zlo6)

- 逐一比对 `.temp` 源目录与 repo 归档:按**内容 sha256(先做 LF 归一化)**核对。
- 结论:两个 RUN 的归档在 git HEAD 已完整(20260730T222605 归档 44 个 blob、
  20260731T031531 归档 46 个 blob,.temp 源文件 0 个未匹配)。
- 说明:工作树曾因 CRLF/LF 行尾与索引出现差异,经核对为同一内容的不同行尾形式,
  无需补档、无新提交;`git add/commit` 自然判定 nothing to commit。
- 按指令:这两个 `.temp` 目录**本轮未删除**,保留待下轮裁决。

### 2. 与根目录重复 zip 校验(5 个,.temp vs 根目录同名)

| zip | MATCH |
|---|---|
| media-enrichment-v0.1.0-dev5.zip | True |
| media-enrichment-v0.1.0-dev6.zip | True |
| media-enrichment-v0.1.0-dev6-hotfix1.zip | True |
| media-enrichment-v0.1.0-dev7.zip | True |
| media-enrichment-v0.1.0-dev7-hotfix1.zip | True |

全部逐字一致,已删除 `.temp` 副本(根目录副本保留)。

## 删除执行(SAFE_DELETE_FAIL_CLOSED)

- 待删清单:从 `inventory-20260801.md` 解析 **A** 类条目,排除 2 个受保护 RUN 目录后共 131 条。
- 删除前快照:`audit/cleanup/deletion-batch1-snapshot.json`(131 条,逐条完整路径 +
  文件 sha256 或目录文件数与大小;合计 61,652,119 字节 / 15,397 文件)。
- 逐条门禁(不满足即不删该条并报错):路径精确等于清单条目;以 `F:\AIXM\wxgzh\` 开头;
  `GetFullPath` 解析后仍在根内且与清单一致;非 `.env`;非受保护 RUN 目录。
- 执行:Powershell 单壳 `Remove-Item -LiteralPath -Recurse -Force`,131 条成功,0 错误。
- 未删除任何 B/C 类条目、`F:\AIXM\wxgzh-env-backup` 下任何内容、清单外任何路径。

## 删除后校验

- 已删路径仍存在:0
- A 类(除 2 个受保护目录)仍存在:0
- B/C 类条目缺失:0
- 受保护 RUN 目录仍存在:
  - `F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260730T222605-ai-9je33o` → True
  - `F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260731T031531-ai-u8zlo6` → True
- `F:\AIXM\wxgzh\.env` → True;`F:\AIXM\wxgzh-env-backup\.env` → True

## doctor 输出(删除后,完整)

```json
{
  "wxgzh_pipeline_version": "0.1.0-dev2-hotfix7R4",
  "project_root": "F:\\AIXM\\wxgzh",
  "skills_home": "F:\\AIXM\\wxgzh\\.agents\\skills",
  "network_mode": "live",
  "skills_locked_ok": true,
  "skills": {
    "super-writer": { "ok": true, "version_ok": true, "hash_ok": true, "entrypoints_ok": true, "missing_files": [], "locked_root_sha256": "46a00a1bcdd5eeafae1ce6723241f97a6c1cd92f14f7baf8dc3625c9aed3018a", "current_root_sha256": "46a00a1bcdd5eeafae1ce6723241f97a6c1cd92f14f7baf8dc3625c9aed3018a" },
    "zh-human-writing": { "ok": true, "version_ok": true, "hash_ok": true, "entrypoints_ok": true, "missing_files": [], "locked_root_sha256": "18491b361060a28d5eaf228f58b9b75e6ebde697eaa1149573bf468e0daea786", "current_root_sha256": "18491b361060a28d5eaf228f58b9b75e6ebde697eaa1149573bf468e0daea786" },
    "media-enrichment": { "ok": true, "version_ok": true, "hash_ok": true, "entrypoints_ok": true, "missing_files": [], "locked_root_sha256": "0d8aea2169cec17c4e9f95af66b6b4da3c532554a0a316fe3fb604bd0b7ab3a3", "current_root_sha256": "0d8aea2169cec17c4e9f95af66b6b4da3c532554a0a316fe3fb604bd0b7ab3a3" },
    "gzh-design": { "ok": true, "version_ok": true, "hash_ok": true, "entrypoints_ok": true, "missing_files": [], "locked_root_sha256": "9a8cd7f548c2186f789a5e24235001308fc6a868e0f57d74fc06c8919b4ff79b", "current_root_sha256": "9a8cd7f548c2186f789a5e24235001308fc6a868e0f57d74fc06c8919b4ff79b" },
    "aihot": { "kind": "agent_invoked_skill", "exists": true, "EXTERNAL_DEPENDENCY_AIHOT": "INSTALLED", "live_pipeline_allowed": true, "version_ok": true, "hash_ok": true, "entrypoints_ok": true, "ok": true }
  },
  "EXTERNAL_DEPENDENCY_AIHOT": "INSTALLED",
  "LIVE_PIPELINE_ALLOWED": true,
  "wechat_config_present": true,
  "wechat_credential_detail": { "WECHAT_APP_ID_nonempty": true, "WECHAT_APP_SECRET_nonempty": true },
  "wechat_required": true,
  "project_writable": true,
  "FAIL_CLOSED": false,
  "doctor": "PASS"
}
```

## 附件

- 删除前快照:`audit/cleanup/deletion-batch1-snapshot.json`
- 本轮新增工作文件(未删、未提交):`.temp\obs62s-delete-list.json`、`.temp\obs62s-runcompare.json`、`.temp\obs62s-build-staging\`(档24S bundle)
