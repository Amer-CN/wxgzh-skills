# 高级组件 —— 媒体（Media）

> 包含 media-text（图文绑定）、gallery（图片画廊）、long-image（长图展示）。

## 输入语法

### media-text
```markdown
:::media-text
![说明](https://example.com/img.png)
这是与图片绑定的解释段落。
:::
```

### gallery
```markdown
:::gallery title="安装过程"
![说明一](https://example.com/1.png)
![说明二](https://example.com/2.png)
:::
```

### long-image
```markdown
:::long-image image="https://example.com/flow.png" caption="完整流程图"
:::
```

## 最小输入

- media-text：图片 URL + 解释文字
- gallery：≥ 2 张图片
- long-image：图片 URL + 说明

## 选择条件

- media-text：图片后紧跟解释段落且语义绑定
- gallery：2-4 张相关图片
- long-image：明确的长截图/流程图/信息图

## 禁止自动识别条件

- **无图片不得生成任何媒体组件**
- 只 1 张图不生成 gallery
- 普通截图无长图语义不生成 long-image

## 降级方式

回退为通用库 2a 标准图片

## HTML 模板

见 `tests/advanced-components/expected/media-text-{theme}.html`、`gallery-{theme}.html`、`long-image-{theme}.html`（各 6 份）。


---

## 生产 HTML 模板（moyu-green 主题示例）

> 其他主题使用相同结构，仅替换 `theme-adapters.md` 中的色值令牌。

```html
<section style="margin:0 0 8px;background:#F0FDF4;border-radius:12px;padding:6px;border:1px solid #BBF7D0;box-shadow:0 4px 16px -4px rgba(0,0,0,0.08);">
  <section style="margin:0;border-radius:12px;overflow:hidden;"><span leaf=""><img src="../assets/media-demo.png" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span></section>
</section>
<p style="margin:0 0 8px;font-size:12px;color:#9CA3AF;text-align:center;"><span leaf="">架构示意图</span></p>
<p style="margin:0 0 24px;font-size:14px;color:#374151;line-height:1.8;"><span leaf="">该架构采用微服务拆分，每个服务独立部署。</span></p>
```

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/media-text-*.html`（验收产物，非生产依赖）。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。


### gallery 模板（moyu-green）

```html
<section style="margin:0 0 24px;"><p style="margin:0 0 14px;font-size:15px;font-weight:700;color:#111827;line-height:1.5;"><span leaf="">安装过程</span></p>
  <section style="margin:0 0 12px;">
    <section style="margin:0 0 6px;border-radius:12px;overflow:hidden;"><span leaf=""><img src="../assets/gallery-01.png" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span></section>
    <p style="margin:0 0 16px;font-size:12px;color:#9CA3AF;text-align:center;"><span leaf="">下载安装包</span></p>
  </section>
<section style="margin:0 0 12px;">
    <section style="margin:0 0 6px;border-radius:12px;overflow:hidden;"><span leaf=""><img src="../assets/gallery-02.png" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span></section>
    <p style="margin:0 0 16px;font-size:12px;color:#9CA3AF;text-align:center;"><span leaf="">配置环境变量</span></p>
  </section>
<section style="margin:0 0 12px;">
    <section style="margin:0 0 6px;border-radius:12px;overflow:hidden;"><span leaf=""><img src="../assets/gallery-03.png" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span></section>
    <p style="margin:0 0 16px;font-size:12px;color:#9CA3AF;text-align:center;"><span leaf="">运行服务</span></p>
  </section>
</section>
```


### long-image 模板（moyu-green）

```html
<section style="margin:0 0 8px;background:#F0FDF4;border-radius:12px;padding:6px;border:1px solid #BBF7D0;box-shadow:0 4px 16px -4px rgba(0,0,0,0.08);">
  <span leaf=""><img src="../assets/long-flow.png" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span>
</section>
<p style="margin:0 0 24px;font-size:12px;color:#9CA3AF;text-align:center;"><span leaf="">完整部署流程图</span></p>
```
