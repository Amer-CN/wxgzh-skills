# 档71C-R5 — 生成器—产物一致性与陷阱反证闭环（OBS-167~174）

## ① 本档修的是上一档的什么错

| OBS | 上一档(R4)的错误 | 本档修复 |
|---|---|---|
| OBS-167 | main() 缺失明细分支用未定义 `out_dir`,fake_offanchor CLI 崩溃(NameError 实测) | 顶部统一 `out = Path(a.out_dir)`,后续全用 out;subprocess 测试焊死 |
| OBS-168 | CLI 缺失明细零测试死代码 | test_obs167_cli_missing_detail.py(returncode/明细段/行数现场计算) |
| OBS-172 | R4 改了 emit 分支反查,但源头函数 export_body_anchors 仍输出旧格式 slot;JSON 产物未重跑(0b 实测:重跑 s-alert-body vs 仓库 body) | 源头函数从 SLOTS 反查(slot_name/mode),emit 直接消费;重跑产物;五列全比测试 |
| OBS-163 | component_anchors.json slot 列旧格式且与源头函数不一致 | slot 列真实槽名 + LOOKUP_MISS 显式失败 |
| OBS-170 | R4 3d 用「真渲染器不丢导语所以构造不出来」作结论(R37/S52 违规) | fake_dropintro 假渲染器实测:**假绿可构造** |
| OBS-171 | 阀二对照是一次性脚本,未落成回归测试 | test_obs165_valve2_anchor_scope.py(甲乙两套锚参数化) |
| OBS-173 | 锚状态键含 `.agents/skills` 硬编码 + import 期读安装侧 | paths+skill_discovery 同源解析;五键分型;惰性化(import 不碰安装侧) |
| OBS-174 | 矩阵 generated_at 停在上一档,内容被手改 | v4 重生成(generated_at 更新) |

## ② 每条「已覆盖」声明 → 测试函数名 + 断言行

| 声明 | 测试函数 | 断言行(原文) |
|---|---|---|
| CLI 不崩溃 | test_obs167_cli_fake_offanchor_no_crash_and_detail | `assert proc.returncode == 0` |
| 明细段存在 | 同上 | `assert "--- 缺失哨兵明细" in proc.stdout` |
| 明细行数=现场计算 | 同上 | `assert len(detail_lines) == expected` |
| 真渲染器 0 行明细 | test_obs167_cli_real_renderer_zero_detail | `assert len(detail_lines) == 0` |
| 五列全比 | test_obs154_anchors_json_matches_export_exact | `assert row["slot"] == info["slot"]` 等五条 |
| slot 非旧格式 | 同上 | `assert not row["slot"].startswith(("s-", "s_"))` |
| slot 命中 SLOTS | 同上 | `assert row["slot"] in slot_names` |
| 陷阱可构造 | test_obs170_dropintro_trap | `assert gd._normalize_text(first_para) in gd._normalize_text(missing) or first_para in missing` |
| 阀二两配置 | test_obs171_valve2_anchor_scope | `assert results["乙"]["body_len"] > results["甲"]["body_len"]` 等 |
| 锚状态五键 | test_obs173_status_missing/corrupt/sha_absent/sha_drift/ok | `assert st["key"] == "ANCHORS_JSON_MISSING"` 等 |

## ③ 所有空集 / 归零结论 → 各自反证物(R32)

| 名单 | 实测值 | 反证物 |
|---|---|---|
| QUARANTINED | 空 | fake_empty.py / fake_partial.py |
| MULTILINE | 空 | fake_collapse.py |
| ANCHOR_GAP | 空 | fake_offanchor.py |
| APPROVED | 9 类 | fake_offanchor.py(降为 <9) |

## 第 0 步 现场取证

- 0a: `git show 33ee5cb --numstat` = `50 1 validators/component_anchors.json`;diff 减行 = **1**
- 0b: 重跑 emit-anchors 到 .temp/71cr5-probe → **新 JSON slot=body(新格式) vs 仓库 JSON slot=s-alert-body(旧格式)** → 4b 未落地实锤(OBS-172)
- 0c: fake_offanchor CLI 崩溃完整 traceback:`NameError: name 'out_dir' is not defined`(OBS-167)
- 0d: grep `.agents`/`parents[2].parent` → gzh_design.py:232-233(硬编码,已修)+ tests 2 处 + paths/skill_discovery 正常路径
- 0e: 独立复算 distinct 非 URL style:R3=**16**、R4=**17**(与审核方一致;算法=git show + URL_SLOT 过滤 + set 去重)

## 第 1 步 OBS-167/168

1a main() 统一 `out`;1b test_obs167_cli_missing_detail.py 2 条全过(subprocess 加 `-X utf8` 解决 GBK 乱码)。

## 第 2 步 OBS-172/163(主线)

- 2a 源头函数 `export_body_anchors_from_measurement` 改用 `_lookup_slot()` 从 SLOTS 反查(slot_name/mode);反查不中 → SLOT_LOOKUP_MISS
- 2b main() emit 分支删重复反查,直接消费源头结果(R29 单一来源)
- 2c 重跑产物:generated_at 旧 `2026-08-06T21:35:16+00:00` → 新 `2026-08-06T22:27:48+00:00`;样例:alert(slot=body/mode=type=caution)、media-text(cap)、long-image(caption)、resources(link_text);SLOT_LOOKUP_MISS=[]
- 2d test_obs154 五列全比 + 形状断言(非 s- 前缀 + 命中 SLOTS)

## 第 3 步 OBS-170 陷阱反证

- fake_dropintro.py:吞首个 ## 前非组件行;组件块文本 + head title 照常渲染
- 实测:**【高危:假绿可构造】风险提示 判存在 —— alert title 同名文本补位**;guard ok=False(因第一段「这是第一段导语」不同名仍被拦)
- 定性:若被吞导语段全部与组件文本同名 → guard 完全假绿(ok=True)。收紧候选(不改 guard,交裁决):
  ① 导语段须在章节标题之前的正文区出现(位置特征)
  ② missing 检查要求「导语段与上下文联合匹配」,防单段同名补位
  ③ 渲染器 intro 区(首 ## 前)独立渲染校验
- 报告不再出现「真渲染器不丢导语所以构造不出来」(S52)

## 第 4 步 OBS-171 阀二回归

test_obs165_valve2_anchor_scope.py:甲=6 条手抄(逐字)、乙=17 条 JSON 锚;guard ok/line_count/missing 两配置一致;组件文本全进 body;body_len 138/189(乙>甲)。

## 第 5 步 OBS-173

- 5a 删 `.agents/skills` 硬编码 → paths.resolve_project_root + skill_discovery.load_lock 同源
- 5b 五键:ANCHORS_JSON_MISSING/CORRUPT/SHA_ABSENT/SHA_DRIFT/RENDERER_NOT_FOUND(缺 sha 不抛异常)
- 5c 惰性化:refresh_anchor_status() 首次调用计算;import 期只读仓内 JSON
- 5d test_obs171_anchor_status.py 五状态各一条,断言具体 key + detail 非空

## 第 6 步 OBS-174

矩阵 v4 重生成:criteria_version=v4、changelog 追加、generated_at=2026-08-06T14:33:17+00:00、renderer_path 相对;测试断言同步 v4。

## 第 7 步 回归与安装

- 7a pytest(junitxml 权威):装前/装后均 **403 collected / 401 passed / 0 failed / 0 error / 1 skipped / 1 deselected**;
  ★差 1 解释:collected(403) = passed(401) + skipped(1) + deselected(1) = 403,**实际不差**;此前 R2/R3/R4「差 1」是进度字符被 `\r` 覆盖的计数误差,非真实差异
- 7b 安装侧已装;三处锁文件 git diff --stat 为空
- 7c OBS_68 算式:641 + 5(fake_dropintro + test_obs167 + test_obs170 + test_obs165 + test_obs171)− 0 = **646**;实测 repo=646/installed=646/diff=0/missing=0/extra=0;OBS_69 MATCH;observability.py 无需改(锁未变+计数动态实算)
- 7d fixture 两份 sha 逐字节不变
- 7e upgrade_regression ALL PASS

## 没证明什么

- 微信端渲染未验证(需人工预览)
- B 组 10 类未接线;fake_live 仍不过语法门禁
- 陷阱假绿的收紧候选方案未实施(交裁决,改 guard 另起一档)
- 锚覆盖仅限 41 哨兵探针样本;组件 title 补位仅测了 alert 一类同名
- 未 relock;gzh-design 仓零改动;references 未动

## 新发现但没修

- 【高危】导语段被渲染器吞 + 组件同名文本补位 → guard 假绿可构造(fake_dropintro 实测),收紧候选 3 条已列,待裁决
- R4 的 emit 反查与源头函数不一致曾致 JSON 产物旧格式(R4 提交物与代码不符)——本档已统一,但提示「生成器改了必须重跑产物」的流程约束仍未自动化(仅测试能抓)
- relock 不自动同步 OBS-69 基线(R2 遗留,仍未修)
