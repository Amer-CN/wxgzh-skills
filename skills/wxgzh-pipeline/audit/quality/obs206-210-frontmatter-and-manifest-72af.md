# 档72A-F — 回滚 + 补真验证（front-matter 禁区 + required_files 响应性）

## ① 授权复述（3d 恢复条件逐字）

`RELOCK_ALLOWED` 于档 72A 由 0 改为 1，批准人=用户，范围=整个升级期（72A/72B/72C），**恢复条件=super-writer 与 zh-human-writing 两个 skill 升级全部完成后立即改回 0**。在恢复之前，每一档的 a 段必须显式复述本条恢复条件。（72A-F 沿用，未变更。）

## ② 1 段 取证（先取证后动手）

- 1a/1b：源树与 installed 侧 super-writer SKILL.md 前 8 行逐字一致（均含首行注释）→ **SKILL.md 确实被安装**（72A relock 的 source-tree install 生效）；OBS-206 的「没被安装」假设不成立，问题在「改动位置 + 无法验证」。
- 1c 三态 front-matter 解析（python + yaml.safe_load，回显原文）：
  - 状态1 当前 installed 版（首行注释）：`front-matter 未找到(首行非 ---) | name = None` → **解析坏了（OBS-207 实锤）**
  - 状态2 删掉首行后：`OK | name = super-writer`
  - 状态3 1e58d01 原版：`OK | name = super-writer`

## ③ 2 段 一次提交（回滚 + 补测）

super-writer commit `a943cfdcc9d95205ef1e6fe8fc88093269345592`（已 push `33c9a60..a943cfd`）：
- SKILL.md：删除首行注释（-1 行，回滚到 1e58d01e 原样）
- scripts/validate_semantic_map.py：docstring 后加 `# 72A-F: runtime_manifest 响应性验证，语义中性。`（+1 行，required_files 内，R96）

## ④ 3 段 relock 第十三次 + 三必答 + 同步

- 3a relock 回显要点：`远端见证 PASS (a/b/c)`；`full_commit_sha 33c9a60… → a943cfd…`、`source_tree_sha a1d93412… → 36f94dd7…`、`skill_root_sha256 c482b8c6… → b5dc5b92…`；`installer PASS (source-tree install)`；`entrypoint smoke PASS`。
- 3b 三必答（原文）：
  - `git diff 1e58d01e -- SKILL.md` = **空**（回滚精确，S98 ✓）
  - `runtime_manifest_sha256: 4e5ed52520ec123378543271143489f2842b24fc7109fdbc2e15c0ee02d5a8b6 -> 4e5ed52520ec123378543271143489f2842b24fc7109fdbc2e15c0ee02d5a8b6` —— **未变化**（期望「必须变化」被违反：validate_semantic_map.py 在 required_files 内但 runtime_manifest_sha256 不响应 → 锁完整性指标形同虚设，登记进 206）
  - `runtime_file_count: 50 -> 50` ✓（没多没少）
- 3c（R93 同次操作）：OBS-159 基线 `observability.py:40` `f8b70221…` → `6c1caea25dfb7de73b608883afb6e434239fbdc3fa81e74015015b754130fd8d`；同次修正 OBS-209 两行陈旧注释（a9e07ef4…/档57 → 72A-F relock 口径）。
- 3d 双侧一致（S94）：repo==installed 锁 sha `6c1caea2…`；四 skill full_commit_sha 双侧一致（super-writer `a943cfd…`，其余三个不变）。

## ⑤ 4 段 验证

- 4a upgrade_regression：`pytest PASS (1 explicit deselects)` / `relock dry-run x4: PASS`（四 skill 无变化）/ `doctor --require-wechat: PASS` / cross-side SKIP / **ALL PASS**（S100 ✓；首跑 FAIL 系 installed 侧 observability.py 未随 relock 传播，bundle+install 后消除）。
- 4b pytest：装前 **448/446/0/0/1/1**、装后同（S100 ✓）。
- 4c OBS_68 = **656/656**（655 + 1：第二次 relock 生成的 lock-backup `skills.lock.20260807T150758Z.json`；报告 md 不计，OBS-107 口径；OBS-210 已登记该计数范围）；OBS_69 MATCH（新基线 6c1caea2）。
- 4d 端到端 RUN `20260807T231946-vibe-coding-guide-16-sxev3b`：final_article sha `3e829be0cb7cea00f0efbb88d00a71d86425454a2b4439dbf6baede80042f6f0`、57 行/3372 字符 —— **照记，不作机制证据（OBS-208 判据作废）**。

## ⑥ 5 段 台账

- 5a 补登 206（部分修）/207（已修）/208（已裁决：判据作废）/209（已修）/210（已修，计数口径）；206 已进未修清单分区。
- 5b 口径第 22 条已加（逐字）。
- 5c 唯一 OBS 编号数 **87 → 92**（119–210 连续，S92 ✓）；R59：全表未修+部分修 `{122,131,148,158,159,175,177,181,182,186,193,200,206}`（13）== 分区编号行（13）✓；台账文件行数 161。

## ⑦ 没证明什么 + 新发现没修

- 没证明：runtime_manifest_sha256 对 required_files 的响应机制（实测不响应，206 待修）；真实内容升级；CI 绿。
- 新发现没修：runtime_manifest_sha256 与 required_files 内容脱钩（本次核心新发现，已并入 206）；relock 内置回归在 OBS-159 未同步时先红（同 72A 观察）；upgrade_regression 首跑失败为 installed 侧传播滞后（bundle+install 后消除，非代码缺陷）。
