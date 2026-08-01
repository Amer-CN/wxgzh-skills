# 档 26 — 升级能力改造·只读勘察(survey-26)

日期:2026-08-01
模式:只读勘察(除本报告外零写入;未重锁、未跑 Pipeline、未调微信接口)
工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(HEAD 见下)
勘察对象:安装副本 `F:\AIXM\wxgzh\.agents\skills`(doctor 已确认四锁定 skill hash_ok=true)

> 说明:下面每一项的「是否在四个被锁 skill 的 runtime manifest 内」,
> manifest 指 skills.lock.json 中每个 skill 的 runtime 文件集
> (super-writer=50 / zh-human-writing=53 / media-enrichment=57 / gzh-design=76,
> 由 `skill_discovery._runtime_files` 计算,排除
> .git/.github/tests/__pycache__/WXGZH_PIPELINE_INTEGRATION.md/.gitignore/.gitattributes/*.pyc)。

---

## 1. receipts.py 恢复时重算 skill root 的代码

- 完整路径:`F:\AIXM\wxgzh\repos\wxgzh-pipeline\wxgzh_pipeline\receipts.py`
- 在 gzh-design 的 76 文件 runtime manifest 内?**否**。该文件属于 Pipeline 自身
  (`wxgzh_pipeline/` 包),不属于任何被锁子 skill 的树,四个 manifest 均不含它。
- 档 21 记录的 :222-228 落在 `verify_receipt` 函数内(L139-230)。函数完整源码:

```python
139: def verify_receipt(run_dir: Path, stage: str, skills_home: Path | None = None,
140:                    network_mode: str | None = None) -> tuple[bool, list]:
141:     """Tamper detection (P0#1/#2/#3). Starts with FULL structural validation
142:     (validate_receipt), then verifies identity + per-mode expectations, then
143:     recomputes EVERY recorded hash from disk. Empty receipts, deleted fields,
144:     deleted hash entries, and missing files are all FAIL — never a skip."""
145:     r = load_receipt(run_dir, stage)
146:     if not r:
147:         return False, ["receipt missing or empty"]
148:     mism = list(validate_receipt(r))  # structural first (P0#1)
149:     sd = Path(run_dir) / stage
150:
151:     # identity: receipt must belong to THIS stage/skill and (if given) this mode
152:     from .execmodel import (STAGE_EXEC, STAGE_SKILL, EXPECTED_OUTPUTS,
153:                             AGENT_VALIDATORS, SUBPROC, WECHAT)
154:     if r.get("stage") != stage:
155:         mism.append(f"stage mismatch: receipt.stage={r.get('stage')} != {stage}")
156:     if r.get("skill_name") != STAGE_SKILL.get(stage):
157:         mism.append(f"skill mismatch: receipt.skill_name={r.get('skill_name')} != {STAGE_SKILL.get(stage)}")
158:     rmode = r.get("network_mode")
159:     if network_mode is not None and rmode != network_mode:
160:         mism.append(f"network_mode mismatch: receipt={rmode} != current={network_mode}")
161:
162:     real_exec = rmode in ("fake_live", "live")
163:     # executable stages MUST record their entrypoint (real execution modes)
164:     if real_exec and STAGE_EXEC.get(stage) in (SUBPROC, WECHAT):
165:         if not r.get("entrypoint_path") or not r.get("entrypoint_sha256"):
166:             mism.append("executable stage missing entrypoint_path/entrypoint_sha256")
167:     # stages that declare official validators MUST carry complete records
168:     if real_exec:
169:         if stage in ("media_enrichment", "gzh_design") and not r.get("official_validator"):
170:             mism.append(f"{stage}: official_validator missing")
171:         if AGENT_VALIDATORS.get(stage) and len(r.get("official_validators") or []) < len(AGENT_VALIDATORS[stage]):
172:             mism.append(f"{stage}: official_validators incomplete "
173:                         f"({len(r.get('official_validators') or [])}/{len(AGENT_VALIDATORS[stage])})")
174:
175:     # expected contract outputs must all be covered by output_hashes
176:     missing_expected = [o for o in EXPECTED_OUTPUTS.get(stage, [])
177:                         if o not in (r.get("output_hashes") or {})]
178:     if missing_expected:
179:         mism.append(f"expected outputs not covered by output_hashes: {missing_expected}")
180:
181:     # inputs — full-path keyed; recorded None means it was missing at run time
182:     for path_str, want in (r.get("input_hashes") or {}).items():
183:         p = Path(path_str)
184:         cur = sha256_file(p) if p.is_file() else None
185:         if want is None:
186:             mism.append(f"input was missing at run time: {path_str}")
187:         elif cur is None:
188:             mism.append(f"input missing now: {path_str}")
189:         elif cur != want:
190:             mism.append(f"input hash mismatch: {path_str}")
191:
192:     # outputs — must exist and match
193:     for name, h in (r.get("output_hashes") or {}).items():
194:         p = sd / name
195:         if not p.is_file():
196:             mism.append(f"output missing: {name}")
197:         elif sha256_file(p) != h:
198:             mism.append(f"output hash mismatch: {name}")
199:
200:     # entrypoint / pipeline validator — recorded path+sha must both exist AND match
201:     for label, path_key, sha_key in [("validator", "validator_path", "validator_sha256"),
202:                                      ("entrypoint", "entrypoint_path", "entrypoint_sha256")]:
203:         p, want = r.get(path_key), r.get(sha_key)
204:         if p and want:
205:             if not Path(p).is_file():
206:                 mism.append(f"{label} script missing: {p}")
207:             elif sha256_file(Path(p)) != want:
208:                 mism.append(f"{label} hash mismatch")
209:
210:     # official sub-skill validator(s) — same strictness
211:     officials = list(r.get("official_validators") or [])
212:     if r.get("official_validator"):
213:         officials.append(r["official_validator"])
214:     for ov in officials:
215:         p, want = ov.get("path"), ov.get("sha256")
216:         if p and want:
217:             if not Path(p).is_file():
218:                 mism.append(f"official_validator script missing: {p}")
219:             elif sha256_file(Path(p)) != want:
220:                 mism.append("official_validator hash mismatch")
221:
222:     # sub-skill root sha (live only — installed skill must still match the receipt)
223:     if skills_home and r.get("network_mode") == "live" and r.get("skill_root_sha256"):
224:         from .skill_discovery import compute_root_sha
225:         skill_dir = Path(r.get("skill_dir") or (Path(skills_home) / r.get("skill_name", "")))
226:         cur, _ = compute_root_sha(skill_dir)
227:         if cur != r["skill_root_sha256"]:
228:             mism.append("skill_root_sha256 mismatch (installed sub-skill changed)")
229:
230:     return (not mism), mism
```

---

## 2. skill_discovery.py::compute_runtime_manifest_sha

- 完整路径:`F:\AIXM\wxgzh\repos\wxgzh-pipeline\wxgzh_pipeline\skill_discovery.py`
- 在四个被锁 skill 的 runtime manifest 内?**否**。Pipeline 自身文件。
- 完整源码(L67-72;依赖的 `_runtime_files` 在 L43-56):

```python
 67: def compute_runtime_manifest_sha(root: Path) -> tuple[str | None, list[str]]:
 68:     """Hash of the runtime FILE LIST itself (which files count as runtime)."""
 69:     if not Path(root).is_dir():
 70:         return None, []
 71:     rels = [p.relative_to(root).as_posix() for p in _runtime_files(root)]
 72:     return hashlib.sha256("\n".join(rels).encode("utf-8")).hexdigest(), rels
```

```python
 43: def _runtime_files(root: Path) -> list[Path]:
 44:     out = []
 45:     for p in Path(root).rglob("*"):
 46:         if not p.is_file():
 47:             continue
 48:         if any(part in EXCLUDE_DIRS for part in p.parts):
 49:             continue
 50:         if p.name in EXCLUDE_FILES or p.suffix in EXCLUDE_SUFFIXES:
 51:             continue
 52:         out.append(p)
 53:     # sort by POSIX relpath (NOT Path objects) so the order is identical on
 54:     # Windows and Linux — os-separator sorting would flip subdir ordering and
 55:     # change the aggregate root hash even when every file hash matches (P0#9 CI).
 56:     return sorted(out, key=lambda p: p.relative_to(root).as_posix())
```

- 佐证:对安装副本 `F:\AIXM\wxgzh\.agents\skills\gzh-design` 实算
  `ced841439195453497e67a63186823f60eee7155b9de472e936c3d4d767e33b2 / 76 文件`,
  与 skills.lock.json 中 gzh-design 的 `runtime_manifest_sha256` 一致(只读计算)。

---

## 3. skills.lock.json 的生成方式

- 路径:`F:\AIXM\wxgzh\repos\wxgzh-pipeline\skills.lock.json`(Pipeline 仓库根)。
- **不存在现成的生成脚本**。全仓检索结论:
  - 没有代码写入该文件。`scripts/install.py` 只读它(L219/290 校验、L340/373 构建
    内存 dict 传给 `verify_all`,不落盘);`scripts/build_portable_bundle.py` L158 仅
    `shutil.copyfile` 复制;测试仅向临时目录写伪造 lock;`scripts/run_cross_repo_integration.py`
    只计算哈希并记录到输出 JSON。
- 实际历史:
  - 初始版本随 `ef5b0ef chore: seed wxgzh-pipeline 0.1.0-dev1 baseline (main)` 手工写入
    (lock_version=1,4 个 skill,69 行);aihot 条目与 lock_version=2 在后续提交加入。
  - 历次「re-lock」均为**手工编辑 JSON 后提交**:`fa67cdf`、`57443ad`、`261a016`、
    `4c6416d` 等 commit 只改 `skills.lock.json`(+审计说明)。
  - 哈希值由 Pipeline 自带函数计算:`compute_root_sha()` / `compute_runtime_manifest_sha()`
    / `_file_sha()`(obs42 的 re-lock 记录明确写明
    "Official algorithm: wxgzh_pipeline.skill_discovery.compute_root_sha() and _file_sha()")。
- 结论:**手工写入/手工编辑**;值由 Pipeline 代码函数算出后抄入 JSON;无现成脚本。

---

## 4. doctor.py 中执行 hash 校验、产出 skills_locked_ok 的代码段

- `scripts/doctor.py` 是薄 CLI(L1-33),真正校验在 orchestrator + skill_discovery:

```python
 19: def main(argv=None):
 20:     ap = argparse.ArgumentParser()
 21:     ap.add_argument("--project-root", default=None)
 22:     ap.add_argument("--require-wechat", action="store_true")
 23:     ap.add_argument("--offline", action="store_true")
 24:     a = ap.parse_args(argv)
 25:     orch = Orchestrator(project_root=a.project_root,
 26:                         network_mode="offline_fixture" if a.offline else "live")
 27:     ok, report = orch.doctor(require_wechat=a.require_wechat or None)
 28:     print(json.dumps(report, ensure_ascii=False, indent=2))
 29:     return 0 if ok else 1
```

- `wxgzh_pipeline\orchestrator.py` L53-59(live 分支)与 L106-140(doctor 汇总):

```python
 53:     def _verify_skills_for_mode(self):
 58:         if self.network_mode == "live":
 59:             return SD.verify_all(self.skills_home, self.lock)
```

```python
106:     def doctor(self, require_wechat: bool | None = None) -> tuple[bool, dict]:
107:         if require_wechat is None:
108:             require_wechat = (self.network_mode == "live")
109:         ok_skills, disc = self._verify_skills_for_mode()
...
124:         report = {
125:             "wxgzh_pipeline_version": __version__, "project_root": str(self.project_root),
126:             "skills_home": str(self.skills_home), "network_mode": self.network_mode,
127:             "skills_locked_ok": ok_skills, "skills": disc,
...
135:         ok = ok_skills and writable and aihot_ok and (wechat_ok or not require_wechat)
136:         if self.network_mode == "live":
137:             ok = ok and live_pipeline_allowed
138:         report["FAIL_CLOSED"] = not ok
139:         report["doctor"] = "PASS" if ok else "FAIL"
140:         return ok, report
```

- `wxgzh_pipeline\skill_discovery.py` L253-270(单 skill hash 判定)与 L287-290(汇总):

```python
253:         root = Path(skills_home) / name
254:         exists = root.is_dir()
255:         cur_sha, nfiles = compute_root_sha(root) if exists else (None, 0)
256:         cur_ver = _read_version(root, name) if exists else None
257:         version_ok = exists and cur_ver == locked.get("skill_version")
258:         hash_ok = exists and cur_sha == locked.get("skill_root_sha256")
259:         req = locked.get("required_files", [])
260:         entrypoints_ok = exists and all((root / rf).is_file() for rf in req)
261:         result[name] = {
...
265:             "file_count": nfiles, "version_ok": version_ok, "hash_ok": hash_ok,
266:             "entrypoints_ok": entrypoints_ok,
267:             "missing_files": [rf for rf in req if not (root / rf).is_file()] if exists else req,
268:             "ok": bool(exists and version_ok and hash_ok and entrypoints_ok),
269:         }
```

```python
287: def verify_all(skills_home: Path, lock: dict, env: dict | None = None) -> tuple[bool, dict]:
288:     disc = discover(skills_home, lock, env=env)
289:     ok = all(v["ok"] for v in disc.values())
290:     return ok, disc
```

- 以上文件均不在四个被锁 skill 的 runtime manifest 内(Pipeline 侧)。

---

## 5. publish_wechat_draft.py 的全部引用点

被引用对象(安装副本):`F:\AIXM\wxgzh\.agents\skills\gzh-design\scripts\publish_wechat_draft.py`
(519 行;gzh-design runtime manifest 76 文件之一,`SHA256SUMS` 记录
`5755247d3a8638f12913f103bc860b15a554085c117997bd3857479844b976f9`;
lock 的 gzh-design `required_files` 含它,且无独立 entry/validator 位——它同时是
`wechat_draft` 阶段的 entry)。

### a. Pipeline 侧引用点

| 位置 | 内容 |
|---|---|
| `wxgzh_pipeline/execmodel.py` L32-39 | `STAGE_EXEC["wechat_draft"] = WECHAT` |
| `wxgzh_pipeline/execmodel.py` L42-49 | `STAGE_SKILL["wechat_draft"] = "gzh-design"` |
| `wxgzh_pipeline/execmodel.py` L110-120 | `LIVE_ENTRY["wechat_draft"] = {skill: gzh-design, entry: scripts/publish_wechat_draft.py, validator: None}` |
| `wxgzh_pipeline/execmodel.py` L122-128 | `FAKE_ENTRY["wechat_draft"] = gzh-design/publish_wechat_draft.py`(fake_live shim) |
| `wxgzh_pipeline/execmodel.py` L150-163 | `resolve_entry()`:按模式解析真实/假 entry 路径 |
| `wxgzh_pipeline/contracts.py` L28-33 | `STAGE_LOCK_SKILL["wechat_draft"] = "gzh-design"` |
| `wxgzh_pipeline/contracts.py` L131-145 | `enforce_contract` 用 `STAGE_LOCK_SKILL` 校验 lock 身份 |
| `wxgzh_pipeline/producers.py` L11 | 模块 docstring 描述 wechat_draft 调用方式 |
| `wxgzh_pipeline/producers.py` L65-66 | `produce()` 分发:`kind == EM.WECHAT -> _wechat(...)` |
| `wxgzh_pipeline/producers.py` L822-859 | `_wechat()`:resolve_entry → 组装 `--html/--title/--audit-dir[/--cover/--dry-run]` → `run_script` 执行 → 记录 entrypoint/exit/输出 sha |
| `wxgzh_pipeline/stages/wechat_draft.py` L23-25 | `invoked_entrypoint()` 声明复用该脚本 |
| `wxgzh_pipeline/stages/wechat_draft.py` L40 | `content_validate` 用 `subskill_validator_sha(ctx,"gzh-design","scripts/publish_wechat_draft.py")` 记录 entry 哈希 |
| `wxgzh_pipeline/stages/wechat_draft.py` L59-62 | `run_live` → `produce(ctx, STAGE, state)` |
| `wxgzh_pipeline/orchestrator.py` L25-31 | `STAGE_MODULES` 注册 `wechat_draft` 模块 |
| `wxgzh_pipeline/orchestrator.py` L64-78 | integration 模式按 `STAGE_SKILL`/`resolve_entry` 校验 shim 存在 |
| `wxgzh_pipeline/orchestrator.py` L197-212 | `_drive` 按 `STAGES` 顺序执行 `execute_stage` |
| `wxgzh_pipeline/receipts.py` L152-157 | 用 `STAGE_SKILL` 核对 receipt 的 skill_name |
| `wxgzh_pipeline/stages/__init__.py` L19/L137 | `from ..execmodel import STAGE_SKILL`,执行时取 `STAGE_SKILL[stage]` |

### b. gzh-design 内部是否有其他文件 import 或调用它

- **没有任何生产代码(runtime 76 文件内)import 或调用它**;它只被 Pipeline 以 CLI
  子进程方式调用。gzh-design 内的引用全部为文档/测试/清单:
  - `RELEASE_NOTES.md:24`、`README.md:65/74`、`SKILL.md:229`(文档示例)
  - `WXGZH_PIPELINE_INTEGRATION.md:19`(集成说明;被 manifest 排除)
  - `SHA256SUMS:3`(哈希清单)
  - `tests/test_wechat_fragment_href.py:37-39`、`tests/test_publish_hotfix.py:53/113/409/438`、
    `tests/test_publish_audit_hotfix.py:16/83`、`tests/test_exact_host_hotfix2.py:9`
    (tests/ 被 manifest 排除)

### c. 它自身 import 的 gzh-design 模块(拆分时需一并迁移的依赖)

- **唯一内部依赖**:`scripts/validate_gzh_html.py`,L109-111:

```python
109: # 与 validate_gzh_html.py 共享同一套检测逻辑
110: sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
111: from validate_gzh_html import validate, find_cn_quoted_attrs
```

- 外部依赖:`requests`(L104 `import requests`;`requirements.txt` 唯一一行
  `requests>=2.31,<3`);其余均为 stdlib(argparse/hashlib/json/os/re/sys/pathlib/urllib.parse)。
- 运行时读取:仅调用方传入的 HTML/封面/图片文件与 `.env`(L92);不读
  references/、assets/、themes 等任何排版资产。

---

## 6. gzh-design 76 个 runtime 文件分类

判定依据(实读安装副本):
- A 侧独有代码:`scripts/publish_wechat_draft.py`;其唯一第三方依赖 `requests`
  只有它在用 → `requirements.txt` 归 A。
- C 侧共用代码:`scripts/validate_gzh_html.py` —— publish 直接 import(L111),
  同时被排版侧 `render_article.py`(L40)、`fix_html_quotes.py`(L17)import,
  并被 `run_b_agent.py`(L27)、`run_real_agent.py`(L39)动态加载。
- 其余 73 个文件与 publish 无任何 import/读取关系 → B。

| 类 | 数量 | 文件 |
|---|---|---|
| A 发布相关 | 2 | `scripts/publish_wechat_draft.py`;`requirements.txt` |
| C 两类共用 | 1 | `scripts/validate_gzh_html.py`(publish 预检 + 排版输出校验共用的唯一校验核心) |
| B 纯排版相关 | 73 | 见下 |

B 类完整清单(73 个):
```
CONTRIBUTING.md
LICENSE
README.en.md
README.md
RELEASE_NOTES.md
SHA256SUMS
SKILL.md
assets/preview-template.html
assets/sample-article.md
assets/theme-previews/theme-mono-blue-editorial.html
docs/all-themes.md
docs/gallery/graphite-minimal.html
docs/gallery/index.html
docs/gallery/moyu-green.html
docs/gallery/moyu-ticket.html
docs/gallery/olive-journal.html
docs/gallery/red-white.html
docs/gallery/sample-article.md
docs/gallery/zen-whitespace.html
references/advanced-components.md
references/advanced/alerts.md
references/advanced/annotated-image.md
references/advanced/case.md
references/advanced/checklist.md
references/advanced/code-compare.md
references/advanced/compare.md
references/advanced/cta.md
references/advanced/decision.md
references/advanced/dialogue.md
references/advanced/facts.md
references/advanced/faq.md
references/advanced/footnotes.md
references/advanced/links-resources.md
references/advanced/media.md
references/advanced/quotes.md
references/advanced/steps.md
references/advanced/theme-adapters.md
references/advanced/timeline.md
references/common-components.md
references/eval-cases.md
references/format-normalize.md
references/theme-generator.md
references/theme-graphite-minimal.md
references/theme-hammer.md
references/theme-index.md
references/theme-moyu-green.md
references/theme-moyu-ticket.md
references/theme-olive-journal.md
references/theme-red-white.md
references/theme-zen-whitespace.md
scripts/check_links.py
scripts/component_lint.py
scripts/extract_docx.py
scripts/fix_html_quotes.py
scripts/generate_advanced_html.py
scripts/generate_article_html.py
scripts/generate_b_articles.py
scripts/generate_b_html.py
scripts/generate_dialogue_hotfix_samples.py
scripts/generate_dialogue_screenshot.py
scripts/generate_hammer_upgrade_samples.py
scripts/lint_advanced_components.py
scripts/make_b_assets.py
scripts/make_b_docs.py
scripts/make_review_zip.py
scripts/make_test_assets.py
scripts/render_article.py
scripts/run_b_agent.py
scripts/run_real_agent.py
scripts/scan_color_residual.py
scripts/screenshot_hammer_upgrade.py
scripts/update_component_docs.py
scripts/wrap_preview.py
```

结构注记:B 侧核心链为 `render_article.py`(lock 的 gzh-design entrypoint,
`required_files[0]`)→ `generate_hammer_upgrade_samples.py`(L39 import)→
`validate_gzh_html.py`(L40 import,归 C)。

---

## 7. 可行性判断:写入 skills.lock.json 属哪一侧职责

事实(非推测):
1. `skills.lock.json` 是 **wxgzh-pipeline 仓库根目录自己的文件**(`SKILL_ROOT =
   wxgzh_pipeline/…/parents[1]`),不在任何被锁 skill 的目录树内。
2. Pipeline 代码对它的全部行为是**读取与校验**:`load_lock`(skill_discovery.py L75-76)、
   `verify_all`/`discover`(L235-290)、doctor(L106-140)、install.py(L219/290/340/373)、
   build_portable_bundle.py(L158 复制)。**没有任何一段 Pipeline 代码写入它**。
3. 历史上对它的所有写入都是**直接手工编辑该 JSON 后 commit 到 Pipeline 仓库**
   (re-lock 提交 `fa67cdf/57443ad/261a016/4c6416d` 等,只改
   `skills.lock.json` + 审计说明),哈希值用 Pipeline 自带函数算好后抄入。
4. 写入 lock 文件本身**不触碰被锁 skill 的目录**:被锁 skill 树只通过
   `scripts/install.py` 从锁定 commit 整树安装/替换,安装流程也不写 lock。

结论:
- **写入 skills.lock.json 属于 Pipeline 侧职责**(文件在 Pipeline 仓库内、计算算法在
  Pipeline 代码内、历史写入全部发生在 Pipeline 仓库提交中)。
- **不需要写入被锁 skill 的任何文件**;被锁 skill 的 runtime 内容改变只能发生在其
  自身仓库并经 install.py 整树安装。
- 附带约束(事实):lock 的 `runtime_manifest_sha256`/`skill_root_sha256` 描述被锁
  skill 树真实内容;若 P2 拆分导致 gzh-design 的 runtime 文件集变化(如
  publish_wechat_draft.py 迁出),gzh-design 的 manifest/root 哈希必然改变,re-lock
  时必须以 `compute_runtime_manifest_sha`/`compute_root_sha` 对新树实算,且 doctor/
  verify_all 必须对新值全部通过;这一过程不改写被锁 skill 目录本身。

---

## 附:勘察期实算校验

- 安装副本 gzh-design runtime manifest:76 文件,sha `ced84143…e33b2` == lock 值。
- 安装副本 gzh-design root sha:`9a8cd7f5…` == lock 值(doctor PASS,四 skill hash_ok=true)。
- 本档除本报告外零写入;未重锁、未跑 Pipeline、未调微信接口。
