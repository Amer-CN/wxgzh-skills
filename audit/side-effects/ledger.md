# 微信副作用总账(WeChat Side-Effects Ledger)

- 维护位置:`audit/side-effects/ledger.md`;本账登记所有已归档 RUN 的真实微信副作用(HTTP 200 / real_api_call)。
- 数据来源:各 RUN 的 `stages/media_enrichment/upload_events.json`、`stages/wechat_draft/draft_creation_result.json`、`stages/wechat_draft/stage_receipt.json`;事件 RUN 数据经档 35 复核。
- 更新记录:2026-08-02 档 37 首次建账,纳入 4 篇归档 RUN + 事件 RUN `20260801T231452-vibe-coding-guide-v2-1-1vg6jx`;2026-08-03 档 49 追加 RUN `20260802T220853-codex-sol-luna-max-m6pyv4`(5 次 uploadimg,未到草稿)。
- 累计 uploadimg:21 次(2+2+12+5);草稿 #1/#2/#3 共 3 份(本 RUN 未创建草稿)。

## 累计汇总(截至 2026-08-02)

| 类别 | 次数 | 说明 |
|---|---|---|
| uploadimg(图片上传) | 16 | 归档 RUN 4 次(各 2)+ 事件 RUN 12 次(6 张图 × 2) |
| draft/add(草稿) | 3 | 草稿 #1/#2/#3,草稿箱 0→3 |
| 封面 add_material | 3 | 每篇草稿各 1 次 |
| publish / mass_send / scheduled / delete | 0 | 全部 RUN 均为 false |

## 逐 RUN 明细

### RUN 20260731T135947-ai-bbg4al(草稿 #1)
- uploadimg 2 次(2026-07-31T18:18:03Z-18:18:07Z):
  - A-003 `418d841fed238ad485cfc959555d518e5e1d6d005efd35080ce3a9035f2b87cf` → https://mmbiz.qpic.cn/sz_mmbiz_png/Rejn3syibRSbfWzLmlKbZL4CYX31xZ4icCCu90CqiaAS1CyUgj67fvEoxY50Nl6xY28UV2RHpEzyanXxPaicgbst8uJDQaqteUTmL3aiazMdyDgI/0?from=appmsg
  - A-004 `5346d55e5a7478a5e7f21a12060900a912c616664e11a2eb8ee1c8ebc09e5e9c` → https://mmbiz.qpic.cn/sz_mmbiz_png/Rejn3syibRSbcBGdmCK5iaicoXibgakZgB6aG4KsDVxNI4nf9vzlnVNyfUYc25CZ0x8iaBoic1Clueicib3j7xgd522Juv6agicDw6ztQO0KSLqxGiaXs/0?from=appmsg
- 草稿 #1:`title=AI智能体正在重写网络安全攻防`,`content_sha256=5962fc7a…`,`before=0 → after=1`,`real_api_call=true`;封面 add_material 1 次;无发布/群发/定时/删除。

### RUN 20260801T182628-topic-ui5f7p(草稿 #2)
- uploadimg 2 次(2026-08-01T12:16:15Z-12:16:18Z):
  - A-003(同 RUN1 内容 sha `418d841f…`)→ https://mmbiz.qpic.cn/mmbiz_png/Rejn3syibRSY73DEibmyGCA6OcK4LXlmLp04g3ic1Tn42LTxn7IMDxDdluh30yCkP2icLD4OxHO4mxvmEo17TGm9Ajmk9MeNLvqBlzfdH8TT71c/0?from=appmsg
  - A-004(同 RUN1 内容 sha `5346d55e…`)→ https://mmbiz.qpic.cn/sz_mmbiz_png/Rejn3syibRSZBJOyF383He5ibsMqLEvRzbWQXmot0Q0NibR9Q0ib77xZzodAbnvHq4UJw84mEe8gFVykgYcqfg6427CRZYxK80l6TfpqSdgpyac/0?from=appmsg
- 草稿 #2:`title=智能体时代的数据库身份安全`,`content_sha256=d244d271…`,`before=1 → after=2`,`real_api_call=true`;封面 add_material 1 次;无发布/群发/定时/删除。

### RUN 20260801T231452-vibe-coding-guide-v2-1-1vg6jx(草稿 #3,UNCONTROLLED)
- uploadimg 12 次(两轮,6 张唯一图表各 2 次;详见 `audit/runs/20260801T231452-vibe-coding-guide-v2-1-1vg6jx/UNCONTROLLED.md` 与 `media_enrichment/upload_events.json`):
  - 首轮 2026-08-01T15:33:57Z-15:34:02Z:A-001..A-006(补丁前编号),文件 sha 依次 `46d83857…/d52b7b44…/2c441775…/3116603b…/62187244…/065258ed…`(chart-001..006)
  - 二轮 2026-08-01T16:05:02Z-16:05:08Z:A-032..A-037(补丁后编号),文件 sha 与首轮逐字相同(内容重复上传)
  - 12 个返回 URL 均为 genuine mmbiz.qpic.cn(逐条见 `upload_events.json`,此处不重复贴出)
- 草稿 #3:`title=vibe-coding-guide v2.1 升级`,`content_sha256=2f749834e7f391e9673dd4710bfa6c95e006f2e5aa0f1ab357899a8c7afc9979`,`before=2 → after=3`,`update_time=1785600958`,`real_api_call=true`;封面 add_material 1 次(封面=未批准图表 chart-001,sha `46d83857…`);无发布/群发/定时/删除。
- 本 RUN 未经人工批准(零批准合同),归入 UNCONTROLLED,见归档目录声明。

## 附注

- OBS-60:同内容跨 RUN 重复上传产生第二份永久素材副本(A-003/A-004 在 RUN1/RUN2 各产生新 URL);事件 RUN 另在同 RUN 内对 6 张图表重复上传(去重键为 asset_id,两轮编号不同未命中)。
- 本账仅登记事实,不替代各 RUN 的 stage receipt 与证据文件。

### RUN 20260802T220853-codex-sol-luna-max-m6pyv4(档49 续跑,media 阶段失败,未到草稿)
- uploadimg 5 次(2026-08-03,人工批准合同 AP-20260803T194207-INDEPENDENT-REVIEW-001,6 张批准中 5 张合格):
  - A-110 `0b873fce422558c2b1fec4f916d833282b0f0b96833e7c75bc9110868c8ff3b3` → https://mmbiz.qpic.cn/mmbiz_jpg/Rejn3syibRSZnqFYRqZ0XIe4bRHdkbbMmrjJYIqHPUTrnvkeZdIdCnOPnlZWMgia7LfFHQr2j8ibbrD93FxLj6EiaUekmdwrhxn28y1iaXGkBhJA/0?from=appmsg
  - A-111 `27460e245edde1a52e6d293e24e0846a52a6387f2a6e561c0db82c4468d71d97` → https://mmbiz.qpic.cn/mmbiz_jpg/Rejn3syibRSZuncfvq9hzXXALSKuicso4jiaSkEqGUrJrZfcZC7ad6FIBsroLvNgZHvH9e9K5T3Walarlpz8sDjnTqBkU4dNlFwwXHH6g57dno/0?from=appmsg
  - A-112 `81f3e427ceca2c3295a6aef6bbf281a1501693b82246d226e1c6bda68d596c4f` → https://mmbiz.qpic.cn/sz_mmbiz_jpg/Rejn3syibRSajdk0vpEB23YHichbs8LuPV01EjGYoxxnjwUDoXiat2CREC3icPRtNVSJcy3vFvXeIlyCVCu6OT5TcIZY396lvLjzvgjlSFk3QjI/0?from=appmsg
  - A-113 `6ba9dc545a1a2478008fc0af291f9d423bc8c01cfdf25704a3a7ce94facde2d0` → https://mmbiz.qpic.cn/sz_mmbiz_png/Rejn3syibRSYwP35SNQjIPTe9MYaNznkbXRxUtibmLiapj6DuutU8rgUHDDaP9cWSk54vMjzicjMN2iazqh7YsRAGjsTWZaWoiaYEnkupg3tgMdia8/0?from=appmsg
  - A-114 `8680b39c821cf8b62078fa36de8b4e506def1357ba4740cf81f0d73af974ee6a` → https://mmbiz.qpic.cn/mmbiz_jpg/Rejn3syibRSZPeGcQpNUtL8wxnCkx8iaABcRcwe0CYYlLuWVvRF1ElpoB7icTEbf0UiamRNq0cgPnBdkBI4icezBgX9VJWcwwpkwp7xoyGqvmibNg/0?from=appmsg
- A-107(已批准)因 `dimensions 100x100 below minimum 640x360` 被 continue 阶段 rejected,未上传;
- 绑定 5 张 < body_images_min=6 → MEDIA_BINDINGS FAIL → 阶段失败停机;
- 未创建草稿;草稿箱仍 3 份;无发布/群发/定时/删除;无封面 add_material;无图表生成(claims 无数字,warning 记录)。
