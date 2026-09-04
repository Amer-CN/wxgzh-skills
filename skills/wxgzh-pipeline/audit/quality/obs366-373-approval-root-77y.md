# OBS-366..373 —— 77Y 审批域根治八项验收报告（字节级落盘）

- 档号：77Y（审批域根治：auto_rule 合法化 + basis 机械生成 + 圆形证据封堵 + OBS-246 激励修复 + 续发显式 RUN_ID + align 修理 + version_check 留痕 + aihot 合成自检）。
- 授权：RELOCK_ALLOWED 临时 0→1（批准人=用户，范围=media-enrichment+wxgzh-pipeline+super-writer——align 脚本触 sw 锁条目）；GZH_DESIGN_WRITE_ALLOWED 维持 0。授权登记行随 feat 落账。
- 用户裁决（2026-09-05）：auto_rule 车道合法化；人工终审点=用户草稿箱发布动作；basis 禁手填；pipeline 自产工件不构成 user 证据。
- feat 提交：38b0176（35 文件：30 改+4 新增测试+obs304 随档）。

## 1. 任务 0 坐实证据（只读，存档）

- basis 生成链：0srcql 12 条 auto_rule 手填 basis 引用死条款 `USER_BLANKET_APPROVAL=true`（04 合同 77W 后现值 false）完整原文在案；recorder :205 只校验非空。
- 76R live 交互：机器车道 `network_mode != "live"` 双门（:364/:1151）；live 代批实际通道=agent 手写 copyright_approval.json（:1105 消费）——「live 结构性不可能」结论作废更正（机器车道非 live 门仍在）。
- OBS-246：unbacked 守卫（:352-360）只认批准依据，rejected 无正名——激励倒置（A-021「避免整批清零」自述）。
- 续发：`_find_resume_run` newest-first 取 candidates[0]，零会话归属过滤。
- align：`:184` 原始字符口径 + 导语区不入任何 section。
- 圆形证据：`_user_action_evidence` 末行自产 sha 即过；0rcwre 18 条 user + user_images=0 全走此通道。
- version_check current 静默 null（0srcql/0rcwre 实测 null 与未跑不可辨）；nlmrly 合成条目 original=aihot story 页冒充。

## 2. 八项实现摘要（OBS-366..373）

| OBS | 项 | 实现 |
|---|---|---|
| 366 | basis 机械生成 | `_mechanical_basis`（04 合同 yaml 实时值+readiness+分类器终值+域名排除）；手填 basis 一律忽略以机械值入账（reasons 留「basis regenerated mechanically」）；测试 +3 |
| 367 | auto_rule 合法化 | SKILL.md 边界改写（条件三要素+终审点=发布键）/04 合同 PER_IMAGE_MANUAL_REVIEW_REQUIRED true→false（注释注明裁决）/producers 立规+76R 更正/守卫测试同步 |
| 368 | OBS-246 激励修复 | rejected_with_reason 一等公民（合同键+unbacked 文案指路+rejected 无理由=error）；测试 +2（部分拒部分批过/存活未处置仍拒） |
| 369 | 续发显式 RUN_ID | cli 多候选→MULTIPLE_CANDIDATE_RUNS 停机列全（77Y/OBS-369 hint）；单候选保持自动续；测试 +2 |
| 370 | align 修理 | count_visible_chars 单一真源（import）+「（导语）」节纳入；0srcql 冻结数据干跑与手算逐节一致（±2 容差，导语 456/454）；测试 +2 |
| 371 | 圆形证据封堵 | `_user_action_evidence` 删自产 sha 分支；合法证据=user_images 或 user_action 三要素；producers 白名单透传 user_action（真实链可达，裁决 3 补）；测试 +2+1 |
| 372 | version_check 留痕 | current 也返回 trace，run() 恒写 st.version_check；测试 +1 |
| 373 | aihot 合成自检 | producers `_aihot_synthetic_original_check` ACK 前挂点：非 cm 前缀条目 original 不得冒充 aihot 站内页、supplemental 按 77X 允许 null；违者 StageError 停机；测试 +1 |

## 3. 测试实测

- media：361 passed / 0 failed / 7 skipped（新增 5 绿+4 夹具文件 user_action 同步语义不变）。
- sw：291 passed / 1 failed（既有 dist 环境红）/ 2 skipped。
- pipeline：612 tests = 580 passed / 10 failed / 22 skipped——7 基线环境红 + 2 新暴露既有红（见 §4）+ 1 obs304（随档 255 转绿后 upgrade_regression 实证）。

## 4. 两颗新暴露既有红——worktree 仲裁（重点报告项）

`test_77v_version_check_current` 与 `test_hf76e_request::test_supplemental_material_accepted` 在 executor 全套报告为红，executor 声称「基线 ebd459a 同红」。**主智能体以独立 worktree 在干净 ebd459a 上实测：两颗同败**（仲裁原文在案）。定性：

1. `test_77v_version_check_current`：硬编码 `baseline_date == "2026-09-02"`——77X relock #105（recorded_at 2026-09-03）后过期；77X 时 upgrade_regression 在 relock 前跑故未暴露，**77X 遗留潜伏红**。
2. `test_supplemental_material_accepted`：夹具 supplemental 材料 permalink=official.example.com——77X input_contract Step 3f（OBS-364 非法分流）生效后应拒；**77X 遗留潜伏红**（夹具未随 77X 语义更新）。

两颗均**非 77Y diff 引入**（worktree 实证），按「既有红不顺手修」纪律未动，留审核方裁决（77Y-F 或单开微档授权修复：前者改读 history 动态断言，后者夹具改 null/aihot 前缀）。

## 5. relock 与锁链

- sw #106：`relock-super-writer-20260904T193929Z-6c7c119d`（0.4.18-rc1→0.4.19-rc1，root/validator 变）。
- media #107：`relock-media-enrichment-20260904T193951Z-d9e778a9`（dev32→dev33）。
- 两 apply 全链 PASS（doctor gate/备份×2/installer/post doctor/entrypoint smoke）；远端见证 a/b/c PASS（--source-commit 38b0176）。
- 新锁 sha：`916422e9379a2f370e996209ca6a3d62b83194d059e91529b6d112de0534f8f6`（旧 9e45a0ea…）；R93 双侧同步。
- pipeline 9R29 无锁条目，触及面 cp 同步装机侧（三技能全同步）。
- doctor：双侧 PASS、OBS_69/OBS_68 MATCH（diff []）。
- upgrade_regression：**obs154×1 既有红 + hf77v current 新暴露既有红（§4，worktree 仲裁非本档引入）**；relock dry-run ×4「无变化 OK」；obs304 随档 255 实证绿。

## 6. 程序校验

- 唯一编号：`255 119 373 True`
- R59：`main=21 partition_active=21` 双差集空
- 授权登记行：恰 1 行

## 7. 基线链

`ebd459a（77X-F）→ 38b0176（feat 77Y，含授权登记行+obs304 随档 255）→ <docs 本报告+锁链>`

## 8. 干跑验收实证（档文任务 9 要求原文，executor 报告在案）

- basis 随合同值变化：mock 改合同值→basis 随变、断言不含旧值（死条款不可能测试）。
- 0srcql 式手填死条款 basis：E2E continue 链 manifest reasons 落「basis regenerated mechanically (77Y/OBS-366)」+实时合同值，exit 0。
- 圆形证据被拒：仅自产 sha 的 user → error 含 77Y/OBS-371 指路。
- rejected 处置过闸：3 资产 1 批 2 拒带理由 → 无 FAIL。
- 歧义续发停机：两候选 → MULTIPLE_CANDIDATE_RUNS return 1、resume 未被调用。
- align 0srcql 重算：导语 456/454、发布 563/563、跑分 642/642、智能体 643/643、定价 426≈425、保留 307/307、接下来 264≈263，total=3300=target。
- version_check current 落 state：`test_77y_version_check_current_recorded_in_state` 绿。
