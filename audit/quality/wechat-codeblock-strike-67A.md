# 档 67A v2 — gzh-design 视觉三修(OBS-90 代码块微信友好 + 删除线对比度 + OBS-77)

- 性质:**动被锁 gzh-design**(预期第八次 relock);阶段一已完成,阶段二(relock)待网络窗口。
- RUN 处置:本档不 continue 媒体阶段、不批准资产;档 67 第二段视觉分级**未启用**(前提待本档重新给出)。
- 网络状态:0d 实测 github.com:443 **可达**(阶段二可执行)。

## 第零步 前置核验

- 0a:另一条发文线 RUN `20260804T185111-ai-inomr0` 最后写入 18:53:33(wechat_draft
  receipt + final_delivery),此后无新写入 → **已停止全部流水线操作**;其产物与草稿
  本档零触碰。安装侧 `.install-receipts` 最近写入 20:27 为档 67 本会话安装器所为
  (非另一线)。
- 0b 安装侧基线(收工复核):lock `81F9342A…`;super-writer `46a00a1b` /
  zh-human-writing `18491b36` / media-enrichment `181752eb`(dev9) /
  gzh-design `c3dd056e`(hammer.4,76 文件)。收工后确认未被本档改动(relock 前)。
- 0c:开工后未发现安装侧非本档改动(仅行尾 CRLF/LF 差异属既有,内容一致)。
- 0d:github.com:443 **可达**(Test-NetConnection TcpTestSucceeded=True)。

## 第一步 OBS-90 代码块微信友好结构

1. `_hammer_code_block`(render_article.py)重写:每行一个 `<p style="margin:0">`
   (与 generate_advanced_html.py `code_compare()` 同构),容器 `<section>` 带
   背景 `#F5F3F0`、边框、圆角、`overflow-x:auto`;**不再输出 `<pre>` 与
   `white-space:pre`**(自家 lint 判 ERROR 的特征,档67A 消除内部矛盾)。
2. 保留:内容为真实可选中文本(`<span leaf="">` 包裹,最小 HTML 转义 + 空格转
   `&nbsp;`),不截图、不伪装元素;⛔/⚠️ 前缀与行内缩进以 `&nbsp;` 对齐
   (实测:unescape 后逐字一致,含 4 空格缩进行)。
3. `validate_gzh_html.py` CODE_STYLE 修正:代码区识别**不再依赖 white-space:pre**,
   改为等宽字体(`font-family` 含 monospace/Consolas/'SF Mono'/courier)。
   不误判普通段落的依据:renderer 只对代码块使用等宽字体,普通段落无
   font-family 或使用系统默认字体栈,不含等宽关键字(测试覆盖正反例)。
4. 新 lint 用例 `tests/test_obs90_wechat_codeblock.py`(11 项):渲染输出无
   `<pre>`/`white-space:pre`、每行 `<p style="margin:0">`、缩进保留、**渲染输出
   通过 lint CHECKS 规则集**(自家 lint 禁止的东西自家渲染器不许输出)、
   过 validate_gzh_html(0 ERROR,代码区半角不误报)。
5. 最终产物验证:渲染测试页生成于 `.temp/obs67a-preview/final.html`
   (hammer 主题,3 行 ⛔/⚠️ 代码块 + 2 行命令块 + 封面 strike)。
   ★微信编辑器人工预览:本会话无微信公众平台访问能力(无登录态/无浏览器控制
   工具),**未能真实完成微信端粘贴预览**——如实报告,不伪造。测试页与粘贴指引
   已就绪,微信端确认需用户或后续有登录态环境执行(见第四步结论)。

## 第二步 删除线对比度

6. 举证:封面 strike 实现于 `hammer_cover()`(generate_hammer_upgrade_samples.py):
   ```
   <p style="font-size:15px;color:{t['divider']};margin:0 0 6px;
        text-decoration:line-through;text-decoration-color:{p};
        text-decoration-thickness:1.5px;letter-spacing:0.5px;">
   ```
   调用点 render_article.py:`hammer_cover(theme_key, kicker=…, strike="别急着划走", …)`。
   - 橙色粗线来源:`text-decoration-color:{p}`(p=primary `#B3593B`)+
     `text-decoration-thickness:1.5px`;
   - 文字对比度不足来源:`color:{t['divider']}` =
     `rgba(202,202,199,0.35)`(白底有效对比度 ≈1.2:1)。
   ★档 23-min 结案「非缺陷」判定被本档推翻:实测色值与 WCAG 标准不符。
7. 修复两项:
   a. 文字色 → `label_text` `#737373`:白底对比度 **4.74:1**(计算:
      L(#737373)=0.1714 → (1.05)/(0.2214)=4.74)≥ 4.5:1 ✓;
   b. 删除线 → `text-decoration-color:{t['label_text']}`(同文字色)+
      `text-decoration-thickness:1px`(细线、不盖字形,不再是橙色粗线)。
8. 测试覆盖:对比度比值断言(≥4.5)、渲染输出含新样式、不含 `#B3593B` 删除线。
   ★微信端人工预览同第一步:本会话无法完成,如实报告。

## 第三步 OBS-77

9. 三项 fixed_signature 预存失败定位(200 passed / 3 failed / 21 skipped):
   - `test_01`(7 主题含固定结尾引用):`theme-zen-whitespace.md` 缺引用;
   - `test_07`(禁「我是 {{作者名}}」):6 个主题文档含该占位符(示例 HTML 或说明文字);
   - `test_08`(禁「{{一句话简介，如…}}」):red-white / graphite-minimal /
     zen-whitespace 3 个主题示例 HTML 含该占位符。
10. 修复:6 个主题文档占位符改为无花括号说明(「作者名与一句话简介,按实际填写,
    未知则整行删掉」);zen-whitespace 补固定结尾引用(指向 common-components.md)。
    修后全量:**214 passed / 21 skipped(0 failed)**——三项恢复,未改断言迁就实现
    (仅对 OBS-90 旧结构断言做语义等价更新:<pre> 断言改为「无 pre + 文本可复制」、
    空格断言改为 unescape+\xa0 归一化,行为语义不变)。

## 第四步 代码块视觉权重重新举证

11. 结构证据(可客观给出,不依赖微信端):
    - 新代码块为全宽容器 `<section>`(与 hammer 图片卡同为全宽、带背景/边框/
      圆角/内边距),每行 `<p style="margin:0">` 独立占位;
    - 10 行代码块在 375px 宽下的估算占位高度:14px 内边距 ×2 + 13px×1.7 行高 ×10
      ≈ 28 + 221 = 249px,与 16:9 图(约 211px)同量级(高比 ≈1.18);
    - 文字与背景均真实存在(非透明/非伪装),可选中可复制。
12. 结论(★依据必须是微信端呈现,本档未完成微信端实测,故给出**条件结论**):
    - 结构性证据支持「代码块构成全宽视觉组件(背景/边框/占位高度)」,权重 1:1
      建议维持;
    - 但「微信端呈现」这一指令要求的实测本会话无法执行(无微信编辑器访问能力),
      **不伪造实测数据**;
    - 请用户在微信编辑器粘贴 `.temp/obs67a-preview/final.html` 确认:
      ①背景/边框是否保留;②换行与缩进是否正常;③文本是否可复制。
      若微信端实测与结构证据不符,档 67 分级方案作废,由用户另行裁决。

## 第五步 阶段二(relock,需网络)

13. 已升版:RELEASE_NOTES 首行 → `v2026.08.02-hammer.5`(OBS-90/删除线/OBS-77
    说明);WXGZH_PIPELINE_INTEGRATION.md Locked version 同步。
    阶段二:push 到 `fix/obs73-codeblock-docs` → 第八次真实 relock --apply
    (远端见证 → 计算 → 仓库外备份 → lock+台账 → 安装器 → post-doctor →
    入口冒烟)→ OBS-69 基线同步 → Pipeline 侧 commit+push。
    ★本报告撰写时网络已恢复(0d),阶段二按【网络受限执行顺序】执行;
    若执行中网络再次中断,停在此处等待,不改安装侧。
14-17. 阶段二复核项(lock 新值/台账 8 条/root/version 变化/四锁 hash_ok/doctor/
    安装侧一致/OBS-69 同步/upgrade_regression ALL PASS/cross-side SKIP/
    零副作用/0b 基线未被第三方改动)将在阶段二完成后逐项贴出。

## 阶段二执行结果(网络恢复后完成)

- 远端见证三检 **PASS(a/b/c)**(c0e69f6 已在远端;含 3 个历史遗留展示产物
  一并纳入版本管理以满足树一致性——非档67A 逻辑改动)。
- **第八次真实 relock --apply 全链**:计算(root `c3dd056e→b667298f`、manifest
  `ced84143→7724e3ba`、count 76→77、entrypoint/render_entry/component_source
  全变)→ 仓库外备份 → lock+台账(**第 8 条** `relock-gzh-design-20260804T130644Z-1657b49a`)→
  安装器 PASS → post-doctor PASS → **入口冒烟 PASS**(CLI subprocess,生产路径)。
- 回归首轮仅 OBS-69 基线 3 项失败 → 既定配套同步 `REPO_LOCK_SHA256`
  (81F9342A → **1B15939B…**)→ **upgrade_regression ALL PASS**(排除清单仍 1 项,
  cross-side 仍 SKIP;四锁 dry-run 全部无变化)。
- 复核:lock 双侧 `1B15939B8875BD868B789C78DCB73C20D70E8405D948F33E23D0EB3BA8621D66`;
  台账 8 条;四锁 hash_ok 全 true;doctor PASS;安装侧与 repo HEAD 逐字一致
  (经正式安装器同步,含 Pipeline 侧 observability 基线)。
- 副作用:零 uploadimg、零 add_material、零草稿、零发布(本档全程零微信调用,
  渲染测试页为本地文件)。
- 0b 基线复核:安装侧 gzh-design 已按本档 relock 更新为 hammer.5(预期变更);
  其余三锁与 lock 双侧均未被第三方改动(与阶段一记录一致)。

## 变更文件

- gzh-design 源树(`fix/obs73-codeblock-docs`):render_article.py /
  validate_gzh_html.py / generate_hammer_upgrade_samples.py / RELEASE_NOTES.md /
  WXGZH_PIPELINE_INTEGRATION.md / 6 个主题文档 / 3 个测试文件 + 新测试
  test_obs90_wechat_codeblock.py
- 阶段二将更新:wxgzh-pipeline(lock/台账/observability 基线/报告)
