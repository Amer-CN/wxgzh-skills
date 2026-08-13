# OBS-56 Stage Failure Observability Diagnosis

## 档20阶段A摘要
- OBS-55撤回：`stage_request.skill_name=gzh-design`是`wechat_draft`复用gzh-design发布模块的执行Skill/锁身份映射；Pipeline按`STAGE_MODULES[stage]`分发。
- OBS-57撤回：真实RUN中存在`gzh_design/final.html`，SHA为`5962fc7a10e303dfc3e33b835a3ef0e83eb4b75f12f6a6c0ff49cec108df6800`；请求相对路径解析一致。
- OBS-56成立：历史失败时`meta.entry_run`未落盘，原始stdout/stderr/elapsed不可取得。

## 阶段C封面验证
### C-1
`gzh-design/scripts/publish_wechat_draft.py:519-531`声明`--cover`和`--thumb-media-id`均非argparse必填；`545-549`仅在传`--cover`时检查文件；`574-577`有`--audit-dir`则进入audit并return；`579-582`的缺封面exit只作用于非审计模式。
### C-2
同文件`239-253`始终写`thumb_media_id`。audit真实模式在`481-492`中从`args.cover`上传所得或`args.thumb_media_id`取值；二者都没有时为`None`，无默认值或占位。
### C-3
`wxgzh_pipeline/producers.py:818-827`参数仅为`--html/--title/--audit-dir`，live不传`--cover`或`--thumb-media-id`。
### C-4
微信官方新增草稿文档：`POST /cgi-bin/draft/add`；`Body.articles.thumb_media_id`表面字段标记“否”，但说明明确“article_type为图文消息(news)时必填，必须是永久MediaID”。当前脚本未设置article_type，官方说明其默认news。
### C-5
结论：`证据不足`。封面是当前news请求的必填条件，但历史exit=1原文不可取得，且预检也可能先失败；不能在第1次新观测前认定封面就是历史根因。条件封面授权尚未生效。

## 测试
- OBS56定向：3 passed。
- media：289 passed, 6 skipped, 0 failed。
- Pipeline：144 passed, 1 skipped, 13 failed；13项均为safe-delete保护或OBS-52缺`.git`夹具，新增OBS56断言无代码失败。
