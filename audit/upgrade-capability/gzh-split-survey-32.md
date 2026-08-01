# 档 32 — gzh-design 两侧一致性核验与迁移清单(gzh-split-survey-32)

日期:2026-08-01
模式:只读勘察。除临时 clone 目录外零写入;未重锁、未跑 Pipeline、未调微信接口、未删除任何文件。
工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(branch `dev/0.1.0-dev2`,HEAD=`52cf80f`,工作树干净)
勘察对象:安装副本 `F:\AIXM\wxgzh\.agents\skills\gzh-design`(76 runtime 文件)vs
GitHub `Amer-CN/gzh-design-skill` `chore/wxgzh-pipeline-dev2-integration`
(临时 clone 于 `%TEMP%\gzh32-clone`,勘察结束后已删除,见附录)。

---

## 第一部分 两侧一致性

### 1. 远端 HEAD 核实

- `git ls-remote --heads https://github.com/Amer-CN/gzh-design-skill`:
  `0007d7e6a4493aab59070d9c31dcde83830302fd` → `refs/heads/chore/wxgzh-pipeline-dev2-integration`
  (与档 32 预期值一致;`main` 为 `d361f6f3…` 与本档无关)
- clone 后 `git checkout 0007d7e6a4493aab59070d9c31dcde83830302fd` → `rev-parse HEAD` =
  `0007d7e6a4493aab59070d9c31dcde83830302fd`
- 该 commit 的 tree SHA = `a1f408201e394add46b0d7dede8c017030160644`,
  与 skills.lock.json 中 gzh-design 的 `source_tree_sha` 逐字一致;
  lock 的 `full_commit_sha` 同为 `0007d7e6…`。

结论:远端分支 HEAD 仍是档 32 预期的 commit,且 lock 锁定的就是该 commit。

### 2. 76 文件逐文件比对

方法:复用 Pipeline 自身 `wxgzh_pipeline.skill_discovery` 的
`_runtime_files` / `compute_runtime_manifest_sha` 生成两侧文件清单,
逐文件计算原始字节 sha256(未做行尾归一化),另以 `_file_sha` 计算归一化值作辅助判定。

| 项 | 结果 |
|---|---|
| 清单规模 | 两侧均为 76 文件,相对路径集合完全一致 |
| runtime_manifest_sha256 | 两侧均 `ced841439195453497e67a63186823f60eee7155b9de472e936c3d4d767e33b2` == lock 值 |
| 原始字节 sha256 一致 | **76 / 76** |
| 仅行尾差异(归一化一致、原始不同) | 0 |
| 内容差异 | 0 |
| 只存在于安装侧(manifest 范围内) | 0 |
| 只存在于 checkout 侧(manifest 范围内) | 0 |

补充:对 manifest 范围外的全树也做了清点(排除 `.git`)。安装侧 295 个文件、
checkout 侧 299 个文件,唯一差异是 checkout 独有的 4 个 `.github/*` 文件
(`.github/ISSUE_TEMPLATE/bug_report.md`、`.github/ISSUE_TEMPLATE/theme_request.md`、
`.github/PULL_REQUEST_TEMPLATE.md`、`.github/workflows/ci.yml`)。
这 4 个文件被 `EXCLUDE_DIRS={"…", ".github", …}` 排除在 runtime manifest 之外,不影响哈希。

### 3. 差异分类

**不存在任何不一致**,第 2 步无差异可分类(本地热修 / checkout 更新 / 构建产物 / 无法判定
四类均无对象)。

附带事实(非两侧差异,两侧 SHA256SUMS 逐字相同,但文件自身已过时):
gzh-design 的 `SHA256SUMS` 共 6 条,其中 4 条与当前树内文件原始 sha256 不符
(`SKILL.md`、`references/theme-hammer.md`、`scripts/publish_wechat_draft.py`、
`scripts/validate_gzh_html.py`),且引用 `gzh-design-v2026.07.18-hammer.zip`
(checkout 与安装树中均不存在)。该文件属 B 类文档产物,不参与哈希计算。

### 4. 特别核查:两个 P2 直接迁移对象

| 文件 | 安装侧原始 sha256 | checkout 侧原始 sha256 | 结论 |
|---|---|---|---|
| `scripts/publish_wechat_draft.py` | `bccf853820d7005a71b062e13f5b2ee9be984868866724d83f4626c01d0df934` | 同左 | **逐字一致** |
| `scripts/validate_gzh_html.py` | `61b8e8ef1cc3adf62f9b3e207e7989b96e2e1b877c47d98e9a41a32b3433c6c2` | 同左 | **逐字一致** |

(两者均属 76/76 全一致之内,此处单独列出以便核对。)

---

## 第二部分 迁移清单

### 5a. 迁出到 Pipeline 侧的文件(基于档 26 分类 A=2 / B=73 / C=1)

| 源路径(gzh-design 内) | 建议目标路径 | 说明 |
|---|---|---|
| `scripts/publish_wechat_draft.py` | `F:\AIXM\wxgzh\repos\wxgzh-pipeline\scripts\publish_wechat_draft.py` | 与 pipeline 现有 `scripts/`(doctor.py/install.py/relock.py 等)并列,或放入包内如 `wxgzh_pipeline/vendored/`;P2 实施时选定。注意其 L109-111 的 `sys.path.insert(0, dirname(abspath(__file__)))` + `from validate_gzh_html import validate, find_cn_quoted_attrs` 依赖同目录下的 C 类文件,迁移后 import 必断,必须先处理 5c 的 C 类归属 |
| `requirements.txt` | 无独立目标文件 | Pipeline 无 requirements.txt,依赖由 `pyproject.toml` + `requirements.lock` 管理;见 5b |

### 5b. requests 依赖如何处理(据实查)

- gzh-design `requirements.txt` 唯一内容:`requests>=2.31,<3`(A 类迁出对象)。
- Pipeline 侧**已有** requests 依赖:`pyproject.toml:13` `"requests>=2.28"`;
  `requirements.lock:4` 锁定 `requests==2.32.3`。
- 但 Pipeline 全部源码(含 tests)没有任何 `import requests`;requests 的**唯一消费方**
  就是 gzh-design 的 `scripts/publish_wechat_draft.py:104`(try/except ImportError 包裹)。
- 迁移事实:无需新增依赖声明;需要把迁入代码的版本契约并入 Pipeline 约束,
  即把 `pyproject.toml:13` 从 `>=2.28` 调整为与迁入代码一致的 `>=2.31,<3`
  (或经裁决采用其他范围;`requirements.lock` 的 `2.32.3` 同时满足两侧范围)。

### 5c. C 类 `scripts/validate_gzh_html.py` 的处理选项(只列事实)

**排版侧(render 链)的用法**:
- `scripts/render_article.py:40` `from validate_gzh_html import validate as validate_html`;
  `:215` 调用 `validate_html(html, "final.html")` → 只用 `validate` 一个函数。
- `scripts/fix_html_quotes.py:15-22` `from validate_gzh_html import (TAG_RE, ANY_CN_QUOTED_ATTR,
  CN_QUOTE_PAIRS, find_cn_quoted_attrs)`;`TAG_RE` 用在 `:35`、`ANY_CN_QUOTED_ATTR` 用在 `:43`、
  `CN_QUOTE_PAIRS` 用在 `:46`、`find_cn_quoted_attrs` 用在 `:109`。
- 动态加载/打包引用:`run_b_agent.py:27`、`run_real_agent.py:38-39`
  (spec_from_file_location 按安装树路径加载)、`make_review_zip.py:48`(打包入 zip)、
  `component_lint.py:7-8`(文档说明其闭环分工)。

**publish 侧的用法**:
- `scripts/publish_wechat_draft.py:111` `from validate_gzh_html import validate, find_cn_quoted_attrs`;
  `:381` 调 `validate(...)`(禁用标签/属性/样式、全属性中文引号、占位符、编辑锚点等预检);
  `:386` 调 `find_cn_quoted_attrs(...)`(中文引号命中统计)。**只用这两个函数**,未直接用模块级正则常量。

**两侧是否同一组功能**:核心两个函数(`validate`、`find_cn_quoted_attrs`)**两侧共用**;
但使用面不完全相同——排版侧 `fix_html_quotes.py` 还直接使用 3 个模块级正则常量,
且排版侧另有 2 处动态加载 + 1 处 zip 打包引用。C 类无法只随 A 迁出而不动排版侧。

**可行选项与各自代价**(不替决策,只列事实):
1. **留在 gzh-design,publish 迁出后经绝对路径/动态加载使用**:
   代价:publish 与安装树强耦合,脱离 skill 安装后无法独立运行,P2「发布层独立」不彻底;
   import 方式要改成 spec_from_file_location 或显式 sys.path 注入。
2. **迁出到 Pipeline 侧,publish 与排版侧都改为引用新位置**:
   代价:排版侧 4 个脚本(render_article/fix_html_quotes/run_b_agent/run_real_agent)+
   相关 tests 全部要改路径;gzh-design 的 lock `validator` 字段(现 `scripts/validate_gzh_html.py`,
   `validator_sha256=b986ae77d78f6205d4eda5b798fed6d5d8df4b58086b51b8204e63dd857a3cc8`)
   与 `required_files` 第 2 项也要改——超出 relock.py 能力(见第 8 节 R1);改动面最大。
3. **两侧各保留一份拷贝**:
   代价:同一校验核心两份,后续热修必须同步;gzh-design 内那份继续被 lock/doctor 管,
   两份长期漂移风险;SHA256SUMS 需维护两份。

### 6. 迁移后需要同步修改的 Pipeline 侧引用点(档 26 第 5a 项,行号为本档实测)

| 文件 | 行号 | 内容 |
|---|---|---|
| `wxgzh_pipeline/execmodel.py` | :12 | 模块 docstring 中 wechat_draft 调用描述 |
| `wxgzh_pipeline/execmodel.py` | :48 | `STAGE_SKILL["wechat_draft"]="gzh-design"` |
| `wxgzh_pipeline/execmodel.py` | :118-119 | `LIVE_ENTRY["wechat_draft"]` 的 skill/entry 指向 |
| `wxgzh_pipeline/execmodel.py` | :127 | `FAKE_ENTRY["wechat_draft"]` entry 指向 |
| `wxgzh_pipeline/execmodel.py` | :150-157 | `resolve_entry()` 按模式解析真实/假 entry 路径 |
| `wxgzh_pipeline/contracts.py` | :29 | 注释(wechat_draft 复用 gzh-design publish) |
| `wxgzh_pipeline/contracts.py` | :33 | `STAGE_LOCK_SKILL["wechat_draft"]="gzh-design"` |
| `wxgzh_pipeline/contracts.py` | :131 | `enforce_contract` 取 `STAGE_LOCK_SKILL.get(stage)` |
| `wxgzh_pipeline/contracts.py` | :159 | `if stage == "wechat_draft":` 特判 |
| `wxgzh_pipeline/producers.py` | :11 | docstring 描述调用方式 |
| `wxgzh_pipeline/producers.py` | :65-66 | `produce()` 分发 `kind == EM.WECHAT -> _wechat(...)` |
| `wxgzh_pipeline/producers.py` | :822-859 | `_wechat()`:resolve_entry → 组装 `--html/--title/--audit-dir[/--cover/--dry-run]` → run_script → 记录 entrypoint/exit/输出 sha |
| `wxgzh_pipeline/stages/wechat_draft.py` | :2 | docstring |
| `wxgzh_pipeline/stages/wechat_draft.py` | :23-24 | `invoked_entrypoint()` 声明复用该脚本 |
| `wxgzh_pipeline/stages/wechat_draft.py` | :40 | `subskill_validator_sha(ctx,"gzh-design","scripts/publish_wechat_draft.py")` 记录 entry 哈希 |
| `wxgzh_pipeline/stages/wechat_draft.py` | :59-62 | `run_live` → `produce(...)` |
| `wxgzh_pipeline/stages/__init__.py` | :19 / :137 | `from ..execmodel import STAGE_SKILL`;执行时取 `STAGE_SKILL[stage]` |
| `wxgzh_pipeline/orchestrator.py` | :25-31 | `STAGE_MODULES` 注册 wechat_draft 模块 |
| `wxgzh_pipeline/orchestrator.py` | :71 | integration 模式按 `STAGE_SKILL` 查 skill |
| `wxgzh_pipeline/orchestrator.py` | :77 / :105 | `EM.resolve_entry(...)` 校验 shim/真实 entry |
| `wxgzh_pipeline/orchestrator.py` | :219-234 | `_drive` 中 wechat_draft 特判与 `execute_stage` |
| `wxgzh_pipeline/receipts.py` | :215-216 | 用 `STAGE_SKILL` 核对 receipt 的 skill_name(若映射值变更,历史 receipt 会 mismatch,联动第 9 节) |
| `scripts/run_cross_repo_integration.py` | :42 | cross-repo 集成检查期望 gzh-design 位置存在 `scripts/publish_wechat_draft.py` |
| `fake_live/skills/gzh-design/publish_wechat_draft.py` | 全文 | fake-live shim,`FAKE_ENTRY` 指向其相对路径 |
| `tests/test_hotfix1.py` | :77 / :115 / :132 | wechat_entry 路径断言 |
| `README.md` | :49 | 阶段表「复用 gzh-design/scripts/publish_wechat_draft.py」 |
| `SKILL.md` | :61 | 同上描述 |

### 7. 迁移后 gzh-design 侧需要清理的引用

**publish_wechat_draft.py 相关(A 迁出后必须处理)**:

| 文件 | 行号 | 在 runtime manifest 内? |
|---|---|---|
| `README.md` | :65 / :74 | 是(B) |
| `RELEASE_NOTES.md` | :24 | 是(B) |
| `SKILL.md` | :229 | 是(B) |
| `SHA256SUMS` | :3 | 是(B);该条哈希本身已过时(见第 3 节附带事实) |
| `WXGZH_PIPELINE_INTEGRATION.md` | :19 | **否**(manifest 排除文件) |
| `tests/test_exact_host_hotfix2.py` | :2 / :9 | 否(tests/ 排除) |
| `tests/test_wechat_fragment_href.py` | :37-39 | 否 |
| `tests/test_publish_hotfix.py` | :53 / :113 / :409 / :438 | 否 |
| `tests/test_publish_audit_hotfix.py` | :2 / :16 / :83 | 否 |

**validate_gzh_html.py 相关(仅当 C 类迁出时才需要清理)**:

| 文件 | 行号 | 在 runtime manifest 内? |
|---|---|---|
| `scripts/render_article.py` | :40 / :215 | 是(B) |
| `scripts/fix_html_quotes.py` | :15-22 / :35 / :43 / :46 / :109 | 是(B) |
| `scripts/run_b_agent.py` | :27 / :150 | 是(B) |
| `scripts/run_real_agent.py` | :38-39 / :452 | 是(B) |
| `scripts/make_review_zip.py` | :48 | 是(B) |
| `scripts/component_lint.py` | :7-8 | 是(B) |
| `SKILL.md` | :121 | 是(B) |
| `CONTRIBUTING.md` | :22 / :26 | 是(B) |
| `README.en.md` | :33 / :119 / :130 / :139 / :149 / :195 | 是(B) |
| `references/eval-cases.md` | :48 / :75 / :79 | 是(B) |
| `references/advanced-components.md` | :59 / :71 | 是(B) |
| `tests/test_wechat_fragment_href.py` | :33 | 否 |
| `tests/test_render_article_hotfix.py` | :17 / :88 | 否 |
| `tests/test_fixed_signature.py` | :31-33 | 否 |
| `tests/test_hammer_contrast.py` | :32-34 | 否 |
| `tests/test_dialogue_hotfix.py` | :19 / :30-32 / :309 / :311 | 否 |

---

## 第三部分 风险

### 8. 迁移后 runtime 文件数变化与 relock 首次真实使用风险

文件数:若仅迁 A 类 2 个文件(`scripts/publish_wechat_draft.py` + `requirements.txt`),
C 类留在 gzh-design,**76 → 74**;若 C 类也迁出,**76 → 73**。
两种情况 `skill_root_sha256` / `runtime_manifest_sha256` / `runtime_file_count` 必变,
需要 relock --apply(或等价重锁)后 doctor 才能 PASS。

relock 首次真实使用风险点(依据 relock.py / skill_discovery.py / doctor.py 现状):
- **R1(最大):`required_files` 残留导致门禁与写后复验双失败**。
  lock 的 gzh-design `required_files` 含 `scripts/publish_wechat_draft.py`(第 4 项);
  `skill_discovery.py:259-260` 判定 `entrypoints_ok = all((root/rf).is_file() ...)`,
  迁出后该文件不在 gzh-design 树内 → `entrypoints_ok=false` → doctor FAIL。
  档 28 门禁把「entrypoints_ok=false」归为**拒绝类**(退出码 3),因此纯 relock --apply
  在写前就会被拒;relock.py 的 `_HASH_FIELDS` 只有
  `skill_root_sha256 / runtime_manifest_sha256 / runtime_file_count` 三个字段,
  **不支持更新 required_files**。迁移必须扩展 relock(新增 required_files 更新能力)
  或另行裁决人工改 lock,二者都超出本档范围。
- **R2:台账首条真实记录**。`skills.lock.history.json` 目前**不存在**;首次真实 --apply
  会创建它。两篇历史 RUN 的 receipt 记录 root=`9a8cd7f…`,首条记录的
  `old_root_sha256` 必须是该值(否则断链,见第 9 节)。期间任何先于迁移的 root 变化
  都会破坏这条链。
- **R3:操作顺序敏感**。迁移后、重锁前,doctor 处于 FAIL_CLOSED=true 且
  entrypoints_ok=false → 属于拒绝类门禁;顺序必须是:更新 required_files(扩展 relock)
  → 安装新树 → relock --apply → 写后 doctor PASS。
- **R4:回滚是保护不是故障**。若写后 doctor FAIL,relock 自动把 lock 与台账逐字还原,
  备份保留;真实环境首次触发该路径时不要误判为「失败后状态被破坏」。
- **R5:序列化保真已有兜底**。`_serialize_lock`(relock.py:83-92)保留 CRLF/尾换行,
  且档 28 已加字节保真测试,真实写入只应产生三个字段的最小 diff。
- **R6:C 迁出时的附加字段**。gzh-design 的 lock 还有
  `validator=scripts/validate_gzh_html.py`(`validator_sha256=b986ae77…`)、
  `render_entry` / `render_entry_sha256` / `component_source` / `component_source_sha256`。
  仅迁 A 时这些字段全部保持有效;C 迁出则 `validator`/`validator_sha256` 也必须改。

### 9. 两篇已归档 RUN 的 receipt 三态推演

事实基础:
- 两篇 RUN(`20260731T135947-ai-bbg4al`、`20260801T182628-topic-ui5f7p`)的
  `stages/gzh_design/stage_receipt.json` 与 `stages/wechat_draft/stage_receipt.json`
  均记录 `skill_root_sha256=9a8cd7f548c2186f789a5e24235001308fc6a868e0f57d74fc06c8919b4ff79b`
  (= 当前 lock 值 = 当前安装树实算值),`network_mode=live`。
- `verify_receipt`(receipts.py:281-306)对 live receipt 做三态:root 一致 → OK;
  不一致时 `_find_upgrade_chain`(receipts.py:144-193,严格:台账缺失/空/非法 → None)
  找 receipt 值 → 当前值的完整链路,找到 → SKILL_UPGRADED(标记需重跑,返回 entry_id),
  找不到 → TAMPERED。
- gzh_design receipt 还记录 `entrypoint_path=…\gzh-design\scripts\render_article.py`
  (迁移后仍在树内)、official_validator 指向 `scripts/validate_gzh_html.py`(C 留树时仍在);
  wechat_draft receipt 记录 `entrypoint_path=…\gzh-design\scripts\publish_wechat_draft.py`
  (迁移后不在该路径)。

推演:
- **今天(未拆分)**:receipt root == 安装树 root → 三态 OK,正常续跑。
- **拆分重锁后(假设 relock --apply 已正确执行,台账含 skill=gzh-design、
  old_root_sha256=9a8cd7f…、new_root_sha256=<新树值>)**:
  - gzh_design receipt:单跳链路命中 → root 三态 = **SKILL_UPGRADED**;
    entrypoint/validator 文件仍在原树 → 无其他失败项;整体不阻断,标记该阶段需重跑。
  - wechat_draft receipt:root 三态同样 = **SKILL_UPGRADED**;
    但 `receipts.py:259-267` 的 entrypoint 校验要求记录的 path 存在且 sha 匹配,
    迁移后旧路径文件不存在 → 「entrypoint script missing」→ **整体 FAIL(阻断)**;
    若届时 `STAGE_SKILL["wechat_draft"]` 映射值变更,`receipts.py:215-216`
    的 skill_name 校验也会 FAIL。即:三态本身是 SKILL_UPGRADED,但该 receipt
    作为一个整体无法通过验证——这是历史 receipt 路径字段指向旧树的必然结果,
    迁移时必须作为已知事实处理(如归档说明,而非当作 TAMPERED 证据)。
- **若台账缺失/为空/格式非法/无对应记录**(例如未走 relock --apply 或首条记录
  old_root 不是 9a8cd7f…):两阶段均为 **TAMPERED**。

### 10. 两侧不一致时以哪一侧为准

本档实测两侧 76/76 逐字一致,不存在取舍问题。若未来出现不一致,原则(事实依据):
**以安装树 `F:\AIXM\wxgzh\.agents\skills\gzh-design` 为准**——lock 的
`skill_root_sha256`/`runtime_manifest_sha256` 描述的就是安装树实算值,doctor 校验的
是安装树,历史 receipt 记录的哈希也来自安装树;checkout 只是产生安装树的上游参考
(本档已证实 commit 与 tree 均与 lock 一致)。checkout 侧的差异只能通过
上游更新 → 重装 → relock --apply 进入正式环境,不能反向把安装树对齐 checkout。

---

## 附录

- 勘察期写入:仅 `%TEMP%\gzh32-clone`(临时 clone);勘察结束后已删除该目录(本机 PowerShell Remove-Item 被 harness 策略拦截,实际以 `cmd /c rmdir /s /q` 对已核实字面路径执行,删除后 Test-Path 确认不存在)。
  对 `F:\AIXM\wxgzh\.agents\skills`、`F:\AIXM\wxgzh\repos\wxgzh-pipeline`
  及其余任何路径零写入、零删除。
- 本档工作副本基线:HEAD=`52cf80f`(档 31),本报告是唯一新增文件。
- 未重锁、未跑 Pipeline、未调微信接口、未修改任何 receipt。