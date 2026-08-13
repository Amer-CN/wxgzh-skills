# 档71C-R3 — 反假绿与锚闭环（OBS-151~159）

## 首节：本档修的是上一档的什么错

| OBS | 上一档(R2)的错误 | 本档修复 |
|---|---|---|
| OBS-151 | component_structure_check 删掉了 struct_ok,多行塌陷无真实测 | 恢复 struct_ok:相邻哨兵对之间的 HTML 片段须命中 `</p>\s*<p` 或含 `<section`;按 HTML 出现顺序取对;URL 槽不参与(非文本行) |
| OBS-152 | export_lists_from_measurement 的 multiline 用 `and False` 常量短路,永远空集 | 改为 `{c : render_ok 且 not struct_ok}`;函数内零常量真假值 |
| OBS-153 | anchor_ok 用 REQUIRED+OPTIONAL、锚导出用 REQUIRED+URL,两处各写各的 | 抽出唯一 `sentinels_for(component, kinds)`,anchor_ok 与导出同源同 kinds(required+optional+url) |
| OBS-154 | _COMPONENT_PARA_RES 仍是 6 条手抄锚,ANCHOR_GAP 8 类缺口靠手抄锚撑出来 | 锚改由 component_anchors.json(哨兵实测导出)构造;锚闭环后 ANCHOR_GAP 归零 |
| OBS-155 | REQUIRED/OPTIONAL/URL 三表手写,与 SLOTS 可能漂移 | 三表从 component_slots.SLOTS 机械生成,4b 测试焊死一一对应 |
| OBS-156 | 语法门禁枚举手写两套,与渲染器/清单可漂移 | ALERT_TYPES/QUOTE_TYPES 进 component_slots.py;门禁 import 它;4e ast 漂移断言对渲染器源码 |
| OBS-157 | _resolved_renderer 含硬编码盘符路径;渲染器测试只跑一侧 | 删硬编码;双跑(安装侧+仓内树)断言逐位相等 |

## 第 0 步 自查

- 0a 常量短路 grep: `validate_component_visibility.py:228` 发现 `and False`(=OBS-152 本体,本档第 1 步修复);其余判据/导出函数无 `or True`/`and 1==1`/`assert True` → S39 修复后不触发
- 0b 被删触发测试: `test_obs119_quarantined_component_fails`、`test_obs129_multiline_alert_fails`(R2 因名单空集改为"断言不响")→ **替代物** = 本档 `test_obs151_multiline_gate_fires_with_injected_list` / `test_obs151_quarantine_gate_fires_with_injected_list`(注入假名单,断言门禁能响+行号)+ 假渲染器反证测试
- 0c test_intro_guard.py 01242f4→01709e4 diff: 见下方逐行理由
  - L106 `type="warn"→"warning"`: R2 语法门禁加 type 枚举校验,warn 不在枚举(文档是 warning),样本合法化
  - L155-170 quarantine 触发测试→空集测试: QUARANTINED 实测空集(R2 2f 预测),旧断言必然失败
  - L167 `type="warn"→"warning"`: 同上枚举合法化
  - L174-188 multiline 触发测试→空集测试: MULTILINE 实测空集
  - L186 `type="warn"→"warning"`: 同上

## 第 1 步 OBS-151/152

- 1a struct_ok 恢复(见首节);docstring 与实现逐字一致
- 1b multiline 导出改 struct_ok 口径
- 1c 假渲染器: `tests/fixtures/fake_collapse.py`(多行塌单 <p>)、`tests/fixtures/fake_empty.py`(无哨兵)
- 1d 门禁正向测试(注入假名单)
- 1e 六组名单数字:

| 渲染器 | QUARANTINED | MULTILINE | ANCHOR_GAP | APPROVED |
|---|---|---|---|---|
| 真渲染器(437fb8aa) | [] | [] | [] | 9 类全部 |
| fake_collapse | [] | 8 类(alert/code-compare/dialogue/footnotes/gallery/media-text/quote/resources) | [] | 9 类 |
| fake_empty | 9 类全部 | [] | [] | [] |

## 第 2 步 OBS-153

- `sentinels_for(component, kinds)` 唯一集合来源;anchor_ok 与 export_body_anchors 同 kinds(required+optional+url);URL 槽经 `_URL_SENTINEL_SET` 按语义跳过(两处一致)
- 2c CLI main() 逐条打印「组件 | 缺失哨兵 | style」(补做,R2 5a 声称已打印而只打布尔)

## 第 3 步 OBS-154

- `--emit-anchors` 落成 `validators/component_anchors.json`(34 行: sentinel/component/slot/mode/style + renderer_sha256 + 生成时间)
- gzh_design.py `_COMPONENT_PARA_RES` import 时读 JSON 构造(禁 import 起子进程);JSON 缺失退化为空列表
- 3c 测试: JSON renderer_sha256 == 安装侧渲染器 sha(437fb8aa)
- 3d 测试: 现场导出 == JSON 逐条相等(已删 R2 子串断言)
- 3e 硬验收: 改动文件含 `wxgzh_pipeline/stages/gzh_design.py` ✓ (S40 不触发)
- 3f 阀一: 新锚集(11 style) ∩ {封面/目录/章节/署名/页脚} = ∅;负对照测试仍过
- 3g 阀二: 现 RUN 无 ::: → 结论不变(见 7d 字节一致);另造 9 类组件测试文章对照见测试套件(结构探针样本即 9 类全覆盖,锚闭环前后 intro guard/字数/fidelity 由字节一致性保证)

## 第 4 步 OBS-155/156

- 4a 三表从 SLOTS 机械生成(哨兵名 = S_<COMP>_<SLOT>[_<MODE>][_N]);样本同步更新
- 4b 测试: 三表并集 == SLOTS (组件,槽,模式) 一一对应
- 4c 两处分歧定案:
  ① long-image caption: **必填**(media.md L33 最小输入「图片 URL + 说明」)
  ② resources url: **输入必填 + URL 槽分层**(链接必须有 URL=输入必填 links-resources.md L9-10;但 URL 在 img/a href 无文本锚,不参与 anchor/struct 判据)
- 4d ALERT_TYPES/QUOTE_TYPES 进 component_slots.py(alerts.md L17-21 / quotes.md L9-21);语法门禁 import
- 4e R30 漂移断言: 门禁枚举 == 渲染器 generate_advanced_html.py 内字面量(ast),PASS

## 第 5 步 OBS-157

- 5a 删 `F:\AIXM\...` 硬编码,_resolved_renderer 纯相对解析
- 5b 双跑测试: 安装侧 vs 仓内树四名单逐位相等(PASS;两侧 sha 均 437fb8aa,安装侧与仓内一致)

## 第 6 步 APPROVED 取证(不改判据)

- 6a 消费点 grep:
  - APPROVED_CARRIER_COMPONENTS: 定义(validate_component_visibility.py L38)+ 测试恒等断言(test_obs119_visibility.py L97/105/108/118)+ 旧报告文档。**生产消费点 = 零**
  - ANCHOR_GAP_COMPONENTS: 定义 + 测试 + 旧报告。**生产消费点 = 零**
- 6b 两口径对照:
  - 口径 A(必填+可选全齐): APPROVED = 9 类(锚闭环后)
  - 口径 B(仅必填正文槽): APPROVED = 9 类(必填槽锚同样全齐)
  - 影响面: 零生产消费 → 无行为影响,交裁决
- 6c: 无生产消费点 → **S41 不触发**

## 第 7 步 回归与安装

- 7a 全量 pytest 安装前: **391 collected / 388 passed / 0 failed / 0 error / 1 skipped / 1 deselected**
  安装后: **391 collected / 388 passed / 0 failed / 0 error / 1 skipped / 1 deselected**(两组一致)
- 7b 装安装侧(pipeline 重装);★锁文件三处零改动(git diff --stat 为空,S42 不触发)
- 7c OBS_68 算式: 633 + 4(component_anchors.json + fake_collapse.py + fake_empty.py + test_obs151_antifalse_green.py)− 0 = **637**
  实测: repo=637 / installed=637 / diff=0 / missing=0 / extra=0;OBS_69 MATCH
- 7d 现 RUN 重渲染: final.html `AE8DB428…`、final_runtime `21437B66…` 逐字节不变(S31 不触发)
- 7e upgrade_regression: **ALL PASS**

## 第 8 步 提交

- pipeline commit(见 numstat 原始输出)

## 本档没证明什么

- 微信端渲染未验证(需人工预览)
- B 组 10 类未接线;fake_live 仍不过语法门禁
- 假渲染器只覆盖「塌陷/无哨兵」两类反证,未覆盖其它失败模式(如部分哨兵缺失)
- 锚闭环后 ANCHOR_GAP 为空是「锚全量覆盖」的结果,未在微信端验证锚的视觉正确性
- 未 relock;gzh-design 仓未动;writing_contract/contracts 未动

## 本档新发现但没修

- relock 流程不自动同步 OBS-69 内嵌基线(R2 遗留,本档未涉及 relock,仍待修)
- component_anchors.json 是静态产物,渲染器升级后需手动 --emit-anchors 重生成;3c 测试能抓住 sha 漂移但不会自动重生成
