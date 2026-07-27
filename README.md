# wxgzh-pipeline

> 微信公众号总编排 Skill。一句话发文，自动跑完六阶段并创建微信草稿。

## 日常使用

```
发文：<选题>
```

示例：

```
发文：Claude Opus 5
```

断点继续：

```
续发
```

查看进度：

```
进度
```

`发文：<选题>` 会固定按 `fast_publish` 模式顺序执行：AI HOT → Super Writer（Material-Heavy Full
Mode）→ zh-human-writing（去 AI 味）→ media-enrichment（配图并上传微信图床）→ gzh-design（锤子
smartisan 主题正式排版）→ **创建微信草稿** → 停止。默认主题锤子、不回退、不跳阶段、不绕过子 Skill。

**"发文"只创建草稿，绝不正式发布。** 正式发布 / 群发 / 定时发布 / 删除草稿在本 Skill 代码中不存在；
正式发布只能由你本人在微信公众号后台手动操作。

## 版本

0.1.0-dev1 · orchestrator（只编排，不复制子 Skill 业务逻辑）

## 依赖的已安装子 Skill（版本与根 Hash 锁定见 `skills.lock.json`）

| 阶段 | 子 Skill | 版本 |
|---|---|---|
| 1 | aihot（agent 调用） | — |
| 2 | super-writer | 0.3.2-rc1 |
| 3 | zh-human-writing | 0.1.0 |
| 4 | media-enrichment | ≥ 0.1.0-dev7-hotfix1 |
| 5 | gzh-design | v2026.07.18-hammer.1 |
| 6 | 微信草稿 | 复用 gzh-design/scripts/publish_wechat_draft.py |

## 命令

```bash
# 发文（新文章）
python -m wxgzh_pipeline.cli "发文：Claude Opus 5"
# 续发（恢复最新未完成运行）
python -m wxgzh_pipeline.cli "续发"
python -m wxgzh_pipeline.cli "续发：<RUN_ID>"
# 进度
python -m wxgzh_pipeline.cli "进度"
# 开发者：验收编排 Skill（release_audit；不生产文章、不上传、不建草稿）
python -m wxgzh_pipeline.cli "验收编排Skill"

# 环境体检 / 安装 / 打包
python scripts/doctor.py
python scripts/install.py --dry-run
python scripts/build_portable_bundle.py
```

## 跨电脑

不硬编码本机路径。项目根解析顺序：用户显式配置 → `WXGZH_PROJECT_ROOT` → `AGENT_SKILLS_HOME` →
当前项目 `.agents/skills` → 用户目录标准 Skill 位置。兼容 Windows / macOS / Linux。凭据只从项目 `.env`
读取（`WECHAT_APP_ID` / `WECHAT_APP_SECRET`），见 `config.example.env`。

## 安全边界

- 只创建草稿；无正式发布/群发/定时发布/删除草稿能力。
- 离线 Fixture 测试不产生任何真实微信副作用。
- 证据包与便携安装包不含 .env / AppID / AppSecret / access_token / 草稿 ID / 本机绝对路径。
