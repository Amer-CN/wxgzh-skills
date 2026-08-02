# gzh-design v2026.07.18-hammer.1

## 新增

- **锤子风格主题**（`theme-hammer.md`）— 暖砖红配色，适用于产品发布、科技评论、品牌故事
- **19 个高级组件支持全部 7 个主题** — alert、quote、code-compare、media-text、gallery、long-image、resources、footnotes、dialogue、facts、decision、steps、compare、annotated-image、faq、timeline、checklist、case、cta
- **固定作者与投稿邮箱结尾** — `fixed-signature` 组件，所有主题统一署名
- **微信 Unicode 双重转义修复** — `ensure_ascii=False` + UTF-8 请求体，杜绝 `\uXXXX` 字面量
- **UTF-8 draft/add 发布链路** — `data=json.dumps(ensure_ascii=False).encode("utf-8")`，不用 `json=payload`
- **正文图片自动上传并替换为微信 CDN** — `media/uploadimg` 接口，`mmbiz.qpic.cn` HTTPS URL
- **全属性中文引号校验** — 扫描所有 HTML 属性（含 cx/cy/r/stroke-linecap/stroke-linejoin/data-*/aria-*）
- **七主题文字对比度修复** — 普通文字 ≥ 4.5:1，大号文字 ≥ 3.0:1（WCAG 2.1）
- **全组件真实微信草稿验收通过** — 56 个组件（12 Common + 25 基础 + 19 高级）在微信后台完整渲染

## 保留原版能力

- 7 个公众号主题（摸鱼绿、红白色系、石墨极简风、留白禅意风、摸鱼票据风、橄榄手记、锤子风格）
- Markdown / Word(.docx) / PDF / 纯文本排版
- 自定义主题生成
- Dialogue 左右聊天窗（微信/QQ 对话风格，头像自动左右布局）

## 发布链路安全

`scripts/publish_wechat_draft.py` 关键修复：

- `ensure_ascii=False` 序列化 JSON
- UTF-8 请求体（`data=bytes`，不用 `json=payload`）
- outgoing content 门禁（字面量 `\uXXXX` 阻断、CJK 检查、HTML 完整性）
- JSON 单次往返验证
- `--expect-sha256` raw bytes 校验
- `raw_file_sha256` / `normalized_content_sha256` 分开记录
- `draft/get` 使用 `resp.content.decode("utf-8")` + `json.loads`
- 正文图片 `media/uploadimg` 后替换为 `mmbiz.qpic.cn` HTTPS URL
- 发布前 `validator` + `preflight` 双重校验（ERROR=0, WARNING=0）

## 浏览器测试退出码

- 关键 Playwright 测试全部 SKIP → `exit 2`（不伪装 ALL PASS）
- 正常执行并通过 → `exit 0`
- 有失败 → `exit 1`

## 已删除

- D.1/D.2 复杂发布框架（publisher/、Transport 注册表、MockTransport、DraftTransport、不可变快照框架、draft-output-manifest.json、多重 SHA-256 清单、双重确认参数、幂等状态机）

## 测试结果

| 测试套件 | 结果 |
|----------|------|
| test_publish_hotfix.py | 44/44 PASS ✅ |
| test_advanced_components.py | 58/58 PASS ✅ |
| test_dialogue_hotfix.py | 15/15 PASS ✅ |
| test_fixed_signature.py | 15/15 PASS ✅ |
| test_hammer_contrast.py | 11/11 PASS ✅ |
| test_all_components_fixture.py | 22/22 PASS ✅ |
| test_all_components_contrast.py | 7/7 PASS ✅ |
| validator | ERROR=0, WARNING=0 ✅ |
| **合计** | **172/172 PASS ✅** |

## 安装与恢复方式

见 README.md。
