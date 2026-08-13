# 档 56 — OBS-80 冒烟样本补齐(不 relock)

- 日期:2026-08-04
- 状态:**通过**。未执行 relock、未动 lock、未改被锁 skill 内容。

---

## 15. 三个 skill 的生产入口调用方式与冒烟方案

| skill | 生产入口(lock entrypoint) | CLI 调用方式 | 冒烟方案 |
|---|---|---|---|
| super-writer | `scripts/material_ingestion.py` | `--ledger <material-ledger.yaml> --output <report.json> [--json]` | 最小合法 ledger(1 素材+1 事件)跑通,rc=0 |
| zh-human-writing | `scripts/fidelity_guard.py`(entry==validator) | `--original <file> --edited <file> [--output json]` | skill 侧现成样本 `examples/01-author-preserve/input.txt` 作 original==edited(零改动),rc=0 |
| media-enrichment | `scripts/run_media_enrichment.py` | `--request <json> --output-dir <dir> [--fixture-dir <dir>] --phase discover` | 离线 fixture 模式(request+article+2 个 html fixture),rc=0,零网络 |

- 实测(已锁版本,CLI 生产路径):三锁冒烟 **全部 rc=0**(super-writer 100%/zh 0 warnings/media Errors:0)。
- 关键发现:media 冒烟必须走 `--fixture-dir` 离线模式(URL slug → `<slug>.html` 映射,`page_fetcher.py` L93-94);skill 侧 `examples/media_enrichment_request.example.json` 的 article.path 相对解析缺 article.md,故样本自包含。

## 16. 样本位置:混合方案(理由)

- **引用 skill 侧现成样本**(不新增文件):zh-human-writing `examples/01-author-preserve/input.txt`。
- **新造样本放 Pipeline 侧** `scripts/smoke-samples/`:
  - `super-writer/material-ledger.smoke.yaml`(skill 侧 k3-material-ledger.yaml 是聚合摘要格式,total_count=192 与 materials 0 失配,不可用)
  - `media-enrichment/media_enrichment_request.smoke.json` + `article.md` + `fixtures/article-001.html|article-002.html`
- **理由**:(a) 本档即可实施——不改被锁 skill 树(禁令),样本不污染被锁树(被锁树任何文件变化都需 relock 重算,样本放 skill 侧会无谓触发 root 变化);(b) 样本是验证基础设施,与 skill 交付物分离,维护集中在 relock 同目录;(c) skill 侧现成样本优先引用,避免复制。
- 若未来某 skill 必须把样本放进 skill 侧(如入口需要 skill 私有数据),按档 56 规则留待该 skill 升级时一并做。

## 17. relock 样本发现与加载逻辑(已实施)

- `scripts/relock.py` `SMOKE_ENTRIES` 扩为四锁(super-writer / zh-human-writing / media-enrichment / gzh-design):
  - 新增 `{sample_dir}` 占位符(→ `scripts/smoke-samples/`),`_run_entry_smoke` 传入;`{skill_dir}`/`{smoke_dir}` 语义不变
  - 冒烟入口仍以 lock entrypoint 为准(lock wins over config,既有逻辑)
  - 无样本配置的 skill 显式打印「无入口样本,跳过冒烟」(既有逻辑,不静默)
- 测试 `tests/test_obs80_smoke_samples.py` 6 项:SMOKE_ENTRIES 覆盖四锁 / 每锁样本路径存在 / entry 前缀校验。**6/6 通过**。

## 18. 冒烟演练(不 apply,不改 lock)——四锁全 PASS

```
gzh-design: entrypoint smoke PASS (CLI subprocess, production path)
super-writer: entrypoint smoke PASS (CLI subprocess, production path)
zh-human-writing: entrypoint smoke PASS (CLI subprocess, production path)
media-enrichment: entrypoint smoke PASS (CLI subprocess, production path)
```
- 演练直接调用 relock 的 `_run_entry_smoke`(生产 CLI 子进程),对**当前已锁版本**执行;未写 lock、未改安装树。
- 意义:档 57(media full_commit_sha relock)与后续任何 skill 升版的 relock 将自动对四锁执行入口冒烟。

## 复核

- upgrade_regression **ALL PASS**(含新 6 项;1 项显式排除;四锁 dry-run 无变化;doctor PASS;cross-side SKIP)
- 双侧 doctor PASS;lock `8FCBC203…` 未变;台账 4 条;安装侧与 repo HEAD 逐字一致
- 微信副作用:0;本档未调微信、未发起新 RUN
