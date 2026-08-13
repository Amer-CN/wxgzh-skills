# OBS-62 · 草稿 media_id 脱敏碰撞 → 校验误报

## 状态

| 部分 | 归属 | 处置 |
|---|---|---|
| 校验侧(DRAFT_DELTA 误报) | Pipeline `validators/validate_draft_delta.py` | 本档(OBS-62R)已修复:改为 total_count / update_time 判定,不依赖 media_id |
| 脱敏侧(media_id 前 8 字符 + `[REDACTED]` 碰撞) | gzh-design(被锁) | **转为推后项,与 OBS-59、OBS-60 同类** |

## 脱敏侧推后理由

- 脱敏代码位于被锁 gzh-design:`scripts/publish_wechat_draft.py::_desensitize_item`
  (`F:\AIXM\wxgzh\.agents\skills\gzh-design\scripts\publish_wechat_draft.py`,第 443-445 行)
- 该文件在 gzh-design 的 76 文件 runtime manifest 内
  (manifest sha `ced841439195453497e67a63186823f60eee7155b9de472e936c3d4d767e33b2`,
  锁定 commit `0007d7e6a4493aab59070d9c31dcde83830302fd`,
  version `v2026.07.18-hammer.1`,branch `chore/wxgzh-pipeline-dev2-integration`)
- 修改被锁 gzh-design 需走升版流程,故与 OBS-59、OBS-60 同类,留待 gzh-design 正式升版时处理

## 升版时的预期改法(未执行)

- 脱敏策略改为 `sha256(完整 media_id)` 前 16 位十六进制,不再保留任何明文前缀
- 字段名保持 `media_id` 不变;届时 Pipeline 校验继续使用 update_time 判定,无需再改

## 本档已做(Pipeline 侧,唯一代码改动)

- `validators/validate_draft_delta.py` 重写:
  1. `NEW_DRAFT_COUNT = after.total_count - before.total_count`,必须等于 1
  2. `draft_before.items` 的 `update_time` 集合必须是 `draft_after.items` 的子集
  3. `draft_after.items` 中恰好 1 条 `update_time` 不在 before 中
  4. `draft_creation_result.json` 的 `deleted_any/formally_published/mass_send/scheduled` 全为 false
  - 四项全通过才 `DRAFT_DELTA=PASS`;不读取 media_id
  - legacy 离线 fixture(`drafts[].fingerprint`,无 items)保留历史指纹判定
  - items 格式下 creation-result 文件缺失 → FAIL(严格关闭)
- 离线复算(未调用微信接口,只读已落盘数据):
  - RUN 20260801T182628-topic-ui5f7p → PASS
  - RUN 20260731T135947-ai-bbg4al → PASS
  - 构造「删一份建一份」模拟数据 → FAIL(证明新逻辑更严)
  - 结果落盘 `audit/runs/20260801T182628-topic-ui5f7p/stages/wechat_draft/delta_revalidation.json`

## 后续注意

- 已安装副本 `F:\AIXM\wxgzh\.agents\skills\wxgzh-pipeline\validators\validate_draft_delta.py`
  未同步(超出本档允许修改范围);下次运行前需经安装流程同步本变更
- 草稿箱现有 2 份草稿:未删除、未修改
