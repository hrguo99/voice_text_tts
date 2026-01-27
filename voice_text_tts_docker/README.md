# Voice Text TTS Docker

基于 Gradio 的语音生成功能 Docker 部署方案，支持一键启动和环境变量配置。

## 功能特性

- 🎙️ **语音合成**：基于 Fun-CosyVoice3-0.5B-2512 API 的语音生成
- 🎤 **多种音频输入**：支持上传音频文件或麦克风录制
- 📝 **ASR 语音识别**：可选的自动语音转文本功能（支持 FunASR）
- 🐳 **Docker 部署**：容器化部署，一键启动
- ⚙️ **灵活配置**：通过环境变量配置所有参数

## 快速开始

### 前置要求

- Docker (>= 20.10)

### 方式一：分步启动（推荐）

```bash
# 进入项目目录
cd voice_text_tts_docker

# 步骤1: 构建镜像
./build.sh

# 步骤2: 启动服务
./run.sh
```

启动成功后，访问 `http://localhost:7862` 即可使用。

### 方式二：一键启动

```bash
# 自动构建并启动
./start.sh
```

### 方式三：使用 Docker Compose

```bash
# 复制配置文件
cp .env.example .env

# 构建并启动
docker compose up -d
```

## 管理命令

### 构建脚本 (build.sh)

```bash
./build.sh              # 构建镜像
./build.sh --no-cache   # 不使用缓存构建
./build.sh --help       # 显示帮助
```

### 运行脚本 (run.sh)

```bash
./run.sh start    # 启动服务（默认）
./run.sh stop     # 停止服务
./run.sh restart  # 重启服务
./run.sh status   # 查看服务状态
./run.sh logs     # 查看服务日志
./run.sh shell    # 进入容器Shell
./run.sh rm       # 删除容器
./run.sh help     # 显示帮助
```

### 一键脚本 (start.sh)

```bash
./start.sh start    # 构建并启动服务
./start.sh stop     # 停止服务
./start.sh restart  # 重启服务
./start.sh logs     # 查看服务日志
./start.sh build    # 仅构建镜像
./start.sh cleanup  # 清理容器和镜像
./start.sh help     # 显示帮助信息
```

## 配置说明

复制 `.env.example` 为 `.env` 并根据需要修改配置：

```bash
cp .env.example .env
```

### 核心配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `API_HOST` | TTS API 服务器地址 | `127.0.0.1` |
| `API_PORT` | TTS API 服务器端口 | `50000` |
| `API_MODE` | TTS API 模式 | `zero_shot` |
| `PROMPT_TEXT` | 系统提示文本 | `You are a helpful assistant.<|endofprompt|>` |
| `SERVER_PORT` | Gradio 服务端口 | `7862` |
| `MAX_TEXT_LENGTH` | 最大文本长度 | `1000` |
| `ASR_ENABLED` | 是否启用 ASR 功能 | `false` |
| `ASR_BACKEND_TYPE` | ASR 后端类型 | `funasr` |

### ASR 配置项（可选）

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `ASR_FUNASR_URI` | FunASR WebSocket 地址 | `ws://localhost:10095/ws` |
| `ASR_FUNASR_MODE` | FunASR 模式 | `2pass-offline` |
| `ASR_FUNASR_CHUNK_SIZE` | 分块大小 | `[5, 10, 5]` |
| `ASR_FUNASR_CHUNK_INTERVAL` | 分块间隔（毫秒） | `10` |
| `ASR_FUNASR_USE_ITN` | 是否使用 ITN | `true` |

## Docker 命令

### 使用 Docker Compose

```bash
# 构建并启动
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down

# 重启服务
docker compose restart
```

### 使用 Docker 原生命令

```bash
# 构建镜像
docker build -t voice-text-tts .

# 运行容器
docker run -d \
  --name voice_text_tts_app \
  -p 7862:7862 \
  --env-file .env \
  --restart unless-stopped \
  voice-text-tts

# 查看日志
docker logs -f voice_text_tts_app

# 停止容器
docker stop voice_text_tts_app
docker rm voice_text_tts_app
```

## 项目结构

```
voice_text_tts_docker/
├── Dockerfile              # Docker 镜像构建文件
├── docker-compose.yml      # Docker Compose 配置
├── .dockerignore           # Docker 构建忽略文件
├── .env.example            # 环境变量示例文件
├── build.sh                # 镜像构建脚本
├── run.sh                  # 服务运行脚本
├── start.sh                # 一键启动脚本
├── README.md               # 使用说明
└── voice_text_tts/         # 应用源代码
    ├── app.py              # Gradio 应用主程序
    ├── config.py           # 配置文件（支持环境变量）
    ├── asr_client.py       # ASR 客户端
    ├── asr_backends.py     # ASR 后端接口
    └── requirements.txt    # Python 依赖
```

## 使用说明

1. **准备参考音频**：上传音频文件或使用麦克风录制
2. **输入参考音频文本**：手动输入或使用 ASR 自动识别
3. **输入要合成的文本**：在文本框中输入目标文字
4. **生成语音**：点击"生成语音"按钮开始合成

## 注意事项

1. **TTS API 依赖**：需要确保 TTS API 服务（Fun-CosyVoice3-0.5B-2512）已启动并可访问
2. **ASR 功能**：如需使用 ASR 功能，需要设置 `ASR_ENABLED=true` 并确保 ASR 服务可访问
3. **端口映射**：默认使用 7862 端口，如有冲突请修改 `.env` 中的 `SERVER_PORT`
4. **网络配置**：如果 TTS/ASR 服务在其他容器中，建议使用 Docker 网络进行通信

## 故障排查

### 服务无法启动

```bash
# 查看容器日志
./run.sh logs
# 或
docker logs -f voice_text_tts_app
```

### 无法连接 TTS API

1. 检查 TTS API 服务是否运行
2. 确认 `.env` 中的 `API_HOST` 和 `API_PORT` 配置正确
3. 如果 API 在 Docker 容器中，使用容器名称而非 `127.0.0.1`

### ASR 功能不可用

1. 确认 `.env` 中 `ASR_ENABLED=true`
2. 检查 ASR 服务 WebSocket 地址是否正确
3. 查看 ASR 服务日志

## 许可证

本项目遵循原 voice_text_tts 项目的许可证。

## 联系方式

如有问题或建议，请联系项目维护者。
