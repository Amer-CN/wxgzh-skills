# 档 67D — 回归 common-components 1a 深色代码块规范(第十次真实 relock)

- 性质:动被锁 gzh-design(回归,非新设计;规格早已存在于 references/,实现走偏)。
- 0a:另一条发文线(RUN `20260804T185111-ai-inomr0`)最后写入 18:53:33,本档全程
  无新写入;0b 安装侧基线(relock 前):lock `B30A2056…`、gzh root `30d7cdb3` hammer.6。
- 网络:github.com:443 可达;push 与 relock 完成。

## 第一步 恢复「不手写 HTML」契约

1. 官方组件源 `generate_hammer_upgrade_samples.py` 新增
   `hammer_code_block(language, text)`:按 `common-components.md`「1a. 深色代码块」
   **逐字实现**(深色版各主题共用,不做主题变色):
   - 外层 `background:#1E293B` + `border-radius:8px` + `overflow:hidden` +
     `box-shadow:0 4px 16px -8px rgba(15,23,42,0.4)`;
   - 顶栏 `background:#0F172A` + `display:flex`,三色圆点
     `#FF5F56/#FFBD2E/#27C93F`(10px 圆,`font-size:0` 隐藏占位字符);
   - 语言标签 `color:#64748B`、`Consolas` 等宽、`letter-spacing:1px`
     (无语言则删该 span,保留顶栏与圆点);
   - 代码行每行一个 `<p style="margin:0;font-family:'SF Mono',…;color:#E2E8F0;">`。
2. `render_article.py` 的 `_hammer_code_block` 改为**纯委托**
   `H.hammer_code_block(language, text)`;parse_article 捕获围栏语言标记
   (` ```bash → bash`、` ```text → text`),代码 item 携带 `language`。
   **本文件不再有任何自拼 hammer HTML 字符串**——文件头
   「hand-writes NO hammer HTML of its own」恢复为真。

## 第二步 缩进与可复制性(规范③⑤)

- 缩进改用**全角空格 U+3000**(规范③,不再用 &nbsp;/普通源码空格);
- 行内空格**一字不动**(规范⑤);
- `test_obs91_copyability.py` 更新并加严:无前导空白行(两条 /plugin)**零 U+00A0
  且零 U+3000**;16 条 deny/ask 逐字可还原(缩进位归一化后比对);行首缩进断言改
  U+3000×4;★反向验证保留——旧全 &nbsp; 实现必须仍判 FAIL(实测 FAIL)。

## 第三步 OBS-95 最小闸门 + 诚实答复

- 新增结构闸门测试(并入 test_obs90):渲染输出中每个代码块必须命中 1a 结构
  (深底 #1E293B / 顶栏 #0F172A / 三圆点色值 / 每行独立 `<p style="margin:0">`);
  并断言无 `white-space:pre` 与 `<pre>`。
- ★step 8 诚实答复:**无**。现有 `lint_advanced_components.py` / `component_lint.py`
  只扫描 references/ 文档源文件的反模式;**validate_gzh_html.py** 只做通用公众号
  规则(leaf 包裹/半角/禁用标签),两者都不具备「渲染器输出 vs references/ 组件
  清单」的交叉校验——OBS-90(`<pre>` 形态,validate 0 ERROR)与 OBS-91(docstring
  与实现不一致)的根因正是此缺口。**登记 OBS-95(高)**;本档不扩大改造(仅加最小
  结构闸门测试)。

## 第四步 验证

- gzh-design 全量 pytest:**220 passed / 21 skipped(0 failed)**;
  test_obs90(12 项)与 test_obs91(5 项)全过。
- `lint_advanced_components.py`:**18/18 干净,ERROR×0 WARN×0**。
- 渲染测试页过 `validate_gzh_html.py`:**0 ERROR**(1 WARN 为测试页正文自带的半角
  逗号,与代码块/语言标签无关)。
- CODE_STYLE 等宽识别:新结构代码行含 `'SF Mono'`、顶栏标签含 `Consolas` → 仍命中
  代码区;语言标签(bash/text)为英文,**不触发 CJK 半角告警**(实测 warnings 无相关项)。

## 第五步 测试页

- `F:\AIXM\wxgzh\.temp\obs67d-preview\final.html`
- `F:\AIXM\wxgzh\.temp\obs67d-preview\final_runtime.html`
- 包含:a. ` ```bash ` 4 空格缩进 deny/ask 块(缩进=U+3000×4);b. ` ```text `
  两行无缩进 `/plugin` 命令(零特殊空白);c. 封面 strike「别急着划走」
  (#737373 + 同色 1px)。
- ★微信人工预览由用户执行,本档未声称已做。

## 第六步 第十次真实 relock 与复核

- **gen_cover.py 处置(67C 待裁决项,裁决=移走)**:`git mv scripts/gen_cover.py
  tests/gen_cover.py`(内容未改);grep 证明无入口引用(仅 RELEASE_NOTES 文档提及,
  非代码引用)。runtime count 按预期 **77 → 76**。
- 远端见证三检 PASS → 计算(root `30d7cdb3→0dd8d317`、manifest `7724e3ba→ced84143`、
  count 77→76、entrypoint/render_entry `82fed151→5ae3be90`、
  component_source `d25beb37→74218a69`、full_commit `5dd5589→af03b43`、
  tree `c0785904→95afcd87`、version hammer.6→hammer.7)→ 仓库外备份
  `skills.lock.20260804T152138Z.json` → **台账第 10 条**
  `relock-gzh-design-20260804T152138Z-47328655` → 安装器 PASS → post-doctor PASS →
  **入口冒烟 PASS**。
- OBS-69 内嵌基线同步 `B30A2056 → 0CD0EBC3…` → **upgrade_regression ALL PASS**
  (排除清单仍 1 项;四锁 dry-run 无变化;doctor --require-wechat PASS;cross-side SKIP)。
- lock 双侧 `0CD0EBC35CF516BD0BD74DA515C74D50F929948F1D0E1FDD772D80D56C6B1CF9`;
  台账 10 条;四锁 hash_ok 全 true;doctor PASS;安装侧经正式安装器同步后与
  repo HEAD 逐字一致(OBS_68 MATCH)。
- 副作用:零 uploadimg、零 add_material、零草稿、零发布(零微信调用)。

## 登记四项观测(不修)

| OBS | 级别 | 描述 |
|---|---|---|
| OBS-92 | 低 | 行内制表符未逐字保真(`run` 分支把行内 tab 当单空格;前导 tab 也仅一格 U+3000)。本篇全为空格缩进故未触发。 |
| OBS-93 | 中 | relock `--source-tree` 无一致性约束:同一个 skill 的身份取决于操作者当时传哪个目录(前四次 43r-build,67A/67C/67D 用 gzh-design-skill)。 |
| OBS-94 | 高 | `body_images_min` 可被 RUN 目录 `validation_config.json` 覆盖,无审批闸门与强制留痕;档 18 曾实际降至 2(存档 RUN1,sha `38A6C67D…`)。 |
| OBS-95 | 高 | references/ 组件规范与 scripts/ 渲染实现之间无校验层,渲染器可输出规范里不存在的形态而全部校验器沉默(OBS-90/91 共同根因;本档已加最小结构闸门,未扩大改造)。 |

## 变更文件

- gzh-design(`fix/obs73-codeblock-docs`,commit `af03b43`):
  generate_hammer_upgrade_samples.py(hammer_code_block 1a)/
  render_article.py(纯委托+语言捕获)/ tests(obs90 结构闸门、obs91 加严、
  旧测试归一化 U+3000)/ gen_cover.py → tests/ / RELEASE_NOTES.md /
  WXGZH_PIPELINE_INTEGRATION.md
- wxgzh-pipeline(本档):observability.py(OBS-69 基线)/ skills.lock.json /
  skills.lock.history.json / lock-backups/skills.lock.20260804T152138Z.json / 本报告
