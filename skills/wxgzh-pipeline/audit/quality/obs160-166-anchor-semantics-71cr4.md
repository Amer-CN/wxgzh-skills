# 档71C-R4 — 锚语义反证与样本覆盖闭环（OBS-160~166）

## 首节：本档修的是上一档的什么错

| OBS | 上一档(R3)的错误 | 本档修复 |
|---|---|---|
| OBS-161 | 哨兵表机械生成后,样本未覆盖全部哨兵(差集 8 个),`if sent in block` 静默跳过 | 补样本使 8 个差集哨兵中 7 个被渲染;lang 槽进显式豁免表;新测试焊死「全集 == 样本集 \| EXEMPT」(R33/S44) |
| OBS-160 | ANCHOR_GAP/APPROVED 空集无反证物,口头称"已闭环" | fake_offanchor/fake_partial 反证测试(断言非空,非全 9);口径改写删「锚全量覆盖已证」措辞(R32) |
| OBS-165 | 阀二(R34)只做了"现 RUN 无 ::: 不算证明"的对照,没造含 9 类组件的对照文章 | nine_components.md 两配置(6 条手抄 vs JSON 锚)guard 逐项对照;陷阱构造判定 |
| OBS-162 | main()「缺失哨兵明细」无真 missing 过滤(零测试死代码) | 加 `sent not in body` 过滤 + fake_offanchor 覆盖测试 |
| OBS-163 | component_anchors.json slot 列是字符串拼的,非 SLOTS 真实槽名 | slot 列改用 component/slot/mode 三元组 + 断言 |
| OBS-164 | _load_component_para_res 对 JSON 缺失/损坏/sha 漂移静默 | 记录 ANCHORS_JSON_MISSING/CORRUPT/SHA_DRIFT 到 theme_identity_report(只可见不阻断) |
| OBS-166 | matrix renderer_path 是机器绝对路径(随 bundle 发布) | 改为相对占位 + 测试断言非绝对路径 |

## 第 0 步 自查

- 0a sentinels_for 全集 42、JSON 34、差集 8,与审核方预判**逐字一致**。逐个原因:
  - S_CODE_COMPARE_TITLE_YES: lang=有 样本 title 复用了 _NO
  - S_CODE_COMPARE_LANG_YES: lang 属性值不渲染进正文(R2 4a 删了 title lang 后缀),无文本锚
  - S_DIALOGUE_MSG_3 / NAME_2 / NAME_3: dialogue 样本只有 2 轮 + 1 个 name
  - S_FOOTNOTES_FN_TEXT_3: footnotes 样本只有 2 条
  - S_RESOURCES_LINK_TEXT_3 / URL_3: resources 样本只有 2 条链接
- 0b 独立复算: SLOTS multi=3 展开 = **42**;JSON 34;差 8(与审核方一致,非采信)
- 0c 绝对路径 grep: 生产代码(wxgzh_pipeline/validators)仅 orchestrator.py L441/443(机器路径扫描正则本身);scripts 2 处注释;tests 硬编码(test_intro_guard L146 / test_obs123 L16 / test_obs31 / test_obs55 / fixtures/obs87 manifest);audit 历史文档。**matrix renderer_path 已由 5b 相对化**

## 第 1 步 OBS-161 样本覆盖闭环

- 补样本: code-compare lang=有 title→TITLE_YES;dialogue 补第 3 轮 + NAME_2/3;footnotes 补 [^3];resources 补第 3 条链接
- 豁免表 EXEMPT_SENTINELS = {S_CODE_COMPARE_LANG_YES: ("lang 属性值不进正文,无文本锚", "OBS-161")}
- test_obs161_sample_coverage.py: 全集 == 样本集 | EXEMPT(差集非空未豁免 → FAIL/S44);豁免条目必须真实存在于生成全集
- --emit-anchors 重生成: **34 → 41 条**;新增 7 条含 S_DIALOGUE_NAME_2(assistant 侧 name style,无 text-align:right)
- 1d: 新样本暴露 dialogue NAME_2 锚缺口 → JSON 重生成后锚集覆盖(非改渲染器/删槽,合规);gzh-design 零改动

## 第 2 步 OBS-160 反证

- fake_offanchor.py: 哨兵放 margin:9px 的 style(不在锚集)→ ANCHOR_GAP 非空、APPROVED < 9
- fake_partial.py: 前 4 组件完整渲染、后 5 丢弃 → QUARANTINED 非空且非全 9(有区分度)
- 口径改写: 顶部注释与 docstring 删「锚全量覆盖已证」,改为「JSON 锚与当前渲染器同步 + 哨兵确在其最近 <p> 内」
- 反证测试断言全部「非空」(R45 无新增 `== frozenset()` 断言)

## 第 3 步 OBS-165 阀二

- nine_components.md: 1 H1 + 2 段导语(第二段"风险提示"与 alert title 同名陷阱)+ 2 章节 + 9 类组件
- 两配置对照(甲=6 条手抄锚 / 乙=JSON 锚):

| 项 | 甲 | 乙 | 一致 |
|---|---|---|---|
| guard ok | True | True | ✓ |
| intro_line_count | 2 | 2 | ✓ |
| missing_text | 空 | 空 | ✓ |
| body_len | 138 | 189 | 差异(锚覆盖范围,可解释) |
| 导语1/导语2/9 类组件文本 in body | 全 True | 全 True | ✓ |

- 3d 陷阱判定: **构造不出来** —— 导语段落经 _PARA_RE(正文段落锚)提取,与组件锚(_COMPONENT_PARA_RES)完全独立;真渲染器不丢导语(OBS-73)。原理风险(若未来渲染器丢导语且组件同名文本在正文区 → 假绿)登记交裁决
- S46 不触发(唯一差异 body_len 由锚覆盖范围解释)

## 第 4 步 OBS-162/163/164

- 4a main() 缺失明细加 `sent not in body` 真过滤;fake_offanchor 覆盖该分支(测试断言 CLI 输出含缺失哨兵行)
- 4b component_anchors.json slot 列用 SLOTS 真实槽名(component/slot/mode 三元组);emit 时从 SLOTS 反查
- 4c _load_component_para_res: JSON 缺失→ANCHORS_JSON_MISSING、损坏→CORRUPT、sha 漂移→SHA_DRIFT,注入 theme_identity_report(只可见不阻断)

## 第 5 步 OBS-166

- 5a 删恒真测试 test_obs145_quarantined_gate_empty_list_returns_empty / test_obs145_multiline_gate_empty_list_returns_empty;替代物 = test_obs151 注入版门禁测试(能响+行号)
- 5b matrix renderer_path → "gzh-design-skill/scripts/render_article.py"(相对);test_obs145_matrix_metadata_shape 改断言非绝对路径

## 第 6 步 回归与安装

- 6a pytest 装前: **393 / 390 / 0 / 0 / 1 / 1**;装后: **393 / 390 / 0 / 0 / 1 / 1**
- 6b 安装侧已装;三处锁文件 git diff --stat 为空(S42 不触发)
- 6c OBS_68 算式: 637 + 4(fake_offanchor + fake_partial + nine_components.md + test_obs161_sample_coverage.py)− 0 = **641**;实测 repo=641 / installed=641 / diff=0 / missing=0 / extra=0;OBS_69 MATCH。observability.py 本档无需改:锁未变 + 计数不写死(动态实算)
- 6d fixture: final.html AE8DB428… / final_runtime 21437B66… 逐字节不变(S31 不触发)
- 6e upgrade_regression: **ALL PASS**

## 第 7 步 提交

- pipeline commit(见 numstat 原始输出)

## 本档所有空集名单 + 各自反证物(R32)

| 名单 | 实测值 | 反证物 |
|---|---|---|
| QUARANTINED | 空 | fake_empty.py(全 9 类)/ fake_partial.py(后 5 类) |
| MULTILINE | 空 | fake_collapse.py(8 类) |
| ANCHOR_GAP | 空 | fake_offanchor.py(9 类 style 偏离锚) |
| APPROVED | 9 类 | fake_offanchor.py(降为 <9) |

## 没证明什么

- 微信端渲染未验证(需人工预览)
- B 组 10 类未接线;fake_live 仍不过语法门禁
- 锚集覆盖「当前渲染器」的证明仅限探针样本(41 哨兵),非全量文章形态
- nine_components.md 陷阱构造仅证明「当前渲染器不丢导语」下 guard 稳健;未来渲染器改动仍需重验
- 未 relock;gzh-design 仓零改动;references 未动

## 新发现但没修

- dialogue assistant 侧 name style(无 text-align:right)此前无锚——本档由样本补全+锚重生成覆盖,但该 style 与 user 侧不同的事实暴露「渲染器对同槽不同侧产生不同 style」,建议后续评估是否统一(不修)
- 导语与组件文本同名的假绿原理风险(3d)未修,交裁决
- relock 不自动同步 OBS-69 基线(R2 遗留,仍未修)
