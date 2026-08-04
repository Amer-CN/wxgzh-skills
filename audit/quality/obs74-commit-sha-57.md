# 档 57 — OBS-74 尾巴 full_commit_sha(第五次真实 relock)

- 日期:2026-08-04
- 状态:**通过**。media-enrichment full_commit_sha 对齐远端 `restore/local-patches-obs42-53`,OBS-74 完全结案。
- 说明:按档 54R 第 22 项,本档为**第五次真实 relock --apply**(台账第五条);未改 media-enrichment 代码内容。

---

## 19. 远端见证前置(实测通过)

- 目标 commit `2595e01465399eb34a10a56b190399039578da9e` 在 `restore/local-patches-obs42-53` 远端可达(`git fetch origin` 后 `rev-parse origin/restore/local-patches-obs42-53` = 2595e014)
- source-tree 工作树:`repos/media-enrichment-39r-build`(HEAD=2595e014,remote=`https://github.com/Amer-CN/media-enrichment.git`)
- relock dry-run:远端见证 **PASS (a/b/c)**

## 20. 完整原子链 --apply

```
ledger: relock-media-enrichment-20260804T050125Z-29b8f728 (media-enrichment)
installer: PASS (source-tree install)
doctor: PASS (post-relock)
media-enrichment: entrypoint smoke PASS (CLI subprocess, production path)
```
- **lock sha**:`8FCBC203…` → **`0FDF2ECECD1FCD9A8A4957F004D7C2EDA8D99DF8C69C9AC3ED9D6730C559421E`**(双侧一致)
- **台账第五条**:`relock-media-enrichment-20260804T050125Z-29b8f728`
- 字段变化:
  - `full_commit_sha`:`cedf92ca` → **`2595e014`**(CHANGED)
  - `source_tree_sha`:`c2b914a2…` → **`6ba0ba41…`**(CHANGED)
  - `branch`:`chore/wxgzh-pipeline-dev2-integration` → `restore/local-patches-obs42-53`(CHANGED)
  - `skill_root_sha256`:`0d8aea21…`(不变,代码内容未动)
  - `runtime_manifest_sha256`:`172aa1b8…`(不变)/ count 57(不变)/ entrypoint/validator sha(不变)/ version `0.1.0-dev7-hotfix4`(不变)

## 21. 入口冒烟

- **已执行**(档 56 已备样本):`media-enrichment: entrypoint smoke PASS (CLI subprocess, production path)`——档 56 的 smoke-samples 在第五次 relock 自动生效。

## 22. 复核

- **upgrade_regression:ALL PASS**(pytest PASS 含 obs80 6 项,1 项显式排除;四锁 relock dry-run 全「无变化」;doctor PASS;cross-side SKIP)
- 双侧 doctor --require-wechat:PASS,四锁 hash_ok 全 true,FAIL_CLOSED=false
- 双侧 lock 一致 = `0FDF2ECE…`;台账 **5 条**;安装侧与 repo HEAD **606 文件逐字一致(0 差异)**
- media 安装侧 root/manifest 实测 = `0d8aea21…`/`172aa1b8…`(与 lock 逐字一致)
- 备注:media relock 后 observability 基线随 lock 同步(`8FCBC203 → 0FDF2ECE`,档 54R 同款流程);obs80 测试路径推导修正(安装侧 `_installed` 用 `WXGZH_PROJECT_ROOT`)

## 23. OBS-74 结案确认

- **完全结案**。结案依据:
  1. 代码已回流(档 39R):四轮补丁(OBS-42/43、44-46、47、53)在 `restore/local-patches-obs42-53` @ 2595e014,远端可达
  2. lock 的 `full_commit_sha`/`source_tree_sha` 现与**同一份远端代码**对齐(此前 full_commit_sha 指向无补丁的 cedf92ca 而 root 是补丁树——内部不一致,档 39R 登记「待修」)
  3. root/manifest/count 不变:证明 lock 语义未漂移,仅 commit 标识字段归位
- 残留:无(lock 内部不一致已消除)

## 微信副作用

- 0(本档为 relock 档,未调微信、未创建草稿、未发布)
