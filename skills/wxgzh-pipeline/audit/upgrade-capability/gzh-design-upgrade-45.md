# 档 45 — 档 43 恢复执行:gzh-design 真实升版闭环(停机于第二步 dry-run 之后)

- 报告编号:gzh-design-upgrade-45
- 执行日期:2026-08-02(Asia/Shanghai)
- 状态:**第零步、第一步完成;第二步 dry-run 完成且零写入;经代码级推演确认 --apply 必在 post-doctor 处失败并自动回滚,依「任一步骤结果与预期不符,立即停机上报,禁止自行修复后继续」在 --apply 之前停机。未执行第二步 apply 及第三~五步。未手工编辑任何 skills.lock.json;未调微信接口;未跑完整 Pipeline;未删除任何文件。**
- 工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(dev/0.1.0-dev2,起点 HEAD `cb4b84e`)

## 第零步 回退路径(完成)

- 快照:`F:\AIXM\wxgzh-presnapshot-45\skills-asfound`(真实 `.agents\skills` 整树逐字节副本,不含 __pycache__/*.pyc;不入 git,不在 .temp 下)。
- 快照整树:1102 文件,树哈希 `a252144048ef077a8cf1c8a0d340370bb822f46e3b58b38c8fc3d21aeaf6288c`(算法:sha256 连接按 posix 路径排序的 `relpath:sha256` 行,与档 34 同口径)。
- 与档 42 OBS_68 检查值比对:快照中 wxgzh-pipeline 子树与档 44 同步时 repo HEAD 一致(571 文件 0 差异;唯一差异为同步后新增的 `audit/upgrade-capability/relock-full-fields-44.md`,属正常滞后,快照即为当前安装态本身)。
- 两侧 lock 备份:`skills.lock.repo.json` / `skills.lock.installed.json`,sha 均 `a9e07ef4…`。
- 完整性确认:快照内四锁 root 实算 == lock(super-writer `46a00a1b…`/zh-human-writing `18491b36…`/media-enrichment `0d8aea21…`/gzh-design `9a8cd7f5…`);若本档任一步失败且 relock 自动回滚也失败,恢复手段即此快照(整树还原 + 两侧 lock 从备份还原)。

## 第一步 补版本号(完成)

- 当前版本:`v2026.07.18-hammer.1`。本次含行为变更(intro 段落进正文、新增代码块渲染)→ 功能性升级 → 递增至 **`v2026.08.02-hammer.2`**(日期字段随发布日推进,预发布序号 1→2)。
- 版本号声明位置(共 3 处,全部更新):
  1. `RELEASE_NOTES.md` L1 标题;
  2. `RELEASE_NOTES.md` L64「追加变更」小节标题(档 43 所加,原写「未改版本号」,已同步改为新版本号并去掉该表述);
  3. `WXGZH_PIPELINE_INTEGRATION.md` L11 `Locked version`(顺带把 L12 已失真的 `Locked root SHA-256`(旧值 127601fa,与当前 lock 不符)刷新为新 root)。
- SHA256SUMS:所列 5 文件(SKILL.md/publish_wechat_draft.py/validate_gzh_html.py/theme-index.md/theme-hammer.md)均未因版本提升变化 → 不失配,无需重算。
- 两个 commit 已 push 到 `fix/obs73-codeblock-docs`:`efb88b2`(版本提升)+ `2d069b7`(root 哈希刷新);分支 HEAD = **`2d069b7664786f2dae2b7b322b1200be59d9315a`**。全量测试 185 passed(3 项既有 fixed_signature 失败与档 43 相同,预存在)。
- 第 9 项重算(档 44 演练值 4d68cd90/b0d81ef7 已作废):

| 字段 | 新值(HEAD 2d069b7) |
|---|---|
| skill_root_sha256 | `802350c131ed537b33e874490749b8b6f71d8bb6c83c4038d678d548c31daafc`(76) |
| runtime_manifest_sha256 | `ced841439195453497e67a63186823f60eee7155b9de472e936c3d4d767e33b2`(不变) |
| runtime_file_count | 76(不变) |
| entrypoint_sha256 / render_entry_sha256 | `ca599b64266777497bdbfb5980c2dda697296be0143fdc7b03e509172cf43275` |
| validator_sha256 | `b986ae77…`(不变) |
| component_source_sha256 | `02c0d884…`(不变) |
| source_tree_sha(HEAD 树) | `fcd6bc517e2b71929bb21b6a8215771a6af98373` |

## 第二步 真实 relock dry-run(完成,零写入)→ **停机点**

完整 dry-run 输出(真实环境,只读;`.temp\relock45-dryrun.txt` 留档):

```
远端见证 PASS (a/b/c)
=== gzh-design ===
installed_dir: F:\AIXM\wxgzh\repos\gzh-design-skill-43r-build
skill_root_sha256: 9a8cd7f5… -> 802350c1…  (CHANGED)
runtime_manifest_sha256: ced84143… -> ced84143…
runtime_file_count: 76 -> 76
entrypoint_sha256: e4023726… -> ca599b64…  (CHANGED)
validator_sha256: b986ae77… -> b986ae77…
render_entry_sha256: e4023726… -> ca599b64…  (CHANGED)
component_source_sha256: 02c0d884… -> 02c0d884…
full_commit_sha: 0007d7e6… -> 2d069b76…  (CHANGED)
source_tree_sha: a1f40820… -> fcd6bc51…  (CHANGED)
branch: chore/wxgzh-pipeline-dev2-integration -> fix/obs73-codeblock-docs  (CHANGED)
status: CHANGED
dry-run: 1 skill(s) checked, 1 CHANGED — run with --apply to write (none written)
```

- 远端见证三项(a commit 远端可达 / b 远端树与本地树逐字一致 / c 待写值==远端实算)全部 PASS(真实网络,细节同档 44 演练)。
- 逐字段核对:root `9a8cd7f5→802350c1`、manifest/count 不变、entrypoint/render `e4023726→ca599b64`、commit `0007d7e6→2d069b76`、tree `a1f40820→fcd6bc51`、branch→`fix/obs73-codeblock-docs` —— 全部符合预期。
- dry-run 零写入:两侧 lock sha 均 `a9e07ef4…`(未变),台账不存在。

### 停机原因(代码级确定性推演,非猜测)

**`--apply` 必在 post-doctor 处失败并自动回滚,闭环无法完成**:relock 不管理 `skill_version` 字段,而本档第一步已把版本号提升。

证据链:
1. `wxgzh_pipeline/skill_discovery.py` `_read_version` L273-278:gzh-design 的 current_version 读 **`RELEASE_NOTES.md` 首行** → 安装新树后为 `v2026.08.02-hammer.2`。
2. `discover` L256-257:`version_ok = exists and cur_ver == locked.get("skill_version")`;`ok` 包含 version_ok。
3. relock(`scripts/relock.py`):`_ALL_FIELDS` 不含 `skill_version`,写入循环只写 `row["new"]` 的键;本次 dry-run 输出中也没有 skill_version 行。
4. 因此 apply 后:lock.skill_version 仍为 `v2026.07.18-hammer.1` ≠ 安装树 `v2026.08.02-hammer.2` → post-doctor `FAIL_CLOSED=true` → 自动回滚(lock+台账+安装树),退出码 4,环境回到快照态。
5. 档 44 报告曾写「skill_version 由技能文档显式升版后,走常规三字段 relock 即可」——**该表述被本次实测推翻**:三字段 relock 同样不写 skill_version,任何版本提升都会破坏 version_ok。

按指令「任一步骤结果与预期不符,立即停机上报,禁止自行修复后继续」与第 14 项「不要手工补救」,本档在 `--apply` 之前停机:不执行必然失败的写操作,不手工编辑 lock,不自行扩展 relock。

## 第三~五步:未执行(停机)

守卫升级、离线回归验收、全面复核均依赖第二步 apply 成功,按停机规则未执行。

## 环境状态(停机时)

- 真实四锁 root 逐字未变(gzh-design 仍 `9a8cd7f5…`);两侧 lock sha `a9e07ef4…` 未动;台账不存在;`F:\AIXM\wxgzh-presnapshot-45\` 保留(快照,非 .temp);gzh-design-skill 远端 main/chore 未动,`fix/obs73-codeblock-docs` = `2d069b7` 已 push。

## 需要裁决的问题

1. **授权扩展 relock 的 skill_version 同步**(建议):在 `--source-tree` 模式把 `skill_version` 纳入字段集,取值 = 源树 `RELEASE_NOTES.md` 首行(与 `_read_version` 同口径,仅 gzh-design 有该语义;其它 skill 走 VERSION 文件或保持原值),dry-run 逐项打印、台账记录 old/new、随 lock 一起写入与回滚。理由:这是版本提升后闭环成立的必要条件;档 44 的排除理由已被实测推翻。
2. 裁决后恢复执行:重跑 dry-run → `--apply`(reason 已定)→ 第三步守卫升级 → 第四步三篇历史 RUN 离线验收 → 第五步全面复核。分支 HEAD `2d069b7`、新哈希(802350c1/fcd6bc51)已就绪,见证已 PASS。

## 双仓库 SHA

- Amer-CN/gzh-design-skill:`fix/obs73-codeblock-docs` HEAD = `2d069b7664786f2dae2b7b322b1200be59d9315a`
- wxgzh-pipeline:本报告 commit = 见提交输出
