# 档 71B′-C：OBS-111 正文区口径 + probe 针体同归一化 + OBS-112 去绝对路径 + OBS-65 动态实算

- 日期：2026-08-05
- 范围：wxgzh-pipeline 仓；零 relock；gzh-design 仓零改动

## 第 0 步 前置自检（PASS，复述已完成结论）

- doctor `--require-wechat` PASS，四锁 hash_ok 全 true（root 前 8 位：super-writer `46a00a1b` / zh `18491b36` / media `181752eb` / gzh-design `0dd8d317`）
- lock 双侧 `0CD0EBC35CF516BD0BD74DA515C74D50F929948F1D0E1FDD772D80D56C6B1CF9`
- pipeline HEAD `2cd3fd79…`（干净）；gzh-design HEAD `af03b438…`（干净）
- OBS_68 621/621 MATCH（基线已排除 audit/quality/**/*.md）

## 第 1 步 取证（复述）

- 1a `_body_plain_text` 唯一调用点：`wxgzh_pipeline/stages/gzh_design.py:152`（`_intro_content_fidelity`），判定 = **包含判定**（`if norm not in body`）——非等值/计数/长度
- 1b 深色代码块第一行 `<p` 开标签原文：
  `<p style="margin:0;font-family:'SF Mono',Consolas,Monaco,monospace;font-size:13px;line-height:1.6;color:#E2E8F0;">`
- 1c `#E2E8F0` 共 **18 次**，全部在 18 个代码行 `<p>` 标签内（SF Mono/Consolas 双特征）；顶栏/语言标签/其他 = 0
- 1d `_PARA_RE`=15、`_PRE_RE`=0

## 第 2 步 OBS-111（已完成 + 3C-a 复验）

- `_CODE_ROW_RE` 以 1b 开标签为锚（SF Mono + #E2E8F0 双特征）；`_body_plain_text` = `_PARA_RE ∪ _CODE_ROW_RE ∪ _PRE_RE`（并集）；`_PRE_RE` 保留注释「兼容 67D 之前历史产物，当前命中 0」
- 2d：**18/18 命中**（bash 16 + text 2）；2e：改造前后 INTRO_GUARD 均 PASS

### 3C-a 抽函数复验

- `_normalize_text(s)` = 去标签 `re.sub(r"<[^>]+>","",s)` → `html.unescape` → `_WS_RE.sub("", …)`（与旧三步逐字一致）；`_body_plain_text` 内部调用
- 复验：2d 仍 **18/18**；2e 改造后 INTRO_GUARD **PASS**

## 第 3C 步 probe 13 类重做

### 3C-b/3C-c 落地

- CATALOG 每类含 `token`（报告/负对照诊断）与 `needle`（判定针，同归一化形态）；13 类逐字清单见 `validators/validate_syntax_gate.py`（code_fence / fence / h3 / quote / ulist / ulist_star / olist / table / bold / strike / inline_code / fn_ref / fn_def + baseline）
- ARTICLE_SCAN 拆分（OBS-115）：`r"^[-*]\s+"` → `r"^-\s+"` + `r"^\*\s+"`；`r"\*\*|~~"` → `r"\*\*"` + `r"~~"`
- fixtures：`tests/fixtures/obs102/current_run_final_article.md`（sha256 6A03F0CF…38999）、`stub_renderer_supports_fence.py`、`tests/fixtures/obs104/guard16_real.txt`

### 3C-d 针体自检（13 项全 True）

| key | needle | self_match |
|---|---|---|
| code_fence | ``` | True |
| fence | ::: | True |
| h3 | ### | True |
| quote | > | True |
| ulist | -SENTINEL_A1 | True |
| ulist_star | *SENTINEL_A1 | True |
| olist | 1.SENTINEL_A1 | True |
| table | \|SENTINEL_A1 | True |
| bold | ** | True |
| strike | ~~ | True |
| inline_code | ` | True |
| fn_ref | [^1] | True |
| fn_def | [^1]: | True |

### 3C-e 负对照（26 项全 False）

baseline 正文归一化文本 = `这是导语占位段落，不含任何控制符。SENTINEL_A1结尾普通段落。`——13 token 与 13 needle 全部不出现。

### 3C-f 十三类三值（实测 vs 预期，全部一致）

| 类 | ctrl_visible | sentinel_missing | html_len | 预期 | 判定 |
|---|---|---|---|---|---|
| code_fence | False | False | 10136 | (F,F) | ✓ 支持 |
| fence | True | False | 9612 | (T,F) | ✓ |
| h3 | False | True | 9078 | (F,T) | ✓ |
| quote | True | False | 9254 | (T,F) | ✓ |
| ulist | True | False | 9254 | (T,F) | ✓ |
| ulist_star | True | False | 9254 | (T,F) | ✓ |
| olist | True | False | 9255 | (T,F) | ✓ |
| table | True | False | 9436 | (T,F) | ✓ |
| bold | True | False | 9256 | (T,F) | ✓ |
| strike | True | False | 9256 | (T,F) | ✓ |
| inline_code | True | False | 9254 | (T,F) | ✓ |
| fn_ref | True | False | 9263 | (T,F) | ✓ |
| fn_def | True | False | 9258 | (T,F) | ✓ |

四类正文区归一化文本原文（3C-f 物证）：
- ulist：`这是导语占位段落，不含任何控制符。-SENTINEL_A1SENTINEL_A2结尾普通段落。`
- ulist_star：`…*SENTINEL_A1SENTINEL_A2…`
- olist：`…1.SENTINEL_A1SENTINEL_A2…`
- strike：`…~~SENTINEL_A1~~SENTINEL_A2…`

四类物证与布尔结论自洽（S14 不触发）。

### 3C-h 现 RUN 复测

- 逐类命中：code_fence=4（L21/38/48/51）、其余 12 类=0
- 门禁 **PASS（exit 0）**，problems=[]——实心绿灯（命中且受支持）

## 第 4 步 免悖论可执行用例

- 正向（stub 渲染器）：exit 0 / PASS / fence unsupported=False
- 反向（真实渲染器）：exit 1 / FAIL / problems[0]={"category":"::: 围栏","line":5,"snippet":":::alert type=\"warn\"","probe_reason":"① 语法控制符原样出现在正文区文本"}
- **4d 两句话**：本用例证明「门禁机制在渲染器支持后会放行」；它**不**证明「71C 的组件输出一定落进正文区口径」。71C 强制交付项：组件正文段落必须进入正文区口径，验收判据 = fence 类 probe 实测由「不支持」转「支持」。

## 第 5 步 OBS-112 去绝对路径

- 现 RUN 文章冻结为 fixture（sha256 断言）；删除 F:\ 硬编码与模块级 assert；渲染器经 skill_discovery 定位，不可得则 skip；RUN 文章优先 `WXGZH_OBS102_RUN_ARTICLE` 环境变量
- 本机实测：**6 项跑 / 0 项 skip**（安装侧渲染器与 fixture 均可得）

## 第 6 步 OBS-104 真实样本

- `guard16_real.txt` 冻结（16 行）；断言 `criteria_hit` 至少含 {1,2,3}——实测 criteria_hit=**[1,2,3]**（6b 验收达成）
- 合成样本测试改名 `test_obs104_synthetic_guard_lines_hit_2_and_3`，docstring 标注「合成样本，非 RUN 真实数据」
- 6d 更正：71B 报告 §5/§7 正确报法 =「命中 ①②③（断言写为至少含 ②③）」；登记审核方缺陷第 54 处（16 行全中文零代码标记符，必然命中判据①）

## 第 7 步 文案与死代码

- 7a `observability.py` docstring 删「564 files」，改描述性（基线 = runtime 集合 − audit/quality/**/*.md，数值随仓库演进）
- 7b `validators_syntax._renderer_path(skills_home)` 删 fake_live/offline 死分支；注释「fake_live 是否纳入门禁 = 独立议题，71C 之后单列」；跳过条件未动

## 第 8 步 OBS-65

- 8a 取证：常量 `EXPECTED_PIPELINE_FILE_COUNT=130` vs 实算 **660**（差额 530，严重过时）
- 8b 动态实算（删除写死常量）；8c 先「实算+打印」→ 第 10 步实测一致（660/1228/1230）→ 启用 fail-closed；8d fail-closed 下构建 exit 0（校验公式：manifest == bundle_zip − 2，两个 MANIFEST.json 自排除）

## 第 9 步 测试

- 逐文件：test_obs102_syntax_gate.py **7 项全 PASS**（含 3C-d 自检、3C-e 负对照、4c 两向、现 RUN PASS/命中）；test_obs104_fence_content.py **5 项全 PASS**（含真实样本）；test_obs107_install_sync.py 4 项全 PASS
- 全量 pytest：全部通过，仅 1 项既有 deselect（`test_hotfix1.py::test_portable_installer_preserves_pipeline_release_include`）
- upgrade_regression：**ALL PASS**

## 第 10 步 同步与提交

- 10a bundle 重建（enforce=True 下 exit 0）→ 安装器 exit 0 → post-doctor PASS
- 10b 手算：621 + 3（新增 fixture 3 个，0 个 audit/quality）− 0 = **624**；实测 **624/624 MATCH** ✓
- 10c push 后复测：见汇报 n 项
- commit message：`fix(obs111/obs112/obs114/obs115): 正文区口径纳入代码块形态 + probe 针体与测量域同归一化并加可匹配性自检 + 拆分并集扫描正则 + 回归测试去绝对路径`

## 新登记

- **OBS-113（中）**：gzh-design 仓 `tests/test_obs90_wechat_codeblock.py`（blob 509ce62f…）与 `tests/test_obs91_copyability.py`（blob 64e9adc9…）存在，但 `skill_discovery.EXCLUDE_DIRS` 含 "tests"，不受哈希保护、不随安装拷贝、不在 pipeline 侧执行路径 → 「可复制性由自动化回归承载」仅在该仓手动执行时成立；跨仓修复单列一档，本档只登记
- **OBS-114（高）**：探针针体无可匹配性自检——不可匹配的针恒产出「支持」；本档实例 = ulist/olist 的 token 含空格而测量域删除全部空白；通用修法 = R9（针与文本同归一化 + 针体自检），已固化为 pytest 用例
- **OBS-115（中）**：ARTICLE_SCAN 并集正则（r"^[-*]\s+"、r"\*\*|~~"）让未测形态借用已测形态结论；本档已拆分并补 ulist_star / strike
- **审核方缺陷第 55 处**：71B′ 的 3d（测量域改归一化正文区）与 3c（沿用含空格 ctrl）内在矛盾——本档以 C 方案修复（needle 同归一化 + 哨兵锚定）

## 已改动文件清单

- `wxgzh_pipeline/stages/gzh_design.py`（OBS-111：_CODE_ROW_RE + 并集 + _normalize_text 抽函数）
- `wxgzh_pipeline/validators_syntax.py`（7b 简化 _renderer_path）
- `wxgzh_pipeline/observability.py`（7a docstring）
- `validators/validate_syntax_gate.py`（3C：13 类 token/needle + 拆分 + 针体自检）
- `scripts/build_portable_bundle.py`（OBS-65：动态实算 + fail-closed）
- `tests/test_obs102_syntax_gate.py`、`tests/test_obs104_fence_content.py`（去绝对路径 + 真实样本）
- `tests/fixtures/obs102/current_run_final_article.md`、`stub_renderer_supports_fence.py`（新增）
- `tests/fixtures/obs104/guard16_real.txt`（新增）
- `audit/quality/obs111-body-scope-71bprime.md`（本报告）

## 零改动声明

未改 gzh-design 任何文件；未 relock；未改 RUN 产物（fixture 为只读复制）；未调微信；未新建/续跑 RUN；未清理任何目录；未 merge/force-push/amend/rebase。

## 未覆盖项

- 71C 接线后 fence probe 实测转「支持」的端到端（本档仅 stub 验证机制）
- fake_live 是否纳入语法门禁（独立议题，71C 后单列）
- OBS-113 的跨仓修复（单列一档）
- 审核方缺陷第 54 处（16 行全中文必然命中判据①）已登记，未改判据
