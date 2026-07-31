# OBS-44 / OBS-46 Diagnosis and Reviewer Questions

## A1 — material级路径是否原有

是，改前已存在。档16前物证`media-enrichment-pre-obs42-20260731/scripts/run_media_enrichment.py`第381-399行明确说明：material/source_url批准由`material.copyright_review.status=known_allowed`表示，无需per-asset approval；后续只检查`asset.copyright_status == known_allowed`等门禁即调用`timed_upload`。

改前证据：
```python
# Material/source_url approval is represented by the material's
# copyright_review.status=known_allowed and needs no per-asset approval.
if (discovery_file_valid
        and asset.copyright_status == "known_allowed"
        and asset.decision == "eligible"
        and asset.quality_status == "pass"
        and asset.relevance_status == "relevant"
        and asset.duplicate_of is None):
    upload_result = timed_upload(...)
```

## A2 — 候选集合是否可能超过copyright approval资产数

存在。一个material known_allowed可包含多张冻结资产；当asset_approvals只有2条甚至0条时，`set(asset_approvals) | material_approved_ids`可能大于2/0。

## A3 — 硬上限

已补强：若`len(upload_candidate_ids) > len(asset_approvals)`，写入builder error并清空上传候选，最终非零退出、零上传。material/source_url known_allowed不再能绕过显式single_asset批准数量。

## 追问二 / OBS-45

确认：修复后，若源站在discover完成之后才新增“禁止转载”声明，continue无法感知，仍可能上传冻结字节。登记`OBS-45(中)`，本档按审核者指示不修改。

## 微信上传只读诊断

- Token接口：`GET https://api.weixin.qq.com/cgi-bin/token`，query包含grant_type/appid/secret。
- 图片接口：`POST https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=<REDACTED>`。
- Token缓存：无。每张图调用`_get_access_token()`，token仅存在局部变量。
- 响应体：`resp.json()`进入内存；失败时转为`UploadResult.error`。原`timed_upload()`仅记录status/time，未记录error/errcode/HTTP，观测在事件层丢失。
- 凭据：报告不存明文；只允许运行时环境读取。
- 当前公网出口IP：`212.135.214.6`。
