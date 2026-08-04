# 护栏从「自觉」到「硬拦」:vibe-coding-guide v2.1 的数字与代码

给 AI 编程立规矩,最难的不是写出规矩,而是让规矩真的生效。

## 一、三组数字

v1.2.0 把红线从 8 条扩到 11 条,自检清单从 19 条扩到 25 条;v2.1.0 把铁律从四条扩到五条。

## 二、十六行拦截文案

全部十六行拦截文案如下:

```bash
⛔ vibe-coding-guide 拦截：这是对根目录或家目录的递归删除，会清空整台机器（铁律 1）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：要安装新依赖了。装之前请先确认包名全称、用途、周下载量和最近更新时间（红线 10）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
```

## 三、安装与边界

启用这套规矩需要两行命令:

```text
/plugin marketplace add Amer-CN/vibe-coding-guide
/plugin install vibe-coding-guide@vibe-coding-guide
```

install.sh 不承诺护栏随 skills 目录安装生效。
