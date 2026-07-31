# 阶段11 · 档14R9 · 媒体发现重跑报告

## 最终状态

```text
RUN_ID=20260731T135947-ai-bbg4al
STATUS=AWAITING_MEDIA_ASSET_APPROVAL
completed_stages=[aihot, super_writer, zh_human_writing]
current_stage=media_enrichment
uploaded_image_count=0
draft_created=false
formally_published=false
gzh_design_executed=false
wechat_draft_executed=false
```

## 1. 应用层DNS门禁原始输出

### .NET

```text
Windows IP 配置已成功刷新 DNS 解析缓存。
techcrunch.com2a04:fa87:fffd::c000:42dc
techcrunch.com192.0.66.220
www.ithome.com2409:8c6c:550:1203::2782:8323
www.ithome.com39.130.131.35
the-decoder.com185.185.24.14
www.anthropic.com2607:6bc0::10
www.anthropic.com160.79.104.10
x.com172.66.0.227
aihot.virxact.com117.187.145.164
aihot.virxact.com183.230.68.100
pbs.twimg.comERROR: 不知道这样的主机。
```

### Python 3.10

```text
techcrunch.com 192.0.66.220
www.ithome.com 39.130.131.35
the-decoder.com 185.185.24.14
www.anthropic.com 160.79.104.10
x.com 172.66.0.227
aihot.virxact.com 117.187.145.164
pbs.twimg.com gaierror: [Errno 11001] getaddrinfo failed
```

六个必需域名在两条路径均返回真实公网IP，无`198.18.0.0/15`或`fdfe:dcba:9876::/96`，门禁PASS。可选域名`pbs.twimg.com`双路径无法解析，按14R9只记录、不阻断。

## 2. 各阶段状态、耗时与ACK

| 阶段 | 状态 | receipt/执行耗时 | ACK token |
|---|---|---:|---|
| aihot | PASS | receipt 0.0s | `c60883f5b3a3f02dd820a27856e2dc1bf2ac008116f4c876d7f5a0cb65465557` |
| super_writer | PASS | receipt 0.0s | `a1184add98d2fc7b36f260248c236e658ad4f2b3180b28500476b5a8985ac159` |
| zh_human_writing | PASS_WITH_REAL_EDITS | receipt 0.0s | `4e5e1d1767e1cfc96cf6930e363067e4642dcf636c7805d18189f727bc74271d` |
| media_enrichment | AWAITING_MEDIA_ASSET_APPROVAL | 正式discover约34s | 无Agent ACK；subprocess批准状态机 |

AI HOT本轮raw=9、dedup=6。Super Writer前两次错误依次为旧章节标题4项、预算3项，第三次Full Mode通过，错误持续减少。zh真实调整两句，保真13/13、0警告、protected span变化0。

## 3. 正式discover前域名预检

| 域名 | 可解析 | IP | 耗时 | 错误 |
|---|---|---|---:|---|
| www.anthropic.com | True | 160.79.104.10, 2607:6bc0::10 | 0.047s | None |
| cloud.google.com | True | 142.250.197.46 | 0.031s | None |
| techcrunch.com | True | 192.0.66.220, 2a04:fa87:fffd::c000:42dc | 0.047s | None |
| www.ithome.com | True | 2409:8c6c:550:1203::2782:8323, 39.130.131.35 | 0.031s | None |

4个实际source_url域名全部可解析，无预检失败项。本轮dedup没有X来源材料，所以`pbs.twimg.com`不会作为正式待抓取source URL。

## 4. 每个来源域名抓取成败、耗时、图片数

正式media CLI提供discover总耗时约34秒和pages统计，不提供逐域名耗时。为避免伪造，逐URL耗时来自discover结束后的独立单次只读HTTP审计；每个URL仅测一次，无重试。

| 材料 | 域名 | HTTP | 单次审计耗时 | 读取样本字节 | 错误 |
|---|---|---:|---:|---:|---|
| M-01 | www.anthropic.com | 200 | 1.859s | 65536 | None |
| M-02 | cloud.google.com | 200 | 1.688s | 65536 | None |
| M-03 | techcrunch.com | 200 | 10.25s | 65536 | None |
| M-04 | www.ithome.com | 200 | 0.141s | 23134 | None |
| M-05 | techcrunch.com | 200 | 1.984s | 65536 | None |
| M-06 | www.ithome.com | 200 | 0.172s | 22775 | None |

正式discover抓取结果：

- M-01 / www.anthropic.com：抓取成功，归一化资产2项；
- M-02 / cloud.google.com：抓取成功，归一化资产4项，另1项去重记录缺source_page_url；
- M-03 / techcrunch.com：抓取成功，归一化资产3项；
- M-04 / www.ithome.com：因`max_total_images (8)`已达到，被正式发现器跳过；事后HTTP审计200/0.141s；
- M-05 / techcrunch.com：同上被跳过；事后HTTP审计200/1.984s；
- M-06 / www.ithome.com：同上被跳过；事后HTTP审计200/0.172s。

正式统计：`pages_fetched=3/pages_requested=3`、`candidates_discovered=39`、`downloads_succeeded=9`。没有域名连续失败，也没有300秒超时，因此无需跳过失败域名或重跑。

## 5. 候选资产完整清单

| ID | 来源页域名 | 图片域名 | 图片URL | 尺寸 | 格式 | 版权 | 决策 | SHA-256 |
|---|---|---|---|---|---|---|---|---|
| A-001 | www.anthropic.com | www-cdn.anthropic.com | https://www-cdn.anthropic.com/images/4zrzovbb/website/d3dd09ad16c68461dc3fb01df5e84cf7ccafda6c-1000x1000.svg | 0×0 | svg+xml | unknown/medium | review_required | c397f44118a2dc07c07e1b70b3f976ed21cca8353e321f93a8f24f168a45577f |
| A-002 | www.anthropic.com | www.anthropic.com | https://www.anthropic.com/api/opengraph-illustration?name=Hand Lock&backgroundColor=heather | 1900×1000 | png | unknown/high | rejected | a83ca5f045dfea5198d6cc35711155ae32da68e479993721e8152c2c86e8d6b8 |
| A-003 | cloud.google.com | storage.googleapis.com | https://storage.googleapis.com/gweb-cloudblog-publish/images/image1_9mv7QXp.max-1100x1100.png | 1024×559 | png | unknown/medium | review_required | 418d841fed238ad485cfc959555d518e5e1d6d005efd35080ce3a9035f2b87cf |
| A-004 | cloud.google.com | storage.googleapis.com | https://storage.googleapis.com/gweb-cloudblog-publish/images/1_TdmG649.max-700x700.png | 700×394 | png | unknown/medium | review_required | 5346d55e5a7478a5e7f21a12060900a912c616664e11a2eb8ee1c8ebc09e5e9c |
| A-005 | cloud.google.com | storage.googleapis.com | https://storage.googleapis.com/gweb-cloudblog-publish/images/10_-_Databases.max-700x700.jpg | 700×344 | jpeg | unknown/high | rejected | 8e2aa5872a1a73e6750e4aa7d7b91ca3bcba0cf9c47ad03a6aaaada1454e3bd8 |
| A-006 | cloud.google.com | www.gstatic.com | https://www.gstatic.com/cgc/super_cloud_gradient.png | None×None | None | unknown/high | rejected | None |
| A-007 | None | storage.googleapis.com | https://storage.googleapis.com/gweb-cloudblog-publish/images/10_-_Databases.max-2600x2600.jpg | None×None | None | unknown/high | rejected | e2705ad8fd017aa4dbab1f230e41d25dfb426d5f3b58554840493dd648b3ce15 |
| A-008 | techcrunch.com | techcrunch.com | https://techcrunch.com/wp-content/uploads/2026/05/tc-lockup-hp.svg | 0×0 | svg+xml | unknown/high | rejected | 376f83cfdfc05c8b4f7b668b38266b3687136391cb35fe4685af1d56f0d2fa81 |
| A-009 | techcrunch.com | techcrunch.com | https://techcrunch.com/wp-content/uploads/2024/09/tc-logo-mobile.svg | 0×0 | svg+xml | unknown/high | rejected | 26ddc3f8a8a2427b8e3ab0987e35aa802e6369d17836f1e4b242cc0ca85e32b7 |
| A-010 | techcrunch.com | techcrunch.com | https://techcrunch.com/wp-content/uploads/2026/07/TechCrunch-Disrupt-2026-Stage-Generic-Assets-AI-Crop.jpg?w=1024 | 1024×535 | jpeg | unknown/medium | review_required | 3381ff4e4f06874660a8150cff02474949c64e238b33f06d83327ea99e80254b |

归一化记录共10项：4项`review_required`、6项`rejected`；自动`eligible`为0。下载图片文件未提交Git，只记录URL、尺寸、格式、文件哈希和版权状态。

## 6. 来源分布与公众号适用性

图片域名分布：

```json
{
  "www-cdn.anthropic.com": 1,
  "www.anthropic.com": 1,
  "storage.googleapis.com": 4,
  "www.gstatic.com": 1,
  "techcrunch.com": 3
}
```

来源页面分布：

```json
{
  "www.anthropic.com": 2,
  "cloud.google.com": 4,
  "null": 1,
  "techcrunch.com": 3
}
```

候选不再集中于单一域名，覆盖Anthropic、Google Cloud/Google Storage和TechCrunch。适用性判断：

- A-003（1024×559 PNG）、A-004（700×394 PNG）、A-010（1024×535 JPEG）尺寸适合作为公众号正文候选，但版权状态unknown，需要人工审查；
- A-001为SVG，不适合作为直接发布照片，需要转换且仍需版权审查；
- logo、社交分享卡、过低尺寸和感知重复项已被正确拒绝；
- 该分布比上一轮33项全部来自pbs.twimg.com更适合作为公众号配图来源，但没有任何自动授权项，不能直接上传。

## 7. Gate与冻结manifest

```json
{
  "input_contract_pass": true,
  "provenance_complete": true,
  "publish_allowed": false,
  "secrets_detected": false,
  "security_checks_pass": true
}
```

```text
candidates_discovered=39
downloads_succeeded=9
review_required_assets=4
rejected_assets=6
eligible_assets=0
uploaded_assets=0
perceptual_duplicates_removed=1
```

RUN manifest路径：

```text
F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260731T135947-ai-bbg4al\media_enrichment\discoversset_discovery_manifest.json
```

Git路径：`audit/runs/20260731T135947-ai-bbg4al/media-manifest.json`

```text
file_sha256=3b114e123caec5448d74d8668d66a157234952942a6e2b1cdb453a7686f97e03
embedded_discovery_manifest_sha256=e950c03f3ed6f6cabe4cd2f27b2227e8b19aff8085c9cc350ab0df2b9e89136d
```

## 临时绕行说明(WORKAROUND,非修复)

- OBS-31：AI HOT产物继续机械添加`source_url ← links.original`和`aihot_permalink ← links.aihot`。代码未修复。
- OBS-32：canonical registry的6个materials/claims从6条dedup机械生成；Anthropic标题级素材的`source_excerpt`为空。代码未修复。
- OBS-37：本轮正式discover仅运行一次，34秒完成，无超时；达到max_total_images后按CLI自身机制停止，未盲目重跑。
- OBS-38：候选来源已由单一pbs.twimg.com改善为Anthropic、Google和TechCrunch多域分布。
- 本轮zh有真实非零编辑，不触发OBS-33。

## 8. 异常

1. AI HOT长JSON内嵌脚本首次出现SyntaxError，未写产物；改为复用同查询、逐项核对一致的8条API结构模板后生成，不涉及编造；
2. Super Writer第一次因复制模板的旧章节标题失败，第二次仅预算偏差，第三次通过；
3. `pbs.twimg.com`可选DNS观察项仍无法解析，但本轮正式素材不依赖X图片；
4. `www.gstatic.com`候选图片解析失败，单项被URL安全检查拒绝；未放宽检查；
5. max_total_images达到后M-04至M-06被正式发现器跳过；6个源URL事后审计均200；
6. 现有CLI不输出逐域名抓取耗时，因此报告使用独立单次HTTP审计并明确标注，不伪造正式耗时。

## 9. 凭据与文件

- 无微信token、appid、secret、Bearer或私钥命中；
- 所有提交文件均小于5MB；
- `discover/images/`下载文件全部排除，不提交图片文件。

## 10. 副作用声明

```text
uploaded_image_count=0
upload_events=[]
draft_created=false
formally_published=false
gzh_design_executed=false
wechat_draft_executed=false
copyright_approval.json=不存在
```

未上传图片、未创建草稿、未发布/群发、未生成批准文件、未修改Skill或Pipeline代码、未删除文件、未绕过URL安全检查。

---

# 阶段12 · 档15 · 媒体批准合同阻断追加报告

## 11. 冻结清单双哈希复核

复核对象：

```text
F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260731T135947-ai-bbg4al\media_enrichment\discover\asset_discovery_manifest.json
```

复核结果：

```text
file_sha256=3b114e123caec5448d74d8668d66a157234952942a6e2b1cdb453a7686f97e03
expected_file_sha256=3b114e123caec5448d74d8668d66a157234952942a6e2b1cdb453a7686f97e03
embedded_sha256=e950c03f3ed6f6cabe4cd2f27b2227e8b19aff8085c9cc350ab0df2b9e89136d
expected_embedded_sha256=e950c03f3ed6f6cabe4cd2f27b2227e8b19aff8085c9cc350ab0df2b9e89136d
result=PASS
frozen_assets=8
```

## 12. copyright_approval.json合同核验

只读核验了以下正式实现：

- `media-enrichment/src/media_enrichment/input_contract.py`；
- `media-enrichment/src/media_enrichment/asset_approval.py`；
- `wxgzh_pipeline/producers.py`中的`_STABLE_SINGLE_ASSET_FIELDS`及`_load_copyright_approvals`；
- 官方单资产批准测试样例。

`approved_scope=single_asset`的每条批准记录必须完整包含以下12个非空字段：

```text
asset_id
material_id
source_page_url
resolved_original_url
asset_sha256
asset_identity_sha256
discovery_manifest_sha256
approval_id
approved_scope
approved_by
approved_at
approval_evidence_sha256
```

其中4个SHA字段必须是64位十六进制；`asset_identity_sha256`还必须等于以下稳定身份计算结果：

```text
sha256(material_id + "\n" + source_page_url + "\n" + resolved_original_url + "\n" + asset_sha256)
```

## 13. 可从冻结清单与裁决取得的批准字段

### A-003

```text
asset_id=A-003
material_id=M-02
source_page_url=https://cloud.google.com/blog/products/databases/alloydb-adds-group-authentication-to-secure-enterprise-scale-and-ai-agents
resolved_original_url=https://storage.googleapis.com/gweb-cloudblog-publish/images/image1_9mv7QXp.max-1100x1100.png
asset_sha256=418d841fed238ad485cfc959555d518e5e1d6d005efd35080ce3a9035f2b87cf
asset_identity_sha256=ab1f59153db7eac712690c0018b113c6373c2fe3eb4f3d45ae0419687eb5cd2c
discovery_manifest_sha256=e950c03f3ed6f6cabe4cd2f27b2227e8b19aff8085c9cc350ab0df2b9e89136d
approved_scope=single_asset
approved_by=independent_reviewer
source_annotation=图片来源:Google Cloud 官方博客
```

### A-004

```text
asset_id=A-004
material_id=M-02
source_page_url=https://cloud.google.com/blog/products/databases/alloydb-adds-group-authentication-to-secure-enterprise-scale-and-ai-agents
resolved_original_url=https://storage.googleapis.com/gweb-cloudblog-publish/images/1_TdmG649.max-700x700.png
asset_sha256=5346d55e5a7478a5e7f21a12060900a912c616664e11a2eb8ee1c8ebc09e5e9c
asset_identity_sha256=353e242b00d7c0c4f0038770d1e6d096ef99a2b4c07fadd9646d13e680dabaa3
discovery_manifest_sha256=e950c03f3ed6f6cabe4cd2f27b2227e8b19aff8085c9cc350ab0df2b9e89136d
approved_scope=single_asset
approved_by=independent_reviewer
source_annotation=图片来源:Google Cloud 官方博客
```

## 14. 无法合法取得的必填字段

以下合同必填字段既不在冻结清单中，也未由档15裁决提供：

```text
approval_id
approved_at
approval_evidence_sha256
```

关键阻断字段是`approval_evidence_sha256`：

- 正式合同只要求它为64位SHA-256；
- 当前Skill/Pipeline没有定义批准证据正文、规范化格式或哈希生成算法；
- 测试中的`"e" * 64`是测试夹具，不是真实批准证据；
- 不能自行把用户指令、当前时间或任意文本假定为正式批准证据；
- 不能用随机/占位哈希换取合同通过。

`approval_id`和`approved_at`虽然测试样例存在命名和时间格式惯例，但用户明确要求：合同字段若无法从冻结清单或裁决中取得，必须停机，不得自行编造。因此也未生成。

## 15. 阻断裁决

```text
STATUS=BLOCKED_BEFORE_MEDIA_CONTINUE_APPROVAL_CONTRACT_INCOMPLETE
copyright_approval.json=未创建
media_continue=未执行
upload_events=保持原发现阶段空数组
uploaded_images=0
gzh_design=未开始
wechat_draft=未开始
```

未输出所谓“完整批准文件”，因为缺失必填值时生成文件即构成编造批准字段，并会违反阻断项3、5及档15第三节明确要求。

## 16. 阶段12实际副作用声明

```text
微信图片上传=0
微信素材media_id=不存在
草稿创建=0
草稿ID=不存在
发布=0
群发=0
定时发送=0
预览群发=0
copyright_approval.json=不存在
gzh_design产物=不存在
wechat_draft产物=不存在
```

阶段12实际操作仅包括：读取冻结manifest、读取合同和测试样例、复核哈希、更新Git审计报告。没有发生任何微信写操作。


---

# 阶段12 · 档15R · 批准证据补齐与media continue阻断报告

## 17. approval_evidence.md

RUN路径：

```text
F:/AIXM/wxgzh/.temp/wxgzh-pipeline/20260731T135947-ai-bbg4al/media_enrichment/approval_evidence.md
```

Git路径：`audit/runs/20260731T135947-ai-bbg4al/stages/media_enrichment/approval_evidence.md`

计算命令：

```text
python -c "from pathlib import Path; import hashlib; print(hashlib.sha256(Path('approval_evidence.md').read_bytes()).hexdigest())"
```

结果：

```text
approval_evidence_sha256=06321c8e58f28e4a4052b3a354d9db01beac8e80565ee995e23ecd07ede307e5
```

完整正文：

```text
-----BEGIN APPROVAL EVIDENCE-----
approval_id: AP-20260731T1449-INDEPENDENT-REVIEW-001
approved_by: independent_reviewer
approved_at: 2026-07-31T14:49:00+08:00
run_id: 20260731T135947-ai-bbg4al
frozen_file_sha256: 3b114e123caec5448d74d8668d66a157234952942a6e2b1cdb453a7686f97e03
embedded_sha256: e950c03f3ed6f6cabe4cd2f27b2227e8b19aff8085c9cc350ab0df2b9e89136d

APPROVED ASSETS (2):
A-003 sha256=418d841fed238ad485cfc959555d518e5e1d6d005efd35080ce3a9035f2b87cf
A-004 sha256=5346d55e5a7478a5e7f21a12060900a912c616664e11a2eb8ee1c8ebc09e5e9c

REJECTED BY REVIEWER (2):
A-001 reason=vector graphic unsuitable for article body
A-010 reason=event promotional material with third-party brandmark

UPHELD DISCOVERY REJECTIONS (6):
A-002 A-005 A-006 A-007 A-008 A-009

ATTRIBUTION REQUIRED:
图片来源:Google Cloud 官方博客

SCOPE:
upload_to_wechat_material_library=allowed
create_draft=allowed
publish=forbidden
mass_send=forbidden
scheduled_send=forbidden
-----END APPROVAL EVIDENCE-----
```

## 18. copyright_approval.json

RUN路径：

```text
F:/AIXM/wxgzh/.temp/wxgzh-pipeline/20260731T135947-ai-bbg4al/media_enrichment/copyright_approval.json
```

Git路径：`audit/runs/20260731T135947-ai-bbg4al/stages/media_enrichment/copyright_approval.json`

```text
sha256=457e8a88a46100efb3a31be01df68827f224813431a3527e66a644e4495108aa
```

完整内容：

```json
{
  "approvals": [
    {
      "approval_evidence_sha256": "06321c8e58f28e4a4052b3a354d9db01beac8e80565ee995e23ecd07ede307e5",
      "approval_id": "AP-20260731T1449-INDEPENDENT-REVIEW-001",
      "approved_at": "2026-07-31T14:49:00+08:00",
      "approved_by": "independent_reviewer",
      "approved_scope": "single_asset",
      "asset_id": "A-003",
      "asset_identity_sha256": "ab1f59153db7eac712690c0018b113c6373c2fe3eb4f3d45ae0419687eb5cd2c",
      "asset_sha256": "418d841fed238ad485cfc959555d518e5e1d6d005efd35080ce3a9035f2b87cf",
      "discovery_manifest_sha256": "e950c03f3ed6f6cabe4cd2f27b2227e8b19aff8085c9cc350ab0df2b9e89136d",
      "material_id": "M-02",
      "resolved_original_url": "https://storage.googleapis.com/gweb-cloudblog-publish/images/image1_9mv7QXp.max-1100x1100.png",
      "source_page_url": "https://cloud.google.com/blog/products/databases/alloydb-adds-group-authentication-to-secure-enterprise-scale-and-ai-agents"
    },
    {
      "approval_evidence_sha256": "06321c8e58f28e4a4052b3a354d9db01beac8e80565ee995e23ecd07ede307e5",
      "approval_id": "AP-20260731T1449-INDEPENDENT-REVIEW-001",
      "approved_at": "2026-07-31T14:49:00+08:00",
      "approved_by": "independent_reviewer",
      "approved_scope": "single_asset",
      "asset_id": "A-004",
      "asset_identity_sha256": "353e242b00d7c0c4f0038770d1e6d096ef99a2b4c07fadd9646d13e680dabaa3",
      "asset_sha256": "5346d55e5a7478a5e7f21a12060900a912c616664e11a2eb8ee1c8ebc09e5e9c",
      "discovery_manifest_sha256": "e950c03f3ed6f6cabe4cd2f27b2227e8b19aff8085c9cc350ab0df2b9e89136d",
      "material_id": "M-02",
      "resolved_original_url": "https://storage.googleapis.com/gweb-cloudblog-publish/images/1_TdmG649.max-700x700.png",
      "source_page_url": "https://cloud.google.com/blog/products/databases/alloydb-adds-group-authentication-to-secure-enterprise-scale-and-ai-agents"
    }
  ]
}
```

Pipeline正式`_load_copyright_approvals`校验：`count=2`，`single_asset=[A-003,A-004]`。continuation request中的`asset_approvals`也只有这两项，无第三资产。

## 19. media continue两次尝试

### 第一次

- 恢复命令显式设置`REAL_WECHAT_TEST_ALLOWED=true`；所有发布、群发、merge、cleanup开关为false；
- 执行约59秒；
- media entry生成continue产物，但官方validator exit 1，Pipeline未复制顶层3项输出；
- `upload_events=[]`，实际上传0；
- A-003稳定身份不匹配：`fresh_asset_identity_sha256`、`fresh_asset_sha256`、`fresh_resolved_original_url`、`fresh_source_page_url`；
- A-004稳定身份不匹配：上述4项加`fresh_material_id`；
- 两项批准均`asset_approval_consumed=false`；
- Anthropic源还出现一次TLS EOF。

### 第二次

按网络瞬时错误规则等待5秒后重试，执行约56秒。结果与第一次完全相同：

- `upload_events=[]`；
- A-003仍为相同4项身份不匹配；
- A-004仍为相同5项身份不匹配；
- 批准未消费；
- 上传0；
- official validator仍exit 1；
- Pipeline顶层media输出仍未生成。

第二次完整upload_events：

```json
{
  "schema_version": "1.0",
  "serial": true,
  "events": []
}
```

没有任何微信`media_id`，因此也不存在每图上传耗时。报告不编造不存在的ID或耗时。

## 20. 阻断判定

两次尝试之间错误清单、数量、批准消费状态和上传事件完全一致，未消除任何已知问题，触发：

```text
STATUS=BLOCKED_MEDIA_CONTINUE_NO_PROGRESS_ASSET_IDENTITY_DRIFT
阻断项=同一阶段连续两次尝试之间毫无进展
```

冻结manifest未修改；批准文件仍严格绑定原冻结A-003/A-004。continue重新抓取源页面时资产编号/URL/字节发生漂移，安全合同正确拒绝，未尝试绕过、替换或上传新鲜抓取的其他图片。

## 21. gzh_design与wechat_draft

```text
gzh_design=NOT_STARTED
gzh_design_ACK=不存在
wechat_draft=NOT_STARTED
draft_id=不存在
media_id=不存在
后台可见位置=不适用（未创建草稿）
```

由于media阶段未完成，未跳过阶段顺序，未创建排版握手或草稿。

## 22. 15R异常与OBS

- OBS-31/OBS-32仍为历史WORKAROUND，代码未修复；
- OBS-41：本轮没有套用任何历史结构模板；批准文件直接从当前冻结manifest机械生成；
- 新观察OBS-42：media continue会重新发现并重新编号资产，而非直接消费冻结资产；源页面抓取/回退变化会使同一`asset_id`指向不同资产，导致稳定身份批准无法消费；
- official validator失败是continue产物无法达到媒体合同门禁的结果，Pipeline未复制顶层输出；
- 两次均零上传，未出现第三图片。

## 23. 阶段12实际不可逆副作用

```text
微信素材上传=0
微信media_id=不存在
草稿创建=0
草稿ID=不存在
发布=0
群发=0
定时发送=0
预览群发=0
```

实际新增的本地可逆文件：`approval_evidence.md`、`copyright_approval.json`及continue审计产物。没有发生任何微信写入副作用。
