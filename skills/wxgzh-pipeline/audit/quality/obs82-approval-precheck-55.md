# 档 55 — OBS-82 批准可批准性预校验(离线)

- 日期:2026-08-04
- 状态:**通过**(离线执行,未调微信、未发起新 RUN)。
- 落点:预校验实现在 **Pipeline 侧**(`wxgzh_pipeline/producers.py`),**未改被锁 media-enrichment**(档 57 禁止改其代码内容,root `0d8aea21…` 必须保持)。

---

## 11. discover 候选硬门槛预校验

- 新增 `_approval_precheck(rd)`(producers.py):
  - 数据源:`media_enrichment/discover/media_manifest.json` 的 `width/height`(discover 阶段已下载并实测尺寸)
  - 判定口径:与 media-enrichment continue 阶段一致——正文图最小 **640×360**(`w < 640 or h < 360` 即不达标)
  - **不依赖 `decision`/`quality_status` 字段**:档 50 实证 A-107 在 discover/media_manifest 中 `decision=rejected` 且 `quality=pass`(语义混乱),仍被人工批准——预校验以硬尺寸独立判定
- 接入点 1(`_media()` discover 成功、等待人工批准之前):写 `media_enrichment/approval_precheck.json`(eligible 清单 + excluded 清单),meta 记录路径
- 接入点 2(`_media()` 批准合同消费时):新增 `_enforce_approval_precheck()`——批准合同中任何资产不在 eligible 清单 → `MediaRequestError` **FAIL_CLOSED**(防止「批准记录被消费而绑定数不足」重演)

## 12. 封面尺寸要求

- 封面无独立代码级尺寸门槛(档 52 第 9 项遗留结论不变):微信侧仅建议比例(如 2.35:1),无 API 强制下限
- 封面从**已批准正文图**选择(OBS-72 实现),正文门槛 640×360 已隐含覆盖封面候选
- 若未来引入封面专用尺寸约束,需扩展 `_approval_precheck`(本档不臆造无权威依据的封面下限)

## 13. ★反向验证(A-107 回归样本)

- 真实 RUN `20260802T220853-codex-sol-luna-max-m6pyv4` 的 discover/media_manifest.json 实测:
  - `eligible`:A-109..A-114(含 A-109 1440×658、A-110 1080×1920 等全部 ≥640×360)✓
  - `excluded`:**A-107(100×100)** 与 A-108(1×1),reason=`dimensions below minimum 640x360` ✓
- 消费端兜底实测:批准合同(含 A-107 的 AP-…-001 记录)消费 → `approval precheck FAIL_CLOSED: approved asset A-107 (100x100 below minimum 640x360)` ✓
- 测试 `tests/test_obs55_approval_precheck.py` 5 项(小尺寸排除/边界 639×359 vs 640×360/消费端拦截/消费端放行/真实数据回归):**5/5 通过**

## 14. 预校验失败行为:排除 + 标注

- **排除**:不达标资产不进 eligible 清单(不进入人工批准候选),消费端 FAIL_CLOSED 兜底
- **标注**:被排除资产完整保留在 `approval_precheck.json` 的 excluded 列表(含宽高与原因)——可追溯、可人工复核是否误判,且不掩盖 media 侧后续改进空间
- 理由:单纯标注会让 A-107 场景重演(人工批准了才发现不能用,档 50 教训);单纯静默排除会丢失复核依据。二者结合是 fail-closed 且可审计的最小形态
- 边界(如实):尺寸未知(width/height 为 null)的资产不排除(不构成「已知不达标」),由 media continue 阶段既有尺寸校验兜底

## 复核

- upgrade_regression **ALL PASS**(pytest PASS 含新 5 项,1 项显式排除;四锁 relock dry-run 无变化;doctor PASS;cross-side SKIP)
- 双侧 doctor PASS,四锁 hash_ok 全 true;lock 双侧 `8FCBC203…` 未变;台账 4 条;安装侧与 repo HEAD 逐字一致(595→597 文件,含新测试与 producers 改动)
- 微信副作用:0(本档离线,未调微信、未发起新 RUN、未创建草稿)
