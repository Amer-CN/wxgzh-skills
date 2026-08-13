# 档 54 — 门槛分级 + OBS-85 + 续跑至草稿 【停机】

- 日期:2026-08-03
- 状态:**停机**(结构性矛盾,按 R2「档 54 失败则整个任务终止」,档 55-59 全部不执行)
- 本档唯一写入:本报告。未改任何代码、未调微信、未创建草稿、未 relock。

---

## 一、矛盾概述

档 54 要求「改 `publish_wechat_draft.py` 预检门槛与 `validate_gzh_html.py` 分级 → 走安装器同步 → 续跑 wechat_draft 显式放行创建草稿」,
同时复核项 9 要求「四锁 hash_ok 全 true、lock `CDC8F100` 双侧未变、台账 3 条、doctor PASS、安装侧与 repo HEAD 逐字一致」。

这两个文件属于**被锁 skill gzh-design**(hammer.3, `acc7745a`, lock root `b517aec6…`),改动必然改变锁定 root;
而不改它们,被锁发布脚本内部 `WARNING=0` 硬门槛(L413-416)无法被外部参数绕过——放行与创建草稿不可达。
**授权与复核项在现有锁定架构下不可兼得。**

## 二、证据链(全部实测)

1. **两个文件在被锁树 hash 范围内**:`compute_runtime_manifest_sha(.agents/skills/gzh-design)` = 76 文件,含
   `scripts/publish_wechat_draft.py`、`scripts/validate_gzh_html.py`、`scripts/render_article.py`。
   `skill_discovery.py` EXCLUDE 集(L23-26)为 `__pycache__/.git/.pytest_cache/.github/tests/node_modules/.idea/.vscode/.install-receipts`
   + `WXGZH_PIPELINE_INTEGRATION.md/.gitignore/.gitattributes` + `*.pyc` —— **不含 scripts**,改动即改 root。
2. **入口硬编码指向被锁脚本**:`execmodel.py` LIVE_ENTRY(L117-119)`wechat_draft → gzh-design/scripts/publish_wechat_draft.py`,无环境变量/配置覆盖机制(rg 全库无 `WXGZH_*_ENTRY`)。
3. **被锁脚本无放行/跳过参数**:`publish_wechat_draft.py` argparse(L519-531)仅 `--html/--title/--expect-sha256/--thumb-media-id/--cover/--audit-dir/--dry-run`;`preflight_html` L413-416 `if errors or warnings: sys.exit(1)` 无条件阻断;`--audit-dir` 审计模式在 preflight **之后**运行,不构成绕过(档 53 已确认)。
4. **安装器会还原被锁树**:`install.py` 四锁从锁定源(locked-skills/bundle 或 git 锁定 commit)拷贝后事务切换(L307-327),安装侧任何手工改动会被锁定版本覆盖——「改被锁侧 + 走安装器同步」在时序上自相矛盾(同步即还原)。
5. **cross-side 防漂移守卫**:`upgrade_regression.py` L108-131——若 Pipeline 侧出现 `scripts/validate_gzh_html.py`,必须与安装侧 gzh-design 逐字一致,否则 FAIL(现为 SKIP,P2 未落地)。在 Pipeline 侧建分级副本会让该检查从 SKIP 变 FAIL。

## 三、路径矩阵(全部不可行)

| 路径 | 失败点 |
|---|---|
| A. 改被锁 gzh-design 两脚本,不 relock | 安装侧 root 失配 → doctor FAIL、hash_ok false;安装器同步即还原;复核项 9 不满足 |
| B. 改被锁 gzh-design + 升版 + relock | 台账变 4 条、lock 变 → 复核项 9(台账 3 条、lock CDC8F100 未变)不满足;且与档 57「第四次真实 relock」定义错位(档 57 为 media full_commit_sha,档 54 若 relock 则计数错乱) |
| C. Pipeline 侧建分级副本,不改入口 | 副本不参与执行(LIVE_ENTRY 硬编码被锁脚本)→ 放行无效 → 第 6 项创建草稿不可达 |
| D. Pipeline 侧建副本 + 入口迁移(改 execmodel/SKILL.md/contracts) | 属 P2「gzh-design split」级架构变更,档 54 授权未覆盖;且迁移后 cross-side 守卫因两侧不一致 FAIL,除非同时改被锁侧(回到 B) |
| E. 给被锁脚本传参跳过预检 | 被锁脚本无放行/跳过参数,无法从外部注入(证据 3) |

## 四、为何不选择「部分执行」

- R3 禁止「调整实现去凑预期」:不能只做分级改造而跳过创建草稿,也不能只建副本假装放行生效。
- R6「未覆盖情况一律取更保守做法」:入口迁移(D)属于未授权架构变更,relock(B)与复核项直接冲突,均不可自行裁量。
- 档 54 为最高优先档且 R2 明文:档 54 失败 → 整个任务终止。故档 55-59 一律不执行。

## 五、待裁决清单(按优先级)

1. **P0 — 档 54 的执行形态**:需裁决以下之一:
   a. 授权「改被锁 gzh-design + 升版 + 真实 relock」,并同步修订复核项(台账 4 条、lock 新 sha),档 57 的 relock 计数顺延;
   b. 授权「P2 gzh-design split」:发布/校验脚本迁入 Pipeline 侧为权威,被锁侧按既定流程同步,并同步修订 cross-side 守卫语义;
   c. 接受「改冻结文章引号全角化」路径(解除档 52/53 禁令),不触碰门槛;
   d. 维持 WARNING=0 现状,放弃本 RUN 草稿,另开新 RUN 验证。
2. **P1 — OBS-85 登记**:「HTML 解析中断归为 WARN」的缺陷判定成立(validate_gzh_html.py L213),无论档 54 采用何种形态都应升 ERROR;本档未登记台账(停机),待裁决后随执行档一并登记。
3. **P1 — 档 55(OBS-82 discover 预校验)**与**档 56/57/58/59** 全部挂起,待档 54 形态裁决后重排。

## 六、基线复核(停机时环境)

- 双侧 lock sha `CDC8F100C2A1D77F9FF87FF1D030C5871AB910B1ECB95376541F2BC713EF1186`(未变)
- 台账 3 条(`59d63817`/`843f9372`/`1afb45bd`);四锁 root 与档 52 基线一致(未变)
- pipeline HEAD `7e710b7`(档 53);gzh-design fix 分支 `acc7745`(hammer.3)
- 微信副作用:0(本档零调用);草稿箱仍 1 份
- 本档未写任何生产代码、未跑安装器、未 relock、未改任何被锁文件
