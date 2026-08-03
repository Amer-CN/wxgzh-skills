# 档 47 — 先核查 intro 首段完整性:停机于第一步(OBS-83 登记,OBS-72 未动)

- 报告编号:e2e-verify-47
- 执行日期:2026-08-03(Asia/Shanghai)
- 状态:**停机**。按档 47 指令「★此时停机报我,不要自行修复,不要继续第二步」执行:第一步核查确认 **intro 第一段全文未进入正文区域**,OBS-73 判定为未完全结案,登记 **OBS-83(高)**;未执行第二步(OBS-72 修复)及后续步骤;未修改任何代码/产物/合同;未调微信接口;未发起草稿。
- RUN_ID:`20260802T220853-codex-sol-luna-max-m6pyv4`

## 第一步 核查结果(逐字对照)

### 1. final_article.md 中 intro 第一段原文

```
导语：多模型编排正在成为 AI 编程成本的关键杠杆，这次的样本来自 Codex 自己。
```
(43 字符)

### final.html 中与之对应的全部文本(反提取纯文本,逐字)

第一段 43 字**整体**出现在 HTML 中,但位置是**封面组件**(`hammer_cover` 的 subtitle 槽位,`subtitle = parsed["intro"][:48]`,43 ≤ 48 恰好全含);oneliner 卡片仅含前 40 字(`parsed["intro"][:40]`)。**正文区域(章节段落)没有第一段**。

- prefix40 在 HTML 中:True(来自 oneliner)
- 首段 40-43 字(「，这次的样本来自 Codex 自己。」尾部):True(来自封面 subtitle,非正文)
- 第二段全文:True(来自正文 intro_paras 渲染)

### 2. parse_article 决定行为代码(render_article.py,已安装 9596ecc)

```python
        if cur is None:
            if not intro:
                intro = st          # ← 第一行只进 intro,不进 intro_paras
            else:
                intro_paras.append({"kind": "para", "text": st})
            continue
```
渲染出口:
```python
L152  subtitle = (parsed.get("intro") or "结构化拆解与要点梳理")[:48]
L161  parts.append(H.hammer_oneliner(theme_key, parsed["intro"][:40]))
L166  for item in parsed.get("intro_paras") or []:   # 仅 intro_paras 渲染进正文
```
**结论:第一段不进 intro_paras;其唯一渲染出口 = 封面 subtitle[:48] 与 oneliner[:40]。**

### 3. _intro_content_fidelity 首行规则语义(档 45R 守卫)

```python
        if idx == 0:
            prefix = norm[:_INTRO_MAX_LEN]      # 只取前 40 字
            if prefix not in plain:
                missing.append(para)
        else:
            if norm not in plain:               # 其余行要求完整
                missing.append(para)
```
**语义:首行只校验「前 40 字前缀存在」——这是在容忍首段被截断,不是验证首段完整。**

### 4. 结论

- 本 RUN 第一段(43 字)在 HTML 中「完整出现」属于**巧合**:43 ≤ 48,封面子标题恰好覆盖全文。若首段 > 48 字,封面与 oneliner 均截断,正文无全文——设计上第一段**从不进入正文**。
- **OBS-73 判定为未完全结案**,登记 **OBS-83(高)**:intro 首段仅以截断 oneliner(前 40 字)/封面子标题(前 48 字)形式呈现,正文缺失首段全文。
- **守卫为何没发现(假绿谱系第五例)**:`_intro_content_fidelity` 对首行只断言「前 40 字前缀存在」,语义是容忍截断;首段被截断(或仅以封面/oneliner 形式出现)时守卫依旧 PASS。档 50 的「intro 两段 OK」正是这一假绿:第二段全文进入正文(守卫有效),第一段依赖 48 字截断巧合(守卫失察)。

## 停机范围

- 未执行:第二步 OBS-72 修复、第三步续跑、第四步复核(upgrade_regression/doctor/同步/总账更新)。
- 未修改:producers.py、任何被锁 skill、lock、台账、RUN 产物、批准合同。
- 无新微信副作用(档 50 后状态不变:本 RUN 累计 6 次 uploadimg,草稿箱 3 份)。

## 需要裁决

1. OBS-83 修复方案(待授权):render_article.py 把 intro 第一段并入 intro_paras(正文渲染全文,封面/oneliner 行为不变),或渲染层新增「正文首段」出口;同时守卫首行规则从 prefix40 改为「全文或明确豁免(封面即全文时)」判定——两者需联动,且触碰被锁 gzh-design(按 OBS-59/60/62/77 流程走升版/重锁)。
2. OBS-72 修复(原档 47 第二步)在 OBS-83 裁决后另行执行;本 RUN 续跑至草稿需两者都落地。

## 证据

- 本 RUN `gzh_design/final.html`、`zh_human_writing/final_article.md`(`.temp\wxgzh-pipeline\20260802T220853-codex-sol-luna-max-m6pyv4\`)
- 代码:`.agents\skills\gzh-design\scripts\render_article.py`(L99-101、L152、L161、L166)、`wxgzh_pipeline\stages\gzh_design.py`(`_intro_content_fidelity` 首行分支)
