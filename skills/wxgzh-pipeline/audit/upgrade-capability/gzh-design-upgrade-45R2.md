# 档 45R2 — OBS-78 CLI 修复 + relock 入口冒烟 + OBS-79 备份纠正 + 闭环完成

- 报告编号:gzh-design-upgrade-45R2
- 执行日期:2026-08-02(Asia/Shanghai)
- 状态:**全流程完成**。第一步~第七步全部走通;真实 relock --apply 第二次执行成功且入口冒烟 PASS;三篇历史 RUN 生产 CLI 重渲染验收全过;OBS-79 备份已纠正。未回滚,采纳方案①。
- 工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(dev/0.1.0-dev2)

## 第一步 修渲染器(完成,commit `9596ecc`,已 push)

1. `_render_item`/`_hammer_code_block` 纯位置移动到 `__main__` 守卫之前(L286/L294),函数体零改动;CLI 实跑 `assets/sample-article.md` rc=0。
2. 全文扫查 `render_article.py` 与 `generate_hammer_upgrade_samples.py`:均只有 1 个 `__main__` 守卫,守卫后无任何 `def/class` 定义。
3. PALETTES 验证:已注册主题 `hammer`/`moyu-green` 均含 `body_color`,无 KeyError 风险。
4. `usage["paragraph"]` 对 code item 计数:已核实 `validate_theme_identity` 基于 HTML 结构指纹(cover/toc/chapter_title/signature/footer/img),不读 usage 的 paragraph 计数;gzh_design 阶段的 component_usage_report 由校验器以指纹重写。无影响,保持原样。

## 第二步 CLI 级测试(完成)

5-7. 新增 `tests/test_render_article_cli.py`(4 项,全部 subprocess 生产路径,禁止 importlib):多段 intro rc=0 且段落完整、fenced code rc=0 且逐字、无 bindings 最小调用、stderr 无 NameError/AttributeError/KeyError(覆盖全部主题)。
8. importlib 式盘账(据实):gzh-design 仓库测试中,`test_render_article_hotfix.py` 与 `test_intro_paras_and_code_block.py` 两个文件为 importlib 式(exec_module 后调 main),覆盖渲染器 CLI 入口能力;本档不改,已记账(OBS-78 已注明)。

## 第三步 relock 入口冒烟(完成)

9-11. `--source-tree` 模式在 post-doctor 之后、判定成功之前执行「锁定入口冒烟」:CLI 子进程调该 skill 的 lock entrypoint,用 skill 自带样本(gzh-design = `assets/sample-article.md`);退出码非 0 或 stderr 含 Traceback/NameError/AttributeError/KeyError → 失败;失败处理与 post-doctor 一致(整链回滚,退出码 4);**无任何跳过开关/参数/环境变量**。
12. 无可冒烟入口的 skill:显式打印「无入口,跳过冒烟」;当前仅 gzh-design 配置了冒烟样本;super-writer / zh-human-writing 为 agent 阶段(无 CLI 渲染入口),media-enrichment 有 CLI 但无自带最小样本 —— 据实列出,均按「无入口样本」显式跳过(真实场景只对 gzh-design 使用 --source-tree)。
13. 测试 4 项:冒烟失败回滚(exit 4、lock/tree 字节还原)、冒烟通过放行、无入口显式跳过、坏→拦→回滚→修→重跑成功。
14. **反向验证(本档核心验收)**:沙箱内用 2d069b7 的真实坏文件直接跑冒烟 —— `NameError: name '_render_item' is not defined` 被准确检出(ok=False);配合单元测试的全链回滚覆盖,证明冒烟机制对已知坏版本有效。附注:对 2d069b7 的完整 relock 反向演练不可行且被见证机制正确拒绝 —— 该 commit 已随分支推进在远端不可达(ls-remote 不含)→ 见证 (a) 失败退出 2,这本身是远端见证在正常工作的正面证据。

## 第四步 备份路径纠正 OBS-79(完成)

15. relock 安装树备份默认改到仓库外:`<project-root 父目录>/wxgzh-relock-tree-backups/`(与 `F:\AIXM\wxgzh-presnapshot-45\` 同级);新增 `--tree-backup-dir` 供测试注入。
16. 仓库内已提交的 `audit/upgrade-capability/lock-backups/skills-tree.gzh-design.preinstall/`(295 文件)已先复制到仓库外 `F:\AIXM\wxgzh-tree-backups-45R2\gzh-design.preinstall\` 并**逐字校验等价(295/295,0 差异)后**才从 git 移除(git rm + 工作区删除)。
17. `.gitignore` 新增规则 `audit/upgrade-capability/lock-backups/skills-tree.*.preinstall/`,防再次误入。
18. lock-backups 下其它整树备份:仅上述一个整树;单文件锁备份 `skills.lock.*.json` 保留(审计证据,非整树)。

## 第五步 重新 relock --apply(完成,第二次真实执行)

- 重算 9596ecc 哈希:root `f59d64bb…`(76)、manifest `ced84143…`(不变)、entrypoint `8bc3ccee…`、validator/component 不变、version `v2026.08.02-hammer.2`、tree `5832ead0…`。
- dry-run:见证 a/b/c PASS;全字段 旧→新 核对无误;WARN 按设计触发(root 变 version 未变 —— 本次为 OBS-78 代码修正,版本号未再提升,如实告警)。
- `--apply` reason:`档45R2 gzh-design 升版修正:OBS-78 CLI 入口修复 + 入口冒烟`;exit 0。
- 锁 sha:前 `CCEA9924…`(双侧)→ 后 `8FB33D83…`(双侧一致)。
- 台账第二条:`relock-gzh-design-20260802T133343Z-843f9372`(root 802350c1→f59d64bb、commit 2d069b76→9596ecc、entry ca599b64→8bc3ccee、tree fcd6bc51→5832ead0;version 无变化故无 old/new_skill_version)。
- 冒烟输出:`gzh-design: entrypoint smoke PASS (CLI subprocess, production path)`;post-doctor PASS。
- 链追溯:`_find_upgrade_chain('9a8cd7f5…' → 'f59d64bb…')` 命中两条记录 `[59d63817, 843f9372]` ✓。

## 第六步 三篇历史 RUN 验收(完成,生产 CLI)

- RUN1(2 段):para1 prefix40 OK / para2 full OK;RUN2(1 段 198 字):prefix40 OK;事件 RUN(8 段):全部 OK。三篇 `guard_ok=True`(档 40 时全 FAIL 的对照成立),stderr 干净。
- fenced code 构造输入:rc=0、无反引号残留、代码逐字(含 4 空格缩进)、`<pre>` 内为可复制文本(无 img)、`validate_gzh_html` errors=0。
- 结构指纹评估(档 43 挂账至今):三篇产物 `structure_ok=True`、chapter_count 与 `_count_h2` 一致(4/4/4);CODE 用例带 bindings 后 `structure_ok=True`(img_types=2,chapters=1)—— 证明 intro 段落与代码块不触碰任何现有结构校验;一处未放宽。注:离线无 exec_evidence 时 THEME_IDENTITY 按设计为 FAIL(非 official 语义),不影响结论。

## 第七步 全面复核(完成)

30. doctor `--require-wechat` 双侧 PASS(exit 0),四锁 hash_ok 全 true,FAIL_CLOSED=false;档 42 两项 WARN:`OBS_69_LOCK_MATCH=MATCH`、`OBS_68_PIPELINE_MATCH=MATCH`(577/577)。
31. `upgrade_regression.py` ALL PASS,排除清单仍 1 项。
32. 四锁 relock dry-run 全部「无变化」(gzh-design 刚重锁完)。
33. 安装器同步(bundle-staging-45R2):安装侧与 repo HEAD **577 文件逐字一致**(0 差异)。
34. 三锁逐字未变(super-writer `46a00a1b…`/zh-human-writing `18491b36…`/media-enrichment `0d8aea21…`);证据目录与 staging 全部完好(bundle-staging-37/40/42/44/45R2、`.temp\obs62s-build-staging`、`incident-20260802`、`wxgzh-tree-backups-45R2`)。
35. 三篇 receipt 的 gzh_design 阶段均判 **SKILL_UPGRADED**,entry_ids 恰为两条台账记录(依据:receipt 记录 root `9a8cd7f5…` ≠ 当前 `f59d64bb…`,台账存在完整链 9a8cd7f5→802350c1→f59d64bb)。ok=False 的其余字段差异据实说明:RUN1/RUN2 的 receipt 输入路径指向已归档的 `.temp` 原路径(input missing now),EVENT 的 entrypoint hash mismatch(入口文件随升版改变) —— 均与本次升版预期一致,不影响三态判定。
36. 快照 `F:\AIXM\wxgzh-presnapshot-45\` 全程未动用,复验 1102 文件 / 树哈希 `a2521440…` 逐字未变。

## 风险点与说明

1. 冒烟仅覆盖配置了样本的 skill(gzh-design);其它 skill 走「无入口,跳过冒烟」显式路径,若未来对它们做 --source-tree 升版,需先补冒烟样本配置。
2. WARN(root 变 version 未变)在本档如实触发:OBS-78 修正未提升版本号,lock 版本标签(v2026.08.02-hammer.2)与实际内容存在「修正级差异」,如后续要发版可考虑 hammer.3。
3. 安装树备份现在落仓库外 `F:\AIXM\wxgzh-tree-backups-45R2\`(TEMP_CLEANUP_ALLOWED=false,保留)。

## 双仓库 SHA

- Amer-CN/gzh-design-skill:`fix/obs73-codeblock-docs` HEAD = `9596eccb67a53d639cfa7990d39fa6c7f200c919`
- wxgzh-pipeline:本报告 commit = 见提交输出
