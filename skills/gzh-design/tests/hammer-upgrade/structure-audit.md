# 锤子主题 ↔ 摸鱼绿主题 结构对照审计报告

> 基线：`theme-moyu-green.md`（936 行） vs `theme-hammer.md`（989 行）
> 审计方法：逐行对照 13 个主组件的 HTML 代码块，分离结构属性与颜色属性
> 审计日期：2026-07-19
> 审计结论：**两主题结构完全同构，无结构性偏差需修复**

---

## 对照标准

| 类别 | 是否允许不同 |
|------|-------------|
| 色值（#XXXXXX / rgba / rgb） | ✅ 允许 |
| 与颜色相关的 rgba 透明度 | ✅ 允许 |
| 色彩名称文案（"绿色"→"砖红"、"黄色"→"陶土"） | ✅ 允许 |
| 锤子主题独有的语义色/对比度说明 | ✅ 允许 |
| HTML 节点层级 | ❌ 不允许 |
| 组件顺序 | ❌ 不允许 |
| font-size | ❌ 不允许 |
| line-height | ❌ 不允许 |
| letter-spacing | ❌ 不允许 |
| margin / padding / gap | ❌ 不允许 |
| width / max-width | ❌ 不允许 |
| border-radius | ❌ 不允许 |
| display / flex 相关属性 | ❌ 不允许 |
| 目录横向滚动结构 | ❌ 不允许 |
| 章节标题结构 | ❌ 不允许 |
| 正文层级 | ❌ 不允许 |
| footer CTA 结构 | ❌ 不允许 |

---

## 逐组件对照结果

### 组件 1 全局容器

| 属性 | 摸鱼绿 | 锤子 | 一致？ |
|------|--------|------|--------|
| max-width | 677px | 677px | ✅ |
| margin | 0 auto | 0 auto | ✅ |
| background | #ffffff | #ffffff | ✅ |
| font-family | 同 | 同 | ✅ |
| color | #374151 | #555555 | ✅（颜色差异） |
| line-height | 1.75 | 1.75 | ✅ |
| letter-spacing | 0.5px | 0.5px | ✅ |
| overflow-x | hidden | hidden | ✅ |

**结论：结构完全一致，仅 color 不同（合理颜色差异）**

---

### 组件 2 封面 cover-breaking

| 属性 | 摸鱼绿 | 锤子 | 一致？ |
|------|--------|------|--------|
| 外层 margin/border-radius/box-shadow | 0 0 32px / 20px / 0 4px 20px rgba(0,0,0,0.06) | 同 | ✅ |
| border | 1.5px solid rgba(5,150,105,0.15) | 1.5px solid rgba(179,89,59,0.15) | ✅（颜色差异） |
| 内层 padding | 32px 28px 28px | 32px 28px 28px | ✅ |
| 顶部行 flex | gap:8px, margin-bottom:28px | 同 | ✅ |
| 圆点 width/height/border-radius | 6px / 6px / 50% | 同 | ✅ |
| 顶部标签 font-size/font-weight/letter-spacing | 11px / 700 / 3px | 同 | ✅ |
| 分隔线 flex:1 / height:1px | 同 | 同 | ✅ |
| 日期 font-size | 10px | 10px | ✅ |
| 主标题 font-size/font-weight/line-height/letter-spacing | 24px / 900 / 1.05 / -2px | 同 | ✅ |
| 装饰短线 width/height/border-radius | 48px / 3px / 2px | 同 | ✅ |
| 副标题 font-size/line-height | 13px / 1.7 | 同 | ✅ |
| 图片槽 width/height/border-radius | 110px / 110px / 16px | 同 | ✅ |
| 底部品牌条 padding | 12px 28px | 12px 28px | ✅ |
| 底部标签 padding/border-radius/font-size | 1px 6px / 3px / 8px | 同 | ✅ |
| 有图版 / 无图版 | 均存在 | 均存在 | ✅ |

**结论：结构完全一致，仅颜色不同（#059669→#B3593B 等）。有图版和无图版均保留。**

---

### 组件 3 目录 toc-scroll

| 属性 | 摸鱼绿 | 锤子 | 一致？ |
|------|--------|------|--------|
| 外层 margin | 0 20px 32px | 同 | ✅ |
| 标题行 flex/justify | space-between | 同 | ✅ |
| 标题 font-size/letter-spacing | 10px / 2px | 同 | ✅ |
| 滚动容器 overflow-x/white-space | scroll / nowrap | 同 | ✅ |
| padding-bottom | 8px | 8px | ✅ |
| 卡片 width/border-radius/padding | 110px / 12px / 12px | 同 | ✅ |
| 卡片 margin-right | 8px | 8px | ✅ |
| 第一卡片背景 | linear-gradient(135deg,#059669,#10B981) | linear-gradient(135deg,#B3593B,#C86442) | ✅（颜色差异） |
| 后续卡片 border/border-radius | 1px / 12px | 同 | ✅ |
| 卡片文字 font-size | 9px / 13px / 10px | 同 | ✅ |
| PART /// 最后卡片 | 存在 | 存在 | ✅ |

**结论：结构完全一致，横向滚动结构保留，第一卡高亮 + 后续白底 + PART /// 均一致。**

---

### 组件 4 章节标题 chapter-title

| 属性 | 摸鱼绿 | 锤子 | 一致？ |
|------|--------|------|--------|
| margin-top（首章/后续） | 16px / 48px | 16px / 48px | ✅ |
| margin-bottom | 32px | 32px | ✅ |
| padding | 0 20px | 0 20px | ✅ |
| flex gap | 16px | 16px | ✅ |
| 大编号 font-size/font-weight/line-height | 28px / 900 / 1 | 同 | ✅ |
| 大编号 letter-spacing | -2px | -2px | ✅ |
| PART font-size/font-weight/letter-spacing | 8px / 700 / 2px | 同 | ✅ |
| 竖线 width/height | 1px / 36px | 同 | ✅ |
| 中文标题 font-size/font-weight/letter-spacing | 17px / 900 / 0.3px | 同 | ✅ |
| 英文副标题 font-size/font-weight/letter-spacing | 11px / 600 / 1.5px | 同 | ✅ |

**结论：结构完全一致。编号 + PART + 竖线 + 标题 + 副标题层级完全匹配。**

---

### 组件 5 正文段落 paragraph

| 属性 | 摸鱼绿 | 锤子 | 一致？ |
|------|--------|------|--------|
| margin-bottom | 16px | 16px | ✅ |
| font-size | 14px | 14px | ✅ |
| line-height | 1.9 | 1.9 | ✅ |
| text-align | justify | justify | ✅ |

**结论：完全一致。**

---

### 组件 6 行内样式（9 种 + 使用原则）

| 子组件 | 结构属性 | 一致？ | 颜色差异 |
|--------|----------|--------|----------|
| 6a 加粗 | `<strong style="color:...;">` | ✅ | #059669 → #B3593B |
| 6b 背景标签 | padding:0 4px, border-radius:2px | ✅ | rgba(5,150,105,0.1) → rgba(179,89,59,0.10) |
| 6c 渐变高亮 | linear-gradient(120deg,...), padding:0 4px, border-radius:2px | ✅ | #FDE68A → #E3C6B9, #111827 → #555555 |
| 6d 底部高亮 | border-bottom:3px solid, font-weight:bold, padding-bottom:2px | ✅ | #FDE68A → #E3C6B9, #111827 → #555555 |
| 6e 下划线 | border-bottom:2px solid, font-weight:600 | ✅ | #A7F3D0 → #EAD6CC |
| 6f 红色下划线 | border-bottom:2px solid #FECACA | ✅ | 完全相同 |
| 6g 代码标签 | padding:2px 6px, border-radius:4px, font-size:13px | ✅ | #F3F4F6→#F7F7F7, #1F2937→#555555 |
| 6h 获取方式标签 | padding:2px 6px, border-radius:4px, font-size:13px | ✅ | #FDE68A→#E3C6B9, #1F2937→#555555 |
| 6i 删除线 | padding:2px 6px, border-radius:4px, text-decoration:line-through | ✅ | #F3F4F6→#F7F7F7, #6B7280→#737373 |

**结论：9 种行内样式的结构属性全部一致，仅颜色不同。**

**已修复的命名偏差**：6d 标题原为"黄色底部高亮"但实际使用陶土色 `#E3C6B9`，已修正为"陶土底部高亮"以与实际颜色一致（与 10c "陶土警告框" 命名风格统一）。

---

### 组件 7 内容标签组（STEP / CASE / SKILL / TOOL）

| 子组件 | 结构属性 | 一致？ |
|--------|----------|--------|
| 7a step-label | margin-bottom:24px, gap:8px, margin-bottom:10px, font-size:10px/15px, padding:2px 8px, border-radius:12px | ✅ |
| 7b case-label | margin-bottom:28px, 同上结构 | ✅ |
| 7c skill/tool-label | margin-bottom:28px, 同上结构 | ✅ |

**结论：结构完全一致。标签背景色从 #111827/#E5E7EB 改为 #555555/rgba(202,202,199,0.18) 是合理颜色差异。**

---

### 组件 8 代码/命令/Prompt

| 子组件 | 结构属性 | 一致？ |
|--------|----------|--------|
| 8a prompt-block | font-size:13px, margin:0 0 16px, line-height:1.8, label padding:1px 7px, border-radius:3px | ✅ |
| 8b cmd-block | font-size:13px, margin:0 0 24px, line-height:1.8, label padding:1px 7px, code padding:2px 6px, border-radius:4px | ✅ |
| 8c 多行代码块 | 指引文字结构一致，左竖条色值指引不同 | ✅ |

**结论：结构完全一致。**

---

### 组件 9 引用与亮点

| 子组件 | 结构属性 | 一致？ |
|--------|----------|--------|
| 9a quote-box | border:1px dashed, border-radius:8px, padding:12px 16px, margin-bottom:24px | ✅ |
| 9b oneliner-card（3 种变体） | border:1px dashed, border-radius:8px, padding:14px 16px, margin-bottom:24px, text-align:center | ✅ |
| 9c subtitle-highlight | font-size:15px, font-weight:900, margin-bottom:16px, linear-gradient(180deg,transparent 65%,...) | ✅ |
| 9d center-divider | font-size:14px, margin-bottom:20px, text-align:center, border-top+border-bottom:1px solid, padding:12px 0 | ✅ |

**结论：结构完全一致，虚线框保留，金句卡片 3 种变体均一致。**

---

### 组件 10 提示与信息

| 子组件 | 结构属性 | 一致？ |
|--------|----------|--------|
| 10a warn-tip | padding:6px 0 4px, margin-bottom:16px, font-size:12px/13px | ✅ |
| 10b green-tip/砖红提示 | 同上结构 | ✅ |
| 10c yellow-warning/陶土警告 | border-radius:12px, padding:12px 16px, margin-bottom:20px | ✅ |
| 10d green-info/砖红信息 | padding:12px 16px, border-radius:8px, border:1px solid, margin-bottom:20px | ✅ |

**结论：结构完全一致。警告色 rgb(255,76,0) / rgb(136,136,136) 两主题相同。**

---

### 组件 11 布局组件

| 子组件 | 结构属性 | 一致？ |
|--------|----------|--------|
| 11a pill-list | border-radius:999px, padding:3px 10px, dot 6px/6px/50% | ✅ |
| 11b flow-cards | 3 卡 flex, gap:6px, padding:10px 8px, border-radius:8px, 箭头 padding:0 4px | ✅ |
| 11c three-col-cards | 3 列 flex, gap:6px, 同上 | ✅ |
| 11d timeline | dot 14px/14px/50%/border:3px solid, line width:2px/min-height:48px, margin-right:16px | ✅ |
| 11e tool-card | border-radius:12px, padding:16px 20px, box-shadow:0 4px 16px | ✅ |
| 11f table | width:100%, border-collapse:collapse, font-size:13px, padding:8px 12px | ✅ |
| 11g ordered-list | circle 22px/22px/50%, gap:10px, margin-bottom:12px, font-size:14px/11px | ✅ |

**结论：全部 7 个布局组件结构完全一致。排列逻辑、卡片尺寸、圆角、间距均未改变。**

---

### 组件 12 媒体组件

| 子组件 | 结构属性 | 一致？ |
|--------|----------|--------|
| 12a image | text-align:center, margin-bottom:24px, border-radius:12px, overflow:hidden | ✅ |
| 12b video-card | border-radius:16px, padding:12px, margin-bottom:32px, border:2px solid, box-shadow:0 4px 12px | ✅ |

**结论：结构完全一致。**

---

### 组件 13 结尾组件

| 子组件 | 结构属性 | 一致？ |
|--------|----------|--------|
| 13a footer-cta | radial-gradient, border-radius:16px, padding:32px 20px, text-align:center | ✅ |
| - 3 个按钮 | width:40px, height:40px, border-radius:12px, margin:0 auto 6px | ✅ |
| - SVG 图标 | 完全相同的 path/circle/polyline | ✅ |
| - THANKS FOR READING | font-size:10px, letter-spacing:1px | ✅ |
| 13b brand-card | text-align:center, nodeleaf="" | ✅ |

**结论：结构完全一致。3 个互动按钮（点赞/在看/转发）的 SVG 图标、尺寸、间距完全相同，仅转发按钮的主色不同（#059669→#B3593B）。**

**说明差异**：摸鱼绿 13a 的说明文字引用旧版"签名文案适配"（`{{作者名}}` 占位符），锤子 13a 的说明文字引用升级版"固定结尾署名组件"。这是文档说明差异，非 HTML 结构差异，且锤子版本更准确——不影响结构一致性判定。

---

### 完整文章模板骨架

| 步骤 | 摸鱼绿 | 锤子 | 一致？ |
|------|--------|------|--------|
| 1. 封面 | 组件 2 | 组件 2 | ✅ |
| 2. 目录 | 组件 3，紧跟封面 | 同 | ✅ |
| 3. 开头引言 | 组件 9b | 同 | ✅ |
| 4. 前言正文 | 组件 5 × N | 同 | ✅ |
| 5. 第一章 | 组件 4, margin-top:16px | 同 | ✅ |
| 6. 第N章 | 组件 4, margin-top:48px | 同 | ✅ |
| 7. 结语章 | 编号 ///, PART 改 LAST | 同 | ✅ |
| 8. 互动三连 | 组件 13a | 同 | ✅ |
| 9. 品牌尾图 | 组件 13b | 同 | ✅ |

**结论：骨架顺序完全一致。**

---

### 视觉层级 / 文章类型配方 / Markdown 映射规则

三个章节的结构完全一致，仅色彩名称文案不同（"绿色"→"砖红"、"黄色"→"陶土"）。

---

## 总结

### 结构一致性

| 组件 | 结构一致 | 需修复 |
|------|----------|--------|
| 1 全局容器 | ✅ | — |
| 2 封面 | ✅ | — |
| 3 目录 | ✅ | — |
| 4 章节标题 | ✅ | — |
| 5 正文段落 | ✅ | — |
| 6 行内样式 | ✅ | 6d 标题命名修正 |
| 7 内容标签组 | ✅ | — |
| 8 代码/命令 | ✅ | — |
| 9 引用与亮点 | ✅ | — |
| 10 提示与信息 | ✅ | — |
| 11 布局组件 | ✅ | — |
| 12 媒体组件 | ✅ | — |
| 13 结尾组件 | ✅ | — |
| 骨架 | ✅ | — |
| 视觉层级 | ✅ | — |
| 配方表 | ✅ | — |
| 映射规则 | ✅ | — |

### 修复清单

| # | 文件 | 修复内容 | 类型 |
|---|------|----------|------|
| 1 | `references/theme-hammer.md` 第 348 行 | 6d 标题"黄色底部高亮"→"陶土底部高亮"（实际使用 #E3C6B9 陶土色，非黄色；与 10c "陶土警告框" 命名风格统一） | 命名准确性修正 |

### 无需修复的合理差异

- 所有颜色值差异（#059669→#B3593B 等）—— 合理颜色差异
- 日期/次要文字色差异（#D1D5DB→rgba(202,202,199,0.35) 等）—— 合理颜色差异
- 锤子独有的"语义色使用规则"章节 —— 允许的差异
- 13a 说明文字引用固定结尾署名组件 —— 文档说明差异，锤子版本更准确
- 视觉层级/配方表/映射规则中的色彩名称文案 —— 允许的差异

### 未修改的文件

- `references/theme-moyu-green.md` —— 未修改（基线文件，只读）
- 其他 5 个主题文件 —— 未修改
- `references/common-components.md` —— 未修改
- `references/advanced/theme-adapters.md` —— 未修改（锤子适配器已存在且正确）

---

*审计完成于 2026-07-19 | 源码 commit: 4053308 | 审计结论：结构完全同构*
