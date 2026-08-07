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
| 211 | runtime_manifest_sha256 不提供 required_files 内容哈希(0A-1/0A-2 实证:该值=compute_runtime_manifest_sha 的运行时文件【清单】哈希,skill_discovery.py:67,relock 写锁为重算赋值 relock.py:567/622;0A-3 三组探测 root 变/manifest 不变,四 skill 行为一致);72A-F「形同虚设」结论修正为「口径澄清,内容由 skill_root_sha256 覆盖」;但 required_files 单文件内容漂移无独立指标 | 未修(留升级机制档决定是否新增 required_files 内容哈希指标;当前内容完整性由 root sha 覆盖) | wxgzh_pipeline/skill_discovery.py:67;scripts/relock.py:567/622 | 72B-0 |
| 212 | 写作阶段 fake/real 无独立开关(0B-1 实证:由 network_mode 单一决定,producers.py:277 fake_live/integration=FakeAgent fixture 重放,live=人工交接);真跑需 live 模式+人工交接,无自动化真写开关;0C 实测还受 TUN DNS 影响媒体发现(github.com→198.18.0.9 被 URL 安全检查拦截) | 未修(登记:72B 采用 live+停媒体批准点的真跑法;DNS 拦截为环境问题,非代码) | wxgzh_pipeline/producers.py:277;orchestrator.py network_mode | 72B-0 |

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
| 211 | runtime_manifest_sha256 无 required_files 内容哈希 | 未修(口径已澄清:清单哈希,内容由 root sha 覆盖;单文件漂移无独立指标) | 不阻塞发文主线(内容完整性现有 root sha 兜底) |
| 212 | 写作阶段 fake/real 无独立开关 | 未修(72B 用 live+停媒体批准点真跑;DNS 拦截为环境问题) | 不阻塞发文主线(72B 已定真跑法) |

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

### ★授权变更登记(72A,不可省)

> `RELOCK_ALLOWED` 于档 72A 由 0 改为 1,批准人=用户,范围=整个升级期(72A/72B/72C),**恢复条件=super-writer 与 zh-human-writing 两个 skill 升级全部完成后立即改回 0**。在恢复之前,每一档的 a 段必须显式复述本条恢复条件。

## ★CI 口径正式化(OBS-193,71I 显著声明)

1. CI 自有记录以来(≥100 次运行,最早 2026-08-06T07:01Z)零 success,长期红。
2. 根因四类并存:类 A 硬编码开发机路径(12 项)、类 B CI 未安装被锁子技能、类 C bs4 依赖缺失(8 项)、类 D 陈旧 LOCKED_HEADS 与 OBS-69 内嵌基线(4 项)。
3. CI 绿不构成验收依据,CI 红也不构成停机依据;一切验收以本机 junit 为准。解除条件:四类全部清零且 CI 出现第一次 success 之后,本条作废。
