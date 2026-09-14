# OBS-385 —— 77AH toc 单行截断部署验收报告（字节级落盘）

- 档号：77AH（toc 单行截断部署 + gzh 重锁同步）。
- 授权：RELOCK_ALLOWED 临时 0→1（批准人=用户，范围=gzh-design：复核 61d92a4 内容+VERSION/CHANGELOG+relock；pipeline 无锁条目不涉锁；GZH_DESIGN_WRITE_ALLOWED 维持 0——渲染 bugfix 部署，palette/配色/字号等主题设计值零触碰）。授权登记行随 feat 落账（序数按台账实况=五十五次，77AG 已占五十四）。
- 背景：61d92a4 已在 main 但装机侧仍旧代码 + repo 树漂移出锁快照（动锁技能未重锁：会话内直改流程违规）。
- feat 提交：7a8266b（5 文件）。

## 1. 任务 0 证据（只读贴回存档）

- 61d92a4 diff 全文：`generate_hammer_upgrade_samples.py`（_toc_card 两分支 4 个 `<p>` 加 `white-space:nowrap;overflow:hidden;text-overflow:ellipsis;` + 1 行注释 `toc 卡片单行纪律`）+ `tests/test_toc_card_single_line.py`（新增 59 行，2 测试）；无其他改动。
- 锁内 gzh：hammer.22（root 0c3a520c…/manifest ced84143…/76 文件/entrypoint 4c1346e8…/component_source 6504a1d2…/validator b3d74347…/full_commit 5bc3944…/source_tree 9dc2d3ad…）；仓侧实算 root 7e78c6e6… ≠ 锁基线（漂移实证）。
- 装机侧实证：截断串仅 2 处（旧 strike/subtitle），`toc 卡片单行纪律` 注释零命中——生产渲染仍走旧代码。
- 副标题数据源盘点（只盘点不动，77AI 备料）：无 `en_label_for`/映射表；`_toc_scroll`（:715-728）cards 由 title_lines 生成（subtitle 空串），仅末卡 `PART ///` 带「署名与 CTA」副标题。

## 2. 任务 1 实现

- 升版：RELEASE_NOTES hammer.22→**hammer.23**（77AH 条目）+ SHA256SUMS 精选集更新（原 5 行逐字节不动 + 新测试 1 行 a1b4f2b2…；执行过程如实记：曾误全树重算 308 行，已回退 surgical）。
- relock **#115**（gzh hammer.23：`relock-gzh-design-20260914T084200Z-5f0066d8`，dry-run root/component_source/version/commit/tree CHANGED、manifest/entrypoint/validator 不变 → apply 全链 PASS，备份在册）；锁 sha `83d9f5ce…→f960015b…`，R93 双侧一致。
- 装机同步：装机侧截断串 clamp **6 处** + `toc 卡片单行纪律` 注释命中（grep 实证，同步到位）。
- doctor：双侧 PASS、OBS_69/OBS_68 双侧 MATCH。

## 3. 任务 2 长标题重渲染实证（装机侧树，smartisan）

```text
[render_article] theme=hammer chapters=3 images=0 leaf=54 validator_errors=0
exit: 0
all titles present: True（3/3 超长章节名逐字在 HTML）
CLAMP count: 9
toc cards: 4（3 章节卡 + PART /// 末卡）
```

toc 卡标题单行（省略号）+ 卡片等高（固定 width:110px + 单行 clamp 构造保证）；已发旧文/旧草稿不受影响（重跑渲染才生效）。

## 4. 台账

- OBS-385 + 口径 100 + 授权登记行（五十四→五十五）；唯一编号 `267 119 385 True`；R59 21=21 双差集空。
- 审核方违规附记：会话内直改（未发档走另一窗口）/动锁未重锁（repo 超前锁无机器门径看守，收口靠本档）。

## 5. 基线链

`17b6fb5（77AG docs）→ 7a8266b（feat 77AH，含授权登记行+obs304/README 随档）→ <docs 本报告+锁链>`

## 6. 最终回归（relock 后）：见 `.temp/upgrade_regression_77ah.log`。
