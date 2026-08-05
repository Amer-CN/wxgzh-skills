# 档 69 OBS-98：校验器 strike 规格错位修复（形态语义断言）

- 日期：2026-08-05
- 范围：Pipeline 仓 validators/ + contracts/ + tests/ + fixtures/ + fake_live shim；零 relock；gzh-design 仓零改动
- 报告 blob sha：见文末

## OBS-98 登记（全文）

**OBS-98（高）：gzh-design 组件色值变更与 Pipeline 侧 validators/ 硬编码断言之间无任何联动校验——OBS-95「两套真理」的跨仓孪生。**

- 现象：67C 修复删除线对比度（`#737373` 文字 + 同色 1px 细线，白底 4.74:1）后，`validators/validate_theme_identity.py` L69-70 仍断言旧形态 `text-decoration-color:#B3593B` + `text-decoration-thickness:1.5px`；任何真实渲染必然 `strikethrough_props_ok=False` → `THEME_IDENTITY=FAIL`。档 69 续跑 gzh_design 首次暴露。
- 根因：被锁 gzh-design 的组件实现与 Pipeline 侧校验器各自维护一份「删除线规格」，无共享来源、无联动测试；67A/67C 改实现时校验器未同步（同 OBS-95 形状，跨仓版本）。
- 修复（本档）：校验器改为形态语义断言（逐元素校验，不硬编码色值）；contracts/05_gzh_design.yaml 规格同步；fixture 与 fake_live shim 两处旧形态产物同步；新增 obs98 回归测试（含旧形态反向验证 FAIL）。
- 防再发：形态语义断言 + 反向验证测试，任何「改回旧形态」都会被拦截。

## 第 1 步：strike 断言改写（形态语义）

### 1.1-1.3 修改后源码（validators/validate_theme_identity.py 关键段）

```python
# OBS-98:主题主色(hammer primary)——删除线不得使用主题主色作为 decoration 色。
_HAMMER_PRIMARY_HEX = "#B3593B"
# OBS-98:低对比度禁用文字色——line-through 元素使用该色一律判 bad,无豁免。
_FORBIDDEN_STRIKE_TEXT_RGBA = "rgba(202,202,199,0.35)"
# OBS-98:白底对比度下限(67C/67D 沿用,WCAG 普通文字阈值)。
_MIN_CONTRAST = 4.5
_WHITE = (255, 255, 255)

def _hex_to_rgb(value): ...      # #RRGGBB -> (r,g,b);其余形态返回 None
def _linearize(c): ...           # WCAG 线性化
def _relative_luminance(rgb): ...  # 0.2126R+0.7152G+0.0722B
def _contrast_ratio(fg, bg=_WHITE): ...  # 与 67D test_obs90 同一算法

def _parse_strike_elements(html): ...  # 逐 style 元素收集 line-through,解析 color/
                                       # text-decoration-color/thickness(归一化空白)

def _strike_element_ok(el) -> (bool, list[str]):
    # (a) 声明了 text-decoration-color;
    # (b) text-decoration-color 与自身 color 同一色值(同色系细线,67A 第 7 条);
    # (c) thickness 存在且 <= 1px;
    # (d) decoration-color 不为 #B3593B(主题主色不得用作删除线色);
    # (e) color 可解析为 hex 且白底对比度 >= 4.5。

def _strike_check(html) -> (props_ok, strike_bad, line_through):
    # line_through == 0 -> props ok(原语义);
    # 任一 line-through 元素 color 为 rgba(202,202,199,0.35) -> strike_bad=True,无豁免;
    # props ok 要求每个 line-through 元素全部通过形态语义断言。
```

完整源码见 `validators/validate_theme_identity.py`（本 commit）。

### 1.2 strike_bad 收紧

- 删除原「`text-decoration-color:#B3593B` 不在该元素内」豁免：只要 line-through 元素 `color` 为 `rgba(202,202,199,0.35)` 一律 bad（收紧，不是放宽）。

### 1.4 全仓扫描（#B3593B / 1.5px / text-decoration / rgba(202,202,199,0.35)）

| 文件:行 | 内容 | 判定 |
|---|---|---|
| `validators/validate_theme_identity.py` L66-70 | 旧 strike_bad 豁免 + 旧 props 断言 | **需改**（本档已改） |
| `contracts/05_gzh_design.yaml` L18-20 | strikethrough 规格 `#B3593B`/`1.5px` | **需改**（本档已改为形态语义描述） |
| `fixtures/offline_pipeline_fixture/gzh_design/outputs/final.html` L11 | 旧橙色粗线 strike 基线 | **需改**（本档已同步为 67D 形态） |
| `fixtures/offline_pipeline_fixture/gzh_design/outputs/final_runtime.html` L19 | 同上 | **需改**（本档已同步） |
| `fake_live/skills/gzh-design/render_article.py` L35-36 | shim 旧形态 strike | **需改**（本档已同步；shim 必须与真实实现同规格，否则 fake_live 全链路测试被新校验器拦截） |
| `tests/test_theme_infra.py` L130 | chapter-title 指纹含 `#B3593B`（replace 测试） | 不需改（主题主色在章节标题的正当用途） |
| `tests/test_theme_infra.py` L146 | `#B3593B → #059669` fallback 测试 | 不需改（主题主色正当用途，检测 fallback） |
| `tests/test_theme_infra.py` L153 | 低对比 rgba line-through 插入测试 | 不需改（断言 `strike_bad=True`，收紧后语义不变仍 True） |
| `wxgzh_pipeline/contracts.py` L244 | `no_theme_fallback` 检查 `#B3593B in html` | 不需改（主题主色正当用途） |
| `contracts/05_gzh_design.yaml` theme 块 | GZH_THEME/THEME_NAME 等 | 不需改（主题声明，非 strike 规格） |
| gzh-design 侧（被锁）palette/label_text | `#B3593B` 主色 / `#737373` 文字色定义 | 不需改（主题主色正当用途；被锁侧也不得改） |

结论：仅 5 处断言/规格/基线类硬编码需改，本档全部处理；主题主色正当用途 4 处不动。

## 第 2 步：回归测试（tests/test_obs98_strike_semantics.py，12 项）

| 用例 | 覆盖 | 结果 |
|---|---|---|
| test_obs98_current_67d_strike_passes | a. 67D 现行实现 PASS | PASS |
| test_obs98_old_orange_thick_strike_fails | b. ★旧橙色粗线反向验证 FAIL | PASS |
| test_obs98_low_contrast_rgba_with_primary_deco_fails | c. 低对比 + #B3593B 无豁免 FAIL | PASS |
| test_obs98_low_contrast_rgba_any_deco_fails | c. 低对比 + 任意 deco FAIL | PASS |
| test_obs98_thickness_1_5px_fails | d1. 1.5px FAIL | PASS |
| test_obs98_missing_decoration_color_fails | d2. 无 decoration-color FAIL | PASS |
| test_obs98_decoration_color_mismatch_fails | d3. 不同色 FAIL | PASS |
| test_obs98_primary_as_decoration_color_fails | d4. 主色作 decoration FAIL | PASS |
| test_obs98_low_contrast_hex_fails | d5. 对比度 < 4.5 FAIL | PASS |
| test_obs98_no_strike_passes | e. line_through==0 PASS | PASS |
| test_obs98_contrast_calibration_737373 | 对比度校准 #737373≈4.74 | PASS |
| test_obs98_contrast_white_text_on_white_is_low | 对比度白=1.0 | PASS |

★反向验证实测（旧形态必须 FAIL）：

```
def test_obs98_old_orange_thick_strike_fails(tmp_path):
    old = _strike_style_body("rgba(202,202,199,0.35)", "#B3593B", "1.5px")
    html = _replace_strike(_base_html(), old)
    ok, rep = _theme(html, tmp_path)
    assert rep["strikethrough_props_ok"] is False   # PASS(断言成立)
    assert rep["strikethrough_forbidden_rgba_present"] is True  # PASS
    assert rep["structure_ok"] is False             # PASS
```

## 第 3 步：全量测试与安装器

- Pipeline 全量 pytest：全部通过，1 项 deselect（`test_hotfix1.py::test_portable_installer_preserves_pipeline_release_include`，档 30/31 既有环境项，无新增）
- upgrade_regression：ALL PASS（relock dry-run x4 无变化；doctor --require-wechat PASS；validate_gzh_html cross-side SKIP 为既有 P2）
- 安装器同步：重建 bundle-staging-61（build 校验常量 `EXPECTED_PIPELINE_FILE_COUNT=130` 为档 30/31 既有已知过时项，staging 已写入新代码）+ install.py 实装成功
- doctor：PASS；OBS_68 MATCH（646/646）；OBS_69 MATCH
- skills.lock.json sha 双侧：`0CD0EBC35CF516BD0BD74DA515C74D50F929948F1D0E1FDD772D80D56C6B1CF9`（零 relock）
- gzh-design 仓：零改动，HEAD `af03b438a37233c111a20be77c4fd28898dc8f10`

## 第 4 步：续跑 gzh_design 验证（档 69 内完成）

- THEME_IDENTITY = **PASS**；strikethrough_props_ok = **True**；strikethrough_forbidden_rgba_present = **False**；LINE_THROUGH_COUNT = **1**
- RUN 内 final.html：U+3000 = 0、U+00A0 = 0（与取证 0/0 一致）；1a 闸门全过（#1E293B/#0F172A/三圆点/box-shadow 原文/18 行 code `<p>`/无 `<pre>`/无 white-space:pre）；INTRO_GUARD = PASS；validate 0 ERROR
- 后续 wechat_draft 被封面 FAIL_CLOSED 拦截（OBS-99，档 70 处理）

## 待裁决清单

- OBS-98 已修；封面定位缺口（OBS-99）转档 70 处理
- build_portable_bundle.py 的 EXPECTED_PIPELINE_FILE_COUNT=130 过时项仍为发布工程遗留（档 30/31 判定），未动

## 报告与 commit

- 本报告：`audit/quality/obs98-strike-validator-69.md`
- commit：见档 70 汇报（a 项）
