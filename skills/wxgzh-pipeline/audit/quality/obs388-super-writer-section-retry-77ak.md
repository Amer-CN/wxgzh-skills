# OBS-388 —— 77AK super_writer 阶段耗时解耦验收报告（字节级落盘）

- 档号：77AK（super_writer 阶段耗时解耦 = pipeline 侧指令瘦身 + 单节 helper + 单节回滚重试路径；B 类完整流程档，含 77AK-R 审核方裁决附记）。
- 基线提交：`7b6417d`（main，工作树干净核验于 2026-09-15）。
- 授权：本档**零授权变更**（RELOCK_ALLOWED 维持 0——pipeline 无锁条目不涉锁；GZH_DESIGN_WRITE_ALLOWED 维持 0）。授权登记行随 feat 落账（序数按台账实况=五十八次，77AJ 已占五十七）。
- 停机底线（简报原文口径）：如实现必需触 sw 树任一文件，立即停机上报（fail-closed，未自裁）；禁自行 relock/扩权/写 skill 树。本档实测**未触 sw 树任一文件**。
- 交付形态：执行端不 commit（角色硬规则），**7 文件**留工作区（tracked 改 4 + 新增 3），待主智能体 `feat(77ak)` + `docs(77ak)` 落提交。

## 1. 任务 0 证据（只读贴回存档）

- 耗时实证锚点：tjyl4w RUN super_writer wall **2354s**，真生成约 2 分钟（article.md 16:49 落盘），其余为 agent 自查等待；失败即整阶段重跑。
- 整阶段重跑机制：`stages/__init__.py:321-322`（exit_code≠0 → `StageError`）→ `orchestrator.py:439-442`（`mark_failed` + `FAIL_CLOSED`）。
- 握手锁死粒度：`agent_handshake.py:10-12`（token 绑 request 字节 + 产物哈希 + upstream）、`:104-111`（`write_ack` 逐产物哈希）、`:146`（`verify_ack` 重算 token）。
- 分节口径只读复用源：`skills/super-writer/scripts/validate_article_length.py:175-201`（`split_sections`：`^(#{1,6})\s+(.+)$` 标题行分节、``` 围栏内跳过；本档**禁改 sw 树**，只同形复刻分节口径到 pipeline 侧）。
- 校验链挂点：`producers.py:240-307`（`_agent_validator_args` 五条官方校验器）、指令 L62（`AGENT_INSTRUCTIONS["super_writer"]`）、复用判定 L347-364（`_reusable_agent_request`，未动语义）。
- resume 语义：`orchestrator.py:292-334/391-393`（只跳已完成阶段，receipt 失效即从该阶段重跑）。

## 2. 任务 1 实现

**① 指令瘦身（`wxgzh_pipeline/producers.py`，sw 指令块）**

- 删 agent 冗余自检轮次措辞：「`失败补字段重跑,`」（与 77M/OBS-330「ACK 前本地全套 VSP 预检清零再 ACK」重复——同一件事被写了两遍预检轮次）。
- 同句补口径锚点：「`(pipeline 官方校验链=唯一真源)`」。
- 义务锚点逐条保留（`test_hf76r.SW_ANCHOR_GROUPS` 33 组锚点逐条在场）；指令实测长度 **2830 ≤ 3000** 上限（`test_hf76r::test_77c_sw_instruction_compressed_anchors` 绿）。
- 语义零丢失清单（`test_hf76r::test_obs288_semantic_zero_loss_rule_inventory`）绿：`extra` 集合为空、无规则号丢失。

**② 单节 helper（新增 `wxgzh_pipeline/section_retry.py`，7483 字节）**

- 分节口径与官方 `split_sections` 同形：标题行分节、``` 围栏内不计标题、preamble 归首节（首节无标题行时 `title="(preamble)"`）。
- `SectionRetry`：`locate()`（header 优先、index 次之、两者皆空=首节）/ `section_text()` / `rewrite_section()` / `unchanged()`（以首次加载原文为基准，确认**其余节逐字未动**）/ `other_section_texts()` / `write_back()`（`write_bytes`，保留原行尾字节）。
- 组装=逐节原文字节拼接；`reassemble_preserving_headings()` 对标题行做前后比对，丢失即 `ValueError`（防朴素 join）。
- **朴素 join 会丢标题行与行尾换行**——测试用独立断言坐实：朴素 join 产物不含 `# 第一节`，本节 assemble 产物与原文逐字节相同。

**③ 单节回滚重试路径（`producers.py` 官方校验链）**

- 单一真源常量（模块顶）：`SECTION_RETRY_MAX_ATTEMPTS = 1`（显式重试上限）、`SECTION_RETRY_VALIDATORS = ("validate_article_length.py",)`（只有节粒度的官方校验器进单节路径）。
- 触发门（**回滚路径，不是放宽门禁**）：失败报告（`<脚本名>.stdout.json`，即 77M 起 producer 自采的官方 stdout 落盘）自报 `sections == 1`，**且** `ctx.section_retry_driver` 在册，**且** `article.md` 在盘。
- 重试动作链：失败节重生成（driver）→ `unchanged()` 守卫（其余节被动过即拒写）→ `write_back()` → **token/ACK 按盘上现状重算重写**（`AH.write_ack`，沿用原 `agent_id`；口径=agent_handshake L104-111/L146）→ 只重跑 `SECTION_RETRY_VALIDATORS` 命中的校验器（其余校验器及其 stdout 落盘产物零副作用）。
- 回退语义（逐条实测）：无 driver / ctx 无该属性 / 失败节数非 1（整篇级）/ 超出上限 / 定位失败 / 重生成返回非串 → **一律保留既有整阶段重跑 + FAIL_CLOSED 语义**。
- 旧调用兼容：**未改 `StageContext`**（无新字段，追加实参无从谈起）；`producers.py` L439 用 `getattr(ctx, "section_retry_driver", None)` 兜底读取（照 R61 口径），测试端 ctx 全用 `SimpleNamespace`——旧调用行为逐字不变。

**④ 测试（新增 `tests/test_hf77ak_section_retry.py`，18 绿）**

- 单节失败注入 → 失败校验器跑 2 次（首跑 + 单节重试），其余校验器各 1 次（`material_ingestion.py`/`validate_semantic_map.py` 各 1、`validate_single_product.py` 2=article+registry 两次首跑、零重跑）。
- 其余产物逐字节不变：调用前快照 vs 调用后哈希，**仅 `article.md` 内容变**；新增文件恰为握手三件套 + 校验器 stdout 落盘 + `full_mode_validator_report.json`。
- ACK token 重算实证：`AH.verify_ack(...) → token_ok=True`，`agent_id` 沿用。
- 重组装无损 8 样本（含 fenced 内伪标题、空节相邻、无标题、无尾换行、空串）逐字节恒等。
- 边界：`unchanged()` 拒写其他节被动过的组装；上限常量生效（stubborn driver 不变好 → 1 轮后保留失败语义）；整篇级 `sections=2` 不进单节路径。

## 3. 任务 2 升版 / 装机同步 / 回归

- **升版**：`VERSION` `0.1.0-dev2-hotfix9R34 → 9R35`（`previous_version` 同步 9R34，`release_date` 按 77X 写入日口径改 2026-09-15；status/kind 不动，#102 版本号以实测口径为准）。
- **装机同步**（`Copy-Item` 保字节，非文本管道再写）：8 文件逐文件 SHA256 MATCH（`VERSION` 135B / `producers.py` 112375B / `section_retry.py` 7483B / `stages/__init__.py` 14984B / `test_hf76r.py` 19507B / `test_hf77ak_section_retry.py` 15543B / `obs-ledger.md` 326813B / 本报告 10459B）。其中 `stages/__init__.py` **已回退**：repo 侧 `git diff` 零输出（与基线 7b6417d 逐字一致），装机侧与仓侧 SHA256 一致（`D623F5AD…`，14678B），双侧回到基线，不在本档交付面。
- **回归**：改后全套 `pytest` = **635 passed / 7 failed / 22 skipped / 664 collected**；7 红名单与基线**逐项同名一致**（hotfix1×1 + hotfix7×3 + obs171×1 + obs80×2），**零新红**；新增 18 绿。
- **doctor 双侧**：`PASS`、`FAIL_CLOSED=false`、`LIVE_PIPELINE_ALLOWED=true`；`OBS_69_LOCK_MATCH=MATCH`（两侧 `79f5cf7e70c680a1…`）；`OBS_68_PIPELINE_MATCH=MATCH`（repo 813 / installed 813 / diff 0 / missing 0 / extra 0）。
- **零 relock**：`git status --short` 对 `skills.lock.json` / `skills.lock.history.json` / backups **零输出**；锁 sha 恒为 `79F5CF7E70C680A12239B2AE9D9234A6B059C84AAA7209C3146B9CAD35BA1C8D`（与 doctor 双侧一致，relock #117 后未变）。

## 4. 台账

- 追加三处（禁改历史行，`git diff` 实测 obs-ledger.md **仅 +3 行、零删除**）：OBS-388 行（全表，已修，不入未修分区）、口径 103、授权登记行（五十八次维持 0）。
- 唯一编号实测：**270**（119–388 连续无缺号；`test_hf76r::test_obs304_ledger_count_command` 钉子同步 269→270、区间 388→389，随 feat 落账）。
- R59 对账：本档自拟测量工具对不上既有口径（partition 79 行 vs 主表 23 条未修行，双向差集非空），**该工具数字不作为结论**；本档判据以既有 77V–77AJ 沿用口径为准（OBS-388 为已修、不入分区，与 77AJ 同型）。如需严格复现 R59，请审核方提供既有 R59 脚本。

## 5. 执行过程如实记（含一次自纠）

- **一次自纠（重要）**：把 `_agent` 校验器内联循环抽成 helper 时，首版按「记录序号=校验器序号」就地回填，导致 `except ValueError` 分支先追加的**错误记录（exit 2，`error="invalid generation-profile.yaml…"`）被覆盖**，`test_hotfix7::test_corrupt_policy_fails_closed_but_runs_material_and_semantic` 转红（基线绿）。定位方式=stash 到基线复跑该用例确认基线绿，再逐行比对；修法=helper 只返回记录、由调用方决定写回，`validator_start` 偏移量入参保证校验器记录起点在错误记录之后。修复后该用例回绿，全套 7 红与基线逐项同名一致。
- 升级路径如实：简报任务 1 的「指令瘦身」按 77AK-R(b) 口径（*非钉子红线停机、允许逐字对应的钉子断言同步*）执行，**未改任何钉子断言之外的红**；`test_hf76r.py` 仅动 obs304 钉子块三行（+1 注释行）。
- 装机侧同步后 `producers.py` / `test_hf76r.py` 两文件曾因后续自纠改动而落后一拍（doctor 首跑 `OBS_68=DIFF, diff_total=2`），**重新 Copy-Item 后 OBS_68 回 MATCH（813/813、diff 0）**——过程如实记。
- `wxgzh_pipeline/__init__.py` 的 `__version__` 仍为 `0.1.0-dev2-hotfix9R19`（doctor 的 `wxgzh_pipeline_version` 字段读它）：系 77L 起的既存陈旧值，**非本档改动、本档未动**（简报允许清单未含该文件）。
- 装机侧与仓侧既存差异（非本档引入、未动）：`audit/quality/obs387-toc-denum-77aj.md`（77AJ 报告仓侧在册、装机侧缺）、`audit/quality/title-hits.md`（生产台账装机侧多生产行）、`.gitattributes`（仅仓侧）。
- flow-gate 登记：本工作区（`F:\AIXM\wxgzh`）门禁要求 `.work/task-<关键词>.md` 声明改动面，故按权威简报原样登记 `F:\AIXM\wxgzh\.work\task-77ak-section-retry.md`（指针简报，不新增范围）。
- `.work/` 脚本与 doctor/JSON 中转产物（`.work/ledger_check_77ak.py`、`.work/r59-77ak.json`、`.work/doctor-*.json`）系中转，未入锁面、未随档交付。

## 6. 基线链

`7b6417d（77AJ-F）→ <本档工作区 7 文件：tracked 改 4（producers/VERSION/test_hf76r/obs-ledger）+ 新增 3（section_retry.py/test_hf77ak_section_retry.py/本报告）> → 待主智能体 feat(77ak)+docs(77ak) 落提交并 push`
