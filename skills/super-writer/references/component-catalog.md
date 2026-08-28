# Super Writer 合法组件清单（单一真源：validate_semantic_map.py）

> 本文件由 77F/OBS-315 生成：合法组件名 = ALLOWED_ROLES；各组件 payload 形状 = ROLE_REQUIRED_FIELDS。
> 校验器注册表单一真源；未注册组件名直接拒并附合法清单指路（预检守卫）。

生成时间：77F | 角色数：41 | 来源：validate_semantic_map.py:ALLOWED_ROLES / ROLE_REQUIRED_FIELDS

## 角色清单（按字母序）

- `article_conclusion` — 必填 payload 字段：`heading_text`
- `article_cover` — 必填 payload 字段：`title, summary_or_intro`
- `article_cta` — 必填 payload 字段：`text, url`
- `article_intro` — 必填 payload 字段：`text`
- `article_section` — 必填 payload 字段：`heading_text, section_index`
- `article_signature` — 无必填 payload 字段
- `article_toc` — 必填 payload 字段：`toc_items`
- `case` — 无必填 payload 字段
- `checklist` — 必填 payload 字段：`items`
- `code` — 必填 payload 字段：`code_text`
- `code_comparison` — 必填 payload 字段：`before_code, after_code`
- `command` — 必填 payload 字段：`code_text`
- `comparison` — 必填 payload 字段：`subject_a, subject_b, dimensions, rows`
- `decision` — 必填 payload 字段：`recommended, options`
- `dialogue` — 必填 payload 字段：`messages`
- `example` — 必填 payload 字段：`text`
- `fact` — 必填 payload 字段：`items`
- `faq` — 必填 payload 字段：`items`
- `footnote` — 必填 payload 字段：`notes`
- `gallery` — 必填 payload 字段：`images`
- `image` — 必填 payload 字段：`image_url`
- `image_annotation` — 必填 payload 字段：`image_url, notes`
- `information` — 必填 payload 字段：`text`
- `key_statement` — 必填 payload 字段：`text`
- `long_image` — 必填 payload 字段：`image_url, caption`
- `media_text` — 必填 payload 字段：`image_url, explanation_text`
- `ordered_list` — 必填 payload 字段：`items`
- `paragraph` — 必填 payload 字段：`text`
- `pill_list` — 必填 payload 字段：`items`
- `process_flow` — 必填 payload 字段：`steps`
- `prompt` — 必填 payload 字段：`code_text`
- `quote` — 必填 payload 字段：`text`
- `resource_list` — 必填 payload 字段：`links`
- `secondary_emphasis` — 必填 payload 字段：`text, style_type`
- `statistic` — 必填 payload 字段：`value, label`
- `step_sequence` — 必填 payload 字段：`steps`
- `subtitle` — 必填 payload 字段：`heading_text`
- `timeline` — 必填 payload 字段：`events`
- `tip` — 必填 payload 字段：`text`
- `video` — 无必填 payload 字段
- `warning` — 必填 payload 字段：`text`

## Markdown 容器与 type 枚举（单一真源：gzh-design render_article.py）

> 77M/OBS-330: `:::` 指令容器的合法 type 值从 render_article.py 常量同步。
> 写作侧只能用下列枚举值，枚举外直接 FAIL 并指路本清单。

| 容器 | 合法 type 值 | 来源常量 |
|---|---|---|
| `:::alert` | note, tip, important, warning, caution | ALERT_TYPES |
| `:::quote` | normal, highlight, sourced | QUOTE_TYPES |

##  payload 形状总表

| role | 必填字段 |
|---|---|
| article_conclusion | heading_text |
| article_cover | title, summary_or_intro |
| article_cta | text, url |
| article_intro | text |
| article_section | heading_text, section_index |
| article_signature | — |
| article_toc | toc_items |
| case | — |
| checklist | items |
| code | code_text |
| code_comparison | before_code, after_code |
| command | code_text |
| comparison | subject_a, subject_b, dimensions, rows |
| decision | recommended, options |
| dialogue | messages |
| example | text |
| fact | items |
| faq | items |
| footnote | notes |
| gallery | images |
| image | image_url |
| image_annotation | image_url, notes |
| information | text |
| key_statement | text |
| long_image | image_url, caption |
| media_text | image_url, explanation_text |
| ordered_list | items |
| paragraph | text |
| pill_list | items |
| process_flow | steps |
| prompt | code_text |
| quote | text |
| resource_list | links |
| secondary_emphasis | text, style_type |
| statistic | value, label |
| step_sequence | steps |
| subtitle | heading_text |
| timeline | events |
| tip | text |
| video | — |
| warning | text |