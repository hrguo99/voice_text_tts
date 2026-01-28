# Voice Text TTS Docker 快速开始指南

## 一键部署（推荐）

### 步骤 1：构建 Docker 镜像

```bash
cd voice_text_tts_docker
./build.sh
```

### 步骤 2：启动服务

```bash
./start.sh
```

### 步骤 3：访问服务

打开浏览器访问：**http://localhost:7863**

---

## 常用命令速查

| 操作 | 命令 |
|------|------|
| 构建镜像 | `./build.sh` |
| 启动服务 | `./start.sh` |
| 停止服务 | `./stop.sh` |
| 查看日志 | `./logs.sh` |
| 清理环境 | `./clean.sh` |

---

## 使用 Docker Compose

### 启动

```bash
docker-compose up -d
```

### 查看日志

```bash
docker-compose logs -f
```

### 停止

```bash
docker-compose down
```

---

## 自定义配置

### 修改端口

编辑 `.env` 文件（从 `.env.example` 复制）：

```bash
cp .env.example .env
# 编辑 .env 文件修改配置
```

或在启动时指定：

```bash
SERVER_PORT=8080 ./start.sh
```

### 启用 ASR

编辑 `.env` 文件：

```bash
ASR_ENABLED=true
ASR_BACKEND_TYPE=funasr
```

---

## 问题排查

### 端口被占用

修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "8080:7863"  # 使用 8080 端口
```

### 查看容器状态

```bash
docker ps
```

### 查看详细日志

```bash
./logs.sh
```

---

## 数据持久化

- 音色预设：`voice_text_tts_docker/presets/`
- 临时文件：`voice_text_tts_docker/temp/`

---

## 更新应用

```bash
# 1. 停止服务
./stop.sh

# 2. 重新构建
./build.sh

# 3. 启动服务
./start.sh
```

---

更多详细信息请参阅 [README.md](README.md)
