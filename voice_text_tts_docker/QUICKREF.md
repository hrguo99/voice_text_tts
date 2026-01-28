# Voice Text TTS - Docker 快速参考

## 文件结构

```
voice_text_tts_docker/
├── Dockerfile              # Docker 镜像构建文件
├── docker-compose.yml      # Docker Compose 配置
├── .dockerignore          # Docker 构建忽略文件
├── .env.example           # 环境变量示例
├── .gitignore             # Git 忽略文件
├── README.md              # 详细部署文档
├── QUICKREF.md            # 本文件（快速参考）
├── start.sh               # 快速启动脚本
├── build.sh               # 构建镜像脚本
└── stop.sh                # 停止和清理脚本
```

## 快速命令

### 一键启动
```bash
./start.sh
```

### 仅构建镜像
```bash
./build.sh
```

### 停止服务
```bash
./stop.sh
```

### 查看日志
```bash
docker-compose logs -f
```

### 重启服务
```bash
docker-compose restart
```

### 进入容器
```bash
docker exec -it voice_text_tts_app bash
```

## Docker Compose 命令

```bash
# 构建并启动
docker-compose up -d

# 仅重新构建
docker-compose build

# 重新构建并启动
docker-compose up -d --build

# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f voice-text-tts

# 停止服务
docker-compose down

# 停止并删除卷
docker-compose down -v
```

## Docker 原生命令

```bash
# 构建镜像
docker build -t voice-text-tts:latest .

# 运行容器
docker run -d \
  --name voice_text_tts_app \
  -p 7863:7863 \
  --env-file .env \
  voice-text-tts:latest

# 查看日志
docker logs -f voice_text_tts_app

# 停止容器
docker stop voice_text_tts_app

# 删除容器
docker rm voice_text_tts_app

# 删除镜像
docker rmi voice-text-tts:latest
```

## 环境变量

主要配置项（在 .env 文件中设置）：

- `SERVER_PORT=7863` - Web 服务端口
- `API_HOST=127.0.0.1` - TTS API 地址
- `API_PORT=50000` - TTS API 端口
- `ASR_ENABLED=false` - 是否启用 ASR

完整配置见 [README.md](README.md)

## 端口映射

- `7863` - Gradio Web 界面

## 访问地址

启动后访问：
- 本地: http://localhost:7863
- 局域网: http://YOUR_IP:7863

## 故障排查

### 容器启动失败
```bash
# 查看日志
docker logs voice_text_tts_app

# 检查镜像
docker images | grep voice-text-tts
```

### 端口冲突
```bash
# 检查端口占用
sudo lsof -i :7863
```

### 重新构建
```bash
# 清理并重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 更新应用

```bash
# 1. 更新源代码
cd ../voice_text_tts
git pull

# 2. 重新构建
cd ../voice_text_tts_docker
docker-compose up -d --build
```

## 系统资源

- 内存: 建议 2GB+
- 磁盘: 建议 5GB+
- CPU: 建议 2 核心以上

## 依赖版本

基于 [voice_text_tts/requirements.txt](../voice_text_tts/requirements.txt)：
- Python: 3.12+
- Gradio: >=6.0.0
- 其他依赖见 requirements.txt
