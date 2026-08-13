# 档 71B：让静默变可见（OBS-102 语法门禁 + OBS-104 围栏内容留痕 + OBS-107 同步基线排除）

- 日期：2026-08-05
- 范围：wxgzh-pipeline 仓（validators/ + wxgzh_pipeline/ + tests/ + audit/）；零 relock；gzh-design 仓零改动

## 第 0 步 前置自检（全部 PASS）

- doctor `--require-wechat`：PASS；四锁 hash_ok 全 true（super-writer `46a00a1b` / zh `18491b36` / media `181752eb` / gzh-design `0dd8d317`）
- skills.lock.json 双侧：`0CD0EBC35CF516BD0BD74DA515C74D50F929948F1D0E1FDD772D80D56C6B1CF9`
- pipeline HEAD：`c4b9d1a9a75745eb8ff5f133d93b99a64a3110b7`，status 空
- gzh-design HEAD：`af03b438a37233c111a20be77c4fd28898dc8f10`，status 空
- OBS_68 现值（修复前）：**650/648 DIFF**（缺 `obs106-advanced-components-71a.md`、`obs99-cover-path-70.md`）

## 第 1 步 取证 A：img src 白名单门禁（穷举）

**结论句式：final.html 的 `<img src>` 【无】白名单门禁。**

命中点逐项判定：
- `gzh-design/scripts/publish_wechat_draft.py` L55-69 `normalize_wechat_image_url`：仅校验 **uploadimg 接口返回值**（L208 `url = normalize_wechat_image_url(data["url"])`）是否为微信图床 URL——不扫描 final.html 内容
- `wxgzh-pipeline/validators/validate_media_bindings.py` L18-26 `_exact_wechat_url`：校验 **bindings remote_url**，非 final.html 的 img
- `gzh-design/scripts/validate_gzh_html.py`：FORBIDDEN 13 条 + id 属性 + href="#" + 中文引号 + PLACEHOLDER_PATTERNS 5 类（`{{...}}`/`[编辑锚点`/`TODO`/`待补`/`需要补充`）+ leaf 包裹 + 半角标点——**无任何 `<img src>` 判定**；PLACEHOLDER 不匹配 `../assets/`
- `wxgzh-pipeline/validators/validate_delivery.py`：只查 final_delivery.json / stage_receipt / MANIFEST 哈希
- `gzh-design/scripts/make_b_docs.py` L71-72：文档声明（非代码门禁）；`make_review_zip.py` L91-112：仅自检相对路径存在性
- 组件模板默认 `../assets/*.png` 可原样流入 final.html 无拦截（归 71C）

## 第 2 步 取证 B：OBS_68 计数比对实现定位

**有固化实现**：
- `wxgzh_pipeline/observability.py` L105-135 `check_pipeline_consistency`（判据：`_runtime_files` 用 `zipping._skip` 排除规则，双侧相对路径集合差集 + 字节 sha 比对）
- `wxgzh_pipeline/orchestrator.py` L156 挂接输出 `OBS_68_PIPELINE_MATCH`（doctor observability 块）

## 第 3 步 修 OBS-107（路 A：在固化实现处加排除）

- `wxgzh_pipeline/observability.py`：新增 `REPORT_DOC_EXCLUDE_PREFIX = ("audit", "quality")` + `_is_report_doc(rel)`（仅 `audit/quality/**/*.md`，`audit/runs/` 严禁排除）+ `_runtime_files` 过滤
- 注释写明理由：报告是审计产物、不是运行资产；「核验先跑、报告后写」是必然时序，不排除则形成「同步 → 产生新报告 → 又不一致」无限递归
- 未改 install.py 拷贝范围（audit/ 仍整体拷贝）；排除为显式常量 + 前缀判定，非正则通配 audit/ 全目录

## 第 4 步 门禁 1：未支持语法（probe 判据，阻断型）

- 新文件：`validators/validate_syntax_gate.py`（catalog 10 类 + probe + validate）；`wxgzh_pipeline/validators_syntax.py`（桥接：定位渲染器、RUN 内 probe/cache）
- 挂载：`wxgzh_pipeline/stages/gzh_design.py` content_validate 开头（渲染后、现有校验前）；fake_live/offline 跳过（shim 渲染会失真，门禁只在真实路径生效）
- probe 判据：每类语法生成最小样本（H1 + ## + 语法 3-5 行 + 哨兵），CLI 子进程调安装侧渲染器；不支持 = ① 控制符原样出现在可见文本 或 ② 哨兵未完整出现在正文区（正文区口径复用 `gzh_design._body_plain_text`，同源）
- 10 类 probe 结果：**全部不支持**（fence/h3 哨兵被丢弃；其余控制符原样输出）
- probe 结果按「渲染器 sha256 + catalog v1」缓存到 RUN 目录 `.obs102-probe-cache.json`；禁止跨 RUN 复用
- 免悖论声明（代码注释 + 本报告）：判据来自 probe，71C 接线后 probe 自动放行 `:::`；无跨仓硬编码期望值（避免 OBS-98 形状）
- **4f 现 RUN 零影响验证：冻结文章（sha 6A03F0CF…38999）→ PASS，hits=0** ✓

## 第 5 步 门禁 2：围栏内容非代码（提示型，绝不阻断）

- 新文件：`validators/validate_fence_content.py`（classify_fence_block + scan_fences + write_allowance）
- 三条判据：① 非 ASCII > 40% 且无代码标记符（标记符集合逐字：`= { } ; ( ) $ -- -> :: #! import def class function sudo rm git pip npm curl`）；② 行首提示图标（⛔ ⚠️ ✅ ❌ 📌 💡 🚫）；③ 语言标签在 {bash,sh,zsh,shell,python,py,js,ts,json,yaml,sql} 且块内零该语言标记符
- 行为：WARN + 强制写 `allowance_record.json`（rule=`fence_content_not_code`，含块序号/语言标签/判据编号/前 3 行）；退出码恒 0
- 悖论检查：writing_contract 仍要求 16 行在代码围栏内；本门禁只提示不阻断 → 不构成不可满足集合；本档不改 writing_contract 判据（载体改造与接线同档 = 71C）
- **5d 实测**：bash 块（16 行护栏文案）命中 ①②③ → 1 条 WARN + 1 条留痕；text 块（2 行 /plugin）零命中 ✓

## 第 6 步 文案修正

- 6a. `wxgzh_pipeline/writing_contract.py` 模块 docstring：「8 deny + 7 ask」→「实测 16 条，至少 MIN_DENY_ASK_COVERAGE 条必须逐字进入文章」（不写死条数）
- 6b. `validators/validate_theme_identity.py` `_style_decl` docstring：「逗号/分号分隔均支持」→「仅按分号分隔」（与实现一致；改实现属行为变更，留独立档）
- 6c. 对 71A′ 报告的两条更正（登记于此，不改那份报告文件）：
  ① 附录 A 前言写 docs/*（8），实为 9 项（all-themes.md + gallery 8 份）；76 项清单本身正确
  ② §12「Stage B 十个组件在 generate_advanced_html.py 中存在」不成立：COMPS 只有 9 键，B 组无 builder，其 HTML 模板在 references/advanced/*.md 的 ```html 块内

## 第 7 步 测试

- `tests/test_obs102_syntax_gate.py`（5 项）：现 RUN PASS / :::alert FAIL 报行号 / ### FAIL / 引用+列表 FAIL / 正文区口径同源断言 —— 全 PASS
- `tests/test_obs104_fence_content.py`（4 项）：16 行命中 ②③ + 留痕 / 真 bash 零命中 / /plugin 零命中 / 无 suspect 不写留痕 —— 全 PASS
- `tests/test_obs107_install_sync.py`（4 项）：报告排除判定 / 新增报告仍 MATCH / 新增运行资产 DIFF / 仅 quality 排除 —— 全 PASS
- 全量 pytest：仅 1 项既有 deselect（`test_hotfix1.py::test_portable_installer_preserves_pipeline_release_include`，档 30/31 判定项，无新增）
- upgrade_regression：**ALL PASS**（relock dry-run x4 无变化；doctor --require-wechat PASS）

## 第 8 步 同步与提交

- bundle 重建（build 校验常量 `EXPECTED_PIPELINE_FILE_COUNT` 为档 30/31 既有已知过时项，staging 已写入新代码）→ 安装器实装成功 → post-doctor PASS
- **8c 计数比对（push 前）：OBS_68 = MATCH（621/621）**——报告类排除生效，此前 650/648 的 2 份报告不再计入
- lock 双侧仍 `0CD0EBC3…`（零 relock）
- 8g push 后计数比对：见汇报（i 项）

## 已改动文件清单

- `wxgzh_pipeline/observability.py`（OBS-107 排除）
- `wxgzh_pipeline/validators_syntax.py`（新增，门禁 1 桥接）
- `wxgzh_pipeline/stages/gzh_design.py`（门禁 1 挂载）
- `wxgzh_pipeline/writing_contract.py`（6a docstring）
- `validators/validate_syntax_gate.py`（新增，门禁 1）
- `validators/validate_fence_content.py`（新增，门禁 2）
- `validators/validate_theme_identity.py`（6b docstring）
- `tests/test_obs102_syntax_gate.py` / `test_obs104_fence_content.py` / `test_obs107_install_sync.py`（新增）
- `audit/quality/obs102-visibility-gates-71b.md`（本报告）

## 零改动声明

未改 gzh-design 任何文件；未 relock；未改 RUN 产物与冻结文章；未调微信；未新建/续跑 RUN；未合并/force-push/amend/rebase。唯一写入 = wxgzh-pipeline 仓 + bundle/安装侧同步产物 + `.temp\obs102-probe\`。

## 未覆盖与不确定项

- 未覆盖：门禁 1 在真实 live 续跑中的端到端执行（本档未续跑 RUN；probe 已在安装侧渲染器实测）
- 未覆盖：71C 接线后 probe 对 `:::` 的自动放行（设计已声明，实测留 71C）
- 未覆盖：img src 白名单门禁（71A′ 第 1 步结论：无门禁；本档只取证不新增，归 71C）
- build_portable_bundle.py 的 EXPECTED_PIPELINE_FILE_COUNT=130 过时项仍为发布工程遗留（档 30/31 判定），未动
