# 档 66 — OBS-88 数字结构化 + 代码块形态指示,重跑写作链(路径 a)

- RUN_ID:`20260804T174355-vibe-coding-guide-v2-1-6-by4s00`(新 RUN,素材沿用档 64
  注入通道与四份素材)
- 状态:**已到媒体批准点,6 张图表全部 approvable(= body_images_min 6,无凑数)**
  ★停在批准点等审批准清单,未继续 continue。
- 本档副作用:零 uploadimg、零 add_material、零草稿、零发布、零微信调用。

---

## 第零步 归属判定:路径 a(Pipeline 侧)

- OBS-88(registry 数字结构化)与写作形态指示都落在 **Pipeline 侧**:
  - 根因是「注入路径下 registry 构建未执行数字结构化」——super-writer skill 本身
    支持 numbers(事件 RUN 实证),不是能力缺口,是执行纪律缺口;
  - 修复 = 指示层(AGENT_INSTRUCTIONS 注入)+ 强制校验层(新增 Pipeline 侧
    `writing_contract.py`,由 `stages/super_writer.py content_validate` 挂载,
    仅注入路径启用);gzh-design 已支持 fenced code block 渲染(档 43),写作侧
    无需新能力;
  - **不动被锁 skill、不 relock**:lock 与台账不变(复核项见第五步)。

## 第一步 OBS-88 修复

- `wxgzh_pipeline/writing_contract.py`(新增):
  - `cn_to_int`:中文数字→阿拉伯(四→4、五→5、十五→15、二十五→25 等);
  - `extract_number_pairs`:从文章提取数字对比对(`从 8 条扩到 11 条`/`四→五`/
    `19→25`,支持中文与阿拉伯数字,解析失败不伪造);
  - `validate_registry_numbers`:文章中的对比对必须被 registry claims 结构化登记
    (每对起/终两个数据点:numbers(数组,事件 RUN 同构)+ chart_group +
    metric_name + series_label 非空;文章无对比对时不要求——不伪造);
  - `validate_codeblock_fidelity`:注入素材的 deny/ask 拦截文案(8 deny + 8 ask =
    16 条)至少 10 条以 fenced code block **逐字**进入文章,且代码块内必须出现
    ⛔ 与 ⚠️ 前缀模板(_common.sh deny()/ask() 模板)。
- `stages/super_writer.py` content_validate:注入路径强制两项校验,FAIL_CLOSED
  (report 含 OBS88_NUMBERS/OBS88_CODEBLOCK/registered_groups/deny_ask_covered)。
- `producers.py` AGENT_INSTRUCTIONS["super_writer"]:新增注入路径强制指示
  (数字结构化 + 代码块形态 + 16 条文案逐字)。
- 测试 `tests/test_obs88_writing_contract.py`(11 项全过):中文数字/对比对提取/
  三组登记 PASS/缺组 FAIL/无对比不伪造/16 条全进 PASS/覆盖不足 FAIL/改写 FAIL/
  前缀缺失 FAIL/★反向验证(四素材夹具提取 16 条)。
- 更正:档 65 取证报告称「15 条」——实测 guard-bash.sh 为 **8 deny + 8 ask = 16 条**
  (取证段计数错误,本档更正;此前取证输出的 ask 清单漏数「线上部署」一条)。

## 第二步 代码块形态指示

- writing-brief/outline 均含形态要求;AGENT_INSTRUCTIONS 指示:
  shell 命令/脚本片段/终端输出/拦截文案必须以 fenced code block 原文呈现,
  不得转写为散文。
- 16 条 deny/ask 文案**全部逐字进入文章**(未取舍——按「保留的必须逐字不改写」,
  16 条全进且正文散文不再复述,篇幅可控;高于最低 10 条要求),含 ⛔/⚠️ 前缀模板
  与「关闭护栏:/plugin disable vibe-coding-guide」后缀,语言标记 bash。
- 与 zh_human_writing 的边界:代码块属引用原文,zh 阶段**逐字保留**(fidelity_guard
  13/13 含代码块 compare,零改写;现有实现无自动改写代码块文本的环节,agent 执行
  中亦未触碰)。
- install.sh 两行 /plugin 命令:进入文章第三节 fenced `text` 块,**无缩进、可复制**
  (原文 7 空格缩进已去除);compare_commands 提取器只认 `$`/`>` 开头行,两行命令
  不在提取器内,无失配(fidelity 13/13 实证)。

## 第三步 重跑写作链(新 RUN)

- **RUN 处置选择:新 RUN**(`20260804T174355…by4s00`)——当前档 65 RUN 停在批准点,
  其写作链为旧指示产物且无强制重跑机制;新 RUN 走同一注入通道(档 64 通道,
  items 复用,blob 已核验),aihot 注入零网络。
- 重跑过程中发现并修复两个 Pipeline 侧判定缺口(实施缺陷,当场修复):
  1. 注入 meta resume 分支字段集与首次不同构 → 握手 token 漂移 → 改为逐字同构;
  2. discover 暂停有效性未绑定上游 registry 哈希 → registry 变更后旧 discover
     产物仍被复用 → 增加 canonical_registry_sha256 比对,漂移即重跑。
- **super_writer 产出**(第 8 条):三个官方校验器**全部 exit 0**
  (material_ingestion / validate_article_length full-mode / validate_semantic_map);
  文章 3950 可见字符(medium 区间内,5 节预算偏差 ≤1.7%);
  **fenced code block 2 个(bash×1 = 16 条拦截文案,text×1 = 2 行安装命令)**;
  **registry 中 numbers 组数 = 3 组 6 条 claims**(红线数量 8/11、自检清单 19/25、
  协作铁律 4/5,数组结构,与事件 RUN 同构);OBS-88 写作合同校验 PASS
  (registered=3、codeblock covered=16/16)。
- **zh_human_writing**(第 9 条):fidelity_guard **13/13 全过,0 fail 0 warning**
  (含 compare_code/compare_commands,代码块逐字);pattern_audit/change_report
  exit 0;六项 gates 全 0;仅两处散文微调,代码块与命令零改动。

## 第四步 media discover(止于批准点)

- **网页抓图候选 4 张,全部 rejected**(GitHub blob 页 og:image 社交卡 + 精确
  去重),正文抓图为零——与档 62 前瞻一致,非异常;
- **自生成图表 6 张**(3 组对比 × bar/comparison 两种形态),全部 review_required:
  - A-005/A-006 红线数量:v1.0 8.0 条 vs v1.2.0 11.0 条(N-01/N-02)
  - A-007/A-008 自检清单:v1.0 19.0 条 vs v1.2.0 25.0 条(N-03/N-04)
  - A-009/A-010 协作铁律:v1.0 4.0 条 vs v2.1 5.0 条(N-05/N-06)
  - 内容描述:生成图表(type)「组名:指标对比」,数据来源 canonical claims
    (source=generated,已核实非 claim 派生填充);caption 含完整数据点;
  - 位置:拟绑定章节锚点(「第一组是红线…」/「第二组是铁律…」行,level=
    article-anchor),来源 = registry claim_text 与文章逐字对齐后的 placement。
- `approval_readiness.json`:`summary {total: 10, approvable: 6, blocked: 4}`;
  **6 张图表 approvable=true**(内容 verified + 位置 known + decision
  review_required);4 张源图 approvable=false(rejected/内容不明/位置未知)。
- 第 13 条:**可批准候选 6 = body_images_min 6 ✓**(未降阈值、未凑数、未手工补
  字段;数字足够凑齐 6 张,与档 66 指令预期一致)。
- 已知小瑕疵(如实记录,不修):图表 content_description 含「数据来源:数据来源:」
  双重前缀(chart spec 的 source_note 自带前缀,拼接重复)——不影响批准信息
  (caption 数据点完整),属被锁侧文案问题,待排期。

## 第五步 复核

- 副作用:零 uploadimg、零 add_material、零草稿、零发布(discover 阶段 3 次图片
  下载为本地落盘,非微信上传)。
- `upgrade_regression.py` **ALL PASS**(排除清单仍 1 项,cross-side 仍 SKIP)。
- 路径 a 复核项:lock 双侧 `81F9342A617893FBE3C51C4FCDCFFCB89E76D43EE4735F5FDB81B6422B951058`
  **未变**;台账仍 **7 条**;四锁 hash_ok 全 true;doctor PASS;安装侧经正式安装器
  同步后与 repo HEAD 逐字一致(OBS_68 MATCH)。
- 阶段状态:aihot / super_writer / zh_human_writing receipt 全部 OK;
  media_enrichment 停在 AWAITING_MEDIA_ASSET_APPROVAL。

## 变更文件(wxgzh-pipeline 仓,`dev/0.1.0-dev2`)

- `wxgzh_pipeline/writing_contract.py`(新增):OBS-88 写作合同校验
- `wxgzh_pipeline/stages/super_writer.py`:注入路径强制挂载
- `wxgzh_pipeline/producers.py`:AGENT_INSTRUCTIONS 指示;注入 meta 同构;
  discover 暂停绑定 registry 哈希
- `tests/test_obs88_writing_contract.py`(新增,11 项)+ `tests/fixtures/obs88/`
- `audit/quality/obs88-codeblock-66.md`(本报告)
