# 档 53 — 引号问题定位(只查不改,停机等裁决)

- 日期:2026-08-03
- 触发背景:档 52 重跑时 wechat_draft 入口预检阻断——冻结文章含 2 处半角引号,本次发布要求 WARNING=0。
- 本档状态:**只读取证完成,未改任何代码/内容/配置,停机等裁决**。

---

## 第一步 来源定位

### 1. 逐层回溯(该标题的原文)

| 层 | 文件 | 该标题原文 | 引号状态 |
|---|---|---|---|
| aihot 素材 | `aihot/deduplicated_items.json` | 素材标题为「Codex 用 Sol 指挥 Luna Max 省额度翻倍产出」;全文**不含「思考」字样**、无内容引号(检索 `思考` 0 命中;命中 `"` 均为 JSON 语法引号) | —(无此标题) |
| super_writer 大纲 | `super_writer/outline.md` | `## 一、把贵模型留给"思考"` | **半角引号在此引入**(LLM 生成) |
| super_writer 正文 | `super_writer/article.md` L7 | `## 一、把贵模型留给"思考"` | 半角,沿用大纲 |
| zh_human_writing 冻结稿 | `zh_human_writing/final_article.md` L7 | `## 一、把贵模型留给"思考"` | 半角,**逐字透传** |

**结论:半角引号由 super_writer 阶段引入(大纲即生成),zh_human_writing 保持透传,非素材透传。**

### 2. zh_human_writing 有无中文标点规范化逻辑

- **无**。检索 `scripts/`(change_report.py / fidelity_guard.py / pattern_audit.py)、SKILL.md、core/constraints.md、core/fidelity.md、FREEZE.md:`全角/半角/引号/标点/规范化` 均无命中。
- fidelity_guard.py 唯一的字符归一(L109-110 `n.replace('％','%')`)仅用于**数字比对**,不作用于输出。
- `core/routing.md` L37/57/77:`rewrite_quote | deny | 硬约束`——zh 阶段被禁止改写引文/引号相关内容;`change_title` 仅当标题存在 hard-residue 时才允许最小替换。
- **判定:系统性缺口成立**——zh-human-writing 无任何引号规范化机制,且其约束体系( preserve 语义 + rewrite_quote deny)倾向「不动引号」。今后任何含 ASCII 引号的标题都会一路透传到 gzh_design,被 WARNING=0 门槛卡住。

### 3. 素材透传路径与「为何前三篇没触发」

- 透传路径:`super_writer/article.md → zh_human_writing/final_article.md → gzh_design final.html(正文标题 + 目录 toc-scroll 各 1 处 = 2 处)→ publish 预检`。
- 前三篇(20260731T135947-ai-bbg4al / 20260801T182628-topic-ui5f7p / 事件 RUN 20260801T231452)的 `final_article.md` **ASCII 引号计数均为 0**;其正文使用全角引号(RUN1/RUN2 为“ ”,事件稿为「」)。
- 即:前三篇只是「恰好没生成 ASCII 引号」。本次是 LLM 输出风格漂移(同一 super_writer,本次大纲用 `"思考"`)。**不是前三篇有豁免,而是内容特征差异**——下一次任何带引号的标题都可能复现。

---

## 第二步 校验规则勘察

### 4. 产生该 WARN 的规则原文(gzh-design `scripts/validate_gzh_html.py`)

```python
L94  # 中文字后紧跟半角逗号/分号/叹号/问号(应改全角);只查"中文在前"避免中英混排误伤
L95  HALF_PUNCT = re.compile(r"[一-鿿㐀-䶿][,;!?]")
L96  ASCII_QUOTE = re.compile(r"[\"']")
L97  # 代码区特征:等宽字体或 white-space:pre —— 其内半角符号是正常的
L98  CODE_STYLE = re.compile(r"monospace|white-space\s*:\s*pre|courier|consolas|sf mono", re.I)
...
L145 if self.code_depth == 0 and (HALF_PUNCT.search(text)
L146                              or ASCII_QUOTE.search(text)):
L147     snippet = text[:24] + ("…" if len(text) > 24 else "")
L148     self.half_punct.append(snippet)
...
L226 if checker.half_punct:
L227     # 剔除固定结尾署名组件内部的半角内容(邮箱 @ . /),这些是允许的半角内容
L229     filtered = []
L231     if "cd.hyxc.jz@foxmail.com" in snippet: continue
L233     if "/ 作者 给自己造把锤子" in snippet: continue
L235     if "/ 投稿或反馈" in snippet: continue
L240     warnings.append(
L241         f"{len(filtered)} 处正文疑似半角标点/英文引号,应改中文全角"
L242         f"(代码块内不计;固定结尾署名组件内的邮箱和 / 已豁免)。例:{sample}")
```

命中机制:`ASCII_QUOTE = [\"']` 对**任何含 CJK 的文本节点**生效(代码区除外),因此 `"思考"` 在章节标题出现 1 次即记 1 处;渲染后正文章节标题 + 目录共 2 处,与档 52 实测一致。

### 5. WARN vs ERROR 与 WARNING=0 门槛

- **级别**:该规则是 **WARN**。`validate()` 返回 `(errors, warnings, leaf_count)`;`validate_gzh_html.py` 的 `main()` 退出码为 `1 if errors else 0`(L278)——**WARN 不改变 validator 退出码**,validator 语义是「无致命问题,可粘贴(warning 请人工确认)」(L276)。
- **门槛位置**:`gzh-design/scripts/publish_wechat_draft.py` `preflight_html()` L413-416:
  ```python
  L413 # 本次真实发布要求 ERROR=0 且 WARNING=0
  L414 if errors or warnings:
  L415     print("\n  不得获取 token,不得调用 draft/add")
  L416     sys.exit(1)
  ```
  L325 文档串:「必须在 get_access_token 之前完成。本次真实发布要求 ERROR=0 且 WARNING=0。」
- **设定者与由来**:`git log -S "WARNING=0"` 定位到 `29864fe`(v2026.07.18-hammer.1,2026-07-19 打包发布)。预检阻断机制本身源自 `4053308`(fix(45166): add validator + preflight blocking——当时为阻止带 `href="#..."` 的 HTML 触发微信 45166,确立了「预检不达标不得取 token」原则)。hammer.1 把该原则扩展为「**任何** WARNING 也阻断」,注释语义为「本次真实发布要求 ERROR=0 且 WARNING=0」——即当时把「建议人工确认」的 WARN 一并升级为硬门槛,未区分级别。
- **现状**:自动链路中不存在人工确认通道(`--audit-dir` 审计模式在 preflight **之后**运行,不绕过;`--dry-run` 只是审计模式的模拟快照),因此 WARN 事实上等于 ERROR。

### 6. 全仓 WARN 级规则清单(会被 WARNING=0 门槛卡住的全部情况)

`publish` 的 `warnings` 唯一来源 = `validate()` 的 `v_warnings`(L381-383)。validate 内全部 `warnings.append` 仅 3 处:

| # | 规则 | 位置 | 触发条件 | 性质 |
|---|---|---|---|---|
| 1 | 半角标点/英文引号 | validate L95-96/L145-148/L226-242 | 非代码区 CJK 文本节点含 `["']` 或 `中文[,;!?]` | 排版/内容规范(本案) |
| 2 | 中文文本未被 span leaf 包裹 | L219-224 | 存在 leaf 但有 unwrapped 中文节点(样式可能丢失) | 排版风险 |
| 3 | HTML 解析中断 | L213 | HTMLParser 抛异常(容错提示) | 结构性异常信号 |

其余全部为 ERROR 级:FORBIDDEN 20 条(L22-37,全部 `"ERROR"`)、id 属性(L171)、内部片段链接(L185)、中文引号属性(L198)、占位符/编辑锚点(L207)、全文无 leaf(L217)、publish 层 E_NOT_HTML / E_NO_CJK_TEXT / E_NOT_RENDERED_HTML / E_RAW_MARKDOWN / E_LITERAL_UNICODE / E_FRAGMENT_HREF(L349-376)。

**结论:WARNING=0 门槛一共卡 3 类情况,不止引号一种。** 其中第 2 类(leaf 包裹)是渲染器缺陷信号,第 3 类罕见;三类在自动链路里都无法人工确认,均会被同权阻断。

---

## 第三步 方案评估(逐个给代价,不推荐,不执行)

### 方案 A:zh_human_writing 输出阶段做中文标点规范化
- 代价:
  1. 动被锁 skill(zh-human-writing 为四锁之一,full_commit_sha=`0c8962f3`,锁于 `chore/wxgzh-pipeline-dev2-integration`),须经正式安装器,禁止手工覆盖。
  2. 需升版(skill_version)+ **第 4 次真实 relock --apply**(台账现 3 条,全部为 gzh-design;zh-human-writing 从未 relock 过),含远端见证、锁定入口冒烟、post-doctor 全链。
  3. receipt 影响:zh-human-writing 是 **agent 握手阶段**(receipt `invoked_entrypoint=agent_handshake:zh_human_writing`),官方 validator(fidelity_guard 等)sha 变化 → 既有 RUN 的 `official_validators.sha256` 失配 → 该 RUN 从 zh_human_writing 起 SKILL_UPGRADED 重跑;aihot/super_writer 不受影响(zh 输入 hash 未变)。
  4. 实现形态难题:zh 输出由 agent 生成,代码侧只有校验器;「规范化」要么写成 agent 执行约定(SKILL.md 约束,软约束,LLM 可能不遵守),要么加确定性后处理脚本(改动 final_article.md 字符,需保证 fidelity_guard 接受——规范化只改标点字符,数字/事实不动,理论可过,但要证明)。
- 优点:在内容源头修复,后续所有文章受益。

### 方案 B:gzh_design 渲染阶段做规范化
- 代价:
  1. 动被锁 skill gzh-design(刚在档 51 完成 hammer.3 relock,台账第 3 条),须再升版(hammer.4)+ 第 4 次真实 relock。
  2. **与内容保真守卫冲突(关键)**:渲染层改正文文字(`"`→`“”`)会使 final.html 反提取文本与 frozen final_article.md 段落不再逐字一致,档 45R/51 的内容保真守卫/INTRO_GUARD 会 FAIL;而「禁止放宽守卫断言」是硬约束。要么守卫同步理解规范化规则(比对逻辑复杂化,且逐字语义被破坏),要么规范化的范围被守卫卡死。
  3. 已有 `fix_html_quotes.py` 只修 **HTML 属性**引号(属性必须 ASCII),修正文引号是新的行为面,与微信渲染质量语义需重新论证。
- 需回答的问题:**标点规范化属于写作职责还是排版职责?** 我的事实陈述:它改变的是「内容字符」而非「呈现样式」,语义上属于写作/编辑职责(内容侧决定用什么字符);排版职责是把给定的字符正确呈现。渲染层兜底可做,但会模糊「final.html 是 final_article.md 的忠实渲染」这一当前保真模型。

### 方案 C:手改冻结文章标题 + 标注 WORKAROUND
- 代价:
  1. 直接违反档 52/53 禁令(禁止修改前四阶段产物),且会被 verify_receipt 发现:`final_article.md` 是 zh_human_writing 的 output,receipt 绑定其 output_hashes;改动 → 重算失配。
  2. resume 行为:invalidated_from = zh_human_writing → agent 阶段重跑(live 模式 AWAITING_AGENT,需 agent 重新执行 zh 去 AI 味)→ **重新生成 final_article.md**。
  3. **死循环(如实指出)**:标题引号来自 super_writer 产物;zh 阶段 `rewrite_quote=deny`、`change_title` 仅 hard-residue 才动 → 半角引号大概率原样保留 → 再次卡预检。除非同时改 super_writer/article.md(进一步伪造中间态,性质更差,不在考虑内)。
  4. 即使当前这篇放行,下一篇文章仍会随机复现——方案 C 连「治标」都算不上,只是单篇绕行。

### 方案 D:调整 publish 入口门槛,建议性 WARN 与阻断性 ERROR 分级
- 事实评估(不推荐不执行):
  1. **倾向「修正分类错误」的证据**:validator 设计语义就是 WARN 不阻断(退出码 0、「可粘贴,请人工确认」);publish 层把 WARN 提到与 ERROR 同权,是 hammer.1 时的保守策略,把「人工确认」在无人值守链路上变成了「自动阻断」——执行层与校验层分级语义不一致。
  2. **倾向「降低阈值」的证据**:`29864fe` 明确写「本次真实发布要求 ERROR=0 且 WARNING=0」,是有意为之的从严设计;半角引号在公众号排版中确属质量问题(正文中英文引号混排不美观),并非完全无害。若「分级」实现为「WARN 一律静默放行」,则是事实上的降低阈值。
  3. 我的判断:**正确形态 = 恢复 validator 的分级语义 + 补一个显式人工确认通道**(如 `--allow-warnings <原因>` 标志 + 审计记录,或把「人工确认」显式化到管线编排层),而不是单纯放开。单纯放开 = 降低阈值;带显式放行 + 留痕 = 修正分类。最终由你裁决。
  4. 注意:即便 D 放行引号 WARN,方案 6 表中第 2 类(leaf 包裹缺失)是渲染缺陷信号,放行它有真实样式丢失风险——分级时应按规则区分,不能一刀切。

---

## 第四步 副作用总账更正

- 档 52 预检发现的「草稿箱 3→1」经用户确认为**本人手动删除**,与流水线无关,**结案**。
- `audit/side-effects/ledger.md` 已更正:
  1. 更新记录行追加档 53 更正说明;
  2. 累计汇总表格新增「草稿箱现存量 1 份(结案)」;
  3. 档 52 条目内「草稿箱异常记录」段追加结案注记。
- 草稿箱基线自此为 **1 份**(现存事件稿「vibe-coding-guide v2.1 升级」,草稿 #3)。

---

## 结论

1. **来源**:半角引号由 super_writer 大纲阶段生成(`outline.md` / `article.md` L7),zh_human_writing 逐字透传;aihot 素材无此内容。
2. **缺口**:zh-human-writing 无标点规范化机制,且 preserve + rewrite_quote deny 约束体系倾向不动引号——系统性缺口,任何含 ASCII 引号的标题都会卡住。
3. **门槛**:WARNING=0 设于 `publish_wechat_draft.py` L413-416(源自 4053308 预检原则,29864fe 扩展为 WARN 同权);全仓共 3 类 WARN 会被该门槛阻断(半角标点/leaf 未包裹/解析中断)。
4. **方案**:A/B/C/D 代价如上,均未执行。C 已证伪(死循环)。D 的性质判断:带显式人工确认的「分级」= 修正分类错误;静默放行 = 降低阈值——由你裁决。
5. **本档零写入代码/内容/配置**,唯一写入为本报告与 ledger.md 更正。查完停机。
