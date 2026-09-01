# gzh-design v2026.09.01-hammer.20

## v2026.09.01-hammer.20(档77S)
- 灵犀安装安检合规(77S 第一轮内容修复): SKILL.md 新增「权限与范围声明（最小权限）」节（文件读写/网络端点/凭据键名/子进程/明确不做五要素）。
- 本档渲染器/主题/模板零代码改动；版本落文件, relock dry-run 验证归第二轮(显示 hammer.20 才算数)。

## v2026.08.30-hammer.19(档77Q)
- OBS-341 封面划线句对比度回归根治: strike_text 进入 PALETTES 单一真源（moyu #4B5563 / hammer #555555），白底对比度 ≥4.5:1；收编旧样张与主题文档浅色定义。
- 回归测试 +1: 真源颜色、对比度、渲染 HTML 与删除线颜色同步断言。

## v2026.08.30-hammer.18(档77P)

## v2026.08.30-hammer.18(档77P)
- OBS-340 封面渲染安全网: strike 与 subtitle 槽位增加 `white-space:nowrap; overflow:hidden; text-overflow:ellipsis`，超长漏网也不折行。
- 测试 +1: 长划线句 + 长导语副标题渲染仍单行截断。

## v2026.08.29-n18(档77M)

## v2026.08.29-n18(档77M)
- 77M/OBS-330: 容器/type 枚举单一真源(ALERT_TYPES/QUOTE_TYPES/CONTAINER_TYPES/MARKDOWN_CONTAINERS)
- 77M/OBS-331: UnboundLocalError 修复(name 提前赋值);畸形指令不 crash

# gzh-design v2026.08.27-hammer.17

## v2026.08.27-hammer.17(档77K)

- render_article 解析 ::: 组件属性失败时留 WARNING（组件名+原文行），不再静默回落默认组件语义；合法正文、合法指令和有图路径零变化。

## v2026.08.25-hammer.16(档77H)

- OBS-318 草稿零图封面兜底:publish_wechat_draft.py 无 --cover/--thumb-media-id 时
  按锤子主题同源颜色生成占位封面(900x383,标题+品牌行),上传后作为 thumb_media_id;
  audit 与直传两分支都覆盖;draft_creation_result 记 cover_source=placeholder_zero_image;
  有图/显式封面行为零变化。测试 +2。

## v2026.08.14-hammer.15(档76T)

- OBS-293 封面划线句改义:render_article 新增 --strike-assumption
  (划线句槽改读新字段);缺失时划线句整行不渲染(不再用 hook_line/默认文案填充,
  消灭语义冲突);旧 --strike 保留读取兼容但不再驱动划线槽。测试 +3。

- OBS-282 交付凭证门:publish_wechat_draft.py 新增强制参数 --evidence(本 RUN 的
  gzh_design/stage_receipt.json)——receipt 校验通过 + html sha 与待推 HTML 一致 +
  HTML 含 hammer 主题签名(#B3593B)三项缺一即 FAIL_CLOSED(报错指引走管线
  wechat_draft 阶段);无后门参数;独立手工发布=公众号后台手动。测试 +6。
- 渲染器/设计系统零改动(render_entry 不变)。

## v2026.08.14-hammer.13(档76J)

## v2026.08.14-hammer.15(档76J)

- OBS-271 表格/列表支持:render_article.py 解析标准 Markdown 表格(首行 header +
  分隔行跳过)与 `- `/`* `/`1. ` 列表块;渲染走既有 hammer 组件样式——表格
  = theme-hammer.md 11f,无序列表 = 11a pill-list,有序列表 = 11g
  ordered-list;单元格/列表项文本以固定 p 样式承载(语法门锚可测,pipeline
  component_anchors.json 同步注册)。测试 +6(解析/渲染/语法门 probe 同语义)。

## v2026.08.12-hammer.12(档76D)

- OBS-257 封面标题链路:render_article.py 新增 --title/--subtitle 可选参数
  (默认 None → 沿用既有解析:H1 / 导语 intro),与 HF-6/72E-1 参数化同模式;
  pipeline 侧 handoff.selected_title(缺省回落 title_candidates[0])流入 --title,
  文章导语缺失时 hook_line 流入 --subtitle。测试 +5(覆盖生效/默认沿用/CLI 参数)。

## v2026.08.10-hammer.11(档72E-1)

- OBS-251 封面文案路径:render_article.py 新增 --kicker 可选参数(默认 None → 沿用
  既有「深度观察 · 标签」构造),与 HF-6 四参数同模式;handoff formatter.cover 的
  kicker 经 pipeline 接线流入。测试 +2(覆盖生效/默认沿用)。

## v2026.08.10-hammer.10(档HF-7)

- OBS-250:署名第二句恢复用户传统落款——「不用马上跟上，知道一点，就不算
  掉队。」(07-19 hammer.1 落成即写错)逐字替换为「用克制的语言讲清楚AI前沿
  正在发生的事。」;改动=references/common-components.md §4(表格行+4a+4c+4d)
  + hammer_fixed_signature + SKILL.md 示例 + showcase/测试字面,共 9 处;
  第一句「热闹是 AI 的，淡定可以是我们的。」与署名结构一个字符不动;
  render_article.py 不动(entrypoint/render_entry sha 不变)。

## v2026.08.09-hammer.9(档HF-6)

- OBS-249:封面 chrome 固定值——date 样品残留(2026.07)+ strike 硬编码占位
  (「别急着划走」);谱系:增强层自生(render_article 与 hammer_* 组件层均为本 fork
  增强,上游 isjiamu/gzh-design-skill 无文章渲染层,无上游修复可拉)。
- 修复(用户裁决 B):render_article.py 封面全参数化——新增 --date/--strike/--brand/--tags
  四个可选参数;date 未显式给出时自动取渲染时点当月(%Y.%m);不传参时除 date 外
  与旧产出逐字一致。generate_hammer_upgrade_samples.py 的 hammer_cover 默认值不动,
  parse_article/split_title/en_label_for 零改动(OBS-73 镜像守卫保持)。

## v2026.08.02-hammer.8(档71C-R)

- OBS-129/132:alert / quote 正文槽由单 `<p>` 改为逐有效行一个 `<p>`(style 逐字复用,
  空行跳过;S12 已实测 `<br>` 在微信端失行,故用逐行 p 而非 `<br>`)。
- OBS-126:media-text 块体 `![说明](url)` 解析为图 URL + 说明;剩余行作解释段,多行逐行。
- OBS-124:code-compare `@before/@after` 支持续行直到 `@end`;同行 `lang="..."` 解析为
  语言标签(title 后缀),不再串入代码正文。
- OBS-125:long-image 按文档 `image=`/`caption=`(兼容 `url=`/`cap=`);删除硬编码
  `setdefault("cap","完整流程图")`,缺 caption 不出说明行。
- OBS-127:alert/quote 类型参数读 `type=`(兼容 `typ`/`qt`),枚举照 references 原文。
- OBS-128:footnotes 支持正文散落 `[^N]`+`[^N]:` 定义与既有 `:::footnotes` 块两种写法,
  产出 HTML 一致(散落定义由 parse_article 收集,无块时自动追加组件)。

## v2026.08.02-hammer.7(档67D)

- 回归 references/common-components.md「1a. 深色代码块(默认)」——恢复「不手写 HTML」
  契约:新增官方组件 `hammer_code_block(language, text)`(generate_hammer_upgrade_samples.py),
  按 1a 逐字实现(外层 #1E293B + box-shadow;顶栏 #0F172A + 三色圆点
  #FF5F56/#FFBD2E/#27C93F;语言标签 #64748B Consolas;每行独立
  `<p style="margin:0;…;color:#E2E8F0;">`);render_article._hammer_code_block 改为
  纯委托,不再手写 hammer HTML(文件头声明恢复为真)。
- 缩进回归规范:行首前导空白转全角空格 U+3000(规范③),行内空格一字不动(规范⑤)。
- test_obs91_copyability 加严:无前导空白行零 U+00A0 且零 U+3000;16 条 deny/ask
  逐字还原;★反向验证(旧全 &nbsp; 实现)仍 FAIL。新增 OBS-95 结构闸门测试
  (渲染输出必须命中 1a 结构:深底/顶栏/三圆点/逐行 p)。
- scripts/gen_cover.py 移入 tests/(无入口引用,67C 待裁决项)。

# gzh-design v2026.08.02-hammer.7

## v2026.08.02-hammer.7(档67C)

- OBS-91:代码块可复制性修复——仅行首前导空白(空格/制表符)转 `&nbsp;` 保留缩进;
  行内空格保持普通空格(复制出来是普通空格,可复制性优先);行内连续空白段仅
  「第二个及之后」转 `&nbsp;`(首个保持普通空格,防折叠同时不伤可复制性)。
  同步修正 `_hammer_code_block` docstring,与实现逐字一致(上次 docstring 与实现
  不一致是 OBS-91 成因之一)。
- 新增可复制性回归测试(`tests/test_obs91_copyability.py`,自动化不依赖人眼):
  渲染 → 去标签 + unescape → 与源代码块逐行比对(逐字节/无前导空白行零 U+00A0/
  ⛔⚠️ 与 16 条 deny/ask 逐字还原);★反向验证:旧全 `&nbsp;` 实现被判 FAIL。
- 举证(见档67C 报告):等宽字体在运行时仅代码块使用(renderer 输出面);gen_cover.py
  为 2026-07-19 遗留未跟踪展示工具,前四次 gzh-design relock 源树为
  repos/gzh-design-skill-43r-build(不含该文件),见证通过系源树不同,非见证漏洞。

# gzh-design v2026.08.02-hammer.7

## v2026.08.02-hammer.7(档67A)

- OBS-90:代码块微信友好结构——每行一个 `<p style="margin:0">`(与
  generate_advanced_html.code_compare 同构),不再输出 `<pre>` / `white-space:pre`
  (自家 lint 判 ERROR 的特征,消除 validate_gzh_html 与 lint 的内部矛盾);
  行内前导/连续空格以 `&nbsp;` 保留(⛔/⚠️ 前缀与缩进对齐);内容保持真实可选中
  文本,不截图、不伪装元素。
- validate_gzh_html:代码区识别改为等宽字体(font-family monospace/Consolas/
  'SF Mono'/courier),不再依赖 white-space:pre;普通段落无等宽字体,不误判。
- 封面删除线对比度:strike 文字色由 divider(≈1.2:1)改为 label_text #737373
  (白底 4.74:1 ≥ 4.5:1);删除线由主题橙 #B3593B 1.5px 改为同文字色 1px 细线,
  不盖字形。
- OBS-77:主题文档占位符修复({作者名}/{一句话简介,如…})+ zen-whitespace
  补固定结尾引用;fixed_signature 三项预存失败恢复。

# gzh-design v2026.08.02-hammer.7

## v2026.08.02-hammer.7 追加变更（wxgzh-pipeline 集成侧）

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
