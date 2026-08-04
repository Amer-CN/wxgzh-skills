# 档 67B — push 补齐 + 归属举证(零改动)

- 性质:**零代码改动**。唯一写入为本报告;未启用视觉分级、未 continue 媒体阶段、
  未批准资产、未调微信接口。
- 网络状态:github.com:443 **可达**(Test-NetConnection=True),push 已完成。

## 1. push 补齐

- `64c4abc43194ff7651ae74a1b590119d2b380bbe`(档67 视觉分级)已 push,远端可见:
  `git merge-base --is-ancestor 64c4abc origin/dev/0.1.0-dev2` → True。
- 同批推送还带上后续 commit `ae59767`(档67A 第八次 relock)——远端 HEAD 现为
  `ae59767`(含 64c4abc)。**档 67 第二段采信条件已满足**;档 67A 第八次 relock
  亦已远端可见(67C 第 16 项届时复核)。

## 2. 举证冲突一:validation_config.json 是否存在

- 电车 RUN(档49/50 主体 `20260802T220853-codex-sol-luna-max-m6pyv4`):
  `F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260802T220853-codex-sol-luna-max-m6pyv4\media_enrichment\validation_config.json`
  → **不存在**(Test-Path=False)。
- 本 RUN(档66 `20260804T174355-vibe-coding-guide-v2-1-6-by4s00`):同路径 → **不存在**。
- 存档 RUN1(档18 时代 `20260731T135947-ai-bbg4al`):
  `F:\AIXM\wxgzh\repos\wxgzh-pipeline\audit\runs\20260731T135947-ai-bbg4al\stages\media_enrichment\validation_config.json`
  → **存在**,sha256 `38A6C67D3A1B2E558C9AF43958EF5DC0CEA4B8E60D96A96DD21C75D4FFC21511`,全文:
  ```json
  {
    "approval_id": "AP-20260731T1449-INDEPENDENT-REVIEW-001",
    "body_images_min": 2,
    "default_value": 6,
    "reason": "候选池仅 4 张待审查资产,审核者批准 2 张,凑不出 6 张",
    "set_by": "independent_reviewer"
  }
  ```
- **裁定**:以**档 49/50 结论为准**(电车 RUN 不存在 → `content_validate` 走
  `source='default'`,body_images_min=6)。档 67 报告中「RUN1 的 reviewer 设
  body_images_min=2 路径」引自**存档 RUN1**(存在),两条证据并存不矛盾:
  电车 RUN 无 config,存档 RUN1 有 config(档 18 时代人工降阈留痕)。依据:
  档 49/50 针对电车 RUN 实测阶段产物;存档 RUN1 是另一条历史 RUN 的归档,
  不构成对电车 RUN 的否定。

## 3. 举证冲突二:validate_media_bindings.py 实际位置

- 绝对路径:`F:\AIXM\wxgzh\repos\wxgzh-pipeline\validators\validate_media_bindings.py`
- 所属仓库:**wxgzh-pipeline(管线仓库),非被锁 media-enrichment**。
- sha256:`470693397BCDBD83A0BA9ACA424C688922548A0DF7A07E99341CB83546A8A462`
- L1-30 原文:
  ```python
  #!/usr/bin/env python3
  """Media bindings validator: each bound image must be eligible + upload success
  + mmbiz.qpic.cn remote_url + binding sha256 == manifest sha256; and >= 6 images.
  """
  from __future__ import annotations
  import argparse, json, sys
  from pathlib import Path
  from urllib.parse import urlparse

  MIN_BODY_IMAGES = 6
  TARGET_BODY_IMAGES = 8
  MMBIZ_HOSTS = ("mmbiz.qpic.cn", "mmbiz.qlogo.cn")

  def _exact_wechat_url(url: str) -> bool:
      """dev2-hotfix2: https + hostname EQUALS a WeChat image host."""
      ...
  def validate(media_manifest, bindings, body_images_min: int = MIN_BODY_IMAGES, ...):
      ...
  ```
- 与被锁 media required_files 的关系:lock 中 media-enrichment
  `required_files = ["scripts/run_media_enrichment.py", "scripts/validate_media_manifest.py",
  "src/media_enrichment/uploader.py", "src/media_enrichment/article_bindings.py"]`;
  **validate_media_bindings.py 不在其中**——它是管线仓库 `validators/` 的官方校验器
  (由 `stages/media_enrichment.py content_validate` 经 `load_validator` 加载),
  与被锁侧的 `scripts/validate_media_manifest.py`(media 子进程独立运行的 manifest
  校验器)是**两个不同文件、两侧职责**。档 67 报告将其列为「Pipeline 仓库的校验器」
  正确;本档给出绝对路径与 sha 钉死。

## 4. 被锁 media-enrichment 侧是否存在 body_images/min 检查

- **不存在**。检索命令与结果(安装侧 + repo checkout 均空):
  ```
  rg -rn "body_images_min|BODY_IMAGES_MIN|MIN_BODY" F:\AIXM\wxgzh\.agents\skills\media-enrichment -g "*.py"
  → (无匹配)
  rg -rn "body_images_min|MIN_BODY" F:\AIXM\wxgzh\repos\media-enrichment -g "*.py"
  → (无匹配)
  ```
- 依据:media 侧 manifest/绑定校验仅做资产级一致性(eligible/upload/mmbiz/sha),
  无 body 数量下限;数量下限完全在管线侧 `validate_media_bindings.py`(见举证 3)。

## 5. 档 67 视觉权重依据的环境声明

- `250px vs 211px`(10 行代码块 ≈250px、16:9 图 375px 宽 ≈211px)是**浏览器/几何
  估算**(CSS line-height×行数 + padding 推算),**不是微信编辑器实测**。
- ★**确认该依据不成立为微信端证据**:它只支持「结构上同量级」的推演,未经微信
  编辑器呈现验证,不满足档 67 第四步「依据必须是微信端呈现」的硬要求。档 67A 已
  声明微信端人工预览未执行(无微信编辑器访问能力);视觉分级方案在 push + 微信端
  确认前保持挂起,由用户裁决。

## 6. 复核(如实,含与指令预期的差异)

- 零改动:除本报告外无任何代码/产物修改;未启用视觉分级、未 continue、未批准、
  零微信调用。
- ★lock/台账与 67B 指令预期(81F9342A / 7 条)存在差异——**如实说明**:
  - 当前 lock 双侧 `1B15939B8875BD868B789C78DCB73C20D70E8405D948F33E23D0EB3BA8621D66`
    (一致);台账 **8 条**(末条 `relock-gzh-design-20260804T130644Z-1657b49a`)。
  - 差异原因:档 67A 已执行第八次真实 relock(本地 commit `ae59767`,本档已 push)。
    指令写 67B 时假设 67A 前的 81F9342A/7 条基线;实际环境处于 67A 之后。
    按「第 8 次 relock 未 push 则不予采信」的裁定,push 已在本档完成 → 采信条件满足。
- doctor:本档以全权限环境复跑,应 PASS(上一只读沙箱会话中 FAIL 的唯一原因是
  `project_writable=false` 沙箱限制;`OBS_68/69` 当时已 MATCH)。

## 变更文件

- `audit/quality/threshold-attribution-67B.md`(本报告)
