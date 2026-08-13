# wxgzh-pipeline

> 微信公众号总编排 Skill。一句话发文，自动跑完六阶段并创建微信草稿。

> ⚠️ CI 口径（OBS-193，71I 正式化）：CI 自有记录以来零 success、长期红，根因四类环境性失败（硬编码开发机路径 12 项 / CI 未安装被锁子技能 / bs4 依赖缺失 / 陈旧 LOCKED_HEADS 与 OBS-69 基线）。CI 绿不构成验收依据，CI 红也不构成停机依据；一切验收以本机 junit 为准。详见 [audit/quality/obs-ledger.md](audit/quality/obs-ledger.md) 的「CI 口径正式化」节。

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

0.1.0-dev2-hotfix6 · orchestrator（只编排，不复制子 Skill 业务逻辑）

## 依赖的已安装子 Skill（版本与根 Hash 锁定见 `skills.lock.json`）

| 阶段 | 子 Skill | 版本 |
|---|---|---|
| 1 | aihot（agent 调用） | — |
| 2 | super-writer | 0.3.2-rc1 |
| 3 | zh-human-writing | 0.1.0 |
| 4 | media-enrichment | 0.1.0-dev7-hotfix3 |
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

## 供图注入（76C/OBS-255，媒体阶段正式人工通道）

媒体 discover 阶段前，可把用户供图直链清单写入 `runs/<RUN>/media_enrichment/user_images.json`：

```json
[
  {"url": "https://example.com/photo.png", "caption": "可选说明", "source_url": "可选来源链接"}
]
```

- 该文件存在时,media discover 把其中图片纳入候选(`user_provided`);
- **免版权审批**:用户供图责任自负,来源链接登记留痕(`content_description_source=user_provided`);
- 仍走安全/尺寸(480×200)/质量/去重检查,不满足则 review_required 而非直接 eligible;
- 与既有图片批准车道一致:命中黑名单域名或安全检查不过即拒。

## 门禁降级（76C，用户裁决 2026-08-11）

图片数量不再是发文限制条件:`body_images_min` 保留为「目标值」。源图 eligible 不足时走降级链:
生图车道兜底(claims 绑定数字/事实生成图表,只可视化 claim 支撑数据,不编造数据图)→ 生图也兜不足 → 允许少图交付,
在 receipt 与 final_delivery 标注 `image_shortfall=true` + 实际图数(留痕,不静默)。
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


## 超窗取料（76H/OBS-267，发文 SOP）

选题关键素材可能超出 AI HOT v1 7 天窗口、或用户显式写历史/回顾类选题时，
aihot 阶段按下列顺序取料（写入手握手指令，agent 执行）：

1. 已知关键日期 → `/api/v1/dailies/{date}` 取当日日报（归档正式端点）。
2. 精选池快照检索：`selected/snapshot`（fields=minimal，翻完分页后本地按关键词
   过滤，遵守 ETag/流量纪律；仅超窗选题使用，日常发文不走快照）。
3. 热点事件回溯：`hot-topics` → `/api/v1/stories/{publicId}` 时间线（逆序报道
   可回溯超 7 天）。
4. 官方源直采：官方博客/公告页/releases 等一手来源——走补充来源注册
   （registry/ledger `provenance: supplemental`，携带 source_url + 抓取证据 +
   登记理由，不再被 dedup 对齐挤出）。
5. 仍缺 → 明示用户手动注入（`items_file_injection` 既有通道），不得静默降级。
