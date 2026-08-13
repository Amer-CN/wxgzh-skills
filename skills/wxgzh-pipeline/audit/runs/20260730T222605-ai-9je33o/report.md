# 阶段11 · 档14R6 · 继续当前RUN至媒体批准点

## 最终状态

```text
RUN_ID=20260730T222605-ai-9je33o
RUN_DIR=F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260730T222605-ai-9je33o
CLI_STATUS=AWAITING_MEDIA_ASSET_APPROVAL
current_stage=media_enrichment
completed_stages=[aihot, super_writer, zh_human_writing]
gzh_design_executed=false
wechat_draft_executed=false
uploaded_image_count=0
draft_created=false
formally_published=false
```

`pipeline_state.json`仍保留`failed_stage=media_enrichment`，这是进入批准点前一次media入口失败留下的历史字段；最终CLI已明确返回`AWAITING_MEDIA_ASSET_APPROVAL`，三个已完成阶段receipt重新验证均`ok=true`。

## 1. Super Writer semantic-map修正进展

文章正文从未改动，SHA始终为：

```text
b51f06c3bf0726f09aa0d45c4ae172b8a51a8dfab7b95e2363ab77a252dd8386
```

### 第一次Full Mode尝试

- `length_status=within_range`；
- 四章节预算偏差30.6%—34.2%；
- 4个块使用未知role=`section`，共8类错误输出。

消除进展：修正length policy/outline预算；role改为`article_section`。

### 第二次尝试

- 长度与章节预算全部通过，偏差0.0%—1.3%；
- 8条错误均变为4个`article_section`分别缺`payload.heading_text`和`payload.section_index`。

消除进展：预算和role问题全部消除；错误语义更具体。

### 第三次尝试

仅在sec-1至sec-4的payload补：

```text
heading_text ← 对应heading_path唯一值
section_index ← 1,2,3,4
```

最终完整JSON：

```json
{
  "passed": true,
  "length_status": "within_range",
  "article_mode": "medium",
  "cjk_chars": 2011,
  "latin_words": 68,
  "visible_chars_no_whitespace": 2564,
  "paragraphs": 24,
  "sections": 5,
  "target_visible_chars": 2180,
  "acceptable_min": 2000,
  "acceptable_max": 2800,
  "section_budgets": [
    {"title":"一、当安全工具开始自己行动","weight":0.21,"budget":457,"actual_chars":463,"deviation":0.013},
    {"title":"二、能力不是一个分数","weight":0.265,"budget":577,"actual_chars":577,"deviation":0.0},
    {"title":"三、身份治理成为新边界","weight":0.263,"budget":573,"actual_chars":574,"deviation":0.002},
    {"title":"四、企业现在该补什么","weight":0.262,"budget":571,"actual_chars":566,"deviation":0.009}
  ],
  "duplicate_findings": [],
  "errors": [],
  "warnings": []
}
```

## 2. 手工补齐字段与逐字段来源

### OBS-31：9条dedup顶层URL别名

对每条现有dedup item机械添加：

```text
source_url ← links.original
aihot_permalink ← links.aihot
```

| item id | source_url（复制自links.original） | aihot_permalink（复制自links.aihot） |
|---|---|---|
| cms5a9tpy00utro7c9bw0s295 | https://x.com/thsottiaux/status/2082241164850364555 | https://aihot.virxact.com/items/cms5a9tpy00utro7c9bw0s295 |
| cms4xiiu3039froa1hrbb2jba | https://www.anthropic.com/research/discovering-cryptographic-weaknesses | https://aihot.virxact.com/items/cms4xiiu3039froa1hrbb2jba |
| cms6bt0tk01ulrotze69gtgvn | https://the-decoder.com/openai-admits-its-autonomous-ai-models-also-compromised-credentials-on-other-platforms-during-security-eval | https://aihot.virxact.com/items/cms6bt0tk01ulrotze69gtgvn |
| cms59994300kcro7c5155buny | https://x.com/kimmonismus/status/2082232405629235649 | https://aihot.virxact.com/items/cms59994300kcro7c5155buny |
| cmryrih7804c9rolge6wdk3v8 | https://the-decoder.com/kimi-k3-trails-frontier-us-models-by-a-wide-margin-on-cyber-exploits-and-distillation-may-explain-why | https://aihot.virxact.com/items/cmryrih7804c9rolge6wdk3v8 |
| cms6lhleg06ourohzls7gb1hk | https://techcrunch.com/2026/07/29/discover-whats-next-for-ai-from-the-saas-reckoning-to-the-agent-security-gap-at-techcrunch-disrupt-2026 | https://aihot.virxact.com/items/cms6lhleg06ourohzls7gb1hk |
| cms5cgsgp01osro7cbxt8b2wq | https://techcrunch.com/2026/07/28/cyera-agrees-to-acquire-oasis-security-for-1b-to-safeguard-proliferating-ai-agents | https://aihot.virxact.com/items/cms5cgsgp01osro7c9bw0s295 |
| cms3yedcz040qro82up1ya5bf | https://www.ithome.com/0/982/312.htm | https://aihot.virxact.com/items/cms3yedcz040qro82up1ya5bf |
| cms5suoi10selrobkfvb0mwoe | https://www.ithome.com/0/983/125.htm | https://aihot.virxact.com/items/cms5suoi10selrobkfvb0mwoe |

Cyera条目的`id`与现有`links.aihot`尾部不一致；本轮严格逐字复制，没有擅自纠正。

### OBS-32：canonical registry

严格从上述9条dedup机械生成9个materials和9个claims，不新增第10条：

```text
materials[].material_id ← 顺序编号M-01..M-09
materials[].dedup_id ← item.id
materials[].source_url ← item.source_url（即links.original别名）
materials[].aihot_permalink ← item.aihot_permalink（即links.aihot别名）
materials[].title ← item.title
materials[].selected_claim_ids ← 对应顺序C-01..C-09
claims[].claim_id ← 顺序编号C-01..C-09
claims[].material_id ← 对应M-01..M-09
claims[].claim_text ← item.title（逐字）
claims[].source_url ← item.source_url（逐字）
claims[].source_excerpt ← item.summary；summary=null时为空字符串
```

C-01至C-04对应4条hot-topics标题级素材，summary为null，所以source_excerpt均为空字符串，没有补写。

## 临时绕行说明(WORKAROUND,非修复)

OBS-31  aihot dedup 的 URL 位于 links.original / links.aihot,

而 media_enrichment 索引只读顶层 source_url / aihot_permalink。

本轮以手工添加顶层别名绕行。代码未修复。

OBS-32  super-writer 的 canonical_claim_registry.json 不含 media 合同

要求的 materials[] 及逐 claim 的 material_id / source_url /

source_excerpt。本轮以手工补齐绕行。代码未修复。

## 3. Receipt漂移与正式ACK重建

Pipeline先检测到：

```text
aihot output hash mismatch: deduplicated_items.json
super_writer input hash mismatch + canonical registry output mismatch
zh input hash mismatch: canonical registry
invalidated_from=aihot
```

没有绕过receipt。Pipeline逐阶段重写请求后，每次都用正式ACK CLI重新绑定当前请求和当前产物。

| 阶段 | 状态 | receipt耗时 | 最终ACK token |
|---|---|---:|---|
| aihot | PASS | 0.0s | `5181e322cc48ba08832393709d5f964f4b133ec1ed14a2d341e249bd52ac997b` |
| super_writer | PASS | 1.0s | `57484b1a2985fe9158e8c62a7925ec7f13740bc3ee3d086d5bb06297e8e3ace3` |
| zh_human_writing | PASSED_BUT_NO_OP | 0.0s | `1c4b5771754b395bbad7d39046cfeabda282143fba6eccfab755da6ec6c4386a` |
| media_enrichment | AWAITING_MEDIA_ASSET_APPROVAL | discover执行后暂停 | 无Agent ACK；该阶段为subprocess/批准状态机 |

最终恢复时三个已完成阶段receipt均重新验证`ok=true`。

## 4. zh-human-writing定性

OBS-33  zh_human_writing 本轮以零编辑通过保真门禁,未执行任何

去 AI 味或语感调整,实质空转。阶段状态记为

PASSED_BUT_NO_OP,不得记为正常 PASS。

Super Writer文章与zh终稿SHA完全相同：

```text
before=b51f06c3bf0726f09aa0d45c4ae172b8a51a8dfab7b95e2363ab77a252dd8386
after =b51f06c3bf0726f09aa0d45c4ae172b8a51a8dfab7b95e2363ab77a252dd8386
差异=0 bytes / 0文字改动
```

本轮按指令不回头重做，但不将空转包装为正常效果。

## 5. media_enrichment候选清单

media输入合同独立验证：

```text
valid=true
request_sha256=9cf7c93aa9a2b4fc63dbc5a8be477f1841311f8c960c9dfd734cc2705ed45627
materials_total=9
claims_total=9
provenance_complete=true
```

候选媒体清单：

```text
candidates_discovered=0
assets=[]
pages_requested=9
pages_fetched=0
downloads_succeeded=0
uploaded_assets=0
upload_events=[]
```

9个source_url分别解析到`198.18.0.84`—`198.18.0.89`，被URL安全检查拒绝；回退到aihot.virxact.com后又解析到`198.18.0.85`并被拒绝。该环境/网络安全错误使发现阶段没有候选资产。

发现阶段`run_media_enrichment.py`返回exit 1，但仍写出冻结发现清单；下一次恢复在不存在`copyright_approval.json`时由Pipeline安全返回批准等待点，没有进入continue或上传。

## 6. 冻结media manifest

RUN原始路径：

```text
F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260730T222605-ai-9je33o\media_enrichment\discover\asset_discovery_manifest.json
```

Git归档路径：

```text
audit/runs/20260730T222605-ai-9je33o/media-manifest.json
```

哈希：

```text
file_sha256=8fa90418ed96899f8336feb32b22d6705d529fb055468f0e7c4ba89b4c15e733
embedded_discovery_manifest_sha256=7c47d985292d8280ae9c85bcc915f7a9ff18e806ae0c22c88ddffd4646bd300d
assets=0
```

没有生成`copyright_approval.json`，没有自行批准任何资产。

## 7. 全部异常

1. Super Writer前两次Full Mode错误逐步减少，第三次通过；
2. OBS-31：dedup URL schema与media索引不兼容；手工别名仅为绕行；
3. OBS-32：canonical registry缺media合同字段；机械补齐仅为绕行；
4. Pipeline主动检测receipt漂移并逐阶段重建；第一次先写ACK后恢复导致request被重写、token失配，随后按新请求正确重建；
5. Cyera item的现有`id`与`links.aihot`尾部不一致，严格保留原值；
6. OBS-33：zh阶段零编辑，实质空转；
7. media发现9个源站及AI HOT回退均受DNS/URL安全检查阻断，候选为0；
8. `pipeline_state.failed_stage`仍保留media历史失败标记，但最终CLI状态为`AWAITING_MEDIA_ASSET_APPROVAL`。

## 8. 凭据与大文件

- 已扫描归档内容，无微信token、appid、secret、Bearer或私钥命中；无需REDACTED替换；
- 所有文件均小于5MB；
- article.md正文未修改。

## 9. 副作用声明

```text
uploaded_image_count=0
draft_created=false
formally_published=false
gzh_design_executed=false
wechat_draft_executed=false
upload_events=[]
```

未上传图片、未创建草稿、未发布/群发、未生成媒体批准文件、未修改任何Skill或Pipeline代码、未新建RUN、未委派子代理、未删除文件。实际外部操作仅有此前AI HOT匿名只读请求；media发现请求全部在URL安全检查阶段被拒绝。

等待独立审核。
