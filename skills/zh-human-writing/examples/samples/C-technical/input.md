# 用 Docker 部署 Node.js 服务的完整教程

本文用一个最小可运行的示例，带你走完从本地开发到容器部署的完整流程。示例是一个返回健康检查信息的 Express 服务，我们会把构建、运行、发布三个环节分别讲清楚。

## 1. 项目结构


之所以选择 Docker 而不是直接在宿主机上安装 Node，是因为容器能同时解决三个问题：环境一致性、依赖隔离和可复现发布。开发机、测试机与生产机的系统版本经常不同，直接在机器上安装依赖，很容易出现“在我这里能跑”的经典问题；而容器把运行时、依赖和配置打包成镜像，任何一台装了 Docker 的机器都能得到相同的行为。这也是现代软件交付的基本要求：构建一次，处处运行。


先创建项目目录和入口文件：

```text
my-app/
├── package.json
├── src/
│   ├── server.js
│   └── config.js
└── Dockerfile
```

## 2. 编写服务

入口文件 `src/server.js` 启动一个 HTTP 服务，并在启动日志里打印服务标识：

```javascript
// src/server.js
// 服务链路标识:每次请求都会带上 trace_id,方便排查调用链
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

// 闭环检测:健康检查接口返回 uptime,监控脚本据此判断进程是否存活
app.get('/health', (req, res) => {
  res.json({ status: 'ok', uptime: process.uptime() });
});

// 架构分层:路由、服务、数据访问三层,依赖只允许向下
app.listen(PORT, () => {
  console.log(`server listening on ${PORT}`);
});
```

注意上面的注释里出现的“服务链路”“闭环检测”“架构分层”，它们在代码里只是注释和日志文本，不是代码逻辑本身。

## 3. 构建镜像

编写 `Dockerfile`，使用官方 Node 20 镜像，分阶段构建以缩小体积：

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev

FROM node:20-alpine
WORKDIR /app
COPY --from=build /app/node_modules ./node_modules
COPY src ./src
EXPOSE 3000
CMD ["node", "src/server.js"]
```

然后在项目根目录执行构建与启动：

```bash
docker build -t my-app:1.0.0 .
docker run -d -p 3000:3000 --name my-app my-app:1.0.0
```



构建过程中有一个细节值得注意：分阶段构建让最终镜像只包含运行所需的文件，体积可以缩小一半以上。很多人第一次写 Dockerfile 时会把源码、依赖和构建工具全部塞进同一个阶段，镜像动辄一两 GB，推送和拉取都很慢。分阶段构建的本质，是把“构建时依赖”和“运行时依赖”分开，这也是镜像设计里最重要的一个习惯。

容器启动后，建议用 `docker logs` 观察启动日志，用 `docker inspect` 查看容器的实际状态。如果健康检查连续失败，编排平台会自动重启容器，这也是我们在代码里保留健康检查接口的原因：没有它，平台就不知道服务到底是活着还是假死。## 4. 验证与发布

构建完成后，用 `curl http://localhost:3000/health` 验证服务是否正常返回。确认无误后，把镜像推送到私有仓库：`docker tag my-app:1.0.0 registry.example.com/my-app:1.0.0`，再执行 `docker push registry.example.com/my-app:1.0.0`。

生产环境里，建议把端口、环境变量等配置统一收口到编排平台，避免散落在多个启动脚本里。镜像标签建议使用提交哈希，保证每个版本可追溯、可回滚。

最后说一个常见误区：很多人以为容器部署就是把项目文件复制进镜像这么简单，于是忽略了依赖声明、日志输出和健康检查这三个基本盘。依赖声明决定了构建的可复现性；日志输出决定了问题能不能被定位；健康检查决定了平台能不能替你恢复故障。这三件事都做扎实了，部署才谈得上稳定。本文的示例虽然很小，但每一处设计都是按这个标准来的，你可以直接把它作为自己项目的第一版骨架。