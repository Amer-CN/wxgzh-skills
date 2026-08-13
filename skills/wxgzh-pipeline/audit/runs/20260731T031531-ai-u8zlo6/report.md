# 阶段11 · 档14R7 · 重跑媒体发现报告

## 最终状态

```text
RUN_ID=20260731T031531-ai-u8zlo6
RUN_DIR=F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260731T031531-ai-u8zlo6
STATUS=AWAITING_MEDIA_ASSET_APPROVAL
completed_stages=[aihot, super_writer, zh_human_writing]
current_stage=media_enrichment
gzh_design_executed=false
wechat_draft_executed=false
uploaded_image_count=0
draft_created=false
formally_published=false
```

最终CLI在批准点停机，三个已完成阶段receipt验证均`ok=true`。`pipeline_state.failed_stage=media_enrichment`为第3次discover返回exit 1时留下的历史字段，不改变最终CLI等待状态。

## 1. 六条nslookup原始结果

```text
服务器:  smartdns
Address:  fe80::1

名称:    techcrunch.com
Addresses:  2a04:fa87:fffd::c000:42dc
          192.0.66.220

服务器:  smartdns
Address:  fe80::1

名称:    www.anthropic.com
Addresses:  2607:6bc0::10
          160.79.104.10

服务器:  smartdns
Address:  fe80::1

DNS request timed out.
    timeout was 2 seconds.
名称:    the-decoder.com
Address:  185.185.24.14

服务器:  smartdns
Address:  fe80::1

名称:    opencdnv6.jomodns.com
Addresses:  2409:8c70:3a91:61::6f14:fe23
          111.20.254.35
Aliases:  www.ithome.com
          www.ithome.com.a.bdydns.com

服务器:  smartdns
Address:  fe80::1

名称:    x.com
Address:  162.159.140.229

服务器:  smartdns
Address:  fe80::1

名称:    aihot.virxact.com.eo.dnse2.com
Addresses:  117.187.145.164
          183.230.68.100
Aliases:  aihot.virxact.com
```

六个目标域名最终均返回真实公网IP，没有`198.18.0.0/15`。`the-decoder.com`出现一次2秒超时提示，但随后返回`185.185.24.14`。

## 2. 重新发现路径与理由

只读检查Pipeline代码后确认，当前RUN没有原生重新发现路径：

- `discover/asset_discovery_manifest.json`不存在时才执行discover；
- 文件存在且无`copyright_approval.json`时只返回批准等待；
- 文件存在且有批准时进入continue；
- 没有`rediscover`、`refresh`参数或命令；
- media尚未完成，没有receipt可用receipt漂移重建。

按指令不得删除或改写旧冻结清单，因此没有操作旧RUN，改用相同选题启动本全新RUN。

## 3. AI HOT与阶段状态

本轮重新检索：

```text
hot-topics: HTTP 200, count=4, 采用Codex安全条目1条
selected&q=智能体安全&window=7d&limit=10: HTTP 200, count=0
all&q=智能体安全&window=7d&limit=10: HTTP 200, count=8
raw=9, deduplicated=6
```

微软MAI-Cyber-1-Flash/MDASH四条同事件报道保留主条目1条，另3条登记为重复ID。

| 阶段 | 状态 | receipt耗时 | ACK token |
|---|---|---:|---|
| aihot | PASS | 1.0s | `d794fba00828fa362095ac969ed2a4072481ee65376920dbdc8808dd88636ffc` |
| super_writer | PASS | 1.0s | `7397d47e30da57244b20dee783277aa349ebe226c19a0ca935af3a680b39dd0c` |
| zh_human_writing | PASS_WITH_REAL_EDITS | 0.0s | `120f0413b976130a663f682469fc133cab75bc9009cc5d0dc3053a03c1182215` |
| media_enrichment | AWAITING_MEDIA_ASSET_APPROVAL | discover尝试300s+300s+约82s | 无Agent ACK；subprocess批准状态机 |

Super Writer第一次Full Mode仅4条章节预算错误；机械调整outline/length policy后第二次`passed=true`，正文未为门禁改写。

zh阶段不是零编辑：两句模板化表达做最小调整。首次保真检查提示否定/条件词变化，局部恢复后复验为13/13通过、0失败、0警告、protected span变化0；终稿SHA=`750c56de75a1c542a301264d20efaa8fc6c7be1d550a71dd455fbddbca98af21`。

## 4. media发现概况与gate

前两次正式discover均在300秒超时，且没有生成冻结manifest。等待5秒后第3次重试运行约82秒，成功写出发现产物但入口返回exit 1。

```text
candidates_discovered=33
pages_fetched=1
pages_requested=6
downloads_succeeded=0
eligible_assets=0
review_required_assets=0
rejected_assets=33
uploaded_assets=0
upload_events=[]
```

Gate：

```json
{
  "input_contract_pass": false,
  "provenance_complete": true,
  "publish_allowed": false,
  "secrets_detected": false,
  "security_checks_pass": false
}
```

系统`nslookup`已经返回公网地址，但media子进程内的域名解析仍不同：5个非X材料源在运行时落入`198.18.0.6`—`198.18.0.9`并被安全检查拒绝；X页面成功抓取1页，提取33个`pbs.twimg.com`图片URL，但该图片域名随后解析失败或落入`198.18.0.5`，33项全部被正确拒绝。未绕过或放宽URL安全检查。

## 5. 候选资产完整清单

说明：这里的“发现候选”是发现器列出的33个图片URL；由于安全检查全部拒绝，可供批准的eligible/review-required资产为0。尺寸因未下载均为`None×None`，版权均`unknown/high`。

| ID | 来源域名 | 图片域名 | 图片URL | 尺寸 | 版权 | 决策 | 原因 |
|---|---|---|---|---|---|---|---|
| A-001 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075819673263001600/pj1vyX6I_normal.jpg | None×None | unknown/high | rejected | URL security: DNS resolution failed for hostname: pbs.twimg.com |
| A-002 | x.com | pbs.twimg.com | https://pbs.twimg.com/card_img/2082316514892668928/hlE3U-ag?format=jpg&name=orig | None×None | unknown/high | rejected | URL security: DNS resolution failed for hostname: pbs.twimg.com |
| A-003 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075290056084844544/rbW_BzIG_normal.jpg | None×None | unknown/high | rejected | URL security: DNS resolution failed for hostname: pbs.twimg.com |
| A-004 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2077181974762942464/absf3ae4_normal.jpg | None×None | unknown/high | rejected | URL security: DNS resolution failed for hostname: pbs.twimg.com |
| A-005 | x.com | pbs.twimg.com | https://pbs.twimg.com/tweet_video_thumb/HOWcIvcWMAAVxwi.jpg | None×None | unknown/high | rejected | URL security: DNS resolution failed for hostname: pbs.twimg.com |
| A-006 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075546952041717760/XkXN2jDT_normal.jpg | None×None | unknown/high | rejected | URL security: DNS resolution failed for hostname: pbs.twimg.com |
| A-007 | x.com | pbs.twimg.com | https://pbs.twimg.com/media/HOYGMeoXYAACIFh?format=webp&name=medium | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-008 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075819673263001600/pj1vyX6I_mini.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-009 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075819673263001600/pj1vyX6I_bigger.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-010 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075819673263001600/pj1vyX6I_x96.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-011 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075819673263001600/pj1vyX6I_reasonably_small.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-012 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075819673263001600/pj1vyX6I_200x200.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-013 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075819673263001600/pj1vyX6I_400x400.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-014 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075290056084844544/rbW_BzIG_mini.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-015 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075290056084844544/rbW_BzIG_bigger.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-016 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075290056084844544/rbW_BzIG_x96.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-017 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075290056084844544/rbW_BzIG_reasonably_small.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-018 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075290056084844544/rbW_BzIG_200x200.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-019 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075290056084844544/rbW_BzIG_400x400.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-020 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2077181974762942464/absf3ae4_mini.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-021 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2077181974762942464/absf3ae4_bigger.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-022 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2077181974762942464/absf3ae4_x96.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-023 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2077181974762942464/absf3ae4_reasonably_small.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-024 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2077181974762942464/absf3ae4_200x200.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-025 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2077181974762942464/absf3ae4_400x400.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-026 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075546952041717760/XkXN2jDT_mini.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-027 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075546952041717760/XkXN2jDT_bigger.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-028 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075546952041717760/XkXN2jDT_x96.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-029 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075546952041717760/XkXN2jDT_reasonably_small.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-030 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075546952041717760/XkXN2jDT_200x200.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-031 | x.com | pbs.twimg.com | https://pbs.twimg.com/profile_images/2075546952041717760/XkXN2jDT_400x400.jpg | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-032 | x.com | pbs.twimg.com | https://pbs.twimg.com/media/HOYGMeoXYAACIFh?format=webp&name=small | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |
| A-033 | x.com | pbs.twimg.com | https://pbs.twimg.com/media/HOYGMeoXYAACIFh?format=webp&name=large | None×None | unknown/high | rejected | URL security: DNS resolves to blocked IP: 198.18.0.5 for hostname pbs.twimg.com |

完整机器可读清单：`stages/media_enrichment/candidate_audit_summary.json`。

## 6. 冻结manifest

RUN路径：

```text
F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260731T031531-ai-u8zlo6\media_enrichment\discoversset_discovery_manifest.json
```

Git路径：`audit/runs/20260731T031531-ai-u8zlo6/media-manifest.json`

```text
file_sha256=8fa90418ed96899f8336feb32b22d6705d529fb055468f0e7c4ba89b4c15e733
embedded_discovery_manifest_sha256=7c47d985292d8280ae9c85bcc915f7a9ff18e806ae0c22c88ddffd4646bd300d
frozen_assets=0
```

冻结清单为空，因为33个发现URL全部在安全检查阶段被拒绝。没有生成`copyright_approval.json`。

## 临时绕行说明(WORKAROUND,非修复)

- OBS-31：AI HOT输出继续机械增加`source_url ← links.original`与`aihot_permalink ← links.aihot`顶层别名。media索引schema不兼容仍未修复。
- OBS-32：canonical registry的6个materials/claims继续从6条dedup机械生成；字段逐字复制，Codex的null summary对应空source_excerpt。代码未修复。
- 本轮zh执行了真实非零编辑，不触发OBS-33。

## 7. 异常记录

1. `the-decoder.com`的nslookup先超时一次，随后返回公网IP；
2. 原RUN没有合法rediscover机制，因此新建RUN；
3. Super Writer首次预算门禁失败，第二次通过；
4. zh首次保真审计出现3条否定/条件词警告，局部回滚后0警告通过；
5. media前两次discover各超时300秒；第3次生成产物但exit 1；
6. 系统nslookup与media子进程的DNS解析结果不一致，media内仍出现`198.18.0.x`；
7. 33个pbs.twimg.com URL全部安全拒绝，最终可批准资产为0；
8. `pipeline_state.failed_stage`保留media历史失败字段，但最终CLI为批准等待点。

## 8. 凭据、大文件与图片

- 已扫描全部产物，无微信token、appid、secret、Bearer或私钥命中；无需REDACTED；
- 所有提交文件均小于5MB；
- 未提交任何图片文件，只提交图片URL与清单。

## 9. 副作用声明

```text
uploaded_image_count=0
upload_events=[]
draft_created=false
formally_published=false
gzh_design_executed=false
wechat_draft_executed=false
```

未上传图片、未批准资产、未创建微信草稿、未发布/群发、未修改Skill或Pipeline代码、未删除或改写旧冻结清单、未委派子代理、未用本地图片或训练记忆伪造发现结果。

等待独立审核。
