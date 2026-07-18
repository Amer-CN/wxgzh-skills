# gzh-design Enhanced v2026.07.18

## 保留原版能力

- 6 个公众号主题（摸鱼绿、红白色系、石墨极简风、留白禅意风、摸鱼票据风、橄榄手记）
- 19 个高级组件（alert、quote、code-compare、media-text、gallery、long-image、resources、footnotes、dialogue、facts、decision、steps、compare、annotated-image、faq、timeline、checklist、case、cta）
- Dialogue 左右聊天窗（微信/QQ 对话风格，头像自动左右布局）
- Markdown / Word(.docx) / PDF / 纯文本排版
- 自定义主题生成

## 新增

- 简单微信草稿箱发布脚本 `scripts/publish_wechat_draft.py`
  - 读取 HTML + title
  - 获取 access_token
  - 上传封面或使用已有 thumb_media_id
  - 调用 draft/add 创建草稿
  - 返回 media_id

## 已删除

- D.1/D.2 复杂发布框架（publisher/、Transport 注册表、MockTransport、DraftTransport、不可变快照框架、draft-output-manifest.json、多重 SHA-256 清单、双重确认参数、幂等状态机）

## 组件检查

- ERROR: 0
- WARN: 2（原有主题中的合法虚线风格提示，不阻断）

## 安装与恢复方式

见 README.md。
