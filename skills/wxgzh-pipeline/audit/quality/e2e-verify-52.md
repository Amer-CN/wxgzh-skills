# 档 52 — OBS-79 澄清 + OBS-72 封面修复 + 从 gzh_design 重跑

- 日期:2026-08-03
- RUN:`20260802T220853-codex-sol-luna-max-m6pyv4`
- 状态:**停机**(wechat_draft 阶段入口安全预检阻断,见「第二步」)
- 基线(重跑前):双侧 lock `CDC8F100C2A1D77F9FF87FF1D030C5871AB910B1ECB95376541F2BC713EF1186` / 台账 3 条(`59d63817`/`843f9372`/`1afb45bd`) / 四锁 root `46a00a1b…`(super-writer) `18491b36…`(zh-human-writing) `0d8aea21…`(media-enrichment) `b517aec6…`(gzh-design)

---

## 第零步 OBS-79 回归澄清

1. **为何 `audit/upgrade-capability/lock-backups/skills.lock.20260803T121024Z.json` 进入仓库**
   - 该文件是 relock 的**单文件 lock sha256 备份**(5,254 字节,完整 lock JSON),不是整树备份。
   - relock 工具 `DEFAULT_BACKUP_DIR = REPO_ROOT/audit/upgrade-capability/lock-backups`(scripts/relock.py L77),自档 27 起即为仓库内路径,属工具既定设计。
   - 当前 `.gitignore` 相关两行(L7-8):
     ```
     # OBS-79: relock preinstall 整树备份不得进入 git(仓库外 F:\AIXM\wxgzh-tree-backups-*)
     audit/upgrade-capability/lock-backups/skills-tree.*.preinstall/
     ```
     只匹配 `skills-tree.*.preinstall/`(整树备份),**不匹配** `skills.lock.*.json` → 没挡住,故随档 51 提交(`2bdddf8`)入仓。
2. **工具行为 vs 本次操作差异**
   - 是**工具既定行为**,不是操作差异。档 45R2 的 OBS-79 只改了**整树备份**路径(`tree_backup_dir` 默认移到仓库外 `F:\AIXM\wxgzh-tree-backups-*`,relock.py L894-897);单文件 lock 备份路径从未属于 OBS-79 的修复范围。OBS-79 的语义是「被锁 skill 源码不得在 pipeline 仓库出现第二份副本」,单文件 lock 备份是配置/状态快照,不是源码副本。
3. **判定:可接受,不登记新 OBS**
   - 单文件 lock 备份(5KB 级)与锁本身、台账(`skills.lock.history.json`)同为仓库内审计痕迹;整树备份才是 OBS-74 教训所指的「同代码多副本」问题,已正确迁出。
   - 若审核者仍要求连 lock 单文件备份也迁出仓库,需另开 OBS-84 排期(本档不动它)。
4. **其他新增文件核查**
   - 档 51 提交 `2bdddf8` 共 7 个文件:报告、lock 备份、台账、lock、守卫测试、守卫代码、observability——全部为档 51 预期产物,无未提及文件。

---

## 第一步 OBS-72 修复(producers.py)

### 修复内容
- 删除 `_wechat()` 中硬编码封面 `media_enrichment/discover/images/418d841f….png` + `expected_cover_sha=418d841f…`(历史 A-003 资产,与本 RUN 无关)。
- 新增 `_select_live_cover(ctx)`(producers.py,`_wechat` 之前):
  - **选择规则(显式,不依赖隐式顺序)**:`article_image_bindings.json` body_images 顺序中**第一张**「已批准 + 已成功上传」的资产。
  - 三条件 FAIL_CLOSED(任一条即拦截,exit 2 零副作用):
    1. 资产不在批准合同内(无稳定 single_asset 批准记录)→ 拦截;候选池为空同样拦截
    2. 批准状态非 approved / 批准记录与冻结 discovery manifest 的 asset_sha256 不一致 → 拦截
    3. 本地 `discover/images/<asset_sha256>.*` 文件缺失或实算 sha256 与冻结清单不一致 → 拦截
  - 批准合同解析复用既有 `_load_copyright_approvals()`(P0#2 严格校验:稳定字段、64-hex、asset_identity 重算)。
  - meta 新增 `cover_asset_id`,便于观察项取证。
- 规则理由:绑定顺序即文章内插图顺序,「第一张已批准正文图」确定、可预期;同时要求「已成功上传」保证封面资产真实存在于本 RUN 的微信上传记录。

### 测试(tests/test_obs72_cover_selection.py,6 项)
1. live 封面 = 第一张已批准+已上传正文图;`--cover` 指向本地冻结文件;`cover_asset_id` 记录
2. 未批准资产不入选;唯一候选未批准 → FAIL_CLOSED(反证)
3. 本地文件 sha 被篡改 → FAIL_CLOSED(`sha256 mismatch`)
4. 批准记录 sha 与冻结清单分叉 → FAIL_CLOSED(`diverges from frozen manifest`)
5. 空批准合同 → FAIL_CLOSED;上传事件为空 → FAIL_CLOSED
6. fake_live 路径回归:不加 `--cover`,保持 `--dry-run`

全部通过(6/6)。

### 真实数据离线验证
对本 RUN 实算 `_select_live_cover`:选中 **A-109**(body 绑定第一张;批准记录 AP-20260803T195315-INDEPENDENT-REVIEW-002;上传成功;本地 `73b4e06d….jpg` sha 匹配)。

### 封面尺寸问题(第 9 项回答)
- 现链路对封面**无尺寸校验**:`publish_wechat_draft.py` 的 `upload_cover`(add_material type=image)不检查宽高;`_select_live_cover` 也不检查。
- 若未来加封面尺寸下限(如 900×383 建议比),存在重演 OBS-82「批准后才不达标」的风险——批准环节只验正文图 640×360,封面约束未入批准前置校验。**本档不修**,如实登记。

---

## 同步安装侧(正式安装器)

- **git 源路径尝试失败(已回滚,零写入)**:`install.py --skills-src` 以 `repos/media-enrichment @ cedf92ca` 为源时,`installed root b8257469… != locked 0d8aea21…`。原因:lock 的 `source_tree_sha=c2b914a2…` 指向 cedf92ca 树,但 `skill_root_sha256=0d8aea21…` 指向**补丁树**(restore/local-patches-obs42-53 @ 2595e014,实算 root=0d8aea21)——即档 39R 登记的 lock 内部不一致(`full_commit_sha` 仍指 cedf92ca,root 是本地补丁树)。该不一致下,任何单一 git 源都无法同时满足 source_tree 与 root 校验。
- **bundle 路径成功**(与档 37/48/51 一致):手工构造 `bundle-staging-52/portable-bundle`(locked-skills=安装侧四锁树,doctor 已验==lock;wxgzh-pipeline=repo HEAD;source-proofs/MANIFEST 逐文件 sha256 绑定;secrets scan 通过),经 bundle 内置安装器实装:`ok=true`,四锁 `runtime_root_match/runtime_manifest_match/receipt_written/verify_all_ok=true`。
- 备注:build_portable_bundle.py 因 `EXPECTED_PIPELINE_FILE_COUNT=130` 常量过期(实际 590)无法走通,与排除清单同源,档 31 授权未覆盖,沿用人工构造路径。
- 校验:安装侧与 repo HEAD release 树 **590 文件逐字一致,0 差异**(排除设计豁免 `__pycache__`/`.pytest_cache`/`.gitattributes`);`producers.py` sha 双侧一致。

---

## 第二步 重跑 gzh_design → wechat_draft

### receipt 前置校验(实证档 48 判定)
- aihot / super_writer / zh_human_writing / media_enrichment:**OK**(零 mismatch)
- gzh_design:**SKILL_UPGRADED**(entrypoint hash mismatch,台账链 `relock-gzh-design-20260803T121024Z-1afb45bd`)→ 重跑
- wechat_draft:无 receipt(上次未执行成功)→ 重跑

### gzh_design 重跑 — 通过
- 新渲染器(hammer.3 `acc7745a`)生产链路首次重跑:`status=success`
- `THEME_IDENTITY=PASS` / `INTRO_GUARD=PASS` / `structure_ok=true` / `HAMMER_CHAPTER_TITLE_COUNT=4` / `RENDER_ENTRY_HASH_MATCHES_LOCK=true` / `INSTALLED_ROOT_MATCHES_LOCK=true`
- **★逐字对照(档 52 最重要项,第 11 项)**
  - `final_article.md` intro 段1(43 字符):`导语：多模型编排正在成为 AI 编程成本的关键杠杆，这次的样本来自 Codex 自己。` → **完整存在于 final.html 正文区域**(反提取纯文本逐字命中)✓
  - intro 段2(107 字符):`把最贵的模型留在最需要推理的地方……机制、价格与边界。` → **完整存在** ✓
  - 内容保真守卫判定:**PASS**(含首段与其余全部段落)

### wechat_draft — 入口安全预检阻断(停机点)
- OBS-72 封面逻辑生产实证:entrypoint argv 已携带 `--cover <run>/media_enrichment/discover/images/73b4e06da007d45a….jpg`(A-109 本地冻结文件)——封面选择、批准校验、sha 校验全部通过,不再有 A-003 硬编码失败。
- 阻断原因(exit 1,预检在**获取 token 之前**):
  ```
  validator ERROR: 0 / validator WARN: 1
  ⚠️ 预检阻断(1 项 WARNING,本次发布要求 WARNING=0):
     • 2 处正文疑似半角标点/英文引号,应改中文全角(代码块内不计;固定结尾署名组件内邮箱和 / 已豁免)。
       例:「一、把贵模型留给"思考"」
  不得获取 token,不得调用 draft/add
  ```
- 根因:冻结文章 `final_article.md` 第 7 行章节标题 `## 一、把贵模型留给"思考"` 含 ASCII 引号;渲染后正文章节标题 + 目录(toc-scroll)共 2 处。属**内容规范问题**(前四阶段产物,本档禁止修改),非渲染器回归、非 OBS-72 未修。
- 按指令**停机,不自行重试、不修改内容、不调低阈值**。
- 微信副作用:零(预检阻断在 token 获取之前;无 uploadimg / 无 add_material / 无 draft/add)。

---

## 第三步 观察项

- **e. 封面选中**:A-109(已批准 AP-…-002,本地 sha 与冻结清单一致);批准状态校验输出:三条件全部通过,`cover_asset_id=A-109` 进入 meta;实为**已批准资产**,OBS-72 修复生效。
- **d. 档 42 两项 WARN**:双侧 doctor 实测 `OBS_68_PIPELINE_MATCH=MATCH`、`OBS_69_LOCK_MATCH=MATCH`(WARN 恢复 MATCH)。
- **f. OBS-70(去重)**:封面走 add_material(永久素材);本次预检阻断发生在取 token 之前,**add_material 未执行**,无去重误判可观察——如实记录为未覆盖。
- **c. 代码块**:本文无 fenced code block,未覆盖(如实记录)。

---

## 第四步 收尾

- **validate_draft_delta 四项**:未执行——预检阻断未创建草稿,无 draft delta 可校验。
- **upgrade_regression.py:ALL PASS**(pytest PASS,1 项显式排除;四锁 relock dry-run 全部「无变化」;doctor --require-wechat PASS)。
- **双侧 doctor --require-wechat:PASS**;四锁 hash_ok 全 true;FAIL_CLOSED=false。
- **双侧 lock sha 未变**:`CDC8F100…`;台账仍 3 条;四锁 root 与基线逐字一致。
- **安装侧与 repo HEAD 逐字一致**:590 文件,0 差异(最终同步后复验)。
- **run 状态**:`failed_stage=wechat_draft` / `draft_created=false` / `formally_published=false`;`uploaded_image_count=6`(档 50 存量,本档零新增)。

## 副作用总账更新

- 本档真实微信副作用:**0 次 uploadimg / 0 次 add_material / 0 份草稿 / 无发布群发定时删除**。
- **草稿箱异常(据实登记)**:预检实测 `total_count=1`(预期 3;档 50 复核时为 3),箱内仅剩事件稿「vibe-coding-guide v2.1 升级」(草稿 #3)。草稿 #1/#2 在 2026-08-03T19:53Z 之后消失;管线代码不存在删除/发布草稿能力,判定为人工侧动作(后台删除或发布),非管线行为,待用户确认。
- 累计:uploadimg 仍 22 次;草稿累计创建仍 3 份(箱内现存 1 份)。

---

## 结论与后续

1. **OBS-79 澄清**:lock 单文件备份入仓为工具既定设计且可接受,不登记新 OBS;整树备份已正确迁出仓库。
2. **OBS-72 已修复并生产实证**:封面选择=已批准正文首图,三条件 FAIL_CLOSED,反证测试 6/6 通过;真实 RUN 选中 A-109。
3. **OBS-83 生产链路实证**:intro 两段(43 字/107 字)完整进入 final.html,守卫 PASS。
4. **停机点**:wechat_draft 入口预检因冻结文章含 2 处半角引号(章节标题「"思考"」)被阻断,未创建第 4 份草稿。按禁令未修改文章、未降阈值。下一步需用户授权修正冻结文章引号全角化(zh-human-writing 阶段产物)后重跑,或另开档处理。
5. **test_intro_guard 修正**:档 52 按指令重跑 gzh_design 合法覆盖了 .temp 实时 final.html(原测试输入),已将档 50 旧渲染样本冻结为 `fixtures/regression_samples/`(hammer.2 `9596ecc` 对同一冻结文章离线复现,语义逐字等同:首段仅 40 字封面 oneliner,正文缺失),断言未放宽:`ok=False` + missing=首段全文,测试 13/13 通过。
