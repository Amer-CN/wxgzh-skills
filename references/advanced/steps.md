# 高级组件 —— 步骤流程（steps）

> 操作教程、安装流程、部署流程

## 输入语法

```markdown
:::steps title="标题"\n1. 步骤一\n2. 步骤二\n:::
```

## 最小输入

至少 2 步

## 选择条件

- 源稿有明确的操作教程、安装流程、部署流程语义
- 显式 `:::steps` 语法优先

## 禁止自动识别条件

- 无明确操作教程、安装流程、部署流程语义的普通段落不得自动升级
- 不得自动补造数据、结果或行动建议

## 降级方式

回退为普通有序列表

## 发布限制

- 正式 release HTML 禁止 `../assets/`、`file://`、本地磁盘路径
- 所有图片 `src` 必须是作者提供的可访问 HTTPS URL

## 六主题适配规则

见 [theme-adapters.md](theme-adapters.md)。组件语义跨主题一致，只有视觉语言不同。

## 生产 HTML 模板（moyu-green 主题示例）

> 其他主题使用相同结构，仅替换 `theme-adapters.md` 中的色值令牌。

```html
<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:#111827;line-height:1.5;"><span leaf="">部署流程</span></p>
  <section style="margin:0 0 8px;padding:10px 14px;background:#ECFDF5;border-radius:0 12px 12px 0;border-left:3px solid #059669;">
      <p style="margin:0;font-size:14px;color:#374151;line-height:1.7;"><span style="font-weight:700;color:#059669;margin-right:8px;"><span leaf="">1</span></span><span leaf="">拉取镜像</span></p>
    </section>
<section style="margin:0 0 8px;padding:10px 14px;background:#ECFDF5;border-radius:0 12px 12px 0;border-left:3px solid #059669;">
      <p style="margin:0;font-size:14px;color:#374151;line-height:1.7;"><span style="font-weight:700;color:#059669;margin-right:8px;"><span leaf="">2</span></span><span leaf="">配置环境变量</span></p>
    </section>
<section style="margin:0 0 8px;padding:10px 14px;background:#ECFDF5;border-radius:0 12px 12px 0;border-left:3px solid #059669;">
      <p style="margin:0;font-size:14px;color:#374151;line-height:1.7;"><span style="font-weight:700;color:#059669;margin-right:8px;"><span leaf="">3</span></span><span leaf="">启动容器</span></p>
    </section>
<section style="margin:0 0 8px;padding:10px 14px;background:#ECFDF5;border-radius:0 12px 12px 0;border-left:3px solid #059669;">
      <p style="margin:0;font-size:14px;color:#374151;line-height:1.7;"><span style="font-weight:700;color:#059669;margin-right:8px;"><span leaf="">4</span></span><span leaf="">验证健康检查</span></p>
    </section>
</section>
```

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/steps-*.html`（验收产物，非生产依赖）。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。
