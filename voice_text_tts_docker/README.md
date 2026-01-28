# Voice Text TTS Docker 部署文档

基于 Python 3.13 的 Voice Text TTS 项目 Docker 化部署方案。

## 目录结构

```
voice_text_tts_docker/
├── Dockerfile              # Docker 镜像定义文件（多阶段构建）
├── docker-compose.yml      # Docker Compose 配置文件
├── .dockerignore          # Docker 构建忽略文件
├── build.sh               # 一键构建脚本
├── start.sh               # 一键启动脚本
├── README.md              # 本文档
├── presets/               # 音色预设目录（持久化）
└── temp/                  # 临时文件目录（持久化）
```

## 功能特性

- ✅ 基于 Python 3.13 slim 镜像
- ✅ 多阶段构建，优化镜像大小
- ✅ 集成 FFmpeg 音频处理
- ✅ 支持音色预设持久化存储
- ✅ 健康检查机制
- ✅ 一键构建和启动
- ✅ 支持环境变量配置
- ✅ 自动重启策略

## 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 1.29+ (可选)
- 至少 2GB 可用磁盘空间

### 方法一：使用一键脚本（推荐）

#### 1. 构建 Docker 镜像

```bash
cd voice_text_tts_docker
./build.sh
```

构建脚本会自动：
- 检查必需的项目文件
- 准备构建环境
- 构建 Docker 镜像
- 显示镜像信息
- 清理临时文件

#### 2. 启动容器

```bash
./start.sh
```

启动脚本会自动：
- 检查镜像是否存在
- 创建数据目录
- 清理旧容器
- 启动新容器
- 显示服务信息

#### 3. 访问服务

打开浏览器访问：`http://localhost:7863`

### 方法二：使用 Docker Compose

#### 1. 构建并启动

```bash
cd voice_text_tts_docker
docker-compose up -d --build
```

#### 2. 查看日志

```bash
docker-compose logs -f
```

#### 3. 停止服务

```bash
docker-compose down
```

### 方法三：手动 Docker 命令

#### 1. 构建镜像

```bash
cd voice_text_tts_docker
docker build -t voice-text-tts:latest -f Dockerfile ../voice_text_tts
```

#### 2. 运行容器

```bash
docker run -d \
    --name voice-text-tts \
    -p 7863:7863 \
    -v $(pwd)/presets:/app/presets \
    -v $(pwd)/temp:/app/temp \
    voice-text-tts:latest
```

## 配置说明

### 环境变量

可以通过环境变量自定义配置：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `API_HOST` | 127.0.0.1 | TTS API 服务地址 |
| `API_PORT` | 50000 | TTS API 服务端口 |
| `API_MODE` | zero_shot | TTS 工作模式 |
| `SERVER_NAME` | 0.0.0.0 | Web 服务监听地址 |
| `SERVER_PORT` | 7863 | Web 服务端口 |
| `ASR_ENABLED` | false | 是否启用 ASR 功能 |
| `ASR_BACKEND_TYPE` | funasr | ASR 后端类型 |
| `MAX_TEXT_LENGTH` | 1000 | 最大文本长度限制 |

### 修改配置

#### 方法一：修改 docker-compose.yml

编辑 `docker-compose.yml` 文件中的 `environment` 部分：

```yaml
environment:
  - API_HOST=127.0.0.1
  - API_PORT=50000
  - SERVER_PORT=7863
  # 添加或修改其他配置
```

#### 方法二：使用 .env 文件

创建 `.env` 文件：

```bash
API_HOST=127.0.0.1
API_PORT=50000
SERVER_PORT=7863
ASR_ENABLED=true
```

#### 方法三：启动时指定

```bash
docker run -d \
    -e API_HOST=192.168.1.100 \
    -e API_PORT=50000 \
    -e ASR_ENABLED=true \
    -p 7863:7863 \
    voice-text-tts:latest
```

### 端口映射

默认端口映射：`7863:7863`

修改主机端口：

```bash
# 使用 8080 端口访问
docker run -p 8080:7863 voice-text-tts:latest
```

在 `docker-compose.yml` 中修改：

```yaml
ports:
  - "8080:7863"
```

### 数据持久化

容器使用两个数据卷：

- `./presets:/app/presets` - 音色预设存储
- `./temp:/app/temp` - 临时文件存储

数据会自动持久化到宿主机的 `voice_text_tts_docker/presets` 和 `voice_text_tts_docker/temp` 目录。

## 常用命令

### 查看容器状态

```bash
docker ps
```

### 查看实时日志

```bash
docker logs -f voice-text-tts
```

### 停止容器

```bash
docker stop voice-text-tts
```

### 启动已停止的容器

```bash
docker start voice-text-tts
```

### 重启容器

```bash
docker restart voice-text-tts
```

### 删除容器

```bash
docker rm -f voice-text-tts
```

### 删除镜像

```bash
docker rmi voice-text-tts:latest
```

### 进入容器

```bash
docker exec -it voice-text-tts bash
```

### 查看容器资源使用

```bash
docker stats voice-text-tts
```

## 优化说明

### 镜像大小优化

本 Dockerfile 采用多种优化策略：

1. **多阶段构建**：将构建环境和运行环境分离
2. **Slim 基础镜像**：使用 `python:3.13-slim` 而非完整版
3. **虚拟环境**：隔离 Python 依赖
4. **清理缓存**：删除 apt 和 pip 缓存
5. **.dockerignore**：排除不必要的文件

预期镜像大小：~500MB - 800MB（取决于依赖）

### 性能优化建议

1. **资源限制**：

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

2. **网络优化**：使用 `host` 网络模式（仅 Linux）

```bash
docker run --network host voice-text-tts:latest
```

3. **日志管理**：限制日志大小

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 故障排查

### 问题 1：容器无法启动

**检查日志**：
```bash
docker logs voice-text-tts
```

**常见原因**：
- 端口被占用：更换端口映射
- 权限问题：检查数据目录权限
- 配置错误：检查环境变量

### 问题 2：无法访问 Web 界面

**检查容器状态**：
```bash
docker ps | grep voice-text-tts
```

**检查端口映射**：
```bash
docker port voice-text-tts
```

**检查防火墙**：
```bash
sudo ufw allow 7863
```

### 问题 3：音频处理失败

**验证 FFmpeg**：
```bash
docker exec voice-text-tts ffmpeg -version
```

**检查音频文件**：
- 确保格式支持（WAV/MP3/M4A）
- 检查文件大小和时长

### 问题 4：镜像构建失败

**清理 Docker 缓存**：
```bash
docker builder prune
```

**重新构建（不使用缓存）**：
```bash
docker build --no-cache -t voice-text-tts:latest .
```

### 问题 5：ASR 功能不可用

**启用 ASR**：
```bash
docker run -e ASR_ENABLED=true -e ASR_BACKEND_TYPE=funasr ...
```

**检查 ASR 服务连接**：
- 确保 ASR WebSocket 服务可访问
- 检查网络配置

## 安全建议

1. **不要在生产环境暴露到公网**：使用反向代理（Nginx/Caddy）
2. **定期更新镜像**：重新构建以获取安全补丁
3. **限制容器权限**：避免使用 `--privileged`
4. **配置防火墙**：只开放必要端口
5. **监控日志**：定期检查异常访问

## 生产部署建议

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name tts.example.com;

    location / {
        proxy_pass http://localhost:7863;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 启用 HTTPS

使用 Let's Encrypt：

```bash
sudo certbot --nginx -d tts.example.com
```

### 配置自动重启

```yaml
restart: unless-stopped
```

### 监控和日志

集成 Prometheus + Grafana 监控：

```yaml
services:
  voice-text-tts:
    # ... 其他配置
    labels:
      - "prometheus.scrape=true"
      - "prometheus.port=7863"
```

## 更新升级

### 更新应用

1. 拉取最新代码
2. 重新构建镜像：

```bash
./build.sh
```

3. 重启容器：

```bash
./start.sh
```

### 备份数据

```bash
# 备份预设
tar -czf presets_backup_$(date +%Y%m%d).tar.gz voice_text_tts_docker/presets

# 备份临时文件（可选）
tar -czf temp_backup_$(date +%Y%m%d).tar.gz voice_text_tts_docker/temp
```

### 恢复数据

```bash
# 恢复预设
tar -xzf presets_backup_20260128.tar.gz
```

## 开发调试

### 挂载源代码

用于开发时实时修改代码：

```bash
docker run -d \
    -v $(pwd)/../voice_text_tts:/app \
    -p 7863:7863 \
    voice-text-tts:latest
```

### 交互式调试

```bash
docker run -it --rm \
    -v $(pwd)/../voice_text_tts:/app \
    voice-text-tts:latest \
    bash
```

## 技术栈

- **基础镜像**：Python 3.13 Slim
- **Web 框架**：Gradio 6.2.0
- **音频处理**：FFmpeg + pydub
- **通信协议**：HTTP + WebSocket
- **容器化**：Docker + Docker Compose

## 贡献和反馈

如有问题或建议，请提交 Issue 或 Pull Request。

## 许可证

与主项目保持一致。

## 相关链接

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Gradio 官方文档](https://www.gradio.app/docs/)

---

**最后更新**：2026-01-28
