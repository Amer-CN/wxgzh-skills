# OBS-62S · 同步安装副本(收尾闭环)

## 目的

把 OBS-62R 修复(`validators/validate_draft_delta.py` 新判定逻辑)经正式安装流程同步到
已安装副本 `F:\AIXM\wxgzh\.agents\skills\wxgzh-pipeline`。

## 执行流程

1. 构造正式结构 bundle:`F:\AIXM\wxgzh\.temp\obs62s-build-staging\portable-bundle`
   - `wxgzh-pipeline/` = 仓库正式复制规则全量镜像(432 文件,含 audit)
   - `locked-skills/` = 当前已安装 4 个被锁子 skill 的完整副本
   - `MANIFEST.json` 逐文件 sha256 哈希绑定(967 文件)、`source-proofs.json` 与 `skills.lock.json` 一致
   - 密钥扫描通过(`secrets_detected=false`)
2. 正式安装器安装(事务化,backup + 回滚 + 安装 receipts):
   - `installer/install.py --target F:\AIXM\wxgzh\.agents\skills --dry-run` → ok=true
   - `installer/install.py --target F:\AIXM\wxgzh\.agents\skills` → ok=true,
     4 个被锁子 skill 均 `commit_match/source_tree_match/repository_match/runtime_root_match/runtime_manifest_match/verify_all_ok=true`

## 校验结果

- `validators/validate_draft_delta.py` sha256:
  - 仓库 `F:\AIXM\wxgzh\repos\wxgzh-pipeline`:`428ad6ee0e0e6f383a09325763ee82a46b92bd7612f4c1ce51c744daa1c77f5f`
  - 安装副本 `F:\AIXM\wxgzh\.agents\skills\wxgzh-pipeline`:`428ad6ee0e0e6f383a09325763ee82a46b92bd7612f4c1ce51c744daa1c77f5f`
  - 两侧一致,且等于 OBS-62R 交付 sha
- 4 个被锁子 skill 运行时根哈希(安装前 → 安装后,逐字相同,未污染):
  - super-writer:`46a00a1b…` → `46a00a1b…`(50 文件)
  - zh-human-writing:`18491b36…` → `18491b36…`(53 文件)
  - media-enrichment:`0d8aea21…` → `0d8aea21…`(57 文件)
  - gzh-design:`9a8cd7f5…` → `9a8cd7f5…`(76 文件)
- doctor 复验(安装副本执行,`--project-root F:\AIXM\wxgzh --require-wechat`):
  `skills_locked_ok=true`、四个锁定子 skill `hash_ok=true`、`EXTERNAL_DEPENDENCY_AIHOT=INSTALLED`、
  `LIVE_PIPELINE_ALLOWED=true`、`wechat_config_present=true`、`FAIL_CLOSED=false`、`doctor=PASS`
- 三组离线复算(安装副本 validator,未调用微信接口,只读已落盘数据):
  - RUN 20260801T182628-topic-ui5f7p → exit=0 PASS
  - RUN 20260731T135947-ai-bbg4al → exit=0 PASS
  - 模拟「删一份建一份」→ exit=1 FAIL
  - 三组 exit_code 与完整 report 与 `delta_revalidation.json` 逐字段一致(`ALL_MATCH=true`)

## 副作用说明

- `.install-receipts/*.json` 由正式安装器重写:锁定值(commit/root/manifest/tree/version)全部不变,
  仅 `installed_at` 更新为 `2026-08-01T12:54:36Z`
- 未修改任何被锁子 skill 内容、未重锁 `skills.lock.json`、未修改任何已有 run receipt、
  未调用微信接口、未删改草稿箱 2 份草稿、未删除任何文件
- 仓库侧无代码改动;本记录为本次同步的审计证据
