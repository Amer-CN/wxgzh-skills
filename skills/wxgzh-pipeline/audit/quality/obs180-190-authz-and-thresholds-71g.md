# 档71G/71G-F — OBS-180~192 授权键代码化 + 判据去单篇化 + S76 事件 + 台账收口

## ① 本档修的是上一档的什么错

| 项 | 错误 | 修复 |
|---|---|---|
| OBS-185 | 门禁阈值是单篇素材常量(MIN_DENY_ASK_COVERAGE=10 / MIN_NUMBER_PAIRS=3),换话题必死 | 1a/1b 参数化:required=min(10,len(lines))、ok=not missing、素材 0 条显式 N/A;1e 七条正反例(③⑥ 贴改造前后) |
| OBS-180 | 授权键零代码强制力 | 2a-2c 三个落点 fail-closed 化(WXGZH_WECHAT_API_ALLOWED);2e 三态实测;2d 其余九键判定不写 gate;4e 措辞更正(『唯一不可逆风险』为误判,三重结构性排除) |
| OBS-186 | resume() 硬编码 create_wechat_draft=True,create=False 不可达 | 只登记不改;风险由 180 的键覆盖 |
| OBS-187/188/189/190 | 反硬编码守卫范围不足 / 台账不对账 / 测试头 docstring 过期 / 12 vs 13 文档口径 | 5b 扩扫描范围 / 4 对账收口 / 5a 更正 / 报告按 13 表述 |
| OBS-191(S76) | 新增 gate 直接访问 ctx.env,16 个既有 live 测试翻红 | 1a 统一 `_wechat_api_env` 防御式读法 + 2a-2e 给 16 个测试补前置授权 + 对照负例;R61/R62 落地 |
| OBS-192 | _media_two_phase 落点覆盖 | 既有测试实测命中 gate 行(证据见 ③),并补授权放行测试 |

## ② 每条「已覆盖」声明 → 测试函数名 + 断言行原文（R36/R49）

| 声明 | 测试函数 | 断言行(原文) |
|---|---|---|
| 16/16 PASS、required=10 | test_obs185_16_of_16_pass | `assert ok is True, rep` / `assert rep["required_coverage"] == 10` / `assert rep["coverage_basis"] == "material_derived"` |
| 9/16 FAIL(不因改造变绿) | test_obs185_9_of_16_fails | `assert ok is False, rep` / `assert rep["covered_in_codeblocks"] == 9` |
| 4/4 PASS、required=4(改造前 FAIL) | test_obs185_4_of_4_pass | `assert ok is True, rep` / `assert rep["required_coverage"] == 4`(改造前实测 `ok=False, min_coverage=10` 已贴) |
| 2/4 FAIL | test_obs185_2_of_4_fails | `assert ok is False, rep` / `assert rep["required_coverage"] == 4` |
| 素材 0 条 → N/A | test_obs185_zero_lines_not_applicable | `assert rep["OBS88_CODEBLOCK"] == "N/A"` / `assert rep["not_applicable_reason"] == "injected material contains no deny/ask lines"` |
| 1 对已登记 PASS(改造前 FAIL) | test_obs185_one_pair_registered_pass | `assert ok is True, rep` / `assert rep["required_pairs"] == 1`(改造前实测 `ok=False, min_pairs=3` 已贴) |
| 1 对未登记 FAIL | test_obs185_one_pair_unregistered_fails | `assert ok is False, rep` / `assert any(m["start"] == 8 and m["end"] == 11 for m in rep["missing"])` |
| 未设+live → FAIL_CLOSED | test_obs180_unset_live_fails_closed | `assert rep["wechat_api_allowed"] is False` / `assert "在 .env 中加入 WXGZH_WECHAT_API_ALLOWED=1" in rep["wechat_api_blocked"]` |
| 设 1+live → 放行 | test_obs180_set_one_live_allowed | `assert rep["wechat_api_allowed"] is True` / `assert ok is True, rep` |
| 设 0 覆盖 .env=1 | test_obs180_zero_overrides_dotenv_one | `assert rep["wechat_api_allowed"] is False` / `assert ok is False` |
| 非 live 不受影响 | test_obs180_non_live_unaffected | `assert rep.get("wechat_api_allowed") is None` / `assert ok is True, rep` |
| _wechat 无 env 属性 → 不抛 AttributeError、FAIL_CLOSED | test_obs180_wechat_no_env_attr_fails_closed_no_attributeerror | `assert meta["entry_run"]["exit_code"] == 2` / `assert meta.get("skipped") is None` |
| _wechat env={} → FAIL_CLOSED | test_obs180_wechat_env_empty_fails_closed | `assert meta["entry_run"]["exit_code"] == 2` |
| _wechat env 授权 → 不被 gate 拦 | test_obs180_wechat_env_allowed_not_blocked_by_gate | `assert "WXGZH_WECHAT_API_ALLOWED" not in str(meta)` |
| _media continue 未授权 → FAIL_CLOSED(实测命中 gate 行) | test_obs180_media_continue_gate_live_unset | `assert meta["entry_run"]["exit_code"] == 2` / `assert "WXGZH_WECHAT_API_ALLOWED" in meta["media_request_failed"]` |
| _media continue 授权 → 过 gate(后续才失败) | test_obs180_media_continue_gate_live_allowed_passes_gate | `assert "WXGZH_WECHAT_API_ALLOWED" not in meta.get("media_request_failed", "")` / `assert "frozen discovery manifest sha256 invalid" in meta.get("media_request_failed", "")` |
| 16 个既有 live 测试全绿 | test_obs72_cover_selection(8) + test_obs99_cover_path(8) | junit failures=0(全量 445/443/0/0/1/1) |

## ③ S76 事件（71G-F）

**现象**:71G 全量 pytest 出现 16 个既有测试失败(junit 440/16/1,passed=423)。

**两层根因**:
1. 属性访问层(14 个):gate 直接读 `ctx.env`,而 test_obs72/test_obs99 的手写 fake `_Ctx` 无 env 属性 → `AttributeError: '_Ctx' object has no attribute 'env'`(producers.py 原 1226 行,贴过原文)。
2. gate 真生效层(2 个):`_CtxEnv(_Ctx)` 的 `self.env = env or {}` 把父类默认整体覆盖成空 → `test_allow_warnings_env_switch` / `test_allowance_record_joins_outputs` 被 gate 本身 FAIL_CLOSED,不是属性缺失。

**处置**(不降严格性):统一 `_wechat_api_env(ctx)`(dict(os.environ) → update(getattr(ctx,"env",None) or {}) → .env setdefault);16 个测试仅补前置授权(`self.env = {"WXGZH_WECHAT_API_ALLOWED": "1"}`)+ `_CtxEnv` 与父类键合并 + autouse delenv(R62);零断言改动(diff 已核)。2e 三条对照负例证明「给测试补授权」不是关闸门:
- 无 env 属性 + live → 不抛 AttributeError,FAIL_CLOSED(exit_code=2),meta 无 skipped
- env={} + live → FAIL_CLOSED
- env 授权 + live → 不被 gate 拦(失败原因不含键名)

## ④ R59 对账表

| 全表未修/部分修行号 | 未修清单分区编号行 | 一致 |
|---|---|---|
| 122,131,148,158,159,175,177,181,182,186 | 122,131,148,158,159,175,177,181,182,186 | ✅ |

分区另有非编号行:微信端渲染【已关闭】/ fake_live / 键测试执行层覆盖【未覆盖】。180/185 已修,不进分区(4d 口径)。

## ⑤ 台账七数

总行数 **126** / 未修 **8** / 部分修 **2** / 未修清单 **13** 行 / 待查 **5** / 空号 **1** / 已关闭 **1**。
台账新增行:185/186/187/188/189/190(71G)+ 191/192(71G-F);口径追加 R57–R62;71G 汇报 passed 计数更正为 **423**(440-16-1)。

## ⑥ 第 1–6 步实测

### 第 1 步 判据去单篇化(OBS-185)
- 1a/1b/1c 代码已改(见 ② 证据);S73 对比:71F 重跑(71G-F RUN 64jf2c)final_article sha `3e829be0…6f6f0`、57 行/3372 字符、16 行各 1 次、codeblock covered=16/required=10/basis=material_derived/PASS、registry 3 对/required_pairs=3/PASS —— 与 71F 判定与 covered 数一致。
- 1e ③⑥ 改造前实测:`ok=False, covered=4, min_coverage=10` / `ok=False, registered=1, min_pairs=3`;改造后 `ok=True, required_coverage=4` / `ok=True, required_pairs=1`。

### 第 2 步 授权键代码化(OBS-180)
- 三个落点:doctor(live 纳入 ok + wechat_api_allowed 字段 + 报错含「在 .env 中加入 WXGZH_WECHAT_API_ALLOWED=1」)、`_wechat`(exit_code=2 FAIL_CLOSED meta,先于 create 检查)、`_media_two_phase`(live continue 前 raise)。
- 三态:未设+live FAIL_CLOSED(测试 ①)/ 设 1+live 放行(测试 ② + 真实 .env 下 doctor PASS)/ 设 0 覆盖 .env=1(测试 ③)。
- 2g:.env 键名清单:`WECHAT_APP_ID` / `WECHAT_APP_SECRET` / `WXGZH_WECHAT_API_ALLOWED`(值不贴)。
- 2d:其余九键不写 gate,理由:约束执行端 git/环境动作,不在本 Python 包管辖范围。

### 第 3 步 OBS-186 登记
resume() 内 `create_wechat_draft=True` 硬编码;任何完整 RUN 必经 resume(agent 阶段返回 AWAITING_AGENT),create=False 在完整跑通路径不可达;审核方 71F 误设前提已认领;行为不改,风险由第 2 步键覆盖。

### 第 4/5 步 台账收口与 R56 欠账
见 ③④⑤;test_obs176 头部改 9 函数/新 F 口径;test_obs183 扩扫 3 键 + AIHOT_INJECTION_INSTRUCTIONS。

### 第 6 步 回归
pytest 装前装后均 **445/443/0/0/1/1**(junit);增量 21 全部来自 test_obs185(7)+ test_obs180(14);OBS_68 = 651+2 = **653**,repo/installed=653/653,diff=0;OBS_69 MATCH;upgrade_regression ALL PASS;三处锁 diff 空;两仓 status 空。

## ⑦ ★怎么发下一篇文章(最小操作清单,用户视角)

前提:本地 .env 已含 `WXGZH_WECHAT_API_ALLOWED=1`(本档 2g 已加);以「自有素材发文」为例(items-file 注入):

1. 准备素材:把文章素材整理为 items JSON(与 `tests/fixtures/obs88/items.four.json` 同构:summary 含 deny/ask 原文与数字对比),存到 `.temp\xxx-items.json`。【不调微信 API】
2. 发起 RUN(实时模式):`python -m wxgzh_pipeline.cli "发文：<选题>"`(或驱动脚本传 items_file)。doctor 先跑:skills 锁校验 + 微信凭据 + `WXGZH_WECHAT_API_ALLOWED` 三态检查,缺任一 FAIL_CLOSED 起不来。【此步不调微信 API,但会校验微信凭据存在】
3. 写作交接:aihot → super_writer → zh_human_writing 三阶段各停一次 AWAITING_AGENT,由你(或写作子代理)产出产物并 `python -m wxgzh_pipeline.ack_cli --stage-dir …`。【不调微信 API;OBS88 数字/代码块门禁在此把关,阈值由素材实测导出】
4. 媒体发现:RUN 停在 AWAITING_MEDIA_ASSET_APPROVAL。审阅 `approval_readiness.json`,对每张图给出批准(单资产批准写入 `copyright_approval.json`)。【此步不调微信 API;★需要人工批准】
5. 续跑:`orch.resume(RUN_ID)` → media continue 真实 uploadimg(每张图一个 HTTP 调用)→ gzh_design 渲染 + 全门禁(theme_identity/intro_guard/img_src/组件可见性/删除线)。【★此处调微信 API(uploadimg);需要人工批准已完成】
6. 草稿:wechat_draft 阶段 `draft/add` 创建草稿,返回 media_id 与草稿数 +1。【★此处调微信 API(draft/add)】
7. 验收:到微信编辑器打开新草稿,肉眼预览(alert 多行/代码可复制/配图位置/删除线)。【★需要人工肉眼预览;不调 API】
8. 发布:本流水线无发布能力,正式发布由你在微信后台手动执行。【★唯一能正式发布的人是你】

禁止项提醒:任何一步发现门禁 FAIL 即停机上报;不降阈值、不删测试、不改锁;本包无 freepublish/群发/定时/删草稿能力。

## ⑧ 没证明什么 + 新发现但没修

- 没证明:授权键对「执行端 git/环境动作」九键无强制力(2d 判定,71G 单独确认过 180 的误判);真实 live 全链路(本轮全部 integration/audit,零真实微信);通用规则对全新话题的首篇产效(仅同素材重跑)。
- 新发现没修:release_audit 经 CLI 默认 live 调 doctor,现要求 .env 有授权键(已满足,但属行为变化);`_wechat_api_env` 的 .env 定位依赖 `ctx.run_dir.parents[2]`,与 doctor 的 project_root 定位两处并存(当前一致,未合并);wechat_draft 在 integration 走 fake shim 时仍写 simulated 草稿计数(与真实草稿计数 11 无关)。

## ⑨ 一句话净变化

判据阈值由素材实测导出(换话题不再被单篇常量卡死)、微信 API 调用有了默认拒绝的代码级闸门(三落点 fail-closed + 三态实测 + 16 个既有测试补授权后全绿),台账按 R59 对账收口 —— 下一篇发文的最小可操作路径与每一步的微信/人工依赖已写成清单。
