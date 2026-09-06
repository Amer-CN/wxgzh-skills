# OBS-374/375/376 —— 77Z 版本检查口径+信封刷新+标题证据验收报告（字节级落盘）

- 档号：77Z（版本检查口径修正 + 握手信封官方刷新 + 标题候选证据完备化）。
- 授权：RELOCK_ALLOWED 临时 0→1（批准人=用户，范围=super-writer；pipeline 无锁条目不涉锁）；GZH 维持 0。授权登记行随 feat 落账。
- feat 提交：0446ce3（18 文件：15 改+3 新增测试）。
- 证据 RUN：20260905T165906-weathernext-3-tlztos / 20260906T170720-gpt-6-astra-skr87r（STALE_VERSION behind+--allow-stale 连续两篇）；0srcql/tlztos/skr87r（title_selection_reason 仅主标题带五维）。

## 1. 任务 0 坐实（存档）

- version_check behind 判定=纯日期比较（:210 `tag_date > baseline 元组`）；installer 写入点=install.py `_write_installed_from`（_git/_bundle_source_proof sha 链现成）。
- verify_ack（agent_handshake.py:150-158）upstream_hashes 逐 rel 重算比对；`_reusable_agent_request`（producers.py:333-345）只比 run_id/stage/expected_outputs——**不含 upstream 时效**；invalidated_from 重置点=orchestrator.py:333。
- 标题门现行（validate_single_product.py:288-306）：五维/风险只查 reason 整体字符串包含；三篇 RUN 摘录：0srcql 287 字（仅候选1 五维）、tlztos 265 字（明写「五维评分（选定主标题）」）、skr87r 518 字（同型）——证据层薄于门检层坐实。

## 2. 三件实现（OBS-374/375/376）

- **374 内容口径**：install.py 落 `.installed-from` 标记（source_commit/resolved_tag/recorded_at 单行 JSON）；version_check 优先标记比对（latest tag sha==标记 sha→current；不等→behind 且更新路径真实可清除）；日期降为 detail 展示；标记缺失/空→回退日期口径；离线 unknown。`_ls_remote_tags` 升级双列（tag+sha）。测试 6 绿（标记 current/behind/缺失回退/离线+落盘契约 2）。核心断言实证：标记 sha==latest 但日期早→current（日期粒度误报消除）。
- **375 信封官方刷新**：`_reusable_agent_request` 加 upstream 时效校验（第 5 参 upstream；信封 upstream_hashes≠当前盘上→不复用→`_agent` 既有覆盖写=编排器自动重签，零删文件）；76F 禁删对象明确=产物/receipt，信封重签不在禁列（_COMMON_RULES 77Z/OBS-375 明路）。测试 4 绿（合法修正重签/未变复用字节不变/重签后 verify_ack PASS 零删/明路在册）。
- **376 标题逐候选**：VSP `_title_candidate_errors`——每候选四组归属+五维（五项 1–5 整数）+显式风险标记（「无」必须显式）；缺一 FAIL 指路 title-playbook.md；候选为纯字符串时分组按 reason「组=标题」映射、五维/风险按候选同句段窗口（句段边界 `；;。`——历史 reason 后置总段误记防护，干跑实证必要性）。sw Phase 6 指令硬措辞同步（producers，obs288 白名单 376 随档）。测试 4 绿。
- 三篇历史 RUN 新门干跑全 FAIL+指路原文在 executor 报告在册（各 11 条 playbook_errors）。

## 3. 裁决与连带（如实）

1. 3 处夹具同步（test_hf76f_tools/test_hf76t_strike_assumption/test_hf77k_quote_gate）——title_selection_reason 77O 整段式升级 77Z 逐候选式，断言语义零变化（77W/Y 先例同型）：主智能体授权认可。
2. **档文「应 258，119–378」算术矛盾**：258 个连续编号自 119 起止于 **376**（258=255+3，规格 D 仅定义 374/376 三行）；executor 未编造 377/378，实测口径为准——obs304 钉子按 258/119–376 随档。
3. obs288 白名单随档：77Z/OBS-375（aihot 面）+77Z/OBS-376（super_writer 面）双补——首补 375 仍红（376 在 sw 键）、二补双绿（test_hf76r 19 绿）。
4. **zipping.py PIPELINE_RELEASE_EXCLUDES 加 `.installed-from`**（规格 A 直接连带，主智能体执行）：relock 内建 installer 把标记落装机侧后 OBS_68 报 extra → 同源豁免（installer 与 OBS_68 共用 release-include 规则，`.gitattributes` 同型先例）→ 双侧 MATCH 恢复。

## 4. 已知边角（如实登记，不扩案）

- **relock 场景标记 source_commit 为空**：relock 内建 installer 从 source-tree bundle 装（bundle 无 .git），`_git` 解析 HEAD 得空——装机侧实测标记 `{"source_commit":"","resolved_tag":null,…}`。行为正确：空标记→回退日期口径→current（结论无误，真实跑原文在案）。标记通道在真实 install.py 安装场景（用户复装，源仓直装）落有效 sha。修 relock 调用链需动锁链脚本，风险不对等，留待需要时授权。

## 5. 升版/锁链/回归（77Y-F 新规：回归在 relock 后）

- 升版：sw 0.4.19-rc1→**0.4.20-rc1**（hotfix 77Z/2026-09-06/test_count 296；MANIFEST 111 条目全过）；pipeline 9R29→**9R30**（release_date 2026-09-06）。
- relock **#108**（sw 0.4.20-rc1，远端见证 a/b/c PASS，apply 全链 PASS，备份在册）；锁 sha `916422e9…→50e87521700a62a2b254bd9baf562c80cadf9bb4ef165df937626dd57ecb4f35`，R93 双侧一致。
- doctor：双侧 PASS、OBS_69 MATCH、OBS_68 MATCH（zipping 豁免后）。
- **最终回归（relock 后跑，77Y-F 新规首用）**：唯一红=obs154×1 既有红——**零新红**（77Y 两颗潜伏红已修复在案）；relock dry-run ×4 无变化 OK。
- 真实 version_check 跑（装机侧）：status=current（回退口径，§4 边角注明）；五技能版本全对（sw 0.4.20-rc1/media dev33/gzh hammer.22/zh 0.1.14/pipeline 9R30）。

## 6. 程序校验

- 唯一编号：`258 119 376 True`（258=255+3；档文「378」系笔误，按规格 D 与实测更正，§3.2）
- R59：`main=21 partition_active=21` 双差集空
- 授权登记行：恰 1 行；更正附记在册（WeatherNext STALE_VERSION 误判→374 / 标题五维销账误判→376，77L-F/77U-F 先例）

## 7. 基线链

`8c73259（77Y-F）→ 0446ce3（feat 77Z，含授权登记行+obs304/obs288 随档）→ <docs 本报告+zipping 连带+锁链>`
