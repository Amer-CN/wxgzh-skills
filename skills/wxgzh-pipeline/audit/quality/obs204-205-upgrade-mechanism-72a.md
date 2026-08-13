# 档72A — 升级机制真跑（单变量对照）+ 授权变更登记

## ① 授权变更（3d，用户已批准）

`RELOCK_ALLOWED` 由 0 改为 **1**，批准人=用户，范围=整个升级期（72A/72B/72C），**恢复条件=super-writer 与 zh-human-writing 两个 skill 升级全部完成后立即改回 0**。已逐字写入台账口径「授权变更登记」节；本档 a 段复述如上。

## ② 0 段 基线固化

- 0a：锁四 skill sha（super-writer `1e58d01e…` / zh-human-writing `0c8962f3…` / media-enrichment `18414cc9…` / gzh-design `ea2fb70…`）；OBS-159 内嵌基线 `f2b5f390…` @ `wxgzh_pipeline/observability.py:40`；OBS_68=654/654、OBS_69 MATCH；pytest **448/446/0/0/1/1**。
- 0b 基线 RUN：`20260807T223408-vibe-coding-guide-16-e0k79p`；final_article sha256 `3e829be0cb7cea00f0efbb88d00a71d86425454a2b4439dbf6baede80042f6f0`、57 行/3372 字符；OBS88 `16/16/10/material_derived/PASS`；upload `wechat_audit`。已声明固化。

## ③ 1 段 最小改动 + relock 真跑

- 1a（R91 语义中性）：super-writer `SKILL.md` 顶部加注释 `# upgrade-capability 机制验证（档 72A）：语义中性改动，不影响任何输出。`（1 行插入），commit `33c9a60edefdda9cba19aecfddd88eb7466296ec`。
- 1b relock（远端见证 a/b/c PASS）：`--skill super-writer --apply --source-tree .temp/obs72-sync-src/super-writer --source-commit 33c9a60… --reason "72A upgrade-capability 单变量对照(语义中性注释,不影响输出)"`；relock 内置 pytest 因 OBS-159 基线未同步 3 项红（正是本档要抓的坑），R93 随即同步后全绿。
- 1c 双侧 sha 对照（四个 skill 全列）：

| skill | 旧 full_commit_sha | 新 full_commit_sha | repo 侧 | installed 侧 |
|---|---|---|---|---|
| super-writer | `1e58d01e38346018886ab1ad6a183228263eae49` | `33c9a60edefdda9cba19aecfddd88eb7466296ec` | 一致 | 一致 |
| zh-human-writing | `0c8962f354e9acc73f29bc57a8b328fc98695a10` | 不变 | 一致 | 一致 |
| media-enrichment | `18414cc9cddb2a9be6782535a9f57ca1860a47d3` | 不变 | 一致 | 一致 |
| gzh-design | `ea2fb70ab84785dd8a6d91880acfe31444855cf3` | 不变 | 一致 | 一致 |

双侧锁 sha：`f2b5f390…` → `f8b7022187c0d8a91bfc73ab5893bc978293aec7314c90bdbc6320d3926aa957`，repo=installed（S94 ✓）。
- 1d（R93，同一次操作）：OBS-159 内嵌基线 `observability.py:40`：`f2b5f390…` → `f8b70221…`（同步后 test_observability 10/10 绿，S95 ✓）。
- 1e：`ci.yml:33` super-writer ref 仍 `1e58d01e…`，与锁 `33c9a60…` 不一致（本档不改 workflow，R94）；类 D 陈旧常量 4→5 项，登记不修。

## ④ 2 段 机制验证

- 2a upgrade_regression 逐项：`pytest: PASS (1 explicit deselects)` / `relock dry-run x4: PASS`（super-writer/zh-human-writing/media-enrichment/gzh-design 均「无变化 OK」）/ `doctor --require-wechat: PASS` / `validate_gzh_html cross-side: SKIP（P2 未落地）` / **ALL PASS**（S96 ✓）。
- 2b pytest：装前 **448/446/0/0/1/1**（junit），装后同；无劣化（S97 ✓；relock 内置 3 项红为 OBS-159 未同步的预期症状，同步后消除）。
- 2c OBS_68 = **655/655**（654 + 1 = relock 生成的 lock-backup `audit/upgrade-capability/lock-backups/skills.lock.20260807T143755Z.json`，如实说明；super-writer 技能不在 pipeline 仓计数内）；OBS_69 MATCH（新基线 f8b70221）。
- 2d 四项对照：

| 项 | 0b 基线 | 2d 实测（RUN `20260807T224442-…-4wbunx`） | 相同 |
|---|---|---|---|
| final_article sha256 | `3e829be0cb7cea00f0efbb88d00a71d86425454a2b4439dbf6baede80042f6f0` | `3e829be0cb7cea00f0efbb88d00a71d86425454a2b4439dbf6baede80042f6f0` | ✅ |
| 行数 / 字符数 | 57 / 3372 | 57 / 3372 | ✅ |
| OBS88 五字段 | 16/16/10/material_derived/PASS | 16/16/10/material_derived/PASS | ✅ |
| upload mode | wechat_audit | wechat_audit | ✅ |

**S93 未触发**——语义中性改动后产物逐字不变，升级机制单变量对照成立。

## ⑤ 3 段 台账

- 3a：OBS-199 收尾观察：0b/2d RUN 产物中 "cover" 命中均为 hammer `cover_breaking` 组件计数，无 `_select_live_cover` 失败路径（wechat 阶段因 create=False 未执行）→ **未观察到 cover 失败，本 RUN 无 cover 失败路径**（未构造）。
- 3b：198 状态 `部分修` → `已修`（两条实例均已闭合），已退出未修清单分区。
- 3c：补登 204（numstat 汇报不实，已处理=R92 生效）/ 205（198 状态陈旧，指令缺陷第 74 处，已修）。
- 3e：唯一 OBS 编号数 **85 → 87**（119–205 连续，S92 ✓）；R59：全表未修+部分修 `{122,131,148,158,159,175,177,181,182,186,193,200}`（12）== 分区编号行（12）✓；台账文件行数 154。
- 3f：口径第 21 条已加。

## ⑥ 没证明什么 + 新发现没修

- 没证明：真实内容升级（72A 仅机制验证，无提示词变化）；zh-human-writing 的 relock 链（本次只动 super-writer）；CI 绿（四类根因仍在，且类 D 因 ci.yml ref 陈旧 +1）。
- 新发现没修：relock 内置 upgrade_regression 会在 OBS-159 未同步时先红 3 项（机制自身对 OBS-159 的暴露是预期的，但「先红后同步」的顺序噪声可在未来 relock 档考虑内置同步）；`ci.yml` super-writer ref 陈旧（类 D +1，留 CI 环境档）；lock-backup 新文件计入 OBS_68（计数口径如实记录）。
