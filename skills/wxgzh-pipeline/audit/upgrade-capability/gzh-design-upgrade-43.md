# 档 43 — gzh-design 升版:OBS-73 根治 + 问题 B + 文档修正 + 首次真实 relock(停机于第五步)

- 报告编号:gzh-design-upgrade-43
- 执行日期:2026-08-02(Asia/Shanghai)
- 状态:**第五步(正式安装器安装新分支)按 fail-closed 拒绝,依「任一步骤结果与预期不符,立即停机上报,禁止自行修复后继续」停机。未执行第六~八步。未手工编辑任何 skills.lock.json、未执行 relock --apply、未调微信接口、未跑完整 Pipeline、未删除任何文件(TEMP_CLEANUP_ALLOWED=false)。**
- 工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(dev/0.1.0-dev2,起点 HEAD `d6e9d51`)

---

## 第零步 档 42 遗留核查(通过)

### +14 −1 全部原文(commit `75ab23f`)

```diff
@@ -36,11 +36,15 @@
 class Orchestrator:
     def __init__(self, project_root=None, network_mode="offline_fixture",
                  fixture_dir=None, env=None, skills_home=None,
-                 lock_path: Path | None = None):
+                 lock_path: Path | None = None,
+                 repo_root: Path | None = None):
         self.env = dict(env) if env is not None else None
         _env = self.env if self.env is not None else None
         self.project_root = P.resolve_project_root(project_root, env=_env)
         self.skills_home = Path(skills_home) if skills_home else P.skills_home(self.project_root, env=_env)
+        # OBS-68: repo worktree for installed-pipeline comparison; None => doctor
+        # reports SKIPPED_NO_REPO (WARN only, never an error).
+        self.repo_root = Path(repo_root) if repo_root else None
         if network_mode not in ("offline_fixture", "fake_live", "integration", "live"):
             raise ValueError(f"unsupported network_mode: {network_mode}")
@@ -143,6 +147,15 @@
             ok = ok and live_pipeline_allowed
         report["FAIL_CLOSED"] = not ok
         report["doctor"] = "PASS" if ok else "FAIL"
+        # OBS-68/69 (档42): detection-only WARN section. Never changes `ok`.
+        from . import observability as OBS
+        installed_lock = self.skills_home / "wxgzh-pipeline" / "skills.lock.json"
+        repo_lock = (self.repo_root / "skills.lock.json" if self.repo_root else None)
+        report["observability"] = {
+            "OBS_69_LOCK_MATCH": OBS.check_lock_consistency(installed_lock, repo_lock),
+            "OBS_68_PIPELINE_MATCH": OBS.check_pipeline_consistency(
+                self.skills_home / "wxgzh-pipeline", self.repo_root),
+        }
```

### 逐行运行期行为与判定

- 第一处(−1 +5):`__init__` 新增可选参数 `repo_root`,默认 `None`;`self.repo_root` 仅存值。所有既有调用方不传该参数 → 行为与之前逐字一致。
- 第二处(+9):位于 `ok`/`FAIL_CLOSED`/`doctor` 计算**之后**、`return ok, report` 之前;只向 report 字典追加 `observability` 键。全仓无任何代码读取该键来影响流程走向、阶段判定或退出码;`doctor()` 的 `ok` 值在其之前已定。
- 结论(a):**零行为影响**——不改变任何路径的流程走向、阶段判定、退出码。
- 结论(b):测试覆盖——`test_doctor_exit_code_unchanged_with_mismatches`(MISMATCH+DIFF 时退出码 0)、`test_doctor_observability_skipped_without_repo_root`(SKIPPED 时退出码 0)均端到端执行该 +9 路径并显式断言退出码;upgrade_regression 的 doctor 步也执行同一路径。**本次按核查要求补了一条 MATCH 路径用例** `test_doctor_exit_code_unchanged_with_match`(MATCH+repo_root 时退出码 0、doctor=PASS),已提交 `d6e9d51` 并 push。
- 结论:确认仅为 WARN 级输出、零行为影响 → 记录后继续。

## 第一步 施工前勘察(通过)

- 远端确认:`chore/wxgzh-pipeline-dev2-integration` = `0007d7e6…`(`git ls-remote`);`main` = `1c5dd963…` 未动。
- 新分支:`fix/obs73-codeblock-docs`(自 0007d7e6 创建),后续改动只在该分支。
- 逐字一致性复验(档 32 结论):分支树实算 `root = 9a8cd7f5…` / `manifest = ced84143…` / `count = 76`,与 lock 逐字一致;与安装侧 runtime 范围逐文件内容 diff = 0;`render_article.py` sha `e4023726…` = lock `entrypoint_sha256`。**一致,继续。**
- 组件库盘点(第 6 项):
  - hammer 组件集(`scripts/generate_hammer_upgrade_samples.py`):`container / cover / toc / oneliner / chapter / para(L753) / image_2a / media_text / fixed_signature / footer_cta`。
  - a. **不存在单栏代码块组件**。`code-compare`(`scripts/generate_advanced_html.py` L65)是双栏「改前/改后」对比组件(标题 + 两个等宽面板),语义不符,不接入。
  - b. 渲染独立段落的现有手段:`hammer_para`(唯一);`hammer_media_text` 是图文卡,`hammer_oneliner` 是引言卡,均非普通段落。

## 第二步 OBS-73 根治(实现完成,commit `b3d5fc4`)

- `parse_article` 新增 `intro_paras`(intro 第一行之后的全部非空非标题行);`intro` 字段语义不变(封面副标题 48 字 / oneliner 40 字截断不变)。
- `render` 在 chapters 循环之前渲染 `intro_paras`(复用 `hammer_para`,未新增组件类型);顺序:封面 → 导语段落 → 第一个章节标题 → 章节正文(第 7 项目标行为)。
- 第 9 项影响评估(先评估后动手):intro 段落/代码块只引入 `hammer_para` 样式(font-size:14px)与 `<pre>`,不触碰 `validate_theme_identity` 的任何结构指纹(cover/toc/chapter_title font-size:28px/signature/footer/img-types)、`toc_dynamic_ok` 的 `PART {i:02d}` 计数与 `chapters_ok` 章节计数 → **现有校验不会 FAIL,无需放宽任何校验**。

## 第三步 问题 B — fenced code block(实现完成,commit `76a91e2`)

- `parse_article` 识别 ``` 围栏(开/关围栏行不并入段落文本;围栏内容逐字保留);章节与 intro 区域均支持。
- 渲染:新增最简 `<pre>` 实现(`_hammer_code_block`,位于 render_article.py):内联样式(等宽字体、浅底 `#F5F3F0`、圆角、`white-space:pre`、`overflow-x:auto`),不依赖 `<style>`/class;内容为可复制的真实文本,非图片/伪装元素;不硬套 code-compare。
- 验证(第 14 项):新测试 8 项全 PASS——反引号不出现在输出中;代码内容逐字保留(含 4 空格缩进);通过 `validate_gzh_html`(其 CODE_STYLE 豁免代码区内半角标点);intro 区代码块正常;未闭合围栏宽松处理。
- gzh-design 全量测试:185 passed + 21 skipped;仅 3 项 `test_fixed_signature` 失败——已在基准 commit 0007d7e6 上复现为**既有失败**(与本次改动无关,如实记录不处理)。

## 第四步 文档修正(commit `7c0c06f`)

- OBS-67:`SHA256SUMS` 移除对不存在 zip 的引用,重算现存 5 文件(仅 theme-index.md 原值不变,其余 4 项更新)。
- OBS-75:`README.md` 4 处安装源 `531285650/gzh-design-skill` → `Amer-CN/gzh-design-skill`(含 Releases 链接)。
- OBS-76:`RELEASE_NOTES.md` 追加「与 wxgzh-pipeline 集成范围的如实说明」:19 高级组件与 `:::` 语法属通用排版入口,锤子渲染管线仅用 9 组件子集(+ 新增单栏代码块);并追加本升版的 OBS-73/问题 B 变更记录。版本号头不变(避免影响 version_ok)。
- 分支已 push:`fix/obs73-codeblock-docs` HEAD = `7c0c06f845b886138525af3bfaafa13614fdfe60`(三个 commit:`b3d5fc4` 渲染器 / `76a91e2` 代码块 / `7c0c06f` 文档)。

## 第五步 安装与重锁 —— **停机点**

### 预演推算验证(第 21 项,先于安装完成)

新分支树实算(仓库侧 `compute_root_sha` / `compute_runtime_manifest_sha` / `_file_sha`):
- `root = 4d68cd90b305db831cb89be2af357a56e66bba0d54accd26e93046915d4a4486`(旧 `9a8cd7f5…` → **必变,成立**)
- `manifest = ced841439195453497e67a63186823f60eee7155b9de472e936c3d4d767e33b2`(**不变,成立**)
- `file_count = 76`(**不变,成立**)
- 档 41 预演「root 必变、manifest/count 不变」**与实际一致,预演无误**。

### 安装器实测(第 20 项,正式安装器 dry-run,零写入)

构建 `bundle-staging-43\portable-bundle`(wxgzh-pipeline 仓库 HEAD 镜像 + locked-skills 中 gzh-design = 新分支树、其余三锁 = 24S 基线;source-proofs 对 gzh-design 如实填新分支 `7c0c06f…` / 树 `b0d81ef7…`;MANIFEST 重建;密钥扫描 clean),执行:

```
python installer\install.py --target F:\AIXM\wxgzh\.agents\skills --project-root F:\AIXM\wxgzh --dry-run
exit: 1
"skill": "gzh-design",
"commit_match": false,
"source_tree_match": false,
"repository_match": true,
"error": "gzh-design: source proof does not match skills.lock"
```

**fail-closed 按设计拒绝**:安装器要求锁定 skill 的来源证明(commit/tree)与 lock 逐字一致,而 lock 的 `full_commit_sha` 仍是 `0007d7e6…`、`source_tree_sha` 仍是 `a1f40820…`。

### 能力缺口分析(据实,不推测)

要让「安装新树 → relock」闭环成立,lock 至少需要更新 4 类字段:
1. `skill_root_sha256`(9a8cd7f5 → 4d68cd90)—— relock.py 可写(`_HASH_FIELDS` 之一);
2. `runtime_manifest_sha256` / `runtime_file_count` —— 本次不变;
3. `entrypoint_sha256` 与 `render_entry_sha256`(e4023726 → ca599b64,render_article.py 已改)—— **relock.py 不写**(`_HASH_FIELDS = ("skill_root_sha256","runtime_manifest_sha256","runtime_file_count")`);validate_theme_identity 的 `entry_hash_ok` 会因 stale 而 false → live 阶段 THEME_IDENTITY 必 FAIL;
4. `full_commit_sha` / `source_tree_sha`(0007d7e6/a1f40820 → 7c0c06f/b0d81ef7)—— **relock.py 不写**;安装器 `commit_match/source_tree_match` 因 stale 而 false → 安装被拒(本次实测即此)。

而「禁止手工编辑任何 skills.lock.json」依然生效。结论:**当前工具链(relock.py 三字段能力 + install.py 锁定来源校验)无法按第五步顺序完成 gzh-design 升版闭环**;这也是 OBS-74 早已记录的「relock 需具备仅更新 full_commit_sha/source_tree_sha 能力,否则需扩展」缺口的首次实际触发。按指令「若 relock 因任何原因失败,不要手工补救,贴出退出码与输出后停机」及 R2,本档在此停机:未执行第六~八步,未做任何手工补救。

## 第六~八步:未执行(停机)

第六步(守卫升级)、第七步(三篇历史 RUN 重渲染验收)、第八步(全面复核)均依赖第五步的安装成功,按停机规则全部未执行。

## 环境状态(停机时快照)

- 安装侧 gzh-design root 仍 `9a8cd7f5…`(76),未受安装尝试影响(dry-run 零写入);
- 两侧 skills.lock.json sha 均 `a9e07ef4…`(未动);`skills.lock.history.json` 不存在(未动);
- 证据/暂存目录完好;wxgzh-pipeline 工作树干净(仅本报告待提交);
- gzh-design-skill 远端:main `1c5dd963…`、chore `0007d7e6…` 未动;新分支 `fix/obs73-codeblock-docs` = `7c0c06f…` 已 push。

## 需要裁决的问题

1. **relock 能力扩展**(建议优先):授权扩展 relock.py,使 `--apply` 对目标 skill 同时更新 `full_commit_sha / source_tree_sha / entrypoint_sha256 / render_entry_sha256 / validator_sha256 / component_source_sha256`(来源值来自安装器的 source-proofs 或显式参数),并保留逐字回滚与台账。理由:不扩展则任何被锁 skill 的升版都走不通(本次为首次实证)。
2. **升级顺序变体**:授权「先 relock(对暂存的新树,--skills-home 指向 staging)后安装」的顺序,并让安装器接受与 lock 一致的 commit/tree(即 relock 先更新 commit/tree 字段)。建议与第 1 项合并实施。
3. **第六步守卫升级**:渲染器已具备多段 intro 渲染能力,但安装未完成,守卫(档 40 版本,拦 intro>1 行)维持现状;建议在 relock 能力补齐、安装闭环后,再按档 43 第六步方案升级守卫并跑第七步验收。
4. 预演结论已实证(manifest/count 不变),第五步恢复执行时无需重新评估。

## 双仓库 SHA

- Amer-CN/gzh-design-skill:`fix/obs73-codeblock-docs` HEAD = `7c0c06f845b886138525af3bfaafa13614fdfe60`(b3d5fc4 / 76a91e2 / 7c0c06f)
- wxgzh-pipeline:本报告 commit = 见提交输出
