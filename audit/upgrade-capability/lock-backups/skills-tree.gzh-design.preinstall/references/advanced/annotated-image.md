# 高级组件 —— 注释图片（annotated-image）

> 界面说明、架构图讲解、截图标注

## 输入语法

```markdown
:::annotated-image image="url" caption="说明"\n@note 1: 注释一\n@note 2: 注释二\n:::
```

## 最小输入

图片 URL + 至少 1 条注释

## 选择条件

- 源稿有明确的界面说明、架构图讲解、截图标注语义
- 显式 `:::annotated-image` 语法优先

## 禁止自动识别条件

- 无明确界面说明、架构图讲解、截图标注语义的普通段落不得自动升级
- 不得自动补造数据、结果或行动建议

## 降级方式

回退为普通图片 + 列表

## 发布限制

- 正式 release HTML 禁止 `../assets/`、`file://`、本地磁盘路径
- 所有图片 `src` 必须是作者提供的可访问 HTTPS URL

## 六主题适配规则

见 [theme-adapters.md](theme-adapters.md)。组件语义跨主题一致，只有视觉语言不同。

## 生产 HTML 模板（moyu-green 主题示例）

> 其他主题使用相同结构，仅替换 `theme-adapters.md` 中的色值令牌。

```html
<section style="margin:0 0 24px;"><section style="margin:0 0 10px;background:#F0FDF4;border-radius:12px;padding:6px;border:1px solid #BBF7D0;box-shadow:0 4px 16px -4px rgba(0,0,0,0.08);"><span leaf=""><img src="../assets/annotated-dashboard.png" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span></section><p style="margin:0 0 12px;font-size:12px;color:#9CA3AF;text-align:center;"><span leaf="">控制台关键区域</span></p><section style="margin:0 0 6px;padding:8px 12px;background:#ECFDF5;border-radius:12px;border-left:3px solid #059669;"><p style="margin:0;font-size:13px;color:#374151;line-height:1.7;"><span style="font-weight:700;color:#059669;margin-right:6px;"><span leaf="">1</span></span><span leaf="">左侧导航用于切换工作区</span></p></section><section style="margin:0 0 6px;padding:8px 12px;background:#ECFDF5;border-radius:12px;border-left:3px solid #059669;"><p style="margin:0;font-size:13px;color:#374151;line-height:1.7;"><span style="font-weight:700;color:#059669;margin-right:6px;"><span leaf="">2</span></span><span leaf="">中央区域显示实时状态</span></p></section><section style="margin:0 0 6px;padding:8px 12px;background:#ECFDF5;border-radius:12px;border-left:3px solid #059669;"><p style="margin:0;font-size:13px;color:#374151;line-height:1.7;"><span style="font-weight:700;color:#059669;margin-right:6px;"><span leaf="">3</span></span><span leaf="">右上角用于发布和导出</span></p></section></section>
```

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/annotated-image-*.html`（验收产物，非生产依赖）。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。
