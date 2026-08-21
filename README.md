<p align="center"><img src="https://capsule-render.vercel.app/api?type=waving&color=0:B3593B,100:7A2E1D&height=170&section=header&text=wxgzh-skills&fontSize=64&fontColor=ffffff&animation=fadeIn" width="100%"></p>

<div align="center">

#### 一句话发公众号：从选题到草稿箱的全自动 AI 流水线

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=20&pause=1200&color=B3593B&center=true&vCenter=true&width=620&lines=%E4%B8%80%E5%8F%A5%E8%AF%9D%E9%80%89%E9%A2%98%EF%BC%8C%E8%BF%9B%E8%8D%89%E7%A8%BF%E7%AE%B1;%E7%B4%A0%E6%9D%90%C2%B7%E5%86%99%E4%BD%9C%C2%B7%E5%8E%BBAI%E5%91%B3%C2%B7%E9%85%8D%E5%9B%BE%C2%B7%E6%8E%92%E7%89%88%C2%B7%E4%BA%A4%E4%BB%98;%E6%AF%8F%E4%B8%80%E6%AD%A5%E9%83%BD%E7%95%99%E8%AF%81%E6%8D%AE)](https://git.io/typing-svg)

[![Skills](https://img.shields.io/badge/Skills-5-10B981?style=for-the-badge)](#-五个-skill)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-8B5CF6?style=for-the-badge)](https://agentskills.io)
[![Pipeline](https://img.shields.io/badge/Pipeline-六阶段-3B82F6?style=for-the-badge)](#-它怎么工作)


</div>

把「写一篇公众号文章」变成一句话的事。五个相互配合的 Skill + 一个编排器：
AI 热点里选素材、写长文、去 AI 味、配图（带版权证据链）、精致排版、
进微信草稿箱——全程留痕，永不自动发布，最后一下永远由你点。

遵循 [Agent Skills](https://agentskills.io) 开放标准，Claude Code、Codex 等
40+ 支持该标准的 Agent 都能装。

## 🍼 小白三分钟上手（第一次接触 Agent Skill？从这里开始）

**你不需要会编程。** 只需要两样东西：

1. **一个支持 Agent Skills 的 AI 工具**——Claude Code、Codex、Cursor
   等 40+ 个都行（没装过的话，装一个
   [Claude Code](https://claude.ai/code) 即可）；
2. **想试哪个功能，就装哪个 skill**——不用全装。

**第一步：装。** 把这句话原样发给你的 AI 工具：

​
帮我安装这个 skill：[https://github.com/Amer-CN/wxgzh-skills/tree/main/skills/super-writer](https://github.com/Amer-CN/wxgzh-skills/tree/main/skills/super-writer)

**第二步：用。** 装好后直接说人话，比如：

​
帮我把这些素材写成一篇公众号文章

就完了。写作（super-writer）、去 AI 味（zh-human-writing）、排版
（gzh-design）三个都能这样单独用，**零配置、不需要公众号**。

**想要「一句话发文」完整流水线？** 那需要你有自己的微信公众号（推送
草稿要用公众号开发者凭证，在 mp.weixin.qq.com「设置与开发 → 基本配置」
里取），然后按 [skills/wxgzh-pipeline](./skills/wxgzh-pipeline) 的
README 装全家桶。没有公众号也不影响——前三个 skill 照常用。

---

## 🚀 它怎么工作

​
一句话选题 → AI HOT 素材（含超窗补料）→ 材料重型长文写作 → 去 AI 味编辑
→ 配图（抓取/视频封面/数据图表 + 版权证据）→ 主题排版 → 微信草稿箱

<img src="docs/assets/cover.png" alt="流水线：选题→写作→去AI味→配图→排版→草稿箱" width="100%">

每一步都有 receipt 回执；任何一关证据不足，宁可停机报告也不硬闯。
**它只进草稿箱——发布、群发、定时永远是你手动。**

## 👀 效果预览

以下三篇均为流水线真实产出（锤子主题，430px 移动端整页截图）：

<table>
<tr>
<td align="center"><img src="docs/assets/preview-grok46.jpg" width="260"><br><sub><b>Grok 4.6</b><br>8 图 + 图注 + 表格</sub></td>
<td align="center"><img src="docs/assets/preview-deepseek.jpg" width="260"><br><sub><b>DeepSeek V4 Pro</b><br>8 图 + 图注</sub></td>
<td align="center"><img src="docs/assets/preview-minimax-h3.jpg" width="260"><br><sub><b>MiniMax H3</b><br>封面 + 目录 + 图注</sub></td>
</tr>
</table>

## 📋 五个 Skill

| 名字 | 一句话 | 单装 | 版本 |
|---|---|---|---|
| ✍️ [super-writer](./skills/super-writer) | 材料重型中文长文写作：先堆素材证据，再写文章 | ✅ 零依赖 | 0.3.8-rc1 |
| 🧼 [zh-human-writing](./skills/zh-human-writing) | 去 AI 味编辑：词表审计 + 逐句保真门禁 | ✅ 零依赖 | 0.1.3 |
| 🔨 [gzh-design](./skills/gzh-design) | 排版引擎：Markdown → 公众号精致 HTML（**基于 isjiamu 版增强，见来源与致谢**） | ✅ 零依赖 | hammer.14 |
| 🖼️ [media-enrichment](./skills/media-enrichment) | 配图管线：抓取/视频封面/数据图表 + 版权证据链 | 流水线配套 | 0.1.0-dev19 |
| 🎛️ [wxgzh-pipeline](./skills/wxgzh-pipeline) | 总编排器：六阶段流水线 + 锁链治理 + 凭证交付 | 需装齐四个依赖 | dev2 |

## 📦 独立工具（不在流水线内）

| 名字 | 一句话 | 边界 |
|---|---|---|
| 📊 [gzh-title-review](./skills/gzh-title-review) | 标题复盘独立工具：发布后按四分类归因（标题因素/选题时机/账号分发/无法判断），给一个下一次动作 | 流水线外、不入锁、不接编排器，单装单用 |


## ✨ 每个 Skill 的故事

<table><tr><td>

### ✍️ super-writer（材料重型写作）

> *"先证明你有材料，再允许你动笔。"*

大多数 AI 写作的毛病是「看着像那么回事，其实全是编的」。这个 skill
反过来：文章必须建立在实名素材库上——每一条关键事实都能回指具体来源，
证据不足的选题会被材料门禁直接拦下（宁可告诉你「材料不够，写不了」）。
从事件池、claim 注册表到语义地图的完整产物链，写完还附自检报告。

→ [SKILL.md](./skills/super-writer/SKILL.md)

</td></tr></table>

<table><tr><td>

### 🧼 zh-human-writing（去 AI 味编辑）

> *"删掉『赋能抓手闭环』，保住你自己的用词习惯。"*

写完的文章过一遍：词表审计抓 AI 腔（strong/advisory 分级，产品名专名
永不误伤），逐句保真门禁保证编辑不改事实——数字、归因、限定词动了就
FAIL。改写不是黑箱：每处改动进 change_report，可回放、可审计。

→ [SKILL.md](./skills/zh-human-writing/SKILL.md)

</td></tr></table>

<table><tr><td>

### 🖼️ media-enrichment（配图与版权证据）

> *"每张图都要有户口：来自哪页、什么内容、谁批准的。"*

从素材页抓图只是起点。每张候选图强制带「可验证内容描述 + 页面位置 +
原始 URL 追溯」三件套，版权审批留痕；水印域名黑名单、视频封面采集、
文章数据自动生图表兜底；实在没图就如实少图交付，绝不拿无关图充数。
每张正文图自动配图注，读者一眼知道图的出处。

→ [SKILL.md](./skills/media-enrichment/SKILL.md)

</td></tr></table>

<table><tr><td>

### 🔨 gzh-design（排版引擎，基于 isjiamu 版增强）

> *"Markdown 进去，能直接粘进公众号编辑器的精致 HTML 出来。"*

**来源**：本 skill 基于
[isjiamu/gzh-design-skill](https://github.com/isjiamu/gzh-design-skill)
（作者：**甲木 × 摸鱼小李**，AGPL-3.0）增强而来——原版提供 6 套精选
主题、主题生成器与双关卡校验的优秀地基，本仓在此基础上做了生产级增强：

- **高级视觉组件体系**：`:::` 围栏语法 + 脚注 + 17 类高级组件
  （alert / quote / code-compare / media-text / gallery / timeline /
  decision / faq / checklist 等）+ 主题适配器；
- **第七套主题「锤子（smartisan）」**：完整组件库 + 文章类型配方表；
- **确定性渲染器 `render\_article.py`**：把排版从「agent 手工装配」
  固化为可复现的 CLI 渲染管线；
- **组件锚点校验体系**：锚点 JSON + 能力矩阵 + 主题身份反解校验；
- **草稿推送 `publish\_wechat\_draft.py`**：含流水线凭证门（receipt
  绑定 + 内容哈希 + 主题签名，缺一拒发）；
- **生产加固**：内链 45166 修复、WebP→JPEG 转码、表格/列表渲染。

原版权与许可声明完整保留在 `skills/gzh-design/LICENSE`（AGPL-3.0 ©
2026 甲木 × 摸鱼小李）；按 AGPL-3.0 要求，本修改为开源并保留署名。

→ [SKILL.md](./skills/gzh-design/SKILL.md)

</td></tr></table>

<table><tr><td>

### 🎛️ wxgzh-pipeline（总编排器）

> *"六个阶段，每一步都留证据；任何一关不过，宁可停机也不硬闯。"*

把上面四个 skill 串成一句话流水线：阶段握手（request/ACK 幂等）、
receipt 双时制入账（校验秒数 + 真实墙钟分开记）、锁链治理（每个 skill
钉 commit + 哈希，relock 全程留痕）、doctor 一致性体检。换哪个 Agent
来跑，行为都该一样——这是设计目标，也是测试结论。

→ [SKILL.md](./skills/wxgzh-pipeline/SKILL.md) ·
[质量台账](./skills/wxgzh-pipeline/audit/quality/obs-ledger.md)

</td></tr></table>

## 🛡️ 质量体系（为什么这套东西可信）

- **锁链治理**：每个 skill 锁定 commit + 树哈希 + 入口校验器哈希；
  换版本走 relock 流程，52 次 relock 全部留痕可回放；
- **证据链**：素材 → claim → 图片三级绑定，缺证据 fail-closed；
- **观测台账**：生产问题逐条编号（OBS-001 起连续 165 条），修复与
  验证证据全公开在 `skills/wxgzh-pipeline/audit/`；
- **安全边界**：只进草稿箱，永不自动发布/群发/定时/删除。

## 🙏 来源与致谢

- **gzh-design** 基于
  [isjiamu/gzh-design-skill](https://github.com/isjiamu/gzh-design-skill)
  增强（AGPL-3.0）——感谢 **甲木 × 摸鱼小李** 开源的排版组件库与
  主题设计标准，没有这个地基就没有这个流水线；
- **AIHOT** 资讯查询 Skill 由 **卡兹克** 开发并开源，感谢；
- 各子 skill 的 LICENSE 保留在各自子目录内，引用/分发请遵守对应
  许可条款。

## 🌟 关于

这套合集从真实日更公众号的生产需求里长出来，每个 skill 都在生产环境里
跑过多轮才定型。如果觉得有用，给个 ⭐；问题建议在 Issues 里说。

<div align="center">

各子 skill 许可见各自目录 · Made by [@Amer-CN](https://github.com/Amer-CN)

</div>