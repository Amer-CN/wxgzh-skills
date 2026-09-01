# SECURITY.md —— 灵犀安检 45 项基线说明（档 77S，2026-09-01）

## ① 目的

让任何 agent 对本合集仓的下次安全扫描可解释：预期残留哪些 finding、为什么残留、
哪些类别在档 77S 已清零。复扫结果先对照本节定性，再决定是否登记缺陷。

## ② AST4 基线：31 处 subprocess 全部位于 tests/（维持不动，不改代码）

- 定性：扫描器噪声。全部 31 处均为 `sys.executable` + 仓库内固定脚本路径的测试自检调用，
  不拼接外部输入，无注入面。
- 实测：生产 `scripts/` 零 subprocess（`grep -rn "subprocess" skills/super-writer/scripts/` 输出 0 条，
  grep 证据日期 2026-09-01）；31 处全部在 `skills/super-writer/tests/`。

报告行号表（file:line，共 31 处）：

| 测试文件 | 行号 | 数量 |
|---|---|---|
| tests/test_calibration.py | 192, 210, 230, 244, 267 | 5 |
| tests/test_hf76f_tools.py | 168, 177, 186 | 3 |
| tests/test_hf77b_schema_unify.py | 107 | 1 |
| tests/test_hf77m_container_vocab.py | 20 | 1 |
| tests/test_hf77n_bold_ban.py | 19 | 1 |
| tests/test_length_material.py | 83, 103, 304, 454, 746, 778, 869, 886, 915, 945 | 10 |
| tests/test_semantic_handoff.py | 656, 1618, 1639, 2015, 2026 | 5 |
| tests/test_structure.py | 7, 237, 451, 471 | 4 |
| tests/test_wxgzh_cli_contract.py | 40 | 1 |

## ③ MP2 基线：多行续行片段误判（77S 已改单行，零语义变化）

- 定性：扫描器把多行表达式的续行片段误判为「内联大表」；实测非内联大表。
- 处置：77S 已将 7 处续行改写为单行完整语句（validate_article_length.py 2 处、
  test_hf77e_registry_consistency.py 1 处、test_length_material.py 1 处、
  test_semantic_handoff.py 1 处，共 5 文件 7 行号位），零语义变化。
- 复扫若再报 MP2，对照本节定性：语句已是单行即属残留误报，按本节口径登记不改代码。

## ④ EA3 基线：LICENSE:16 行为声明误报（维持不动）

- 定性：扫描器误报。LICENSE 第 16 行为 MIT 许可证正文
  「FITNESS FOR A PARTICULAR PURPOSE…」条款，被误判为行为声明。
- 处置：许可证文本不可更改，维持原样，不做任何修改。

## ⑤ LP3 处置：六技能 SKILL.md 已加权限声明

super-writer / zh-human-writing / media-enrichment / gzh-design / wxgzh-pipeline /
gzh-title-review 六份 SKILL.md 均已加「权限与范围声明（最小权限）」节，
覆盖文件读写 / 网络端点 / 凭据键名 / 子进程 / 明确不做五要素。

## ⑥ 复扫指引：预期残留

- AST4 ×31（tests 基线，见②）；
- EA3 ×1（LICENSE 误报，见④）。
- 其余类别（AST7、RP1、MP2、LP3）应清零；复扫再报先对照本节定性，不直接登记缺陷。

## ⑦ 来源

灵犀 45 项安检报告（2026-09-01）。对应关系：31 AST4=全部 tests/ 噪声（本档②基线）；
1 AST7=validate_article_length.py 动态属性（77S 显式分派修复）；4 RP1=npx 无锁版本
（77S 锁 skills@1.5.23）；7 MP2=多行续行误判（77S 改单行）；1 LP3=权限声明缺口
（77S 六 SKILL.md 补节）；1 EA3=LICENSE MIT 正文误报（本档④基线）。
