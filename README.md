# wxgzh-skills

微信 AI 写作/排版五个一手 Skill 的**合集仓**（2026-08 用户裁决迁移）。

五个 Skill 由 git subtree 合并至此，历史完整保留，子目录分 skill：

| 子目录 | Skill | 版本（迁移钉死） | 说明 |
| --- | --- | --- | --- |
| `skills/super-writer` | super-writer | 0.3.8-rc1 | 中文长文/公众号文章写作系统（材料重型） |
| `skills/zh-human-writing` | zh-human-writing | 0.1.3 | 简体中文写作编辑（去 AI 味/词表/审计） |
| `skills/media-enrichment` | media-enrichment | 0.1.0-dev19 | 媒体资产富化（抓图/审批/上传/图注） |
| `skills/gzh-design` | gzh-design | v2026.08.13-hammer.13 | Markdown → 公众号 HTML 排版引擎 |
| `skills/wxgzh-pipeline` | wxgzh-pipeline | dev/0.1.0-dev2 | 发文编排（锁链/握手/墙钟/receipt） |

## 安装

### AIHOT（第三方，不入仓）

AI HOT 是第三方 Skill（作者：卡兹克），**不包含在本合集仓**。请使用作者官网安装器：

- 安装器：`aihot.virxact.com/aihot-skill`
- 安装时**必须校验下载产物的 SHA-256**（安装器页面提供；校验方式随安装器说明）。
- 校验通过后按安装器指引落位到你的 skills 目录。

### 五个一手 Skill

各子目录自带 `SKILL.md`、`README.md` 与安装/自检脚本（`scripts/`）。推荐流程：

1. clone 本仓：`git clone https://github.com/Amer-CN/wxgzh-skills.git`
2. 按子目录 README 安装依赖并运行各自测试（pytest）。
3. 编排使用以 `skills/wxgzh-pipeline` 为准（其 `skills.lock.json` 锁定其余四 skill 的版本与哈希）。

## 许可

各子 Skill 的 LICENSE 保留在各自子目录内（`skills/<name>/LICENSE`），互不覆盖。
本合集仓自身不新增许可；引用/分发请遵守各子目录许可条款。

## 旧仓

迁移前的五个独立仓库已归档（只读），README 顶部均指向本合集仓。
