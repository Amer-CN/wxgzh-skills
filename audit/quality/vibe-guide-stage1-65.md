# 档 65 第一段 — vibe-coding-guide 续跑至媒体批准点(停机等待裁决)

- RUN_ID:`20260804T163519-vibe-coding-guide-v2-1-6-7atsk0`
- 状态:**已到媒体批准点,可批准候选 0 < body_images_min=6,按第 11 条停机上报,
  等用户裁决,不继续 continue。**
- 本段副作用:零 uploadimg、零 add_material、零草稿、零发布、零微信调用。

---

## 第一步 zh_human_writing(fidelity 全过)

- `fidelity_guard.py`(官方校验器,exit 0):**13/13 全过,0 fail,0 warning**
  (数字/日期/URL/命令/路径/引号等字面比对逐项保留;首次试跑因「如果」条件词
  计数 6→5 触发 WARN(exit 1),已恢复结尾原文后重验 13/13)。
- `pattern_audit.py` exit 0;`change_report.py` exit 0。
- 六项 gates(内容校验器):`NEW_UNREGISTERED_FACTS/NUMBER_CHANGES/
  ATTRIBUTION_LOSS/QUALIFIER_LOSS/CLAIM_SEMANTIC_CHANGE/HARD_RESIDUE`
  首跑输出全 0;首跑整体 FAIL 的唯一原因是 **zh-human-writing 禁词表命中
  「Agent」×2**(正文含「description 是 Agent 判断…」与素材引用的组名
  「Agent 操作安全」)——按去 AI 味职责替换为「AI 客户端判断…」「AI 代理
  操作安全」(语义不变,已写入 edit_summary),重跑 exit 0。
- 修改范围:仅 `final_article.md` 三处文字微调;`super_writer/article.md`
  (fidelity 基准)零改动;冻结 sha 未变。

## 第二步 文章形态取证(只报告,未修改)

| 取证项 | 结果 |
|---|---|
| ⛔ 拦截文本 | 文章 **0 处**(guard-bash.sh 素材本身也无 ⛔ 字符) |
| `/plugin` 出现 | 文章 1 处,为行内文本「(/plugin disable vibe-coding-guide)」(_common.sh 关闭方法),非命令块 |
| fenced code block | **0 个**;反引号 **0 个** |
| 文章结尾两行安装命令 | 文章**未包含** `/plugin marketplace add Amer-CN/vibe-coding-guide` 与 `/plugin install vibe-coding-guide@vibe-coding-guide`;两行命令存在于素材 `install.sh`(原文 `echo "       /plugin …"`,**7 空格缩进**),未进入文章 |

- 结论:文章无代码块形态需要裁决;若后续要呈现两行安装命令,形态(缩进/代码块)待裁决。

## 第三步 media discover(止于批准点)

- 4 个网页全部抓取成功;**候选 4 张,全部来自 GitHub blob 页的 og:image(仓库
  社交卡),3 张为同一 og 图的重复(精确 sha 去重),全部 rejected**;正文抓图
  候选 **为零**——与档 62 前瞻结论一致(GitHub 素材页无正文图),非异常。
- **自生成图表:0 张**(注入素材的 claims 无 numbers/chart_group——四份素材为
  shell 脚本与 CHANGELOG,无结构化数字;图表零生成是正确行为,非故障)。
- `approval_readiness.json` 完整内容(第 7 条):

```json
{
  "schema_version": "1.0",
  "run_id": "20260804T163519-vibe-coding-guide-v2-1-6-7atsk0",
  "discovery_manifest_sha256": "",
  "gate": {"content_description_required": true, "page_position_required": true,
           "claim_derived_text_never_accepted": true},
  "assets": [
    {"asset_id": "A-001", "decision": "rejected",
     "content": {"kind": "empty", "description": "内容不明(无任何内容描述)",
                 "source": null, "verified": false},
     "page_position": {"known": false, "heading": null, "level": null},
     "approvable": false,
     "approvable_blockers": ["decision=rejected — 非可批准状态,不得写入批准合同",
                             "缺少可验证内容描述(empty)", "页面位置未知"]},
    {"asset_id": "A-002", …同 A-001(og 图重复)…},
    {"asset_id": "A-003", …同 A-001(og 图重复)…},
    {"asset_id": "A-004", …同 A-001(og 图重复)…}
  ],
  "summary": {"total": 4, "approvable": 0, "blocked": 4}
}
```

- 逐张汇总(第 7 条字段):A-001..A-004 全部 `asset_origin=source /
  extraction_method=og:image(或 exact sha duplicate)/ decision=rejected /
  content_description 无(empty)/ source null / page_region=unknown /
  page_position 未知 / 拟绑定章节无 / 尺寸:仅 A-001 有 1774×887,其余未检 /
  sha256=a7174fd0e12b5e51…(四张同内容)/ copyright_status=unknown /
  copyright_risk=high / approvable=false`。
- 第 8 条(图表逐张):**无图表可列**(零生成)。
- 第 9 条:网页抓图候选 **4**(全 og 卡,0 可批准);自生成图表 **0**。

## 第四步 数量门槛前置判断(第 10/11 条)

- `body_images_min=6`、`max_total_images=8`;**可批准候选 = 0**。
- ★**不足 6 张:按指令停机上报,等裁决**。未降阈值、未为凑数批准任何资产、
  未手工补字段。这是技术文媒体形态的内容问题(vibe-coding-guide 素材页无正文
  图、素材无数字图表),不是流程问题——裁决方向(文章类型区分媒体要求/代码块
  形态/图表数据点补充)由用户决定。

## 顺带修复:Pipeline discover 失败残留判定缺口

- 现象:首次 discover 因 1 个页面抓取 SSL 瞬时失败 exit 1,但 frozen manifest
  已落盘;resume 时 `_media_two_phase` 只按 `frozen.is_file()` 判定「已暂停」,
  导致跳过 discover 且**不生成 approval_precheck/approval_readiness**,直接进入
  批准点(信息不完备)。
- 修复(`wxgzh_pipeline/producers.py`):discover 暂停有效条件改为
  `frozen + approval_precheck + approval_readiness 三者齐备`;残留即重跑 discover。
- 影响:档 61/62/63/64 语义未改;修复后本 RUN discover 重跑成功并生成
  readiness(见上)。

## 第五步 复核

- 副作用:零 uploadimg、零 add_material、零草稿、零发布(discover 阶段 4 次
  图片文件下载为本地落盘,非微信上传)。
- lock 双侧 `81F9342A617893FBE3C51C4FCDCFFCB89E76D43EE4735F5FDB81B6422B951058`
  未变;台账仍 7 条;四锁 hash_ok 全 true;doctor PASS(安装侧已同步
  producers.py 修复,OBS_68 MATCH)。
- 阶段状态:aihot / super_writer / zh_human_writing receipt 全部 OK;
  media_enrichment 停在 AWAITING_MEDIA_ASSET_APPROVAL(gzh_design/wechat_draft
  未执行)。

## 变更文件

- `wxgzh_pipeline/producers.py`:discover 失败残留判定(1 处)
- `audit/quality/vibe-guide-stage1-65.md`(本报告)
