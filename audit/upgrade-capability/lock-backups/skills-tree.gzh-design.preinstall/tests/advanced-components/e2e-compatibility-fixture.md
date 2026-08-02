# 端到端兼容性 Fixture

> 此文件模拟完整链路：super-writer 产出 → zh-human-writing 处理 → gzh-design 渲染
> 用于验证新增高级组件语法不破坏现有交接合同

---

# AI 排版工具横评：2026 年 7 月数据

> 3 款工具同台测试，结果与半年前完全不同。

## 测试背景

[[protected]]本次测试在 2026 年 7 月 15 日完成，使用 Node.js v18.19.0 环境。[[/protected]]所有测试数据来自公开仓库 https://github.com/example/benchmark 的 release v3.14.2。

[编辑锚点：请补充你实际使用工具时的真实感受，不要让 AI 代写]

## 关键数据

系统响应时间为 100ms，在 2024 年 1 月 15 日的测试中，延迟降低了 30%。处理了 1,000,000 次请求，内存占用稳定在 32GB。

## 核心发现

使用命令 `npm install` 安装依赖后，配置文件位于 `/etc/app/config.yaml`。启动命令：

```bash
docker run -d -p 8080:8080 app:v3.14.2
```

<!--keep-->服务器配置：8 核 CPU、32GB 内存、500GB SSD。<!--/keep-->

:::alert type="warning" title="版本兼容性风险"
v3.14.2 在 PostgreSQL 16.2 上存在已知的连接池泄漏问题，连接数上限 200 可能不够用。详见官方 issue。
:::

## 改进对比

:::code-compare title="连接池修复"
@before lang="python"
pool = psycopg2.connect(maxconn=200)
pool.query("SELECT 1")
@end
@after lang="python"
pool = psycopg2.connect(maxconn=200, retry_on_timeout=True)
pool.query("SELECT 1", timeout=30)
@end
:::

## 参考资料

:::resources title="延伸阅读"
- [PostgreSQL 连接池文档](https://www.postgresql.org/docs/current/connection-pooling.html)
- [Docker 部署最佳实践](https://docs.docker.com/config/best-practices/)
:::

---

[^1]: 数据来源：example/benchmark 仓库 v3.14.2 release notes，https://github.com/example/benchmark/releases/tag/v3.14.2
