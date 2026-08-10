# Release notes

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
