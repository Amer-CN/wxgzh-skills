# 档 41 — 素材注入路径调研 + gzh-design 升版备料(纯只读)

- 报告编号:material-injection-survey-41
- 执行日期:2026-08-02(Asia/Shanghai)
- 性质:纯只读;唯一写入为本报告。未修改 `.agents\skills` 任何文件、未改 lock、未调微信接口、未跑 Pipeline、未删除任何文件。
- 工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(dev/0.1.0-dev2,起点 HEAD `ab6e478`,档 40)

---

## 第一 aihot 阶段的素材注入能力

### 1. 输入契约与调用方式

- 阶段实现:`wxgzh_pipeline/stages/aihot.py`
  - `stage_inputs` L20-22:仅 `{"topic": state.topic}`
  - `run_live` L38 → `producers.produce(ctx, "aihot", state)`
  - `content_validate` L25-35:只要求 `deduplicated_items.json` 存在且 `len >= 1`
- 契约:`contracts/01_aihot.yaml` — `inputs.required=[topic]`;`outputs.required=[raw_items.json, deduplicated_items.json, fetch_log.json]`(hashed);`gates: deduplicated_count >= 1`;`forbidden: [write_article, final_image_inventory]`
- 执行方式:aihot 为 `agent_invoked_skill`(execmodel `STAGE_EXEC`=AGENT),**无 CLI**。live 模式下由 agent 按握手契约(`agent_handshake.json`:`produced_files` 三文件 + `produced_hashes`)调 aihot skill(只向 `https://aihot.virxact.com/api/v1/*` 匿名只读请求),再落盘三个文件。
- **是否支持跳过抓取/外部注入**:无任何 `--items-file` / `--source` / 等价参数(整个 aihot 阶段没有 argparse;cli.py 只有 `--offline/--fake-live/--integration/--fixture-dir` 属开发模式)。注入入口盘点:
  - 开发模式:offline fixture(`fixtures/offline_pipeline_fixture/aihot/outputs/`)、fake_live fixture(`fixtures/fake_live_fixture/aihot/outputs/`)
  - live 模式:**无正式入口**;但 live 是 agent 中介,agent 可以手写三个文件——事件 RUN `20260801T231452-vibe-coding-guide-v2-1-1vg6jx` 已实证:`fetch_log.json` 记录 `mode=user_materials_override`、`aihot_api_skipped=true`、18 条用户素材(「AI HOT 阶段按用户要求跳过 API」)。代码层面没有「必须调用 API」的强制,只有 aihot skill 的规则约束与如实记录约定。

### 2. deduplicated_items.json 完整 schema(实测 + 消费方读取)

顶层为 JSON 数组;元素字段(基于 RUN2 真实数据与消费方代码):

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | 是 | 去重键 / 资产绑定键(事件 RUN 用 `user-material-NN`) |
| `title` | string | 是 | 标题,进入正文事实/标题 |
| `summary` | string | 否 | 摘要,正文事实的主要来源;**自由文本,源码片段最合适放这里** |
| `originalTitle` | string | 否 | 原文标题 |
| `source.name` | string | 是 | 来源名 |
| `links.original` | string | 是 | 原文 URL |
| `links.aihot` | string | 是 | AI HOT 页 URL |
| `source_url` | string | 是 | 抓取源(media 阶段使用) |
| `aihot_permalink` | string | 是 | media 阶段与 canonical_claim_registry 一致性校验(`producers.py` L484-487,不一致 FAIL_CLOSED) |
| `publishedAt` / `discoveredAt` / `latestAt` | ISO 时间 | 否 | 时间线 |
| `sourceCount` / `signalCount` / `sourceNames` | int / array | 否 | 聚合统计 |
| `category` / `score` / `selected` / `attribution` / `query_origin` | 混合 | 否 | 元数据(事件 RUN 用 `category=project-update`,非标准值) |

- 消费方读取:`producers.py` `_dedup_index` L338-360(`id/source_url/aihot_permalink/title/summary` 等);media 请求构造 L429-499(`material_id` 分配、`aihot_permalink` 一致性、`source_url`)。
- 真实样例(节选 RUN2,AlloyDB 条目):`{"id": "cms7q9upv0q0gro2ev1apyhwk", "title": "AlloyDB 推出 IAM 群组认证预览版…", "summary": "Google Cloud 宣布 AlloyDB 推出 IAM 群组认证(预览版),允许安全团队通过最多 200 个 Google Groups 管理数据库访问…", "source": {"name": "Google Cloud：Databases（RSS）"}, "links": {"aihot": "https://aihot.virxact.com/items/cms7q9upv0q0gro2ev1apyhwk", "original": "https://cloud.google.com/…"}, "publishedAt": "2026-07-30T16:00:00.000Z", "category": "ai-products", "source_url": "https://cloud.google.com/…", "aihot_permalink": "https://aihot.virxact.com/items/cms7q9upv0q0gro2ev1apyhwk", "query_origin": "items:all:q=智能体安全"}`

### 3. super_writer 如何消费

- 上游输入(execmodel `UPSTREAM_INPUTS`):`aihot/deduplicated_items.json` + `aihot/raw_items.json` + `aihot/fetch_log.json`;契约 `contracts/02_super_writer.yaml` `inputs.required=[deduplicated_items.json]`。
- super_writer 为 agent 阶段;官方校验器:`material_ingestion.py`(material-ledger 与材料一致性)、`validate_article_length.py`(full-mode)、`validate_semantic_map.py`。
- 字段进入文章的路径:agent 读取 dedup 条目 → `material-ledger.yaml`(每条 `id/title/source_url/source_name/event_id/status`,实测样例)→ 证据地图/核心卡 → `article.md`。`title`/`summary` 是正文事实来源;`links`/`source_url` 是来源标注(media 阶段追溯);数字/日期进入证据链。
- 源码片段放置建议:**`summary` 字段**(自由文本,可逐字承载命令/代码原文),并保证 material-ledger 对应条目与 `canonical_claim_registry.json` 一致。

### 4. fidelity_guard 的比对基准(关键)

- 调用点:`wxgzh_pipeline/producers.py` `_agent_validator_args` **L156-159**:
  `("zh-human-writing", "scripts/fidelity_guard.py", ["--original", str(rd/"super_writer"/"article.md"), "--edited", str(sd/"final_article.md")])`
- 结论:**要让某个数字或命令字符串通过 guard,它必须出现在 `super_writer/article.md`(original)中,并原样保留在 `zh_human_writing/final_article.md`(edited)中**。材料文件(deduplicated_items 等)不是比对基准。
- 方向性(fidelity_guard.py,安装侧 `scripts/fidelity_guard.py`):数字 `compare_numbers` L135-183 **双向**(终稿新增数字也 FAIL);日期/URL/代码块+行内代码/命令/路径**单向**(原文有而终稿缺失才 FAIL,终稿新增不 FAIL)。
- 命令提取口径 `extract_commands` L69-83:`$`/`>` 开头行 + `npm|pip|docker|git|kubectl|python|node` 前缀。**裸字符串(如 `rm -rf /`)不在任何提取器内**;要受确定性保护需写成 `$ rm -rf /`(命令)或行内代码 `` `rm -rf /` ``(行内代码,单向)。

### 5. deny 字符串 + CHANGELOG 事实逐字入文的可行性

**有可行路径,但非正式支持**(事件 RUN 20260801T231452 已实证同一路径,且因此被定性为失控 RUN)。步骤(精确到文件):

1. 用户明确指示「跳过 AI HOT 抓取,使用自有素材」——这是唯一的授权依据(aihot skill 边界被绕过,需用户显式要求)。
2. 在 `run_dir/aihot/` 手写三文件:
   - `deduplicated_items.json`:每条 `{id, title, summary(逐字放 deny 字符串/CHANGELOG 事实), source.name, links.original, source_url, aihot_permalink(指向真实仓库文件 URL 或素材页), material_id}`;
   - `raw_items.json` 与 `fetch_log.json` 同步落盘,`fetch_log` 如实写 `mode=user_materials_override`、`aihot_api_skipped=true`、来源与哈希(receipt 绑定三文件哈希)。
3. super_writer 阶段:agent 据材料写 `article.md`,deny 字符串与 CHANGELOG 事实**逐字**进入正文(建议命令写成 `$ cmd` 或行内代码以进入 guard 单向校验);`material-ledger.yaml`/`canonical_claim_registry.json` 同步一致。
4. zh_human_writing 阶段:只做文字润色,所有数字/日期/URL/代码/命令/路径/引号保留;`fidelity_guard --original article.md --edited final_article.md` 通过。
5. media 批准点照常人工批准后继续。

**缺口与代价(如实,不夸大)**:
- 无正式注入入口(live 模式没有 --items-file/--source/等);依赖 agent 手写材料文件,违反 aihot skill「只向 aihot.virxact.com 匿名只读请求」边界。
- zh_human_writing 禁词表(`stages/zh_human_writing.py` `_FORBIDDEN_TERMS`:`本次抓取/这次检索/输入材料/素材库/Material/Claim/Validator/Agent/流水线/系统没有找到/根据提供的材料`)可能与逐字引用冲突(例如原文含「Agent」字样)。
- media 阶段抓取仓库文件 URL 无图 → 走图表生成路径(known_allowed,档 35/36 已定性为失控通道);`body_images_min` 默认 6。
- gzh_design 渲染器无代码块能力(问题 B),命令示例只能以纯文本/行内代码呈现。
- 事件 RUN 的教训:该路径本身可跑通,但媒体批准点与已知 known_allowed 缺口叠加后产生 12 次重复上传与未批准封面;不走该路径的正式化前,风险未消除。

## 第二 非资讯类文章的适配性评估

### 6. 设计假设

- aihot 阶段=AI 资讯聚合(中文 AI 资讯/精选/热点/日报);media-enrichment=网页素材配图;README 示例选题均为资讯类(「Claude Opus 5」)。整条流水线的默认形态是「AI 资讯长文」。
- super_writer 自身**不限于资讯**(SKILL.md:支持主题/链接/PDF/访谈稿/笔记/素材包;v0.3.2 `INPUT_MODE` 有 `direct`=少量结构清晰素材),但流水线将其绑定为 material_heavy(素材来自 aihot JSON)。
- 结论(据实):「项目升级复盘」这类自有素材文章**不在流水线设计范围内**;唯一可运行路径是绕过 aihot(事件 RUN 方式),无正式入口。super_writer 单点可支持,流水线整体不支持。

### 7. 摩擦点清单(只列举)

1. aihot 无注入入口;skill 规则仅 API;手写材料需伪造 fetch_log/raw_items 的一致性。
2. media_enrichment:仓库文件 URL 无图 → 图表路径(known_allowed 失控通道);body_images_min=6 默认值;素材 copyright_review 非标准。
3. zh_human_writing:禁词表与逐字引用冲突风险;数字双向比对(自写数字必须先入 article.md)。
4. gzh_design:无 fenced code block 渲染(复盘文常见命令示例)。
5. 无自有素材的样例/文档支持(README 全部为资讯选题示例)。

## 第三 gzh-design 升版备料

### 8. 已知待修项汇总

| 项 | 文件 / 行号 | 问题 | 影响面 |
|---|---|---|---|
| OBS-73 根治 | `scripts/render_article.py` L79-104 `parse_article` | 首 `## ` 前的第 2 段起静默丢弃;oneliner 截 40 字 | 每篇多段导语文章头部内容丢失(档 38;档 40 已加 Pipeline 守卫,根因仍在) |
| 问题 B | `scripts/render_article.py` + `scripts/generate_hammer_upgrade_samples.py`(hammer_para L753-756 仅转义) | fenced code block 不渲染(纯文本+反引号);技能库有 `code-compare`(generate_advanced_html.py L65/L221)与 common-components 代码块定义,但**锤子管线渲染器未接入** | 含代码的文章排版缺失 |
| OBS-72 | `wxgzh_pipeline/producers.py`(仓库)`_wechat()` L822-859 | 封面路径与期望 sha 硬编码为历史 A-003(`418d841f…`),批准状态从未被读取/校验(档 36 取证) | 封面可能取自未批准资产 |
| OBS-67 | `SHA256SUMS` | 6 行中 5 处失配/缺失(SKILL.md、publish_wechat_draft.py、validate_gzh_html.py、theme-hammer.md 过时;zip 条目对应文件不存在;仅 theme-index.md 匹配) | 发布物哈希清单失实 |
| 新发现(建议登记) | `README.md` / `SKILL.md` | README 未提 hammer/smartisan 主题与锁定关系;安装方法指向 `~/.reasonix` 旧仓库 `531285650/gzh-design-skill`(锁定仓库为 `Amer-CN/gzh-design-skill`);SKILL.md 宣称代码块能力但锤子管线未实现 | 建议 OBS-75(文档失实) |
| 新发现(建议登记) | `RELEASE_NOTES.md` | 宣称 19 高级组件(code-compare 等),与锤子管线实际可用组件集不一致 | 建议 OBS-76(发布说明与管线能力不一致) |

### 9. 修改范围评估

| 项 | 涉及文件 | file_count | required_files | P2 拆分冲突 |
|---|---|---|---|---|
| OBS-73 根治 | render_article.py(修改) | 不变(76) | 不变 | 无(B 类纯排版) |
| 问题 B | render_article.py + generate_hammer_upgrade_samples.py(或新增组件文件) | 只改现有文件则不变;新增文件则 76→77 | 不变 | 无(B 类) |
| OBS-72 | producers.py(仓库 P 侧 `_wechat` L822-859) | 不变 | 不变 | 无(本就在 P 侧);若改 publish_wechat_draft.py 的 `--cover` 逻辑则触及 A 类迁移对象 |
| OBS-67 | SHA256SUMS(内容更新) | 不变 | 不变 | 无 |

### 10. 升版后 relock 预演推算

- 上述任一改动落地后:gzh-design `root_sha256` 必变(内容哈希);`runtime_manifest_sha256` 不变(文件清单不变,除非问题 B 新增组件文件);`runtime_file_count` 76(或 77)。
- `required_files` 不变 → **不需要 `--allow-required-files-removal`**。
- receipt 三态:两篇归档 RUN 的 gzh_design receipt 记录 `skill_root_sha256=9a8cd7f5…`(实测 RUN1/RUN2 一致)→ 升版后当前实算 ≠ 9a8cd7f5:
  - 若先执行 `relock --apply`(生成台账记录)→ `SKILL_UPGRADED`,返回 `upgrade_entry_ids=[新记录]`(receipts.py L283-307 三态逻辑);
  - 若未重锁/台账缺失 → `TAMPERED`。
- 风险点:relock 首次真实使用若落在 gzh-design(76 文件)上;若 P2 拆分先于升版,publish_wechat_draft.py 迁出会触发 required_files 移除,届时**才需要** `--allow-required-files-removal`(顺序敏感:先升版后 P2 可避免交叉)。

## 第四 本档收尾

### 11. 零写入验证(快照比对)

本档执行前后(档 41 全程只读,除报告外)实测快照:

- 四锁实算 root:super-writer `46a00a1b…`(50)/ zh-human-writing `18491b36…`(53)/ media-enrichment `0d8aea21…`(57)/ gzh-design `9a8cd7f5…`(76)——与 lock 记录逐字一致
- 两侧 skills.lock.json sha256 均 `a9e07ef4…`(小写),逐字一致
- `skills.lock.history.json`(台账)两侧均不存在
- 证据目录均在:bundle-staging-37 / bundle-staging-40 / `.temp\obs62s-build-staging` / `F:\AIXM\wxgzh-incident-20260802`
- 仓库 git 工作树除本报告外无任何改动

验证方式:同一 `compute_root_sha`(仓库自带)在档初/档末各跑一次比对;lock 用字节 sha256;台账与证据目录用存在性检查。
