# 档 48 — OBS-31 字段口径统一 + 空值一致性排查(离线,未发起新 RUN)

- 报告编号:url-field-contract-48
- 执行日期:2026-08-03(Asia/Shanghai)
- 状态:**完成**。仅修改 `wxgzh_pipeline/producers.py` + 测试 + 报告;未发起新 RUN、未调微信接口、未修改被锁 skill / lock / 台账、未删除任何文件、未修改本轮 RUN 任何产物。
- 工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`(dev/0.1.0-dev2)

## 归因纠正(按指令)

档 46R 报告(e2e-verify-46R.md)原定性「本轮 aihot 交付数据质量问题」**更正为**:流水线缺陷,归入 **OBS-31**(aihot URL 在 `links.*`,`_dedup_index` 的 URL 提取缺少 `links.original` 回退,与 canonical_claim_registry 生成侧口径不一致,导致 FAIL_CLOSED)。档 46R 报告原文保留,另附更正段(见「归因更正」节)。

## 第一步 空值一致性排查(先查,结论:登记 OBS-81 并加固)

1. 比对逻辑原文(`wxgzh_pipeline/producers.py`):

```python
# _load_dedup_index(L359 修复前)
url = it.get("source_url") or it.get("url")

# registry 侧比对(修复前 L481-483)
if di["source_url"] != src:
    raise MediaRequestError(
        f"material {mid} source_url disagrees with dedup (FAIL_CLOSED)")
```

2. **判定:两侧 source_url 均为 None 时,比对表达式 `di["source_url"] != src` 为 False(不 raise)→ 判定为「一致(放行)」**。实际流程中该组合通常被更早的 registry 空值检查(L461 `if not mid or not src: raise`)兜底拦截,但比对逻辑本身对「两边都空」是放行的——在最缺来源信息的场景下,若前置检查被绕过或未来改动,校验会全通。这是真实安全缺陷。
3. 按指令**登记 OBS-81(高)**,并在第二步一并修复:任一侧取不到 URL 即 FAIL_CLOSED,不允许以「两边都空」构成一致。

## 第二步 字段口径统一

4-5. 新增单一同源函数 `_material_source_url(item)`(producers.py):

```python
def _material_source_url(item: dict) -> str | None:
    """Priority: source_url -> links.original(与 canonical_claim_registry
    生成侧逐字一致;任何改动必须只改这一处,禁止在别处重写该优先级)。"""
    url = item.get("source_url")
    if not url:
        links = item.get("links")
        if isinstance(links, dict):
            url = links.get("original")
    return url or None
```

`_load_dedup_index` 改用该函数;比对逻辑抽出为 `_check_material_url_consistency(mid, dedup_url, registry_url)`(任一侧为空 → FAIL_CLOSED「missing on one side」;两侧不同 → FAIL_CLOSED「disagrees」;两侧皆空 → FAIL_CLOSED,绝不判一致),registry 校验点调用它。

6. 优先级说明(据实):修复前两侧优先级**本就不同**——dedup 侧为 `source_url → url`,registry 生成侧(档 46R 起)为 `source_url → links.original`。统一采用 **registry 侧**(source_url → links.original),理由:① registry 是 canonical 对照基准;② AI HOT 数据实际只有 source_url 或 links.original,`url` 层无真实数据,保留它只会再造一个分裂点(已在函数注释中说明)。

## 第三步 全局排查(素材 URL 读取点清单)

| 位置 | 用途 | 口径 | 处理 |
|---|---|---|---|
| producers.py `_load_dedup_index`(L359) | dedup 索引 source_url | 修复前 source_url→url;修复后 source_url→links.original(同源函数) | **统一(本次修复)** |
| producers.py registry 校验(L455-485) | registry material source_url 与 dedup 比对 | 读 registry 字段 + 同源比对函数 | **统一(本次修复)** |
| producers.py L500/L512 | material/claim 的 source_url 透传进 media request | 透传,无口径选择 | 保留 |
| producers.py `_load_approvals` L312-313 | 批准合同 source_url(用户批准文件) | 独立语义(批准对象),非素材提取 | 保留(有意不同) |
| stages/media_enrichment.py L13 `source_url_first: True` | media request 内 URL 顺序配置(media skill 消费) | 消费侧配置,非提取 | 保留 |
| media-enrichment skill input_contract/validate(被锁) | 消费方校验 | 被锁 skill,本档不动 | 保留 |

结论:素材 URL 的「提取」仅两处语义点(dedup 侧 + registry 生成约定),已统一到同一函数;其余为透传/批准语义/被锁消费方,不统一。无其他同类口径缺失点。

## 第四步 测试

新增 `tests/test_obs31_url_contract.py`(8 项,全部 PASS):

| 要求 | 覆盖 |
|---|---|
| a. 仅有 links.original → 正确取到且校验通过 | TestMaterialSourceUrl::test_links_original_fallback + 真实 RUN 回归 |
| b. 仅有 source_url → 行为不变(回归) | test_source_url_wins_over_links |
| c. 两侧 URL 真实不同 → FAIL_CLOSED | TestConsistencyCheck::test_different_urls_fail_closed |
| d. 任一侧取不到 → FAIL_CLOSED | test_one_side_missing_fails_closed(两侧各测) |
| e. 两侧均取不到 → FAIL_CLOSED,不判一致 | test_both_sides_missing_fails_closed_not_consistent(OBS-81) |
| 11. 本轮 RUN 真实产物离线回归 | test_real_run_dedup_and_registry_agree:复制 RUN `20260802T220853…` 的 aihot/deduplicated_items.json → `_load_dedup_index` → 12 条 material 全部通过一致性校验(只读,未执行 media 阶段、未上传任何图片) |

## 第五步 复核

12. `upgrade_regression.py` ALL PASS,排除清单仍 1 项;四锁 dry-run 无变化。
13. doctor `--require-wechat` 双侧 PASS(exit 0),四锁 hash_ok 全 true,FAIL_CLOSED=false;档 42 WARN:`OBS_69=MATCH`、`OBS_68=MATCH`(581/581)。
14. 正式安装器同步(bundle-staging-48):安装侧与 repo HEAD **581 文件逐字一致**(0 差异)。
15. 四锁 root 未变(`46a00a1b…`/`18491b36…`/`0d8aea21…`/`f59d64bb…`);lock 双侧 sha 均 `8fb33d83…`;台账仍 2 条。
16. 本轮 RUN 产物完好:三阶段 produced 文件 sha 与 `agent_handshake.json` 记录逐字一致(未被修改);本档未调微信接口,以档 46R 预检(草稿箱 total_count=3)与本档零副作用为准,草稿箱仍 3 份。
17. **档 49 续跑判定(据实)**:**可直接续跑(resume),无需重跑前三阶段**。依据:
   - `verify_receipt` 校验范围 = 阶段产物 output_hashes / input_hashes / 被锁 skill 的 entrypoint-validator sha / official validators;`producers.py` 是 Pipeline 编排代码,不在任何已收 receipt 的绑定范围内,修改它不影响任何 receipt 的 hash 校验。
   - 前三阶段产物未被修改(第 16 项)→ aihot / super_writer / zh_human_writing receipts 全部仍有效。
   - resume 语义:completed_stages 通过 FULL 校验后从 media_enrichment 继续;修复后 `_load_dedup_index` 对现有产物能取到 `links.original`,与 registry 一致 → media discover 可进入批准等待。无需重写 aihot 产物(这也符合档 48「禁止手工修改本轮 RUN 产物」)。

## 归因更正(追加于 e2e-verify-46R.md)

档 46R 报告「根因…责任在本轮 aihot 交付数据缺字段,非流水线缺陷」表述**作废**,更正为:流水线缺陷 OBS-31(aihot URL 位于 `links.*`,`_dedup_index` 提取缺少 `links.original` 回退,与 registry 侧口径不一致);并新增 OBS-81(空值一致性:两侧皆空曾被判一致,已显式 FAIL_CLOSED)。

## 风险点

1. registry 生成侧(agent 交付约定)与 `_material_source_url` 的同步依赖约定与测试(真实 RUN 回归已覆盖);若未来 registry 生成口径变化,须同步修改该函数并跑回归。
2. `url` 中间层别名被移除:若历史数据中存在仅带 `url` 字段的素材,将按「任一侧取不到」FAIL_CLOSED(安全方向)。
3. OBS-81 的加固消除了对前置空值检查的隐式依赖,后续若有代码走查可确认 L461 与比对处双保险一致。
