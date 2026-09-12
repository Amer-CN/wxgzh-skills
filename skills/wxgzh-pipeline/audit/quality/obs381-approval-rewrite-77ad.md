# OBS-381 —— 77AD 审批台账机械回写封堵验收报告（字节级落盘）

- 档号：77AD（审批台账机械回写封堵 + 77Y 手填穿透堵漏 + 手填行为留痕）。
- 授权：RELOCK_ALLOWED 临时 0→1（批准人=用户，范围=media-enrichment + wxgzh-pipeline；GZH 维持 0）。授权登记行随 feat 落账（序数按台账实况=五十一次，77AC 已占五十）。
- 背景证据：RUN 14j153（20260912T022502-iphone-duo-14j153）copyright_approval.json 23 条 basis=USER_BLANKET_APPROVAL=True vs 04 合同现值 false；manifest.reasons 23 条机械值 False + 23 条 regenerated 标记；执行端手填进 continuation 请求 asset_approvals[].basis 并写入落账文件。
- feat 提交：7b6b47b（18 文件）。

## 1. 任务 0 证据（只读贴回存档）

- `_mechanical_basis` 落点：`run_media_enrichment.py:1324-1338` 只追加 `asset.reasons`（含 `basis regenerated mechanically (77Y/OBS-366)`）；`manifest_builder.py:44/104` 有 reasons 字段并输出，无 basis 字段（`54-58` 只有 approval_id/scope/by/at/evidence）。
- 写入方钉死：生产代码唯一写点=`producers.py:1359-1376`（`_write_zero_image_fallback_approval`，仅零图空合同）；其余只有 `_load_copyright_approvals` 读取消费（`producers.py:576-634`）；全仓写该文件的生产命中只有测试夹具。结论：非零图文件系执行端手写。
- 消费点：`producers.py:929-940` 把 `_load` 读到的 `basis` 条件透传进 `media_continuation_request.json`，无机械刷新；`1490-1514` 缺文件等待批准、存在则读取消费。
- 14j153 复核：落账/请求各 23 条 basis=True 逐字一致；合同 `04_media_enrichment.yaml:12` 现值 false；manifest 双份各 23 条机械 False + 23 条 regenerated 标记。

## 2. 实现（任务 1–2，全部落在 media-enrichment 内）

- `MECHANICAL_BASIS_PROVENANCE` 常量（`orchestrator_mechanical_rewrite (77AD/OBS-381)`）。
- `_approval_lane_error` 加伪造机械标记拒收（标记在但值非机械=伪造；缺标记手填走回写 heal，不拒）。
- `_rewrite_approval_basis_file`：落账文件指定 auto_* 记录 basis 回写机械值+打标记，只动两键；缺失/损坏/无记录返回 False。
- continue 机械块：机械 None→记账 error+摘除消费+跳过上传（77W fail-fast，不落账）；手填≠机械→计数+1、reasons 留痕、落账文件同值回写（文件缺失跳过；存在但回写失败→error+摘除+跳过）。
- `hand_filled_basis_ignored` 循环后进 manifest `warnings`（体检可见）。
- 取舍如实记：pipeline 侧 `_load/_build` 宽松语义不动（旧测试面大）；回写点选在已算出机械值的 media continue 内（编排器调用的子进程，确定性机械动作），避免在 pipeline 侧复制整套合同/readiness/分类器上下文。

## 3. 测试实测

- 新增 `tests/test_hf77ad_basis_rewrite.py` 4 绿（进程内跑真 main()，零网络零子进程）：14j153 形状重放 2 条 True→全机械 False+标记/warnings 计数=2/exit 0；伪造标记拒收（exit 1，落账不动）；approvable=false 时 error+fail-fast（落账保持 True，exit 1）；helper 边界（缺失/损坏/无记录 False，正常只动两键）。
- media 全套：372 passed / 7 skipped / 0 failed（基线 368 + 新增 4，零新红）。
- pipeline `test_hf76r.py` 19 绿（含 obs304 钉子 263/119–381 与 obs288 白名单——本档未加指令规则，白名单零改动）。

## 4. 升版/锁链/回归（77Y-F 新规：回归在 relock 后）

- 升版：media dev34→**dev35**（77J 全站同步 12 文件集+CHANGELOG）；pipeline 9R31→**9R32**（release_date 2026-09-12）；根 README 版本表同步（含 77AC 欠账 sw rc3）。
- relock **#113**（media dev35：`relock-media-enrichment-20260912T095253Z-477cfc2a`，远端见证→apply 全链 PASS，备份在册）；锁 sha `4b86e2e4…→5256ec28cd08a6440afa6e9d234effdbef112eb111d94333bfe25f42a05af580`，R93 双侧一致。
- doctor：双侧 PASS、OBS_69/OBS_68 双侧 MATCH。
- 最终回归（relock 后）：见 §6（`F:\AIXM\wxgzh\.temp\upgrade_regression_77ad.log`）。

## 5. 程序校验

- 唯一编号：`263 119 381 True`
- R59：`main=21 partition_active=21` 双差集空
- 授权登记行：恰 1 行（五十一次）

## 6. 基线链

`bbe4c2b（77AC-F）→ 7b6b47b（feat 77AD，含授权登记行+obs304/obs288/README 随档）→ <docs 本报告+锁链>`

## 7. 执行过程如实记

- executor 通道：子智能体因文件沙箱（工作区仅 `F:\AIXM\wxgzh`）零改动停机上报，主智能体收回直接执行；后沙箱策略放开（danger-full-access），后续编辑直写。
- 本会话管道捕获曾报 WinError 5（子进程命名管道受限），纯函数/文件 IO 测试与进程内 main() 重放不受影响；relock entrypoint smoke（含子进程）PASS。
