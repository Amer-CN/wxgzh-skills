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


---

# 阶段13 · 档16 · media-enrichment解冻修复与RUN恢复报告

## 24. 原始Skill备份

```text
source=F:/AIXM/wxgzh/.agents/skills/media-enrichment
backup=F:/AIXM/wxgzh/.agents/skills-backup/media-enrichment-pre-obs42-20260731
source_files=95
source_dirs=12
backup_files=95
backup_dirs=12
backup_result=PASS
```

备份在任何代码修改前完成，未删除或覆盖。

## 25. 六项只读定位结论

1. Continue入口：`media-enrichment/scripts/run_media_enrichment.py::main()`，由`--phase continue`进入。  
2. 原重抓路径：原代码对discover/continue共用materials循环，依次调用`fetch_page → extract_images → decode_proxy_url → download_image`，再把新鲜结果与冻结manifest比对。  
3. Discover图片落盘：`media_enrichment/discover/images/`；下载器以内容SHA-256命名，常规格式保留扩展名。  
4. 冻结映射：`asset_discovery_manifest.json`提供asset_id、material、URL、asset SHA和稳定身份；同目录`media_manifest.json`以asset_id提供`local_path`与图片元数据。  
5. 稳定身份：`sha256(material_id + "
" + source_page_url + "
" + resolved_original_url + "
" + asset_sha256)`。  
6. 产物落盘：Skill写入传入的output_dir；Pipeline给continue传`media_enrichment/continue/`，阶段合同却在`media_enrichment/`根读取3项required outputs，造成OBS-43。  

Discover确实持久化图片，因此修复方案成立。

## 26. 改动文件与SHA

| 文件 | 改前SHA-256 | 改后SHA-256 |
|---|---|---|
| `media-enrichment/scripts/run_media_enrichment.py` | `824de0a4677f60cacfa74c096bdab4d180857539b7f556473446ac55f6efb0e3` | `0f86838f57b02eb0d970404a072609d7bf4fa98e807f0f64d67607df7a0dedbd` |
| `media-enrichment/tests/test_single_asset_e2e.py` | `07de60bf7be20fc2d64e6e3cd4b838fb3d43653fc9486b484c4b63d749f902b8` | `c758dd627fb931034d4f60368b667c882363452e0b7994d64f76db3522c4c69a` |
| `wxgzh-pipeline/skills.lock.json` | `ff64e8ae3b5e80e2c45a5a86e8945c223ac6b1b6ca823a41a2d7b8fc45eef53b` | `c3f9a4ce07921e9ce5271faec92723bae4b90861af835c42cf3c0a72d8a3f16c` |

完整diff与诊断已在恢复RUN前提交：

```text
audit/skill-patches/obs42-media-enrichment/changes.diff
audit/skill-patches/obs42-media-enrichment/diagnosis.md
audit/skill-patches/obs42-media-enrichment/safety-checklist.md
audit/skill-patches/obs42-media-enrichment/files-changed.md
patch_commit=aa32198f79b60bd2dbde4b050979158fc54a75b0
relock_commit=4c6416d1b79531171bdf259b8db3c33b56b5e485
```

## 27. 最小修复结果

- OBS-42：continue不再抓源站，只读取冻结manifest同目录discover manifest与`images/`本地文件；
- OBS-43：continue/保留规范产物，并将3项required outputs字节镜像到阶段根；
- Discover路径行为未改；
- 未修改函数签名或公共CLI；
- 未修改其他Skill；
- Pipeline代码未改，只有被授权的锁文件字段更新。

## 28. 六条安全属性确认

1. **本地SHA强校验**：实际文件SHA与冻结asset SHA不一致即builder error、非零退出、零上传；有专用篡改测试。  
2. **仅批准资产**：当前RUN single_asset集合只含A-003/A-004；未批准资产不进入pending uploads。  
3. **数量不超过批准数**：single_asset遍历批准ID集合；本轮事件中不存在第三资产。  
4. **URL安全不放宽**：冻结resolved URL仍执行`is_safe_url(require_dns=True)`。  
5. **批准合同不放宽**：input contract、冻结manifest SHA、`approval_mismatches`与稳定身份均保留。  
6. **无自动批准路径**：unknown不自动批准；restricted/no-repost保持最高优先级。  

测试过程发现并修复了当前request材料绑定缺失和restricted优先级回归。最终：

```text
283 passed, 6 skipped
```

## 29. 重新锁定与doctor

官方锁算法：`wxgzh_pipeline.skill_discovery.compute_root_sha()`，只统计runtime文件，排除tests/cache/VCS元数据，对文本换行标准化。入口文件另由`_file_sha()`锁定。

```text
media.skill_root_sha256=e982b757f37050b0a92cbb4378b106a4f3637224ad3de4abc8b3389e6196a4f7
media.entrypoint_sha256=c99d5f505f8c9bc2aca064546ff91ffcae64a9667af00beb3121fe16d47a4641
runtime_manifest_sha256=172aa1b8082c6bb80822e56e201732ba5a118c6a53d7472f34b911f4a891e996
runtime_file_count=57
```

完整doctor输出保存于`audit/runs/20260731T135947-ai-bbg4al/doctor-output.json`：

```json
{
  "wxgzh_pipeline_version": "0.1.0-dev2-hotfix7R4",
  "project_root": "F:\\AIXM\\wxgzh",
  "skills_home": "F:\\AIXM\\wxgzh\\.agents\\skills",
  "network_mode": "live",
  "skills_locked_ok": true,
  "skills": {
    "super-writer": {
      "skill_name": "super-writer",
      "skill_dir": "F:\\AIXM\\wxgzh\\.agents\\skills\\super-writer",
      "exists": true,
      "locked_version": "0.3.2-rc1",
      "current_version": "0.3.2-rc1",
      "locked_root_sha256": "46a00a1bcdd5eeafae1ce6723241f97a6c1cd92f14f7baf8dc3625c9aed3018a",
      "current_root_sha256": "46a00a1bcdd5eeafae1ce6723241f97a6c1cd92f14f7baf8dc3625c9aed3018a",
      "file_count": 50,
      "version_ok": true,
      "hash_ok": true,
      "entrypoints_ok": true,
      "missing_files": [],
      "ok": true
    },
    "zh-human-writing": {
      "skill_name": "zh-human-writing",
      "skill_dir": "F:\\AIXM\\wxgzh\\.agents\\skills\\zh-human-writing",
      "exists": true,
      "locked_version": "0.1.0",
      "current_version": "0.1.0",
      "locked_root_sha256": "18491b361060a28d5eaf228f58b9b75e6ebde697eaa1149573bf468e0daea786",
      "current_root_sha256": "18491b361060a28d5eaf228f58b9b75e6ebde697eaa1149573bf468e0daea786",
      "file_count": 53,
      "version_ok": true,
      "hash_ok": true,
      "entrypoints_ok": true,
      "missing_files": [],
      "ok": true
    },
    "media-enrichment": {
      "skill_name": "media-enrichment",
      "skill_dir": "F:\\AIXM\\wxgzh\\.agents\\skills\\media-enrichment",
      "exists": true,
      "locked_version": "0.1.0-dev7-hotfix4",
      "current_version": "0.1.0-dev7-hotfix4",
      "locked_root_sha256": "e982b757f37050b0a92cbb4378b106a4f3637224ad3de4abc8b3389e6196a4f7",
      "current_root_sha256": "e982b757f37050b0a92cbb4378b106a4f3637224ad3de4abc8b3389e6196a4f7",
      "file_count": 57,
      "version_ok": true,
      "hash_ok": true,
      "entrypoints_ok": true,
      "missing_files": [],
      "ok": true
    },
    "gzh-design": {
      "skill_name": "gzh-design",
      "skill_dir": "F:\\AIXM\\wxgzh\\.agents\\skills\\gzh-design",
      "exists": true,
      "locked_version": "v2026.07.18-hammer.1",
      "current_version": "v2026.07.18-hammer.1",
      "locked_root_sha256": "9a8cd7f548c2186f789a5e24235001308fc6a868e0f57d74fc06c8919b4ff79b",
      "current_root_sha256": "9a8cd7f548c2186f789a5e24235001308fc6a868e0f57d74fc06c8919b4ff79b",
      "file_count": 76,
      "version_ok": true,
      "hash_ok": true,
      "entrypoints_ok": true,
      "missing_files": [],
      "ok": true
    },
    "aihot": {
      "skill_name": "aihot",
      "kind": "agent_invoked_skill",
      "exists": true,
      "registration": "C:\\Users\\Admin\\.agents\\skills\\aihot\\registration.json",
      "EXTERNAL_DEPENDENCY_AIHOT": "INSTALLED",
      "live_pipeline_allowed": true,
      "version_ok": true,
      "hash_ok": true,
      "entrypoints_ok": true,
      "ok": true,
      "note": "external dependency (卡兹克); capability checked for real (registration + output contract); never copied/modified/republished"
    }
  },
  "EXTERNAL_DEPENDENCY_AIHOT": "INSTALLED",
  "LIVE_PIPELINE_ALLOWED": true,
  "aihot_registration": "C:\\Users\\Admin\\.agents\\skills\\aihot\\registration.json",
  "aihot_checked_locations": [
    "F:\\AIXM\\wxgzh\\.agents\\skills\\aihot",
    "C:\\Users\\Admin\\.agents\\skills\\aihot"
  ],
  "wechat_config_present": true,
  "wechat_credential_detail": {
    "WECHAT_APP_ID_nonempty": true,
    "WECHAT_APP_SECRET_nonempty": true
  },
  "wechat_required": true,
  "project_writable": true,
  "FAIL_CLOSED": false,
  "doctor": "PASS"
}
```

## 30. RUN恢复与upload_events

补丁生效后，A-003/A-004均：

- 从discover持久化路径读取；
- SHA与冻结清单一致；
- approval consumed=true；
- copyright_status=known_allowed；
- decision=eligible；
- 无identity mismatch；
- 没有第三资产上传事件。

但微信上传连续两次均失败，第二次完整事件为：

```json
{
  "schema_version": "1.0",
  "serial": true,
  "events": [
    {
      "asset_id": "A-003",
      "mode": "wechat_image_host",
      "status": "failed",
      "started_at": "2026-07-31T10:38:31Z",
      "ended_at": "2026-07-31T10:38:31Z",
      "start_monotonic": 5966.937,
      "end_monotonic": 5966.937
    },
    {
      "asset_id": "A-004",
      "mode": "wechat_image_host",
      "status": "failed",
      "started_at": "2026-07-31T10:38:31Z",
      "ended_at": "2026-07-31T10:38:31Z",
      "start_monotonic": 5966.937,
      "end_monotonic": 5966.937
    }
  ]
}
```

两次均恰好2条事件、A-003/A-004各一次、status=failed、remote_url=null、media_id不存在。现有upload_events结构未记录上传器error字段，因此无法从审计产物获得微信返回的具体错误码；未编造错误原因。

## 31. 新阻断OBS-44

Pipeline的`validate_media_bindings.py`固定要求：

```text
body_images_min >= 6
```

本次审核只批准并授权上传2张图片。即使两张上传成功，正文绑定数最多2，仍无法通过`0/2 < 6`门禁。修改该门禁需要改Pipeline代码，超出本档授权；上传额外4张则违反“只允许A-003/A-004”。因此不能绕过。

最终状态：

```text
STATUS=BLOCKED_WECHAT_UPLOAD_FAILED_AND_MIN6_CONTRACT_CONFLICT
media_continue=FAILED
successful_uploads=0
media_ids=0
gzh_design=NOT_STARTED
gzh_design_ACK=不存在
wechat_draft=NOT_STARTED
draft_id=不存在
```

## 32. 各阶段耗时

- Skill备份：单次本地复制并核对；
- media完整测试：34.76s，283 passed/6 skipped；
- doctor：9s；
- 修复后首次RUN恢复：后台句柄过期，产物时间显示上传尝试于09:37:24Z；
- 第二次RUN恢复：15s，上传尝试于10:38:31Z；
- gzh-design与wechat_draft未执行。

## 33. 实际副作用声明

```text
微信上传尝试=4（2轮×2资产）
微信上传成功=0
微信media_id=0
成功写入微信素材库=0
草稿创建=0
发布=0
群发=0
定时发送=0
```

本地/代码副作用：创建原Skill完整备份；修改media-enrichment的1个runtime文件与1个测试文件；更新Pipeline锁文件中media条目的root/entry哈希；创建补丁审计与RUN审计。未删除文件、未修改其他Skill、未修改Pipeline代码、未绕过安全检查。


---

# 档17 · 微信错误观测与显式批准硬上限

## 34. 动手前备份

```text
backup=F:/AIXM/wxgzh/.agents/skills-backup/pre-obs44-obs46-20260731
media_source_files=116
media_source_dirs=14
media_backup_files=116
media_backup_dirs=14
pipeline_source_files=159
pipeline_source_dirs=45
pipeline_backup_files=159
pipeline_backup_dirs=45
result=PASS
```

档16备份`media-enrichment-pre-obs42-20260731`仍保留，未删除。

## 35. 追问一书面回答

### A1

material/source_url级上传路径是改前已有行为，不是档16补丁新引入。改前物证代码位于备份`media-enrichment-pre-obs42-20260731/scripts/run_media_enrichment.py`第381-399行：

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

### A2

存在输入组合让`upload_candidate_ids`大于`copyright_approval.json`资产数。一个known_allowed素材可包含多张冻结资产，而single_asset批准可以只有2条甚至0条。

### A3

已增加硬上限：若`len(upload_candidate_ids) > len(asset_approvals)`，写入builder error、清空候选、零上传并非零退出。material/source_url状态不再能扩大显式single_asset批准集合。

## 36. 追问二与OBS-45

确认：**修复后，若源站在 discover 完成之后才加上“禁止转载”声明，continue 已无法感知并仍会上传冻结字节。**

登记：`OBS-45(中) 源站在discover后新增禁止转载声明，continue无法感知。`

按审核者要求不为此改代码。

## 37. 阶段A微信只读诊断

```text
token_method=GET
endpoint=https://api.weixin.qq.com/cgi-bin/token
upload_method=POST
endpoint=https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=<REDACTED>
token_cache=none
token_scope=local variable per upload
public_egress_ip=212.135.214.6
```

响应体在`uploader.py`的`data = resp.json()`进入内存；原实现失败时压入`UploadResult.error`，但`timed_upload()`只记录status和时间，因此HTTP状态、errcode、errmsg在事件层丢失。

凭据审计：

```text
WECHAT_APP_ID=<REDACTED>; visible=false; length=0; prefix4=null
WECHAT_APP_SECRET=<REDACTED>; visible=false; length=0; prefix4=null
```

未写入appid、secret或access_token明文。

## 38. 阶段B观测补丁

每条upload event新增：

```text
http_status
wechat_errcode
wechat_errmsg
request_elapsed_seconds
endpoint_path
request_attempt_index
media_id
url
```

token不会进入事件。接口路径、判定逻辑、成功条件、重试次数均未改变。

media全量测试：

```text
284 passed
6 skipped
0 failed
elapsed=30.51s
```

旧material/source_url测试更新为：没有显式single_asset批准时必须失败闭合、零上传。这是六条安全属性第2、3条的收紧。

## 39. 六条安全属性

1. 本地文件SHA必须与冻结清单逐字一致，不一致即拒绝、不可降级。
2. 只能上传copyright_approval.json显式批准的资产。
3. 上传候选数量不能超过批准条数；超出即错误退出。
4. URL安全检查未放宽或跳过。
5. 批准合同、manifest SHA、approval_mismatches和稳定身份均未放宽。
6. 没有新增自动批准路径；restricted优先级保留。

## 40. 阶段C补丁归档与重锁

```text
audit/skill-patches/obs44-obs46/diagnosis.md
audit/skill-patches/obs44-obs46/changes.diff
audit/skill-patches/obs44-obs46/safety-checklist.md
audit/skill-patches/obs44-obs46/files-changed.md
commit=dd880c04839f776d101e884ad6b1867b8734b1e1
```

官方锁方式仍为`compute_root_sha()`和`_file_sha()`：

```text
media.skill_root_sha256=a8500e7ecc4b1b34e285340198a066ed1fa7e3484200346c373d0aa58498e8e4
media.entrypoint_sha256=4e0810510b17490c41eb6a892723ab60846820ad8ef7f894a2e0de3d8f7b901c
runtime_manifest_sha256=172aa1b8082c6bb80822e56e201732ba5a118c6a53d7472f34b911f4a891e996
runtime_file_count=57
```

Doctor完整输出：

```json
{
  "wxgzh_pipeline_version": "0.1.0-dev2-hotfix7R4",
  "project_root": "F:\\AIXM\\wxgzh",
  "skills_home": "F:\\AIXM\\wxgzh\\.agents\\skills",
  "network_mode": "live",
  "skills_locked_ok": true,
  "skills": {
    "super-writer": {
      "skill_name": "super-writer",
      "skill_dir": "F:\\AIXM\\wxgzh\\.agents\\skills\\super-writer",
      "exists": true,
      "locked_version": "0.3.2-rc1",
      "current_version": "0.3.2-rc1",
      "locked_root_sha256": "46a00a1bcdd5eeafae1ce6723241f97a6c1cd92f14f7baf8dc3625c9aed3018a",
      "current_root_sha256": "46a00a1bcdd5eeafae1ce6723241f97a6c1cd92f14f7baf8dc3625c9aed3018a",
      "file_count": 50,
      "version_ok": true,
      "hash_ok": true,
      "entrypoints_ok": true,
      "missing_files": [],
      "ok": true
    },
    "zh-human-writing": {
      "skill_name": "zh-human-writing",
      "skill_dir": "F:\\AIXM\\wxgzh\\.agents\\skills\\zh-human-writing",
      "exists": true,
      "locked_version": "0.1.0",
      "current_version": "0.1.0",
      "locked_root_sha256": "18491b361060a28d5eaf228f58b9b75e6ebde697eaa1149573bf468e0daea786",
      "current_root_sha256": "18491b361060a28d5eaf228f58b9b75e6ebde697eaa1149573bf468e0daea786",
      "file_count": 53,
      "version_ok": true,
      "hash_ok": true,
      "entrypoints_ok": true,
      "missing_files": [],
      "ok": true
    },
    "media-enrichment": {
      "skill_name": "media-enrichment",
      "skill_dir": "F:\\AIXM\\wxgzh\\.agents\\skills\\media-enrichment",
      "exists": true,
      "locked_version": "0.1.0-dev7-hotfix4",
      "current_version": "0.1.0-dev7-hotfix4",
      "locked_root_sha256": "a8500e7ecc4b1b34e285340198a066ed1fa7e3484200346c373d0aa58498e8e4",
      "current_root_sha256": "a8500e7ecc4b1b34e285340198a066ed1fa7e3484200346c373d0aa58498e8e4",
      "file_count": 57,
      "version_ok": true,
      "hash_ok": true,
      "entrypoints_ok": true,
      "missing_files": [],
      "ok": true
    },
    "gzh-design": {
      "skill_name": "gzh-design",
      "skill_dir": "F:\\AIXM\\wxgzh\\.agents\\skills\\gzh-design",
      "exists": true,
      "locked_version": "v2026.07.18-hammer.1",
      "current_version": "v2026.07.18-hammer.1",
      "locked_root_sha256": "9a8cd7f548c2186f789a5e24235001308fc6a868e0f57d74fc06c8919b4ff79b",
      "current_root_sha256": "9a8cd7f548c2186f789a5e24235001308fc6a868e0f57d74fc06c8919b4ff79b",
      "file_count": 76,
      "version_ok": true,
      "hash_ok": true,
      "entrypoints_ok": true,
      "missing_files": [],
      "ok": true
    },
    "aihot": {
      "skill_name": "aihot",
      "kind": "agent_invoked_skill",
      "exists": true,
      "registration": "C:\\Users\\Admin\\.agents\\skills\\aihot\\registration.json",
      "EXTERNAL_DEPENDENCY_AIHOT": "INSTALLED",
      "live_pipeline_allowed": true,
      "version_ok": true,
      "hash_ok": true,
      "entrypoints_ok": true,
      "ok": true,
      "note": "external dependency (卡兹克); capability checked for real (registration + output contract); never copied/modified/republished"
    }
  },
  "EXTERNAL_DEPENDENCY_AIHOT": "INSTALLED",
  "LIVE_PIPELINE_ALLOWED": true,
  "aihot_registration": "C:\\Users\\Admin\\.agents\\skills\\aihot\\registration.json",
  "aihot_checked_locations": [
    "F:\\AIXM\\wxgzh\\.agents\\skills\\aihot",
    "C:\\Users\\Admin\\.agents\\skills\\aihot"
  ],
  "wechat_config_present": true,
  "wechat_credential_detail": {
    "WECHAT_APP_ID_nonempty": true,
    "WECHAT_APP_SECRET_nonempty": true
  },
  "wechat_required": true,
  "project_writable": true,
  "FAIL_CLOSED": false,
  "doctor": "PASS"
}
```

## 41. 阶段D唯一一次上传尝试

完整upload_events：

```json
{
  "schema_version": "1.0",
  "serial": true,
  "events": [
    {
      "asset_id": "A-003",
      "mode": "wechat_image_host",
      "status": "failed",
      "started_at": "2026-07-31T15:20:58Z",
      "ended_at": "2026-07-31T15:20:58Z",
      "start_monotonic": 22913.89,
      "end_monotonic": 22913.89,
      "http_status": null,
      "wechat_errcode": null,
      "wechat_errmsg": null,
      "request_elapsed_seconds": 0.0,
      "endpoint_path": null,
      "request_attempt_index": 1,
      "media_id": null,
      "url": null
    },
    {
      "asset_id": "A-004",
      "mode": "wechat_image_host",
      "status": "failed",
      "started_at": "2026-07-31T15:20:58Z",
      "ended_at": "2026-07-31T15:20:58Z",
      "start_monotonic": 22913.89,
      "end_monotonic": 22913.89,
      "http_status": null,
      "wechat_errcode": null,
      "wechat_errmsg": null,
      "request_elapsed_seconds": 0.0,
      "endpoint_path": null,
      "request_attempt_index": 1,
      "media_id": null,
      "url": null
    }
  ]
}
```

判定：

```text
attempt_rounds=1
assets=[A-003,A-004]
third_asset=false
successful_uploads=0
wechat_errcode=null
wechat_errmsg=null
http_status=null
endpoint_path=null
media_id=null
```

两条事件均在HTTP请求前失败。只读检查确认当前执行环境没有暴露`WECHAT_APP_ID`和`WECHAT_APP_SECRET`给上传器（长度均0），因此没有调用token或uploadimg接口，无法取得微信errcode。

该失败属于环境配置问题，不是网络抖动；按档17阻断项10停机，没有第二轮。

## 42. 阶段E/F未执行

```text
body_images_min_code_change=NOT_EXECUTED
body_images_min_effective=6(default unchanged)
pipeline_full_tests=NOT_EXECUTED
gzh_design=NOT_STARTED
wechat_draft=NOT_STARTED
draft_id=null
```

阶段E只有阶段D两图均success时才授权。由于上传失败，未修改`validate_media_bindings.py`，未进入排版或草稿。

## 43. OBS与异常

- OBS-42：冻结本地字节修复保持有效。
- OBS-43：continue三产物根目录镜像保持有效。
- OBS-44：至少6图合同冲突仍存在，但本档阶段E未获执行条件。
- OBS-45：discover后新增禁止转载声明无法感知。
- OBS-46：旧upload_events缺少微信错误观测；本档已补字段。本次实际证明失败发生在HTTP前，字段为null。

## 44. 实际不可逆副作用

```text
档17微信上传尝试=2（单轮×A-003/A-004）
档17实际HTTP微信请求=0
档17上传成功=0
档17新增微信素材=0
media_id=0
草稿创建=0
发布=0
群发=0
定时发送=0
预览群发=0
```

本地副作用：创建档17前备份；修改media-enrichment continue硬上限、uploader观测字段及对应测试；更新media锁；创建补丁与RUN审计。没有删除文件、没有上传图片成功、没有创建草稿。

最终状态：

```text
STATUS=BLOCKED_PRE_HTTP_WECHAT_CREDENTIALS_NOT_VISIBLE
WECHAT_ERRCODE=null
UPLOADED_COUNT=0
DRAFT_ID=null

---

# 档18 · OBS-47 凭据来源统一、Token缓存与单轮上传结果

## 45. 第0节自检与备份

```text
formal_version=0.1.0-dev2-hotfix7R4
obs42_freeze_patch=present
obs46_observability_and_approval_limit=present
pre_obs47_backup=F:/AIXM/wxgzh/.agents/skills-backup/pre-obs47-20260801
media_backup=116 files / 14 dirs
pipeline_backup=159 files / 45 dirs
historical_evidence_dirs=untouched
```

## 46. 阶段A诊断与A1-A6

- A1 doctor来源：`wxgzh_pipeline/orchestrator.py:110-115`先复制进程环境，再从`F:/AIXM/wxgzh/.env`用`SEC.parse_env_file`和`setdefault`补入；`secrets.py:52-60`检查两个字段非空且非占位。
- A2 上传器原来源：`media-enrichment/src/media_enrichment/uploader.py:191-193`只读`os.environ`；`_get_access_token()`使用实例字段。
- A3 修复前不同：doctor验证“进程环境 + 项目.env”局部字典，Pipeline `producers.py:758-776`未把该合并字典传给media子进程；修复后`_media_subprocess_env()`将同一来源传入discover/continue子进程，doctor未反向修改。
- A4 doctor来源`F:/AIXM/wxgzh/.env`：APP_ID存在、长度18；APP_SECRET存在、长度32；不记录明文、前缀或后缀。
- A5未触发；来源非空。
- A6根因是子进程环境未继承doctor的局部合并字典。

Token修复：uploader实例内存缓存`_access_token`，单RUN两张图复用一次；不落盘、不进入report、events或日志。

## 47. 网络路径

```text
.NET api.weixin.qq.com = 120.233.18.202, 120.232.65.161, 112.53.42.235, 112.60.20.154
Python api.weixin.qq.com = 120.233.18.202
fake-ip-hit = false
current_egress_ip = 185.217.5.28
stage17_egress_ip = 212.135.214.6
```

## 48. 测试与锁

- media全量：`286 passed, 6 skipped, 0 failed`；
- Pipeline全量：除1个portable-installer测试外全部通过；该测试失败原因是测试夹具复制目录缺少`.git`，随后对锁定commit执行checkout失败；不是凭据修复断言失败。
- OBS47直接凭据同源断言：`PASS`。pytest重试因安全删除保护被用户拒绝，未再重试或删除临时目录。
- 官方锁算法：`compute_root_sha()`、`compute_runtime_manifest_sha()`、`_file_sha()`。
- media新root：`1dab61844d364f2ca401b0516a6a118cfa80a9b14c9f29379d0a76ab5149953b`；entry：`a54deef36cefd952cffa88c404858948150e383636a74ac7f996fe791aa9541e`；manifest保持`172aa1b8082c6bb80822e56e201732ba5a118c6a53d7472f34b911f4a891e996`；count=57。
- Pipeline runtime root：`bc5009621c4b0ffeebaf19f239d27c7ea38805ab0cf934379b6358e195c8843a`。
- skills.lock改前SHA：`9de36f1605554192e9c937c2a8c09c79720f2ffb0d609d48c723a66eaed92dc4`；改后SHA：`668dd8e689331c795a27aa45217ec12b8b67af4ebe1edc152a2fd579150530f3`。
- doctor：`skills_locked_ok=true`、`EXTERNAL_DEPENDENCY_AIHOT=INSTALLED`、`LIVE_PIPELINE_ALLOWED=true`、`wechat_config_present=true`、`FAIL_CLOSED=false`、`doctor=PASS`。完整脱敏输出见`doctor-output-stage18.json`。

## 49. 阶段E单轮上传

只执行一次media continue，未重跑discover。清单只有A-003/A-004，无第三资产。

```json
{
  "A-003": {"status":"success","http_status":200,"errcode":null,"errmsg":null,"elapsed":1.422,"endpoint":"/cgi-bin/media/uploadimg","media_id":null,"url":"https://mmbiz.qpic.cn/..."},
  "A-004": {"status":"success","http_status":200,"errcode":null,"errmsg":null,"elapsed":1.0,"endpoint":"/cgi-bin/media/uploadimg","media_id":null,"url":"https://mmbiz.qpic.cn/..."}
}
```

微信`uploadimg`返回URL而非media_id，因此media_id为null是接口实际返回形态。成功上传数=2，正文绑定数=2，错误码为空。

## 50. 阶段F/G阻断

阶段E成功后发现：

- `validate_media_bindings.py:13`默认`MIN_BODY_IMAGES=6`；
- `contracts.py:175-177`另有独立`counts.BODY_IMAGES_MIN`默认6校验；
- 阶段E失败输出明确为`body_image_count=2`, `min_required=6`。

要让Pipeline通过，不能只改validator；还必须接线第二层合同，超出本档“仅限validate_media_bindings.py中body_images_min”的授权边界。另一个不可接受方案是重新resume media producer，因为会再次调用微信上传造成重复不可逆副作用；手工改state/receipt则是伪造回执。故未修改body_images_min、未重传、未进入gzh_design、未创建草稿。

## 51. OBS与异常

- OBS-47：doctor与上传器凭据来源已统一；doctor绿灯与上传器读取同源。
- OBS-48：出口IP不稳定，当前`185.217.5.28`不同于档17`212.135.214.6`；token单RUN已缓存。
- OBS-49：批准数量硬上限使material级路径失效，按审核者主动收紧不修。
- OBS-50：本次未执行作废指令；档18第0节自检优先级生效。
- 安全删除保护异常：一次Pipeline pytest清理及一次doctor保存命令触发历史临时垃圾目录清理拒绝；未删除任何文件，未重试等价清理。

## 52. 实际副作用

```text
成功微信上传调用=2
成功写入微信图片托管=2（A-003/A-004）
media_id=0（接口返回URL）
draft_id=null
发布=0
群发=0
定时发送=0
预览群发=0
```

实际状态：`STATUS=BLOCKED_MIN_IMAGES_SECOND_CONTRACT_AND_NO_SAFE_RESUME_PATH`。

档18最终不能创建草稿，不是因为上传失败，而是因为已成功上传后，Pipeline仍有第二层未授权可改的最小图片数合同，且重新resume会重复上传。

---

# 档19 · 第二层最小图片数、上传幂等与草稿首次失败

## 53. 自检与备份

档16冻结字节、档17观测/批准上限、档18凭据同源/token缓存均存在。备份`pre-obs53-20260801`成功：media源/备份均116文件14目录，Pipeline源/备份均181文件46目录。未清理任何物证或pytest目录。

## 54. 阶段A定位

- `contracts.py:168-177`从合同YAML的`counts.BODY_IMAGES_MIN`读取，默认6；`STAGE_CONFIG`定义于`stages/media_enrichment.py:11-15`。
- `validate_media_bindings.py:13,29-66`原硬编码6；调用入口为`stages/media_enrichment.py:39-54`。
- `orchestrator.py:158-195,197-224`对失败阶段重跑producer，原无免上传复验分支。
- media continue原先只写upload_events，上传前从不读取。
- 未发现第三层最小图片数执行校验。

## 55. 显式配置全文

```json
{
  "approval_id": "AP-20260731T1449-INDEPENDENT-REVIEW-001",
  "body_images_min": 2,
  "default_value": 6,
  "reason": "候选池仅 4 张待审查资产,审核者批准 2 张,凑不出 6 张",
  "set_by": "independent_reviewer"
}
```

validator与contracts读取同一文件；缺失回落6；小于1拒绝；validator报告实际值与来源。contracts除BODY_IMAGES_MIN取值外其他校验未改。

## 56. OBS-53幂等护栏

continue先读已有事件。仅当资产已有`success`且URL为合法微信托管URL时，在完成冻结SHA、批准、数量上限、URL安全、稳定身份等全部校验后复用URL，并追加`skipped_already_uploaded`；原success事件保留，failed事件不复用。

本次恢复结果：

```text
UPLOADIMG_CALLS_THIS_STAGE=0
A-003=skipped_already_uploaded; URL与档18逐字一致
A-004=skipped_already_uploaded; URL与档18逐字一致
third_asset=false
body_images_count=2
body_images_min_effective=2
body_images_min_source=media_enrichment/validation_config.json
```

## 57. 测试、锁与doctor

- media：289 passed，6 skipped，0 failed。
- Pipeline：142 passed，1 skipped，12 failed；12项均由安全删除保护拒绝测试内部unlink/rmtree，或OBS-52临时夹具缺`.git`引起；档19新增配置测试未失败。
- 直接min规则断言PASS：默认6、显式2、0/负数拒绝。
- 官方锁算法：`compute_root_sha`、`compute_runtime_manifest_sha`、`_file_sha`。
- media root=`0d8aea2169cec17c4e9f95af66b6b4da3c532554a0a316fe3fb604bd0b7ab3a3`；entry=`2d877a93b37658bb5b2e247827952a86abe11fff5a9c148024238dd0cccd979f`；manifest=`172aa1b8082c6bb80822e56e201732ba5a118c6a53d7472f34b911f4a891e996`；count=57。
- doctor：skills_locked_ok=true、wechat_config_present=true、FAIL_CLOSED=false、doctor=PASS。
- OBS-51说明：doctor证据为重建证据，来源为本次会话已返回的完整doctor输出；没有声称是原始重定向文件。

## 58. 排版与草稿

media合同PASS。gzh_design正式执行成功：`status=success`、`CONTRACT=PASS`、`THEME_IDENTITY=PASS`、`OFFICIAL_GZH_CALL=true`；其`stage_receipt.json`即ACK，文件已归档。

wechat_draft首次且唯一一次入口执行返回exit 1，仅生成`stage_request.json`，未生成`draft_creation_result.json`，故`draft_id=null`，微信后台无可见草稿位置。按阻断项17未作第二次尝试。

## 59. 七条安全属性

1. 冻结本地SHA不一致即拒绝。
2. 仅上传copyright_approval.json明确批准资产。
3. 上传数不超过批准数。
4. URL安全检查未放宽。
5. 批准合同/稳定身份未放宽。
6. 无自动批准路径。
7. 已有success资产本轮uploadimg调用为0，复用前仍完整校验。

## 60. 实际不可逆副作用

```text
累计微信图片托管=2（档18已产生）
本档新增uploadimg=0
本档新增草稿=0
发布=0
群发=0
定时发送=0
预览群发=0
```

图片来源:Google Cloud 官方博客

最终状态：`BLOCKED_WECHAT_DRAFT_FIRST_ATTEMPT_FAILED_NO_RETRY`。

---

# 档20R · 通用失败观测与草稿真实根因

## 61. 更正、自检与备份

确认档20的OBS-55、OBS-57撤回：`skill_name=gzh-design`是执行Skill/锁身份映射，Pipeline按stage分发；真实RUN中`gzh_design/final.html`存在且请求路径一致。未修改路由或HTML路径。

档16/17/18/19四类补丁只读自检均成立。备份`pre-obs56-20260801`成功：Pipeline源与备份均181文件、46目录；统计包含46个pyc/cache文件，排除后135文件。未删除、移动、复用任何历史物证或pytest目录。

## 62. OBS-56失败观测修复

通用`execute_stage`非零子进程路径在抛`StageError`前写`stage_failure.json`，字段包括stage、entry、exit_code、stdout_tail、stderr_tail、request_elapsed_seconds、脱敏argv、recorded_at。stdout和stderr均记录；query、键值和参数形式的token/secret均脱敏。

不改变成功条件、路由、输入路径、合同、receipt或异常传播；成功路径不写失败文件。

测试：

```text
OBS56定向=3 passed
media=289 passed, 6 skipped, 0 failed
Pipeline=144 passed, 1 skipped, 13 failed
```

Pipeline的13项均为safe-delete保护或OBS-52缺`.git`夹具；本档最终定向3项独立通过。

## 63. 阶段C封面验证

- `publish_wechat_draft.py:519-531`的`--cover/--thumb-media-id`均非argparse必填。
- `545-549`只校验已传入的cover；`574-577`有`--audit-dir`即进入audit；`579-582`缺封面exit只作用于非audit模式。
- `create_draft:239-253`始终写`thumb_media_id`；无默认值/占位。
- `producers.py:818-827`只传`--html/--title/--audit-dir`，没有cover或thumb id。
- 微信官方`draft/add`文档：`article_type=news`时`thumb_media_id`必填，且必须为永久MediaID；当前脚本未传article_type，默认news。

第1次尝试前结论为`证据不足`：官方/代码证明news需要封面，但历史真实错误不可取得，预检也可能先失败。因此尝试前条件封面授权未生效，没有上传封面。

## 64. 锁与doctor

官方方式复算`compute_root_sha()`、`compute_runtime_manifest_sha()`和锁定entrypoint SHA；super-writer、zh-human-writing、media-enrichment、gzh-design的root/manifest/count全部match。

本档只改Pipeline自身；`skills.lock.json`只锁外部Skill，因此无需修改，前后SHA均为：

```text
a9e07ef42017cff225158466213253baf1155f34a7c2f1bdaf62a87dbbc751d6
```

Doctor完整返回：`skills_locked_ok=true`、`wechat_config_present=true`、`project_writable=true`、`FAIL_CLOSED=false`、`doctor=PASS`。本次为会话直接返回证据，没有重建doctor文件。

## 65. 第1次草稿尝试与真实错误

只恢复wechat_draft；前五阶段receipt全部有效，未重跑discover/media/gzh_design，uploadimg调用0。

`stage_failure-stage20r-attempt1.json`：

```text
exit_code=1
request_elapsed_seconds=2.076
stderr_tail=""
wechat_errcode=40007
wechat_errmsg=invalid media_id hint: [cGqAPa023644-1] rid: 6a6d0f4c-421f718d-2a6d5a2b
endpoint_path=/cgi-bin/draft/add
```

stdout原文证明：HTML raw/normalized SHA均为`5962fc7a...df6800`；CJK=1773、leaf=82、validator ERROR/WARN=0、publish ERROR/WARNING=0，预检和outgoing门禁均PASS；随后`draft/add`返回`40007 invalid media_id`。

综合官方文档、代码和本次运行：封面是news草稿必填项，空`thumb_media_id`是本次失败根因。但档20R的F-2/阻断项16明确将40007列为环境类错误，必须停机交用户；因此没有启用封面上传动作，也没有第2次草稿尝试。

## 66. 八条安全属性

1. 冻结本地SHA校验未改。
2. 仅批准资产上传规则未改。
3. 批准数量上限未改。
4. URL安全检查未改。
5. 批准合同加载/校验未改。
6. 未新增自动批准路径。
7. 本档uploadimg调用0，历史success未重传。
8. cover素材上传0；不存在需要复用的cover success事件，也未绕过幂等要求。

## 67. 实际不可逆副作用

```text
累计微信正文图片托管=2（档18）
本档新增uploadimg=0
本档material/add_material=0
本档草稿尝试=1
本档新增草稿=0
发布/群发/定时/预览群发=0
删除素材=0
```

无WORKAROUND。微信后台无新增草稿，draft_id=null。

图片来源:Google Cloud 官方博客

最终状态：`BLOCKED_WECHAT_40007_INVALID_MEDIA_ID_NO_COVER_UPLOAD_NO_RETRY`。

---

# 档21 · 封面接线前自相矛盾阻断

## 68. 自检、备份与阶段A

档16/17/18/19/20R五项补丁只读自检均通过。创建`pre-obs58-20260801`备份：Pipeline源/备份均181文件、46目录（含46个pyc/cache，排除后135）；gzh-design源/备份均297文件、15目录（含2个pyc/cache，排除后295）。未清理任何目录。

封面链路：`publish_wechat_draft.py:163-180`从本地文件读取封面，POST`/cgi-bin/material/add_material?type=image`的multipart media，成功取响应`media_id`；`--cover`与`--thumb-media-id`互斥。计划选择`--cover`，使gzh脚本内部拥有上传、事件和幂等复用。

A-003冻结文件：

```text
path=F:/AIXM/wxgzh/.temp/wxgzh-pipeline/20260731T135947-ai-bbg4al/media_enrichment/discover/images/418d841fed238ad485cfc959555d518e5e1d6d005efd35080ce3a9035f2b87cf.png
actual_sha256=418d841fed238ad485cfc959555d518e5e1d6d005efd35080ce3a9035f2b87cf
manifest_sha256=418d841fed238ad485cfc959555d518e5e1d6d005efd35080ce3a9035f2b87cf
approval_sha256=418d841fed238ad485cfc959555d518e5e1d6d005efd35080ce3a9035f2b87cf
approved_scope=single_asset
```

三者逐字一致。没有网络重下载、裁剪或重编码。草稿脚本没有freepublish、masssend、定时发送或预览群发调用路径。

## 69. 阻断项23

档21要求修改`gzh-design/scripts/publish_wechat_draft.py`并重锁gzh-design，同时要求只执行wechat_draft、禁止改receipt或重跑其他阶段。两项无法同时成立：

1. 官方runtime manifest包含`publish_wechat_draft.py`，runtime count=76；修改它必然改变gzh-design root。
2. `receipts.py:222-228`对每个已完成live阶段重算整个sub-skill root，并与receipt记录比较。
3. 当前`gzh_design` receipt验证PASS、mismatches为空；它记录的是修改前root。
4. 修改并重锁后，该receipt必然报`skill_root_sha256 mismatch`，恢复将使gzh_design失效并重跑。
5. 若避免重跑，只能放宽receipt校验或手工重写receipt，二者均被禁止。

因此命中档21阻断项23：“指令内部出现自相矛盾，服从更严格要求并立即上报”。

曾在正式Pipeline做过尚未提交的最小参数草案，发现冲突后已逐字撤回；正式、Git和pre-obs58备份中的`producers.py`SHA均为：

```text
129af865de658280485557bfec206550477b678d348e99292fe4e87fa69c43ec
```

未修改gzh-design，未修改锁，未修改receipt，未运行测试/doctor（无最终代码变更），未执行阶段D/E。

## 70. 九条安全属性与副作用

1. 冻结SHA规则未改。
2. 显式批准规则未改。
3. 批准数量上限未改。
4. URL安全未改。
5. 批准合同未改。
6. 无自动批准路径。
7. 本档uploadimg调用0。
8. 本档封面素材上传0，未伪造cover事件。
9. A-003未从网络下载、裁剪或重编码。

```text
累计uploadimg图片=2（档18）
本档material/add_material=0
本档新增草稿尝试=0
本档新增草稿=0
发布/群发/定时/预览群发=0
```

图片来源:Google Cloud 官方博客

最终状态：`BLOCKED_INSTRUCTION_CONTRADICTION_GZH_RUNTIME_RECEIPT_ROOT`。
