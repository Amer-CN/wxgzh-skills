# 高级组件 —— 清单（checklist）

> 发布前检查、迁移检查、安全检查

## 输入语法

```markdown
:::checklist title="标题"\n- [x] 已完成项\n- [ ] 未完成项\n:::
```

## 最小输入

至少 2 项

## 选择条件

- 源稿有明确的发布前检查、迁移检查、安全检查语义
- 显式 `:::checklist` 语法优先

## 禁止自动识别条件

- 无明确发布前检查、迁移检查、安全检查语义的普通段落不得自动升级
- 不得自动补造数据、结果或行动建议

## 降级方式

回退为普通列表

## 发布限制

- 正式 release HTML 禁止 `../assets/`、`file://`、本地磁盘路径
- 所有图片 `src` 必须是作者提供的可访问 HTTPS URL

## 六主题适配规则

见 [theme-adapters.md](theme-adapters.md)。组件语义跨主题一致，只有视觉语言不同。

## 生产 HTML 模板（moyu-green 主题示例）

> 其他主题使用相同结构，仅替换 `theme-adapters.md` 中的色值令牌。

```html
<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:#111827;line-height:1.5;"><span leaf="">发布前检查</span></p>
  <section style="margin:0 0 6px;padding:8px 12px;background:#ECFDF5;border-radius:12px;border-left:3px solid #059669;">
      <p style="margin:0;font-size:14px;color:#374151;line-height:1.7;text-decoration:line-through;"><span style="font-weight:700;color:#059669;margin-right:8px;"><span leaf="">✓</span></span><span leaf="">完成单元测试</span></p>
    </section>
<section style="margin:0 0 6px;padding:8px 12px;background:#ECFDF5;border-radius:12px;border-left:3px solid #059669;">
      <p style="margin:0;font-size:14px;color:#374151;line-height:1.7;text-decoration:line-through;"><span style="font-weight:700;color:#059669;margin-right:8px;"><span leaf="">✓</span></span><span leaf="">完成灰度验证</span></p>
    </section>
<section style="margin:0 0 6px;padding:8px 12px;background:#F0FDF4;border-radius:12px;border-left:3px solid #9CA3AF;">
      <p style="margin:0;font-size:14px;color:#9CA3AF;line-height:1.7;text-decoration:none;"><span style="font-weight:700;color:#9CA3AF;margin-right:8px;"><span leaf="">○</span></span><span leaf="">准备回滚预案</span></p>
    </section>
<section style="margin:0 0 6px;padding:8px 12px;background:#F0FDF4;border-radius:12px;border-left:3px solid #9CA3AF;">
      <p style="margin:0;font-size:14px;color:#9CA3AF;line-height:1.7;text-decoration:none;"><span style="font-weight:700;color:#9CA3AF;margin-right:8px;"><span leaf="">○</span></span><span leaf="">通知相关负责人</span></p>
    </section>
</section>
```

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/checklist-*.html`（验收产物，非生产依赖）。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。
