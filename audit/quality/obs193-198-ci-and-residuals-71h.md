# 档71H — OBS-193~198 升级前清障(CI 定性 + 残留 R57/假绿/重复实现修复)

## ① 本档修的是上一档的什么错

| OBS | 错误 | 修复 |
|---|---|---|
| 193 | CI 全红(100 次运行零 success),只查不修 | 1 段归因:四类环境性失败并存(详见 ②) |
| 194 | 假绿第 27 例:test_obs180_wechat_stage_gate_zero_overrides_dotenv 的 run_dir parents[2] 读不到 .env,断言 exit 2 只由 ctx.env 的 0 单方满足 | 4a run_dir→tmp_path/a/b/c;R84 例外加严 stderr 断言;4b 反转即红实测 |
| 195 | deny/ask 前缀条件式残留 R57:正则非捕获组判不出 kind,退回整文件 emoji 判断 | 3a 捕获组 + extract_deny_ask_entries + 删 items_raw 死代码 + 3e 无漂移 + 3f 单变量反例 |
| 196 | .env 解析两份独立实现同语义 | 2a _media_subprocess_env 一行委派 _wechat_api_env |
| 197 | WXGZH_ALLOW_WARNINGS 解析范围未声明(只读 ctx.env 是巧合) | 5a docstring 精确化 + 5b 注释 + 5c 钉死测试(R82 未放宽) |
| 198 | 未授权错误文案双重 FAIL_CLOSED 前缀 | 2c WECHAT_API_BLOCKED_MSG 单一来源,raise 去前缀 |

## ② 第 1 段 CI 定性(OBS-193,只查不修)

- 1a:`gh run list --branch dev/0.1.0-dev2 --limit 30` 30 条全 failure → limit 100 仍全 failure,**零 success 记录**;最早可见 2026-08-06T07:01:32Z(34ca3e7a)。→ **S87 未触发**(不存在「最后一次 success 晚于 e8c5291」)。
- 1b:失败发生在 **assert 阶段**(collection 成功、pytest 执行到断言;无 import/路径 collection 错误)。test 作业与 integration 作业日志已拉取(前 40 行 runner 噪音,实际失败清单见下)。
- 1c:REAL_SKILLS **不是唯一原因**。失败四类:
  - **类 A 硬编码开发机路径**(11 项/test 作业):test_obs180_wechat_api_gate ×10(REAL_SKILLS=F:\AIXM\wxgzh\.agents\skills)+ test_obs31_url_contract ×1(RUN_AHOT=F:/AIXM/wxgzh/.temp/...m6pyv4/aihot/deduplicated_items.json)。首行报错如 `FileNotFoundError: ... 'F:\\AIXM\\wxgzh\\.agents\\skills\\gzh-design\\scripts\\publish_wechat_draft.py'`。
  - **类 B CI 未安装被锁子技能**(3 项 pytest + integration 作业整体):test_obs171(ANCHORS_RENDERER_NOT_FOUND 于 workspace/.agents/skills)、test_obs80_smoke_samples ×2(冒烟样本缺失);integration 作业 `doctor FAIL_CLOSED` / `discover_exit_code=2: ... skills/media-enrichment/scripts/run_media_enrichment.py can't open file` / `THEME_IDENTITY=FAIL: render failed: ... skills/gzh-design/scripts/render_article.py`。
  - **类 C CI 依赖缺失**(8 项):test_obs87_approval_evidence ×8 `ModuleNotFoundError: No module named 'bs4'`(test 作业 pip 只装 pytest/jsonschema/pyyaml;integration 作业装了 beautifulsoup4 故无此问题)。
  - **类 D 陈旧常量/基线**(4 项):test_hotfix1::test_portable_installer_preserves_pipeline_release_include(`assert 'cedf92ca45b0...' == '18414cc9cddb...'`,LOCKED_HEADS 的 media-enrichment 头陈旧)、test_observability ×3(embedded OBS-69 baseline f2b5f390 vs 期望 d126995d → MISMATCH)。
- 1d 定性:**「CI 在可见窗口内(≥100 次运行,最早 2026-08-06T07:01Z)全部 failure、无任何 success——CI 长期红,根因为四类环境性失败并存(类 A 硬编码开发机路径 11 项,类 B CI 未安装被锁子技能,类 C bs4 依赖缺失,类 D 陈旧 LOCKED_HEADS 与 OBS-69 基线);71G-F 仅新增类 A 中的 obs180 10 项,其余 16 项在 71F 及更早已红。」**

## ③ 第 3 段 OBS-195 修复(必做)

- 3a 正则:`_DENY_ASK_RE = re.compile(r"(deny|ask)\s+'([^']+)'")`(捕获关键字)。
- 3b `extract_deny_ask_entries(items_path) -> list[tuple[str, str]]`:(kind, text),按 text 去重、首次 kind 胜出。
- 3c `extract_deny_ask_lines` 公开签名/返回值不变,委派 `return [t for _, t in extract_deny_ask_entries(items_path)]`。
- 3d `validate_codeblock_fidelity`:`entries = extract_deny_ask_entries(...)`,`material_has_deny/ask = any(k == ...)`,删除死代码 `items_raw = items_path.read_text(...)`;report 字段名/结构零改动。
- 3e 无漂移不变量测试(test_obs185_no_drift_vs_71gf):`assert [t for _, t in extract_deny_ask_entries(p)] == extract_deny_ask_lines(p)` + 五字段 16/16/10/True/True。
- 3f 单变量反例(test_obs185_deny_only_stray_warn_ask_not_required,新 fixture `tests/fixtures/obs88/items.deny_only_stray_warn.json`):2 条 deny 条目、0 条 ask、⚠️ 只出现在无关说明位置 → `ask_prefix_required is False`,载体无 ⚠️ 时 `OBS88_CODEBLOCK == "PASS"`。反证回显见 ④。

## ④ 反证回显(R83,三段式)

**3f(改前绿 → 临时改回 emoji 宽口径 → 红 → 改回绿)**:
- 改前绿:全量定向 pytest 通过(见 6a 448/446/0/0/1/1)。
- 反转后红(`material_has_ask = "⚠️" in items_path.read_text(...)`):
```
E       AssertionError: {'OBS88_CODEBLOCK': 'FAIL', 'ask_prefix_present': False,
        'ask_prefix_required': True, 'carrier_block_count': 1, ...}
E       assert False is True
tests\test_obs185_material_derived_thresholds.py:218: AssertionError
```
- 改回后绿:临时改动已还原,同测试通过。

**4b(改前绿 → setdefault 反转成 update → 红 → 改回绿)**:
- 改前绿:4a+加严后测试通过。
- 反转后红(`resolved[k] = v`):
```
E       AssertionError: assert 'WXGZH_WECHAT_API_ALLOWED' in
        'FAIL_CLOSED: cover FAIL_CLOSED: no stable single_asset approval in contract'
tests\test_obs180_wechat_api_gate.py:111: AssertionError
```
- 改回后绿:临时改动已还原,同测试通过。
- ★偏差上报:4a 的「断言一字不改」与 4b 的「必须变红」实测不相容——gate 放行后 cover 失败同样返回 exit_code=2,仅靠 exit_code 无法区分;按 **R84 例外**(OBS-194 即修复标的)给该测试加严一条 stderr 断言(必须含 WXGZH_WECHAT_API_ALLOWED),4b 反证随即变红。改动仅限该修复标的测试本身。

## ⑤ 第 2/4/5 段(建议项均落地)

- 2a/2b:`_media_subprocess_env` 一行委派;调用点清单:producers.py:897(discover)、:1013(continue)、tests/test_obs47_credential_source.py:19 —— 行为逐字不变(test_obs47 绿)。
- 2c/2d:`WECHAT_API_BLOCKED_MSG` 模块常量;`_wechat_api_blocked_meta` 拼 `"FAIL_CLOSED: " + MSG % raw`;`_media_two_phase` raise `MediaRequestError(WECHAT_API_BLOCKED_MSG % raw)`(去前缀,OBS-198);`test_obs180_media_continue_gate_live_unset` 零改动仍绿(2d,S88 未触发)。
- 4c:同文件 `tmp_path / "r" / "d"` 共 7 处(审核方数 6,实测 7,5c 新增前为 6)。仅改 4a 一处;其余 7 处说明:① wechat_stage_gate_live_unset / wechat_env_empty / no_env_attr 均未写 .env,gate 靠键缺失阻断,parents 解析无关;② wechat_env_allowed 靠 ctx.env 放行,无 .env 参与;③ wechat_stage_non_live_not_blocked 为 integration,gate 跳过;④ media_continue 两测试靠 ctx.env 或缺失阻断,无 .env 参与。
- 5a/5b/5c:docstring 精确化(取值照抄、范围刻意不同);`_wechat` allow_raw 上方注释钉死;新测试 test_obs180_allow_warnings_ignores_dotenv(.env 写 1 + ctx.env 空 + live → argv 不含 --allow-warnings)。

## ⑥ 第 6 段 回归与交付

- 6a pytest(junit):装前 **448/446/0/0/1/1/0**(total/passed/failed/errors/skipped/xfail),装后同;增量 +3 全部归属:test_obs185_no_drift_vs_71gf(3e)、test_obs185_deny_only_stray_warn_ask_not_required(3f)、test_obs180_allow_warnings_ignores_dotenv(5c)。S85 未触发。
- 6b fake_live 端到端 RUN `20260807T211938-vibe-coding-guide-16-dtcnoy`:final_article sha `3e829be0…6f6f0`、57 行/3372 字符;OBS88_CODEBLOCK 完整 JSON(deny_ask_total=16/covered=16/required=10/basis=material_derived/双前缀 required+present/PASS);五字段与 71G-F 完全一致 → **S86 未触发**;upload mode=wechat_audit(零真实微信)。
- 6c OBS_68 = 653 + 1(新 fixture items.deny_only_stray_warn.json)= **654**,实测 repo=654/installed=654/diff=0/missing=0/extra=0;OBS_69 **MATCH**;upgrade_regression ALL PASS;三处锁 diff 空;两仓 status 空。
- 6d 台账:新增 193-198 六条;总行数 126 → **134**(132 的预期未含 193 分区行与口径第 19 行);七数 = 总行数 134 / 未修 9 / 部分修 2 / 未修清单 14 行 / 待查 5 / 空号 1 / 已关闭 1;R59 对账:全表未修+部分修 {122,131,148,158,159,175,177,181,182,186,193} == 分区编号行(11=11)✓。

## ⑦ 没证明什么 + 新发现没修

- 没证明:真实 live 全链路(本档 fake_live/integration,零真实微信);OBS-181/182/186 未触碰(本档范围外);CI 仍红(本档只查不修,R80——红是预期结果,未动任何测试去让它变绿);「类 A 修复后 CI 会绿」未被证明(类 B/C/D 仍在)。
- 新发现没修:CI test 作业缺 beautifulsoup4 依赖(类 C,与 integration 作业的 pip 清单不一致);test_hotfix1 的 LOCKED_HEADS 与 test_observability 的 OBS-69 内嵌基线陈旧(类 D);test_obs31 的 RUN_AHOT 硬编码历史 RUN 路径(类 A,非 REAL_SKILLS 变量);CI 已红至少到 2026-08-06(更早记录超出 100 条窗口,未追溯)。
