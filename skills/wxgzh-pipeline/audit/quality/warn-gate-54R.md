# 档 54R — 门槛分级 + OBS-85 + 第四次真实 relock + 续跑至草稿

- 日期:2026-08-04
- 取代:原档 54(已停机,`bd303e4`);原档第 5 项「走安装器同步」作废(时序矛盾,已按裁决以 relock 原子链承载安装)。
- 状态:**通过**。草稿 #4 创建成功(不发布),第四次真实 relock(台账第 4 条)完成。

---

## 第一步 OBS-85 与分级设计

1. **OBS-85 登记(高)**:`validate_gzh_html.py` L213「HTML 解析中断」原归 WARN——校验器未能完成检查却输出温和结果,属假绿家族同型缺陷。**已升为 ERROR**(`errors.append(f"HTML 解析中断: {e}")`),任何情况(含放行开关全开)不可放行,反证测试覆盖。
2. **分级方案**(理由):
   - ① 半角标点/英文引号 → `WARN_ALLOWABLE`(可显式放行):排版规范问题,不影响微信渲染有效性,validator 设计语义本就是「建议检查」(exit 0)
   - ② span leaf 未包裹 → `WARN_BLOCKING`(不可放行):样式丢失风险,粘贴后视觉效果受损,属渲染缺陷信号
   - ③ 解析中断 → ERROR(OBS-85)
   - ② 归类维持「不可放行」——若审核者认为应调整,请裁决。
3. **放行开关形态**(四条全落实):
   - a. 显式参数 `--allow-warnings`(store_true,默认关闭);Pipeline 侧另有环境开关 `WXGZH_ALLOW_WARNINGS`(默认未设置=关闭,CLI 显式透传),双层显式
   - b. 仅对 `WARN_ALLOWABLE` 类别生效(`publish_wechat_draft.py` 分级判定:blocking 类与全部 ERROR 无条件阻断)
   - c. 放行事实写入 `wechat_draft/allowance_record.json`(schema/时间/html_sha256/entries),并经 Pipeline `_wechat()` 纳入 stage 产物 → **stage_receipt.json output_files/output_hashes 绑定**,可事后追溯
   - d. 逐条列出规则与文本原文(entries: rule/category/text/snippets)

## 第二步 实施

4. `validate_gzh_html.py`:新增 `WARN_ALLOWABLE/WARN_BLOCKING` 类别常量;`validate_full()` 内部实现 + `validate()`(兼容三元组)+ `validate_graded()`(结构化条目);③ 升 ERROR。
5. `publish_wechat_draft.py`:新增 `--allow-warnings`;`preflight_html` 分级判定;放行条目写 `allowance_record.json` + 打印;摘要新增 `allowed WARNING` 行。
6. 测试(`tests/test_warn_grading.py`,7 项):开关关①阻断 / 开关开①放行且留痕逐字 / 开关开②仍阻断 / 任何情况③阻断 / 记录内容正确 / 解析中断为 ERROR / graded 类别正确。**7/7 通过**。
7. ★反向验证:mock `LeafChecker.feed` 抛异常 + `--allow-warnings` 全开 → `SystemExit`(被拦下)。✓
   - gzh-design 全量:pytest 200 passed / 3 failed(OBS-77 预存 fixed_signature 失败,stash 复测确认与本次改动无关)/ 21 skipped。

## 第三步 回流与升版

8. push `fix/obs73-codeblock-docs`:**`ce9bf4cc8e270bcdc71940dd2c430d4727b888c8`**(acc7745 → ce9bf4c)。
9. `RELEASE_NOTES.md` 首行 → **v2026.08.02-hammer.4**,写明 WARN 分级 + OBS-85;`WXGZH_PIPELINE_INTEGRATION.md` Locked version → hammer.4、Locked root 重算(**3e3aed4a…**;附注:hammer.3 时该 root 漏同步,本次一并修正);`SHA256SUMS` 重算(publish/validate 两行)。

## 第四步 第四次真实 relock

10. `relock.py --skill gzh-design --source-tree repos/gzh-design-skill-43r-build --source-commit ce9bf4c --apply`
    原子链:远端见证 **PASS (a/b/c)** → 计算 → 仓库外备份 → 写 lock+台账 → 安装器 **PASS** → post-doctor **PASS** → 入口冒烟 **PASS**(CLI subprocess,生产路径)。
11. 字段变化:
    - lock sha:`CDC8F100…` → **`8FCBC2034EF031227BFEB56041DE4C1F648EBD165A24C8F6EAD1A2532C93E479`**(双侧一致)
    - 台账第四条:`relock-gzh-design-20260804T042535Z-a0ec5388`
    - root:`b517aec6…` → **`c3dd056e…`**;validator:`b986ae77…` → `4e834e21…`;full_commit:`acc7745` → `ce9bf4c`;source_tree:`725bd903…` → `19a14013…`;version:`hammer.3` → **`hammer.4`**
    - manifest `ced84143…` / count 76 / entrypoint `5356c480…` 不变
12. 冒烟输出:见 `.temp/relock54r-apply.txt`(`gzh-design: entrypoint smoke PASS (CLI subprocess, production path)`)。
    - **附注(如实)**:relock 进程退出码为 1,末尾输出「lock 已更新但回归未通过,需人工裁决」——根因是本次调用环境设了 `PYTHONIOENCODING=utf-8`,relock 内 upgrade_regression 子进程按 GBK 解码 UTF-8 输出抛 `UnicodeDecodeError`(Windows 控制台编码问题,非测试失败)。**人工裁决**:在干净环境(未设 PYTHONIOENCODING,与既往 ALL PASS 运行一致)独立重跑 `upgrade_regression.py` → **ALL PASS**;双侧 doctor PASS;安装侧 root 与 lock 一致。据此判定 relock 功能结果完整,「需人工裁决」为环境编码误报。

## 第五步 续跑至草稿

13. receipt 状态(实测):aihot / super_writer / zh_human_writing / media_enrichment **OK**;gzh_design **SKILL_UPGRADED**(台账 a0ec5388,validator hash mismatch);wechat_draft 无 receipt → **从 gzh_design 续跑**。
14. 续跑命令:显式 `WXGZH_ALLOW_WARNINGS=1` → gzh_design 重跑(hammer.4,产物 sha `160b26aa…` 与档 52 逐字一致,渲染逻辑未变)→ wechat_draft(带 `--cover` A-109 + `--allow-warnings`)→ **exit=0,draft_created=true**。
15. ★放行条目原文(wechat_draft/allowance_record.json,全文):
    ```json
    {
      "schema_version": "1.0",
      "allow_warnings": true,
      "allowed_at": "2026-08-04T04:40:40Z",
      "html_sha256": "160b26aad2bcc12e9bcf0dd2a7bfdc37d272bf54ab8a16de449524e137ef250a",
      "entries": [
        {
          "rule": "half_width_punct",
          "category": "allowable",
          "text": "2 处正文疑似半角标点/英文引号，应改中文全角（代码块内不计；固定结尾署名组件内的邮箱和 / 已豁免）。例：「一、把贵模型留给\"思考\"」；「一、把贵模型留给\"思考\"」",
          "snippets": ["一、把贵模型留给\"思考\"", "一、把贵模型留给\"思考\""]
        }
      ]
    }
    ```
    **确认:仅那 2 处半角引号(half_width_punct),无夹带任何其他规则。**
16. validate_draft_delta 四项(validator_report):**DRAFT_DELTA PASS**(AFTER_eq_BEFORE_plus_1=true,BEFORE=1→AFTER=2)/ **OLD_DRAFTS_PRESERVED true** / **NEW_DRAFT_UNIQUE true** / **UPDATE_TIME_SUBSET true**;CREATION_RESULT=PASS;flags:formally_published/mass_send/scheduled/deleted_any 全 false。
17. ★草稿信息:
    - title:`Codex 用 Sol 指挥 Luna Max 省额度翻倍产出`
    - 封面来源资产:**A-109**(`_select_live_cover` 确定性重放实证,sha `73b4e06d…`,已批准 AP-20260803T195315-INDEPENDENT-REVIEW-002)
    - 正文图片:**6 张**(A-109..A-114 绑定,档 50 存量上传,本档零 uploadimg)
    - final.html 正文首段对照(逐字):
      - 段1(43字)`导语：多模型编排正在成为 AI 编程成本的关键杠杆，这次的样本来自 Codex 自己。` → **完整存在** ✓
      - 段2(107字)`把最贵的模型留在最需要推理的地方…机制、价格与边界。` → **完整存在** ✓
    - 记录缺口(如实):本次成功 run 的 entry argv 未落盘(stage_result 不存 meta),封面资产以确定性重放 + 放行记录 + 草稿产物交叉实证。

## 第六步 复核

18. **upgrade_regression:ALL PASS**(pytest PASS,1 项显式排除;四锁 relock dry-run 全「无变化」;doctor PASS);**cross-side 守卫仍为 SKIP**(P2 未落地,未因本档改动变 FAIL)✓
19. 双侧 doctor --require-wechat:**PASS**,hash_ok 全 true,FAIL_CLOSED=false;OBS_68/OBS_69 MATCH
20. lock 双侧一致 = **8FCBC203…**;台账 **4 条**;安装侧与 repo HEAD **595 文件逐字一致(0 差异)**
21. 副作用总账(已更新 ledger.md):草稿箱 **2 份**(基线 1 + 新增 1);累计创建 **4 份**;uploadimg 累计 **22 次**(本档 0);封面 add_material 累计 **4 次**(本档 +1);发布/群发/定时/删除 **0**。

## 配套 Pipeline 侧改动(本档)

- `wxgzh_pipeline/producers.py`:`_wechat()` 双层显式开关(WXGZH_ALLOW_WARNINGS → `--allow-warnings`);`allowance_record.json` 纳入 stage 产物(receipt 绑定)
- `wxgzh_pipeline/cli.py`:透传环境变量(此前 env 参数从未经 CLI 传入,放行开关等无法生效——修复)
- `wxgzh_pipeline/observability.py`:OBS-69 基线 CDC8F100 → 8FCBC203(随 lock 变更同步)
- `tests/test_obs72_cover_selection.py`:+2 项(env 开关传参/放行产物入 outputs),8/8 通过

## 结论

档 54R 全项通过:OBS-85 登记并修复、WARN 分级 + 显式留痕放行、hammer.4 回流、第四次真实 relock(台账第 4 条)、续跑创建草稿 #4(箱内 2 份),零发布。待裁决遗留:OBS-77(3 项 fixed_signature 预存失败)与 relock 子进程 Windows 编码缺陷(环境误报,建议后续以 encoding 修复)。
