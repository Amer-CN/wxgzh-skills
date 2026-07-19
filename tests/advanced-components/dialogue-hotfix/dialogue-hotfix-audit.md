# Dialogue 热修复视觉验收审计

## 审计范围

对 dialogue 组件左右聊天窗热修复进行视觉验收审计，确认从"所有内容靠左的问答卡"改为"微信/QQ 式左右对称聊天窗口"。

## 审计文件

| 文件 | 说明 |
|------|------|
| `dialogue-conversation.md` | 对话源稿（8 轮对话，覆盖所有场景） |
| `dialogue-moyu-green.html` | 摸鱼绿主题样稿 |
| `dialogue-red-white.html` | 红白色系主题样稿 |
| `dialogue-graphite-minimal.html` | 石墨极简主题样稿 |
| `dialogue-zen-whitespace.html` | 留白禅意主题样稿 |
| `dialogue-moyu-ticket.html` | 摸鱼票据主题样稿 |
| `dialogue-olive-journal.html` | 橄榄手记主题样稿 |

## 场景覆盖

| 场景 | 对话轮次 | 验证结果 |
|------|---------|---------|
| 助手短消息 | 第 1 条 | ✅ 左头像+右气泡 |
| 用户短消息 | 第 2 条 | ✅ 左气泡+右头像 |
| 助手长消息 | 第 3 条 | ✅ 长文本自然换行，不溢出 |
| 用户短消息 | 第 4 条 | ✅ 右对齐行 |
| 用户连续消息 | 第 4-5 条 | ✅ 同侧连续，不强制交替 |
| 助手连续消息 | 第 6-7 条 | ✅ 同侧连续，不强制交替 |
| 用户结束消息 | 第 8 条 | ✅ 右对齐行 |

## 元素顺序验证（moyu-green 示例）

```
user       row: text-align:right  avatar@360  bubble@ 88  avatar_first=False
assistant  row: text-align:left   avatar@ 84  bubble@312  avatar_first=True
```

- **assistant 行**：avatar@84 < bubble@312 → 头像在气泡之前 ✅
- **user 行**：bubble@88 < avatar@360 → 气泡在头像之前 ✅

## 六主题色值验证

| 主题 | 用户气泡背景 | 用户文字 | 助手气泡背景 | 助手文字 | 用户头像 | 助手头像 |
|------|------------|---------|------------|---------|---------|---------|
| moyu-green | #059669 绿 | #FFFFFF | #ECFDF5 浅绿 | #374151 | #047857 深绿 | #9CA3AF 灰 |
| red-white | #DC2626 红 | #FFFFFF | #F5F5F5 浅灰 | #374151 | #991B1B 深红 | #9CA3AF 灰 |
| graphite-minimal | #27272A 深灰 | #FAFAFA | #FAFAFA 浅灰 | #52525B | #52525B 灰 | #A1A1AA |
| zen-whitespace | #F5F5F5 微底 | #2B2B2B | #FFFFFF 白 | #525252 | #4A5D52 | #A3A3A3 |
| moyu-ticket | #fffef8 纸感 | #1a1a1a | #fffef8 纸感 | #555 | #1a1a1a 黑 | #888 |
| olive-journal | #ed7b2f 橙 | #FFFFFF | #eeefe9 浅橄榄 | #4d4f46 | #1e1f23 墨 | #9ea096 |

## 公众号兼容性验证

| 检查项 | 结果 |
|--------|------|
| 禁止 div/class/id | ✅ 未使用 |
| 禁止 flex/grid | ✅ 未使用 |
| 禁止 float/position:absolute | ✅ 未使用 |
| 使用 display:inline-block | ✅ |
| 使用 text-align:left/right | ✅ |
| 全部内联样式 | ✅ |
| span leaf 包裹中文 | ✅ |
| validate_gzh_html ERROR=0 | ✅ 全部 6 主题 |
| validate_gzh_html WARNING=0 | ✅ 全部 6 主题 |

## 430px 移动端验证

- 气泡 max-width: 72% → 430px × 72% ≈ 310px，不溢出 ✅
- 头像 34px 固定宽度 → 不溢出 ✅
- 长文本自然换行 → 不溢出 ✅

## 移动端截图

> `dialogue-mobile-contact-sheet.png` 需在浏览器中打开 6 份 HTML 后截图。
> 当前环境无法自动生成截图，建议人工在 430px 视窗下查看 6 份 HTML。

## 审计结论

✅ dialogue 组件已从"所有内容靠左的问答卡"成功修复为"微信/QQ 式左右对称聊天窗口"。

- assistant：左头像 + 右气泡 ✅
- user：左气泡 + 右头像 ✅
- 用户气泡内部文字左对齐 ✅
- 6 主题全部更新 ✅
- 连续同角色消息保持正确侧别 ✅
- 公众号兼容性验证通过 ✅
