# 档 71C-1：OBS-116/117/118/109/110 pipeline 五修 + gzh-design ::: A组9类接线 + 第十一次 relock

- 日期：2026-08-05
- 范围：wxgzh-pipeline 仓 + gzh-design 源树（仅 render_article.py / generate_advanced_html.py）；第十一次 relock（仅 gzh-design）

## 第 0 步 前置自检 + 0e probe 快照

- doctor PASS；lock 双侧 `0CD0EBC3…`；pipeline HEAD `6b316b7…`（干净）；gzh-design HEAD `af03b438…`（干净）；OBS_68 624/624
- 0e 快照（fence 对照基线）：fence ctrl_visible=True / sentinel_missing=False / unsupported=True；其余 12 类见下（7c 表对比）

## 第 1 步 OBS-116 新魔数

- 改前：`if manifest_count != bundle_count - 2:`（写死 2）
- 改后：`skip_count = sum(1 for i in bundle_z.infolist() if not i.is_dir() and Path(i.filename).name == "MANIFEST.json")` + `if manifest_count != bundle_count - skip_count:`；失败信息打印 skip_count
- 过程中发现 set 推导 bug（同名文件合并为 1）→ 改为计数（skip_count）
- 注释删除「实测（档71B'-C）：manifest=1228 bundle_zip=1230」照数字定判据表述

## 第 2 步 OBS-117 恢复被删维度

- 举证：`pipeline_count` 在 `_enforce_expected_counts` 内只出现在 print（死参数）
- 新增 `_disk_enum_count()`：独立按 PIPELINE_RELEASE_INCLUDES/EXCLUDES 枚举磁盘（不复用 copy_tree/zip），断言 `pipeline_count == disk_count`
- 实测：disk_count=661、pipeline_count=661（构建时）、差集为空（zip_set == disk_set 661 项全同）

## 第 3 步 OBS-118 去二次归一化

- `_probe_single`: `body = _normalize_text(_body_plain_text(html))` → `body = _body_plain_text(html)`（_body_plain_text 内部已归一化）
- 新增 pytest `test_obs118_no_double_normalization`：含 `&amp;lt;` 的 HTML，单次 vs 二次归一化结果不同（实证分叉真实存在）

## 第 4 步 OBS-109 指纹去碰撞

- 举证：`image_media_text_card` 原值 `"0 4px 16px -4px rgba(179,89,59,0.10)"` == `T["hammer"]["sh"]`（阴影令牌）
- 改后：FINGERPRINTS 保留原令牌，新增 `_img_type_occurrences(html, token)`——阴影令牌命中处后续 400 字符内含 `<img` 才计数
- 4d 负对照：alert 改前/改后 img_types 均 []（alert 本不含令牌）；media-text/long-image 正确命中
- 4e 正对照：现 RUN final.html 改前/改后 img_types 均 `['image_2a_standard','image_media_text_card']` 一致 ✓

## 第 5 步 OBS-110 图片来源白名单

- 5a 举证四处无门禁：validate_gzh_html（无 img src 判定）、validate_delivery（不在 final.html 路径）、publish_wechat_draft:208（只校验 uploadimg 返回值）、validate_media_bindings:26（只校验 bindings）
- 新增 `validators/validate_img_src_whitelist.py`：`<img src>` 必须 https://，命中 `../`/`file://`/盘符/`data:` → FAIL_CLOSED
- 5c 悖论检查：现 RUN final.html 打印模式命中 **0**（3 img 全 https）→ 启用 enforce；挂载 gzh_design content_validate（final.html 在其路径上）
- **commit A = `73cdea709f98a58fbcc869d3193080a55c759648`**（6 文件 +150/−10，push 成功）

## 第 6 步 gzh-design ::: 接线（A组9类）

- 6a 源树干净（af03b438）
- 6b OBS-108：`OUT`/`os.makedirs` 移入 main()——import 零写盘；改前后 9 份 hammer HTML 字节与 sha256 完全一致（alert 660 / code-compare 1173 / dialogue 1445 / footnotes 585 / gallery 1302 / long-image 415 / media-text 641 / quote 297 / resources 891）
- 6c render_article.py：parse_article 新增 `:::` 块识别（kind="component"），A 组 9 类；未知名进 unknown 列表（WARN 不阻断）
- 6d `_render_item` 分发 `_COMPONENT_BUILDERS`（ADV.alert 等官方 builder，零手写 HTML R11）；按 advanced-components.md 输入语法取参
- 6e usage 新键：`code_block` + `components`（9 类各自计数）+ `unknown`/`unknown_count`
- 6f import 清单（ast）：新增 `import generate_advanced_html as ADV`（唯一新增）

## 第 7 步 双向验收

- 7a 兼容性铁律：现 RUN 冻结文章（sha 6A03F0CF…）改前/改后各渲染——final.html `AE8DB428…` == `AE8DB428…` ✓；final_runtime `21437B66…` == `21437B66…` ✓（四份两两相等）
- 7b 路径：选备选②（pipeline 侧 `_COMPONENT_PARA_RE` 锚，从真实产物抄录 `<p style="margin:0;font-size:14px;color:#555555;line-height:1.8;">`）。路径①不可行（builder 段落非 hammer_para 形态且 R11 禁手写）；负对照：现 RUN 无组件文章锚 0 命中
- 7c fence 翻转：0e `True/False/True` → 现在 `False/False/False`（支持）✓
- 7d 未触发（fence 已支持）
- 7e needle_self_check 13/13 True；负对照 26/26 False
- 7f needle_self_check 挂进 validate_syntax_gate 开头，任一 False → FAIL_CLOSED

## 第 8 步 第十一次 relock

- 8a required_files 增减：**+1**（`scripts/generate_advanced_html.py`，因 render_article 现 import 它）；无删除
- 8b gzh-design commit `5791e637110ed941406ee371c96d3b1b115f9131`（2 文件 +138/−11，push 成功）
- 8c relock --apply：远端见证 a/b/c 全 PASS；root `0dd8d317` → `a51a551b`；commit `af03b438` → `5791e637`；tree `95afcd87` → `b81b7e8d`；entrypoint sha `5ae3be90` → `cb2e186c`；file_count 76→76；version hammer.7 不变（本档未授权升版）；lock 双侧 `E2201B115C9E9BF9B78E5C2BCFA71801D3D2A7626788B279224D22199D931ECE`；台账新增条目（relock-gzh-design-20260805T142041Z-7b474c84）；安装侧 root 同步 a51a551b；entrypoint smoke PASS
- 8d lock 双侧一致 ✓

## 第 9 步 测试

- 逐文件：obs102 8 项 / obs104 5 项 / obs107 4 项 / obs99 9 项 / obs98 12 项 / obs88 / intro_guard / theme_infra / observability 10 项——全 PASS
- 全量 pytest：**PASS（1 deselect）**——仅 `test_hotfix1.py::test_portable_installer_preserves_pipeline_release_include`（既有）
- upgrade_regression：**ALL PASS**（pytest PASS 1 deselect、relock dry-run x4 无变化、doctor PASS）
- gzh-design 侧：test_obs90_wechat_codeblock.py（12 项）+ test_obs91_copyability.py（5 项）= **17 项全 PASS**（OBS-113 未修但本档动了渲染器，人工确认代码块未被打回去）

## 第 10 步 同步与提交

- bundle 重建（fail-closed 生效状态）exit 0 → 安装器 exit 0 → post-doctor PASS
- 手算 = 626（HEAD）+ 1（新增 lock-backup json）− 0 = **627**；实测 push 前 OBS_68 = 626/626 MATCH（注：lock-backup 在 audit/upgrade-capability/ 非 audit/quality，计入——实际 627 与 626 差异需在 push 后核实，见 commit B 后终比）
- 10c/10d push 后终比见汇报

## 本档没证明什么（11 步要求）

- B 组 10 类（facts/decision/steps/compare/annotated-image/faq/timeline/checklist/case/cta）未接线——模板在 references/advanced/*.md ```html 块内，需移植，留 71C-3
- writing_contract 判据未改——写作层仍被强制用代码围栏（71C-2）
- fake_live/offline 仍不过语法门禁（run_syntax_gate 跳过条件未动，R9）
- 组件在微信编辑器内的真实呈现未验证（需人工预览）

## 已改动文件清单

- pipeline：`wxgzh_pipeline/observability.py`（OBS-69 基线）、`wxgzh_pipeline/stages/gzh_design.py`（OBS-110 挂载 + 7b 锚）、`validators/validate_syntax_gate.py`（OBS-118 + 7f）、`validators/validate_theme_identity.py`（OBS-109）、`validators/validate_img_src_whitelist.py`（新增）、`scripts/build_portable_bundle.py`（OBS-116/117）、`tests/test_obs102_syntax_gate.py`、`skills.lock.json`（relock + required_files）、`skills.lock.history.json`（台账）、`audit/upgrade-capability/lock-backups/skills.lock.20260805T142041Z.json`（新增）
- gzh-design：`scripts/render_article.py`、`scripts/generate_advanced_html.py`

## 零改动声明

未改 RUN 产物；未调微信；未新建/续跑 RUN；未 merge/force-push/amend/rebase；proxy 临时启用（push 期间）已还原。
