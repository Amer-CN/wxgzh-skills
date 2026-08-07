# 档71I — OBS-199~203 收尾档（台账口径拆分 + CI 口径正式化 + 两处清障）

## ① 本档定位与 RUN 豁免（5a）

本档零判据改动（R89：writing_contract.py、validators/*、producers.py 的 gate 与阈值代码一律未动）；第 4 段仅动 `_select_live_cover` 的错误文案字符串（15 处 `"cover FAIL_CLOSED: "` → `"cover: "`），不触及任何 RUN 产物写入路径（grep 确认该串只出现在 producers.py raise 与历史报告，不进 final_article/final.html/任何产物文件）。**故端到端 RUN 豁免成立，本档未跑 RUN。**

## ② 第 1 段 台账补登与口径修正

- 1b：198 行状态 `已修` → `部分修`，机制描述修正为「`_media_two_phase` 的 raise 自带前缀 + 外层 except 再拼一次；`_wechat_api_blocked_meta` 一直只有一层（71H 描述误指）」；198 已同步进未修清单分区（R59）。
- 1a：补登 199（已修，71I 4b cover 前缀修复）/ 200（未修，R90 类 A 只登记不单修）/ 201（已修，本档 1c 口径拆分）/ 202（已修，本档 1b 描述修正）/ 203（已修，本档 3b 统一 run_dir 深度）。
- 1c 口径拆分（OBS-201）：
  - **唯一 OBS 编号数 = 85**（主表编号集合 119–203 连续，S92 校验：集合大小 == 85 ✓，完整集合见下）。
  - **台账文件行数 = 148**（原「总数 134」改名，仅作文件体积参考）。
  - 新旧对照：旧「总数 134」（混计主表 + 分区重复行 + 口径行，193 计两次）→ 新「唯一 OBS 编号数 85 / 台账文件行数 148」。
  - 完整编号集合：`119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203`（85 个）。
- 1d R59 对账：全表未修+部分修 `{122,131,148,158,159,175,177,181,182,186,193,198,200}`（13）== 未修清单分区编号行（13）✓。
- 1e：口径第 20 条已追加（71I 口径拆分 + R89/R90 说明）。

## ③ 第 2 段 CI 口径正式化（OBS-193）

- 2a：台账新增「★CI 口径正式化」显著声明（逐字含三点：零 success 长期红 / 四类根因（类 A 12 项、类 B、类 C 8 项、类 D 4 项）/ CI 绿不构成验收依据、CI 红不构成停机依据、以本机 junit 为准、解除条件=四类清零且 CI 首次 success）。
- 2b：仓根存在 `README.md`，顶部已加同义提示并链接台账「CI 口径正式化」节；未新建文件。
- 2c：未改 `.github/workflows/*`、未 skip 任何测试、未动 LOCKED_HEADS、未加 bs4 依赖（全部留给 CI 环境档）。

## ④ 第 3 段 OBS-203（7 处 run_dir 统一深度）

- 3a 七函数清单：`test_obs180_wechat_stage_gate_live_unset` / `test_obs180_wechat_stage_non_live_not_blocked` / `test_obs180_media_continue_gate_live_unset` / `test_obs180_wechat_no_env_attr_fails_closed_no_attributeerror` / `test_obs180_wechat_env_empty_fails_closed` / `test_obs180_wechat_env_allowed_not_blocked_by_gate` / `test_obs180_media_continue_gate_live_allowed_passes_gate`。
- 3b：7 处 `tmp_path/"r"/"d"` → `tmp_path/"a"/"b"/"c"`（parents[2]==tmp_path），断言零改动。
- 3c：全量 pytest 7 条逐一仍绿（junit failures=0，见 ⑤）。

## ⑤ 第 4 段 OBS-199（cover 路径双前缀）

- 4a grep `cover FAIL_CLOSED` 完整命中：`producers.py` 15 处 raise（L1086–1229，全部在 `_select_live_cover`）+ 历史报告 `obs99-cover-path-70.md`（14 处，未动）+ `obs193-198…71h.md`（1 处，未动）；**tests/ 零命中（无测试断言完整串）** → 走 4b 修复分支。
- 4b：15 处前缀 `"cover FAIL_CLOSED: "` → `"cover: "`；外层 except 仍拼 `FAIL_CLOSED: `，最终 stderr 依旧以 `FAIL_CLOSED:` 开头。
- 4c 前后实测：
  - 改前（71H 4b 反证捕获）：`'FAIL_CLOSED: cover FAIL_CLOSED: no stable single_asset approval in contract'`
  - 改后（本档实测）：`'FAIL_CLOSED: cover: no stable single_asset approval in contract'`（exit_code=2 不变）。

## ⑥ 第 5 段 收口

- pytest（junit）：装前 **448/446/0/0/1/1/0**（total/passed/failed/errors/skipped/xfail），装后同 —— 与预期完全一致，本档未新增测试；S91 未触发。
- OBS_68 = **654/654**（仅新增 audit/ 报告 md，按口径不计入；diff=0/missing=0/extra=0）；OBS_69 **MATCH**；upgrade_regression ALL PASS；三处锁 diff 全空；两仓 status 空。

## ⑦ 没证明什么 + 新发现没修

- 没证明：端到端 RUN（本档豁免）；类 A 12 项修复（R90 只登记不单修）；CI 变绿（四类根因均在，解除条件未达）。
- 新发现没修：`producers.py` 与 `obs99-cover-path-70.md` 中的 cover 文案历史记录仍含旧前缀（报告为历史留痕，未改）；`test_obs180_wechat_api_gate.py` 内 `tmp_path/"a"/"b"/"c"` 现共 9 处（7 处本档统一 + 4a/5c 两处既有），未来若有人给任一测试写 .env，parents[2]==tmp_path 已就位，OBS-194 不会复发。
