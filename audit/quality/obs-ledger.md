# OBS 台账（119–174，档71C-R7 重建版）

> 五列:OBS 号 / 一句话问题 / 状态 / 承载文件与测试函数名 / 首次认领档号。
> 状态取值:已修 | 未修 | 已裁决未实施 | 待查 | 空号(附证据)。
> 证据基:报告文件名区间法(0b/71C-R7)+ 全仓 grep(0c)+ 审核方给定(0d)。

## 全表

| OBS | 问题 | 状态 | 承载 | 认领档 |
|---|---|---|---|---|
| 119 | 组件正文可见性只覆盖 2/9 | 已修 | validate_component_visibility.py;test_obs119_visibility.py | 71C-2 |
| 120 | 导语守卫与渲染器解析不同步 | 已修 | gzh_design.py;test_intro_guard.py | 71C-2 |
| 121 | 图片白名单死分支与解析缺口 | 已修 | validate_img_src_whitelist.py;test_obs121_img_src.py | 71C-2 |
| 122 | B 组 10 类(facts/decision/steps/compare/annotated-image/faq/timeline/checklist/case/cta)未接线 | **未修** | gzh-design references/advanced/*.md(未接线) | 71C-R7(0d 给定) |
| 123 | 图片指纹 400 魔数窗口 | 已修 | validate_theme_identity.py;test_obs123_img_fingerprint.py | 71C-2 |
| 124 | code-compare @before/@after 只取同一行 | 已修 | gzh-design render_article.py | 71C-R1 |
| 125 | long-image image=/caption= 双不匹配 | 已修 | 同上 | 71C-R1 |
| 126 | media-text ![](url) 从不解析 | 已修 | 同上 | 71C-R1 |
| 127 | alert/quote type= 与 typ=/qt= 不匹配 | 已修 | 同上;validate_syntax_gate.py | 71C-R1 |
| 128 | footnotes 文档语法与实现不兼容 | 已修 | render_article.py parse_article;test_obs136 | 71C-R1 |
| 129 | alert 多行块体塌成单 <p> | 已修 | generate_advanced_html.py alert();test_obs151 | 71C-R1 |
| 130 | 可见性判据只查文本不查结构 | 已修 | validate_component_visibility.py struct_ok | 71C-2 |
| 131 | A 组无并列短句载体(71D 阻塞;alert 多行已由 OBS-129 修复) | 未修(已裁决未实施) | obs119-carrier-visibility-71c2.md;OBS-129 修复承载 | 71C-2A' |
| 132 | quote 同单槽多行塌陷 | 已修 | generate_advanced_html.py quote() | 71C-R1 |
| 133 | media-text 多行塌陷/名单手填 | 已修 | validate_component_visibility.py;test_obs151 | 71C-2A' |
| 134 | (grep 无着落) | 待查 | — | 71C-R7 |
| 135 | 测试顺序依赖(赋值后自证) | 已修 | test_obs119_visibility.py | 71C-2A' |
| 136 | footnotes 样本语法错误 | 已修 | test_obs136_footnotes_doc_vs_impl_syntax | 71C-2A' |
| 137 | 渲染器路径硬编码 | 已修 | test_obs119_visibility.py::_resolved_renderer | 71C-2A' |
| 138 | footnotes 双语法测试翻转 | 已修 | test_obs136 | 71C-R2 |
| 139 | docstring 与实现不一致 | 已修 | validate_component_visibility.py | 71C-2A' |
| 140 | 位 3 判据魔数 3 | 已修 | per_item_ok v2 | 71C-R2 |
| 141 | (文件名区间认领;正文无描述,grep 无着落) | 待查 | obs141-143-anchor-split-71cr1.md | 71C-R7 |
| 142 | (文件名区间认领;正文无描述,grep 无着落) | 待查 | 同上 | 71C-R7 |
| 143 | code_compare after 色值误改 | 已修 | generate_advanced_html.py code_compare() | 71C-R1 |
| 144 | 文档槽欠测清单 | 已修 | component_slots.py;test_obs161 | 71C-R4 |
| 145 | 结构位落成探针/名单实测导出 | 已修 | validate_component_visibility.py | 71C-2A' |
| 146 | quote source / dialogue name 未接线 | 已修 | render_article.py _render_component(lock history 证据) | 71C-R2 |
| 147 | 判据与导出不同源 | 已修 | sentinels_for() | 71C-R2 |
| 148 | 探针样本(SLOT_SAMPLES 等)住在随包发布的生产文件里 | **未修** | validators/validate_component_visibility.py(样本即生产文件) | 71C-R7(0d 给定) |
| 149 | (文件名区间认领;正文无描述,grep 无着落) | 待查 | obs145-150-anchor-split-relock-71cr2.md | 71C-R7 |
| 150 | (文件名区间认领;正文无描述,grep 无着落) | 待查 | 同上 | 71C-R7 |
| 151 | struct_ok 被删/and False 短路 | 已修 | validate_component_visibility.py;test_obs151 | 71C-R3 |
| 152 | multiline 导出常量短路 | 已修 | 同上 | 71C-R3 |
| 153 | anchor_ok 与锚导出集合不同源 | 已修 | sentinels_for() | 71C-R3 |
| 154 | _COMPONENT_PARA_RES 手抄锚 | 已修 | gzh_design.py 读 JSON | 71C-R3 |
| 155 | 哨兵表手写 | 已修 | _build_sentinel_tables() | 71C-R3 |
| 156 | 枚举两套手写 | 已修 | component_slots.py ALERT/QUOTE_TYPES | 71C-R3 |
| 157 | 测试只跑一侧渲染器 | 已修 | test_obs157_dual_run | 71C-R3 |
| 158 | _nearest_p_style 只取 ps[-1],不校验哨兵是否真在该 <p>…</p> 内 | **未修** | validate_component_visibility.py::_nearest_p_style | 71C-R7(0d 给定) |
| 159 | relock 不自动同步 OBS-69 内嵌基线 | **未修** | scripts/relock.py | 71C-R7(0d 给定) |
| 160 | ANCHOR_GAP/APPROVED 无反证 | 已修 | fake_offanchor.py;test_obs151 | 71C-R4 |
| 161 | 样本未覆盖全部哨兵 | 已修 | test_obs161_sample_coverage.py;EXEMPT_SENTINELS | 71C-R4 |
| 162 | main 缺失明细无真过滤 | 已修 | main();test_obs167 | 71C-R4/R5 |
| 163 | anchors slot 列旧格式/源头未改 | 已修 | _lookup_slot();test_obs154;test_obs163_lookup_miss | 71C-R5 |
| 164 | 锚 JSON 状态静默 | 已修 | refresh_anchor_status();test_obs171_anchor_status | 71C-R4 |
| 165 | 阀二未落成回归 | 已修 | test_obs165_valve2_anchor_scope | 71C-R4/R5 |
| 166 | matrix renderer_path 绝对路径 | 已修 | 矩阵 v4 | 71C-R4 |
| 167 | main out_dir NameError 崩溃 | 已修 | main() out 统一;test_obs167 | 71C-R5 |
| 168 | CLI 明细零测试 | 已修 | test_obs167_cli_missing_detail | 71C-R5 |
| 169 | (空号:obs167-174 区间内无 OBS-169 内容;R5/R6 报告标注空缺) | 空号(附证据) | obs167-174-generator-artifact-71cr5.md | 71C-R5 |
| 170 | 导语假绿可构造(组件同名补位) | 已修 | _intro_body_text();test_obs170_intro_trap | 71C-R6 |
| 171 | 阀二锚范围回归测试 | 已修 | test_obs165;test_obs171_anchor_status | 71C-R5/R6 |
| 172 | 生成器改了产物未重跑(源头 slot 旧格式) | 已修 | _lookup_slot();test_obs154 五列全比 | 71C-R5 |
| 173 | 锚状态键硬编码/惰性化 | 已修 | refresh_anchor_status();test_obs171_anchor_status | 71C-R5/R6 |
| 174 | 矩阵产物时间戳/版本 | 已修 | component_capability_matrix.json v4 | 71C-R5 |
| 175 | 配图位置无机器判据(bindings placement anchor 空/confidence=0,chart-003 跨章) | 已修(独立判据+CLI+测试落地;按 S65/3d 例外不挂主门禁,第 6 步仍实测) | validators/validate_image_section_affinity.py;test_obs175_image_affinity.py | 71E |
| 176 | validate_codeblock_fidelity 只认 fenced code block,16 行同一批文案出现两遍 | 已修(载体放宽 = fence ∪ 已批准组件块,R48 单一来源导入;MIN=10 未动) | wxgzh_pipeline/writing_contract.py;test_obs176_carrier_widen.py | 71E |
| 177 | 8 条 ⛔ 与 8 条 ⚠️ 压平进同一 alert type=warning | 已修(第 6 步拆两块:caution=⛔ / warning=⚠️,16 行全文出现次数=1) | producers.py 指令;本档第 6 步 | 71E |
| 178 | closeout 报告被就地改成跨档混合文档,三处过期陈述 | 已修(三处加「71E 更正」标注,本档新建独立报告文件) | obs-ledger-closeout-71cr7.md;obs175-179-carrier-widen-71e.md | 71E |
| 179 | OBS-131 行引用无出处直引「71D 不换载体…」 | 已修(删除无出处直引,改写为审核方 71E 判定口径) | obs-ledger.md;obs-ledger-closeout-71cr7.md | 71E |

## 未修清单（独立分区）

| OBS/项 | 问题 | 阻塞 71D |
|---|---|---|
| 122 | B 组 10 类未接线(71C-3 范围) | 不阻塞(71D 用 alert type=warning 承载 16 行,alert 属 A 组已接线;71D 不使用 B 组任何类) |
| 131 | A 组无并列短句载体(已裁决未实施;71D 承载见上) | 不阻塞(审核方 71E 判定:OBS-129 已修,alert 结构位成立且语义最近,故 71D/71E 用 alert 承载;71C-2 的『A 组无语义载体』结论系 alert 多行未修时点的结论;无出处直引已于 71E 删除) |
| 148 | 探针样本住在随包发布的生产文件 | 不阻塞(仅测试资产,随包发布是工程债) |
| 158 | _nearest_p_style 只取 ps[-1],不校验哨兵是否真在该 <p>…</p> 内 | 不阻塞(如实:该导出是生产侧 _COMPONENT_PARA_RES 的来源,缺陷偏「假绿」方向;71D 由 anchor_ok + 实测可见性门禁兜底,本档真实渲染已过 component_visibility,故维持不阻塞,但理由不再写「仅探针用」) |
| 159 | relock 不自动同步 OBS-69 基线 | 不阻塞(下一档 relock 前手动同步即可) |
| — | 微信端渲染 | **已关闭**(2026-08-07 02:18 用户人工预览三项全过:alert 16 行逐行显示 / /plugin 命令可复制 / 无异常删除线;用户原话「1 过 2 过 3 过」;R51 证据) |
| — | fake_live 仍不过语法门禁(R9 保留项) | 不阻塞(仅测试路径) |
| — | 键测试执行层覆盖(1a/71D):test_obs173 撤 rg 后执行层覆盖无断言 | 不阻塞(文本层 impl_keys==test_keys 断言仍在;执行层未验证已如实登记【未覆盖】,不再输出恒真警告) |

## 本台账口径

1. 报告名区间法:OBS 号的存在性以 audit/quality/ 报告文件名的编号区间为准;
   号的具体内容抄自报告正文(0b,71C-R7)。
2. 空号必须有证据:标「空号」需给出检索依据(此处:obs167-174 区间无 OBS-169 内容,
   且 R5/R6 报告明确标注空缺)。无证据一律标「待查」,不得默认空号。
3. 待查项:134/141/142/149/150——文件名区间认领但正文无描述、全仓 grep(非 audit)零命中;
   需由后续档回查指令原文或审核方补充。
4. 下次更新责任:任何新档新增/修复 OBS 号,须同步更新本台账并标注认领档号。
5. R45(71D):「已裁决未实施」= 未修的一种,必须进未修分区并给 71D 阻塞判定。
6. R51(71E):「已关闭」必须附闭环证据(时间 + 验收人 + 验收内容原文),无证据不得标已关闭。
