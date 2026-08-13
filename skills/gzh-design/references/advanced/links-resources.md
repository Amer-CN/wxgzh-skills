# 高级组件 —— 链接与资源（Links & Resources）

> 2 个及以上作者提供的 HTTPS 链接的集合展示。

## 输入语法

```markdown
:::resources title="参考资料"
- [官方文档](https://example.com/docs)
- [项目仓库](https://github.com/example/repo)
:::
```

## 最小输入

≥ 2 个 HTTPS 链接

## 选择条件

- 源稿有 2 个及以上作者提供的 HTTPS 链接且语义为"参考资料"
- 显式 `:::resources` 语法优先

## 禁止自动识别条件

- 只 1 个链接时使用原版链接，不生成资源模块
- 非参考资料语义的链接列表不自动升级

## 降级方式

回退为普通链接文本

## HTML 模板

见 `tests/advanced-components/expected/resources-{theme}.html`（6 份）。


---

## 生产 HTML 模板（moyu-green 主题示例）

> 其他主题使用相同结构，仅替换 `theme-adapters.md` 中的色值令牌。

```html
<section style="margin:0 0 24px;"><p style="margin:0 0 12px;font-size:15px;font-weight:700;color:#111827;line-height:1.5;"><span leaf="">参考资料</span></p>
  <section style="margin:0 0 8px;padding:10px 14px;background:#ECFDF5;border-radius:12px;border-left:3px solid #059669;"><p style="margin:0;font-size:14px;color:#111827;font-weight:600;line-height:1.6;"><span leaf="">官方文档</span></p><p style="margin:2px 0 0;font-size:12px;color:#9CA3AF;"><span leaf="">https://example.com/docs</span></p></section>
<section style="margin:0 0 8px;padding:10px 14px;background:#ECFDF5;border-radius:12px;border-left:3px solid #059669;"><p style="margin:0;font-size:14px;color:#111827;font-weight:600;line-height:1.6;"><span leaf="">项目仓库</span></p><p style="margin:2px 0 0;font-size:12px;color:#9CA3AF;"><span leaf="">https://github.com/example/repo</span></p></section>
</section>
```

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/resources-*.html`（验收产物，非生产依赖）。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。
