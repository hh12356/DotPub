# 阶段1：基于node:24-slim镜像，命名为build，用来编译前端代码
FROM node:24-slim AS build
#设置工作目录为 `/app`
WORKDIR /app

#把宿主机当前目录下 `package.json`、`package-lock.json` 复制到容器内 `/app/`
COPY package.json package-lock.json ./
#定义构建参数（仅 build 镜像阶段生效），设置 npm 源为官方源，可以传参覆盖
ARG NPM_CONFIG_REGISTRY=https://registry.npmjs.org
#**根据 lock 文件精确安装依赖**，不会改动 package-lock
RUN npm ci

#把宿主机当前目录剩下所有源码，复制到容器内 `/app`
COPY . .
#执行前端打包命令，生成 dist 静态产物（html/js/css 图片），输出到 `/app/dist`
RUN npm run build


# 阶段2：最终运行镜像，基于nginx:stable-alpine轻量nginx镜像
FROM nginx:stable-alpine
#把上一阶段打包产物 `/app/dist` 复制到当前 nginx 容器的网页根目录 `/usr/share/nginx/html`
COPY --from=build /app/dist /usr/share/nginx/html
#将宿主机的 nginx 配置文件，覆盖容器内 nginx 默认站点配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

#容器启动主命令：`nginx -g "daemon off; 
#"`daemon off 让 nginx 前台运行，维持容器进程
ENTRYPOINT ["nginx", "-g", "daemon off;"]
CMD []
#声明容器打算使用 80 端口，仅文档提示，不会真正打开端口
EXPOSE 80
