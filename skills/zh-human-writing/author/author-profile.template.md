# author/author-profile.template.md
# zh-human-writing v1 — 作者 Profile 模板
# 本文件是模板，不包含真实作者数据。
# 每个特征必须能够关联样本证据。

---

## 使用说明

1. 复制本模板
2. 根据作者样本填充各字段
3. 每个特征必须有 evidence_samples 和 evidence_excerpts
4. 无样本证据的特征不得进入正式 profile
5. 少于 3 个样本时不生成正式 profile
6. stable_features 需 ≥3 个样本一致

---

## 作者信息

- **作者名称**: [待填]
- **适用文体**: [essay / technical / social]

---

## 样本索引

| sample_id | source_url | source_hash | short_excerpt | word_count | collected_date | verification_status |
|-----------|-----------|-------------|---------------|------------|----------------|-------------------|
| [待填] | [待填] | [SHA-256] | [前200字] | [数字] | [日期] | [verified/unverified] |

---

## 稳定特征

> 只有在 ≥3 个样本中都观察到的特征才能标记为 stable。

### 特征 1
- **feature_id**: [待填]
- **feature_name**: [如"句长偏短"]
- **feature_type**: [sentence_length / paragraph_structure / vocabulary_preference / punctuation_habit / tone / register / opening_pattern / ending_pattern / transition_style / other]
- **description**: [具体描述]
- **evidence_samples**: [sample_id 列表]
- **evidence_excerpts**: [原文摘录，每条 ≤100 字]
- **confidence**: [high=5+样本一致 / medium=3-4样本一致]

---

## 允许变体

> 作者在不同场景下的风格变体。

### 变体 1
- **variant_name**: [待填]
- **applicable_genre**: [essay / technical / social]
- **description**: [待填]
- **evidence_samples**: [sample_id 列表]

---

## 禁止模仿项

> 不得在编辑中模仿的作者特征。

### 禁止项 1
- **item_name**: [待填]
- **reason**: [为什么不应模仿]
- **evidence_samples**: [sample_id 列表]

---

## 必须保留项

> 编辑中必须保留的作者特征。

### 保留项 1
- **item_name**: [待填]
- **reason**: [待填]
- **evidence_samples**: [sample_id 列表]

---

## 不确定特征

> 观察到但证据不足的特征。不进入正式 profile。

### 不确定特征 1
- **feature_name**: [待填]
- **description**: [待填]
- **evidence_samples**: [sample_id 列表]
- **uncertainty_reason**: [样本不足/场景单一等]

---

## 用户确认状态

- **confirmed**: [true/false]
- **confirmed_date**: [日期]
- **confirmed_by**: [确认者标识]
- **notes**: [备注]
