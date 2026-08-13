# 档 37 — 恢复基线报告

- 报告编号:baseline-restore-37
- 执行日期:2026-08-02(UTC 时间戳 2026-08-01T17:4x)
- 工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(branch `dev/0.1.0-dev2`)
- 授权状态:INSTALL_ALLOWED=true(仅本档、仅下列指定操作);RELOCK_APPLY_ALLOWED=false / SKILLS_TREE_WRITE_ALLOWED=false(除安装器外)/ P2_START_ALLOWED=false
- 执行方式:恢复全部经由正式安装器 `scripts/install.py`(bundle 模式,事务化 backup+回滚+receipts);未手工覆盖任何安装侧文件;未手工编辑 skills.lock.json;未调用微信接口;未跑完整 Pipeline;未删除证据副本;未删除 .temp 事件 RUN 目录。

## 第一步 归档事件产物(已完成,commit `1b2679e`)

1. 事件 RUN `20260801T231452-vibe-coding-guide-v2-1-1vg6jx` 自 `.temp\wxgzh-pipeline\` 完整归档至 `audit/runs/`:
   - 102 个源文件逐文件 sha256 与 .temp 源逐字一致(content-diff=0、无缺失无多余)
   - 归档树另含 `UNCONTROLLED.md`(零批准合同 / known_allowed 图表路径 / 12 次重复上传 / 封面未批准 / 热修基线 / 保留用途 OBS-71 回归样本)
   - 归档整树 103 文件
2. 副作用总账新建 `audit/side-effects/ledger.md`:4 篇归档 RUN + 事件 RUN;uploadimg 累计 16 次、草稿 #1/#2/#3、封面 add_material 3 次、无发布/群发/定时/删除。
3. 已 push:`968fc88..1b2679e dev/0.1.0-dev2`。

## 关键勘察结论:media-enrichment 锁定 root `0d8aea21…` 的来源(第二步前置)

- 锁定值:`skill_root_sha256=0d8aea2169ce…`、`runtime_manifest_sha256=172aa1b8…`、`runtime_file_count=57`、`full_commit_sha=cedf92ca45b0…`、`source_tree_sha=c2b914a2…`、`skill_version=0.1.0-dev7-hotfix4`。
- 实算对照(全部用仓库自带 `skill_discovery.compute_root_sha` / `_file_sha`,行尾归一):
  - GitHub `Amer-CN/media-enrichment @ cedf92ca`(sibling HEAD,工作树干净;`git ls-remote` 确认远端分支即 cedf92ca):root=`b8257469…`,entrypoint=`6429e4db…` → 与 lock 的 root/entrypoint 均不一致
  - 证据副本/事件态(asfound,热修 2 文件):root=`0c2d676b…`,entrypoint=`afc2e5a5…` → 不一致
  - `.agents` 全部历史备份(skills-hotfix6-lastknown-good / skills-hotfix7R3 / skills-halfstate 等):media root 全部=`b8257469…` → 均不一致
- 溯源:lock 变更来自 pipeline 仓库 commit `7c91489`(2026-08-01 03:20,OBS-53「media idempotency and configurable minimum」),该 commit 把 media root 从 `1dab6184…` 改为 `0d8aea21…`、entrypoint 改为 `2d877a93…`。
- 唯一匹配树:`.temp\obs62s-build-staging\portable-bundle\locked-skills\media-enrichment`(2026-08-01 12:54 24S 构建暂存,事件前):root=`0d8aea21…`、manifest=`172aa1b8…`、entrypoint=`2d877a93…`、57 文件 — 与 lock 逐字一致,全盘扫描(entrypoint==2d877a93)仅此一处。
- 结论:lock 的 media 基线 = **OBS-53 未推送到 GitHub 的本地补丁态**;GitHub 上的 cedf92ca 树无法产出 `0d8aea21`。这是 7c91489 时代 lock 与远端树长期不一致的根源(档 31 sibling 建立时即已存在,档 34「media root 与 lock 失配」是该事实的另一种表现)。
- 档 37 第 4-5 步的验收目标(实算 root == `0d8aea21…`)只能由该 24S 基线树满足;恢复经正式安装器 bundle 模式完成,source-proofs.json 仍记录 cedf92ca/c2b914a2(与 lock 逐字一致),receipt 校验链(commit/tree/repo/root/manifest)全部通过。

## 第二步 恢复 media-enrichment 到锁定基线

1. 证据副本完整性(档 37 第 3 步):`F:\AIXM\wxgzh-incident-20260802\skills-asfound` 整树 1048 文件,树哈希 `a6378730b604c126acb50dafa7089ed247a71680729db91b334713f3861f8b3e` 与档 34 记录值**一致**(算法:sha256(LF 连接按 posix 路径排序的 `relpath:sha256` 行))。7 行热修留在副本内,本档未回流。
2. 构造正式结构 bundle(24S 模式,置于 `.temp` 之外,防止清理):`F:\AIXM\wxgzh\bundle-staging-37\portable-bundle`
   - `wxgzh-pipeline/` = 仓库 HEAD 正式复制规则全量镜像(558 文件,与 repo 逐文件 sha256 一致,含 `.github/workflows/ci.yml`)
   - `locked-skills/` = 24S bundle 四锁树(唯一与 lock 逐字一致的基线快照;四锁 root/manifest/count 与 lock 全部一致)
   - `skills.lock.json`/`config.example.env`/`installer/install.py`(repo HEAD 版)/`source-proofs.json`/`MANIFEST.json`(1092 文件逐文件 sha256)重建;密钥扫描 `secrets_detected=false`
3. 正式安装器(事务化):
   - dry-run:`ok=true`,四锁 `commit_match/source_tree_match/repository_match=true`
   - 实装:`ok=true`,四锁 `runtime_root_match/runtime_manifest_match/receipt_written/verify_all_ok=true`;`.install-receipts` 重写,仅 `installed_at` 更新(2026-08-01T17:44:14Z),commit/tree/root 均为锁定值
4. 验证(档 37 第 5 步):
   - 安装侧 media 实算 root=`0d8aea2169ce…` == lock `0d8aea21…` ✓
   - manifest=`172aa1b8…`、file_count=57 == lock ✓

## 第三步 同步 Pipeline 到仓库 HEAD

- 安装侧 `wxgzh-pipeline/` 已由安装器整体替换为 repo HEAD 镜像(558 文件,与 repo 逐字一致;.git 除外,符合安装语义)
- 安装侧 `wxgzh_pipeline/producers.py` 与仓库 HEAD 逐字一致 ✓;`_wechat_cover_asset` 不存在于安装树(热修已清除)✓
- 安装侧补齐了此前缺失的 `scripts/relock.py`、`scripts/upgrade_regression.py`(档 27/28/29/31/33 改动随 HEAD 同步)

## 第四步 全面复核

1. 五 skill 与权威来源一致性(档 37 第 8 步):

| skill | 实算 root | lock/期望 | 一致 |
|---|---|---|---|
| super-writer | 46a00a1b… | 46a00a1b… | ✓(50) |
| zh-human-writing | 18491b36… | 18491b36… | ✓(53) |
| media-enrichment | 0d8aea21… | 0d8aea21… | ✓(57) |
| gzh-design | 9a8cd7f5… | 9a8cd7f5… | ✓(76) |
| wxgzh-pipeline | 0f06cd75…(535) | repo HEAD 镜像逐字一致 | ✓ |

2. 安装侧 lock vs 仓库 lock(档 37 第 9 步):**逐字一致**,sha256 均为 `a9e07ef42017cff225158466213253baf1155f34a7c2f1bdaf62a87dbbc751d6`(无任何差异,包括行尾)。
3. doctor `--require-wechat`(安装副本执行):`skills_locked_ok=true`、四锁 `hash_ok=true`、`EXTERNAL_DEPENDENCY_AIHOT=INSTALLED`、`LIVE_PIPELINE_ALLOWED=true`、`wechat_config_present=true`、`FAIL_CLOSED=false`、`doctor=PASS`(全文见附件 A;仓库侧同参复跑同样 PASS)。
4. `upgrade_regression.py`:ALL PASS —— pytest PASS(显式排除清单仍为 **1 项**)、relock dry-run ×4 全「无变化」、doctor PASS、`validate_gzh_html` 跨侧比对按档 33 设计 SKIP(附跳过原因)。
5. 四锁 relock dry-run(逐条执行):super-writer / zh-human-writing / media-enrichment / gzh-design 全部「无变化」(root/manifest/count 与 lock 逐字相同)。

## 第五步 补跑档 33 沙箱演练 5d/5e/5f(沙箱 `.temp\relock37-sandbox`,演练后已彻底删除)

### 5d — required_files 移除全链(迁移场景模拟)

- 沙箱:复制 `.agents\skills` 整树 + 仓库 lock;台账/备份初始不存在;基线 dry-run 四锁全部「无变化」
- 沙箱内删除 `gzh-design/scripts/publish_wechat_draft.py`(sha 前 `bccf8538…`);dry-run:`gzh-design CHANGED(root 9a8cd7f5…→29199ee1…,manifest 变,count 76→75,required_files removals=[scripts/publish_wechat_draft.py])`,其余三锁「无变化」
- `--apply --allow-required-files-removal --skip-regression`:写前门禁按档 33 分类放行(仅目标 skill 缺失文件且 ⊆ 待移除集);备份生成;required_files 移除恰 1 项(其余条目逐字未动);三哈希字段更新;台账新增 1 条 `relock-gzh-design-20260801T174834Z-39338a7d`,`removed_required_files=[scripts/publish_wechat_draft.py]`,old/new 值与实算一致,`doctor_result=PASS`;写后 doctor PASS;再次 dry-run 报「无变化」
- 验证:沙箱 lock 中其他三 skill 条目与执行前逐字相同;备份文件与执行前 lock 字节完全相同;真实 lock 未受影响

### 5e — 三态判定(沙箱内)

- 构造 receipt:`network_mode=live`、`skill_root_sha256`=变更前旧值 `9a8cd7f5…`、skill_dir 指向沙箱 gzh-design;entrypoint/validator 指向真实安装(sha 与文件实算一致);4 个输出文件建于沙箱 run 目录(结构通过 `validate_receipt`,mism=[])
- 4a 台账在位:`ok=True | skill_root_state=SKILL_UPGRADED | upgrade_entry_ids=['relock-gzh-design-20260801T174834Z-39338a7d']`(恰为 5d 那条记录)✓
- 4b 台账移走:同一 receipt → `TAMPERED`,`mism` 含「no full upgrade chain in skills.lock.history.json」✓
- 4c 台账恢复 ✓

### 5f — 写后 doctor 失败回滚(沙箱内)

- 沙箱 gzh-design `RELEASE_NOTES.md` 首行版本改为 `v2026.07.18-hammer.1-sandbox-rollback-drill`(文件 sha `0d6ab950…` → `5394229b…`),制造「写后 doctor 版本失配」
- 执行 `--apply --skip-regression` 前快照 lock sha=`989b5cd5…`、history sha=`270f1f20…`
- 结果:写前门禁放行(仅目标 version/hash 失配);写后 doctor FAIL(`FAIL_CLOSED=true`,version_ok=false)→ 自动回滚;**退出码 4**;lock 与台账均**逐字还原**到执行前字节;备份文件保留(2 份:5d/5f 各一,备份不参与回滚删除)✓

### 收尾

- 沙箱目录已彻底删除(`relock37-sandbox` 不存在)
- 真实环境逐字未变证明:五 skill 实算 root 与安装后一致(media `0d8aea21…`);安装侧 lock sha=`a9e07ef4…`;仓库 lock 同值;真实台账 `skills.lock.history.json` 不存在;真实备份目录 `audit/upgrade-capability/lock-backups` 不存在(未产生任何真实写入)

## 风险点与说明

1. **OBS-53 未推送态**:lock 的 media 基线对应未推送到 GitHub 的本地补丁态,唯一副本为 `.temp\obs62s-build-staging\portable-bundle`(24S 暂存)。`.temp` 会被清理,该树若丢失将无法再次满足 lock 校验——建议尽快把 OBS-53 补丁正式推送/回流 media 仓库并在 lock 中如实更新,或由审核者裁决将该补丁态正式固化为 release。
2. **bundle 依赖 24S 暂存物**:本档 bundle( `bundle-staging-37` )与 24S 暂存物均保留待审;正式安装器在 bundle 模式下以 MANIFEST 绑定 source-proofs,不比对真实 git 树(设计使然,OBS-69 已记录该信任链问题,不在本档修复范围)。
3. **安装 receipts 仅 installed_at 更新**:符合 24S 既有语义;commit/tree/root/manifest 均为锁定值。
4. 档 33 演练 5d 实际移除项为 1(而非原计划的 2):真实 lock 的 gzh-design `required_files` 不含 `requirements.txt`,与档 33 已查明事实一致。
5. 恢复后 `upgrade_regression` 排除清单仍为 1 项(档 31 收敛结果),未因恢复操作扩大或缩小。

## 附件 A:doctor 完整输出(安装副本,2026-08-02)

```json
{
  "wxgzh_pipeline_version": "0.1.0-dev2-hotfix7R4",
  "project_root": "F:\\AIXM\\wxgzh",
  "skills_home": "F:\\AIXM\\wxgzh\\.agents\\skills",
  "network_mode": "live",
  "skills_locked_ok": true,
  "skills": {
    "super-writer": {"version_ok": true, "hash_ok": true, "entrypoints_ok": true, "ok": true},
    "zh-human-writing": {"version_ok": true, "hash_ok": true, "entrypoints_ok": true, "ok": true},
    "media-enrichment": {"version_ok": true, "hash_ok": true, "entrypoints_ok": true, "ok": true,
                         "current_root_sha256": "0d8aea2169cec17c4e9f95af66b6b4da3c532554a0a316fe3fb604bd0b7ab3a3"},
    "gzh-design": {"version_ok": true, "hash_ok": true, "entrypoints_ok": true, "ok": true},
    "aihot": {"EXTERNAL_DEPENDENCY_AIHOT": "INSTALLED", "live_pipeline_allowed": true, "ok": true}
  },
  "EXTERNAL_DEPENDENCY_AIHOT": "INSTALLED",
  "LIVE_PIPELINE_ALLOWED": true,
  "wechat_config_present": true,
  "wechat_credential_detail": {"WECHAT_APP_ID_nonempty": true, "WECHAT_APP_SECRET_nonempty": true},
  "wechat_required": true,
  "project_writable": true,
  "FAIL_CLOSED": false,
  "doctor": "PASS"
}
```

## 附件 B:commit 记录

- `1b2679e` — 档 37 第一步:事件 RUN 归档 + 副作用总账(push 完成)
- 本报告提交 SHA 见 git 记录(紧随本档)
