# 档 31 —— 补齐 media-enrichment sibling checkout,收敛排除清单

- 执行日期:2026-08-01
- 工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(branch `dev/0.1.0-dev2`,HEAD `1ede1d9`)
- 遵守:未修改 `.agents\skills` 任何文件(仅 pytest 运行在 `__pycache__` 下生成缓存文件,属档 30 明示例外,见第 12 步账目)、未修改真实 `skills.lock.json`、未修改被锁 skill、未修改任何已有 receipt、未实际重锁、**未修改 `build_portable_bundle.py`**、未调微信接口、未跑完整 Pipeline、未删除任何文件。

## 第一步 来源勘察

| 来源 | 版本 | input_contract.py sha256 | 带 .git |
| --- | --- | --- | --- |
| GitHub 远端 `Amer-CN/media-enrichment`:`chore/wxgzh-pipeline-dev2-integration` @ `cedf92ca45b0cdb7e010d489e9da67dd28ef6e59`;另有 `main` @ `68076ed7…` | 0.1.0-dev7-hotfix4(分支 HEAD 与 lock `full_commit_sha` 精确一致) | —(未检出时不可算) | 是(clone 后) |
| `.agents\skills\media-enrichment`(已安装) | 0.1.0-dev7-hotfix4 | `7c2ad6298b67d25c2b3961e49d73e51d9ca2550d2aaa8f01446bb175b2bec8c0` | 否 |
| `.temp\media-enrichment-dev5-20260727T0030` | 无 VERSION(构建产物目录) | 无该文件 | 否 |
| `.temp\media-enrichment-dev6-20260727T1329` | 无 VERSION | 无该文件 | 否 |
| `.temp\media-enrichment-dev6-hotfix1-20260727T1434` | 无 VERSION | 无该文件 | 否 |
| `.temp\media-enrichment-dev7-hotfix1-20260727T1457` | 无 VERSION | 无该文件 | 否 |
| `.temp\media-enrichment-oss-20260727T1547` | 0.1.0-dev7-hotfix1(≠ 锁定) | `430795ca3b52d355f887b9fac5cbcbc746a3448070d2e4a3bcaa4ce800b9d790`(≠ 已安装) | 是 |
| `.temp\media-enrichment-v0.1.0-dev*.zip`(9 个) | dev1–dev7-hotfix1,无 dev7-hotfix4 | — | 否(zip) |

**结论:唯一与锁定版本(0.1.0-dev7-hotfix4)一致的正规来源 = GitHub 远端 `Amer-CN/media-enrichment` 的 `chore/wxgzh-pipeline-dev2-integration` 分支,其 HEAD `cedf92ca…` 与 `skills.lock.json` 的 `full_commit_sha` 逐字相同。** 其余本地来源全部为旧版本或构建产物,不满足「与锁定版本一致」。

## 第二步 建立 sibling + 一致性校验

```
git clone https://github.com/Amer-CN/media-enrichment.git F:\AIXM\wxgzh\repos\media-enrichment
git checkout chore/wxgzh-pipeline-dev2-integration
git rev-parse HEAD -> cedf92ca45b0cdb7e010d489e9da67dd28ef6e59   (== lock full_commit_sha)
```

校验结果:

```
4a input_contract sha256 checkout : 7c2ad6298b67d25c2b3961e49d73e51d9ca2550d2aaa8f01446bb175b2bec8c0
4a input_contract sha256 installed: 7c2ad6298b67d25c2b3961e49d73e51d9ca2550d2aaa8f01446bb175b2bec8c0
4a MATCH: True
4b checkout VERSION: 0.1.0-dev7-hotfix4 | locked skill_version: 0.1.0-dev7-hotfix4 | MATCH: True
checkout manifest sha = 172aa1b8… = locked 172aa1b8… (57 files)  MATCH
```

**额外发现(如实记录,非验收项):** checkout 与已安装树有 2 个 runtime 文件内容不同(`scripts/run_media_enrichment.py`、`src/media_enrichment/uploader.py`)——已安装树含安装侧本地热修(如 OBS-42 续跑消费冻结清单、token 缓存、上传事件明细等;已安装版 sha 与 lock `entrypoint_sha256` 一致),远端 commit 不含;因此 checkout 的 runtime root sha(`b8257469…`)≠ lock root sha(`0d8aea21…`,对应安装树),但**文件清单(manifest)一致**。`input_contract.py`(测试实际依赖的 `validate_request`)逐字一致,4a/4b 验收通过。补丁来源在 pipeline 安装脚本中未检索到(`scripts/install.py`/`installer/` 无相关逻辑),`.temp` 各构建目录中也未找到 sha 完全相同的文件;已如实标注,不推测。

doctor 复验(第 5 步):`doctor --require-wechat` → **PASS**,`skills_locked_ok=true`,四锁 `hash_ok` 全部仍为 `true`,新增目录未影响现有环境。

## 第三步 重跑并收敛

### 6. 重跑结果(26 项:23 项 media 类 + 3 项 env 变量类)

环境:与 `_child_env()` 一致(`AGENT_SKILLS_HOME` 置空、`WXGZH_PROJECT_ROOT=F:\AIXM\wxgzh`),并设置 `WXGZH_REAL_SUPER_WRITER_ROOT=F:\AIXM\wxgzh\.agents\skills\super-writer`(hotfix7 恢复条件,validator sha 已实测与锁定值 `f2f878b1…` 一致)。

| # | 节点 | 档30(无 sibling) | 档31 | 说明 |
| --- | --- | --- | --- | --- |
| 01 | test_fake_live_six_stages | FAIL | **PASS** | |
| 02 | test_receipt_tamper | FAIL | **PASS** | |
| 03 | test_dynamic_chapter_gate | ERROR | **PASS** | |
| 04 | hotfix1 resume tamper media_manifest | FAIL | **PASS** | |
| 05 | hotfix1 resume tamper upstream_article | FAIL | **PASS** | |
| 06–12 | hotfix2 receipt_tamper a–g(7 项) | FAIL | **PASS** | |
| 13 | hotfix2 wechat_gate | FAIL | **PASS** | |
| 14–19 | hotfix3 approved_scope(6 项) | FAIL | **PASS** | |
| 21 | hotfix7 real_full_mode_long_pass | FAIL | **PASS** | 设 `WXGZH_REAL_SUPER_WRITER_ROOT` 后 |
| 22 | hotfix7 medium_overlong_policy | FAIL | **PASS** | 同上 |
| 23 | hotfix7 missing_full_mode_artifact | FAIL | **PASS** | 同上 |
| 24–27 | test_pipeline(4 项) | FAIL | **PASS** | |

**26/26 全部转 PASS,无新增失败,未暴露代码问题。**

### 7. 收敛后 `EXCLUDED_TESTS`(27 → 1)

- 26 项实测 PASS → **全部移除**。
- **仅保留 1 项**:`tests/test_hotfix1.py::test_portable_installer_preserves_pipeline_release_include`(20 号),注释按档 31 指令改写:失败根因是代码/发布工程常量问题——`scripts/build_portable_bundle.py` 写死 `EXPECTED_PIPELINE_FILE_COUNT=130`(commit `4163811` 引入后未更新),当前 release 树实际 446 个文件 → `unexpected pipeline file count: 446`;档 31 授权范围**禁止修改 `build_portable_bundle.py`**,故保留,待发布工程或后续获授权档更新常量后移除。
- 恢复条件固化:media-enrichment sibling 已恢复到 `F:\AIXM\wxgzh\repos\media-enrichment`;hotfix7 的 `WXGZH_REAL_SUPER_WRITER_ROOT` 注入已固化进 `_child_env()`(已安装 super-writer 源存在且含锁定 validator 时自动设置,不存在则不设、测试 fail-closed)。

### 8. 四组安全核心测试最终结论(17 项,全部通过)

| 组 | 项数 | 最终结论 |
| --- | --- | --- |
| test_hotfix2_receipt_tamper.py(参数化 a–g 7 项 + wechat_gate 1 项 = 8 项) | 8 | **全部 PASS**(篡改检测与 resume 阻断断言实际执行并通过) |
| test_hotfix3_approved_scope.py(6 项) | 6 | **全部 PASS**(material/source_url 范围批准断言实际执行并通过) |
| test_hotfix1.py 两项 resume tamper | 2 | **全部 PASS**(media_manifest 篡改 / upstream article 篡改 → resume 正确失效) |
| test_dev2_fake_live.py::test_receipt_tamper | 1 | **PASS**(完整六阶段后 tamper → verify 失败) |

安全核心 17 项在本档全部得到真实执行并通过;档 30 的「保护逻辑处于回归未覆盖状态」已解除。

### 9. 档 28「8 个失败 / 12 个失败」口径差异

- 档 28 报告(relock-28.md):「全量套件:本工作树 8 个失败;干净 HEAD(fa23a2a)worktree 复跑为 12 个失败」,未记录当时全量套件运行的 env、命令与失败明细。
- **重放核实**:在 `%TEMP%\r28-replay-fa23a2a` 与 `%TEMP%\r28-replay-7d3570a` 两个 worktree 以与档 30 相同环境(`AGENT_SKILLS_HOME` 空、`WXGZH_PROJECT_ROOT=F:\AIXM\wxgzh`、无 sibling、无 `WXGZH_REAL_*`)全量 `pytest tests -q`:**两个 HEAD 均为 27 个失败**(与档 30 的 27 项逐项结果完全一致)。
- **结论(口径差异原因)**:8/12 与 27 对不上,最可能的原因是档 28 报告全量套件运行时环境与本轮不同——当时大概率设置了 `WXGZH_FIXED_MEDIA_ROOT`(指向某个存在的 media-enrichment 源,如 `.temp\media-enrichment-oss-…`)和/或 `WXGZH_REAL_*`,使 23 项 media 类及 hotfix7 部分转 PASS(若 media 23 + hotfix7 3 均 PASS,失败应剩 1 项即 portable;若仅 media 23 PASS,剩 4 项;均不等于 8/12,说明当时环境介于两者之间或统计口径不同)。档 28 报告未留存命令与 env,该数字**无法复现**;本档以重放事实(27=27,与档 30 一致)为准。

## 第四步 验证

### 10. upgrade_regression.py 重跑(原样输出)

```
upgrade_regression: project_root=F:\AIXM\wxgzh
pytest: PASS (1 explicit deselects)
......................s................................................. [ 38%]
........................................................................ [ 76%]
.............................................                            [100%]
relock dry-run x4: PASS
  super-writer: status: 无变化 OK
  zh-human-writing: status: 无变化 OK
  media-enrichment: status: 无变化 OK
  gzh-design: status: 无变化 OK
doctor --require-wechat: PASS
upgrade_regression: ALL PASS
EXIT=0
```

### 11. relock dry-run(四锁)

```
status: 无变化 (x4)
dry-run: 4 skill(s) checked, 无变化 — nothing to write
EXIT=0
```

### 12. 真实环境未受污染证明

- `skills.lock.json`:工作树字节 sha = `a9e07ef4…d751d6`(与档 29/30 快照一致);与 HEAD 版本 LF 归一化后**逐字相同**(差异仅为 git `core.autocrlf=true` 的 CRLF/LF 行尾,非内容变化)。
- `.agents\skills` 树:排除全部 `__pycache__` 后的 964 个非缓存文件清单 sha = `27bcace3…`(与档 29 快照期同口径值**逐字一致**)→ 非缓存内容零变化。当前全树 1007 文件 = 964 非缓存 + 43 个 `__pycache__/*.pyc`;相对档 29 快照(982 = 964 + 18)新增 25 个 pyc,时间戳 22:36 之后,全部为档 30/31 pytest 运行副产物(四锁 runtime root sha 未变,`hash_ok` 全 true 佐证;`__pycache__` 属运行时哈希显式排除目录)。
- 本档写入仅:新建 `F:\AIXM\wxgzh\repos\media-enrichment`(git clone)、修改 `scripts/upgrade_regression.py`、`%TEMP%` 下两个重放 worktree(未删除)。未触碰 `.agents\skills`、未改真实 lock、未改被锁 skill、未删任何文件。

## 风险点

1. **sibling 与安装树 2 文件差异**:`repos\media-enrichment` 是精确锁定 commit 的正规 checkout,但含安装侧本地热修的 `run_media_enrichment.py`/`uploader.py` 未在 checkout 中;fake_live 测试只依赖 `input_contract.py`(已一致),真实管线阶段若引用 sibling 的 entrypoint/uploader 会使用旧逻辑——本档不涉及真实管线,留待后续裁决是否需要同步热修到 checkout。
2. **`EXPECTED_PIPELINE_FILE_COUNT=130` 常量陈旧**(20 号):保留在排除清单,待发布工程更新;严禁扩大清单掩盖。
3. **档 28 的 8/12 数字不可复现**:以重放事实为准(27),后续引用失败数应使用可复现口径。
4. **pytest 在 `.agents\skills` 内生成 pyc**:已证明内容零变化且属例外范围,但持续运行测试会继续累积缓存文件;如需彻底清零,需另行授权清理。
