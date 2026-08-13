
​
<div align="center">

# 🧰 wxgzh-skills

#### 一句话发公众号：从选题到草稿箱的全自动 AI 流水线

[![Skills](https://img.shields.io/badge/Skills-5-10B981?style=for-the-badge)](#-五个-skill)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-8B5CF6?style=for-the-badge)](https://agentskills.io)
[![Pipeline](https://img.shields.io/badge/Pipeline-六阶段-3B82F6?style=for-the-badge)](#-它怎么工作)

</div>

把「写一篇公众号文章」变成一句话的事。五个相互配合的 Skill + 一个编排器：
AI 热点里选素材、写长文、去 AI 味、配图（带版权证据链）、锤子风格排版、
进微信草稿箱——全程留痕，永不自动发布，最后一下永远由你点。

遵循 [Agent Skills](https://agentskills.io) 开放标准，Claude Code、Codex 等
40+ 支持该标准的 Agent 都能装。

---

## 🚀 它怎么工作
​
一句话选题 → AI HOT 素材（含超窗补料）→ 材料重型长文写作 → 去 AI 味编辑
→ 配图（抓取/视频封面/数据图表 + 版权证据）→ 锤子主题排版 → 微信草稿箱

每一步都有 receipt 回执；任何一关证据不足，宁可停机报告也不硬闯。
**它只进草稿箱——发布、群发、定时永远是你手动。**

## 📦 安装

**只装一个 skill**（比如只要写作）：在 Claude Code / Codex 等支持
Agent Skills 的工具里直接说：
​
帮我安装这个 skill：https://github.com/Amer-CN/wxgzh-skills/tree/main/skills/super-writer

把结尾的 `super-writer` 换成你要的那个即可——每个子目录都是完整独立的
skill（SKILL.md / 脚本 / 文档 / 许可齐全）。super-writer、
zh-human-writing、gzh-design 三个零依赖、单装即用；media-enrichment
为流水线配套设计（吃 super-writer 的产物格式），一般不单装。

**装整个流水线**（一句话发文）：
​
git clone https://github.com/Amer-CN/wxgzh-skills.git

然后按 `skills/wxgzh-pipeline` 的 README 安装——编排器的 doctor 会用
`skills.lock.json` 强制校验其余四个依赖 skill 必须齐、版本与哈希必须对，
缺一个直接拒跑。

**AIHOT（第三方依赖，不入仓）**：AI HOT 资讯查询 Skill 由卡兹克开发，
用作者官网安装器安装（自带 SHA-256 校验）：
👉 https://aihot.virxact.com/aihot-skill

## 📋 五个 Skill

| 名字 | 一句话 | 单装 | 版本 |
|---|---|---|---|
| ✍️ [super-writer](./skills/super-writer) | 材料重型中文长文写作：先堆素材证据，再写文章 | ✅ 零依赖 | 0.3.8-rc1 |
| 🧼 [zh-human-writing](./skills/zh-human-writing) | 去 AI 味编辑：词表审计 + 逐句保真门禁 | ✅ 零依赖 | 0.1.3 |
| 🔨 [gzh-design](./skills/gzh-design) | 锤子风格排版引擎：Markdown → 公众号精致 HTML | ✅ 零依赖 | hammer.14 |
| 🖼️ [media-enrichment](./skills/media-enrichment) | 配图管线：抓取/视频封面/数据图表 + 版权证据链 | 流水线配套 | 0.1.0-dev19 |
| 🎛️ [wxgzh-pipeline](./skills/wxgzh-pipeline) | 总编排器：六阶段流水线 + 锁链治理 + 凭证交付 | 需装齐四个依赖 | dev2 |

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

### 🔨 gzh-design（锤子排版引擎）

> *"Markdown 进去，能直接粘进公众号编辑器的精致 HTML 出来。"*

锤子主题组件库（封面/目录/章节卡/引用/表格/图注/署名）+ 组件级锚点
校验：渲染产物必须带主题签名，样式漂移当场报警。推送草稿要出示流水线
凭证（receipt 绑定 + 内容哈希 + 主题签名），缺一拒发。

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

## 🌟 关于

这套合集从真实日更公众号的生产需求里长出来，每个 skill 都在生产环境里
跑过多轮才定型。如果觉得有用，给个 ⭐；问题建议在 Issues 里说。

AIHOT 资讯查询 Skill 版权归原作者所有，感谢卡兹克开源。

<div align="center">

各子 skill 许可见各自目录 · Made by [@Amer-CN](https://github.com/Amer-CN)

</div>
​
