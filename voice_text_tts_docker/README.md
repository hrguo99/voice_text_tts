# Voice Text TTS - Docker 部署指南

这是一个基于 Gradio 的语音文本 TTS 应用的 Docker 部署包。

## 功能特性

- 🎤 **语音生成**: 支持多种音色和模式的语音合成
- 🎤 **语音识别**: 集成 ASR 功能，支持语音转文字
- 🎨 **Web 界面**: 基于 Gradio 6.0+ 的现代化界面
- 🔧 **灵活配置**: 支持环境变量配置
- 🐳 **Docker 支持**: 一键部署，易于管理

## 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 2GB 可用内存
- 至少 5GB 可用磁盘空间

## 快速开始

### 1. 准备工作

确保你已经在同一目录下有 `voice_text_tts` 文件夹（包含应用源代码）。

目录结构应该是：
```
.
├── voice_text_tts/           # 应用源代码
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   └── ...
└── voice_text_tts_docker/    # Docker 部署包
    ├── Dockerfile
    ├── docker-compose.yml
    └── ...
```

### 2. 配置环境变量（可选）

复制示例配置文件：
```bash
cp .env.example .env
```

根据需要修改 `.env` 文件中的配置项。

### 3. 快速启动（推荐）

使用提供的快速启动脚本：
```bash
cd voice_text_tts_docker
./start.sh
```

### 4. 手动构建和启动

或者手动执行以下步骤：

使用 Docker Compose：
```bash
# 从父目录运行（包含 voice_text_tts 和 voice_text_tts_docker 的目录）
cd ..  # 如果当前在 voice_text_tts_docker 目录
docker-compose -f voice_text_tts_docker/docker-compose.yml up -d
```

或使用 Docker 命令构建镜像：
```bash
# 构建镜像（从 voice_text_tts_docker 目录运行）
cd voice_text_tts_docker
./build.sh

# 或手动构建
docker build -f voice_text_tts_docker/Dockerfile -t voice-text-tts:latest ..

# 运行容器
docker run -d \
  --name voice_text_tts_app \
  -p 7863:7863 \
  --env-file voice_text_tts_docker/.env \
  voice-text-tts:latest
```

### 5. 测试配置

在构建前，可以运行测试脚本验证配置：
```bash
cd voice_text_tts_docker
./test-config.sh
```

### 6. 访问应用

服务启动后，在浏览器中访问：
- 本地: http://localhost:7863
- 局域网: http://YOUR_IP:7863

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `SERVER_PORT` | 7863 | 应用监听端口 |
| `API_HOST` | 127.0.0.1 | TTS API 服务地址 |
| `API_PORT` | 50000 | TTS API 服务端口 |
| `API_MODE` | zero_shot | TTS 模式 |
| `PROMPT_TEXT` | You are a helpful assistant. | 提示文本 |
| `MAX_TEXT_LENGTH` | 1000 | 最大文本长度 |
| `ASR_ENABLED` | false | 是否启用 ASR 功能 |
| `ASR_BACKEND_TYPE` | funasr | ASR 后端类型 |
| `ASR_FUNASR_URI` | ws://localhost:10095/ws | ASR WebSocket 地址 |

### ASR 配置

如果要启用 ASR 功能，需要：

1. 设置 `ASR_ENABLED=true`
2. 配置 ASR WebSocket 服务地址（`ASR_FUNASR_URI`）
3. 根据 ASR 服务调整其他参数

## 常用命令

### 查看日志
```bash
# 从父目录运行
docker-compose -f voice_text_tts_docker/docker-compose.yml logs -f

# 或使用启动脚本
cd voice_text_tts_docker
./start.sh  # 选择不重新构建
```

### 停止服务
```bash
# 使用停止脚本
cd voice_text_tts_docker
./stop.sh

# 或手动停止
docker-compose -f voice_text_tts_docker/docker-compose.yml down
```

### 重启服务
```bash
docker-compose -f voice_text_tts_docker/docker-compose.yml restart
```

### 更新应用
```bash
# 拉取最新代码
cd voice_text_tts
git pull

# 重新构建并启动
cd voice_text_tts_docker
./start.sh  # 选择重新构建
```

### 进入容器
```bash
docker exec -it voice_text_tts_app bash
```

## 故障排查

### 容器无法启动

1. 检查端口是否被占用：
```bash
sudo lsof -i :7863
```

2. 查看容器日志：
```bash
docker logs voice_text_tts_app
```

### 无法访问 Web 界面

1. 检查容器是否在运行：
```bash
docker ps | grep voice_text_tts_app
```

2. 检查健康状态：
```bash
docker inspect --format='{{.State.Health.Status}}' voice_text_tts_app
```

3. 确认防火墙设置：
```bash
sudo ufw allow 7863
```

### API 连接失败

如果应用无法连接到 TTS API 服务：

1. 使用 `host.docker.internal` 访问宿主机服务（Docker Desktop）
2. 使用宿主机实际 IP 地址（Linux Docker）
3. 确认 API 服务正在运行且可访问

## 依赖说明

本项目依赖以下核心库（版本见 [requirements.txt](../voice_text_tts/requirements.txt)）：

- **gradio** (>=6.0.0): Web 界面框架
- **huggingface_hub** (>=0.23.0): Hugging Face 集成
- **numpy** (>=1.24.0): 数值计算
- **ffmpeg-python**, **pydub**, **ffmpy**: 音频处理
- **requests** (>=2.31.0): HTTP 请求
- **websockets** (>=12.0): WebSocket 支持

## 系统要求

容器内已安装以下系统依赖：

- **ffmpeg**: 音频/视频处理
- **gcc/g++**: 编译工具

## 许可证

请参考主项目的许可证文件。

## 支持

如有问题，请查看主项目文档或提交 Issue。
