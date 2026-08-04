# 档 67C — OBS-91 可复制性修复 + 两处举证(第九次真实 relock)

- 性质:动被锁 gzh-design(第九次真实 relock --apply,完整原子链 + 入口冒烟)。
- 另一条发文线(RUN `20260804T185111-ai-inomr0`):最后写入 18:53:33(final_delivery),
  本档全程无新写入 → 0a/0b/0c 维持。
- 网络:github.com:443 可达;push 与 relock 全部完成。

## 第一步 OBS-91 可复制性修复(核心)

1. `_hammer_code_block`(render_article.py)改造:
   - **仅行首前导空白(空格/制表符)整段转 `&nbsp;`**(保留缩进对齐);
   - **行内空格保持普通空格**(复制出来是普通空格,可复制性优先);
   - 行内连续空白段:仅「第二个及之后」转 `&nbsp;`,首个保持普通空格
     (防 HTML 折叠,同时不伤可复制性);
   - **docstring 与实现逐字一致**(本次实现与注释不一致是 OBS-91 成因之一,
     已同步修正)。
2. 可复制性回归测试(`tests/test_obs91_copyability.py`,自动化不依赖人眼):
   渲染 final.html → 提取代码行(`<p style="margin:0;font-family:'SF Mono'…">`)→
   去标签 + `html.unescape` → 与源 final_article.md 代码块逐行比对:
   a. 每行内容逐字节相同(行首缩进允许 U+00A0,归一化后比对);
   b. 无前导空白的行(两条 /plugin 安装命令)**零 U+00A0**;
   c. ⛔/⚠️ 前缀与全部 **16 条 deny/ask 文案逐字可还原**。
3. ★反向验证:构造旧实现(全空格转 `&nbsp;`)的输出 → 新测试**必须 FAIL**
   (断言「无前导空白行含 U+00A0」),实测 FAIL,修复被证实有效。

## 第二步 举证:等宽豁免面

- 检索命令:
  ```
  Select-String -Path scripts\generate_advanced_html.py, scripts\render_article.py -Pattern "font-family" (等宽相关)
  全 skill 递归 grep monospace|Consolas|'SF Mono'|courier
  ```
- 运行时输出中**仅**代码块使用等宽字体:`render_article._hammer_code_block`(L312)
  与 `generate_advanced_html.code_compare`(L72/76/83/87,独立示例生成器)。
- **除代码块外命中新 CODE_STYLE 的组件(模板/参考层,非 render_article 输出)**:
  `references/common-components.md` L23/L40(代码块头部标签 span,属代码块区域)、
  L53(行内代码);`theme-graphite-minimal.md` L255、`theme-olive-journal.md`
  L296/L317(行内代码);`docs/gallery/olive-journal.html` L183(预览页)。
  → 这些不在 render_article 运行时输出路径,validate_gzh_html 不校验它们;
  **运行时 final.html 的豁免面 = 代码块**。若模板行内代码经复制进入 final.html,
  其半角标点会被静默豁免——判定:行内代码内含半角标点语义正常(如 `x=1,`),
  且 renderer 不产出该形态,风险可控、如实记录,不加白名单。

## 第三步 举证:count 76→77(gen_cover.py 溯源 + 见证答案)

- 来源:2026-07-19 22:22:24 起存在于 `F:\AIXM\wxgzh\gzh-design-skill`
  (CreationTime=LastWriteTime),**从未被 git commit**(untracked);功能=生成 hammer
  封面展示图,与 `tests/hammer-all-components-showcase.html` / `hammer-showcase-cover.jpg`
  配套(7/19 22:50)。**无任何入口引用**(grep 确认,仅自引用自身输出文件名)。
- ★见证答案:**选 (a)**——之前它不在用于 relock 的源树内:
  前四次 gzh-design relock(45R/45R2/51/54R)的 `--source-tree` 均为
  `F:\AIXM\wxgzh\repos\gzh-design-skill-43r-build`(54R 报告 L38 明载命令;
  45 报告 L44 `installed_dir` 同路径);该目录**实测不含** gen_cover.py 与两个
  showcase 文件(Test-Path=False)。本次(67A/67C)源树为
  `F:\AIXM\wxgzh\gzh-design-skill`(含这些遗留未跟踪文件)→ 67A 远端见证 (b)
  据此拦下,属源树差异,非见证漏洞。见证三检(a/b/c)实现本身无缺陷。
- 处置建议(本档不擅自移动,等裁决):保留在 `scripts/`(进 manifest,成为锁定
  树一部分,root 将含它——与 67A 起已纳入一致)或移入 `tests/`(runtime 排除,
  root 不再含)。两者皆可行;移入 tests/ 更符合「展示工具非运行资产」定位,
  但需下档执行并再次 relock。

## 第四步 删除线对比度重算

- strike 实际背景:`hammer_cover` 封面卡外层 `<section style="…background:#fff;…">`,
  strike `<p>` 无独立背景 → **落在白底 #FFFFFF**。
- `#737373` 白底对比度:**4.74:1**(L=0.1714 → (1.05)/(0.2214))≥ 4.5:1 ✓,
  无需重选色值;删除线同色 1px,不盖字形。

## 第五步 测试页(待人工微信预览)

- 渲染输出:`F:\AIXM\wxgzh\.temp\obs67c-preview\final.html`(hammer 主题)。
- 包含:a. 4 空格缩进的 deny/ask 代码块(行首 `&nbsp;`×4,行内普通空格);
  b. 无缩进两行 `/plugin` 安装命令(零 U+00A0,可复制);c. 封面 strike「别急着划走」
  (`#737373` + 同色 1px)。
- ★微信编辑器人工预览由用户执行;本档未声称已做微信端预览。

## 第六步 第九次真实 relock 与复核

- 远端见证三检 **PASS(a/b/c)**(commit `5dd5589` 已在远端)。
- 原子链:计算(root `b667298f→30d7cdb3`、manifest/count 不变 `7724e3ba/77`、
  entrypoint/render_entry `a2182459→82fed151`、full_commit `c0e69f6→5dd5589`、
  tree `0d0f7077→c0785904`、version hammer.5→hammer.6)→ 仓库外备份
  `skills.lock.20260804T140552Z.json` → **台账第 9 条**
  `relock-gzh-design-20260804T140552Z-16596eea` → 安装器 PASS → post-doctor PASS →
  **入口冒烟 PASS**。
- OBS-69 内嵌基线同步 `1B15939B → B30A2056…` → **upgrade_regression ALL PASS**
  (排除清单仍 1 项;四锁 dry-run 全部无变化;doctor --require-wechat PASS;
  cross-side 仍 SKIP)。
- lock 双侧 `B30A20564F3595FEE2827FDDF4697CB61A65309B33208030C1C2ED277CA24022`;
  台账 9 条;四锁 hash_ok 全 true;doctor PASS;安装侧经正式安装器同步后与
  repo HEAD 逐字一致(OBS_68 MATCH)。
- ★档 67A `ae59767` 已在档 67B push 时随批推送,远端可见
  (`merge-base --is-ancestor ae59767 origin/dev/0.1.0-dev2` → True);
  第八次 relock 采信条件满足。
- 副作用:零 uploadimg、零 add_material、零草稿、零发布(本档零微信调用)。

## 变更文件

- gzh-design 源树(`fix/obs73-codeblock-docs`,commit `5dd5589`):
  render_article.py / tests/test_obs91_copyability.py(新增)/
  tests/test_obs90_wechat_codeblock.py / RELEASE_NOTES.md / WXGZH_PIPELINE_INTEGRATION.md
- wxgzh-pipeline(本档):observability.py(OBS-69 基线)/
  skills.lock.json / skills.lock.history.json /
  audit/upgrade-capability/lock-backups/skills.lock.20260804T140552Z.json /
  本报告
