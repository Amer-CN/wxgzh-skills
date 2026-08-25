# Release notes

## v0.1.8

77I(档77I):

- fidelity_guard 官方 JSON 模板补齐六个零值 gate 字段（OBS-319），NUMBER_CHANGES 可由 number 类 fail 计数。
- pipeline 读取侧缺省字段按 0 处理并留痕 `zero_gate_defaults`；显式违规仍 FAIL。

## v0.1.7

77A(档77A):

- 半角引号机械归一(OBS-309):新增 scripts/normalize_quotes.py——中文语境 ASCII 双引号
  成对转全角（全局配对、单边落单不猜仅留 WARNING），跳过 fenced code block 与行内代码；
  管线 zh 阶段链首强制前置执行。SHA256SUMS 重生成(61→62 条目)。

## v0.1.6

76Z(档76Z):

- 根目录开发期报告清理(体脂 A 刀):删除 8 个运行时无人读的报告文件
  (step-10 系列×4 + implementation-deviations/report + structural-validation + unit-test-report),
  git 历史即档案;HANDOFF.md 因 FREEZE.md 引用保留。SHA256SUMS 重生成(69→61 条目)。

76W(档76W):

- OBS-298 修复:pattern_audit SC-007a/SC-007b/SC-011 三处 first_span=None 解包崩溃
  (跨句正则段落命中、单句搜不到 span 时曾 TypeError);段落 span 兜底,永不许崩溃。
- run_tests.py:新增 FS-009(跨句零崩溃)/FS-010(SC-007a span 在册)。测试基数 85 → 87。

76Q(档76Q):

- OBS-286 修复:fidelity_guard 显式粗体豁免——extract_bold_spans 提取 `**text**` 加粗
  span,compare_code 将粗体正文排除在行内代码比较之外(防御:未来即使把配对语法扩到
  `**`,粗体也绝不误报为代码);extract_inline_code 契约文档化(仅反引号是行内代码
  标记)。根因实证:渲染器不支持 `**` 加粗,语法门 probe 如实报 unsupported(非误判),
  ADM/Harness 两轮「语法门拒加粗/去粗体根治」的行为层引导已写入 pipeline 指令。
- run_tests.py:新增 FS-006(含 `**加粗**` 正文零 fail)/FS-007(真行内代码改动仍 fail)/
  FS-008(粗体内行内代码改动仍 fail)。测试基数 82 → 85。

## v0.1.3

76D(档76D):

- OBS-253 修复:词表新增 forbidden_term 类目(FT-001,首批 Agent/智能体助手)——命中疑似
  专名(大写开头英文词、引号/「」内文本、产品名连写)时降级为 advisory(报告留痕、
  不强制改写、不判 fail);普通命中保持 strong(与 SC-009 同级,不进 pass_fail)。
  实证:Luma Agents 三轮连中 + 流水线 ×2 被强制改写为 Luma。
- pattern_audit.py:FORBIDDEN_TERM_PATTERNS 独立挂载 + _is_proper_noun_span 专名判定 +
  detect_forbidden_term;FT-001 普通命中归 strong 高置信桶(输出分组兼容)。
- run_tests.py:run_script 子进程统一 PYTHONUTF8=1 + UTF-8 解码(Windows 管道 GBK 互踩);
  新增 PB-048(产品名命中降级 advisory)/PB-049(普通命中保持 strong);PB-026 临时词表
  补 forbidden_term 键(R111:schema 类目集合固定,旧最小词表不再合法,属本档预期红态)。
- 测试基数 80 → 82。

## v0.1.2

Batch 3 (档72E-1):

- SC-005 语义重写(OBS-227):量对对象=句式同构(功能词/标点骨架,内容占位),非句长;分句不跨段落;取消只比紧邻前句;每句只归属一个同构簇消除双重计数
- OBS-232:profiles/*.md 三死文件删除(阈值真源在 config/default.yaml,相关文档同步)
- HR-001 补 <...> 变体;AO-006 补「不是吗？」独立变体;HR-006/AO-005/AO-012 作废登记


## v0.1.1

Batch 2 (档72D-1):
- core/routing.md 前置规则:handoff 携 prose_craft_applied=true 时 strategy 一律 preserve、检测照跑只报告不改写(audit 语义)
- 注释修正:pattern_audit.py 统计层接线注释与现状对齐(R56);run_tests.py 两处注释算术(PB-035 8.2‰、PB-043 5/610)

## v0.1.0-canonical

First canonical release of zh-human-writing.

Canonical baseline:
- Source commit before governance: a600f5945d45af67b04e715254545d2e07e2f490
- Pattern Audit: 8/8 audit samples passed
- Fidelity Guard: passed
- Full regression: 36/36 passed
- GitHub, development directory, and Runtime were identical before release
- No production behavior changes were introduced by this release

This release adds version and integrity governance only.
It does not change humanization behavior.
