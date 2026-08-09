# Release notes

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
