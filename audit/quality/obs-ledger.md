# OBS 台账（119 起持续追加，档71C-R7 重建版，71G 收口）

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
| 175 | 配图位置无机器判据(bindings placement anchor 空/confidence=0,chart-003 跨章) | 部分修(判据已落地但未挂主门禁(S65),根因 _distribute() round-robin 未动,71E 的同章结果系文章结构迎合所致) | validators/validate_image_section_affinity.py;test_obs175_image_affinity.py | 71E/71F |
| 176 | validate_codeblock_fidelity 只认 fenced code block,16 行同一批文案出现两遍 | 已修(载体放宽 = fence ∪ 已批准组件块,R48 单一来源导入;MIN=10 未动) | wxgzh_pipeline/writing_contract.py;test_obs176_carrier_widen.py | 71E |
| 177 | 8 条 ⛔ 与 8 条 ⚠️ 压平进同一 alert type=warning | 部分修(拆两块已生效,但实现方式为单篇硬编码指令,71F 已去硬编码,通用性待 4e 验证) | producers.py 指令;test_obs183_no_hardcoded_article.py | 71E/71F |
| 178 | closeout 报告被就地改成跨档混合文档,三处过期陈述 | 已修(三处加「71E 更正」标注,本档新建独立报告文件) | obs-ledger-closeout-71cr7.md;obs175-179-carrier-widen-71e.md | 71E |
| 179 | OBS-131 行引用无出处直引「71D 不换载体…」 | 已修(删除无出处直引,改写为审核方 71E 判定口径) | obs-ledger.md;obs-ledger-closeout-71cr7.md | 71E |
| 180 | 授权键零代码强制力(指令声明的 ALLOWED/禁止无代码层强制)。审核方 71G 更正:此前标注的『唯一不可逆风险』为误判。误群发已被三重结构性排除——orchestrator._scan_forbidden_endpoints扫描六个禁用端点且 release_audit 要求 no_formal_publish_capability;wechat_draft.post() 中state.formally_published=False 且无任何代码路径置真;cli.py 只有 发文/续发/进度/验收编排 四条命令、无发布入口。真实缺口仅为『WECHAT_API_ALLOWED 与 RELOCK_ALLOWED 无代码强制力』,后果可逆(删草稿 / lock-backups 回滚)。 | 已修(本档:WXGZH_WECHAT_API_ALLOWED 已代码化;其余九键判定为不在本包管辖范围,不写 gate) | wxgzh_pipeline/orchestrator.py;producers.py;test_obs180_wechat_api_gate.py | 71F/71G |
| 181 | placement_planner.find_anchors 的 claim_text[:30] 匹配对图表 claim 几乎必然落空(半角冒号 vs 全角逗号) | 未修(待 relock 档由媒体侧图表 spec 直出锚点) | media-enrichment placement_planner.py(锁内) | 71F |
| 182 | _APPROVED_CARRIER_COMPONENTS 模块导入时求值 | 未修,不阻塞(环境/路径变化会导致整模块 import 失败) | wxgzh_pipeline/writing_contract.py | 71F |
| 183 | 反例 F 恒真(改写在普通段落,未证明「载体内改写不计数」) | 已修(重写为与正例 A 唯一差异=文本被改写,covered 16→0 实测) | tests/test_obs176_carrier_widen.py::test_obs176_f_rewritten_prose_false | 71F |
| 184 | 测试名/docstring 与实测行为不符(unpaired_and_nested_ignored 实为「被 ::: 提前关闭的块仍计数」) | 已修(改名 test_obs176_carrier_blocks_state_machine_matches_parse_article + docstring 对齐) | tests/test_obs176_carrier_widen.py;writing_contract.py | 71F |
| 185 | 门禁阈值为单篇素材常量(MIN_DENY_ASK_COVERAGE=10 / MIN_NUMBER_PAIRS=3,经 stages/super_writer.py content_validate 对任何 --items-file RUN 无条件生效,失败即 StageError 中止 RUN,换话题必死) | 已修(本档 1a/1b 参数化:required=min(10,len(lines))、ok=not missing、素材 0 条显式 N/A) | wxgzh_pipeline/writing_contract.py;test_obs185_material_derived_thresholds.py | 71G |
| 186 | resume() 硬编码 create_wechat_draft=True,完整 RUN 必经 resume,故 create=False 不可达(审核方 71F 误设前提,已认领) | 未修(风险已由 180 的键覆盖:live+键未允许 → wechat_draft FAIL_CLOSED) | wxgzh_pipeline/orchestrator.py::resume | 71G |
| 187 | 反硬编码守卫只扫 AGENT_INSTRUCTIONS["super_writer"] 一个字符串,aihot 注入路径运行时指令串与 zh_human_writing 键未纳入 | 已修(本档 5b 扩范围:全部三个值 + AIHOT_INJECTION_INSTRUCTIONS 常量) | tests/test_obs183_no_hardcoded_article.py;producers.py | 71G |
| 188 | 台账全表与未修清单不对账、175 行四格塞三列、标题范围与列名过期 | 已修(本档 4:R59 对账 + 175 三格 + 标题/列名更新) | audit/quality/obs-ledger.md | 71G |
| 189 | test_obs176_carrier_widen.py 头部写「7 条」实为 9 个测试函数,「反例 F 改写/散文化」与改后行为不符 | 已修(本档 5a:头部改为实际函数数与 F 新口径) | tests/test_obs176_carrier_widen.py | 71G |
| 190 | 反硬编码测试实为 13 个禁用字面量,71F 汇报与 commit message 均写 12 | 已修(仅文档口径,代码本就正确;本档报告按 13 表述) | tests/test_obs183_no_hardcoded_article.py | 71G |
| 191 | 新增 gate 直接访问 ctx.env,无视仓内手写 fake ctx 约定,导致 16 个既有 live 测试 AttributeError / FAIL_CLOSED(S76) | 已修(本档 1a/2a-2e:统一 _wechat_api_env 防御式读法 + 16 个测试补前置授权 + 对照负例) | producers.py;orchestrator.py;test_obs72_cover_selection.py;test_obs99_cover_path.py;test_obs180_wechat_api_gate.py | 71G-F |
| 192 | _media_two_phase 落点测试覆盖情况 | 已覆盖(证据:test_obs180_media_continue_gate_live_unset 实测命中 gate 行并断言 media_request_failed 含键名;本档补 test_obs180_media_continue_gate_live_allowed_passes_gate 证明授权放行) | tests/test_obs180_wechat_api_gate.py | 71G-F |
| 193 | CI 全红定性(100 次运行零 success,长期红) | 未修(本档只查不修,R80;根因四类并存:未安装被锁子技能/bs4 缺失/陈旧 LOCKED_HEADS 与 OBS-69 基线/硬编码开发机路径) | .github/workflows/ci.yml(本档未改) | 71H |
| 194 | 惰性守卫测试(假绿第 27 例):test_obs180_wechat_stage_gate_zero_overrides_dotenv 的 run_dir parents[2] 读不到 .env,断言 exit 2 由 ctx.env 的 0 单方满足 | 已修(4a run_dir→a/b/c 使 .env 真被读;R84 例外加严 stderr 断言;4b 反转优先级即红实测) | tests/test_obs180_wechat_api_gate.py | 71H |
| 195 | deny/ask 前缀条件式残留 R57:正则非捕获组判不出 kind,退回整个文件 emoji 判断,无关位置的 ⚠️ 会误要求 ask 前缀致 RUN 中止 | 已修(3a 捕获组 + extract_deny_ask_entries + 删除 items_raw 死代码 + 3e 无漂移 + 3f 单变量反例) | wxgzh_pipeline/writing_contract.py;tests/fixtures/obs88/items.deny_only_stray_warn.json;test_obs185 | 71H |
| 196 | .env 解析两份独立实现(_wechat_api_env / _media_subprocess_env)同语义 | 已修(2a _media_subprocess_env 一行委派 _wechat_api_env;2b 调用点 2 生产+1 测试,行为逐字不变) | wxgzh_pipeline/producers.py | 71H |
| 197 | WXGZH_ALLOW_WARNINGS 解析范围未声明(只读 ctx.env 是巧合,docstring 自称照抄但没照抄范围) | 已修(5a docstring 精确化;5b 注释钉死窄口径;5c 钉死测试:.env 写 1 也不传 --allow-warnings;R82 未放宽) | wxgzh_pipeline/producers.py;test_obs180_wechat_api_gate.py | 71H |
| 198 | 微信 API 未授权错误文案双重 FAIL_CLOSED 前缀(机制:_media_two_phase 的 raise 自带前缀 + 外层 except 再拼一次;_wechat_api_blocked_meta 一直只有一层,71H 描述误指) | 已修(两条实例均已闭合:_media_two_phase 71H 2c / _wechat cover 路径 71I 4b;72A 3b 回升) | wxgzh_pipeline/producers.py;test_obs180_wechat_api_gate.py | 71H/71I/72A |
| 199 | OBS-198 修复不完全:_wechat 的 cover 失败路径仍是双 FAIL_CLOSED: 前缀(_select_live_cover 抛 "cover FAIL_CLOSED: …" + 外层 except 再拼一层) | 已修(71I 4b:15 处前缀改 "cover: ";改后实测 stderr="FAIL_CLOSED: cover: …" 单前缀;tests/ 无完整串断言) | wxgzh_pipeline/producers.py::_select_live_cover | 71I |
| 200 | 71H 的 5c 新测试硬编码 REAL_SKILLS,CI 上必红,类 A 由 11 项增至 12 项;71H 的 i 段未自报 | 未修(R90:本档只登记不修,类 A 12 项待 CI 环境档统一处理;禁 skip/xfail/importorskip) | tests/test_obs180_wechat_api_gate.py::test_obs180_allow_warnings_ignores_dotenv | 71I |
| 201 | 台账「总数」名实不符(R56):同时计入主表行、未修清单分区重复行、口径说明行;193 被计两次;既非条目数也非唯一编号数 | 已修(71I 1c:拆分为「唯一 OBS 编号数」与「台账文件行数」两指标) | audit/quality/obs-ledger.md 口径 | 71I |
| 202 | 台账 198 行机制描述错误:双前缀来自 _media_two_phase 的 raise + 外层 except,_wechat_api_blocked_meta 一直只有一层 | 已修(71I 1b:198 行描述改为正确机制,状态降级部分修) | audit/quality/obs-ledger.md | 71I |
| 203 | 余下 7 处 run_dir = tmp_path/"r"/"d" 的 parents[2] 逃逸到 pytest 会话共享目录;今天无害,但任何人给其中一条加 .env 即复发 OBS-194 | 已修(71I 3b:7 处统一改 tmp_path/"a"/"b"/"c",parents[2]==tmp_path;断言零改动,7 条原样绿) | tests/test_obs180_wechat_api_gate.py | 71I |
| 204 | 71I 首次汇报的 numstat 与提交实际不符(同一 sha 两组数字:汇报 124/25,实际 86/23;test_obs180 7/0 对 7 处原地替换在算术上不可能);数字未取自 git diff --numstat 回显 | 已处理(72A 起 R92:sha/numstat/计数一律贴回显原文) | 档 71I 汇报;R92 红线 | 72A |
| 205 | 71I 后 198 状态陈旧:两条实例均已修,仍标部分修并占未修清单,R59 集合虚高 1(13 应为 12)。成因为审核方指令缺陷第 74 处(1b 未写"若第 4 段执行则 198 回升已修"的条件分支) | 已修(72A 3b:198 回升已修并退出分区) | audit/quality/obs-ledger.md | 72A |
| 206 | 72A 语义中性改动落在 SKILL.md(front-matter 前)且非 required_files,无法验证进入运行时 | 已修(72A-F 回滚精确 S98 + 补测落 required_files R96 + 1b 证实安装链生效;runtime_manifest 语义澄清移入 211) | super-writer SKILL.md/scripts/validate_semantic_map.py | 72A-F/72B-0 |
| 207 | SKILL.md 首行注释破坏 front-matter 解析(1c 三态实测:当前版 name=None,删行后/1e58d01 原版均 OK) | 已修(72A-F 回滚,installed 第 1 行恢复 ---,S99 验证) | super-writer SKILL.md | 72A-F |
| 208 | fake_live 端到端产物不变不得作为提示词升级/机制成立的证据(fixture 驱动,技能内容与产物无关;72A 曾以此举证) | 已裁决(判据作废:72A-F 起 RUN 只照记 sha 不举证;真实提示词升级须用真实 RUN 验证) | 档 72A/72A-F 报告 | 72A-F |
| 209 | observability.py 基线上方两行陈旧注释(a9e07ef4…/档57 relock,与当前基线不符) | 已修(72A-F 3c 改为 72A-F relock 口径,与基线同步同次完成) | wxgzh_pipeline/observability.py | 72A-F |
| 210 | OBS_68 计数范围未明确:relock 生成的 audit/upgrade-capability/lock-backups/*.json 计入 repo 计数(655→656),audit/quality/*.md 不计(OBS-107 口径) | 已修(口径明确:lock-backup json 计入,报告 md 不计;本档实测 656) | OBS_68 计数口径 | 72A-F |
| 211 | runtime_manifest_sha256 不提供 required_files 内容哈希 | 已修(72C-4 坐实:该值=运行时文件【路径清单】哈希。实证链:五次内容改动(72B-2R/2F/72C-2/72C-3/72C-4)manifest 均不动;72C-4 新增 lexicon-deai.yaml 使清单 53→54,manifest 立即变(022e62c5→53fdd26b)。已排除 size/mtime 假说:pattern_audit.py 改动 154/6 行,大小与 mtime 必变而 sha 不动。Batch 3 的 grep 降级为补书面证据) | wxgzh_pipeline/skill_discovery.py:67;scripts/relock.py | 72B-0/72C-4 |
| 212 | 写作阶段 fake/real 无独立开关(0B-1 实证:由 network_mode 单一决定,producers.py:277 fake_live/integration=FakeAgent fixture 重放,live=人工交接);真跑需 live 模式+人工交接,无自动化真写开关;0C 实测还受 TUN DNS 影响媒体发现(github.com→198.18.0.9 被 URL 安全检查拦截) | 未修(登记:72B 采用 live+停媒体批准点的真跑法;DNS 拦截为环境问题,非代码) | wxgzh_pipeline/producers.py:277;orchestrator.py network_mode | 72B-0 |
| 213 | 六闸门自评:NEW_UNREGISTERED_FACTS/NUMBER_CHANGES/ATTRIBUTION_LOSS/QUALIFIER_LOSS/CLAIM_SEMANTIC_CHANGE/HARD_RESIDUE 六键在 zh-human-writing 仓零命中,由被检查方自写 fidelity_report.json 提供,Stage 3 门禁=自评;唯一真闸是 _FORBIDDEN_TERMS(假绿#29) | 未修(本档不修) | zh-human-writing scripts/fidelity_guard.py;wxgzh_pipeline/stages 3c | 72B-2 |
| 214 | fidelity_guard exit 1(warning)与 3c「非 0 即失败」语义错配:真实 de-AI 改写只要动一个「所以/不/如果」Stage 3 必然失败 | 已修(72B-1R §0-4:exit 1 进 official_validator_warnings 不抬升 exit_code;判据=FS-003/FS-004 四组约 40 词出现次数完全相等的 warning 契约) | wxgzh_pipeline/stages/__init__.py 3c;tests/test_obs214_validator_exit1_is_warning.py | 72B-2 |
| 215 | pattern_audit stdout 无消费者(死线),hard_residue 经 sys.exit(2) 为活线;sc/ao 因 --check-level 默认 hard_residue_only 根本不执行 | 已修(72B-1R §0-1:--check-level full --profile essay;stdout 落盘 <脚本名>.stdout.json 并入 receipt output_files) | wxgzh_pipeline/producers.py::_agent_validator_args | 72B-2 |
| 216 | advisory_only/strong_contextual 恒 0 系代码未执行所致,非文本干净(假绿#30) | 已修(72B-1R §0-1 接线;72B-2/72B-2R 0C 重跑实测 advisory_only=34 为证) | wxgzh_pipeline/producers.py;0C RUN 629w48 | 72B-2 |
| 217 | de-AI 阶段无活性断言:change_report change_ratio=0.0 仍 meets_threshold=true 且 exit 0,零改写照样 PASS 并冻结产物 | 未修(本档不修) | zh-human-writing scripts/change_report.py | 72B-2 |
| 218 | PROFILE_MULTIPLIERS 统一乘数已存在于代码,设计稿「禁用」实为删除任务 | 已修(72B-2 §4 删除乘数,改每条规则自带 thresholds 字典;72B-2R §1 修正 SC-005 technical=int(3*1.5)=4,int 截断非 ceil) | zh-human-writing scripts/pattern_audit.py | 72B-2/72B-2R |
| 219 | pattern_audit 无任何读配置代码,config/default.yaml:68 的 check_level 是纯文档(死文件) | 已修(72C-2 §7:config 真源化——删死乘数,新增 pattern_thresholds 段;load_config() + --config 注入,缺失/错/缺键一律 exit 3 无兜底 R111;config/default.yaml 加入锁 required_files R96;PB-013~015 覆盖) | zh-human-writing scripts/pattern_audit.py;config/default.yaml | 72B-2/72C-2 |
| 220 | change_report --length-retention:agent 自报 strict,管线未传参实跑 balanced,声明与实跑不符 | 已修(72B-1R §0-2:管线写死 balanced + 握手模板自报 balanced 对齐) | wxgzh_pipeline/producers.py | 72B-2 |
| 221 | PB-001~006 六项 profile 测试全部无法因 profile 逻辑失败(PB-004 硬编码 passed=True,其余只受 hard_residue 控制;PB-001/002 同文本同断言仅 profile 不同;假绿#31) | 部分修(72B-2 §5 新增 PB-007~009 正反例,72B-2R §3 新增 PB-010 18 格恒等回归;原六条仍假绿) | zh-human-writing tests/run_tests.py | 72B-2/72B-2R |
| 222 | UF-001 断言 rc in [0,2] 覆盖 pattern_audit 全部正常退出码,恒真;注释自承「pattern_audit 不直接处理 fiction」 | 未修(本档不修) | zh-human-writing tests/run_tests.py::UF-001 | 72B-2 |
| 223 | fake_live shim 与真脚本 CLI 一致性仅由 docstring 声明,change_report 缺 --length-retention 长期未发现,直到传参以 17 项无关测试集体变红暴露 | 已修(72B-1R §0-5:test_obs223 直接消费 _agent_validator_args 生成 argv,逐条 sys.executable 真跑 shim,returncode!=2) | tests/test_obs223_shim_cli_contract.py;fake_live/skills/zh-human-writing/change_report.py | 72B-2 |
| 224 | fake_live 三个 validator shim 均为无条件通过桩(fidelity 永不产生 exit 1,pattern_audit 硬编码 hard_residue:0 永不 exit 2,三者 stdout schema 与真脚本完全不同),validator 语义在 pipeline 测试套件零覆盖 | 部分修(72B-1R §0-4R:WXGZH_FAKE_FIDELITY_EXIT 注入口 + exit-1/exit-2 两条用例;pattern_audit exit-2 路径与真 schema 仍零覆盖) | fake_live/skills/zh-human-writing/fidelity_guard.py;tests/test_obs214_validator_exit1_is_warning.py | 72B-2 |
| 225 | validate_receipt 把任一 official validator exit!=0 判为 receipt 无效,verify_receipt 以其为第一步 → exit-1 警告 receipt 写下即无效 → resume 视该阶段未执行并重跑(与 OBS-217 叠加成死循环) | 已修(72B-2 §0-6:execmodel.validator_exit_acceptable/WARNING_EXIT_ALLOWED 单一真源 R106,receipts.validate_receipt 与 stages 3c 共消费;test_obs225 四条含「全跑不重跑」) | wxgzh_pipeline/execmodel.py;receipts.py;stages/__init__.py;tests/test_obs225_warning_receipt_is_valid.py | 72B-2 |
| 226 | 同步树是 08-03 从本地路径克隆的快照:media-enrichment 同步树连锁 pin 18414cc9 都无法解析(cat-file 报 Not a valid object name);relock 若以同步树为源会静默 pin 到更旧祖先 commit;当前配方只打单目标故未触发,属潜伏陷阱 | 未修(审核方裁决:不推进 media-enrichment/gzh-design 同步树,保持 08-03 快照原样;S106 作废改 S106-R) | .temp/obs72-sync-src/* | 72B-2R |
| 227 | SC-005 特殊逻辑量错了对象:不只是双重计数(consecutive_count>=3 逐句 append,5 句产出 3 条)与缓慢漂移误判(20→25→30→35 判同构),而是**实测的是句长差(<=5),不是文档声明的「相同句式」**;规则名已由 72C-2 改为「连续等长句」以名实对齐 | 已修(72E-1:语义重写为句式同构——功能词/标点骨架保留、内容占位 X、数字占位 N,同骨架句=同构;分句不跨段落;取消只比紧邻前句;每句只归属一个同构簇消除双重计数;活性实测:同段 3 句同构命中/跨段同构簇 2<3 不命中/句长相近句式不同不命中;0C 锦标本体不动,历史数值保持历史记录) | zh-human-writing scripts/pattern_audit.py::detect_strong_contextual(SC-005) | 72B-2R/72C-2/72E-1 |
| 228 | §4 首版 thresholds 查表用 `or` 链兜底:对 0 短路且缺键静默回退 essay/1,fail-open(R111) | 已修(72B-2R §2:模块加载期结构断言三 profile 齐备且 >=1 整数;取值直接下标 pattern_def['thresholds'][profile],缺键 KeyError) | zh-human-writing scripts/pattern_audit.py | 72B-2R |
| 229 | SC-005 的 thresholds 字典为死配置:其 patterns 为空数组,被 detect_strong_contextual 主循环的 continue 跳过,专用检测块将阈值与输出的 cluster_threshold 双双硬编码为 3。profile 分档对 SC-005 从未生效(新旧代码皆然),输出字段与配置值名实不符;PB-010 的 SC-005 三格因此为假绿(#33) | 已修(72B-2F §3:接入 _SC_BY_ID['SC-005']['thresholds'][profile] 真源;essay 档配置值同为 3,0C 重跑八项数字逐字不变(S110);PB-011 活性断言 R112:红态 2/2/2 恒 3 → 绿态 2/1/0 thr 3/4/-。OBS-227 双重计数+跨段分句仍未修,留 Batch 3) | zh-human-writing scripts/pattern_audit.py::detect_strong_contextual(SC-005);tests/run_tests.py::PB-011 | 72B-2F |
| 230 | 过期注释「缺省回落到 essay」与 R111 代码名实不符(R56):72C-2 §7 已改直接下标+模块断言,注释未删 | 已修(72C-3 §0-1:grep 实证注释仍在 pattern_audit.py:289,本档删除;发现方式=grep '缺省回落到 essay\|PROFILE_MULTIPLIERS 已删除' 命中一行) | zh-human-writing scripts/pattern_audit.py | 72C-3 |
| 231 | 文档-代码 18 项名实不符((a)8 项文档有代码没有:HR-006/AO-005/AO-008/AO-009/AO-010/AO-012/HR-001 的 <...>/AO-006 的「不是吗？」;(c)10 项内容不一致:SC-005 语义句长≠句式、SC-001~006 profile 档位与文档逐条声明不符(统一乘数遗毒)、SC-002/HR-003/HR-005 字面量前缀差异、HR-002/HR-004 变体集合、AO-011 粒度) | 已修(72C-2 §1~§6:阈值改文档逐条声明值;SC-005 改名「连续等长句」并标注实测语义;SC-007a 阈值 1+第 5 条正则;SC-008 移入 HR-007;SC-007b 升级机制;文档回写补齐 HR-007/SC-007a/SC-007b 并标注未实现项。SC-005 语义重写留 Batch 3(见 227)) | zh-human-writing scripts/pattern_audit.py;config/default.yaml;references/patterns/*.md | 72C-2 |
| 232 | profiles/essay.md、technical.md、social.md 三个文件无人读取,是死文件;其声明的「×1.5/×2.0 放宽」「短句不检测」「第二人称不判假互动」等无代码落点;fidelity_guard.py 接受 --profile 但从未使用 | 已修(72E-1:三个死文件删除;execution-flow.md 指向 config/default.yaml pattern_thresholds 真源;README 目录树与文体 Profile 节同步;SHA256SUMS 重生成 72→69) | zh-human-writing profiles/*.md(已删);core/execution-flow.md;README.md | 72C-2/72E-1 |
| 233 | 任务书 §3 指定的 references/domain-lexicon.yaml 实为误杀防护词表(术语/命令逐字保护),不是检测词表,任务书目标文件错配 | 已修(72C-4 另建 references/lexicon-deai.yaml 承载 59 词检测词表;与 domain-lexicon 零重合,两类词表不再互相污染) | 任务书 §3;references/lexicon-deai.yaml | 72C-2/72C-4 |
| 234 | argparse 错误退出码与 hard-residue 撞车:argparse 默认 exit 2,而 exit 2 在本项目已占用为 hard-residue/fail,参数错误与内容失败无法区分 | 已修(72C-3 §0-2:pattern_audit/fidelity_guard/change_report 三脚本覆写 argparse error() → 统一 exit 3(文件/配置错误语义);UF-002 断言收紧为 rc==3,消除恒真写法) | zh-human-writing scripts/pattern_audit.py;scripts/fidelity_guard.py;scripts/change_report.py;tests/run_tests.py::UF-002 | 72C-3 |
| 235 | examples/*/audit-output.json 旧版为 UTF-16LE+BOM(含 1049 个 NUL 字节),git 按二进制处理,导致 R92 的 numstat 证据链对这三个文件失效一档(git show --numstat 恒显示 `- -`) | 已修(72C-3 重生成 UTF-8 无 BOM;72C-4 生成代码显式 encoding='utf-8' + newline='\n'(工作区 crlf=0);git show c9c1ef3 --numstat 已实证 `2 1` 真实行数;历史侧 UTF-16 不回溯、不 amend) | examples/*/audit-output.json | 72C-3/72C-4 |
| 236 | relock 与 required_files 顺序耦合:先给锁加 required_files 行再 relock,预写 doctor 会以 installed 树缺该文件为由拒绝(entrypoints_ok=false);须先 relock(installer 把文件带入 installed 树)再补 required_files 行 | 已修(72C-4 记录规避步骤:先 relock 后补行;终态锁/installed 一致,upgrade_regression doctor PASS 验证) | scripts/relock.py 预写 doctor;skills.lock.json required_files | 72C-4 |
| 237 | AO-007/AO-011 计数口径变更:逐次命中各产出一条 finding 改为每段一条(occurrence_count=段内命中次数,span_text=段内首命中处,其余 AO 规则不动);0C advisory 35→20(AO-007 22→7 条,其余 13 条不变,降幅 15;occurrence 和守恒 22) | 已修(72C-6 任务 3;PB-031~033,检测逻辑/severity/退出码零改动) | zh-human-writing scripts/pattern_audit.py;tests/run_tests.py | 72C-6 |
| 238 | OBS-227 段落边界实证(72C-6 任务 2):样本 A 恢复《背影》原文 3 段后 SC-005 条数不变(4→4)且命中文本逐字相同,location 由「第1段第30句」如实化为「第2段第4句」——实证 split_sentences 完全不读段落边界(空结果=阳性证据),旧「跨段误连」推断不成立;OBS-227 本体保持未修(语义重写留 Batch 3) | 已实证(72C-6R 决定日志;不改代码) | zh-human-writing examples/samples/A-human | 72C-6R |
| 239 | 词表定性为低产率保险:59 词四篇(A/B/C/0C)实测 56 词零命中,仅「还有一层」真阳 1、「链路」「闭环」存疑各 1;A(真人散文)特异性 100%(SC-009+SC-010 零命中);B(AI 稿)敏感性达标(SC-009+SC-010=1>0)但总体低产率;统计层新增 ST-003/ST-005 为 0C 首批统计命中 | 已登记(72C-5 词频表 + 72C-6R 四篇总表实证;校准决策归 Batch 1 之后) | audit/quality/obs-samples-frequency-72c5.md | 72C-6R |
| 240 | PB-010 与 PB-014 同路径冗余:两者均 importlib 直载 pattern_audit 后读内存 STRONG_CONTEXTUAL_PATTERNS,与同一 EXPECTED_SC_THRESHOLDS 逐格比对,调用路径与断言同构(同一保险拉两次);非活性黑洞——模块加载真实消费 default.yaml,PB-013(--config CLI 活性)与 PB-009(默认阈值 CLI 分档)补足行为链路 | 已裁决未实施(Batch 3 测试整理时合并其一或改挂 CLI 行为断言) | zh-human-writing tests/run_tests.py | 72C-6F |
| 241 | pattern_audit.py 统计层接线注释陈旧:仍写「恒 count=0 直至任务书 §4 指标注入」,九指标已注册,名实不符(R56) | 已修(72D-1:注释改为「只读不判:命中只进 statistical 段,不参与 pass_fail/退出码;--config 覆盖时走同一 fail-closed 加载」) | zh-human-writing scripts/pattern_audit.py | 72C-6F/72D-1 |
| 242 | run_tests.py 两处注释算术小疵:PB-035 注释「5 连词→16.4‰」实为 8.2‰(5/610);PB-043 注释「5/606」实为 5/610;断言均不受影响 | 已修(72D-1:PB-035 注释改 8.2‰;PB-043 注释改 5/610*1000=8.20) | zh-human-writing tests/run_tests.py | 72C-6F/72D-1 |
| 243 | pipeline 把 media discover 任何非零退出一律判 STAGE_FAILED:可恢复的部分 fetch 失败(锁 pin 18414cc9 下 errors 全为「Failed to fetch page for 」前缀且仍有可批准候选)无法路由到批准点,整次发文被卡死 | 已修(HF-1:producers._discover_degraded_recoverable 判定 + meta 留痕 discover_degraded/discover_exit_code/discover_errors,继续既有 paused 路径;测试 5 条新增) | wxgzh_pipeline/producers.py;tests/test_hf1_discover_degraded.py | HF-1 |
| 244 | media-enrichment 退出码语义不区分「跑出候选但需审批」与「真失败」(run_media_enrichment.py exit 1 if errors else 0;gate.input_contract_pass/security_checks_pass 只是 has_errors 的投影,非独立判定) | 未修(契约债务;锁 pin 仓,归 media-enrichment 自身批次处理,本档只在 pipeline 侧做可恢复降级) | media-enrichment run_media_enrichment.py(锁 pin 18414cc9) | HF-1 |
| 245 | OBS-87 闸门对源图结构性关闭:content_description 字段只有 generated 图表写(档61-62 半截工程),源图永不写 → 源图 single_asset 批准链焊死 | 已修(HF-3:readiness 构建器按 source_page_url 抓取时提取 img alt/title(page_alt,白名单来源),过 claim 派生判定后采纳;触发条件=位置未知或内容缺失;HF-2 lane3 实证 skill 侧车道完好;skill 侧 discover 直写已于 HF-4 完成(img alt/title=page_alt > 提取上下文=page_context,meta 通道用 og:title/og:description)) | wxgzh_pipeline/approval_evidence.py | HF-3 |
| 246 | material 批准车道双堵:守卫 len(candidates)>len(asset_approvals) 把纯 material 批准判死 + material 批准不重跑分类致 review_required 永不上传 | 已修(HF-4:守卫改「每个上传候选必须有批准依据(single_asset 或 material/source_url),无依据即 FAIL_CLOSED 列明」;restricted/no-repost 永不可覆盖。HF-4R 勘误:HF-4 的重分类块仍嵌套在「elif approval is not None」分支内,注释声称两车道共用与结构不符(R56),material 批准(approval=None)实际触不到——审核方批次末端实读发现;HF-4R 将重分类块 dedent 到 for 循环体层级(与 if/elif 平级,条件逐字不变),material 车道自此真正贯通;回归=test_hf4_pure_material_lane_exit0_and_upload 忠实复现 HF-2 lane1 序列(discover 版权 unknown 冻结 review_required → continue known_allowed → eligible + 上传成功),红态实证:未 dedent 时 decision 卡 review_required) | media-enrichment run_media_enrichment.py(b3a70e7) | HF-3/HF-4/HF-4R |
| 247 | og:image/twitter:image meta 提取通道被分类器一票否决(x.com 等 SPA 源正文图只能经 meta 标签提取,原始 HTML 无正文 DOM img;A-032 1638x2048 真内容图被冤杀) | 已修(HF-4:meta 通道仅当 URL 命中动态伪卡片端点(/opengraph-image-xxxx 等)时拒绝;正常 URL 放行到安全/尺寸/质量/去重关卡;page_position 记 page-meta=页面 title,取不到则 known=false;回归 fixture=test_hf4_meta_channel) | media-enrichment image_classifier.py/image_extractor.py(26f4fec) | HF-4 |
| 248 | 来源域名质量过滤缺失:discover 无域名信誉机制,带水印/广告图可进批准链(76ty1p 的 A-265 img.ithome.com 实证);URL 广告关键词识别(AD_PATTERNS)既有,但对无标识图床 URL 不触发;HTML 容器级广告识别与水印检测均无 | 已修(76C:config.domain_blacklist 可配置域名黑名单,首批 ithome.com/img.ithome.com,URL 尾段匹配命中即拒;test_hf76c_gates 命中拒绝/非命中放行) | media-enrichment run_media_enrichment.py(c6d67e4);wxgzh_pipeline/producers.py(请求侧注入) | HF-5/76C |
| 249 | 封面 chrome 固定值:date 样品残留(2026.07)+ strike 硬编码占位(「别急着划走」)+ brand/tags 隐式落 hammer_cover 默认;谱系=增强层自生(render_article 与 hammer_* 组件层均为本 fork 增强,上游 isjiamu/gzh-design-skill 无文章渲染层,无上游修复可拉) | 已修(HF-6:render_article.py 封面全参数化——--date/--strike/--brand/--tags 四参数,date 未给时自动取渲染时点当月;不传参时除 date 外与旧产出逐字一致;用户裁决 B;验收渲染 76ty1p 真实输入 date=2026.08 标题/导语来自文章;版本 v2026.08.09-hammer.9) | gzh-design scripts/render_article.py(d947116) | HF-6 |
| 250 | 署名第二句与用户传统不一致:规范 references/common-components.md §4 自 07-19(hammer.1)落成即为「不用马上跟上，知道一点，就不算掉队。」,与用户传统落款「用克制的语言讲清楚AI前沿正在发生的事。」不符;hammer_fixed_signature 忠实跟随规范,71C 执行证据门禁封死手工定制后规范文本成为唯一输出 | 已修(HF-7:全仓 9 处逐字替换为传统落款(common-components §4 表格行+4a+4c+4d + hammer_fixed_signature + SKILL.md 示例 + showcase/测试字面);第一句「热闹是 AI 的，淡定可以是我们的。」与署名结构一个字符不动;render_article.py 不动(entrypoint/render_entry sha 不变);验收渲染 76ty1p 署名 section 第二句=传统落款;版本 v2026.08.10-hammer.10) | gzh-design references/common-components.md;scripts/generate_hammer_upgrade_samples.py(faf2d0d) | HF-7 |
| 251 | 封面文案逐篇定制路径缺失:门禁封死手工定制后无替代通道(用户五张历史封面截图实证),封面/署名文案只能落规范默认值;HF-6 已备渲染参数机制(--date/--strike/--brand/--tags)但写作侧尚无结构化产出与 handoff 契约流入 | 已修(72E-1:handoff v2.1 formatter.cover{kicker,strike,tags} 写作侧结构化产出 + gzh --kicker 参数 + pipeline producers._entry_args 读 cover 传 --strike/--tags/--brand/--kicker(--date 永远不传);封面验收渲染 76ty1p+构造 cover:构造值出现且 date=当月;prose-craft.md 末尾交接小节) | super-writer handoff v2.1;gzh-design render_article.py;wxgzh_pipeline/producers.py | HF-7/72E-1 |
| 252 | minimax-h3 生产 RUN 实证:super-writer 未产 handoff.yaml(不在 full-mode 必检清单内),致 preserve+audit 与封面文案通道静默失效——契约字段无人强制 | 已修(76A:handoff.yaml 进 validate_article_length.py --full-mode 必检 11→12(存在性+schema_version/prose_craft_applied/prose_craft_version/formatter.cover 嵌套校验,fail-closed);SKILL.md Phase 7/length-policy.md/handoff.md 同步;pipeline 契约 02_super_writer.yaml outputs 与握手产物同步加 handoff.yaml;fake_live/offline fixture 与 shim 同步;验证样本 20260810T184144 必产且 3c 正向过、负向删 handoff exit 1) | super-writer scripts/validate_article_length.py;wxgzh-pipeline contracts/02_super_writer.yaml | 76A |
| 253 | 词表 forbidden_term 误杀产品名「Luma Agents」并驱动违反「不得改产品名」铁律的编辑且 gate 放行——检测规则与产品名保护规则冲突 | 未修(规则冲突,待样本回流后修;修法方向=检测层对专有名词/产品名豁免或与领域词表联检) | zh-human-writing 词表(检测层) | 76A |
| 254 | discover 只抓已选素材致图源漏池:X 图源(pbs.twimg.com)动态渲染抓不到、带图素材在池内但未入选写作素材,三轮 Seedance 发文全撞 0 图硬墙 | 已修(76C:抓取范围扩到 deduplicated_items 全池潜力源,links.aihot 站内页(直出 HTML 绕 X 动态渲染)优先,来源扩池图仍按 OBS-86 做 claim 相关性绑定只放行相关者;pool_fetch_limit 默认 30,pool_image_count 独立计数;pipeline 侧 discover 超时 300→900s 匹配新抓取预算) | media-enrichment run_media_enrichment.py(c6d67e4);wxgzh_pipeline/producers.py | 76C |
| 255 | 用户供图注入通道缺失:发文侧无法直接提供图片直链进入批准链 | 已修(76C:runs/<RUN>/media_enrichment/user_images.json 存在则纳入候选,user_provided 资产 copyright_status=user_granted 免版权审批(用户供图责任自负,登记来源链接),asset_origin=user_provided;continue 阶段 user_granted_ids 免守卫+免 source_url 比对;SOP 写入 README「供图注入」节) | media-enrichment run_media_enrichment.py(c6d67e4);wxgzh_pipeline/producers.py;README.md | 76C |

## 未修清单（独立分区）

| OBS/项 | 问题 | 阻塞发文主线 |
|---|---|---|
| 122 | B 组 10 类未接线(71C-3 范围) | 不阻塞(71D 用 alert type=warning 承载 16 行,alert 属 A 组已接线;71D 不使用 B 组任何类) |
| 131 | A 组无并列短句载体(已裁决未实施;71D 承载见上) | 不阻塞(审核方 71E 判定:OBS-129 已修,alert 结构位成立且语义最近,故 71D/71E 用 alert 承载;71C-2 的『A 组无语义载体』结论系 alert 多行未修时点的结论;无出处直引已于 71E 删除) |
| 148 | 探针样本住在随包发布的生产文件 | 不阻塞(仅测试资产,随包发布是工程债) |
| 158 | _nearest_p_style 只取 ps[-1],不校验哨兵是否真在该 <p>…</p> 内 | 不阻塞(如实:该导出是生产侧 _COMPONENT_PARA_RES 的来源,缺陷偏「假绿」方向;71D 由 anchor_ok + 实测可见性门禁兜底,本档真实渲染已过 component_visibility,故维持不阻塞,但理由不再写「仅探针用」) |
| 159 | relock 不自动同步 OBS-69 基线 | 不阻塞(下一档 relock 前手动同步即可) |
| — | 微信端渲染 | **已关闭**(2026-08-07 02:18 用户人工预览三项全过:alert 16 行逐行显示 / /plugin 命令可复制 / 无异常删除线;用户原话「1 过 2 过 3 过」;R51 证据) |
| — | fake_live 仍不过语法门禁(R9 保留项) | 不阻塞(仅测试路径) |
| — | 键测试执行层覆盖(1a/71D):test_obs173 撤 rg 后执行层覆盖无断言 | 不阻塞(文本层 impl_keys==test_keys 断言仍在;执行层未验证已如实登记【未覆盖】,不再输出恒真警告) |
| 175 | 配图位置无机器判据(判据已落地但未挂主门禁(S65),根因 _distribute() round-robin 未动,71E 的同章结果系文章结构迎合所致) | 部分修 | 不阻塞(独立判据+文章结构可满足;挂主门禁待渲染器位置控制点) |
| 177 | 8 条 ⛔ 与 8 条 ⚠️ 压平进同一 alert type=warning | 部分修(拆两块已生效,但实现方式为单篇硬编码指令,71F 已去硬编码,通用性待 4e 验证) | 不阻塞(通用指令+反硬编码门禁已落地,重跑 16/16 覆盖) |
| 181 | placement_planner.find_anchors 的 claim_text[:30] 匹配对图表 claim 几乎必然落空 | 未修(待 relock 档由媒体侧图表 spec 直出锚点) | 不阻塞(驱动侧补写锚点+章节亲和判据兜底) |
| 182 | _APPROVED_CARRIER_COMPONENTS 模块导入时求值 | 未修,不阻塞(环境/路径变化会导致整模块 import 失败) | 不阻塞 |
| 186 | resume() 硬编码 create_wechat_draft=True,create=False 不可达 | 未修(风险已由 180 的键覆盖) | 不阻塞(真实发文路径 resume 恒 create=True,键已 fail-closed) |
| 193 | CI 全红定性(长期红,本档只查不修) | 未修(根因四类环境性失败,修复待升级/CI 环境档) | 不阻塞发文主线(CI 红不影响本地流水线发文;但升级/CI 修复前不可把 CI 绿当作验收依据) |
| 200 | 71H 5c 测试硬编码 REAL_SKILLS,类 A 12 项待 CI 环境档统一处理 | 未修(R90:只登记不单修) | 不阻塞发文主线(CI 红不构成验收依据,71I 口径正式化) |
| 212 | 写作阶段 fake/real 无独立开关 | 未修(72B 用 live+停媒体批准点真跑;DNS 拦截为环境问题) | 不阻塞发文主线(72B 已定真跑法) |
| 213 | 六闸门自评(唯一真闸 _FORBIDDEN_TERMS),Stage 3 门禁=自评(假绿#29) | 未修 | 不阻塞发文主线(官方校验器 fidelity_guard 13 项数值闸为真闸;自评字段是 agent 报告) |
| 217 | de-AI 阶段无活性断言,change_ratio=0.0 照样 PASS | 未修 | 不阻塞发文主线(0C 基线即 0.0;活性判据属 Batch 2 语义工作) |
| 221 | PB-001~006 六项仍假绿 | 部分修 | 不阻塞(PB-007~009/010 已提供真实 profile 覆盖;旧六条属 zh 仓测试整理) |
| 222 | UF-001 恒真 | 未修 | 不阻塞(测试资产问题) |
| 224 | shim 无条件通过桩(exit-2 路径与真 schema 仍零覆盖) | 部分修 | 不阻塞(fake_live 仅测试用;真实语义由 live 校验器与 0C 重跑覆盖) |
| 226 | 同步树快照潜伏陷阱(media 同步树连 pin 都无法解析) | 未修 | 不阻塞(当前配方单目标+远端见证+R109 先 push,陷阱未触发) |
| 240 | PB-010/PB-014 同路径冗余(同一保险拉两次,非黑洞) | 已裁决未实施(Batch 3 测试整理合并) | 不阻塞(PB-013/PB-009 已补行为链路) |
| 244 | media-enrichment 退出码不区分「候选待审批」与「真失败」 | 未修(契约债务,归其自身批次) | 不阻塞(HF-1 已在 pipeline 侧做可恢复降级,发文不再被卡) |
| 253 | 词表 forbidden_term 误杀产品名「Luma Agents」并驱动违反「不得改产品名」铁律的编辑且 gate 放行(规则冲突) | 未修(待样本回流后修;方向=专有名词豁免或与领域词表联检) | 不阻塞(单篇编辑已人工修正;检测层误伤面待统计) |

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
7. R52(71F):裁决直引必须给出可核验的仓内出处(文件 + 章节号),无出处不得引用。
8. R53(71F):停机条件是否触发由审核方判定;执行端只贴原文并停,不得自行判「未触发」后继续。
9. R54(71F):注入指令/提示词不得含单篇文章的专有字面量(数字对/条目数/章节映射/逐字标题),通用规则须用占位表述。
10. R55(71F):反例测试只允许改动被测的那一个变量,其余条件与对应正例逐项一致。
11. R56(71F):函数名/测试名/docstring 必须与实测行为一致,不符即缺陷。
12. R57(71G):门禁阈值不得是单篇素材的常量,必须由本 RUN 素材/文章实测量导出;素材不含该要素时显式判 N/A 并写 report,不得静默 PASS 也不得硬失败。
13. R58(71G):新增/修改环境开关必须给出「未设 / 设为允许 / 设为禁止」三态实测,缺任一态视为未验证。
14. R59(71G):台账全表与未修清单必须对账:全表所有「未修/部分修/已裁决未实施」行号必须全部出现在未修清单分区。
15. R60(71G):表格行单元格数必须等于表头列数,多格少格都是缺陷。
16. R61(71G-F):新增门禁不得依赖 ctx 属性存在;env 一律防御式读取,任何 ctx.env 直接属性访问视为缺陷。
17. R62(71G-F):凡读环境键的测试必须 hermetic:先显式 delenv 再注入,结果不得依赖开发机 shell。
18. 71G 汇报 passed 计数更正:junit 440-16-1 = 423(非 424)。
19. 71H:CI 全红定性(193)只查不修(R80);OBS-194 断言加严按 R84 例外(修复标的)并如实上报。
20. 71I:OBS-201 口径拆分——「唯一 OBS 编号数」与「台账文件行数」分列;分区重复行与口径说明行不计入缺陷计数。R89 判据禁改;R90 类 A 只登记不单修。
21. 72A:升级机制单变量对照(语义中性改动→产物必须逐字不变,S93);R91-R94;RELOCK_ALLOWED 授权范围与恢复条件见下。
22. 72A-F:R95 front-matter 禁区;R96 中性改动须落在 required_files;OBS-208 判据作废,fake_live 不得用于验证提示词升级;OBS_68 计数范围见 210。
23. 72B-0:OBS-211 runtime_manifest_sha256 为运行时文件清单哈希(内容由 skill_root_sha256 覆盖,0A 三组探测实证,四 skill 一致);OBS-212 写作阶段 fake/real 由 network_mode 单一决定,无独立开关;0C 升级前对照基线 RUN 70efs9(final_article sha 3e829be0…,素材 71e-items.json),72B 升级后须用同一素材重跑比对。
24. 72B-2/72B-2R:OBS-225 §0-6 退出码可接受性单一真源(R106,WARNING_EXIT_ALLOWED 全仓唯一);OBS-218/221/228 词表与阈值改造(SC-007a/SC-008 新增,SC-001~006 恒等变换 technical=int(×1.5) 截断,PB-010 硬编码 18 格期望值 R110,R111 禁 or 兜底);S106 作废改 S106-R(比对对象=installed vs 锁,仅 super-writer/zh-human-writing 不等才停机;media/gzh 既存差异只登记不修);R109 锁中 pin 必须 GitHub 远端可达(relock 前必 push)。唯一编号 94→110(119–228 连续,共 110),R59 未修分区 22 条。
25. 72C-2:阈值真源=config/default.yaml pattern_thresholds(文档逐条声明值,SC-001~006 §1 表 + SC-007a 阈值 1);SC-008 移入 HR-007(命中 exit 2);SC-007b 升级机制(同段 AO-001 ≥2 → strong,confidence=low);SC-005 改名「连续等长句」(OBS-227 名实对齐);OBS-219 已修退出分区;OBS-232 未修 Batch 3;OBS-233 已裁决未实施(72C-3 另建文件)。R112:配置驱动字段必须有活性断言(PB-013)。
26. 72C-3:统一 audit 十字段(rule_id/group/severity/confidence/profile/action/location/span_text/reason/suggestion,任务书 §6;location 改中文「第N段第M句」);mask_non_prose 等长屏蔽五类非散文(任务书 §7,span_text 取原文);保护区命中 action=review_only;argparse 错误统一 exit 3(OBS-234);OBS-230 已修;OBS-211 猜想入档待 Batch 3。S114:0C 八项与 72C-2 逐字相同。
27. 72C-4/72C-5:S116 释放记录——停机条件设计缺陷(比例阈值无样本量下限、且误用 advisory 级命中),审核方指令缺陷 #82;「链路」改判存疑,词表零改动。OBS-211 已坐实(路径清单哈希);OBS-236 顺序耦合规避步骤入档;三篇样本(A 真人散文/B AI 生成稿/C 技术教程)与 59 词词频表为下一档校准的唯一输入。
28. 72C-6/72C-6R:统计检测层九项指标(任务书 §4 逐字,ST-001~009)阈值与词表全部在 config/default.yaml statistical 段(标注「待校准基线」,禁统一乘数 D2,H=屏蔽后总汉字数 D1);AO-007/011 每段聚合口径(occurrence_count);OBS-227 段落边界实证(238);词表低产率保险定性(239);指令缺陷 #85(引用任务书章节未随附原文,致三次同因阻塞)。统计层 severity=audit/action=review_only,不进 pass_fail 不影响退出码。
29. 72C-6F:批次末一次性 GitHub 实读完成(核 10 commit numstat 全符、读 stat_audit/pattern_audit/default.yaml/run_tests 源码、PB-010/014 疑点坐实为冗余非黑洞、relock #20 三处同步验证、manifest 随清单 60→61 响应符合 OBS-211 口径);审核方沙箱独立复算 A/B/C 统计层,与仓内 audit-output.json 逐字一致(A=1:ST-005;B=3:ST-004/005/006;C=1:ST-005;A、B 的 ST-007 被段落门挡掉,C 无被挡);S118 判定未触发(1<3),方向正确。C 的 H/段落数按 masked 口径为 827/16(与审核方复算一致;72C-6R 汇报所用 raw 口径 895/23 已在本档修正)。
30. Batch 1 验收通过(72C-6R/72C-6F):S118 未触发(1<3),批次末实读四节全过。三条保留:统计层阈值待校准基线;词表低产率保险(56/59 零命中);0C 统计命中未人工核验。
31. HF-1:media discover 可恢复降级——errors 全为「Failed to fetch page for 」前缀且 eligible+review_required>0 时降级进批准点(meta 留痕)。根因修正:gate.input_contract_pass/security_checks_pass 是 errors 的投影,非独立判定;copyright_review.status=unknown 只给 review_required 不产 error;发文 agent 原根因链「eligible=0→exit 1」在该 pin(18414cc9)上不成立——那次 RUN(20260808T220417-qwen3-8-max-76ty1p)exit 1 真凶是 errors 数组 3 条 fetch 失败(TUN 网络段)。
32. HF-3/HF-3R/HF-3R2:OBS-87 内容描述接缝——pipeline 侧 build_approval_readiness 补 page_alt 提取(触发条件=位置未知或 content_description 缺失/为空;claim 派生防自证照旧;来源白名单已含 page_alt);尺寸门槛 480×200(用户裁决 2026-08-09);档 62 与 test_obs55 断言按裁决更新(审核方指令缺陷 #87:触发条件未预告与档 62 既有断言冲突;#88:尺寸变更未预扫 test_obs55);OBS-245 已修(pipeline 侧;skill 侧直写留 media-enrichment 批次),OBS-246 未修(material 车道双堵,HF-2 lane1/lane2 实证)。HF-3 全量 pytest 467/465/0/0/1/1。
33. HF-4:media-enrichment 锁仓正修(26f4fec,relock #21)——用户根治裁决(2026-08-09:根治不绕行,本篇 Qwen 稿是发现 bug 的载体);page-meta 位置语义裁定(推文页=内容单元本身,页级主图位置即页面,heading=页面 title,取不到则 known=false);OBS-247/245/246 已修(meta 通道去冤 + content_description 直写 page_alt/page_context + material 车道守卫语义修正);范围控制:OBS-244 退出码契约债务仍归后续,HF-1 已管线侧收口,HF-4 不动退出码语义。76ty1p 续跑操作步骤(发文侧执行,不在 HF-4):①删除 RUN 的 media_enrichment/ 阶段目录 → ②续跑 discover(修复后提取器重跑,文章冻结不动) → ③检查 approval_readiness 候选与内容描述 → ④重建 copyright_approval.json(single_asset,绑新冻结清单 sha 与新 readiness sha;旧 11 条合同对新清单自动失效属预期) → ⑤续跑 continue/上传/gzh/草稿。生产发文不在 HF-4 范围。
34. HF-4R(勘误档,b3a70e7,relock #22):审核方批次末端实读抓缺记录——①注释与实现不符的 R56 问题:run_media_enrichment.py 重分类块上方注释声称「material/source_url 批准与 single_asset 批准共用同一块重跑分类」,实际嵌套在 elif approval is not None 分支内,material 批准(approval=None)永远触不到;②测试夹具未复现生产序列:test_hf4 pure_material 在 discover 时已 known_allowed(冻结即 eligible),未复现 HF-2 lane1 真实序列(冻结 review_required + 后补批准);③审核方指令缺陷 #89 登记(HF-4 未预告 21 条预期红态清单);④执行端 HF 系列首个实现缺陷如实记(OBS-246 半修)。本档修复:重分类块 dedent(条件逐字不变;不变量=restricted 到不了这里/single_asset 身份核验失败到不了这里/single_asset 消费成功与 material 批准都会到这里)+ 测试重写(红态实证:未 dedent 时 decision 卡 review_required)+ image_classifier docstring 名实对齐(meta 通道不再一票否决,仅 URL 命中动态伪卡片端点拒绝)+ HF-4 半截升版版本串对齐 0.1.0-dev10(版本一致性两测试恢复绿)。relock #22(26f4fec->b3a70e7),R93 同步 observability.py(OBS-159=02119edf…,doctor OBS_69 MATCH 双侧)。
35. HF-5:76ty1p 生产验收完成(2026-08-09 晚,发文侧执行)——discover 重跑后 6 张候选全部 single_asset 批准、6/6 eligible、6/6 上传 mmbiz 成功、装定校验过 6 张门、wechat_draft +1(draft_only=true、real_api_call=true、formally_published=false,标题「Qwen3.8-Max正式版」);A-032(og:image 冤案)与 A-034(480×200 裁决救回)均在列——HF-1/HF-3/HF-4/HF-4R 修复链生产实证成立。新守卫「全有或全无」语义操作提示:批准点无法单独剔除单张 vetted 图,剔除只能靠上游——本例即 OBS-248 的动因之一。审核方指令缺陷 #90 登记(HF-4R 指令「冻结清单携带 decision」措辞错误;冻结清单只含身份字段,执行端已按意图正确落到 discover manifest 断言)。OBS-248 未修登记(来源域名质量过滤缺失,归 media-enrichment 批次,与 OBS-244 同批)。
36. HF-6/HF-6R:gzh-design 封面修复(OBS-249,用户裁决 B 2026-08-09 22:54,GZH_DESIGN_WRITE_ALLOWED 临时 0→1 范围仅本档,验收通过后立即改回 0)——render_article.py 封面全参数化(--date/--strike/--brand/--tags,date 未给取渲染时点当月;hammer_cover 默认值不动,parse_article/split_title/en_label_for 零改动);版本 v2026.08.09-hammer.9;验收渲染(76ty1p 真实输入):date=2026.08、标题 Qwen3/.8-Max 拆行、subtitle 来自文章、strike/brand/tags 默认值。上游谱系核对结论(审核方实读 isjiamu/gzh-design-skill):上游无文章渲染层,render_article.py 与 hammer_* 组件层均为本 fork 增强自生,无上游修复可拉。发文 agent 报告三处误读修正:①「固定文案 2」实为 H1 拆行(split_title 在 Qwen3.8-Max 无空格时按半长拆分 Qwen3/.8-Max),非空格处拆行;②brand「给自己造把锤子」是用户品牌栏(hammer_cover 参数),非固定文案;③三条根因推测(硬编码日期/固定文案/模板残留)均不成立——实为 hammer_cover 默认参数经 render 隐式落值。relock #23(ea2fb70->d947116,component_source/manifest/76 不变)。G3 裁决(HF-6R):test_obs154 红=render_entry 升级后 component_anchors.json 的 renderer_sha256 钉过期机械连带(锚内容 41 行零差异取证),按官方 --emit-anchors 重新生成(仅 sha 行+时间戳变化);审核方指令缺陷 #91(HF-6 relock 预期清单漏掉 component_anchors.json 对 render_entry sha 的钉住耦合,#88 同类)。★过程规则入册:凡 relock 触碰任一 render_entry,必须随档重新生成 component_anchors.json。OBS-73 镜像复核:parse_article 新旧 commit 函数体逐字节一致(空 diff)。
37. HF-7:gzh-design 署名第二句修正(OBS-250,GZH_DESIGN_WRITE_ALLOWED 临时 0→1 范围仅本档,验收通过后立即改回 0)——「不用马上跟上，知道一点，就不算掉队。」(07-19 hammer.1 落成即写错)全仓 9 处逐字替换为用户传统落款「用克制的语言讲清楚AI前沿正在发生的事。」(AI 大写);第一句与署名结构零改动;render_article.py 不动(entrypoint/render_entry sha 不变);版本 v2026.08.10-hammer.10;relock #24(faf2d0d,entrypoint/render_entry 不变,component_source/root/version 变,manifest/76 不变)。★封面/署名统一根故事入册:71C 执行证据门禁封死手工定制后,规范文本(common-components.md)成为唯一输出——OBS-249(封面 chrome)与 OBS-250(署名第二句)同根;OBS-251 未修(封面文案逐篇定制路径缺失,归 Batch 3 契约设计)。执行侧注记:relock #24 虽未改 render_article.py 内容(blob=ec98dcef 不变),但新 source-tree 检出使 installed 工作树行尾归一化(全 CRLF 534 vs 旧混合 514+20),工作树字节变化 → 按 HF-6R 过程规则重新生成 component_anchors.json(renderer_sha256 a30b58bb→5a54aab6,anchors 41 行零差异);installed 侧 anchors json 双侧同步后 doctor OBS_68 MATCH。
38. 72D-1/72D-1R(Batch 2 起步,任务书重建稿整批,用户 2026-08-10 00:39 批准发车):T1–T7 裁决点按页面草案锁定,裁决点 A 由审核方补全(用户可否决后重裁)——prose-craft 层(super-writer references/prose-craft.md,R1–R9 逐字,谱系 KKKKhazix/human-writing v1.1.0 MIT,上限 12 条余量 3 条不使用)+ 编辑审查扩项(段落推进 P1/翻案腔语义 P2/结尾专项)+ 说话位置五问(Phase 1 内嵌)+ handoff prose_craft 两字段 + conflict-resolution v0.4(15–18)+ zh routing preserve 前置 + OBS-241/242 注释修。审核方指令缺陷 #92(HF-7 relock 预期漏算工作树行尾归一化对锚 JSON 字节钉的连带)与 #93(72D-1 引用任务书页面未随附 R1–R9 原文,#85 同类重演)登记。验证样本 RUN 20260810T014343-prose-craft-q6qz6m(super_writer→zh_human_writing 两阶段,未进 media 及以后):prose_craft_applied=true(bool)/prose_craft_version="1.0"(str)类型正确;zh 侧 preserve+audit 生效(final_article 与输入逐字一致,三检测报告照常产出,三 exit_code 全 0);R1–R9 自检与五问痕迹在 writing-brief/HANDSHAKE。super-writer 0.3.3-rc1(relock #25,50→51),zh 0.1.1(relock #26,61 不变;verify_release 陈旧 36→80 一次对齐)。
39. 72E-1(Batch 3 契约层,交接包摘要+审核方重建,用户可否决):任务 1–6 全量——材料门分档(validate_material_gate.py,short 无下限/medium≥3/long≥5/deep 每 core claim≥2+覆盖率100%/digest 单一来源≤40%/synthesis 覆盖率100%)+ scope_reduction(失败退出表新增行,收窄记入 handoff.scope)+ handoff v2.1(handoff_stage/author_intent/allow_rewrite_scope(none|expression_only)/material_stats/scope + formatter.cover{kicker,strike,tags})+ dist/super-writer-lite.md(1054 汉字≤2000)+ SC-005 语义重写(OBS-227,句式同构骨架)+ profiles 删除(OBS-232)+ AO/HR 处置(HR-001 补 <...>、AO-006 补「不是吗？」已实现;HR-006/AO-005/AO-012 作废登记)+ OBS-211 书面证据(obs211-manifest-hash-evidence-72e1.md,skill_discovery.py L71-72 只哈希路径清单)+ 封面接线(OBS-251,gzh --kicker + pipeline cover 读取)。★重建裁决点(待用户追认):①weekly_roundup 归 digest 档;②allow_rewrite_scope 语义(枚举 none/expression_only,默认 none;与 prose_craft_applied 关系:两者同时为 true/none 时行为与现状逐字一致);③cover 三字段语义(kicker=文章类型标签/strike=被推翻的旧认知疑问句/tags=2 个内容标签);④synthesis 判定用 claim_coverage==1.0。AO/HR 处置去向:HR-001(已实现)/AO-006(已实现)/HR-006(作废)/AO-005(作废)/AO-012(作废)。验证样本 RUN 20260810T132438-batch3-ktyrck:handoff v2.1 七字段类型正确、material_stats 真实计数、材料门留痕(short 无下限 exit 0)、preserve+audit 与 Batch 2 逐字一致。relock #27/#28/#29 与 R93、upgrade_regression 等在网络恢复后执行(三仓 commit 已落盘待推:sw d395d70 / zh 944f65f / gzh c1268c7)。
40. 72E-2(升级期闭合,最终档,用户批准 2026-08-10):授权键归位——`RELOCK_ALLOWED` 1→0(72A 临时授权恢复条件达成:Batch 1/72C、Batch 2/72D、Batch 3/72E 全部验收 PASS)、`GZH_DESIGN_WRITE_ALLOWED` 1→0(历次临时授权验收均通过);其余键一律不动(`WECHAT_API_ALLOWED=0` 保持;`.env` 的 `WXGZH_WECHAT_API_ALLOWED=1` 为发文 ritual 既有状态,不属本档)。Batch 3 验收结论 **PASS**(批次末四仓实读 + 材料门校验器真身核验,六档分档逐字一致、不可评估时 fail-closed)。升级期闭合:Batch 1/2/3 全部 PASS、发文链修复 HF-1~HF-7 全部验收、relock 累计 29 次。口径 39 四点重建裁决:用户明示不再逐一评审、授权审核方按默认落定并负全责——①weekly_roundup 归 digest 档;②allow_rewrite_scope 枚举 none|expression_only、默认 none;③cover 三字段=kicker/strike/tags;④synthesis 用 claim_coverage 判定。审核方指令缺陷 #94 登记(72E-1 任务书「传 --brand」与 cover 三字段口径不一致,执行端按实际键传参处置正确)。搁置项(用户指示,使用中即测试,一句话可重启):≥10 段真人长文重测 S118、词表校准、few-shot 语料收集(Batch 4 预案)、OBS-214 端到端、CI 环境档。未修复留:OBS-248(域名黑名单,下次发文注意 ithome 类水印图)、其余 R59 分区条目。本档无代码变更、无 relock。
41. 76A(生产补丁批,用户批准 2026-08-10,RELOCK_ALLOWED 临时 0→1 范围本档):handoff 强制化(OBS-252)——validate_article_length.py --full-mode 必检 11→12,handoff.yaml 存在性+schema_version/prose_craft_applied/prose_craft_version/formatter.cover 嵌套校验 fail-closed;SKILL.md Phase 7/length-policy.md/handoff.md 同步;pipeline 契约 02_super_writer.yaml outputs 与握手产物(SUPER_WRITER_AGENT_OUTPUTS)+_agent_validator_args 同步。标题打磨(用户点单):Phase 3 攻核后产 3–5 候选标题+一句钩子,handoff v2.1→v2.2 新增 title_candidates(数组)/hook_line(字符串),formatter.cover.strike 未指定时默认取 hook_line(联动默认);候选标题供草稿箱挑选,不自动替换 H1。OBS-253 未修登记(词表 forbidden_term 误杀产品名「Luma Agents」,规则冲突待样本回流)。验证样本 RUN 20260810T184144-76a-handoff-8p06aa:handoff 必产且 3c 正向过、负向(缺 handoff)exit 1、preserve+audit 逐字一致、封面渲染定制 kicker/tags 出现。relock #30(super-writer d395d70→45b51ce,0.3.5-rc1,validator_sha256 变 f2f878b1→4ad677aa,entrypoint 不变,53 不变,manifest 不变);执行侧注记:relock installer 首次因控制台 GBK 编码崩溃(锁已写、树未装),手动按官方 write_install_receipt 完成树同步+receipt,后续 relock 均以 -X utf8 运行。pipeline pytest 468/466/0/0/1/1 逐字不变。
　　【76A-F 补记】档 76A 验收 PASS(审核方 2026-08-10 远端点验两仓 numstat 逐字一致:super-writer 45b51ce / pipeline 204c17b;负向 fail-closed 实证在案:缺 handoff → exit 1)。RELOCK_ALLOWED 归位 1→0(见授权登记节)。

42. 76B(标题选定闭环,用户批准 2026-08-10,RELOCK_ALLOWED 临时 0→1 范围本档):Phase 6 内容审稿新增子步骤「标题选定」——Reviewer 角色(非 Writer)按固定评分尺(具体>有判断>贴核心张力>长度≤30字>无标题党空壳)从 title_candidates 选定最终 H1 并写一行理由;article.md H1=选定标题(封面拆行随 H1 自动生效);title_candidates 保留备查;禁止另造候选外新标题。handoff v2.2 追加 selected_title/title_selection_reason 两字段(字符串)。Phase 3.5 描述更新。测试 +1(字段存在性/类型/契约),242 passed。无新 OBS。sw 0.3.6-rc1,relock #31(9ab1bce,entrypoint/validator/53/manifest 不变)。　　【76B-F 补记】档 76B 验收 PASS(审核方 2026-08-10 远端点验两仓 numstat 逐字一致:super-writer 9ab1bce / pipeline 3bdca9a)。RELOCK_ALLOWED 归位 1→0(见授权登记节)。
43. 76C(媒体批,用户批准 2026-08-11,RELOCK_ALLOWED 临时 0→1 范围本档,恢复条件=验收通过后立即改回 0):门禁降级链(用户裁决原文:图片数量不再是发文限制条件,缺图时以生图车道兜底;生图也兜不足→允许少图交付,receipt/handoff 留痕 image_shortfall=true+实际图数,不静默;body_images_min 保留为目标值不再是阻断条件)——pipeline 侧 validate_media_bindings/contracts/stage/evidence/state 同步降级语义(短少进 image_shortfall 不再 FAIL,count>8 与 bindings 一致性仍 FAIL);gzh 主题校验器 validate_theme_identity 图片组件类型门槛 2→1 随 image_shortfall 降级(默认无短少行为不变,test_theme_infra 新增降级断言);Codex 图表车道官方化记录(生图兜底=用 claims 绑定数字/事实生成图表,铁律=只可视化 claim 支撑数据不得编造,自产图免版权审批但内容审核照走 OBS-89 判重)。OBS-248 已修(域名黑名单 ithome.com/img.ithome.com,URL 尾段匹配命中即拒,名单可配置)/OBS-254 已修(discover 扩池 links.aihot 站内页优先,pool_fetch_limit 默认 30)/OBS-255 已修(供图注入 user_images.json,user_provided 免版权审批,SOP 入 README)。media-enrichment 0.1.0-dev10→dev11(c6d67e4),relock #32(full_commit/source_tree/root/version/entrypoint 变;validator/manifest/59/required_files 不变),R93 同步 observability.py 双侧,upgrade_regression ALL PASS,doctor PASS/OBS_69 MATCH/OBS_68 MATCH 双侧。验收(实证,RUN 20260811T205905-seedance-2-5-7x4nh8,live 全链):aihot(50 素材)→super_writer(复用 20260810T225901 全套真实产物)→zh→media discover 扩池(44 页预算,1 review_required 候选 A-004 the-decoder.com 1200x675 page-meta 内容描述)→single_asset 批准→上传 mmbiz 成功(1/1)→gzh(降级主题校验过)→wechat_draft 真实 API 草稿+1(draft_only=true、real_api_call=true、formally_published=false,标题 Seedance 2.5);image_shortfall=5 留痕(state+side_effects+final_delivery),allowance_record 放行 18 处半角标点(WXGZH_ALLOW_WARNINGS=1,档54R 正式通道,双层显式+逐条留痕)。执行端操作偏差如实记:①误以 offline_fixture 续跑原冻结 RUN(20260811T005013)致其上游产物被 fixture 覆盖(原文章不可恢复,仅 claims/冻结清单幸存)——改为同主题新 RUN 并复用 225901 真实文章产物,原 RUN 损坏事实已记入本口径;②discover 300s 旧超时预算与扩池不匹配(实测 44 页抓取超时),超时 300→900s;③gzh THEME_IDENTITY image_types>=2 门槛未在任务 0 预告(1 图交付即红)——与 76C 降级链语义冲突,本档修(审核方指令缺陷 #95 登记,未预告既有校验器与降级链的冲突,#88 同类)。pipeline pytest 469/467/0/0/1/1(+1=test_theme_infra 少图降级断言);media pytest 306 passed/6 skipped(+4=test_hf76c_gates)。

### ★授权变更登记(72A,不可省)

> `RELOCK_ALLOWED` 于档 72A 由 0 改为 1,批准人=用户,范围=整个升级期(72A/72B/72C),恢复条件=super-writer 与 zh-human-writing 两个 skill 升级全部完成后立即改回 0。在恢复之前,每一档的 a 段必须显式复述本条恢复条件。
>
> **归位(档72E-2,用户批准 2026-08-10)**:恢复条件已达成——Batch 1/72C、Batch 2/72D、Batch 3/72E 全部验收 PASS,`RELOCK_ALLOWED` 由 1 改回 0,升级期闭合,本条恢复条件不再复述。
>
> `GZH_DESIGN_WRITE_ALLOWED` 于档 HF-6/HF-7/72E-1 三次临时由 0 改为 1(批准人=用户,范围=各档任务项),恢复条件=各档验收通过后立即改回 0。**归位(档72E-2):历次验收均已通过,由 1 改回 0**;后续如需使用须重新申请。
>
> `RELOCK_ALLOWED` 于档 76A 二次临时由 0 改为 1(批准人=用户,范围=档 76A 一处补丁),恢复条件=本档验收通过后立即改回 0。**归位(档76A-F,审核方 2026-08-10 验收通过):由 1 改回 0**。
>
> `RELOCK_ALLOWED` 于档 76B 三次临时由 0 改为 1(批准人=用户,范围=档 76B 标题选定闭环),恢复条件=本档验收通过后立即改回 0。**归位(档76B-F,审核方 2026-08-10 验收通过):由 1 改回 0**。
> RELOCK_ALLOWED 于档 76C 四次临时由 0 改为 1(批准人=用户,范围=档 76C 媒体批:门禁降级链/discover 扩池/域名黑名单/供图注入),恢复条件=本档验收通过后立即改回 0。**归位:待审核方验收宣告后执行(同 76A-F/76B-F 规程)**。

## ★CI 口径正式化(OBS-193,71I 显著声明)

1. CI 自有记录以来(≥100 次运行,最早 2026-08-06T07:01Z)零 success,长期红。
2. 根因四类并存:类 A 硬编码开发机路径(12 项)、类 B CI 未安装被锁子技能、类 C bs4 依赖缺失(8 项)、类 D 陈旧 LOCKED_HEADS 与 OBS-69 内嵌基线(4 项)。
3. CI 绿不构成验收依据,CI 红也不构成停机依据;一切验收以本机 junit 为准。解除条件:四类全部清零且 CI 出现第一次 success 之后,本条作废。