# OBS-357/358/359 —— 77W 审批记录名实修复+规则冲突单源化+supplemental 通道验收报告（字节级落盘）

- 档号：77W（审批记录名实修复 + 规则冲突单源化 + supplemental permalink 通道）。
- 授权：RELOCK_ALLOWED 临时 0→1（批准人=用户，范围=media-enrichment+wxgzh-pipeline）；GZH_DESIGN_WRITE_ALLOWED 维持 0。**授权登记行随 feat 提交落账（77U-F 首咬新规首次执行）**。
- 背景纪律事件：gy7usp→srddqe 体检执行端主动披露——copyright_approval.json 七条 approved_by=user 系手填、用户未看图；04 合同 USER_BLANKET_APPROVAL=true 与 media SKILL.md 边界冲突、执行端自裁未停机。审核方裁决：SKILL.md 为现行有效规则，合同对齐收编；自动批唯一合法记录=approved_by=auto_rule/auto_approve+依据；user 仅限真实用户动作证据；规则冲突一律停机上报。披露文化定性=名实不符+冲突自裁，处置=修复向前生效+本篇用户追溯审图。
- feat 提交：684eb87（25 文件：23 改+2 新增）。

## 1. 任务 0 证据（只读贴回存档）

- recorder 真身：copyright_approval.json 无生成代码（全仓 grep 仅 obs71 夹具命中），agent 阶段手写；run_media_enrichment.py:1105 仅搬运 approved_by。srddqe 实测 7 条 approved_by='user' 无用户证据；user_images 通道（:308/:470）存在未用。
- schema 现状：approved_by 仅 minLength:1（:177）。
- 04 合同：USER_BLANKET_APPROVAL=true / PER_IMAGE_MANUAL_REVIEW_REQUIRED=false 与 SKILL.md「必须人工：图片审批（默认道）」冲突；audit/incident 实证 USER_BLANKET_APPROVAL 为死配置（无消费代码）。
- 76R 先例：run_media_enrichment.py:343-348/1154-1159 approved_by="auto_approve"+scope="auto"+reasons 依据——枚举设计锚。
- supplemental 构造填充实证：srddqe dedup 池 `supp-hf-blog-index` 的 aihot_permalink=https://huggingface.co/blog（外站），schema materials 节 aihot_permalink 仅 uri 类型无 null 通道。

## 2. 实现（规格 A–F）

- **A（OBS-357 schema）**：approved_by 改三值枚举 `["user","auto_rule","auto_approve"]`（auto_approve=76R 遗留值）+同级 basis 字段（auto_* 必填依据=合同/规则条号）。jsonschema 实测枚举外值报错原文：`'real-user' is not one of ['user', 'auto_rule', 'auto_approve'] (path: asset_approvals/0/approved_by)`。
- **B（OBS-357 recorder）**：run_media_enrichment.py 新增 `_approval_lane_error`/`_user_action_evidence` 助手，single_asset 搬运块前 fail-fast——枚举外拒/auto_* 缺 basis 拒/user 车道需用户动作证据（user_images 匹配或自带非空 approval_evidence_sha256 留痕；仓内无 sha→文件路径既有约定，按此口径实现并登记）。测试 +3（test_hf77w_approval_lane.py）。
- **C（OBS-358 单源化）**：04 合同六键改值（USER_BLANKET_APPROVAL=false、PER_IMAGE_MANUAL_REVIEW_REQUIRED=true）+ SINGLE_SOURCE_REF 指向 SKILL.md#自动决策边界；守卫测试两文一致（test_hf77w_single_source.py 3 条，含合同三键+SKILL.md 边界节+立规锚点）；producers APPROVAL_CONTRACT_RULE 追加 77W 立规「规则冲突一律停机上报审核方，禁止执行端自裁」。
- **D（OBS-359 supplemental 通道）**：materials[].aihot_permalink 类型 `["string","null"]`；validate_media_manifest.py 新增 REQUEST_MATERIAL_PERMALINK_LANE 分流——supplemental 非 null 须 aihot 前缀（构造外站填充拒），normal/缺省维持既有口径不新增门槛（如实登记：仓内既有夹具 permalink 多为 github/x.com，新增 normal 域门槛会制造大面积新红）。测试 +2（null 通过/外站拒）。
- **裁决连带**：3 个既有测试夹具车道值对齐（real-user/independent_reviewer→user，单点字面量 4 处；逐点验 18 测试受影响、其中 2 负例与车道值无关；3 文件 22 测试全绿）。
- **E 升版**：media dev30→dev31（77J 全站同步集）+CHANGELOG；pipeline hotfix9R26→9R27。
- **F 台账**：OBS-357/358/359 落账+口径 89+授权登记行（随 feat）。

## 3. 测试实测

- media：361 tests / **0 failed** / 7 skipped（基线 349+新增 5+夹具对齐 16 保持绿）；3 夹具文件单独 22 passed。
- pipeline：600 tests / 8 failed（7 项基线环境红逐一相同+obs304 计数钉子，已随档 238→241 转绿）。
- test_hf77w_approval_lane 5 passed / test_hf77w_single_source 3 passed。

## 4. relock 与锁链

- dry-run：远端见证 PASS (a/b/c)；root/entrypoint/validator/full_commit/source_tree/version 全 CHANGED（dev30→dev31、commit→684eb87）。
- apply：doctor gate PASS→备份 skills.lock.20260902T204358Z.json→entry `relock-media-enrichment-20260902T204358Z-cc21e33b`→installer PASS→post doctor PASS→entrypoint smoke PASS。
- 新锁 sha：`aa821744514b9ea9fd03a95f4b20fd0731d8c74e18ec8497337b2680a79dcfa1`（旧 217a5c37…）；R93 双侧同步（observability.py 一行）。
- pipeline 无锁条目：VERSION 9R27+文件 cp 同步装机侧（producers/contract/SKILL/ledger/测试/version_check 等触及面全同步）。
- doctor：源码侧 PASS（OBS_69 MATCH/OBS_68 MATCH）；装机侧 PASS（OBS_69 MATCH/OBS_68 MATCH）。
- upgrade_regression：唯一红 obs154×1（既有在册）；relock dry-run ×4「无变化 OK」。

## 5. 程序校验

- 唯一编号：`241 119 359 True`
- R59：`main=21 partition_active=21` 双差集空
- 授权登记行：grep 恰 1 行（ledger :551）

## 6. 基线链

`68e15a6（口径 88）→ 684eb87（feat 77W，含授权登记行+obs304 随档 241）→ <docs 本报告+锁链>`

## 7. 留给后续档的已知项

- producers `_STABLE_SINGLE_ASSET_FIELDS` 未含 basis 透传（media_request 层面 basis 流转，第二档裁决）。
- input_contract.py 未加 supplemental 分流（不在 77J 同步集授权，validator 分流已覆盖）。
- pipeline VERSION release_date: 2026-07-30 陈旧（历史惯例维持现状）。
