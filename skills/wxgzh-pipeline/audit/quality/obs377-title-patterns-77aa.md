# OBS-377 —— 77AA 标题生成端升级验收报告（补落，77AA-F）

- 档号：77AA（标题生成端升级：六范式语料库+关键词实证表+hits 台账=能力增强，OBS-377）。
- 授权：RELOCK_ALLOWED 临时 0→1（批准人=用户，范围=super-writer——title-playbook.md+新增 title-patterns.md+新增 title-hits.md+Phase 6 指令面；wxgzh-pipeline 无锁条目不涉锁，producers 指令面与 tests 随档）；GZH_DESIGN_WRITE_ALLOWED 维持 0。授权登记行随 feat 落账；已于档 77AA-F 归位（1→0，审核方 2026-09-07 验收通过）。
- feat 提交：2a39a54 + docs 提交：ff46d82（区间恰 2 颗，逐颗点验一致）。
- 本报告落盘说明：77AA 简报允许清单漏列本文件，验收报告缓落；由档 77AA-F 按成规补落（审核方简报缺陷，非执行端遗漏）。

## 1. 证据背景

- 用户标题痛点（三篇体检实证）：tlztos 点击欲望仅 4 分；skr87r 用户人工改标题；3bhpi2 用户裁决选网感款但带「无据」风险标记——网感组凭空发挥产出平庸，缺语料支撑。
- GitHub 调研两源：① woyin2024/lengyi-title——TOP50 标题榜，六范式分类与结构统计规律；② liucongg/liucong-skills（empirical-signals.md，Apache-2.0）——645 篇关联数据的关键词实证表（正向/负向信号）。

## 2. 任务 0 坐实摘录（存档）

- title-playbook.md 网感组仅一句指导（「有冲突/悬念/反差，允许口语，不准说谎」:24），无生成模板。
- Phase 6 挂点=producers AGENT_INSTRUCTIONS super_writer 77D/标题双轨段+77Z += 模式。
- 口径 68 先例措辞=「自写措辞，方法气质致谢 liucongg…ATTRIBUTION/README 一笔」；sw ATTRIBUTION.md 在册。

## 3. 三件实现（OBS-377）

- **title-patterns.md（新增，六范式语料库）**：§0 双目标原则（阅读量 vs 分享率二选一，实证 14.5 万阅读爆款分享率仅 1.9%）+ §1 六范式（新品速报/保姆级干货/清单盘点/第一人称战绩/横评实测/行业观点）各配定义+生成公式+适用场景+本号领域自写示例 2-3 条 + §2 结构统计表（22–27 字目标/Top10 均值 25.7/80% 逗号分段/56% 含数字/92% 点名带版本号/感叹号≤1/问号仅真痛点/`|` 后缀挂附加承诺/免费零门槛强钩子）+ §3 关键词实证表（正向 GitHub/Star 3.84×、Skill 3.23×、一键/直接用 3.16×；负向 DeepSeek 0.30× 过期实证、免费/白嫖 0.26×；四任务规则+禁堆叠只描述技术却无读者结果的词）+ §4 禁用清单（「揭秘/震惊/颠覆认知」0 条同禁）。
- **title-playbook.md（§2.1 四步配方+§6 纪律）**：网感组从一句话升级 §2.1 四步配方（双目标→六范式选型→关键词正负向选词→结构约束）+ §6 追加关键词四任务与禁堆叠纪律；其余各组/五维评分/风险标记/推荐结构/候选总数 3–5 不动（77D/77O/77Z 语义零回退）。
- **title-hits.md（新增，hits 台账）**：schema（日期/RUN_ID/标题/组/五维分/风险标记/表现回填位/验证状态）+三态（待回填/已验证/已证伪）+纪律（只追加不删改/只收本号真实数据防基数污染）+种子行（3bhpi2 2026-09-07 网感点击 22 分 5·4·5·4·4 无据-用户裁决接受 待回填）。
- 连带：sw Phase 6 指令面追加 77AA/OBS-377 hits 回填义务（轻义务不阻断流水线，producers += 模式，sw 指令实测 2910≤3000）；ATTRIBUTION.md 补 lengyi-title 与 empirical-signals 两行。
- 升版：sw 0.4.20-rc1→**0.4.21-rc1**（VERSION+CHANGELOG+MANIFEST 重算 114 行，test_count 303=passed 302+failed 1，skipped 2 不计，77Z 同法）。

## 4. 验收五条实测结论

1. **双重核验**：审核方+code-reviewer 独立核验——feat 2a39a54 + docs ff46d82 逐颗点验一致、区间恰 2 颗。
2. **锁链**：relock #109 sw 0.4.21-rc1（entry relock-super-writer-20260907T165250Z-fb89f516、备份在册、history+1）；R93 锁 sha 04a951e3… 双侧一致。
3. **落账与计数**：OBS-377 落账；唯一编号实测 259（119–377 连续无缺号）、R59 实测 main=21 partition_active=21 双差集空。
4. **回归与体检**：最终回归在 relock 后跑（77Y-F 新规），仅 obs154×1 既有红、零新红；doctor OBS_69/OBS_68 双侧 MATCH。
5. **锚点与防抄袭**：锚点测试 7 绿（test_hf77aa_title_patterns.py）；原榜标题零命中 grep 实证（77AA 交付时附录 A 仅含 1 条完整标题串，档 77AA-F 扩至 3 条）。

## 5. 缺信息与教训（如实登记）

- 77AA 简报任务 4a 要求「取附录 A 任意 3 条完整标题串做零命中断言」，实测附录 A 仅含 1 条（#6 案例标题），另 49 条存档于 researcher 会话未随简报——77AA 以在册 1 条实现并如实登记，77AA-F 由审核方补料扩至 3 条。
- executor 报告 relock --apply 首跑 exit 6 系调用时未带 WXGZH_PROJECT_ROOT+R93 未同步（72A 先例预期态），自纠后全绿、锁链无损——登记为跑姿教训不立案。

## 6. 许可证处置

- **lengyi-title**：按「不复制原文」原则不搬运任何标题原文与段落，仅嫁接范式结构与 TOP50 统计规律；ATTRIBUTION.md 登记一行。其 README 声称 MIT 但仓库无 LICENSE 文件——建议用户向作者确认许可证；未确认前维持「不复制原文」口径。
- **liucong empirical-signals**：Apache-2.0，77D 先例同法——注明出处、不搬运原文段落。

## 7. 反转条件（命中即回退）

1. 连续 3 篇按六范式配方生成，hits 台账回填后阅读/分享无提升 → 回退（playbook 网感组回一句话指导，语料库降级为参考件）。
2. 后续发文用户仍普遍人工改标题 → 配方无效，回退。
3. lengyi-title 许可证确认不下来 → 删除嫁接的范式结构/统计内容并回退 ATTRIBUTION 行。

## 8. 基线链

`a75d021（77Z-F）→ 2a39a54（feat 77AA，含授权登记行+obs304/obs288 随档）→ ff46d82（docs 77AA，relock #109+R93）→ <docs 77AA-F：归位+口径93 补记+本报告+锚点扩表>`
