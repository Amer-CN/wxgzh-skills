# OBS-74 — 四轮本地补丁回流与 lock 内部不一致

- 状态:代码已回流;lock 待修(不属本档范围)
- 首次记录:档 39(--apply 预填 reason「OBS-74:回流 OBS-53 补丁,修正 lock 内部不一致」,未执行)
- 本文件:档 39R 第四步第 11 项按审核者指令更新描述

## 描述(档 39R 更新后)

四轮补丁曾长期未回流;代码已回流至 restore/local-patches-obs42-53;
lock 的 full_commit_sha 仍指向 cedf92ca,待修。

## 背景事实

- 四轮本地补丁(obs42/43、obs44-46、obs47、obs53)此前仅存在于本地安装树,从未推送;lock 的 media `skill_root_sha256=0d8aea21…` 长期指向无远端副本的本地树。
- 档 39R(2026-08-02)已按时间顺序拆分为 4 个 commit 推送到 Amer-CN/media-enrichment 新分支 `restore/local-patches-obs42-53`,HEAD = `2595e01465399eb34a10a56b190399039578da9e`。
- 新分支树经全新 clone 实算:root `0d8aea21…` / manifest `172aa1b8…` / count 57,与 lock 逐字一致。
- lock 的 `full_commit_sha` 仍为 `cedf92ca45b0cdb7e010d489e9da67dd28ef6e59`(未改,档 39R 禁止动 lock);lock 内部不一致(commit sha ↔ root sha 指向不同树)尚未修复,留待后续单独处理(建议:relock --apply 仅更新 full_commit_sha 指向 `2595e01…`,需先确认 relock 是否支持该字段,不支持则需能力扩展后另行授权)。
