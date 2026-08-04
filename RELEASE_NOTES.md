# gzh-design v2026.08.02-hammer.4

## v2026.08.02-hammer.4 追加变更（wxgzh-pipeline 集成侧）

- **WARN 分级 + 显式放行通道（档54R）** — 发布预检门槛分级:`validate_gzh_html.py` 引入规则类别标记;半角标点/英文引号 = `allowable`(可显式放行)、span leaf 未包裹 = `blocking`(不可放行);`publish_wechat_draft.py` 新增 `--allow-warnings` 显式开关(默认关闭,仅对 `allowable` 类别生效),放行条目逐条写入 `allowance_record.json`(audit 留痕,可追溯)。
- **OBS-85:HTML 解析中断升为 ERROR** — 校验器未能完成检查不得输出温和结果,任何情况下(含开关全开)不可放行。

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

## v2026.08.02-hammer.3 追加变更（wxgzh-pipeline 集成侧）

- **OBS-73 根治**:首个 `##` 之前、intro 第一行之后的段落不再被丢弃,作为正文段落渲染在第一个章节标题之前(顺序:封面 → 导语段落 → 章节标题 → 章节正文)。`intro` 字段语义不变,封面副标题与 oneliner 截断长度不变。
- **fenced code block**:``` 围栏识别为代码块,渲染为可复制的 `<pre>`(内联样式:等宽字体、浅底、横向滚动、保留空白);不依赖 `<style>`/class;反引号不进入输出。

## 与 wxgzh-pipeline 集成范围的如实说明

本仓库 19 个高级组件(alert/quote/code-compare/media-text/gallery/long-image/resources/footnotes/dialogue/facts/decision/steps/compare/annotated-image/faq/timeline/checklist/case/cta)及其 `:::` 围栏语法面向通用排版入口;wxgzh-pipeline 的锤子(smartisan)渲染管线(`scripts/render_article.py` + `scripts/generate_hammer_upgrade_samples.py`)只使用以下组件子集:cover-breaking、toc-scroll、chapter-title、paragraph、oneliner-card、media-text、image-2a、fixed-signature、footer-cta(以及本次新增的单栏代码块)。高级组件不在该管线渲染路径内。

- **OBS-83 修复**:intro 首段完整渲染进正文(首个章节标题之前,与其余 intro 段落同一路径);取消 oneliner 卡片(其内容仅为 intro[:40],首段正文化后冗余);封面 subtitle 行为不变。
