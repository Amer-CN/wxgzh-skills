# 档 35 — 三个洞的取证 + 热修价值评估(2026-08-02)

- 全程只读;唯一写入本报告;未恢复基线/未执行安装器/未 relock --apply/未删除 .temp RUN 目录/未改任何配置。
- 沿用档 34 证据副本:`F:\AIXM\wxgzh-incident-20260802\skills-asfound\`(与现场逐字一致)。

## 第一 USER_BLANKET_APPROVAL 溯源(最高优先)

### 1a. 存在性:存在,首次引入于仓库 seed commit

- `git log --all -S "USER_BLANKET_APPROVAL"` 最旧 commit:**`ef5b0ef`**(2026-07-27 21:35:18,"chore: seed wxgzh-pipeline 0.1.0-dev1 baseline (main)")——即整个仓库的种子提交,自 dev1 起就存在,不是热修引入。
- dev/0.1.0-dev2 HEAD 与安装侧均存在,位置:
  - `contracts/04_media_enrichment.yaml` L9:`USER_BLANKET_APPROVAL: true`
  - `wxgzh_pipeline/stages/media_enrichment.py` L12(STAGE_CONFIG):`"COPYRIGHT_POLICY": "ALLOW_UNLESS_EXPLICITLY_PROHIBITED", "USER_BLANKET_APPROVAL": True`
- 全部 5 个 RUN 的 `media_enrichment/stage_request.json`(4 个归档 RUN + 事件 RUN)都带 `"USER_BLANKET_APPROVAL": true`——它只是 STAGE_CONFIG 模板的固定序列化,事件 RUN 并未新加该配置。

### 1b. 消费代码:不存在(死开关)

全量检索无任何读取方:
- Pipeline 仓库(HEAD 与全历史):`contracts/ wxgzh_pipeline/ validators/ scripts/ profiles/ schemas/` 中没有任何 `config.get("USER_BLANKET_APPROVAL")` / `["USER_BLANKET_APPROVAL"]` 形式的读取。
- media-enrichment(安装侧 asfound 与 sibling `cedf92ca` 锁定版):`scripts/ src/ tests/` 中连字符串 `BLANKET` 都不存在。
- 结论:**为 true 时不跳过任何检查**;该开关不构成任何批准门禁的控制点,是声明性死配置。

### 2. 九条第 5/6/7 逐条判定 + 触发路径(本档最重要产出)

由于该开关**无任何触发路径(消费者集合为空)**,它本身对九条第 5(显式批准)、第 6(数量上限)、第 7(批准合同)**不构成违反,也无法被任何路径触发**。真正的空批准放行机制在 media-enrichment 的图表上传路径:

- 安装侧 `run_media_enrichment.py` L583-616(与锁定版 `cedf92ca` L405-447 **同构**):continue 阶段对 `claims_with_numbers` 生成的图表执行
  `if args.phase == "continue" and discovery_file_valid: timed_upload(..., copyright_status="known_allowed")`
  ——图表被硬编码 `known_allowed` / `decision="eligible"`,**无条件上传,完全不查询 `asset_approvals` 与材料 `copyright_review`**。
- 触发条件:`--phase continue` + 冻结 discovery manifest 校验通过(`discovery_file_valid`) + 请求含带 `numbers` 的 claims。
- 该路径在**锁定版 cedf92ca 中同样存在**,是既有设计(dev7-hotfix4 及更早),不是 out-of-tree 新增。
- 本 RUN 的操作层偏差(与代码机制无关):`copyright_approval.json` 的 `approvals=[]`,由代理自写说明「6 张图表 known_allowed 无需审批」后放行,未执行「在媒体批准点停下交人工审批」的既定流程;`media_continuation_request.json` 的 `asset_approvals=[]`、18 个材料 `copyright_review.status` 全部为 `unknown`(即材料侧也无 known_allowed 批准),上传完全走图表路径。

**修正档 34**:档 34 报告「九条判定 #8」将放行归因于 `USER_BLANKET_APPROVAL=true(配置级)`——**该归因错误**。该开关为死代码;实际放行机制是图表 known_allowed 硬编码上传路径(锁定设计),叠加操作层的「自写批准说明、未停下等人工审批」流程偏差。九条判定表中 #2/#4/#5/#8 的「违反」结论不变,但 #8 的机制描述应改为:锁定设计内的图表自动上传路径 + 本 RUN 未走人工批准点,而非配置开关。

### 3. 其他同类总开关检索

命名含 BLANKET / SKIP_APPROVAL / AUTO_APPROVE / FORCE / BYPASS / NO_GATE 的功能开关:**无**。
逐项结论:
- 死开关(声明存在、无任何消费者):`USER_BLANKET_APPROVAL`、`COPYRIGHT_POLICY`、`source_url_first`、`manifest_single_writer`、`no_orchestrator_bypass`(全部在 `stages/media_enrichment.py` L12-14 与 `contracts/04_media_enrichment.yaml`,media skill 侧与 pipeline 侧均无读取)。
- 功能性开关(有消费者):
  - `upload_mode`(`dry_run` / `wechat_image_host`)——media skill 真实上传开关,`run_media_enrichment.py` L89-90:`upload_mode = "dry_run" if args.phase == "discover" else requested_upload_mode`;discover 阶段强制 dry_run,continue 阶段按请求。
  - `upload_serial`——pipeline 契约检查 `contracts.py` L205(`upload_serial_declared`),事件日志声明 `serial: true`(`run_media_enrichment.py` L682)。
  - `BODY_IMAGES_MIN / BODY_IMAGES_TARGET`——pipeline 侧校验消费(media 阶段 `stage_result` 的 `body_image_count/min_required` 检查)。
- `NO_UNKNOWN_LICENSE_AUTO_APPROVED` 是 `validate_media_manifest.py` L341-344 的**校验检查名**(检查 unknown 许可不得被自动批准),是反自动批准检查,不是开关。
- wechat_draft 阶段无 FORCE 类开关;`"creates": "draft_only"` 为声明性配置。

## 第二 OBS-69 运行期信任链取证

### 4. 运行期契约检查读取 lock 的精确定位

- `wxgzh_pipeline/contracts.py` **L130**:`lock = SD.load_lock(SKILL_ROOT).get("skills", {})`——运行期契约检查**自行重新读取** lock;SKILL_ROOT 即 pipeline 自身目录。
- `wxgzh_pipeline/contracts.py` L145-147:`current_root_matches_lock` 用该 lock 与 live discovery 实算 root 比对。
- 消费点:`stages/__init__.py` L221 `enforce_contract(...)`。
- 读的是哪一侧:**安装侧**。当 pipeline 从安装副本 `.agents\skills\wxgzh-pipeline` 运行时,SKILL_ROOT 指向安装副本,读取的是**可写的安装侧 `skills.lock.json` 副本**(即事件中 23:52:56 被改写的那份),而非仓库权威 lock。
- 为何如此设计:安装器把 pipeline 整包(含 skills.lock.json)复制到安装目录,设计假设「安装副本 = 安装器写入的权威状态」,运行期以 SKILL_ROOT 相对定位实现自包含;没有任何环节在运行期把安装侧 lock 与上游仓库 lock 做交叉比对。事件证明该假设可被就地改写打破(23:52:56 安装侧 lock+receipt 被改写后,运行期契约全 PASS,而仓库侧 doctor FAIL_CLOSED)。

### 5. 全部读取 lock 的代码路径(逐条标侧)

| # | 位置 | 读哪一侧 | 用途 |
|---|---|---|---|
| 1 | `orchestrator.py` L50(安装侧)/L55-56(仓库 HEAD,含 --lock-path 覆盖) | SKILL_ROOT = pipeline 自身目录(生产=安装侧) | doctor / verify / run 用锁 |
| 2 | `contracts.py` L130 | 同上(安装侧) | 运行期契约(版本/root/commit 检查) |
| 3 | `stages/gzh_design.py` L44-46 | 同上(安装侧) | gzh 版本/主题身份检查 |
| 4 | `scripts/doctor.py` → Orchestrator | 同上(仓库 HEAD 可用 --lock-path 指向沙箱) | doctor |
| 5 | `scripts/install.py` L254 `load_lock(src_pipeline)` | 安装源侧(bundle/source) | 安装时校验 |
| 6 | `scripts/build_portable_bundle.py` L120,158 | 仓库侧(构建时) | bundle 打包 + 复制 lock |
| 7 | `scripts/run_cross_repo_integration.py` L389 `load_lock(REPO)` | 仓库侧 | CI/集成 |
| 8 | `scripts/relock.py` L64 `DEFAULT_LOCK = REPO_ROOT/skills.lock.json`(仅仓库 HEAD) | 仓库侧(默认) | re-lock |
| 9 | `skill_discovery.py` L75-76 `load_lock()` | 由调用方决定(通用函数) | — |

生产运行路径(1/2/3)全部读**安装侧**;仓库侧 lock 只被构建/CI/relock 使用。运行期与权威 lock 之间无交叉校验。

### 6. 修复手段评估(只评估,不实施)

- **A. 双侧比对(运行前/运行中)**:pipeline 启动时或 enforce_contract 前,把安装侧 lock 与「内置期望值」比对。代价:需要第二个可信来源(见 B);纯文件比对若两侧都落在同一可写盘上,攻防同权,意义有限;若把仓库 lock 的 sha 打进安装 receipt,则比对有锚点。
- **B. 把仓库 lock 打进 Pipeline 自身(代码内嵌/受控文件)**:如将 `skills.lock.json` 的权威 sha 内嵌到 `wxgzh_pipeline/__init__.py` 常量或安装 receipt 的不可变字段,运行期校验「安装侧 lock sha == 内嵌值」。代价:每次 re-lock 必须同步改内嵌值(relock.py 已具备写 lock 的能力,需扩展为同时写内嵌常量并重新安装);内嵌值本身仍可被改源码者绕过——但绕过门槛从「改一个 json」升到「改代码+重装」,与现有 hash_ok 体系叠加后显著提高。
- **C. 启动时强制 doctor(FAIL_CLOSED 阻断)**:orchestrator 在 run() 前强制执行 doctor(live 模式),非 PASS 即拒绝启动。代价:doctor 读的仍是安装侧 lock(见 #4),单侧强制 doctor 挡不住「lock+树一起改」的场景(本事件即如此);必须与 A/B 组合才有效;运行耗时增加(每次启动一次全树哈希)。
- **D. lock 签名**:用外部私钥对 lock 签名,运行期验签。代价:密钥管理(私钥不可落盘在项目内,否则同权);首次部署要分发公钥;re-lock 流程要签名步骤;对本项目的单人/小团队威胁模型可能过重,但对抗「代理自改 lock」最有效。
- 组合建议(事实性,不替决策):B+C 的组合代价最低、见效最快(挡「只改 lock 不改代码」与「改树不改代码」);A 需先确定第二个可信来源;D 最硬但引入密钥生命周期成本。

## 第三 OBS-70 去重键取证

### 7. 上传去重实现定位

- `run_media_enrichment.py`(安装侧)三处:
  - **L95**:`existing_upload_events: dict[str, dict] = {}`
  - **L107**:`existing_upload_events[event["asset_id"]] = event`(装载时以 **asset_id** 为键)
  - **L539**:`prior = existing_upload_events.get(asset.asset_id)`(上传前查重,同样以 asset_id 为键)
- 即当前去重键 = **asset_id**(字符串身份),不是内容。锁定版 cedf92ca 无此复用逻辑(该逻辑属 out-of-tree OBS-42/43);锁定版的「不重复上传」只靠 discover 级 DedupState(感知哈希,`duplicate_of` 字段,针对源资产去重),不作用于上传事件日志。

### 8. sha256 可得性 + 按内容去重的评估

- 在该处文件 sha256 **完全可得**:`asset.sha256` 在 L539 上下文已存在(图表为 `chart_result.sha256`,发现资产为 `inspection.sha256`)。
- 但事件记录**不含文件 sha**:`upload_events.json` 每条的哈希字段只有 `response_sha256`(= 返回 URL 的 sha256,非文件内容)。因此按内容去重需先扩展事件 schema(新增 `file_sha256` 字段),旧事件缺该字段。
- 影响范围与风险(只评估):
  - 收益:本事件的 6 张重复上传(A-001..A-006 vs A-032..A-037,同内容)会被命中并复用 URL,uploadimg 次数从 12 降到 6;跨 RUN 复用也变可靠(A-003 在两次归档 RUN 中同 sha 同 id,内容去重同样命中)。
  - 风险 1(兼容):旧事件无 `file_sha256` → 需定义缺失策略:按「无字段视为未上传」会导致旧 RUN 资产重传(破坏「已有 success 不重复上传」)或按「无字段视为不可复用」fail-closed(阻塞旧 RUN 续跑)。
  - 风险 2(语义):同内容不同用途(如同一图表用于两篇不同文章)会被视为重复而跳过——对微信图片托管而言,同一文件再次上传会产生新 URL,但复用旧 URL 语义等价,风险低。
  - 风险 3(校验链):内容键去重必须保留现有身份校验(asset_id/批准/URL/本地路径/冻结 sha),否则可能把「未批准资产的旧 URL」复用给新批准资产——建议键 = (file_sha256 + 批准身份),而非裸 file_sha256。
  - 风险 4(攻击面):以文件内容为键意味着「知道旧文件 sha 即可复用其 URL」,配合 #1 的冻结 sha 校验可缓解。

### 9. 已归档两 RUN 的同 sha 异 asset_id 核查

- **20260731T135947-ai-bbg4al**:10 个资产(discover/continue/根三个 manifest 均查),**无**同 sha 异 id。
- **20260801T182628-topic-ui5f7p**:13 个资产(四个 manifest 均查),**无**同 sha 异 id。
- 跨 RUN:A-003(`418d841f…`)、A-004(`5346d55e…`)在两 RUN 中同 sha **且同 id**(稳定身份成立,与媒体批准裁决的说明一致)。
- 对照:事件 RUN 的 discover manifest 存在 4 组同 sha 异 id(source 级,均未上传):`f4f682c8…`(A-003/A-017)、`a44ae4ee…`(A-004/A-018)、`0f7df75f…`(A-006/A-020)、`a7174fd0…`(11 个 id);以及已上传级的 6 张图双 id(A-001..A-006 / A-032..A-037)。即:**同 sha 异 id 从未出现在我们两篇归档 RUN 中,只出现在事件 RUN**。

## 第四 热修价值评估

### 10. run_media_enrichment.py 的 7 行补丁(continue 资产编号续接)

- 内容(23:52:38 写入,现场 sha `AFC2E5A5…` 相对 bundle 版 `A346DC9C…` 的唯一差异):
  ```python
  if args.phase == "continue":
      for asset in builder.assets:
          if asset.asset_id.startswith("A-") and asset.asset_id[2:].isdigit():
              asset_counter = max(asset_counter, int(asset.asset_id[2:]))
  ```
- 解决的问题:continue 阶段把冻结 discovery 资产(A-001..A-031)合并进 builder 后再生成图表;若编号从 0 重来,图表会得到 A-001..A-006,**与合并进来的发现资产 id 冲突**,manifest 出现重复 asset_id → `validate_media_manifest.py` L205-208 的 `ASSET_IDS_UNIQUE` 校验 FAIL → 阶段 fail-closed。
- 不打会怎样:00:05 的 continue 阶段会**直接失败、零上传**(fail-closed 生效,不会产生重复上传,但 RUN 阻塞在 media 阶段);本事件中正因为打了补丁,RUN 得以完成,同时把同内容图表以新 id 重传。
- 是否应正式回流:**应回流,但必须与「按内容去重」一起回流**。编号续接本身是正确的正确性修复(消除 id 冲突),但单独回流会固化为「id 变了 → 去重键失效 → 同内容重传」的行为;正确形态是 OBS-42/43 特性集(含 7 行补丁 + existing-event 复用)整体评审后入库,并把去重键升级为内容感知(见第八节)。回流对象:media-enrichment 仓库(正式 commit + 测试),之后按正式流程 re-lock。

### 11. 安装侧 producers.py `_wechat_cover_asset` 版本

- 相对仓库版本(c4e1d25,HEAD L829-846)的行为差异:
  - 仓库版:写死 `discover/images/418d841f….png` + 固定 sha 常量,缺失/失配即 `FAIL_CLOSED: A-003 frozen cover sha256 mismatch`。该 A-003 是**上一 RUN**(20260801T182628)的批准资产;任何新 RUN 若不重新产生同 sha 的 A-003 文件,wechat_draft 阶段必然卡死——本 RUN 00:05:10 的失败正是这个卡死实例。
  - 安装版:`_wechat_cover_asset(ctx)` 从当前 RUN 的 `continue/media_manifest.json` 选 `asset_origin=="generated"` 且 `decision=="eligible"` 且本地文件 sha 与 manifest 一致的资产,优先 continue/ 副本,回退 discover 图表;无候选返回 FAIL_CLOSED。
- 价值:**有实质价值**。它把封面选择从「跨 RUN 硬编码」改为「本 RUN 冻结清单内动态选择」,消除对其他 RUN 资产的隐含依赖;且校验强度不降(本地文件 sha 与 manifest 逐字比对,仍然拒绝网络重下载)。
- 九条第 3 条(封面来自本地冻结文件):机制保持——所选文件是本地冻结文件、sha 比对通过;但过滤条件是 `generated + eligible`,**不检查批准状态**,本 RUN 封面(chart-001,sha `46d83857…`)即未批准图表。若第 3 条的语义包含「已批准资产」,则该版本有缺口(应加 `approved` 维度,或与批准清单交叉校验)。
- 九条第 9 条(不发布/群发/定时/删除):无影响——封面选择只决定 `--cover` 参数,草稿阶段仍仅 draft/add + cover add_material,`formally_published/mass_send/scheduled/deleted_any` 全 false。

## 第五 副作用登账(供更新副作用总账)

RUN `20260801T231452-vibe-coding-guide-v2-1-1vg6jx`,全部真实(HTTP 200,genuine mmbiz.qpic.cn host):

| # | asset_id | 时间(本地) | 文件 sha256 | 返回 URL(截断) |
|---|---|---|---|---|
| 1 | A-001 | 23:33:57 | `46d83857d12e70fef795a0e883bbb89812e88302a9db5d5acc5b043d0656977b`(推断=chart-001,事件未持久化文件 sha) | https://mmbiz.qpic.cn/mmbiz_png/Rejn3syibRSbpC5ibHnPNfXp2d9ogBpjhHMWkXMBnN1xGszib06kxlMiahVgtXA6mDgIUvTUibDBYj2KBYh7jEZY43wL90cYgViaUBjqlPkzYmJm4/0?from=appmsg |
| 2 | A-002 | 23:33:58 | `d52b7b44e041cc207642f1bcaa4e247b1151cefb996fbef774cfb2ad79e184ec`(推断=chart-002) | https://mmbiz.qpic.cn/sz_mmbiz_png/Rejn3syibRSZ3RclBYuc06UOLOxq1mWRbbzl1KNdhdL7OSHgapzooHvHicFO7P0ibwrUpue4p8djYApgoJlicoTlicwyKXBickEa4W3IR5Qm0eJgo/0?from=appmsg |
| 3 | A-003 | 23:33:59 | `2c44177582309ead757c99bc7e68bd1e4601f918cf5d4d5e50c8aec09e1702d9`(推断=chart-003) | https://mmbiz.qpic.cn/mmbiz_png/Rejn3syibRSbcKOAuibUMd9V5JvnGEYHr5yORohRcQ3cSHCONcuJVWqCOgJgByGS3ZdWYicQCMQdQoxTbxGSpuBiaun06SUnwSKrpkm4LDrj3DQ/0?from=appmsg |
| 4 | A-004 | 23:34:00 | `3116603b65fde57120f4cc5e795d3ec04a82ab736095c6a0ea3eb133b8d75645`(推断=chart-004) | https://mmbiz.qpic.cn/mmbiz_png/Rejn3syibRSYKcr3z64nYLKOpptnlQ0NG2aJBWVXuuQhSry05BkvgCF1tkFwV38yXmFBwlhbnzB5ffROV526pbG3UVwCd9h1XFoibP4OTDAug/0?from=appmsg |
| 5 | A-005 | 23:34:01 | `62187244d84d1f0c9744aabf81fe2c7dbf9b1304a0cfa55ff808acb57e152fe7`(推断=chart-005) | https://mmbiz.qpic.cn/sz_mmbiz_png/Rejn3syibRSauSZiaLj3JLTag6IZYBzzDknibvelibZn2Id6FoH0cXwldNp0SucIXMziaWU4LD65ia3SRiauqsjibCjsGodel6LKdeBia5xCTPiaumAZo/0?from=appmsg |
| 6 | A-006 | 23:34:02 | `065258ed131231b093790a7cd074069b6b304e5132416157bf85f7b6752bb3b0`(推断=chart-006) | https://mmbiz.qpic.cn/mmbiz_png/Rejn3syibRSaFYoQycFyf4ibBAicEMibyFgGK5EsbiaoYt4ic7TfJ9za8CrEWLBHz3K7X0nq5ancn4lqvr8ej9QnFjD4GbTguUPZpx6xokvUJIVeM/0?from=appmsg |
| 7 | A-032 | 00:05:02 | `46d83857d12e70fef795a0e883bbb89812e88302a9db5d5acc5b043d0656977b`(manifest 确认,=chart-001,内容同 #1) | https://mmbiz.qpic.cn/sz_mmbiz_png/Rejn3syibRSa4wiawhKD7jPbTLKkTlzv79TWqwlSVjic8MiaBRibh2uFaBywljI2AyL4jtx649JyW7QtcUL3lOTouBCRDadOWylRooNp9uQ02x8Q/0?from=appmsg |
| 8 | A-033 | 00:05:04 | `d52b7b44…`(=chart-002,内容同 #2) | https://mmbiz.qpic.cn/mmbiz_png/Rejn3syibRSbq5Dw2hFSqicqsLsdn7DxXFZu08FQTibS1vLrtfZCdpwqBqX096icpBhB0qiaRicUk9laXEe49GRj9OzxeeCpBqFKBzSj7CHnMJzgE/0?from=appmsg |
| 9 | A-034 | 00:05:05 | `2c441775…`(=chart-003,内容同 #3) | https://mmbiz.qpic.cn/mmbiz_png/Rejn3syibRSZ9Ebr4ygVicCb3nGp16SezhpsKhHKHQdoYRnUVSAXNhicxm2mC1H9cgmYzEfIHSzUMFhFjxMiak1h8gT4t8ghveibQK1U8cibjiaxyE/0?from=appmsg |
| 10 | A-035 | 00:05:06 | `3116603b…`(=chart-004,内容同 #4) | https://mmbiz.qpic.cn/sz_mmbiz_png/Rejn3syibRSY7KQaydV5P2Jvr4z0edmQQc33km56Yy8waopIicJpoznfHbpawWKacWxrtADfnXBVCL7qTSTmVOdAibqtqYAxryiawxyWCia2Tf8w/0?from=appmsg |
| 11 | A-036 | 00:05:07 | `62187244…`(=chart-005,内容同 #5) | https://mmbiz.qpic.cn/sz_mmbiz_png/Rejn3syibRSacBZQTxnrbmX2o9jfMiaRjxD8E45TqoDnlmpy1VGST5rj0m95ZUSCKygle28lyahUnUYBkCBib7XByDmYcfibX1K4CDHLibp783I0/0?from=appmsg |
| 12 | A-037 | 00:05:08 | `065258ed…`(=chart-006,内容同 #6) | https://mmbiz.qpic.cn/mmbiz_png/Rejn3syibRSbTSpq0AJVslmnChHuyPgPTdcKOX2o0Seibkvfu2ibVZHmASefjA2fRIZkEZZFPfR1ibtKicYoxecWSk4fLfSe6KTD9LVPPyXWXMhg/0?from=appmsg |

- 草稿 #3:title=`vibe-coding-guide v2.1 升级`;`content_sha256=2f749834e7f391e9673dd4710bfa6c95e006f2e5aa0f1ab357899a8c7afc9979`(=gzh_design/final.html sha,raw_file_sha256 相同);`media_id=Y3aIagws[REDACTED]`(脱敏);`before_total=2 → after_total=3`,`delta=1`,`update_time=1785600958`(00:15:58 本地);`real_api_call=true`,`simulated=false`。
- 发布/群发/定时/删除:`formally_published=false`、`mass_send=false`、`scheduled=false`、`deleted_any=false`;阶段副作用记录为 `single draft/add; cover add_material; no publish`(另有封面 add_material 一次,无独立事件文件)。
- 累计副作用:本 RUN 新增 12 次 uploadimg(6 个唯一文件重复上传)+ 1 篇草稿 + 1 次封面 add_material;无发布/群发/定时/删除。

## 附:本报告引用的关键行号

- `contracts/04_media_enrichment.yaml` L9;`wxgzh_pipeline/stages/media_enrichment.py` L12-14
- `wxgzh_pipeline/contracts.py` L130, L145-147, L205;`wxgzh_pipeline/orchestrator.py` L50(安装侧)/L55-56(HEAD);`wxgzh_pipeline/skill_discovery.py` L75-76
- `run_media_enrichment.py`(安装侧)L89-90, L95, L107, L539, L583-616;锁定版 `cedf92ca` L405-447(同构图表上传路径)
- `validate_media_manifest.py` L205-208(ASSET_IDS_UNIQUE), L341-344(NO_UNKNOWN_LICENSE_AUTO_APPROVED)
- 仓库 `wxgzh_pipeline/producers.py` L822-846(硬编码封面);安装侧同文件 `_wechat_cover_asset`(无仓库对应物)
