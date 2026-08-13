# 档 45R — gzh-design 真实升版闭环(停机于第四步:渲染器 CLI 入口缺陷)

- 报告编号:gzh-design-upgrade-45R
- 执行日期:2026-08-02(Asia/Shanghai)
- 状态:**第一段(工具补全)沙箱验证通过并单独 commit;第二段 apply 成功、post-doctor PASS;第三步守卫升级完成;第四步离线验收时发现已安装/已锁定渲染器的 CLI 入口缺陷(生产调用方式必然崩溃)——按「任一步骤结果与预期不符,立即停机上报,不要调整实现去凑预期」停机。未执行第五步全面复核。未手工编辑任何 lock;未调微信接口;未跑完整 Pipeline;未删除任何文件。**
- 工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(dev/0.1.0-dev2)

## 第一段 工具补全(完成,commit `50b3ab1`)

1. 快照体检:`F:\AIXM\wxgzh-presnapshot-45\` 完好 —— 1102 文件、树哈希 `a2521440…` 逐字未变;两侧 lock 备份 `a9e07ef4…` 在位。
2. `skill_version` 纳入 `--source-tree` 字段集,取值直接复用 `skill_discovery._read_version`(L273-278,与 doctor 完全同源)。
3. 口径同源实测:构造 `\ufeff# gzh-design   v9.9.9-tricky  \r\n`(BOM+CRLF+前后空白)样本 → `_read_version` 读出与 relock 写入值逐字相等(`v9.9.9-tricky`)。
4. WARN(仅输出,不改退出码):root 变 version 未变 → 「代码已变但版本号未提升,lock 的版本标签将与实际内容脱节」;version 变 root 未变 → 另一条文案。
5. 测试 17 项全过(新增 5 项:写入+台账 old_/new_、口径同源、两个 WARN 方向、回滚还原);既有 relock 25 项 + full-fields 12 项不受影响。
6. 档 44 报告已追加更正节:原「skill_version 不可从树推导/走三字段 relock 即可」判断有误,由档 45 dry-run 实测推翻(如实写明)。
7. 沙箱演练(`relock45r-sandbox`,源 @2d069b7):全字段含 skill_version `v2026.07.18-hammer.1 → v2026.08.02-hammer.2`;installer PASS;post-doctor **PASS**(非档 45 推演的回滚);沙箱已删除;真实环境逐字未变。
- 工具段 commit:`50b3ab11f58822afc95bc2d2bf8120589347ad2b`(已 push)。

## 第二段 真实 apply(成功,exit 0)

- dry-run 复验:远端见证 a/b/c PASS;skill_version 在字段集内;零写入。
- `--apply` reason:`档45R gzh-design 升版:OBS-73 根治 + fenced code block + OBS-67/75/76 + version bump`
- 执行结果(完整输出 `.temp\relock45r-apply.txt`):
  - doctor gate: PASS (pre-write)
  - backup:`audit\upgrade-capability\lock-backups\skills.lock.20260802T131321Z.json`
  - ledger:`relock-gzh-design-20260802T131321Z-59d63817`
  - installer: PASS (source-tree install);doctor: PASS (post-relock);relock: OK
- 两侧 `skills.lock.json` sha:执行前 `A9E07EF4…`(双侧)→ 执行后 `CCEA9924C10CD06C2C07FC7EA8B8EFEBC7192EDDA915F421C86919A90B8514A9`(双侧一致)。
- 台账首条真实记录全文(节选):`old_root_sha256 9a8cd7f5… / new_root_sha256 802350c1…`、`old_entrypoint_sha256 e4023726… / new ca599b64…`、`old_render_entry_sha256 e4023726… / new ca599b64…`、`old_full_commit_sha 0007d7e6… / new 2d069b76…`、`old_source_tree_sha a1f40820… / new fcd6bc51…`、`old_branch chore/… / new fix/obs73-codeblock-docs`、`old_skill_version v2026.07.18-hammer.1 / new v2026.08.02-hammer.2`、`source_commit_verified true / remote_repo https://github.com/Amer-CN/gzh-design-skill`、`doctor_result PASS`(全文见 `skills.lock.history.json`)。
- 安装后真实 gzh-design:root `802350c1…`(76)、manifest `ced84143…`、version `v2026.08.02-hammer.2`、entry `ca599b64…`;receipt 诚实记录 commit `2d069b76…`/tree `fcd6bc51…`/root `802350c1…`。

## 第三步 守卫升级(完成)

- `wxgzh_pipeline/stages/gzh_design.py`:档 40 的行数守卫替换为**内容保真校验** `_intro_content_fidelity(md, html)`:
  - 从 final.html 反提取纯文本(去标签 + `html.unescape` + 空白归一化);
  - 取 final_article.md 首个 `## ` 之前的每个段落(`_intro_paras`,与渲染器同区域);
  - 第一行允许截断(要求前 40 字出现),第二行起必须**完整**存在;
  - 保留「取不到冻结文章即 FAIL」;无任何跳过开关/豁免参数。
- 测试重写(`tests/test_intro_guard.py`):9 项全 PASS(多行 PASS、首行截断 PASS、缺失第二段 FAIL 含原文、缺失首行前缀 FAIL、实体/空白归一化、三篇 RUN 形状断言)。

## 第四步 离线验收 —— **停机点(渲染器 CLI 缺陷)**

### 现象

以生产调用方式离线重渲染三篇历史 RUN 的首篇即崩溃:

```
python -X utf8 .agents\skills\gzh-design\scripts\render_article.py --article … --output-dir … --theme smartisan
rc: 1
Traceback … render_article.py line 246, in main → line 167, in render
NameError: name '_render_item' is not defined
```

### 根因(已定位,非环境问题)

- 已安装/已锁定(commit `2d069b7`、root `802350c1…`)的 `scripts/render_article.py` 中,`_render_item`(L291)与 `_hammer_code_block`(L299)定义在 **`if __name__ == "__main__": sys.exit(main())`(L287-288)之后**——该缺陷由档 43 commit `76a91e2` 引入。
- 生产调用是 CLI 子进程(`execmodel.LIVE_ENTRY` gzh_design entry = `scripts/render_article.py`):模块自上而下执行,到 L288 调用 `main()` 时两个函数尚未定义 → NameError → gzh_design 阶段必然失败(任何文章)。
- 档 43/44 测试全部走 `importlib.exec_module` 后调用 `main()`(整模块先执行完,函数已定义)→ 测试全绿,掩盖了 CLI 缺陷。对照实测:A) CLI 子进程 rc=1 NameError;B) importlib 路径 rc=0 正常渲染。
- 结论:**真实升版闭环已落地(lock/台账/安装树一致、doctor PASS),但锁定的渲染器入口在生产调用方式下无法渲染任何文章**——第四步验收正是为此设计,并成功拦截。

### 按指令处理

- 未自行修改 gzh-design 分支(档 45R 明示「2d069b7 即为最终源,无需再动」);
- 未调整任何断言/校验去迁就实现;
- 未执行第五步。

## 环境状态(停机时)

- 两侧 lock `CCEA9924…`;台账首条记录在库;备份文件在 `audit/upgrade-capability/lock-backups/`;安装侧 gzh-design = 缺陷版渲染器(与 lock 一致)。
- doctor 会 PASS(hash/version/entrypoints 均一致),但 gzh_design 阶段 live 渲染必失败——即「锁一致性」与「功能可用」在此缺陷下脱节。
- 快照 `F:\AIXM\wxgzh-presnapshot-45\` 完好(回退路径仍可用,未动用)。

## 需要裁决的问题

1. **修复分支缺陷**(建议,优先级最高):在 `fix/obs73-codeblock-docs` 把 `_render_item`/`_hammer_code_block` 移动到 `if __name__ == "__main__"` 之前(纯代码位置调整,零行为变化,importlib 路径输出不变),push 后重新实算 root/entry/tree,再走一次 `relock --apply`(或按你授权的方式重锁)。建议同时给该缺陷登记 OBS 编号(如 OBS-77:renderer CLI 入口 NameError,importlib 测试掩盖)。
2. **补一条 CLI 级回归测试**(建议随修复):在 gzh-design 仓库 tests 中新增以 `subprocess` 直接运行 `render_article.py` 的用例,防止再次被 importlib 路径掩盖。
3. 若你选择回滚:恢复手段为快照 `F:\AIXM\wxgzh-presnapshot-45\`(整树)+ 两侧 lock 备份(逐字节),需另行授权执行。
4. 第五步全面复核(含 receipt 三态、`_find_upgrade_chain`、upgrade_regression、双侧 doctor、安装器同步)在缺陷修复并重锁后恢复执行。

## 双仓库 SHA

- Amer-CN/gzh-design-skill:`fix/obs73-codeblock-docs` HEAD = `2d069b7664786f2dae2b7b322b1200be59d9315a`(含缺陷,待裁决修复)
- wxgzh-pipeline:本报告 commit = 见提交输出(含守卫升级、测试、observability 基线更新、lock/台账/备份)
