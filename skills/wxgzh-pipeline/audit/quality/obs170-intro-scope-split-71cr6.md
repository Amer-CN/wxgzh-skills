# 档71C-R6 — 导语判据分离与陷阱结论焊死（OBS-170 主线）

## ① 本档修的是上一档的什么错

| 项 | 上一档(R5)的错误 | 本档修复 |
|---|---|---|
| OBS-170 主线 | `_body_plain_text` 同时喂两个判据;导语段(按 _intro_paras 定义永远非组件段落)却与组件文本比对 → 组件同名补位 → 完全假绿可构造(R5 已实测但未修) | 判据分离:新增 `_intro_body_text`(不含组件锚),`_intro_content_fidelity` 改用它;`_body_plain_text` 原样(anchor_ok 不受影响) |
| A(恒真断言) | test_obs170 两条恒真断言(`trap_in_missing or ...` / `"ok" in guard and ...`) | 删除;重写三条会翻转变红的测试 |
| B(结论无断言) | R5 报告「陷阱可构造」贴的是前置断言 | test_obs170_full_false_green_constructible / component_title_substitutes 承载结论;更正 R5 报告 ② 表 |
| C(RENDERER_NOT_FOUND 无测试) | refresh_anchor_status 六键只有五条测试 | 补 test_obs173_status_renderer_not_found(JSON 合法前提下) + test_obs173_all_keys_have_tests(全集相等) |
| E(阀二非同源) | `assert len(cfg_b) >= 6` 手写下限 | 改与 JSON 同源 N(distinct 非 URL style);probes 5→9 类 |
| F(LOOKUP_MISS 静默) | SLOT_LOOKUP_MISS 只记录不失败 | export 收尾 raise ValueError;main 捕获 return 1;反证测试 |

## ② 每条「已覆盖」声明 → 测试函数名 + 断言行原文（R36）

| 声明 | 测试函数 | 断言行(原文) |
|---|---|---|
| 假渲染器吞导语 | test_obs170_dropintro_drops_intro | `assert gd._normalize_text(FIRST_PARA) not in body` |
| 同名补位坐实(修复前)/修复后翻转 | test_obs170_component_title_substitutes | `assert TRAP_PARA in guard["missing_text"]` + `assert guard["ok"] is False` |
| 完全假绿可构造(修复后拆穿) | test_obs170_full_false_green_constructible | `assert guard["ok"] is False` |
| RENDERER_NOT_FOUND | test_obs173_status_renderer_not_found | `assert st["key"] == "ANCHORS_RENDERER_NOT_FOUND"` + `assert st["detail"]` |
| 键全集相等 | test_obs173_all_keys_have_tests | `assert impl_keys == test_keys` |
| 阀二同源 N | test_obs171_valve2_anchor_scope | `assert len(cfg_b) == n_json` |
| LOOKUP_MISS 真失败 | test_obs163_lookup_miss_raises | `assert "SLOT_LOOKUP_MISS" in str(ei.value)` |

## ③ 2c 四输入前后对照表（R34）

| 输入 | 修复前 | 修复后 | 判定 |
|---|---|---|---|
| ① 现 RUN fixture | ok=True | ok=True(不变) | ✓ S57 不触发 |
| ② nine_components(真渲染器) | ok=True | ok=True(不变) | ✓ |
| ③ nine_components(fake_dropintro) | ok=False(部分补位,风险提示 not in missing) | ok=False,missing 含「风险提示」+第一段 | ✓ 补位失效 |
| ④ single_intro_trap(fake_dropintro) | **ok=True(完全假绿)** | **ok=False**,missing='风险提示' | ✓ 假绿拆穿 |

## ④ 所有空集 / 归零结论 → 各自反证物（R32）

| 名单 | 实测值 | 反证物 |
|---|---|---|
| QUARANTINED | 空 | fake_empty.py / fake_partial.py |
| MULTILINE | 空 | fake_collapse.py |
| ANCHOR_GAP | 空 | fake_offanchor.py |
| APPROVED | 9 类 | fake_offanchor.py(降为 <9) |
| 导语假绿 | 已拆穿 | fake_dropintro.py + single_intro_trap.md(test_obs170_full_false_green) |

## 第 0 步 现场取证

- 0a: skip = `test_hotfix1.py::test_reinstall_from_pr_trees_doctor_pass`(WXGZH_SUBSKILL_CLONES not set);deselect = `test_portable_installer_preserves_pipeline_release_include`(显式传参)
- 0b: 依赖渲染器解析的测试 = 3 文件 12 处调用(test_obs119:9 / test_obs151:1 / test_obs171:2)
- 0c: single_intro_trap(单段导语=alert title 同名)+ fake_dropintro → **guard ok=True、missing_text="" 完全假绿**(完整 dict 已贴)

## 第 1 步

- 1a 删恒真断言;1b fixture 固化 tests/fixtures/single_intro_trap.md;1c 三条测试重写;1d tmp_path 化(git status 干净)

## 第 2 步 判据分离

- `_intro_body_text` = _PARA_RE + _CODE_ROW_RE + _PRE_RE(不含组件锚);docstring 写明裁决理由;`_intro_content_fidelity` 改用它;`_body_plain_text` 原样
- 四输入对照见 ③;①②不变(S57 不触发)、③④翻 False

## 第 3 步

- test_obs173_status_renderer_not_found(monkeypatch skills_home→tmp + 合法 JSON)→ RENDERER_NOT_FOUND
- test_obs173_all_keys_have_tests: 实现源码 key 常量集 == 测试断言字面量集(抓取结果: 6 键全等)

## 第 4 步

- 4a 阀二 N=17(JSON 同源);4b probes 9 类(code_compare_before/long_image_cap 在甲配置下无锚,如实分列断言+理由);4c LOOKUP_MISS raise + main return 1;4d 反证测试

## 第 5 步

- 5a 更正 R5 报告 ② 表(指向本档新测试 + 说明 R5 无断言支撑);5b docstring 补 mode;5c obs-ledger.md(119-174,169/172 空号标注)

## 第 6 步

- 6a pytest(junit): 装前/装后均 **407 collected / 405 passed / 0 failed / 0 error / 1 skipped / 1 deselected**
- 6b 安装侧已装;锁三处 diff 空
- 6c OBS_68 算式: 646 + 1(single_intro_trap.md)− 0 = **647**;口径: obs-ledger.md 在 audit/quality/ 下按 OBS-107 排除,不计入;实测 repo=647/installed=647/diff=0/missing=0/extra=0
- 6d OBS_69 MATCH;observability.py 无需改(锁未变+计数动态实算)
- 6e fixture 两份 sha 逐字节不变;6f upgrade_regression ALL PASS;6g git status 干净(仅本档改动)

## 没证明什么

- 微信端渲染未验证(需人工预览)
- B 组 10 类未接线;fake_live 仍不过语法门禁
- _intro_body_text 的取值(不含组件锚)在真渲染器下与 _body_plain_text 的差异仅组件区;导语区(首 ## 前)两者应一致(未单独断言)
- 收紧候选(位置特征/联合匹配/intro 区独立校验)未采纳,判据分离是唯一改动
- 未 relock;gzh-design 仓零改动;references 未动

## 新发现但没修

- fake_dropintro 只模拟「吞导语」;真实渲染器若未来引入导语丢失 bug,同型假绿依赖 _intro_body_text 独立于组件锚才不复发——已由本档判据分离结构性阻断
- relock 不自动同步 OBS-69 基线(R2 遗留,仍未修)
