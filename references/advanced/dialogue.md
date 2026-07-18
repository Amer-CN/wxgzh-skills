# 高级组件 —— 对话（Dialogue）

> 用户/助手、访谈、排障问答。左右对称聊天窗布局。

## 输入语法

```markdown
:::dialogue title="排障问答"
@assistant: 粘贴后代码高亮丢失，是因为公众号会清洗 class 与外部 CSS。
@user: 那怎么保留样式？
@assistant: 必须使用内联 style 属性，所有样式写死在标签上。
@user: 明白了，谢谢！
:::
```

### 可选名称

```markdown
:::dialogue title="访谈记录"
@assistant name="排版助手": 你好，我是排版助手。
@user name="甲木": 请问如何保留代码高亮？
:::
```

## 最小输入

≥ 1 组对话（@user 或 @assistant 至少一个）

## 选择条件

- 源稿有问答/访谈/排障语义块
- 显式 `:::dialogue` 语法优先

## 禁止自动识别条件

- 无对话语义的普通段落不自动升级

## 降级方式

回退为普通引用段落

## 左右布局规则

| 角色 | 整行对齐 | 头像位置 | 气泡位置 | 气泡内部 |
|------|---------|---------|---------|---------|
| @assistant | `text-align:left` | 左侧 | 头像右侧 | `text-align:left` |
| @user | `text-align:right` | 右侧 | 头像左侧 | `text-align:left` |

### 元素顺序

- **assistant 行**：头像 → 气泡（avatar_index < bubble_index）
- **user 行**：气泡 → 头像（bubble_index < avatar_index）

### 连续消息

同一角色连续消息保持同一侧，不强制交替：

```
@assistant: 第一条消息
@assistant: 第二条补充
@user: 我的回复
@assistant: 最终回答
```

### 公众号兼容

- 使用 `display:inline-block` + `vertical-align:top` 实现并排
- 禁止 `flex` / `grid` / `float` / `position:absolute`
- 头像为 34px 圆形文字（"AI" / "我"），不依赖外部图片
- 气泡 `max-width:72%`，长文本自然换行

## HTML 模板

见 `tests/advanced-components/expected/dialogue-{theme}.html`（6 份）。


---

## 生产 HTML 模板（moyu-green 主题示例）

> 其他主题使用相同结构，仅替换色值。见 `theme-adapters.md`。

### assistant 行（左头像 + 右气泡）

```html
<section style="text-align:left;margin:0 0 12px;">
  <span style="display:inline-block;width:34px;height:34px;line-height:34px;text-align:center;border-radius:50%;font-size:12px;font-weight:700;vertical-align:top;background:#9CA3AF;color:#FFFFFF;"><span leaf="">AI</span></span>
  <section style="display:inline-block;max-width:72%;vertical-align:top;text-align:left;padding:10px 14px;margin-left:8px;background:#ECFDF5;border-radius:12px;">
    <p style="margin:0;font-size:14px;color:#374151;line-height:1.8;"><span leaf="">消息内容</span></p>
  </section>
</section>
```

### user 行（左气泡 + 右头像）

```html
<section style="text-align:right;margin:0 0 12px;">
  <section style="display:inline-block;max-width:72%;vertical-align:top;text-align:left;padding:10px 14px;margin-right:8px;background:#059669;border-radius:12px;">
    <p style="margin:0;font-size:14px;color:#FFFFFF;line-height:1.8;"><span leaf="">消息内容</span></p>
  </section>
  <span style="display:inline-block;width:34px;height:34px;line-height:34px;text-align:center;border-radius:50%;font-size:12px;font-weight:700;vertical-align:top;background:#047857;color:#FFFFFF;"><span leaf="">我</span></span>
</section>
```

> **关键**：user 行虽然整体 `text-align:right`，但气泡内部必须重新设置 `text-align:left`。
> user 气泡必须先输出，头像后输出。assistant 头像必须先输出，气泡后输出。

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/dialogue-*.html`。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。
