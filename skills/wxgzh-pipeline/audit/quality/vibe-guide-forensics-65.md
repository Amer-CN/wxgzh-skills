# 档 65 取证段 — claims 数字缺失与文章代码块缺失成因(纯只读)

- RUN_ID:`20260804T163519-vibe-coding-guide-v2-1-6-7atsk0`
- 性质:**零改动**。未修改任何代码/文章/RUN 产物/批准清单;未调微信;未上传;
  未继续 continue;未调整任何阈值。唯一写入为本报告。
- 复核基线:lock 双侧 `81F9342A…`、台账 7 条、四锁 hash_ok 全 true、doctor PASS。

---

## 第一步 数字去哪了

### 1. 事件 RUN(20260801T231452)6 张图表的数据点(归档只读)

事件 RUN 的 claims 带结构化 `numbers/chart_group/metric_name/series_label`,
discover 生成 **3 组对比图表 × 2 轮编号 = 6 张唯一图表**:

| 图表(唯一) | claim 对 | chart_group / metric | 数据点(series → numbers) |
|---|---|---|---|
| chart-001/…(A-001..A-006,两轮) | C-02 + C-04 | 红线数量 / 红线条数 | v1.0 → 8 条;v1.2.0 → 11 条 |
| chart-00?(A-007..,两轮) | C-07 + C-11 | 协作铁律 / 铁律条数 | v2.1 → 5 条;v1.0 → 4 条 |
| chart-00?(A-013..,两轮) | C-08 + C-13 | 测试覆盖 / 测试断言数 | v1.0 → 32 条;v2.1 → 62 条 |

每张图表的 caption 为「组名·指标名对比(共 n 项):版本 值单位;…」,数据点
完全来自 claims 的 numbers。

### 2. 本次 RUN 的 claims 实际内容(逐条)

`super_writer/canonical_claim_registry.json` 的 5 条 claim(C-01..C-05)字段:
`claim_id / material_id / claim_text / source_url / source_excerpt`——
**零条带 numbers/chart_group/metric_name/series_label**(全量核验)。

### 3. ★逐层定位(结论:c 层丢失)

| 层 | 核验 | 结论 |
|---|---|---|
| a. 素材 → 注入 items | `deduplicated_items.json` 的 summary = 素材全文逐字(含 CHANGELOG);「19 条/25 条/8 条/11 条/四条扩到五条」全部命中 | **数字在** |
| b. items → article.md | `final_article.md` 正文含「红线从 8 条扩到 11 条」「自检清单从 19 条扩到 25 条」「铁律从四条扩到五条」「8 条最小必查」 | **数字在** |
| c. article.md → claims | registry claims 无 numbers/chart_group(见第 2 条) | **★数字在此层丢失** |

- **定位:数字丢失在 c 层——super_writer 阶段的 canonical_claim_registry 构建
  没有把文章事实中的数字登记为结构化 numbers/chart_group/metric_name/
  series_label**。素材有数字(用户已实读确认),a/b 层完整,只有 c 层缺失。
- 事件 RUN 的 claims 带 numbers(其写作按规范提取);本次注入路径下 agent 构建
  registry 时未执行同样的数字结构化登记。
- **登记 OBS-88(中)**:素材注入路径 claim 数字结构化登记缺失——含数字事实
  (8→11 / 19→25 / 4→5)未提取 numbers/chart_group,导致图表零生成。
  修复方向(不在本段修):重跑 super_writer 时按证据链规范登记结构化数字,
  或把「含数字事实必须结构化」纳入 registry 校验。

## 第二步 代码块去哪了

### 5. 素材 deny/ask 文案全量清单(逐条原文)

`hooks/guard-bash.sh`(8 deny + 7 ask)+ `_common.sh` 的 deny()/ask() 模板:

```
deny '这是对根目录或家目录的递归删除，会清空整台机器（铁律 1）'
deny '这是对系统目录的递归删除，会让系统无法启动（铁律 1）'
deny '这会删掉整个当前目录，包括你还没提交的代码（铁律 1）'
deny '强推主分支会永久覆盖远端历史，别人的提交会消失（红线 11）'
deny '这会删除整个数据库，且通常无法恢复（红线 6）'
deny '这是把网上下载的内容直接执行，你没机会看清它要做什么（红线 10）'
deny '递归 777 会把文件权限对所有人开放（红线 7）'
deny '这是直接格式化或写裸设备，会造成不可恢复的数据丢失（铁律 1）'
ask '要安装新依赖了。装之前请先确认包名全称、用途、周下载量和最近更新时间（红线 10）'
ask '这会丢弃你本地还没提交的改动，丢了找不回来（铁律 1）'
ask '这是在改数据库结构。请先出迁移文件再执行，不要直接改库（红线 6）'
ask '这条 DELETE 没有 WHERE 条件，会清空整张表（红线 6）'
ask '强推会覆盖远端历史。确认这个分支只有你一个人在用（红线 11）'
ask '要递归删除文件了。确认路径没写错、且这些文件已经提交过（铁律 1）'
ask '你正在把 .env 加进 Git。密钥一旦提交，删掉也留在历史里（红线 7）'
ask '这是往线上环境部署。确认已经在本地验证过（红线 11）'
```

模板(`_common.sh`):`deny() { emit "deny" "⛔ vibe-coding-guide 拦截：$1。确需执行请你自己在终端手动运行。$CLOSE_HINT"; }`
与 `ask() { emit "ask" "⚠️ vibe-coding-guide 提醒：$1。确认要继续吗？$CLOSE_HINT"; }`。

### 6. 文案在 article.md 中的形态(逐条对照)

| 文案 | 形态 |
|---|---|
| 「这是对根目录或家目录的递归删除…(铁律 1)」 | **散文改写引用**——文章写为「拒绝信息是…会清空整台机器(铁律 1)」,半角括号、非逐字 |
| 「这是对系统目录的递归删除…(铁律 1)」 | 散文改写(取消息后半段「这会让系统无法启动(铁律 1)」) |
| 「这会删掉整个当前目录…(铁律 1)」 | 散文改写(半角括号) |
| 「强推主分支会永久覆盖远端历史…(红线 11)」 | 散文改写(半角括号) |
| 「这会删除整个数据库…(红线 6)」 | 散文改写(半角括号) |
| 其余 10 条 deny/ask(下载执行/递归 777/格式化/装依赖/丢弃改动/改库/DELETE 无 WHERE/强推确认/递归删除确认/.env 进 Git/线上部署) | **完全未出现** |
| ⛔ / ⚠️ 模板与 deny()/ask() 函数本体 | **完全未出现**(见第 8 条) |

- 全文 **fenced code block = 0,反引号 = 0**;5 条被引用的文案全部以散文/行内
  引号形态出现,无一以代码块或行内代码呈现。

### 7. ★代码块缺失成因

- a. **items 保留了 shell 原文?是**——注入 items 的 summary 为素材全文逐字
  (含 deny()/ask() 函数、15 条文案与 ⛔ 模板),a 层无丢失。
- b. **super_writer 是否指示过代码块形态?否**——本 RUN 的 writing-brief.md /
  outline.md 未包含任何代码块/命令块呈现要求;super-writer 产物规范也未强制
  技术文案以代码块呈现(skill 中关于命令的建议属 zh_human_writing 的 guard
  保护口径,非写作形态指示)。
- c. **是否有环节把代码内容转成散文?是**——agent 写作时把 deny 消息改写为
  散文引用(「拒绝信息是…」),shell 原文/函数/⛔ 形态未保留;无任何环节要求
  代码块 → 文章零代码块。

### 8. ★⛔ 核对(_common.sh blob 7389e536)

- **用户指认成立**:⛔ 位于 `_common.sh` 的 `deny()` 模板
  (`"⛔ vibe-coding-guide 拦截：$1。…"`),blob `7389e5363cba` 已核对。
- ⛔ 进入 items?**是**(items summary 含 _common.sh 全文,含该模板)。
- ⛔ 进入 article.md?**否**(全文 0 处 ⛔;guard-bash.sh 本身无 ⛔ 字符,
  其 15 条文案的 ⛔ 前缀由 deny()/ask() 模板注入)。

## 第三步 结论

### 9. 若要带代码块与数字图表,重跑哪些阶段

- **数字图表**:根因在 c 层(claims 无 numbers)。需要重跑
  `super_writer`(registry 构建,把 8→11 / 19→25 / 4→5 登记为
  numbers+chart_group+metric_name+series_label)→ `zh_human_writing`
  (registry 是 upstream,receipt 哈希绑定,必重跑)→ `media_enrichment`
  discover(图表生成)→ 批准点。**这是「重跑上游阶段产出新文章」= 正常流程**。
- **代码块**:根因在写作形态。需要重跑 `super_writer`(写作指示:shell 文案
  以 fenced code block 呈现;gzh-design 渲染已支持,档 43 已修)→
  `zh_human_writing`(fidelity 保护代码)→ `media_enrichment` →
  `gzh_design`。
- ★**「修改已产出文章 / 手工补字段」是红线,两个方案都不包含它**;即便只想
  给现有 registry 补 numbers,也属于修改 frozen 写作产物,必须走正常重跑。

### 10. 两方案代价对比(只给事实,不做选择)

| | A 保留现文章,仅补图表 | B 重跑 super_writer(代码块+数字图表) |
|---|---|---|
| 重跑范围 | super_writer(registry 重建,文章文本可保持不变)+ zh_human_writing + media discover + 批准点 | super_writer(全文重写)+ zh_human_writing + media discover + 批准点 + gzh_design |
| 数字图表 | 可生成(文章数字 8/11/19/25/4/5 可支撑三组对比:红线 8→11、铁律 4→5、清单 19→25) | 可生成(写作时直接登记) |
| 代码块 | 无(文章不变,代码块形态依旧缺失) | 有(写作指示代码块) |
| 技术文媒体形态问题 | 仍在:网页正文图 0、可批准候选仍可能 <6,需媒体形态裁决 | 仍在(图表增加候选,但正文图/数量门槛依旧需要内容裁决) |
| 风险 | registry 重建与文章文本的对应需 agent 严格保真(数字与文章一致) | 全文重写引入新保真面(fidelity 需重新全过) |

### 11. 不选择,等用户裁决。

## 复核(第 12-13 条)

- 本段零改动:无代码、无产物、无微信、无草稿(唯一写入为本报告)。
- lock 双侧 `81F9342A617893FBE3C51C4FCDCFFCB89E76D43EE4735F5FDB81B6422B951058`
  未变;台账仍 7 条;doctor PASS(四锁 hash_ok 全 true)。

## 变更文件

- `audit/quality/vibe-guide-forensics-65.md`(本报告;OBS-88 登记于此,不在本段修复)
