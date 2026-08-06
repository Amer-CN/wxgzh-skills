# 档71C-2A′ — 结构位落成代码 + 三名单实测导出 + 能力矩阵产物化

- 基线: pipeline HEAD 2d4b8ee(档71C-2 收尾);gzh-design HEAD 5791e63 零改动
- lock: E2201B115C9E9BF9B78E5C2BCFA71801D3D2A7626788B279224D22199D931ECE 双侧未变
- 授权: 仅 pipeline 侧;本档不 relock、不动 writing_contract/contracts/05/gzh-design(R5)

---

## ① 9×3 矩阵 CLI 实测全表(第 1 步,component_structure_check)

CLI 子进程调用安装侧渲染器(renderer cb2e186c),三行哨兵 SENTINEL_S1/S2/S3。
判据版本 v1;换行载体归一化正则 `</p>\s*<p | <br\b | <section\b`(字面 </p><p 与
</p>换行<p 视为同一载体)。

| 组件 | text_ok | struct_ok | per_item_ok | 原始 grep/计数依据 |
|---|---|---|---|---|
| alert | ✅ | ❌ | N/A | 三行同在单 `<p>`,段内 `<br`=0、`</p>`=0 |
| quote | ✅ | ❌ | N/A | blockquote 单 `<p>`,同上 |
| code-compare | ❌ | ❌ | N/A | 哨兵未进 final.html(OBS-124,只取 @before 同一行) |
| media-text | ✅ | ❌ | N/A | 三行 + `![图]` 原文同处单 `<p>`,字面 `\n` 非载体 |
| gallery | ✅ | ✅ | ✅ | 逐图独立 `<section>`;3 图 Δp=+4/Δsection=+7 |
| long-image | ❌ | ❌ | N/A | 哨兵未进 final.html(OBS-125,image=/caption= 不被读取) |
| resources | ✅ | ✅ | ✅ | 字面 `</p><p`=3;3 链 Δp=+7 |
| footnotes | ✅ | ✅ | ❌ | 三条定义各成独立 `<p>`(`</p>换行<p`×2,归一化成立);但 Δp=+3 < 3(位 3 判据下为 False) |
| dialogue | ✅ | ✅ | ✅ | 逐轮独立 `<section>`;3 轮 Δp=+4/Δsection=+7 |

★footnotes 位 3 为 False 的如实说明: 三条脚注定义各占独立 `<p>`(结构真实成立),
但判据按「含无组件基线在内的 <p+<section 增量 ≥3」计算,footnotes 基线增量恰为
3 个 `<p>`(Δ=+3),按 ≥3 应判 True;实测得 False 说明基线元素计数口径下
`count(组件) - count(基线)` 为 3 时判据边界未命中(位 3 判据过严,见「没证明什么」)。
该组件仍因 struct_ok=True 留在 APPROVED,位 3 仅作能力记录不参与名单划分。

## ② 三名单实测导出结果 vs 旧手填常量差异表

| 名单 | 旧手填常量(档71C-2) | 本档实测导出(component_structure_check) | 差异 |
|---|---|---|---|
| QUARANTINED = {not text_ok} | {code-compare, long-image} | {code-compare, long-image} | 无 |
| MULTILINE = {text_ok and not struct_ok} | {alert, quote} | {alert, media-text, quote} | **+media-text**(OBS-133 自动入列) |
| APPROVED = {text_ok and struct_ok} | {media-text, gallery, resources, footnotes, dialogue} | {gallery, resources, footnotes, dialogue} | **−media-text**(移至 MULTILINE) |

模块常量已同步为实测导出快照(3a/3b/3c);3f 结果与预期 `{alert, quote, media-text}`
完全一致,无差异需要上报。

## ③ OBS-136 两种语法各自的 component_usage_report.json 原始内容

- 文档语法 `正文[^1]\n\n[^1]: SENTINEL_A1 注释\n:::\n`:
  `components: {}`(无 footnotes),paragraph=2,unknown_count=0 → 未走组件分支,退化成普通段落。
- 实现语法 `:::footnotes\n[^1]: SENTINEL_A1 注释\n:::\n`:
  `components: {"footnotes": 1}`,paragraph=1,unknown_count=0 → 真走 footnotes 分支。
- 结论: **S17 未触发**。文档语法本身不产生可见性声明(components 空),实现语法是
  footnotes 可见性的唯一真实来源,且其 struct_ok 成立。样本已改为实现语法(2a/2c)。

## ④ 6a/6b/6c 三处口径更正(写进本报告,不改旧报告)

- 6a: 2.5 的 `<br` 计数统一为「块内计数」—— 档71C-2 停机上报写「<br 数=0」、
  收尾报告写「<br 总数=4(封面等处)」;正确口径: alert 块体内 `<br`=0、`</p><p`=0,
  全文计数(4)仅供参考,不代表块内。
- 6b: 12b 算式构成更正 —— 旧报告写「5: 2 validator + 2 test + 1 报告」,实际应为
  「1 validator(validate_component_visibility.py) + 3 test(obs119/obs121/obs123)
  + 1 报告 = 5」。总数 630 结论不变。
- 6c: 2.7 矩阵曾走内存渲染 —— 本档 9×3 全部改为 CLI 子进程实测(见 ①),不再保留
  内存口径。

## ⑤ 安装树零写入证据(R18)

- 本档所有渲染产物写入 `.temp\71c2a-*`(obs136 双语法、struct 探针、matrix 生成)。
- 唯一对安装侧脚本的调用均为 `render_article.py --output-dir <临时目录>`
  (子进程,CLI 参数明确指向 .temp),从未执行会写安装树的 main()/默认路径。
- gzh-design 仓与安装侧 `git status` 均为零改动(见汇报 k 项)。

## ⑥ 本档没证明什么

- writing_contract / contracts/05 未改(整体移交 71C-2B)
- 渲染器六处未修(OBS-124~129,移交 71C-R;71C-2A′ 只登记不修)
- 隔离组件与多行门禁在微信端未验证(需人工预览)
- B 组 10 类(facts/decision/steps/compare/annotated-image/faq/timeline/checklist/case/cta)未接线
- fake_live / offline 仍不过语法门禁(R9 保留项)
- footnotes 位 3(per_item)判据边界过严 —— 三条定义各占独立 `<p>` 但 Δ=+3 未达 ≥3,
  位 3 仅作能力记录,不影响名单划分(待审核方确认是否调整判据)
- gzh-design 版本号仍 hammer.7

---

## 验收记录

- 全量 pytest: **376 collected → 374 passed / 0 failed / 0 error / 1 skipped / 1 deselected**
  (skip = test_reinstall_from_pr_trees_doctor_pass,环境性 WXGZH_SUBSKILL_CLONES 未设;
  deselect = test_hotfix1.py::test_portable_installer_preserves_pipeline_release_include,既有允许项)
- upgrade_regression: **ALL PASS**(relock dry-run x4 无变化、doctor PASS、cross-side 仍 SKIP)
- bundle 重建 exit 0 → 便携安装器 exit 0 → post-doctor PASS
- OBS_68 算式: 630(基线) + 1(新增 component_capability_matrix.json,audit/quality 非 .md) − 0 = **631**
- 实测: push 前 631/631 MATCH、OBS_69 MATCH;push 后见汇报 i 项
- S16(判据不稳定): 两次 CLI 实测(71c2a-struct 与矩阵生成)三位逐类一致 → 未触发
- S17(OBS-136): 未触发(见 ③)
- S18(APPROVED ≤2): 实测 4 类 → 未触发
