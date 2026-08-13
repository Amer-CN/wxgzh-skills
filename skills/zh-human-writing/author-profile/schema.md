# author-profile/schema.md
# zh-human-writing v1 — 作者 Profile Schema

---

## 概述

本文件定义作者 profile 的 schema。不包含真实作者数据。

核心原则：**无样本证据的特征不得进入正式 profile。**

---

## Schema 字段

### 1. sample_index（样本索引）
- 类型：list，最少 3 个
- 每个样本：sample_id, source_url, source_hash, short_excerpt, word_count, collected_date, verification_status

### 2. stable_features（稳定特征）
- 类型：list
- 只有在 ≥3 个样本中都观察到的特征才能标记为 stable
- 每个特征：feature_id, feature_name, feature_type, description, evidence_samples, evidence_excerpts, confidence
- confidence: high=5+样本一致, medium=3-4样本一致, low=不应进入stable

### 3. allowed_variants（允许变体）
- 类型：list，可选
- 作者在不同场景下的风格变体

### 4. prohibited_imitation（禁止模仿项）
- 类型：list
- 不得在编辑中模仿的作者特征

### 5. must_preserve（必须保留项）
- 类型：list
- 编辑中必须保留的作者特征

### 6. uncertain_features（不确定特征）
- 类型：list，可选
- 观察到但证据不足的特征，不进入正式 profile

### 7. evidence_articles（证据文章）
- 类型：list，最少 3 个
- 必须与 sample_index 一致

### 8. applicable_genres（适用文体）
- 类型：list，值为 essay/technical/social

### 9. user_confirmation_status（用户确认状态）
- 未确认的 profile 只作为参考，不用于自动编辑决策

---

## 生成规则

- 最少 3 个样本
- stable_features 需 ≥3 个样本一致
- 不允许基于"常识"或"风格感觉"添加特征
- 单一作者的风格不得被当作通用"好中文"标准
- 偶然特征（只在 1 篇文章中出现）不进入 stable_features

---

## 使用规则

### 何时使用
- source=author_written 且用户提供了作者样本
- 用户明确要求匹配特定作者风格

### 何时不用
- source=ai_draft 且无作者样本
- source=unknown
- 用户未确认 profile

### profile 做什么
- 在编辑中保留作者的 stable_features
- 在编辑中保留作者的 must_preserve 项
- 在编辑中避免模仿作者的 prohibited_imitation 项

### profile 不做什么
- 不注入原文没有的观点、感受、经历
- 不模仿作者的坏习惯
- 不把作者风格当作通用标准
- 不跨文体使用

---

## 空 Profile 处理

当没有作者样本时不生成 profile。编辑行为按默认规则执行：
- 不注入个性
- 仅删除 AI 痕迹
- 不模仿任何作者风格
- 不增加第一人称（除非原文已有）
- 不增加观点和感受
