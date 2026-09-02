# Release notes
# Release notes

## v0.1.13

77T(档77T):

- SKILL.md frontmatter 新增 `permissions:` 机器可读块；正文「权限与范围声明」节保留。
- 新增 tests/test_hf77t_run_script_safety.py：run_script 列表参数无 shell 防御钉子（OH1）。
- examples/03-technical/input.txt、examples/samples/C-technical/input.md 首行加夹具注（fidelity 保留样本，非部署指令）。
- VERSION 0.1.12 → 0.1.13；SHA256SUMS 重算；verify_release.py VERSION_EXPECTED 同步。

## v0.1.12

77S(档77S):

- SKILL.md 新增「权限与范围声明（最小权限）」节：文件读写/网络/凭据/子进程/明确不做。
- VERSION 0.1.11 → 0.1.12；SHA256SUMS 重算。

## v0.1.11

77R(档77R):

- pattern_audit 新增 ai_tone 只读层六族（OBS-342）：LT-001 段首零回指、LT-002 拟人化喻体、LT-003 起首语、LT-004 序数词编号小标题、LT-005 相邻同构/顿号过密、LT-006 译文句式；列表/代码/引用/对话豁免。
- 新增证伪护栏（OBS-343）：禁调节奏/CV 检查、禁删设问/比喻/句内排比、禁补单字虚词；翻案腔改动作级 balance；handoff.prose_craft 优先于通用去味规则。
- references/patterns/ai-tone.md 落上游 pin 27d29232f10124db904ca9c0536d0b67cb3b2833 与 MIT 出处。

## v0.1.10

77L(档77L):

- extract_commands(OBS-329)命令行判定严格化:行首锚定 + MULTILINE + 非贪婪,
  仅行首 $ 提示符且后接非空内容才算命令行;行中 $ 价格/数学用途($5/$9 无空白)
  一律不命中(修复 dfnsls 轮 run-killer 假阳);行首 > 引用块(含 CJK 散文)不误伤。
  回归测试 77L-01/02/03 三条。SHA256SUMS 重生成(62 条目,无增删文件)。


## v0.1.9

77K(档77K):

- normalize_quotes(OBS-326)跳过 ::: 指令头/收尾行与指令属性行，机器语法引号零触碰；正文成对归一与单边 WARNING 语义不变。

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
