# Docker 镜像体积优化：从 1.2GB 到 180MB 的实战记录

> 把一个臃肿的 Python 服务镜像瘦身 85%，每一步都是踩坑换来的。

## 背景

我们的 API 服务镜像一直停在 1.2GB。每次 CI 拉取镜像要 4 分钟，本地调试启动要 30 秒。团队忍了半年，直到某天磁盘空间告警，才下定决心优化。

最终结果：镜像从 1.2GB 降到 180MB，CI 拉取时间从 4 分钟降到 25 秒。

## 问题诊断

:::alert type="warning" title="多阶段构建不是银弹"
多阶段构建能减小体积，但如果基础镜像选错了（比如用 `python:3.12` 而非 `python:3.12-slim`），体积差异可以到 800MB。先选对基础镜像，再做多阶段。
:::

原始 Dockerfile 的问题集中在三处：

- 基础镜像 `python:3.12` 自带完整 Debian 工具链（约 900MB）
- `pip install` 把 `.whl` 和缓存都留在了镜像层里
- 没有 `.dockerignore`，`COPY .` 把 `.git` 和 `node_modules` 都打进去了

## 优化前后对照

:::code-compare title="Dockerfile 优化对照"
@before lang="dockerfile"
FROM python:3.12
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
@end
@after lang="dockerfile"
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim
COPY --from=builder /root/.local /root/.local
COPY . /app
WORKDIR /app
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "main.py"]
@end
:::

## 关键数据

| 指标 | 优化前 | 优化后 | 变化 |
|------|--------|--------|------|
| 镜像体积 | 1.2GB | 180MB | -85% |
| CI 拉取时间 | 4 min | 25 s | -90% |
| 本地启动 | 30 s | 6 s | -80% |
| 构建层数 | 4 | 7 | +75% |

:::alert type="important" title="为什么层数反而增加了？"
多阶段构建把依赖安装和代码复制分离到不同层。虽然层数增加，但每层更小，总体积下降。这是用层数换体积的正确权衡。
:::

## 延伸阅读

:::resources title="参考资料"
- [Docker 多阶段构建官方文档](https://docs.docker.com/build/building/multi-stage/)
- [Python Docker 最佳实践](https://docs.docker.com/language/python/build-images/)
:::

## 踩过的坑

最大的坑是 `COPY --from=builder /root/.local` 这行。如果 builder 阶段用 `pip install --user`，文件会装到 `/root/.local`。但如果基础镜像的 HOME 不是 `/root`，路径就对不上。排查了两个小时才发现在 `python:3.12-slim` 里 HOME 默认是 `/root`，但在某些 CI 环境里被覆盖了。

[^1]: 测试环境：Docker Engine v26.0.0，macOS 14.4，8 核 M2 Pro，32GB 内存
[^2]: 镜像体积使用 `docker images` 命令测量，不含 build cache
