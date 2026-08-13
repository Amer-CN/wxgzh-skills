# 档71C-2 收尾 — OBS-119 组件载体以实测可见性为唯一事实源

- RUN: 20260804T174355-vibe-coding-guide-v2-1-6-by4s00(仅作 fixture,本档零写入)
- 基线: pipeline HEAD 5374b5c → 本档 commit A 34ca3e7;gzh-design HEAD 5791e63 零改动
- lock: E2201B115C9E9BF9B78E5C2BCFA71801D3D2A7626788B279224D22199D931ECE 双侧未变
- 决策依据: 档71C-2 收尾指令(S12 裁决后,C 路线降范围收尾;第 6/7/8 步移交 71C-2B)

---

## ① 0e 与 10b/10c 并排表

0e 三组快照的原始文件未落盘(上一会话仅留交接记录),本档以交接记录为 0e 基准,
10b/10c 为同口径复算,不重跑覆盖任何 RUN 产物。

### 0e① vs 10b: 13 类探针三值表(ctrl_visible, sentinel_missing, unsupported)

| 类 | 0e①(交接记录) | 10b 实测(v3, renderer cb2e186c) | 一致 |
|---|---|---|---|
| fence `:::` | 已翻转 False/False/False | False/False/False | ✓ |
| code_fence ``` | 同前 | False/False/False | ✓ |
| bold ** / ~~ | 同前 | True/False/True | ✓ |
| fn_def [^N]: | 同前 | True/False/True | ✓ |
| fn_ref [^N] | 同前 | True/False/True | ✓ |
| h3 ### | 不支持 | False/True/True | ✓ |
| inline_code ` | 同前 | True/False/True | ✓ |
| olist 1. | 同前 | True/False/True | ✓ |
| quote > | 同前 | True/False/True | ✓ |
| strike ~~ | 同前 | True/False/True | ✓ |
| table \| | 同前 | True/False/True | ✓ |
| ulist - | 同前 | True/False/True | ✓ |
| ulist_star * | 同前 | True/False/True | ✓ |

### 0e② vs 10c: 现 RUN 语法门禁

| 项 | 0e②(交接记录) | 10c 实测 | 一致 |
|---|---|---|---|
| exit_code | 0 | 0 | ✓ |
| OBS102_SYNTAX_GATE | PASS | PASS | ✓ |
| problems | [] | [] | ✓ |

### 0e③ vs 复算: writing_contract(现 RUN 冻结文章)

| 判据 | 0e③(交接记录) | 复算 | 一致 |
|---|---|---|---|
| ok | True | True | ✓ |
| deny_ask covered | 16/16 | 16/16 | ✓ |
| deny_prefix(⛔) | true | true | ✓ |
| ask_prefix(⚠️) | true | true | ✓ |
| numbers 登记 | 3 组 | 3 组(19→25 自检清单 / 8→11 红线数量 / 四→五 协作铁律) | ✓ |

---

## ② 2c′ 原始表 + 2d′ 分类取证表

### 2c′ 九类布尔全表(改前,先测不改)

| 组件 | 2c′ 可见 | 2d′ 分类 | grep 原始证据(复现,同安装侧渲染器) |
|---|---|---|---|
| alert | True | — | — |
| footnotes | True | — | — |
| dialogue | True | — | — |
| quote | False | 类A: 哨兵在 final.html,锚没认出 | `SENTINEL_A1` 命中 1 处:`<span leaf="">SENTINEL_A1</span></p></section>` |
| media-text | False | 类A | 命中 1 处:`<span leaf="">![图](...)\nSENTINEL_A1</span></p>` |
| gallery | False | 类A | 命中 1 处:`<p style="margin:0 0 16px;font-size:12px;..."><span leaf="">SENTINEL_A1</span></p>` |
| resources | False | 类A | 命中 1 处:`<span leaf="">SENTINEL_A1</span></p><p style="margin:2px 0 0;...` |
| code-compare | False | 类B: 哨兵未进 final.html | grep 零命中(`@before` 后只取同一行) |
| long-image | False | 类B: 哨兵未进 final.html | grep 零命中(`image=`/`caption=` 参数不被读取) |

类B 共 2 项 ≤ 3 → S13 未触发。

### 2e′ 补锚后可见集合(7 类)

alert / quote / media-text / gallery / resources / footnotes / dialogue。
锚点逐类抄录自 generate_advanced_html.py 真实 builder 产物(R11),见
`wxgzh_pipeline/stages/gzh_design.py` `_COMPONENT_PARA_RES`(逐类注释来源函数与主题参数)。
code-compare / long-image 归 QUARANTINED(渲染器缺陷 OBS-124/125),不补锚(R15)。

---

## ③ 2.5 的 16 行原始形态片段与三项断言结果

```
① 16/16 哨兵在 _body_plain_text ✓    ② L01→L16 顺序严格递增 ✓
③ 换行载体: <br 总数=4(封面等处) / </p><p 字面=0 → 相邻行无换行载体 ✗ → S12 停机
```

16 行实际形态(复现,安装侧渲染器):

```html
<p style="margin:0;font-size:14px;color:#555555;line-height:1.8;"><span leaf="">SENTINEL_L01 这是第 1 条护栏文案（全角括号）
SENTINEL_L02 这是第 2 条护栏文案（全角括号）
...
SENTINEL_L16 这是第 16 条护栏文案（全角括号）</span></p>
```

根因(审核方已坐实): `generate_advanced_html.alert()` 正文槽为单个 `<p>{s(body)}</p>`,
builder 层零换行处理 → 收尾裁决走 C 路线(2.6 组件×模式隔离),原 6e②「16 行进 :::alert
必须 ok=True」判据作废。

---

## ④ 2.6d 四项实测 + 2.6e 三条恒等断言结果

### 2.6d(组件×模式)

| 项 | 输入 | multiline_gate 结果 | 判定 |
|---|---|---|---|
| ① alert 单段(1 行) | `:::alert` + S1 | [] | 允许,S14 未触发 |
| ② quote 单段(1 行) | `:::quote` + S1 | [] | 允许,S14 未触发 |
| ③ alert 多段(3 行) | `:::alert` + S1..S3 | [alert@L5-L9, line_count=3] | 门禁 FAIL,reason 命中 |
| ④ quote 多段(3 行) | `:::quote` + S1..S3 | [quote@L5-L9, line_count=3] | 门禁 FAIL,reason 命中 |

### 2.6e 三条恒等断言(test_obs119_visibility.py,全量 pytest 通过)

- ① `APPROVED_CARRIER_COMPONENTS == component_body_visibility_check 现场实测集合`
  —— 实测可见(7) − MULTILINE(alert/quote) = {media-text, gallery, resources,
  footnotes, dialogue},测试现场计算,非手填。
- ② `APPROVED ∪ QUARANTINED ∪ MULTILINE == 安装侧 _COMPONENT_BUILDERS 键集合`(9 类),
  且两两交集为空(测试注释写明「组件×模式」口径)。
- ③ QUARANTINED 与 MULTILINE 各项在源码注释中带 OBS 号(OBS-124/125/129/132,正则校验)。

---

## ⑤ 2.7a 9×3 能力矩阵全表 + 2.7d 结论

实测口径: 环境曾只读受限,矩阵以「内存调用安装侧渲染器同一代码路径」完成
(parse_article → render,`-B` 零写盘;与 CLI 仅差文件往返,写权限恢复后已用
CLI 重渲染 fixture 验证逐字节一致——见 10a)。位2 换行载体判据: `<br` / `</p><p` /
独立 `<section>`;footnotes 的段落边界为 `</p>\n<p`(字面 `</p><p`=0、`</p>\n<p`=2),
按归一化 `</p>\s*<p` 判定为成立,原始计数并列贴出。

| 组件 | 位1 单段可见 | 位2 多行保结构 | 位3 每项独立元素 |
|---|---|---|---|
| alert | ✅ | ❌ 塌成单 `<p>`(<br=0,</p><p=0) | N/A 单 body 槽 |
| quote | ✅ | ❌ 同上 | N/A |
| code-compare | ❌ 哨兵未进 final.html | ❌ | N/A |
| media-text | ✅ | ❌ 三行+`![图]` 原文同处一个 `<p>` | N/A |
| gallery | ✅ | ✅ 逐图独立 `<section>` | ✅ Δp=+4, Δsection=+7 |
| long-image | ❌ 哨兵未进 final.html | ❌ | N/A |
| resources | ✅ | ✅ 字面 `</p><p`=3 | ✅ Δp=+7 |
| footnotes | ✅ | ✅(`</p>\n<p`×2,归一化) | ✅ Δp=+3,三条定义各成独立 `<p>` |
| dialogue | ✅ | ✅ 逐轮独立 `<section>` | ✅ Δp=+4, Δsection=+7 |

### 2.7d 结论

结构位能承载 N 项并保持独立元素: gallery / resources / footnotes / dialogue 四类;
但语义分别是图集、链接、脚注、问答,无一类适配「N 条并列警告短句」(16 条 deny/ask)。
→ **A 组不存在语义正确的并列短句载体 → 登记 OBS-131(能力缺口,71D 阻塞项,本档只登记不解决)**。

★矩阵新发现(待裁决): media-text 多行块体同样塌陷(位2=False),但不在
`MULTILINE_UNSUPPORTED_COMPONENTS` 名单内 → 2.6c 门禁对 media-text 多行不拦截,
属 R16 假绿漏网。建议登记 OBS-133(或并入 71C-R),是否纳入名单由审核方裁决,本档不改。

---

## ⑥ 2i′ 负对照四项

封面副标题 / 目录项(PART 01)/ 固定署名 / 页脚 CTA 四段文本均不得被
`_body_plain_text` 取到 —— test_obs119_visibility.py::test_obs119i_negative_cover_toc_signature_footer
通过(四个探针词全部不出现)。

---

## ⑦ 10a 四份 sha

- 现 RUN fixture: final.html `AE8DB428782A7FE511D9F5E1D69ED7EAA8F0FCB7D4D2E23B6A821F541275D139`(31587 B)
- 现 RUN fixture: final_runtime.html `21437B6651D5561475C10897BE7A1E9CC6393FE19F23A56508AF4B5E8AE3A2F1`(31887 B)
- CLI 重渲染(同文章+同 bindings 到临时目录): 两者逐字节一致,validator_errors=0
  → S10 未触发,渲染路径未受本档 pipeline 改动影响。

---

## ⑧ 12b 算式与实测

- 算式: 预期 = 626(基线) + 本档新增文件数(5: 2 validator + 2 test + 1 报告)
  − 本档新增 audit/quality/*.md 数(1) = **626 + 4 = 630**
- 实测(push 前): repo_file_count=630, installed_file_count=630, MATCH, diff/missing/extra 全 0
- 手算与实测相等 ✓

---

## ⑨ OBS 清单(文件 + 行号 + 文档原句 + 实现原句 + 后果)

| OBS | 文件/行号 | 文档原句 | 实现原句 | 后果一句话 |
|---|---|---|---|---|
| OBS-124(高) | gzh-design scripts/render_article.py(code-compare 分支) | `@before lang="python"\n旧代码\n@end`(advanced-components.md L17) | `before = l[len("@before"):].strip()` 只取同一行 | 续行代码丢失且 `lang="..."` 串入正文 |
| OBS-125(高) | 同上(long-image 分支) | `image="url" caption="说明"`(L20) | `url = args.get("url") or ""`;`cap` 默认值 | `image=`/`caption=` 双不匹配,图与说明双丢 |
| OBS-126(高) | 同上(media-text 分支) | `![说明](url)\n解释段落`(L18) | `exp = body.strip()` 原样入槽 | 块体 `![](url)` 从不解析,markdown 原文串入解释段 |
| OBS-127(中) | 同上(alert/quote 分支) | `type="warning"`/`type="highlight"`(L15-16) | `typ=`/`qt=` | 用户指定类型被静默忽略,直接影响 71D 的 ⛔/⚠️ 区分 |
| OBS-128(中) | 同上(footnotes 分支) | 正文散落 `[^N]` | 只认 `:::footnotes` 块体 `[^N]:` | 文档语法与实现不兼容 |
| OBS-129(高) | generate_advanced_html.alert() | — | 正文槽单 `<p>{s(body)}</p>` 零换行处理 | 多行块体塌成单 `<p>`,微信端失行分隔 |
| OBS-130(高) | pipeline 可见性判据(本档已修) | — | 只查文本存在不查结构 | 假绿闸门缺口;本档改为文本位+结构位双判据 |
| OBS-131 | A 组能力缺口(本档登记) | — | — | 无组件可语义承载 N 条并列短句,71D 阻塞项 |
| OBS-132(高) | quote 同单槽结构(本档登记) | — | blockquote 单 `<p>` | 多行塌陷(2.6d 实测确认) |
| OBS-133(候选,待裁决) | media-text 多行塌陷(本档矩阵实测) | — | 单 `<p>` 含字面 `\n` | 不在 MULTILINE_UNSUPPORTED 名单,门禁漏网 |

---

## ⑩ 本档没证明什么

- writing_contract 未改(第 6/7/8 步整体移交 71C-2B,本档零改动,S15 通过)
- 渲染器六处未修(OBS-124~129,移交 71C-R)
- 隔离组件与多行门禁在微信端未验证(需人工预览)
- B 组 10 类(facts/decision/steps/compare/annotated-image/faq/timeline/checklist/case/cta)未接线
- fake_live / offline 两条路径仍不过语法门禁(R9 保留项)
- gzh-design 版本号仍 hammer.7

---

## 第 1 步 OBS-120(_intro_paras 同步 + 未知组件 FAIL_CLOSED)

- 改前: `_intro_paras` 无组件块排除逻辑 → 首个 ## 前的 :::alert 块体会进导语清单
  → INTRO_GUARD 必然 FAIL_CLOSED(1b 炸点)。
- 改后: 从 `:::` 开标签行到配对 `:::` 收尾行整块排除(与安装侧 parse_article
  L107-128 in_component 状态机逐字对齐);`fa` 提前定义复用;挂载 quarantine_gate
  (2h′)、multiline_gate(2.6c)、usage 报告 unknown_count≠0 → COMPONENT_UNKNOWN=FAIL
  (R12: 文件不存在行为不变)。
- 1e 三条 pytest: ① 导语 :::alert → PASS ② 正常文字缺失 → 仍 FAIL ③ unknown_count=1
  → FAIL_CLOSED 且 reason 命中 —— 全过。

## 第 2 步 组件可见性(已在上文 ②/④/⑥ 呈现)

- 错误注释「A 组 9 类共用的形态」已改写为逐类各自形态(R13),见
  `wxgzh_pipeline/stages/gzh_design.py` `_COMPONENT_PARA_RES` 注释。

## 第 3 步 OBS-121(validators/validate_img_src_whitelist.py)

- 3b 改前: `if not https: reason="not https://"` + `elif bad-prefix` → bad prefix 永不可达。
  改后: `if https: continue` → `bad prefix(../ file:// data: 盘符)` / `not https://` 两分支都可达。
- 3c 正则: 双引号/单引号/无引号三种 src 写法(大小写不敏感)。
- 3d 自洽: `parsed_count != html.count("<img")` → exit 1, reason=IMG_SRC_PARSE_GAP,
  打印两数字与前 3 个未解析片段。
- 3e 三条 + gap 一条(test_obs121_img_src.py 4 项全过)。
- 3f 现 RUN 复测: hits=0, img_src_total=3(不变,S6 未触发)。

## 第 4 步 OBS-123(validators/validate_theme_identity.py)

- 4a 改前: `window = html[i:i+len(token)+400]`;改后: `rfind("<section")` → 深度配对
  `</section>` → `<img` 须在该区间内;400 常量删除。
- 4b 正对照: 现 RUN img_types 新旧一致 = ['image_2a_standard','image_media_text_card'](S7 未触发)。
- 4c 负对照: alert-hammer.html(660 B,官方样例)新旧口径均 []。
- 4d 两向 pytest: `<img` 在配对 section 内 → 命中;<img 在 section 闭合后 380 字符处
  → 不命中,且测试先断言旧 400 窗口会误命中(证明魔数确实死了)。

## 第 5 步 打包校验残留

- 5a: `_enforce_expected_counts` 失败信息补打 skip_names 全清单。
- 5b: 新增 `_disk_enum_set()`,与 zip 条目集合双向差集,only_in_disk/only_in_zip
  任一非空 → SystemExit(替代旧 count 比对)。
- 5c: test_obs102_baseline_no_needle_hit 去掉双重归一化(与 OBS-118 同源)。
- 5d: bundle 重建 exit 0(pipeline=668 manifest=1236 bundle_zip=1238,
  manifest_verified=true,集合比对通过,S8 未触发)。

## commit A

- sha: `34ca3e7`;files: 10;stats: +648/−50;push: 5374b5c..34ca3e7(dev/0.1.0-dev2)

## 第 6/7/8 步 — 本档未执行,整体移交 71C-2B

`wxgzh_pipeline/writing_contract.py` 与 `contracts/05_gzh_design.yaml` 零改动(S15 通过)。

## 第 9 步 写作层载体规格取证(只读)

- 9a 穷举来源: writing_contract.py 全文 / stages/super_writer.py / contracts/02_super_writer.yaml
  全文 / super-writer 技能 77 文件全量检索。
- 9b 「必须用代码围栏」仅三处,全在 pipeline 侧:
  - writing_contract.py L16-17: 「至少 10 条必须以 fenced code block 逐字进入文章,
    且代码块内必须出现 ⛔ 与 ⚠️ 模板前缀;改写/散文化不计数」
  - writing_contract.py L38: `MIN_DENY_ASK_COVERAGE = 10`
  - stages/super_writer.py L46-48: 挂载点,仅 items_file 注入路径启用
  - super-writer 技能侧(formatter-capability-map.md L112/L118/L481、semantic-components.md
    L456-464、length-policy.md L11、drafting.md L53)均为组件能力定义,无强制围栏要求;
    contracts/02 无形态要求。
- 9c: 若 71D 要求写作层改出组件形态,需动 super-writer 形态指示(被锁)→
  **登记,须并入 71C-R 或另起 relock 档**,本档不动手。

## 第 10 步 双向验收(见 ①/⑦)

10d: 针体自检 13/13、负对照 26/26(13 token + 13 needle)、组件正文可见性 9/9
(union 恒等断言覆盖全部 9 个 builder 键)。

## 第 11 步 测试

- 11a 逐文件: test_intro_guard.py 新增 7(3 obs120 + 2 quarantine + 2 multiline)/
  test_obs119_visibility.py 新增 4 / test_obs121_img_src.py 新增 4 /
  test_obs123_img_fingerprint.py 新增 3 / test_obs102_syntax_gate.py 1 处改(5c)。
- 11b 全量: **370 passed / 0 failed / 0 error / 1 skipped / 1 deselected**
  (372 collected;skip = test_reinstall_from_pr_trees_doctor_pass,环境性
  WXGZH_SUBSKILL_CLONES 未设;deselect = test_hotfix1.py::test_portable_installer_preserves_pipeline_release_include,既有允许项)。
- 11c upgrade_regression: **ALL PASS**(pytest PASS 1 deselect、relock dry-run x4 无变化、
  doctor PASS、cross-side 仍 SKIP)。
- 11d: gzh-design 仓零改动。

## 第 12 步 同步与提交

- 12a: bundle 重建 exit 0 → 便携安装器 exit 0(四锁 hash_verification 全 true,
  receipt 已写)→ post-doctor PASS。
- 12b: 见 ⑧。
- 12c 四个数字: push 前 OBS_68 630/630 MATCH + OBS_69 MATCH;push 后 OBS_68 630/630
  MATCH(diff/missing/extra 全 0)+ OBS_69 MATCH。
- 12d commit B: 未执行(第 6/7/8 步随主移交 71C-2B)。
- push: 仅 commit A(34ca3e7),代理用 `git -c` 内联,零配置残留。

## 零改动声明与遗留阻塞项

- 未修改任何 RUN 目录产物(探针/复算全部写入 .temp\71c2-step10 与
  .temp\obs123-check 等临时目录);唯一安装侧触碰: 官方样例生成器
  generate_advanced_html.py 重写安装侧 tests/advanced-components/expected,
  与仓内 182/182 逐字节一致,零漂移(如实声明,R5 边界)。
- 未调用微信任何接口;未新建/续跑 RUN;未 merge/force-push/amend/rebase;
  未写 gzh-design 源树;lock 双侧 E2201B11… 未变;台账未动。
- 遗留: OBS-92/93/94(前档登记,未变)/ OBS-131(71D 阻塞)/ OBS-133 候选(media-text
  门禁漏网,待裁决)/ 第 6/7/8 步移交 71C-2B / 渲染器 OBS-124~129 移交 71C-R /
  微信端人工预览待执行。
