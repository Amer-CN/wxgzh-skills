# 阶段11 · 档14R2 · 停机审计报告

## 状态

```text
RUN_ID=NO-RUN-20260730T2145-aihot-skill-403
STATUS=BLOCKED_BEFORE_RUN
阻断项=同一阶段连续失败两次
```

本次尚未选定选题，未启动 Pipeline RUN，因此没有真实 Pipeline RUN_ID/RUN_DIR、article.md、pipeline_state.json、AI HOT输出或阶段ACK。为避免伪造，本目录只提交本报告。

## 1. AI HOT SKILL.md 规定的正式调用方式

读取文件：

```text
C:\Users\Admin\.agents\skills\aihot\SKILL.md
version=1.2.1
```

该文档未提供独立CLI命令或Python入口函数。正式方式是：在会话内加载已安装AI HOT Skill，由Skill根据用户意图选择其规定的匿名只读能力。

原文：

> 1. 根据意图选择下面唯一的默认入口。
> 2. 使用服务端参数表达范围；不要先拉大列表再用本地关键词代替 `q`。
> 3. 按 API 顺序选择最重要的 3—8 条，用 `links.aihot` 作为标题主链接。
> 4. 只基于返回内容总结；证据不足就明说，不用训练记忆补成“实时结果”。

支持的意图/参数包括：

- 当前最热：`/api/v1/hot-topics`；
- 过去24小时：selected + window=24h；
- 最近一周：selected + window=7d + limit=10；
- 公司/产品/主题关键词：selected + q + window；
- mode：selected/all；window：24h/7d；category；q；limit；cursor；by。

关键词空结果回退原文：

> 关键词查询精选池返回空集时，用完全相同的参数再查一次 `mode=all`。

当前热榜能力原文：

> “当前最热／最近在爆什么” | `/api/v1/hot-topics`

本档遵守更正：主流程没有自行拼接URL，没有直接访问AI HOT HTTP接口。

## 2. 开跑前doctor

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

## 3. AI HOT正式Skill调用与连续失败

目标意图：通过已安装AI HOT Skill获取当前热榜，选出至少3条相关素材支撑的新选题。

### 第一次正式Skill调用

调用形态：

```text
WorkBuddy会话代理加载 C:\Users\Admin\.agents\skills\aihot\SKILL.md
意图=当前最热的AI/科技热点
输出要求=结构化条目与候选选题
```

结果：

```text
403 This API can only be used with the WorkBuddy client.
```

### 第二次正式Skill调用

调用形态：与第一次相同，改用默认执行模型重试一次，仍由会话代理加载正式AI HOT Skill。

结果：

```text
403 This API can only be used with the WorkBuddy client.
```

这不是AI HOT返回0条，而是WorkBuddy执行层拒绝了两次Skill代理调用。

按档14R2阻断项4：同一阶段连续失败两次，立即停机。

## 4. 选题与素材

```text
选题=未选定
最终素材条数=0（未获得Skill调用结果，不代表AI HOT数据为空）
标题列表=无
```

没有改用裸HTTP，没有用训练记忆或其他新闻源补造素材。

## 5. Pipeline与阶段产物

```text
Pipeline RUN=未启动
RUN_DIR=无
AIHOT ACK=无
Super Writer命令=未执行
13个Full Mode产物=均未生成
article.md=未生成
zh-human-writing=未执行
media_enrichment=未执行
media manifest=未生成
AWAITING_MEDIA_ASSET_APPROVAL=未到达
```

没有创建占位article.md、pipeline_state.json、fetch_log.json、raw_items.json或deduplicated_items.json，避免把不存在的真实产物伪造成RUN证据。

## 6. 异常记录

1. AI HOT正式Skill代理调用连续两次被执行层403拒绝；
2. Git审计路径规范要求RUN_ID，但实际RUN未创建；本报告使用明确的`NO-RUN-...`审计标识，避免伪造Pipeline RUN_ID。

## 7. 凭据与大文件

- 本报告不含微信token、appid、secret、cookie或API Key；无需REDACTED替换；
- 无单文件超过5MB；
- 未提交任何RUN产物，因为RUN不存在。

## 8. 副作用声明

- 未直接访问AI HOT HTTP接口；
- 未启动或续跑Pipeline RUN；
- 未续跑两个旧RUN；
- 未写入任何RUN_DIR；
- 未修改任何Skill、Pipeline或已有仓库文件；
- 未上传图片；
- 未创建微信草稿；
- 未发布/群发；
- 未删除任何文件或目录；
- Git仅新增本审计报告；
- 未合并PR，未amend/rebase/force push。

等待独立审核。
