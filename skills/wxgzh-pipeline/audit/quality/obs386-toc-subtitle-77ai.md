# OBS-386 —— 77AI toc 卡片副标题透传验收报告（字节级落盘）

- 档号：77AI（toc 卡片副标题：章节首段首句透传）。
- 授权：RELOCK_ALLOWED 临时 0→1（批准人=用户，范围=gzh-design：render 管线透传+toc 签名；pipeline 无锁条目不涉锁；GZH_DESIGN_WRITE_ALLOWED 维持 0——数据透传，主题设计值零触碰）。授权登记行随 feat 落账（序数按台账实况=五十六次，77AH 已占五十五）。
- 前置：77AH-F 已归位（4865903；单行截断已部署，副标题行自带省略号）。
- feat 提交：3fb05c3（10 文件）。

## 1. 任务 0 证据（只读贴回存档）

- 章节结构：`parse_article` 产 `chapters=[{title, paras:[{kind,text}...]}]`（:204/235）；空 paras 章节存在（`##` 后直接 `##`）；:267 回退项 paras=[intro 字符串]（str 非 dict，需兼容）；paras 首项 kind 可能是 code/table/list/component。
- `hammer_toc` 全仓唯一调用点（render_article.py:291）→ 改签名加可选参数 `subtitles=None`（旧调用零影响）。
- 无现成首句切分函数 → helper 9 行（`re.split(r"[。！？]", strip, maxsplit=1)[0].strip()`，禁分词依赖）。

## 2. 任务 1 实现

- `generate_hammer_upgrade_samples.py`：`hammer_toc(theme_key, chapter_titles, subtitles=None)`，等长对齐透传 `_toc_card`（缺省/不足回退 ""；末卡 PART /// 不动）。
- `render_article.py`：`chapter_first_sentence()`（首个 kind==para 的 text 取首句；code/table 首项跳过；无首段回退 ""）+ 组装 `chapter_subtitles` 传入。
- 主题文档单行说明补齐（77AH 欠账旧档观察项销）：theme-hammer.md 组件3节 + theme-moyu-green.md 组件3节各一句（单行纪律+副标题规则）；偏离初版简报说明：common-components.md 无 toc 节，唯二 toc 组件文档位是 hammer/moyu-green，属不扩。
- 测试：新增 `tests/test_hf77ai_toc_subtitle.py` 4 绿（三章首句进卡/空章节回退/长首句截断不断字/旧双参调用兼容；执行过程如实记：首版断言误将正文第二句排除，改按卡片区断言后全绿）。

## 3. 升版/锁链/回归

- 升版：gzh hammer.23→**hammer.24**（RELEASE_NOTES+SHA256SUMS 精选集更新：原 5 行不动+新测试 1 行；执行过程如实记：曾误全树重算 308 行，已回退 surgical）。
- relock **#116**（gzh hammer.24：`relock-gzh-design-20260914T091834Z-54d30d4f`，dry-run root/entrypoint/render_entry/component_source/version/commit/tree 变、manifest/validator 不变 → apply 全链 PASS，备份在册）；锁 sha `f960015b…→32568218…`，R93 双侧一致。
- 装机同步：装机侧 `subtitles=None` 参数 + `chapter_first_sentence` 双命中；装机侧重渲染实证（首句进卡/第二句排除/单行，exit 0）。
- doctor：双侧 PASS、OBS_69/OBS_68 双侧 MATCH（装机同步：gzh 8 文件+pipeline 3 文件）。
- 最终回归（relock 后）：见 §6（`.temp/upgrade_regression_77ai.log`）。
- 台账：OBS-386 + 口径 101 + 授权登记行（五十五→五十六）；唯一编号 `268 119 386 True`；R59 21=21 双差集空。

## 4. 基线链

`4865903（77AH-F）→ 3fb05c3（feat 77AI，含授权登记行+obs304/README 随档）→ <docs 本报告+锁链>`

## 5. 执行过程如实记

- executor 通道不可用，主智能体降级直接执行。
- flow-gate 拦截过渡文件写入一次，补简报登记后继续；过渡文件用后删。

## 6. 最终回归（relock 后）：见 `.temp/upgrade_regression_77ai.log`。
