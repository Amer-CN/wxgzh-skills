# OBS-378/379 —— 77AB aihot 域名双前缀+40164 探针验收报告（字节级落盘）

- 档号：77AB（aihot 域名双前缀适配 + 40164 上传前探针）。
- 授权：RELOCK_ALLOWED 临时 0→1（批准人=用户，范围=media-enrichment scripts+wxgzh-pipeline producers/契约；pipeline 无锁条目）；GZH 维持 0。授权登记行随 feat 落账（序数按台账实况=四十九次，77AA 已占四十八）。
- feat 提交：607f3ea（22 文件）；后续连带：b944486（生产 hits 回流）。
- 证据 RUN：x7fm2q（5/5 aihot.news 域入册，验收漏检）/m9coc1（301 后撞单前缀门致执行端全链改写域名留痕；40164 upload_events 11 事件，errmsg 含出口 IP 183.221.7.130）。

## 1. 任务 0 坐实（存档）

- 三处前缀判定各写一份：producers.py:327（77Y/OBS-373 冒充门）、run_media_enrichment.py:1293（internal_page/分类器）、input_contract.py:169+validate_media_manifest.py:175（REQUEST_MATERIAL_PERMALINK_LANE 分流）。
- 两 RUN 域形态：x7fm2q 5/5 news、m9coc1 20/20 virxact（301 后 aihot.news 撞单前缀门）。
- token 获取点=uploader.py:251 `_get_access_token`（_last_token_observation 结构现成可复用）。

## 2. 两件实现（OBS-378/379）

- **378 双前缀**：单一真源常量 `AIHOT_SITE_PREFIXES = ("https://aihot.virxact.com/", "https://aihot.news/")`——media 侧落 url_security.py、pipeline 侧落 producers.py（两子树无法共享 import，**双文一致守卫测试钉住**，77W 先例）；三处判定+错误文案全改双前缀；明规=记录层禁止改写上游返回域名（media SKILL.md 绝对约束第 10 条+pipeline aihot 指令），门的职责是兼容不是倒逼改写。测试：media 7 绿+pipeline 6 绿（含双文一致守卫）。
- **379 探针**：uploader `probe_token()`（复用 _get_access_token 结构、不缓存、errmsg 正则解析出口 IP、_scrub_token）；run_media 批量上传循环前挂探针（live 才探、非 live 跳过）；40164→FAIL_CLOSED（文案含 IP+mp 后台「设置与开发→基本配置→IP 白名单」指引+「零张上传」）；非 40164 走既有错误路径不误伤；探针观测照 _last_token_observation 形状入 upload_events.json `token_probe` 留痕。测试 3 绿（命中停机/正常过/异常不误伤）。

## 3. 干跑验收实证（档文要求原文）

- x7fm2q 冻结 dedup 新 producers 门干跑：`violations: [] / RESULT: PASS`——**5/5 条目 aihot.news 原值全过**（旧单前缀门全拦，改写需求根除）。
- mock 40164 实跑（真 main+真 probe_token，仅 mock 传输层）：

```text
continue exit code: 1
ERROR: 77AB/OBS-379: 微信上传 IP 白名单拦截(40164)——出口 IP 183.221.7.130，请到微信公众号后台「设置与开发→基本配置→IP 白名单」加入该 IP 后重跑;探针拦截于批量上传前,零张上传。errmsg 原文: invalid ip 183.221.7.130 ipv6 ::, not in whitelist, request from 183.221.7.130
upload_events.json: {"schema_version":"1.0","serial":true,"events":[],"token_probe":{"http_status":200,"wechat_errcode":40164,...,"ok":false,"errcode":40164,"ip":"183.221.7.130"}}
requests.post uploadimg calls: 0
```

- 防冒充不放松：aihot.news 与 virxact 站内页填 links.original 均 FAIL（2 violations 各含条目 id）。

## 4. 过程事件（如实）

1. **executor 相对 import 自愈**：input_contract 初版相对 import 在 pipeline `spec_from_file_location` 加载下 41 红，改绝对 import 后归零（media 全套不受影响）。
2. **授权行序数更正**：77AA 已占四十八次，77AB 按台账实况写四十九次（简报模板 48 为过时快照）。
3. **relock media 首跑被 doctor gate 拒**：super-writer hash_ok=false——**定性=77AA 把 references/title-hits.md（生产数据台账）纳入锁 runtime 覆盖面，生产 RUN（m9coc1）追加行致装机侧 hash 漂移**（源码侧 root==锁基线，dry-run 实证）。处置=生产 hits 行回流源码侧入册（title-hits 首次生产回流）+77AA-F 锚点测试两 pattern 行同步装机侧+sw 升 0.4.21-rc2+MANIFEST 重算（119 条目全过）→ 独立 commit b944486 → relock **#110 sw**（gate 判「target hash/version mismatch only, re-lockable」）+**#111 media dev34** 双 apply 全链 PASS。**根治（title-hits 移出锁面/加白名单）系结构裁决，本档不扩案，留审核方**。
4. obs304 钉子 259→261/119–379+obs288 白名单 77AB/OBS-378+README 版本表（sw 0.4.21-rc2/ media dev34/9R31，含 77AA 欠账 sw 0.4.21）均随主智能体回归轮完成，test_hf76r 19 绿。

## 5. 升版/锁链/回归（77Y-F 新规：回归在 relock 后）

- 升版：media dev33→**dev34**；pipeline 9R30→**9R31**（release_date 2026-09-10）；sw 0.4.21-rc1→**rc2**（回流连带）。
- relock **#110 sw**（20260910T135318Z-d76aa1ee）+**#111 media**（20260910T135340Z-15d96697），远端见证 a/b/c PASS（--source-commit b944486），apply 全链 PASS，备份×2 在册。
- 新锁 sha：`04a951e3…→354b7c39ba419c34595e1d0d7d8c864df9982c693c6f06a10bfe19416746f6a6`，R93 双侧一致。
- doctor：双侧 PASS、OBS_69/OBS_68 双侧 MATCH。
- **最终回归（relock 后）**：唯一红=obs154×1 既有红，零新红；relock dry-run ×4 无变化 OK。

## 6. 程序校验

- 唯一编号：`261 119 379 True`
- R59：`main=21 partition_active=21` 双差集空
- 授权登记行：恰 1 行（四十九次）；更正附记（x7fm2q 验收漏检）在册口径 94

## 7. 基线链

`efc4cd2（77AA-F）→ 607f3ea（feat 77AB）→ b944486（fix hits 回流+sw rc2）→ <docs 本报告+锁链>`
