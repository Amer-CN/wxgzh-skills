# 档 64 — 素材注入正门(自有素材,路径 a:只动 Pipeline 侧)

- 日期:2026-08-04
- 性质:功能档。**路径 a(不动被锁 skill、不 relock)**:注入点落在 Pipeline 侧
  aihot 阶段(agent 驱动阶段的前置写入),产物与 aihot 正常输出同构,下游
  (registry/super_writer/media)零改动。
- 零微信调用;零草稿;档 61/62/63 语义未动;lock 与台账未变(复核项见第五步)。

---

## 第零步 归属判定:路径 a(Pipeline 侧)

1. 自有素材注入 = 在 aihot 阶段用用户提供的 items 替代「AI HOT 检索结果」。
   - aihot 阶段是 `agent_invoked_skill`,执行入口在 Pipeline 侧 `producers._agent`
     (握手契约:raw_items/deduplicated_items/fetch_log 三文件);
   - super_writer 消费的是 `deduplicated_items.json`(契约 02_super_writer),其
     `material_ingestion.py` 输入契约**无需改动**——只要注入产物与 aihot 输出同构;
   - 结论:**a 可行**。注入由 Pipeline 代码执行(schema 校验 + 来源留痕 + 注入标记),
     agent 只核验后 ACK;super_writer 侧零改动、零 relock。

## 第一步 取证

2. **user_materials_override 现有实现(非代码通道)**:全仓检索无任何
   `user_materials_override` 消费代码——它是 **agent 手写三文件的非正式路径**
   (事件 RUN 20260801T231452 实证:fetch_log.mode=user_materials_override、
   aihot_api_skipped=true、18 条用户素材)。档 41 调查定性:live 模式无正式入口,
   agent 手写即可绕过 aihot skill 边界;事件 RUN 因「手写 + 未停下人工批准 +
   图表 known_allowed 硬编码」叠加被定性为 UNCONTROLLED(档 63 已修复图表路径)。
   **关闭方式(代码强制)**:`stages/aihot.py content_validate` 对
   `mode=user_materials_override` 一律 FAIL_CLOSED——旧通道从规则约束变为
   代码拦截。
3. **aihot 正常路径 items 结构**(档 41 实测 + 消费方读取):必填
   `id/title/source.name/links.original/links.aihot/source_url/aihot_permalink`,
   可选 `summary/originalTitle/publishedAt/category/score/selected/attribution` 等;
   消费方:`producers._dedup_index`(id/source_url/aihot_permalink/title/summary)、
   `_build_media_request`(material_id 分配、aihot_permalink 一致性 FAIL_CLOSED)。
   正门注入 items 采用**同一字段集 + 注入专用必填扩展** `source_provenance`
   (source_type/original_ref/content_sha256)——同一份数据、一个入口,不是第二套口径。

## 第二步 实施(Pipeline 侧)

4. **正式 `--items-file` 注入入口**:
   - `wxgzh_pipeline/material_injection.py`(新增):
     - `validate_items`:与 aihot 产出同构的必填字段 + `source_provenance`
       必填(来源类型 ∈ local_file/repo_path/url、原始标识、64-hex 内容 sha256),
       缺任一 FAIL_CLOSED;
     - `write_injected_aihot`:写三文件(同构)+ 冻结输入副本
       `aihot/items_file.injected.json`(审计留档);
     - `build_fetch_log`:注入块(items_file 路径/sha256/item_count/逐条 provenance),
       `mode=items_file_injection`、`aihot_api_skipped=true`、reason 写明
       「自有素材注入,不伪装为检索结果」。
   - `wxgzh_pipeline/orchestrator.py`:`run(..., items_file=None, stop_after=None)`,
     `resume(..., stop_after=None)`;`_drive` 支持受控停止(冒烟用,停在指定阶段后,
     状态 STOPPED_AFTER,不执行后续阶段)。
   - `wxgzh_pipeline/producers.py` `_agent`:aihot 阶段若有 items_file,由
     Pipeline 代码先写三文件,agent 指令改为「禁止调用 AI HOT API;核验三文件后
     ACK」;**resume 幂等**(已注入则不再重写,避免 fetch_log 时间戳破坏握手
     token);meta 显式标记 `material_injection`。
   - `wxgzh_pipeline/stages/aihot.py`:
     - `content_validate`:`mode=user_materials_override` → FAIL(旧通道关闭);
       `mode=items_file_injection` → 校验注入块一致性(数量/ID 与 dedup 对齐),
       报告 `AIHOT: PASS(INJECTED)`;
     - `side_effects`:注入路径声明 `{"type": "none", "detail": "自有素材注入,
       无 AI HOT API 调用"}`(receipt 不谎报网络读取)。
5. **★关闭 user_materials_override(同一档完成)**:旧 mode 在 content_validate
   硬 FAIL——「每关掉一条非正式通道,同时开一扇正门」的两件事在同一档完成,
   无并行可用通道。
6. **OBS-27(检索合同缺失)说明**:指令所称 OBS-27 在仓库无登记文本(与 OBS-29
   同况,据实记录)。按描述理解:正常路径有「检索动作 + fetch_log 记录」合同;
   注入路径**不执行检索**,检索合同语义不适用——由注入证据链替代:
   `fetch_log.mode=items_file_injection` + 注入块(输入文件 sha、逐条来源与内容
   sha)+ `items_file.injected.json` 冻结副本,全部经 contract 哈希绑定(receipt
   可追溯)。注入不绕过任何既有校验(保真、批准、媒体门槛均在下游原样生效)。

## 第三步 测试(9 项全过)

`tests/test_obs64_material_injection.py` + `tests/fixtures/obs64/`(冻结夹具):
- schema 合规通过 / 缺必填字段 FAIL_CLOSED;
- ★反向验证:缺 `source_provenance` 的 items 文件必须被拦下(夹具
  `items.missing_provenance.json`);
- 来源类型非法 / content_sha256 非 64-hex → FAIL_CLOSED;
- 三文件写入 + fetch_log 注入块与逐条 provenance + 冻结副本;
- content_validate:注入一致 → `PASS(INJECTED)`;数量/ID 篡改 → FAIL;
- **user_materials_override → FAIL_CLOSED(旧通道关闭)**;items 文件缺失 → FAIL。

## 第四步 冒烟(vibe-coding-guide 四素材,不发布)

10-11. **素材坐标验证**:经 GitHub contents API 核对 git blob sha 逐字匹配
      (hooks/_common.sh `7389e5363cba` / hooks/guard-bash.sh `f5571b3c2aaa` /
      CHANGELOG.md `50e0ac5398d5` / install.sh `327261f46514`,main `8260988b`);
      内容 sha256 逐一记录进 provenance。
- **注入后的 items 清单**(4 条):user-material-01..04(路径/标题/来源
  repo_path/original_ref `Amer-CN/vibe-coding-guide@8260988b:<path>`/
  content_sha256 完整);
- **来源留痕**:fetch_log 注入块 + 逐条 provenance + `items_file.injected.json`
  冻结副本;aihot receipt `side_effects=[{"type": "none", "detail": "自有素材注入,
  无 AI HOT API 调用"}]`;
- **super_writer 产出状态**:真实文章《护栏从「自觉」到「硬拦」:vibe-coding-guide
  v2.1 补上的两条铁律》(3839 可见字符,medium 区间内),13 个契约产出全部落盘,
  **三个官方校验器全部 exit_code=0**(material_ingestion / validate_article_length
  full-mode / validate_semantic_map),receipt 哈希绑定;zh_human_writing 仅生成
  stage_request(受控停止,零产物、零微信、零草稿)。
- RUN_ID:`20260804T163519-vibe-coding-guide-v2-1-6-7atsk0`(live 模式;
  `stop_after="super_writer"`;resume 后按受控停止处理,未履行后续阶段)。
- 12. 冒烟未暴露需要停机的问题(过程中发现并修复的均为本档新代码自身的
      幂等/停止语义缺陷:resume 注入重写破坏握手 token → 幂等化;resume 未透传
      stop_after → 已补;均属实施缺陷,当场修复后重验)。

## 第五步 复核(路径 a)

- 13. `upgrade_regression.py` **ALL PASS**(排除清单仍 1 项,cross-side 仍 SKIP);
      四锁 relock dry-run 全部无变化。
- 14. 路径 a 复核项:**lock 双侧未变**
      (`81F9342A617893FBE3C51C4FCDCFFCB89E76D43EE4735F5FDB81B6422B951058`,
      与档 63 结束时一致);**台账仍 7 条**(未新增);四锁 hash_ok 全 true;
      doctor PASS;安装侧经正式安装器同步后与 repo HEAD 逐字一致
      (OBS_68:623/623,0 差异)。
- 15. 副作用总账:与档 59 终稿一致(草稿箱 2 / uploadimg 22 / add_material 4 /
      发布 0);本档零微信调用(冒烟只到 super_writer,未触达微信链路)。

## 变更文件(wxgzh-pipeline 仓,`dev/0.1.0-dev2`)

- `wxgzh_pipeline/material_injection.py`(新增):注入正门(schema/留痕/注入标记)
- `wxgzh_pipeline/stages/aihot.py`:旧通道 FAIL_CLOSED + 注入一致性校验 + 副作用如实声明
- `wxgzh_pipeline/producers.py`:`_agent` 注入分支(resume 幂等)+ meta 注入标记
- `wxgzh_pipeline/orchestrator.py`:`run/resume` 支持 `items_file`/`stop_after`
- `wxgzh_pipeline/state.py`:`items_file` 字段
- `tests/test_obs64_material_injection.py`(新增,9 项)+ `tests/fixtures/obs64/`(冻结夹具)
- 本报告
