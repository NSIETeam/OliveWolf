# OliveWolf Studio 客户服务器部署说明

交付目标：客户拿到 `olivewolf-studio-*.tar.gz` 后，在服务器上执行两条命令即可打开网页使用。

---

## 1. 服务器要求

最低配置（Studio 控制台 + API）：

- Ubuntu 22.04 LTS
- 4 CPU / 8GB RAM
- 50GB 磁盘
- Docker Engine + Docker Compose v2

GPU训练/构建数字人资产建议：

- NVIDIA GPU，显存 16GB 以上
- NVIDIA Driver + nvidia-container-toolkit
- CUDA 12.x 运行环境
- 100GB+ 磁盘用于模型权重和输出文件

> 当前 Studio 已包含训练任务入口和 Worker 边界；GPU Worker 接入后即可执行真实模型训练/构建。

---

## 2. 解压

```bash
tar -xzf olivewolf-studio-*.tar.gz
cd olivewolf-studio
```

如果从 GitHub 克隆：

```bash
git clone https://github.com/NSIETeam/OliveWolf.git olivewolf-studio
cd olivewolf-studio
```

---

## 3. 安装

```bash
bash deploy/customer-package/scripts/install.sh
```

脚本会：

- 检查 Docker / Compose
- 生成 `.env`
- 自动生成 `STUDIO_API_KEY`
- 构建 Studio API 镜像

---

## 4. 启动

```bash
bash deploy/customer-package/scripts/start.sh
```

打开：

```text
http://服务器IP:8080/
```

API文档：

```text
http://服务器IP:8080/docs
```

启动脚本会输出 API Key。复制到网页顶部的 `API Key` 输入框。

---

## 5. 客户使用流程

1. 创建公司空间 Tenant。
2. 创建项目 Project。
3. 创建数字人 Avatar。
4. 上传数字人头像/形象图。
5. 点击 `Start Training Job`。
6. 添加知识库来源。
7. 测试对话。
8. 创建渲染任务。

---

## 6. 停止服务

```bash
bash deploy/customer-package/scripts/stop.sh
```

---

## 7. 打包交付

开发方执行：

```bash
bash deploy/customer-package/scripts/package.sh v0.1.0
```

会生成：

```text
dist/olivewolf-studio-v0.1.0.tar.gz
```

把这个压缩包发给客户即可。

---

## 8. 当前训练任务说明

`Training Job` 是客户可见的训练入口，当前会完成：

- 校验 Avatar 是否已上传形象图
- 创建训练任务记录
- 返回任务ID和状态

GPU Worker 接入后将继续执行：

- LivePortrait 实时头像预处理缓存
- LHM 全身3D重建缓存
- 声音/知识库资产绑定
- 输出可部署数字人资产

---

## 9. 生产注意事项

- 对外开放前必须设置强 `STUDIO_API_KEY`。
- 建议用 Nginx/HTTPS 反代。
- SQLite 仅适合试用；生产请切换 Postgres。
- 生成文件建议迁移到 S3/MinIO。
- GPU Worker 应独立部署，不要和 API 共用容器。
