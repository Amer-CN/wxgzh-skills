# OBS-356 —— 77V 版本新鲜度检查内建验收报告（字节级落盘）

- 档号：77V（版本新鲜度检查内建：skill 自带「我是不是最新」第 0 步）。
- 授权：无变更（仅 pipeline 子树，无锁条目；RELOCK/GZH 双键维持 0）。
- feat 提交：见本报告尾部基线链（本轮 docs 前最后一颗）。
- 设计依据：用户 2026-09-02 裁决——更新检查不绑定任何 agent 记忆（agent 用完即弃），必须内建于 skill 本身；发版侧打 tag（归位微档模板已加）+ 本档消费侧检查 = 配套两半。

## 1. 任务 0 侦察结论

- 入口链：`cli.py:main` → `parse_command` → `Orchestrator.run()`（`orchestrator.py:187`），run() 首行 `self.doctor()`（FAIL_CLOSED 挂点）→ 第 0 步插入点=doctor 之后、RUN 创建之前。
- 指令面：第 0 步是编排器行为非 agent 阶段行为 → 落 SKILL.md「Agent 执行约定」+ frontmatter permissions，producers.py 不动。
- tag 现状：本地/远端均零 tag（首个 tag 本轮补打）。
- 装机侧 `.agents/skills` 无 .git（纯拷贝）→ version_check 不做本地 git 操作，本地版本面来自锁/VERSION/history，远端面来自 ls-remote。
- 离线形态：ls-remote rc≠0 → unknown；无 tag 可识别 → unknown（不猜）。

## 2. 实现（9 文件）

- `scripts/version_check.py`（新增，纯 stdlib）：本地版本面（四锁技能 skill_version+pipeline VERSION+锁 sha256+基线日期三级来源 history→release_date→unknown）；`git ls-remote --tags <ORIGIN>`（固定 URL 常量）取最新 v 前缀 tag（日期主序、同日字典序最大）；比对仅日期级；输出单行 JSON `{status, current, latest, detail}`；恒 exit 0。
- `orchestrator.py`：`run()` 加 `allow_stale`；doctor 通过后、RUN 创建前 `_version_check_step()`（列表式 subprocess、timeout 20、失败降级 unknown）；current 静默 / behind → 返回 `STALE_VERSION`（RUN 不创建）+ hint「更新（拉取+installer+SECURITY.md §8/§9 基线对账）或 --allow-stale 继续」/ unknown 与 behind+allow_stale → `st.version_check` 留痕（state 落盘+run 结果附键，overridden=true）。`resume()` 不检查（续发优先跑完断点，不新增停机点）。
- `state.py`：`PipelineState.version_check: dict | None = None`（旧 state 反序列化兼容）。
- `cli.py`：`--allow-stale` 旗标，fabu 透传。
- `SKILL.md`：执行约定第 0 步（含 resume 不检查说明），后续步骤重排 1→2…6→7；frontmatter network 追加「git ls-remote 查询 origin tags（version_check，无凭据传输）」、subprocess 合并追加；正文网络访问条同步。
- `tests/test_hf77v_version_check.py`（新增，7 条）：三形态 mock（current/behind/unknown）+编排器三形态（behind→STALE_VERSION 且 RUN 目录不创建；allow_stale→COMPLETE+overridden 留痕；unknown→COMPLETE+留痕）+旧 state 兼容。
- `VERSION`：hotfix9R25→9R26（previous_version 同步）。
- `audit/quality/obs-ledger.md`：OBS-356 落账+口径 87。
- 仓库根 `README.md`：五技能表上方版本速览行（含发版打 tag 约定与第 0 步自动检查说明）。
- `tests/test_hf76r.py`：obs304 计数随档 237→238、119–356（主智能体，77Q 起既定模式）。

## 3. 三形态验收实证（原文）

形态①真实远端（无 tag→unknown 留痕继续）：

```json
{"status": "unknown", "current": {"skills": {"super-writer": "0.4.18-rc1", "zh-human-writing": "0.1.14", "media-enrichment": "0.1.0-dev30", "gzh-design": "v2026.09.02-hammer.22"}, "pipeline_version": "0.1.0-dev2-hotfix9R26", "lock_sha256": "217a5c37…", "baseline_date": "2026-09-02", "baseline_source": "skills.lock.history.json"}, "latest": null, "detail": "远端无 v 前缀 tag（vYYYY.MM.DD-<suffix>）可识别：https://github.com/Amer-CN/wxgzh-skills.git"} rc=0
```

形态②离线（ls-remote rc=128→unknown）：

```json
{"status": "unknown", …, "detail": "git ls-remote 失败 rc=128: fatal: unable to access 'https://127.0.0.1:1/nonexistent.git/': Failed to connect…"} rc=0
```

形态③current/behind/allow-stale/兼容：`pytest tests/test_hf77v_version_check.py` → **7 passed**（behind→STALE_VERSION+RUN 不创建；allow_stale→COMPLETE+overridden；unknown→留痕；旧 state 无键不崩）。

## 4. 回归与 doctor

- `upgrade_regression`：唯一红 obs154×1（既有在册）；relock dry-run ×4「无变化 OK」（无锁条目档，锁链零扰动）。
- doctor：源码侧 PASS；装机侧 PASS、OBS_69 MATCH、OBS_68 MATCH（本档 9 文件同步装机侧后复验）。
- 全套 pytest：567 passed/22 skipped/8 failed——8 红=7 项 76Q/76N 在册环境红（缺 installed 布局/env）+obs304（随档更新后已绿，见上）。

## 5. 已知缺口（记档，交后续档裁决，本档不扩案）

1. **编排器测试真实联网**：`_version_check_step` 无 network_mode 门，19 处既有 `orch.run()` 测试每次真实 ls-remote（约 1.6s/次）。**当前不爆**：首个 tag v2026.09.02-77v 日期=本地基线日期 2026-09-02 → current 通过；只有未来「pipeline-only 档升版发新 tag 但 relock history 基线日期未推进」时这些测试才会集体 STALE_VERSION。下个触 pipeline 的档应加测试豁免门（如 env `WXGZH_SKIP_VERSION_CHECK=1` 或 fake_live/offline 模式跳过）。
2. run() doctor 失败分支引用未定义 `st`（`_wall_seconds(st)` 在赋值前）——既有潜伏缺陷（非本档引入，未授权不修）。
3. README 五技能表内 pipeline 版本单元格仍写 9R25（速览行已写 9R26；表单元格修正未授权，留给下个 README 触碰档）。

## 6. 程序校验

- 唯一编号：`238 119 356 True`
- R59：`main=21 partition_active=21` 双差集空
- 锁 sha 不变：`217a5c37…`（无锁条目档）

## 7. 基线链

`5a7cd31（77U-F3 README 同步）→ <feat 77V>（本报告随 docs 或并入 feat 提交）→ tag v2026.09.02-77v`

tag 命名与打点：首个 tag，按「vYYYY.MM.DD-<档号>」约定，指向 77V feat 提交，推送后 version_check 形态①将从 unknown 变为 current（远端 tag 日期 2026-09-02 == 本地基线日期）。
