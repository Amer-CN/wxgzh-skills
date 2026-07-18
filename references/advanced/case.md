# 高级组件 —— 案例复盘（case）

> 实践案例、项目复盘、问题-行动-结果

## 输入语法

```markdown
:::case title="标题"\n@context: 背景\n@challenge: 挑战\n@action: 行动\n@result: 结果\n:::
```

## 最小输入

context/challenge/action/result 至少 3 项

## 选择条件

- 源稿有明确的实践案例、项目复盘、问题-行动-结果语义
- 显式 `:::case` 语法优先

## 禁止自动识别条件

- 无明确实践案例、项目复盘、问题-行动-结果语义的普通段落不得自动升级
- 不得自动补造数据、结果或行动建议

## 降级方式

回退为普通小标题段落

## 发布限制

- 正式 release HTML 禁止 `../assets/`、`file://`、本地磁盘路径
- 所有图片 `src` 必须是作者提供的可访问 HTTPS URL

## 六主题适配规则

见 [theme-adapters.md](theme-adapters.md)。组件语义跨主题一致，只有视觉语言不同。

## 生产 HTML 模板（moyu-green 主题示例）

> 其他主题使用相同结构，仅替换 `theme-adapters.md` 中的色值令牌。

```html
<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:#111827;line-height:1.5;"><span leaf="">镜像瘦身实践</span></p>
  <section style="margin:0 0 8px;padding:10px 14px;border-radius:0 12px 12px 0;border-left:3px solid #9CA3AF;background:#ECFDF5;">
      <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#9CA3AF;"><span leaf="">背景</span></p>
      <p style="margin:0;font-size:13px;color:#374151;line-height:1.7;"><span leaf="">一个 Node.js 服务的生产镜像初始体积为 1.2GB。</span></p>
    </section>
<section style="margin:0 0 8px;padding:10px 14px;border-radius:0 12px 12px 0;border-left:3px solid #9CA3AF;background:#ECFDF5;">
      <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#9CA3AF;"><span leaf="">挑战</span></p>
      <p style="margin:0;font-size:13px;color:#374151;line-height:1.7;"><span leaf="">部署慢，安全扫描耗时长。</span></p>
    </section>
<section style="margin:0 0 8px;padding:10px 14px;border-radius:0 12px 12px 0;border-left:3px solid #9CA3AF;background:#ECFDF5;">
      <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#9CA3AF;"><span leaf="">行动</span></p>
      <p style="margin:0;font-size:13px;color:#374151;line-height:1.7;"><span leaf="">改用多阶段构建，并移除开发依赖。</span></p>
    </section>
<section style="margin:0 0 8px;padding:10px 14px;border-radius:0 12px 12px 0;border-left:3px solid #059669;background:#ECFDF5;">
      <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#059669;"><span leaf="">结果</span></p>
      <p style="margin:0;font-size:13px;color:#374151;line-height:1.7;"><span leaf="">镜像降至 180MB，部署时间缩短约 60%。</span></p>
    </section>
</section>
```

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/case-*.html`（验收产物，非生产依赖）。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。
