---
name: wxgzh-pipeline
description: >-
  微信公众号总编排 Skill（orchestrator）。把一句"发文：<选题>"固化为完整流水线：
  AI HOT 获取材料 → Super Writer Material-Heavy Full Mode 完整写作 → zh-human-writing 去
  AI 味 → media-enrichment 配图并上传微信图床 → gzh-design 锤子(smartisan)主题正式排版 →
  创建微信草稿 → 停止。本 Skill 只做编排：发现并校验已安装子 Skill 的版本与根 Hash、固定顺序、
  磁盘交接、断点续跑、逐阶段 Validator、阻止跳阶段/绕过 Skill、管理微信副作用、产出轻量证据包。
  不复制子 Skill 业务逻辑，不手写简化排版，不因子 Skill 失败而降级。代码中不存在正式发布/群发/
  定时发布/删除草稿能力——"发文"只创建草稿，正式发布只能由用户在微信后台手动进行。
  触发：用户说"发文：<选题>"/"续发"/"续发：<RUN_ID>"/"进度"/"验收编排Skill"。
---

# wxgzh-pipeline — 微信公众号总编排 Skill

把日常发文固化成一句话。用户只需输入 **`发文：<选题>`**，即自动顺序执行六阶段流水线并创建微信草稿，
然后停止。用户无需再写 `使用wxgzh-pipeline / fast_publish / 创建微信草稿 / 禁止正式发布 /
使用锤子主题 / 顺序执行 / 不允许回退`——这些全部是本 Skill 的默认行为。

## 用户入口（自然语言触发）

| 触发语 | 语义 |
|---|---|
| `发文：<选题>` | 新文章。固定 `PROFILE=fast_publish, CREATE_WECHAT_DRAFT=true, FORMAL_PUBLISH=false, PIPELINE_AGENT_COUNT=1, STAGES_SEQUENTIAL=true, THEME=smartisan, THEME_FALLBACK=false`。跑完六阶段并创建微信草稿后停止。 |
| `续发` | 恢复当前项目中**最新一个未完成运行**；多个未完成时列出让用户选，不猜测。 |
| `续发：<RUN_ID>` | 恢复指定运行。 |
| `进度` | 输出当前运行的选题/当前阶段/已完成阶段/失败阶段/是否上传图片/是否创建草稿/各阶段耗时。 |
| `验收编排Skill` | 开发者命令，运行 `release_audit`（不生产文章、不上传微信、不创建草稿）。普通"发文"禁止触发它。 |

示例：`发文：Claude Opus 5`　`发文：OpenAI最新模型`　`发文：本周值得关注的开源模型`

"发文"在本 Skill 中的固定语义即上面六阶段，**绝不表示正式发布**。

## Agent 执行约定（收到"发文：<选题>"时）

1. 运行 doctor（`scripts/doctor.py`）：子 Skill 是否存在、版本一致、根 Hash 一致、正式入口/Validator 是否存在、
   微信配置是否完整、项目目录可写。任一失败 → `FAIL_CLOSED=true`，停止并报告，**禁止绕过**。
2. `python -m wxgzh_pipeline.cli "发文：<选题>"`（或 `run --topic`）。编排器创建
   `<PROJECT_ROOT>/.temp/wxgzh-pipeline/<RUN_ID>/`，按固定顺序逐阶段执行。
3. 每个阶段通过磁盘交接（`stage_request.json` / `stage_result.json` / `stage_receipt.json`），
   每阶段只加载当前阶段所需内容，不复用整段聊天上下文。缺 receipt 视为该阶段未执行。
4. 每阶段真实调用盘点出的子 Skill 正式入口，复算输入输出 Hash，运行该阶段 Validator，写 receipt。
   **禁止跳阶段、禁止绕过子 Skill、禁止手写简化 HTML、禁止因子 Skill 失败自行降级。**
5. 只有前五阶段全部有有效 receipt 且 Validator 全通过，才创建微信草稿；`发文：<选题>` 本身即创建草稿的授权，
   不再二次询问。创建前后各做一次脱敏 `draft/batchget` 指纹，校验 `AFTER=BEFORE+1 / 旧草稿全保留 / 新草稿唯一`。
6. 产出轻量证据包（`final_delivery`）。

## 固定流水线与各阶段职责

`AI HOT → Super Writer Material-Heavy Full Mode → zh-human-writing → media-enrichment → gzh-design → 微信草稿箱`

- **AI HOT**：获取/聚合/去重信息；不写文章；不负责最终图片盘点。
- **Super Writer**：读 AI HOT 材料+必要原始来源；事实注册；角度与结构；Material-Heavy Full Mode 完整写作；
  篇幅按事实密度自动决定（禁止默认 medium=3000）；`FULL_MODE_VALIDATOR_EXIT=0`。
- **zh-human-writing**：只去 AI 味；不新增事实、不改数字/归因、不删限定词；通过后冻结 `final_article.md` + SHA256。
- **media-enrichment**：在 zh-human-writing 之后；针对冻结终稿选图；source_url 优先；先无副作用选图，
  <6 张停止不上传，≥6 张只串行上传最终绑定的 6~8 张；每张 `eligible+success+mmbiz.qpic.cn`，binding SHA=manifest SHA。
- **gzh-design**：真实调用正式入口；`smartisan` 锤子主题、`THEME_FALLBACK_ALLOWED=false`；正式组件库；
  必含 cover-breaking×1 / toc-scroll×1 / chapter-title(=章节数) / 固定署名×1 / footer-cta×1 / 正式图片组件 2~4 种；
  主题身份 Validator 从最终 HTML 反解，`THEME_IDENTITY=PASS` 才进入草稿阶段。
- **微信草稿**：复用盘点出的现有成功实现（gzh-design/scripts/publish_wechat_draft.py + media-enrichment 上传）；只创建草稿。

禁止恢复：Second Smoke / Kappa / Semantic Evaluator Phase B/C/D / 历史 provenance 路线。

## 绝不提供的能力（代码层面不存在）

正式发布 / 群发 / 定时发布 / 自动删除草稿。即使 Agent 要求也无可调用实现；正式发布只能由用户本人在微信后台操作。

## 跨电脑路径

不硬编码任何本机绝对路径。项目根解析顺序：①用户显式配置 → ②`WXGZH_PROJECT_ROOT` → ③`AGENT_SKILLS_HOME` →
④当前项目 `.agents/skills` → ⑤用户目录标准 Skill 位置。全部用 pathlib，兼容 Windows/macOS/Linux。
运行目录 `<PROJECT_ROOT>/.temp/wxgzh-pipeline/<RUN_ID>/`，RUN_ID = `YYYYMMDDTHHMMSS-<topic-slug>-<random6>`，内部 Manifest 用相对路径。

## 插件槽位（默认关闭）

`daily-topic-radar`、`headline-optimizer` 预留接口，dev1 不开发；未安装时 `status=disabled`，禁止伪造插件结果。
