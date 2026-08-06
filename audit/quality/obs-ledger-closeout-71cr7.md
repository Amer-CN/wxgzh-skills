# 档71C-R7 — 台账重建与 71C 线收口

## ① 本档修的是上一档的什么错

| 项 | 上一档(R6)的错误 | 本档修复 |
|---|---|---|
| 台账不合格 | obs-ledger.md 全表零「未修」行,8 个真实未修项被标「空号」 | 重建:五列 + 独立「未修清单」分区(R41);空号附证据(R42:169 有 R5/R6 报告标注,其余无证据标待查) |
| 台账口径缺失 | 无「本台账口径」小节 | 补口径:报告名区间法/空号证据要求/更新责任 |
| 反证测试未跟进 | — | test_obs170_full_false_green 补「风险提示 in missing_text」断言 |
| main 异常过宽 | except ValueError 吞一切 | 自定义 SlotLookupMiss(ValueError 子类),main 只捕获它 |
| skip 覆盖未透明 | 键测试可能被 skip 无提示 | test_obs173_all_keys_have_tests 输出执行层未验证警告 |

## ② 每条「已覆盖」声明 → 测试函数名 + 断言行原文（R36）

| 声明 | 测试函数 | 断言行(原文) |
|---|---|---|
| 完全假绿拆穿 | test_obs170_full_false_green_constructible | `assert guard["ok"] is False` + `assert TRAP_PARA in guard["missing_text"]` |
| 键全集相等 | test_obs173_all_keys_have_tests | `assert impl_keys == test_keys` |
| LOOKUP_MISS 反证 | test_obs163_lookup_miss_raises | `assert "SLOT_LOOKUP_MISS" in str(ei.value)` |

## ③ 台账数字（1d）

- 总行数 **87**
- 状态列「未修」**4** 行(OBS-122/148/158/159)
- 未修清单分区 **6** 行(4 OBS + 微信端未验证 + fake_live)
- 「待查」**6** 行(OBS-134/141/142/149/150 + 无)
- 空号 **1** 行(OBS-169,附证据)

## ④ 所有空集 / 归零结论 → 各自反证物（R32）

| 名单 | 实测值 | 反证物 |
|---|---|---|
| QUARANTINED | 空 | fake_empty.py / fake_partial.py |
| MULTILINE | 空 | fake_collapse.py |
| ANCHOR_GAP | 空 | fake_offanchor.py |
| APPROVED | 9 类 | fake_offanchor.py |
| 导语假绿 | 已拆穿 | fake_dropintro.py + single_intro_trap.md |

## 第 0 步 证据基

- 0a: audit/quality/ 45 份报告(行数已粘)
- 0b: 8 份关键报告逐份抄出 OBS 原文(见上文提取输出;119-133/136-140/143-147/151-157/160-168/170-174 均有正文描述)
- 0c: grep 全仓(非 audit):OBS-122/134/141/142/148/149/150/158/159/169 零命中;OBS-146 1 处(lock history 的 relock reason,已修证据)
- 0d: 审核方给定四条直接采用(122/148/158/159,均未修)

## 第 1 步 台账重建

见 ③ 与 obs-ledger.md 全文(五列 + 未修清单 + 口径)。

## 第 2 步 渲染器 skip 处置（12 处判定）

| 测试函数 | skip 条件 | 判定 |
|---|---|---|
| test_obs145_four_lists_equal_measured | 渲染器不可得 | 合理 skip(安装侧缺失时名单无从实测) |
| test_obs145_union_equals_builders | 同上 | 合理 skip |
| test_obs154_anchors_json_renderer_sha | 同上 | 合理 skip |
| test_obs154_anchors_json_matches_export | 同上 | 合理 skip |
| test_obs145_negative_samples_render_ok | 同上 | 合理 skip |
| test_obs136_footnotes_doc_vs_impl | 同上 | 合理 skip |
| test_obs145_matrix_json_matches_measured | 同上 | 合理 skip |
| test_obs157_dual_run(仓内) | repo 树缺失 | 合理 skip |
| test_obs157_dual_run(安装侧) | 安装侧缺失 | 合理 skip |
| test_obs173_status_sha_drift | 安装侧缺失 | 合理 skip(状态键本身在测缺失场景) |
| test_obs173_status_ok | 安装侧缺失 | 合理 skip |
| test_obs173_all_keys_have_tests | 无 skip(文本层) | 已实施执行层警告(2b) |

2b 实施:all_keys_have_tests 输出「文本层覆盖,执行层未验证」显式警告(无法用 pytest request.session 精确断言每条键测试已执行,渲染器不可得时 skip 合法;不引入新框架)。

## 第 3 步 三条小修

- 3a: docstring「(11 条 style)」→「条数以 component_anchors.json 现算为准,当前 17」
- 3b: `class SlotLookupMiss(ValueError)`;export 抛它;main 只捕获它;反证测试保留 `pytest.raises(ValueError)` 基类断言(SlotLookupMiss 是其子类,基类断言同时覆盖新旧异常,选基类理由:不绑定实现细节)
- 3c: test_obs170_full_false_green 补 `assert TRAP_PARA in guard["missing_text"]`

## 第 4 步 回归与安装

- 4a pytest(junit 权威):装前 **407/405/0/0/1/1**;装后重跑 **407/405/0/0/1/1**
  (装后首次跑有 2 个 smoke 失败,路径 `.agents\.agents` 双前缀——重跑零失败,判定为命令环境瞬态污染,非本档代码问题;skip 名单同 R6:test_reinstall_from_pr_trees_doctor_pass)
- 4b 安装侧已装;锁三处 diff 空
- 4c OBS_68 算式:647 + 0(本档无新增计入文件;obs-ledger.md 按 OBS-107 口径在 audit/quality/ 下排除)= **647**;实测 repo=647/installed=647/diff=0/missing=0/extra=0
- 4d OBS_69 MATCH;observability.py 无需改(锁未变+计数动态实算)
- 4e fixture 两份 sha 逐字节不变;4f upgrade_regression ALL PASS;4g git status 仅本档改动

## 71C 线收口结论

71C 线(组件载体可见性 + 锚语义 + 导语守卫)已完成主线:判据分裂(render/anchor/per_item)、
锚实测导出闭环(component_anchors.json 驱动 _COMPONENT_PARA_RES)、导语判据分离
(_intro_body_text 不含组件锚,完全假绿拆穿)、反证物齐全(5 个假渲染器 + 2 陷阱 fixture)。
**剩余未修项及 71D 阻塞判定**:

| 未修项 | 71D 阻塞 |
|---|---|
| OBS-122 B 组 10 类未接线 | 【不阻塞 71D】(71D 用 A 组 9 类) |
| OBS-148 探针样本住生产文件 | 【不阻塞 71D】(测试资产,工程债) |
| OBS-158 _nearest_p_style 不校验哨兵在 <p> 内 | 【不阻塞 71D】(锚判据仅探针用) |
| OBS-159 relock 不同步 OBS-69 基线 | 【不阻塞 71D】(下一档 relock 前手动同步) |
| 微信端渲染未验证 | 【阻塞 71D】(发文前必须人工预览) |
| fake_live 不过语法门禁 | 【不阻塞 71D】(仅测试路径) |

**结论:71C 线代码层收口完成;71D 的唯一硬前置是微信端人工预览。**

## 没证明什么

- 微信端渲染未验证(71D 阻塞项)
- 待查 5 号(134/141/142/149/150)未考证(需指令原文或审核方补充)
- B 组 10 类未接线;fake_live 仍不过
- 安装侧与仓内树一致性仅由 OBS_68 计数保证(内容 diff=0)
- 未 relock;gzh-design 仓零改动;references 未动

## 新发现但没修

- 装后首次 pytest 曾出现 2 个 smoke 失败(路径双 `.agents` 前缀),重跑消失——疑似命令环境瞬态注入 WXGZH_PROJECT_ROOT,未定位根因(不阻塞,但建议后续关注 test_obs80 的 env 继承)
- relock 不自动同步 OBS-69 基线(OBS-159,未修)
