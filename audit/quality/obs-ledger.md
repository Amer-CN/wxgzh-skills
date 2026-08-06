# OBS 台账（119–174）

> 一次性重排,四列:OBS 号 / 一句话问题 / 状态 / 承载文件与测试函数名。
> 169 号空缺、172 号插队为审核方编号失误——保留空号,不复用。
> 既有测试文件名不改动(避免搅动 OBS_68 计数)。

| OBS | 问题 | 状态 | 承载 |
|---|---|---|---|
| 119 | 组件正文可见性只覆盖 2/9 | 已修 | validators/validate_component_visibility.py;test_obs119_visibility.py |
| 120 | 导语守卫与渲染器解析不同步 | 已修 | wxgzh_pipeline/stages/gzh_design.py;test_intro_guard.py |
| 121 | 图片白名单死分支与解析缺口 | 已修 | validators/validate_img_src_whitelist.py;test_obs121_img_src.py |
| 122 | (空号) | — | — |
| 123 | 图片指纹 400 魔数窗口 | 已修 | validators/validate_theme_identity.py;test_obs123_img_fingerprint.py |
| 124 | code-compare @before/@after 只取同一行 | 已修(渲染器 71C-R1) | gzh-design scripts/render_article.py;test_obs124(71C-R1 报告) |
| 125 | long-image image=/caption= 双不匹配 | 已修(71C-R1) | 同上 |
| 126 | media-text ![](url) 从不解析 | 已修(71C-R1) | 同上 |
| 127 | alert/quote type= 与 typ=/qt= 不匹配 | 已修(71C-R1) | 同上;validators/validate_syntax_gate.py |
| 128 | footnotes 文档语法与实现不兼容 | 已修(71C-R1) | render_article.py parse_article;test_obs119_visibility.py::test_obs136 |
| 129 | alert 多行块体塌成单 <p> | 已修(71C-R1) | generate_advanced_html.py alert();test_obs151_antifalse_green.py |
| 130 | 可见性判据只查文本不查结构(假绿闸门缺口) | 已修 | validate_component_visibility.py struct_ok |
| 131 | A 组无并列短句载体(71D 阻塞) | 已裁决(71C-2A′) | 报告 obs119-carrier-visibility-71c2.md |
| 132 | quote 同单槽多行塌陷 | 已修(71C-R1) | generate_advanced_html.py quote() |
| 133 | media-text 多行塌陷/名单手填 | 已修 | validate_component_visibility.py;test_obs151 |
| 134 | (空号) | — | — |
| 135 | 测试顺序依赖(赋值后自证) | 已修 | test_obs119_visibility.py |
| 136 | footnotes 样本语法错误 | 已修 | 同上::test_obs136_footnotes_doc_vs_impl_syntax |
| 137 | 渲染器路径硬编码 | 已修 | test_obs119_visibility.py::_resolved_renderer |
| 138 | footnotes 双语法测试翻转 | 已修 | test_obs119_visibility.py::test_obs136 |
| 139 | docstring 与实现不一致 | 已修 | validate_component_visibility.py |
| 140 | 位 3 判据魔数 3 | 已修 | 同上 per_item_ok v2 |
| 141 | (空号) | — | — |
| 142 | (空号) | — | — |
| 143 | code_compare after 色值误改 | 已修(71C-R1) | generate_advanced_html.py code_compare() |
| 144 | 文档槽欠测清单 | 已修(71C-R4) | component_slots.py;test_obs161_sample_coverage.py |
| 145 | 结构位落成探针/名单实测导出 | 已修(71C-2A′) | validate_component_visibility.py |
| 146 | quote source / dialogue name 未接线 | 已修(71C-R2) | render_article.py _render_component |
| 147 | 判据与导出不同源 | 已修(71C-R3) | sentinels_for() |
| 148 | (空号) | — | — |
| 149 | (空号) | — | — |
| 150 | (空号) | — | — |
| 151 | struct_ok 被删/and False 短路 | 已修(71C-R3) | validate_component_visibility.py;test_obs151 |
| 152 | multiline 导出常量短路 | 已修(71C-R3) | 同上 |
| 153 | anchor_ok 与锚导出集合不同源 | 已修(71C-R3) | sentinels_for() |
| 154 | _COMPONENT_PARA_RES 手抄锚 | 已修(71C-R3) | gzh_design.py 读 JSON;component_anchors.json |
| 155 | 哨兵表手写 | 已修(71C-R3) | _build_sentinel_tables() |
| 156 | 枚举两套手写 | 已修(71C-R3) | component_slots.py ALERT_TYPES/QUOTE_TYPES |
| 157 | 测试只跑一侧渲染器 | 已修(71C-R3) | test_obs151::test_obs157_dual_run |
| 158 | (空号) | — | — |
| 159 | (空号) | — | — |
| 160 | ANCHOR_GAP/APPROVED 无反证 | 已修(71C-R4) | fake_offanchor.py;test_obs151 |
| 161 | 样本未覆盖全部哨兵 | 已修(71C-R4) | test_obs161_sample_coverage.py;EXEMPT_SENTINELS |
| 162 | main 缺失明细无真过滤 | 已修(71C-R4/R5) | validate_component_visibility.py main();test_obs167 |
| 163 | anchors slot 列旧格式/源头未改 | 已修(71C-R5) | _lookup_slot();test_obs154 五列全比;test_obs163_lookup_miss |
| 164 | 锚 JSON 状态静默 | 已修(71C-R4) | gzh_design.refresh_anchor_status();test_obs171_anchor_status |
| 165 | 阀二未落成回归 | 已修(71C-R4/R5) | test_obs165_valve2_anchor_scope.py |
| 166 | matrix renderer_path 绝对路径 | 已修(71C-R4) | 矩阵 v4;test_obs119_visibility matrix 测试 |
| 167 | main out_dir NameError 崩溃 | 已修(71C-R5) | main() out 统一;test_obs167_cli_missing_detail |
| 168 | CLI 明细零测试 | 已修(71C-R5) | 同上 |
| 169 | (空号,审核方编号失误,保留不复用) | — | — |
| 170 | 导语假绿可构造(组件同名补位) | 已修(71C-R6) | _intro_body_text();test_obs170_intro_trap.py |
| 171 | 阀二锚范围回归测试 | 已修(71C-R5/R6) | test_obs165_valve2_anchor_scope.py;test_obs171_anchor_status |
| 172 | (插队号,审核方编号失误,保留不复用) | — | — |
| 173 | 锚状态键硬编码/惰性化 | 已修(71C-R5/R6) | refresh_anchor_status();test_obs171_anchor_status |
| 174 | 矩阵产物时间戳/版本 | 已修(71C-R5) | component_capability_matrix.json v4 |
