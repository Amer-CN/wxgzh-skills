# 档 40 — OBS-73 Pipeline 侧 intro 内容丢失守卫

- 报告编号:intro-guard-40
- 执行日期:2026-08-02(Asia/Shanghai)
- 范围:仅 Pipeline 侧代码 + 测试 + 报告;未修改 `.agents\skills` 下任何被锁 skill(同步经正式安装器,内容逐字未变);未 relock --apply;未改 lock;未调微信接口;未跑完整 Pipeline;未删除任何文件;TEMP_CLEANUP_ALLOWED=false(新临时目录保留)。
- 工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(dev/0.1.0-dev2,起点 HEAD `1b3e985`)

---

## 第一 实现

- 文件:`wxgzh_pipeline/stages/gzh_design.py` 的 `content_validate`。
- 冻结文章来源:与 media_enrichment 同一份 `ctx.run_dir/zh_human_writing/final_article.md`(execmodel `UPSTREAM_INPUTS` 中 gzh_design 与 media_enrichment 均绑定该文件);取不到即 `return 1, {"reason": "frozen final_article.md missing — OBS-73 intro guard cannot run"}` — **FAIL,不许跳过**。
- 新增 `_intro_guard_report(md_text)`:`INTRO_MAX_LEN = 40`(对应 render_article.py L127-128 oneliner `[:40]`)。提取逻辑与 `gzh-design/scripts/render_article.py` `parse_article()` L79-104 **逐行对应**,代码注释中标注了映射(L81 分行 / L88 H1 标题 / L92 首个 `## ` 结束 intro 区 / L95 其他 `#` 行跳过 / L97 空行跳过 / L99-102 首行作 intro、其余行被渲染器静默丢弃),并注明「gzh-design 升版修复后此守卫需同步复核」。
- 判定(第二):
  - `intro_line_count > 1`(即存在被丢弃段落)→ FAIL
  - `intro_line_count == 1` 且 `intro_char_count > 40`(oneliner 截断,取 40 而非 48,更严)→ FAIL
  - 均不命中 → PASS,并在 theme identity report 中写入 `INTRO_GUARD=PASS`
- FAIL 信息(`content_validate` 返回 report)包含:
  - a. `intro_line_count` / `intro_char_count`(实际行数、字符数)
  - b. `intro_dropped_text`(将被丢弃的原文全文:多行时为整段原文;单行超长时为 `intro[40:]` 截断尾部)
  - c. `guidance`(逐字):「首个 ## 之前只能有一行且不超过 40 字。请将导语内容并入第一个章节,或压缩为副标题。」
- 无任何跳过开关/环境变量/豁免参数(代码中不存在相关分支)。

## 第二 用历史数据验证守卫有效(第三)

测试文件:`tests/test_intro_guard.py`(9 项)。

| 输入 | 期望 | 实测 |
|---|---|---|
| RUN1 `20260731T135947-ai-bbg4al` final_article.md(2 段) | FAIL | `intro_line_count=2`,dropped 含 para2 全文(「本轮AI HOT素材把这种变化摆在了一起…正在成为安全流程里的行动者」)✓ |
| RUN2 `20260801T182628-topic-ui5f7p`(1 段 198 字符) | FAIL | `intro_line_count=1`, `intro_char_count=198 > 40`,dropped 为截断尾(含「出了问题找谁」)✓ |
| 事件 RUN `20260801T231452-vibe-coding-guide-v2-1-1vg6jx`(8 段) | FAIL | `intro_line_count=8`,dropped 含 para2-8(「说的是我做的 vibe-coding-guide」「今天先认个账」「那不叫安全气囊」「这次，纸条是真的变成锁了」等)✓ |
| 合规输入(单行 ≤40 字) | PASS | `ok=True`,`intro_line_count=1`,`intro_char_count<=40` ✓ |

三篇全部 FAIL、正向 PASS,守卫有效。另有两项补充测试:`test_guard_intro_matches_reference_parse_article`(在测试内独立复刻 parse_article L79-104,证明守卫首行选择与锁定渲染器一致——三篇 intro 字符数全部相等)与 `test_blank_and_heading_lines_are_skipped_like_parse_article`(空行/多余 H1/H3 不计入 intro 行)。

测试输出:`9 passed in 0.16s`(见附件 A)。

## 第三 确认不影响存量(第四)

1. 新增校验位于 `gzh_design.content_validate`,只在 `execute_stage` 对**当前 RUN** 执行(`wxgzh_pipeline/stages/__init__.py` execute_stage 每次运行现场调用);已归档 RUN 的 receipt 是落盘历史文件,新代码不读取、不重算、不重写它们。
2. `verify_receipt`(receipts.py)只做文件存在性/哈希/字段校验,不调用 content_validate,故既有 receipt 不会因新代码失效。
3. 全量 pytest(upgrade_regression 内)通过,离线/伪造夹具文章的 intro 均合规(offline fixture「导语。」3 字、fake_live fixture「开篇导语，交代背景与动机。」12 字),状态机类测试无行为变化。

## 第四 复核(第五)

1. `scripts/upgrade_regression.py`:**ALL PASS**(1 项显式排除不变:portable installer 常量问题;relock dry-run ×4 全部「无变化」;doctor PASS;gzh 两侧一致性步按设计 SKIP,输出见附件 B)。
2. doctor --require-wechat **双侧 PASS**(安装侧 + 仓库侧):`skills_locked_ok=true`、四锁 `hash_ok=true`、`FAIL_CLOSED=false`、`wechat_config_present=true`。
3. 正式安装器同步:
   - 构建 `F:\AIXM\wxgzh\bundle-staging-40\portable-bundle`(仓库 HEAD 镜像 564 文件 + 24S 基线四锁 + lock/config/source-proofs/MANIFEST 重建;密钥扫描 `secrets_detected=false`)。
   - dry-run `ok=true`;实装 `ok=true`:四锁 `commit_match/source_tree_match/repository_match/runtime_root_match/runtime_manifest_match/receipt_written/verify_all_ok` 全 true;receipts 仅 `installed_at` 更新(2026-08-01T21:23:06Z),其余字段与 lock 逐字一致。
   - **安装侧与 repo HEAD 逐字一致**:564 文件内容 diff=0、无缺失无多余;`wxgzh_pipeline/stages/gzh_design.py` 两侧 sha256 同为 `790d3bb0…`。
4. 两侧 `skills.lock.json` sha256 均为 `A9E07EF4…`(本档前后一致);证据目录(bundle-staging-37、24S 暂存、incident 副本)完好。

## 附件

### A:test_intro_guard.py 输出

```
tests\test_intro_guard.py .........                                      [100%]
============================== 9 passed in 0.16s ==============================
```

### B:upgrade_regression.py 输出(尾部)

```
pytest: PASS (1 explicit deselects)
relock dry-run x4: PASS
  super-writer: 无变化 OK
  zh-human-writing: 无变化 OK
  media-enrichment: 无变化 OK
  gzh-design: 无变化 OK
doctor --require-wechat: PASS
validate_gzh_html cross-side: SKIP — Pipeline 侧尚无 scripts/validate_gzh_html.py(P2 未落地;该步在 P2 落地后自动生效)
upgrade_regression: ALL PASS
```

### C:doctor 双侧摘要

- 安装侧 / 仓库侧均:`skills_locked_ok=true`;四锁 `current_root_sha256` = super-writer `46a00a1b…`、zh-human-writing `18491b36…`、media-enrichment `0d8aea21…`、gzh-design `9a8cd7f5…`,全部 `hash_ok=true`;`wechat_config_present=true`;`FAIL_CLOSED=false`;`doctor=PASS`。

## 风险点与后续

1. 守卫阈值 40 字镜像 oneliner 截断;若 gzh-design 升版后 oneliner 长度或 intro 保留规则变化,守卫必须同步复核(代码注释与本文档均标注)。
2. 该守卫只覆盖「首个 `## ` 之前」区域;章节正文的保真校验不在本档范围(OBS-73 其余部分待后续评估)。
3. `bundle-staging-40` 为新构建目录(未清理,TEMP_CLEANUP_ALLOWED=false)。
