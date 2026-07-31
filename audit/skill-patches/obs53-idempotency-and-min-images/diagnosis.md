# OBS-53 Idempotency and Minimum Images Diagnosis

## A-1
`wxgzh_pipeline/contracts.py:168-177`读取合同`counts.BODY_IMAGES_MIN`，默认6；`stages/media_enrichment.py:11-15`定义STAGE_CONFIG，但合同执行来自`contracts/04_media_enrichment.yaml`。

## A-2/A-3
`validators/validate_media_bindings.py:13,29-66`原先判定`count >= MIN_BODY_IMAGES`；stage入口`stages/media_enrichment.py:39-62`加载validator并调用`validate`。现支持显式`body_images_min`，默认6、下限1、报告值和来源。stage读取`validation_config.json`，缺失回落6；contracts仅BODY_IMAGES_MIN读取同一文件，其他校验不变。

## A-4
`orchestrator.py:158-195`恢复时验证已完成回执；随后`_drive:199-224`对未完成阶段调用`execute_stage`，原无media复验免上传分支。

## A-5
修复前continue只写upload_events；上传前不读既有事件。现continue先读同目录事件，只有合法success+url复用。

## 幂等行为
既有success资产先完成冻结SHA、批准、稳定身份、URL安全等校验；校验通过才生成`skipped_already_uploaded`并复用URL，不调用uploadimg。原success事件保留，合同仍以success证明历史上传；skip事件不参与HTTP重叠判断。failed事件不复用。
