# 档 38 — 内容静默丢失影响面核查 + A/B/C 判定

- 日期:2026-08-02(Asia/Shanghai)
- 性质:纯只读核查;唯一写入为本报告。未修改 `.agents\skills` 任何文件、未执行安装器、未 relock --apply、未改 lock/配置、未调用微信接口、未跑 Pipeline、未删除任何文件。
- 工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(branch `dev/0.1.0-dev2`,核查起点 HEAD `77560dd`)

---

## 第一部分 问题 A 影响面(本档核心)

### 1. parse_article() 实现

- 文件:`F:\AIXM\wxgzh\.agents\skills\gzh-design\scripts\render_article.py`
- 函数:`parse_article`,L79-104。完整源码:

```python
def parse_article(md: str) -> dict:
    """Parse H1 title, an intro paragraph, and H2 chapters with paragraphs."""
    lines = md.replace("\r\n", "\n").split("\n")
    title = ""
    intro = ""
    chapters: list[dict] = []
    cur: dict | None = None
    for ln in lines:
        st = ln.strip()
        if not title and st.startswith("# ") and not st.startswith("## "):
            title = st[2:].strip()
            continue
        if st.startswith("## ") and not st.startswith("### "):
            cur = {"title": st[3:].strip(), "paras": []}
            chapters.append(cur)
            continue
        if st.startswith("#"):
            continue
        if not st:
            continue
        if cur is None:
            if not intro:
                intro = st
            continue
        cur["paras"].append(st)
    return {"title": title or "未命名", "intro": intro, "chapters": chapters}
```

### 2. 确切行为

- 首个 `# ` 标题之后、首个 `## ` 之前的非空行:只取**第一行**作为 `intro`(L99-102,`if cur is None: if not intro: intro = st`),**其余所有行被静默丢弃**。
- 丢弃行为无任何日志、警告、计数或落盘记录:`parse_article` 本身无输出;`main()`(L180 起)在渲染后只输出 `validate_html` 的 errors/warnings,不涉及 intro 区域的统计。
- `intro` 的消费方式(同在 `render()` 内,`render_article.py` L107-131):
  - L119:`subtitle = (parsed.get("intro") or ...)[:48]` → 封面子标题,截 48 字符;
  - L120:`hammer_cover(..., strike="别急着划走", ...)` → 封面;
  - L127-128:`parsed["intro"][:40]` → oneliner 卡片,截 40 字符。
- 即:**即便只有一段 intro,HTML 中也只呈现其前 40~48 字符**;多段时第 2 段起完全消失。章节正文段落(`cur["paras"]`)不受影响,经 `hammer_para`(generate_hammer_upgrade_samples.py L753-756)完整输出。

### 3. 两篇归档 RUN 逐段比对

判定方法:取 `stages/zh_human_writing/final_article.md` 首个 `## ` 之前的全部段落,逐一在 `stages/gzh_design/final.html` 中检索段落首句/中段/尾句指纹。

**RUN1 `20260731T135947-ai-bbg4al`** — 首 `## ` 前 = 标题 + 2 段:

| 段落 | 位置 | final.html 中是否存在 | 结论 |
|---|---|---|---|
| para1(L3,86 字符) | 首句/中段在 | 「AI安全的讨论正在从」「转向一个更难的问题」存在;「谁来约束它的权限」「谁来还原它的行动链」「人工停止点」不存在 | **部分保留**(仅封面子标题前 48 字 + oneliner 前 40 字,后半截断) |
| para2(L5,导语段) | 首句/中段/尾句 | 「本轮AI HOT素材把这种变化摆在了一起」「这些动向说明」均不存在 | **完全丢失** |

**RUN2 `20260801T182628-topic-ui5f7p`** — 首 `## ` 前 = 标题 + 1 段(198 字符):

| 段落 | final.html 中是否存在 | 结论 |
|---|---|---|
| para1(L3) | 「数据库的访问控制」「过去讨论智能体」存在(前 ~40-48 字);「出了问题找谁」「这一轮 AI HOT 素材把这个问题摆得很集中」「安全模型和终端信任链也在同时下沉」不存在 | **部分保留**(整段无丢失,但导语后半截断) |

**两篇共同结论**:首个 `## ` 之前的内容从未完整进入 HTML。RUN1 存在一整段完全丢失;RUN2 无整段丢失但导语被截断。章节正文未发现同类丢失(章节段落在 HTML 中完整渲染)。

### 4. 被丢弃原文全文与对「用户肉眼验收通过」结论的影响

RUN1 被完全丢弃的 para2 原文(L5):

> 本轮AI HOT素材把这种变化摆在了一起。Anthropic调查发现Claude模型在网络安全评估中入侵三家组织生产基础设施；Google Cloud为AlloyDB加入面向AI智能体的IAM群组认证；微软推出专用网络安全模型与多智能体框架；Cyera计划收购专注非人类身份的Oasis Security；产业议程则直接讨论“智能体安全缺口”。这些动向说明，AI已经不只是安全系统保护的对象，也正在成为安全流程里的行动者。

影响:
- 该段是全篇素材导语,浓缩了 5 条资讯(Anthropic / Google Cloud / 微软 / Cyera / 产业议程)。HTML 读者只能看到第一段前 40 字 + 章节正文,无法感知素材全貌;封面 oneliner 以第一段开头替代导语,正文开头呈「断裂」观感。
- 「用户肉眼验收通过」的历史结论需要加限定:若验收基于 final_article.md(内容完整),结论成立;若基于 final.html(实际发布形态),则 RUN1 的导语段缺失未被发现。无论如何,这是 gzh_design 阶段的真实内容保真缺口,与验收人是否看到无关。

### 5. 事件 RUN 同位核查

- 文件:`audit/runs/20260801T231452-vibe-coding-guide-v2-1-1vg6jx/zh_human_writing/final_article.md`,首 `## `(L19)前 = 标题 + **8 段**(L3-L17)。
- `gzh_design/final.html`:仅 para1 首句存在(截断),para2-8 的 7 段**全部完全丢失**(逐一检索均为 False)。
- 7 段被丢弃原文全文:
  1. L5「说的是我做的 vibe-coding-guide。我说它会给 AI 编程加一道保险：遇到 rm -rf、遇到 DROP TABLE、遇到把密钥写进文件，它会停下来，等你确认。」
  2. L7「今天先认个账：第一版，它拦不住任何东西。」
  3. L9「它是一份 Markdown 规矩本，全部效力来自「请 AI 自觉」。AI 心情好就遵守，上下文一长、或者你开了跳过权限的开关，规矩本就是一页纸。」
  4. L11「那不叫安全气囊。那是贴在方向盘上的一张纸条，写着「出事时请自行减速」。」
  5. L13「更吓人的是，这个洞一直藏着。写「禁止把私钥写进文件」这条规则时，代码里有个小错误，导致这条规则每次都执行失败、然后静默跳过。而当时的测试套件有 32 条断言，全部通过——因为那 32 条里，一条私钥测试都没有。」
  6. L15「「测试全绿」和「功能能用」，是两件完全不同的事。」
  7. L17「所以今天我把它升级到了 v2.1.0。从早上开始审查，到晚上 22:00 真机验证通过，一天发了四个版本。这次，纸条是真的变成锁了。」
- 说明:归档中的 `UNCONTROLLED.md` 未记载该内容丢失点;但代码与产物事实一致,同一 `parse_article` 行为导致,交接文档对事件 RUN 的描述与本轮取证互相印证。

---

## 第二部分 与「别急着划走」的关联

### 6. 代码位置与关系

- 「别急着划走」为 `render_article.py` L120 `hammer_cover(..., strike="别急着划走", ...)` 的写死参数;`hammer_cover` 定义于 `scripts/generate_hammer_upgrade_samples.py` L650。
- 它与 `parse_article` 丢弃 intro 段落属于**同一 render 流程、相邻代码块,但不是同一段逻辑**:一处是内容提取与丢弃,一处是封面组件文案渲染。两者无因果关系。

### 7. 档 23-min「删除线非缺陷」判定是否需重审

**不需推翻**。理由:
- 档 23-min 的留存证据 `audit/runs/20260731T135947-ai-bbg4al/obs61-strikethrough/diagnosis.md`(commit `ed526eb` 记录)证明:该句不存在于 zh_human_writing 终稿 markdown,是组件写死文案。
- 删除线样式为 hammer 官方装饰(`font-size:15px;text-decoration:line-through;text-decoration-color:#B3593B;text-decoration-thickness:1.5px`),且 `validators/validate_theme_identity.py` L59-62 明确处理了低对比色 `rgba(202,202,199,0.35)` 的合法用法(line-through 元素限定检查),不是隐藏文本缺陷。
- parse_article 丢弃开头段落是**独立缺陷**,与删除线文案无关;建议在 OBS-73 下作为独立问题跟踪(修复需触碰被锁 gzh-design,按 OBS-59/60/62 同类流程留待 gzh-design 升版)。

---

## 第三部分 全链保真缺口盘点(OBS-73)

### 8. 逐阶段内容保真校验手段

| 阶段 | 校验内容 | 校验手段(文件) | 是否校验内容完整性 |
|---|---|---|---|
| aihot | `deduplicated_items.json` 存在且 count>=1 | `wxgzh_pipeline/stages/aihot.py` content_validate | 否,仅存在性+数量 |
| super_writer | `full_mode_validator_report.json` `passed=true` + 章节数 + 长度模式 | `wxgzh_pipeline/stages/super_writer.py` content_validate | 否,结构/长度/语义映射,不校验事实 |
| zh_human_writing | 六项零门禁(NEW_UNREGISTERED_FACTS/NUMBER_CHANGES/ATTRIBUTION_LOSS/QUALIFIER_LOSS/CLAIM_SEMANTIC_CHANGE/HARD_RESIDUE)+ 禁用词 + fidelity_guard 数字/日期/URL 存在性比对 | `wxgzh_pipeline/stages/zh_human_writing.py`;`zh-human-writing/scripts/fidelity_guard.py` | **部分**:字面保真(数字/日期/URL 存在性),不核来源 |
| media_enrichment | `media_manifest.json` + `article_image_bindings.json` + `validate_media_bindings` + bindings 引用冻结文章 sha | `wxgzh_pipeline/stages/media_enrichment.py` content_validate | 否,媒体绑定,非正文保真 |
| **gzh_design** | 结构指纹(组件计数)、章节数 `_count_h2`、execution evidence、theme identity、receipt 链 | `wxgzh_pipeline/stages/gzh_design.py` L33-55;`validators/validate_theme_identity.py` | **否,只校验结构/格式,不校验正文内容** ← 问题 A 的漏检点 |
| wechat_draft | `validate_draft_delta.py`(档 24R:total_count 差=1、update_time 集合子集、新增恰 1 条、deleted/formal/mass/scheduled 全 false) | `validators/validate_draft_delta.py` | 否,只校验草稿数量与时间戳,不校验正文 |

结论:内容保真链到 zh_human_writing 为止;gzh_design 与 wechat_draft 两个阶段均无正文保真校验,问题 A 正是在 gzh_design 阶段漏检。

### 9. gzh_design 阶段加内容保真校验的可行性评估(只评估,不实施)

- 方案 1(段落级指纹,最稳):以 frozen `final_article.md` 的 `parse_article` 结果为准,对每个 md 段落取前 20 字符指纹,断言其在 final.html 的纯文本(去标签/HTML 实体解码后)中存在。代价:需排除 intro 区域截断(封面 48 字 / oneliner 40 字)、HTML 转义(引号、`&` 等)、图片 caption 重复;误报风险低。
- 方案 2(全文覆盖率):HTML 反提取纯文本与 md 做字符级覆盖率/相似度比对。代价:需处理截断、标签噪声、长文阈值调参;误报风险中等(标题、TOC、签名等组件文本与正文重叠)。
- 方案 3(最小改动):仅校验「首个 `## ` 之前的段落数」由 md 的 n 段 → HTML 可见 1 段,发现 n>1 即 FAIL。代价最小,但只覆盖本问题,不覆盖章节正文。
- 建议(不实施):先做方案 3 或方案 1 的 intro 区域变体,纳入 OBS-73;实施位置在 Pipeline 侧 `stages/gzh_design.py` content_validate,不触碰 gzh-design。

---

## 第四部分 问题 B 定位

### 10. 渲染器对 fenced code block 的处理

- **不支持,样式缺失(非样式选项问题)**。证据:
  - 全文无任何 `pre/code` 渲染组件;`hammer_para`(generate_hammer_upgrade_samples.py L753-756)只对文本做 `s(text)` 转义后包 `<p>`。
  - `parse_article` 把 `` ``` `` 当普通行处理,围栏会被并入段落文本。
  - `scripts/validate_gzh_html.py` L98 `CODE_STYLE = re.compile(r"monospace|white-space\s*:\s*pre|...")` 仅是校验器对「检测到等宽样式则豁免」的规则,不是渲染能力。
- 若 markdown 含围栏,反引号将作为字面文本输出,代码以纯文本呈现、无等宽/背景样式。

### 11. 历史文章核查

- 三篇 RUN 的 `final_article.md` 围栏数均为 0(`super_writer` 与 `zh_human_writing` 两处均 0),即**历史文章未出现过 fenced code block**,无法从历史渲染结果验证;问题 B 目前是「能力缺失」而非「已发生渲染事故」。

---

## 第五部分 问题 C 与历史数字可信度

### 12. fidelity_guard.py 判定机制

- 文件:`F:\AIXM\wxgzh\.agents\skills\zh-human-writing\scripts\fidelity_guard.py`,702 行。
- `compare_numbers` L135-183:`extract_numbers`(L36)→ `normalize_number`(L107)→ 两组排序列表 → **存在性双向比对**(原文有而终稿缺 → fail;终稿有而原文无 → fail)。`compare_dates`(L184)/`compare_urls`(L232)/`compare_code`(L267)/`compare_commands`(L316)同构。
- 结论:**纯字面存在性比对,无来源核验**(不查数字真实与否),也不做重数(次数)校验;它只回答「数字有没有被改掉/新增」,不回答「数字对不对」。

### 13. 「授权豁免」通道核查

- `USER_BLANKET_APPROVAL` 与 `COPYRIGHT_POLICY` 为**死配置**:存在但无消费代码(档 35 已完整取证,全仓仅 `stages/__init__.py` L145 元数据暴露)。**不构成任何豁免通道。**
- 无其他 BLANKET / BYPASS / NO_GATE / AUTO_APPROVE / SKIP_APPROVAL / EXEMPT 命名的总开关。
- 功能性开关(`upload_mode`、`BODY_IMAGES_MIN`、`WXGZH_FIXED_MEDIA_ROOT`、`WXGZH_INTEGRATION_RESULT`、`WXGZH_IN_RELEASE_AUDIT`)均为运行参数,非授权豁免。
- 真正的人工批准通道:`producers.py` L733 `meta["await_media_approval"] = True`(discovery 后暂停,orchestrator 返回 `AWAITING_MEDIA_ASSET_APPROVAL`),approval_file 缺失时同样 await(L745-748)。
- 注:事件 RUN 的放行点是 approvals=[] 时 `_media()` 的 continue 分支直接 `_build_media_request(phase="continue")` 走 known_allowed 图表上传(档 35/36/37 已取证),与 `USER_BLANKET_APPROVAL` 无关。

### 14. 两篇归档 RUN 的数字核查(为过 fidelity_guard 而改数字?)

- 独立复算方法:正则提取 `\d+(\.\d+)?(%|％)?`(去百分号后按重数比较),比对 `stages/super_writer/article.md` 与 `stages/zh_human_writing/final_article.md`:

| RUN | super_writer 数字数 | zh_human_writing 数字数 | 缺失 | 新增 |
|---|---|---|---|---|
| 20260731T135947-ai-bbg4al | 12 | 12 | 0 | 0 |
| 20260801T182628-topic-ui5f7p | 12 | 12 | 0 | 0 |

- 两篇 `fidelity_report.json` 亦均为 `NUMBER_CHANGES=0`、六项零门禁、`status=PASS_WITH_REAL_EDITS`。
- 结论:**未发现任何为通过 fidelity_guard 而修改正文数字的痕迹**;历史数字可信度未受问题 C 影响。

---

## 结论汇总

1. **问题 A 成立且为真实内容丢失**:`parse_article` 静默丢弃首个 `## ` 前的第 2 段起全部内容;RUN1 丢失素材导语整段(5 条资讯),事件 RUN 丢失 7 段;RUN2 无整段丢失但导语截断。gzh_design 阶段无任何内容保真校验,是漏检根因(OBS-73)。
2. 「别急着划走」与问题 A 无因果;档 23-min 判定不推翻。
3. 问题 B:渲染器无 fenced code block 支持(纯文本输出),历史 0 处代码块,暂无实际事故。
4. 问题 C:fidelity_guard 为字面存在性比对,无来源核验、无重数校验;两篇归档 RUN 数字 0 差异,无「改数字过门禁」痕迹;无授权豁免通道。
5. 全部修复面均触碰被锁 gzh-design(`render_article.py` 等),按 OBS-59/60/62 同类流程处理;本档不实施任何修复。

- 风险点:若后续文章在开头写入多段导语,丢失将持续且不可见;建议在 OBS-73 下优先落地 Pipeline 侧「intro 段落数」守卫(最小改动,不触碰被锁 skill)。
