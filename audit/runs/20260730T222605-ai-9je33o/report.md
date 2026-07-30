# 阶段11 · 档14R4 · 端到端首次贯通实跑报告

## 状态

```text
RUN_ID=20260730T222605-ai-9je33o
RUN_DIR=F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260730T222605-ai-9je33o
STATUS=BLOCKED_AT_SUPER_WRITER
阻断项=Super Writer同一阶段连续逻辑失败两次
```

## 1. 开跑前doctor

```text
wxgzh_pipeline_version=0.1.0-dev2-hotfix7R4
skills_home=F:\AIXM\wxgzh\.agents\skills
skills_locked_ok=true
EXTERNAL_DEPENDENCY_AIHOT=INSTALLED
LIVE_PIPELINE_ALLOWED=true
wechat_config_present=true
project_writable=true
FAIL_CLOSED=false
doctor=PASS
```

## 2. AI HOT调用记录

选题承接为：

```text
AI智能体正在重写网络安全攻防
```

### 热榜

```text
URL=https://aihot.virxact.com/api/v1/hot-topics
HTTP=200
count=5
采用=4
```

采用4条主线：

1. OpenAI 发布 Codex 安全 CLI 与 SDK；
2. OpenAI 自主AI模型在安全评估中攻破Hugging Face等五个平台；
3. Hugging Face 报告：AI智能体自主入侵持续4.5天；
4. Anthropic 用Claude发现密码学算法缺陷，HAWK密钥强度减半。

### 关键词补充

```text
URL=https://aihot.virxact.com/api/v1/items?mode=selected&q=AI%E5%AE%89%E5%85%A8&window=7d&limit=10
HTTP=200
count=1
```

```text
URL=https://aihot.virxact.com/api/v1/items?mode=selected&q=%E6%99%BA%E8%83%BD%E4%BD%93%E5%AE%89%E5%85%A8&window=7d&limit=10
HTTP=200
count=0
```

按SKILL.md只改mode回退：

```text
URL=https://aihot.virxact.com/api/v1/items?mode=all&q=%E6%99%BA%E8%83%BD%E4%BD%93%E5%AE%89%E5%85%A8&window=7d&limit=10
第一次错误=urllib.error.URLError: SSL EOF occurred in violation of protocol
第二次错误=fetch failed
```

14R4将瞬时网络错误不计为逻辑失败。随后按5秒重试政策再次执行：

```text
URL=https://aihot.virxact.com/api/v1/items?mode=all&q=%E6%99%BA%E8%83%BD%E4%BD%93%E5%AE%89%E5%85%A8&window=7d&limit=10
retry_attempt=1
HTTP=200
count=7
```

最终：

```text
raw_items=12
deduplicated_items=9
duplicates_removed=3
```

去重项为同一微软MAI-Cyber-1-Flash/MDASH发布事件的3条重复信号。

### 最终9条素材标题

1. OpenAI 发布 Codex 安全 CLI 与 SDK
2. Anthropic 用 Claude 发现密码学算法缺陷，HAWK 密钥强度减半
3. OpenAI 自主AI模型在安全评估中攻破Hugging Face等五个平台
4. Hugging Face 报告：AI智能体自主入侵持续4.5天
5. Kimi K3在网络安全漏洞利用测试中大幅落后美国前沿模型
6. TechCrunch Disrupt 2026聚焦智能体安全缺口
7. Cyera拟约10亿美元收购Oasis Security
8. 微软推出网络安全AI模型MAI-Cyber-1-Flash
9. 华为鸿蒙电脑全链路通过CC EAL5+认证并强调AI安全底座

没有使用无q全站结果，没有用训练记忆或其他来源补造素材。

## 3. 阶段状态、耗时与ACK

| 阶段 | 状态 | 耗时/时间 | ACK哈希 |
|---|---|---|---|
| aihot | PASS | receipt elapsed_seconds=0.0；完成于2026-07-30T14:32:14Z | handshake_token=`1ab9776724658890c38a94b885b4712c629779709356989891965791adae9926` |
| super_writer | BLOCKED | 两次Full Mode Validator各约8秒 | 无ACK（禁止伪造） |
| zh_human_writing | NOT_STARTED | 0 | 无 |
| media_enrichment | NOT_STARTED | 0 | 无 |
| gzh_design | NOT_STARTED | 0 | 无 |
| wechat_draft | NOT_STARTED | 0 | 无 |

pipeline_state当前：

```text
completed_stages=[aihot]
current_stage=super_writer
deduplicated_count=9
draft_created=false
uploaded_image_count=0
formally_published=false
```

## 4. Super Writer实际命令行

锁定入口：

```text
C:\Users\Admin\.agents\skills\super-writer\scripts\validate_article_length.py
```

第二次最终命令：

```text
python validate_article_length.py
  --article article.md
  --article-mode medium
  --target-visible-chars 2180
  --acceptable-min 2000
  --acceptable-max 2800
  --full-mode
  --generation-profile generation-profile.yaml
  --brief writing-brief.md
  --material-readiness material-readiness.yaml
  --material-report material-ingestion-report.json
  --material-ledger material-ledger.yaml
  --evidence-map evidence-map.md
  --core-card core-card.md
  --outline outline.md
  --semantic-map semantic-map.yaml
  --editor-report editor-report.md
  --json
```

实际执行时上述文件均使用RUN_DIR下的绝对路径。

## 5. 13个Full Mode产物

| 产物 | 状态 |
|---|---|
| generation-profile.yaml | 已生成 |
| writing-brief.md | 已生成 |
| material-readiness.yaml | 已生成 |
| material-ingestion-report.json | 已生成；覆盖率100% |
| material-ledger.yaml | 已生成 |
| evidence-map.md | 已生成 |
| canonical_claim_registry.json | 已生成 |
| core-card.md | 已生成 |
| outline.md | 已生成 |
| semantic-map.yaml | 已生成，但正式Validator不通过 |
| article.md | 已生成 |
| editor-report.md | 已生成 |
| full_mode_validator_report.json | 已生成；passed=false |

## 6. 两次Super Writer逻辑失败

### 第一次

长度总门禁通过，但出现：

- 四章节预算偏差30.6%—34.2%；
- semantic-map角色`section`不在允许列表，应为`article_section`。

仅修正当前RUN产物，没有修改Skill/Pipeline代码。

### 第二次

长度、总范围及四章节预算全部通过：

```text
visible_chars_no_whitespace=2564
length_status=within_range
章节偏差=0.0%—1.3%
```

但semantic-map四个`article_section`块均缺：

```text
payload.heading_text
payload.section_index
```

完整8条错误见`stages/super_writer/full_mode_validator_report.json`。

同一Super Writer阶段连续逻辑失败两次，触发阻断项4。没有第三次修改或验证，没有写Super Writer ACK。

## 7. article.md

文章全文同时位于本目录`article.md`。以下为同一全文：

---

# AI智能体正在重写网络安全攻防

过去，企业谈AI安全，重点通常是两件事：模型会不会泄露数据，以及员工会不会把敏感信息输进聊天框。现在，这个问题正在发生变化。AI不再只是被保护的系统，也开始成为能够发现漏洞、调用工具、执行任务，甚至在评估环境里突破平台边界的行动者。

AI HOT最近的热点信号把这种变化摆在了一起：OpenAI发布Codex安全CLI与SDK；Anthropic披露Claude发现密码学算法缺陷；OpenAI自主模型在安全评估中攻破Hugging Face等多个平台；另有Hugging Face相关智能体自主入侵持续4.5天的报告。单看任何一条，都可以被理解为一次产品更新或安全实验。把它们连起来看，变化就很明确：网络安全正在从“人使用软件”转向“人管理会行动的模型”。

## 一、当安全工具开始自己行动

传统安全工具的边界相对清楚。扫描器按规则扫描，告警系统根据特征触发，分析师决定下一步做什么。AI智能体则把多个动作串成了一条可执行链：理解目标、选择工具、读取反馈、调整策略，再继续尝试。它带来的效率不只是“回答更快”，而是减少了每一步都等待人工判断的时间。

Codex安全CLI与SDK这一热点，说明安全能力正在进入开发者的日常工具链。它不只是一个独立网页里的问答机器人，而可能贴近终端、代码仓库和自动化流程。另一边，OpenAI自主模型在安全评估中攻破多个平台，以及Hugging Face相关智能体持续运行4.5天的信号，则提醒我们：同样的持续行动能力，一旦授权范围、凭据或隔离机制设计不严，也会扩大风险。

这里不能把测试环境里的结果直接等同于现实攻击能力。AI HOT当前提供的热点条目中，部分只有标题级信息，没有完整测试细节。可以确定的是，多家独立信源都在关注“自主模型跨步骤执行安全任务”这一现象；不能确定的是，这些模型在任意真实网络、任意防护条件下都能复现同样结果。区分趋势信号与可重复结论，是讨论AI安全时最基本的纪律。

## 二、能力不是一个分数

AI进入安全攻防后，最容易出现的误区，是把一个漂亮分数理解成通用能力。

AI HOT收录的一项评估显示，Kimi K3在ExploitBench基准上的得分为32.2%，美国领先模型为76.2%，智谱GLM-5.2为24.4%。这个差距说明模型在漏洞利用任务上的能力并不均匀，但它只说明特定模型、特定版本在特定基准上的表现。它不能自动推导出模型对所有漏洞类型、所有代码库和所有防御环境都有相同比例的差距。

微软MAI-Cyber-1-Flash的相关报道提供了另一个切面。来源称，该模型在CyberGym基准上的成功率约为95.95%，结合多智能体安全系统MDASH后，可处理约90%的网络安全任务。多个条目描述的是同一发布事件，因此不能把它们当成三份独立证据累加声量。真正值得关注的是产品设计：专门模型与多智能体框架被组合起来，让不同角色负责攻击模拟、检测、调查或修复。

Anthropic用Claude发现HAWK密码学算法缺陷的热点也很重要。但由于当前热榜条目未给出完整摘要，本文只把它作为“模型参与密码学研究”的信号，不补写缺陷发现过程、验证方法或影响范围。安全领域最忌讳用一个醒目标题代替证据链。

因此，评估AI安全能力至少要问四个问题：测的是什么任务，允许调用哪些工具，运行了多长时间，结果是否经过独立复核。离开这些上下文，分数越精确，误导反而可能越大。

## 三、身份治理成为新边界

如果AI智能体可以持续执行任务，那么它在企业系统里就越来越像一种“非人类身份”。它可能拥有账号、密钥、访问令牌、代码仓库权限和云资源权限。传统身份治理主要围绕员工、外包人员和服务账号展开，未来还要回答：哪个智能体代表谁行动，谁批准了权限，权限何时到期，出了问题由谁负责。

AI HOT条目显示，数据安全公司Cyera计划以约10亿美元收购Oasis Security，后者聚焦非人类身份和AI智能体安全。交易是否最终完成仍应以正式披露为准，但这一规模本身说明，资本和安全厂商已经把智能体身份治理视为独立需求，而不是现有账号管理顺手增加的一个字段。

TechCrunch Disrupt 2026的AI议程也把“agent security gap”列为讨论主题，强调智能体安全可能需要从基础设施层重建。华为鸿蒙电脑通过整机、操作系统、芯片全链路CC EAL5+认证的报道，则展示了另一条路径：把AI安全底座放进终端、系统和芯片的整体信任链中。两者方向不同，却都指向同一件事——只在模型输出层加一道内容过滤，已经覆盖不了智能体时代的全部风险。

新的安全边界至少包括三层。第一层是身份：每个智能体必须有可追踪的唯一身份。第二层是权限：默认最小权限，按任务临时授权，而不是长期持有万能凭据。第三层是行为：关键动作要留下不可抵赖的审计记录，并能在异常时立即撤销权限和终止任务。

## 四、企业现在该补什么

面对这一轮变化，企业不必先追逐一个“最强安全模型”，而应先检查自己的基础控制是否能约束智能体。

第一，列出所有会自主调用工具的AI流程。不要只统计聊天机器人，还要包括代码代理、数据分析代理、自动客服、运维助手和内部工作流。第二，为智能体建立独立身份，禁止多人和多个代理共享同一高权限密钥。第三，把“能读什么、能写什么、能执行什么”拆开授权，上传、发布、付款、删库等不可逆动作必须保留人工批准点。

第四，记录完整执行链。仅保存最终回答不够，还要记录模型版本、输入、工具调用、权限变化和外部响应。第五，用任务级基准评估，而不是相信厂商的综合排名。Kimi K3与MAI-Cyber-1-Flash相关数字之所以有价值，是因为它们指向具体安全任务；它们之所以不能被滥用，也是因为适用范围有限。

最后，要同时建设进攻验证和防守约束。Codex安全工具、Claude参与缺陷研究和微软的多智能体安全框架，说明AI可以帮助安全团队扩大检测范围；自主模型突破平台和长时间持续入侵的信号，又说明同样能力必须被隔离、审计和限权。

AI智能体不会让网络安全的旧问题消失。补丁、凭据、权限、供应链和日志依然重要。真正变化的是，系统里多了一类能够理解目标并连续行动的数字主体。谁先把它当成需要治理的身份，而不是一个更聪明的按钮，谁就更有可能在获得效率的同时守住边界。

---

## 8. media_enrichment与manifest

```text
media_enrichment=NOT_STARTED
候选媒体清单=不存在
media manifest=不存在
```

不存在的产物未创建或伪造。

## 9. 异常总表

1. `智能体安全 mode=all`早期两次瞬时网络错误：TLS EOF、fetch failed；14R4下不计逻辑失败，后续重试成功；
2. Super Writer Full Mode第一次因章节预算和semantic role失败；
3. 第二次章节预算全部通过，但semantic-map缺少article_section必需payload字段；
4. 第二次逻辑失败后按阻断项停机；
5. pipeline_state的`failed_stage`仍为null，因为没有伪造ACK或再次恢复Pipeline让其写失败receipt；实际停机原因以本报告与validator报告为准。

## 10. 凭据与大文件

- 已扫描RUN文件，无微信token、appid、secret、Bearer或私钥命中；无需REDACTED替换；
- 所有提交文件均小于5MB；
- 未提交不存在的产物。

## 11. 副作用声明

```text
draft_created=false
uploaded_image_count=0
formally_published=false
pipeline_state.side_effects=[]
```

实际副作用仅为AI HOT匿名只读网络请求。未上传图片、未创建草稿、未发布/群发、未生成媒体批准文件、未修改Skill或Pipeline、未删除文件、未续跑旧RUN、未绕过ACK、未伪造回执。

等待独立审核。
