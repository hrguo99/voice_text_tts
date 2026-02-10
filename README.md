# 语音合成与识别项目 (Voice Synthesis & Recognition Project)

基于 Gradio 的语音合成（TTS）和语音识别（ASR）综合应用，支持 Docker 容器化部署。

## 项目概述

本项目是一个功能完整的语音处理系统，集成了：
- **TTS（文字转语音）**：基于 Fun-CosyVoice3-0.5B-2512 模型的高质量语音合成
- **ASR（语音转文字）**：支持 FunASR 等多种后端的语音识别
- **音色预设管理**：保存和管理用户自定义音色
- **Docker 部署**：支持一键容器化部署

## 项目结构

```
guohaoran/
├── voice_text_tts/              # 核心应用（TTS + ASR）
│   ├── app.py                   # Gradio 应用主程序
│   ├── asr_client.py            # ASR WebSocket 客户端
│   ├── asr_backends.py          # ASR 后端抽象层
│   ├── config.py                # 配置文件
│   ├── requirements.txt         # Python 依赖
│   └── README.md                # 应用文档
│
├── voice_text_tts_docker/       # Docker 部署配置
│   ├── Dockerfile               # Docker 镜像定义
│   ├── docker-compose.yml       # Docker Compose 配置
│   ├── build.sh                 # 一键构建脚本
│   ├── start.sh                 # 一键启动脚本
│   ├── stop.sh                  # 一键停止脚本
│   ├── export.sh                # 导出镜像脚本
│   ├── import-and-start.sh      # 导入并启动脚本
│   ├── clean.sh                 # 清理脚本
│   ├── logs.sh                  # 查看日志脚本
│   ├── presets/                 # 音色预设存储（持久化）
│   ├── temp/                    # 临时文件（持久化）
│   └── README.md                # Docker 部署文档
│
├── asr_server_mock/             # 模拟 ASR 服务器
│   ├── asr_server.py            # WebSocket 服务器
│   ├── test_client.py           # 测试客户端
│   ├── start_server.sh          # 启动脚本
│   └── README.md                # 服务器文档
│
├── cv_gradio/                   # CV 相关应用
│   └── README.md                # CV 应用文档
│
├── FUNASR_model/                # FunASR 模型存储
├── tts_model/                   # TTS 模型服务和代码
│   ├── server.py                # FastAPI TTS 服务器
│   ├── client.py                # 测试客户端
│   ├── update_docker.sh         # Docker 代码更新脚本
│   ├── logs.sh                  # 日志查看脚本
│   └── README.md                # TTS 模型文档
├── ASR_PROJECT_GUIDE.md         # ASR 项目详细指南
├── FUNASR_REFERENCE.md          # FunASR 参考文档
└── README.md                    # 本文档
```

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户界面层                               │
│                    Gradio Web UI (Port 7862/7863)               │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
┌───────────────────────────┐    ┌───────────────────────────┐
│      TTS 服务层           │    │      ASR 服务层           │
│  Fun-CosyVoice3-0.5B      │    │   FunASR / WebSocket      │
│  (Port 50000)             │    │   (Port 10095)            │
└───────────────────────────┘    └───────────────────────────┘
                │                             │
                └──────────────┬──────────────┘
                               │
                    ┌──────────┴──────────┐
                    │    核心应用层       │
                    │  voice_text_tts     │
                    │  - asr_client.py    │
                    │  - asr_backends.py  │
                    │  - app.py           │
                    └─────────────────────┘
```

### 核心组件

#### 1. TTS 模块（语音合成）
- **模型**：Fun-CosyVoice3-0.5B-2512
- **功能**：文字转语音、零样本语音克隆
- **API 端口**：50000
- **模式**：zero_shot

#### 2. ASR 模块（语音识别）
- **后端支持**：
  - FunASR（推荐）
  - 通用 WebSocket
  - 自定义后端
- **功能**：自动识别参考音频文本
- **协议**：WebSocket

#### 3. 音色预设系统
- **存储**：持久化到本地文件
- **格式**：JSON + 音频文件
- **功能**：保存、加载、删除、预览

#### 4. Docker 部署系统
- **基础镜像**：Python 3.13 Slim
- **容器端口**：7863
- **数据卷**：presets、temp

## 快速开始

### 本地部署

#### 前置要求
- Python 3.13
- FFmpeg
- 足够的磁盘空间（模型文件约 2GB+）

#### 1. 安装依赖

```bash
# 安装 FFmpeg
sudo apt-get install ffmpeg

# 进入应用目录
cd voice_text_tts

# 安装 Python 依赖
pip install -r requirements.txt
```

#### 2. 配置应用

编辑 `voice_text_tts/config.py`：

```python
# TTS API 配置
API_HOST = "127.0.0.1"
API_PORT = "50000"
API_MODE = "zero_shot"

# ASR 配置
ASR_ENABLED = True
ASR_BACKEND_TYPE = "funasr"
ASR_BACKEND_CONFIG = {
    "funasr": {
        "uri": "ws://localhost:10095/ws",
        "mode": "2pass-offline",
    }
}
```

#### 3. 启动服务

```bash
cd voice_text_tts
python app.py
```

访问：http://127.0.0.1:7862

### Docker 部署（推荐）

#### 前置要求
- Docker 20.10+
- Docker Compose 1.29+

#### 一键部署

```bash
# 进入 Docker 目录
cd voice_text_tts_docker

# 构建镜像
./build.sh

# 启动容器
./start.sh
```

访问：http://localhost:7863

#### Docker Compose 部署

```bash
cd voice_text_tts_docker
docker-compose up -d --build
```

### TTS 模型服务部署

TTS 模型服务使用 **Fun-CosyVoice3-0.5B-2512**，需要单独部署。

#### 拉取官方镜像

```bash
# 从 ModelScope 拉取 CosyVoice3 镜像
docker pull registry.cn-beijing.aliyuncs.com/modelscope-repos/cosyvoice3:v1.0.0
```

#### 启动 TTS 服务

```bash
docker run -d \
  --name cosyvoice3-tts \
  --restart unless-stopped \
  -p 50000:50000 \
  -v ~/.cache/modelscope:/root/.cache/modelscope \
  registry.cn-beijing.aliyuncs.com/modelscope-repos/cosyvoice3:v1.0.0
```

#### 更新代码（使用增强版 server.py）

本项目对原版 `server.py` 进行了优化，支持：
- 流式响应进度信息
- 首块生成时间优化
- 细粒度子块分割

使用更新脚本：

```bash
cd tts_model
./update_docker.sh
```

或手动更新：

```bash
# 复制更新后的代码到容器
docker cp tts_model/server.py cosyvoice3-tts:/app/server.py

# 重启容器使更改生效
docker restart cosyvoice3-tts
```

#### 查看 TTS 服务日志

```bash
# 使用脚本
cd tts_model
./logs.sh

# 或直接查看
docker logs -f cosyvoice3-tts
```

#### TTS 服务详情

- **模型**: Fun-CosyVoice3-0.5B-2512
- **端口**: 50000
- **模型页**: [ModelScope](https://modelscope.cn/models/FunAudioLLM/Fun-CosyVoice3-0.5B-2512)
- **详细文档**: [tts_model/README.md](tts_model/README.md)

## 功能使用

### TTS 语音合成

1. 上传或录制参考音频（作为音色样本）
2. 输入参考音频对应的文字
3. 输入要合成的目标文本
4. 点击"生成语音"
5. 等待处理完成，下载或播放生成的音频

### ASR 语音识别

**自动识别**：
1. 上传参考音频
2. 点击"提取音频文字"按钮
3. 系统自动调用 ASR 服务识别文本

**手动使用**：
```python
from asr_client import transcribe_audio_sync

result = transcribe_audio_sync(
    "audio.wav",
    backend_type="funasr",
    mode="2pass-offline"
)
print(result.text)
```

### 音色预设管理

**保存预设**：
1. 上传/录制参考音频
2. 输入预设名称和描述
3. 点击"保存为预设"

**使用预设**：
1. 从预设列表选择
2. 自动填充音频和文本

## ASR 后端配置

### FunASR 后端（推荐）

```python
ASR_BACKEND_CONFIG = {
    "funasr": {
        "uri": "ws://localhost:10095/ws",
        "mode": "2pass-offline",      # offline/online/2pass-offline/2pass-online
        "chunk_size": [5, 10, 5],     # 分块大小
        "hotwords": '{"阿里巴巴": 20}', # 热词增强
    }
}
```

### WebSocket 后端

```python
ASR_BACKEND_CONFIG = {
    "websocket": {
        "uri": "ws://localhost:8080/asr",
    }
}
```

### 自定义后端

```python
from asr_backends import ASRBackend, ASRBackendFactory

class MyASRBackend(ASRBackend):
    async def connect(self) -> bool:
        # 实现连接逻辑
        pass

    async def transcribe(self, audio_path: str, callback=None) -> str:
        # 实现识别逻辑
        pass

# 注册并使用
ASRBackendFactory.register_backend("myasr", MyASRBackend)
```

## Docker 配置

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `API_HOST` | 127.0.0.1 | TTS API 地址 |
| `API_PORT` | 50000 | TTS API 端口 |
| `API_MODE` | zero_shot | TTS 工作模式 |
| `SERVER_NAME` | 0.0.0.0 | Web 服务监听地址 |
| `SERVER_PORT` | 7863 | Web 服务端口 |
| `ASR_ENABLED` | false | 是否启用 ASR |
| `ASR_BACKEND_TYPE` | funasr | ASR 后端类型 |

### 数据持久化

Docker 容器使用以下数据卷：
- `./presets:/app/presets` - 音色预设存储
- `./temp:/app/temp` - 临时文件存储

### 常用命令

```bash
# 查看容器状态
docker ps

# 查看实时日志
docker logs -f voice-text-tts

# 停止容器
./stop.sh

# 重启容器
docker restart voice-text-tts

# 进入容器
docker exec -it voice-text-tts bash

# 清理容器和镜像
./clean.sh
```

## 测试 ASR 服务

### 启动模拟服务器

```bash
cd asr_server_mock
python asr_server.py
# 或
./start_server.sh
```

### 测试连接

```bash
cd asr_server_mock
python test_client.py
```

## 技术栈

### 核心技术
- **前端框架**：Gradio 6.2.0
- **语言**：Python 3.13
- **音频处理**：FFmpeg, pydub, numpy
- **通信协议**：HTTP, WebSocket

### TTS 技术
- **模型**：Fun-CosyVoice3-0.5B-2512
- **推理引擎**：FunASR

### ASR 技术
- **主要后端**：FunASR
- **备选后端**：WebSocket

### 容器化
- **容器引擎**：Docker
- **编排工具**：Docker Compose
- **基础镜像**：Python 3.13 Slim

## 故障排查

### TTS 相关

**问题**：无法连接 TTS 服务
```bash
# 检查 TTS API 端口
netstat -an | grep 50000

# 检查配置
cat voice_text_tts/config.py
```

### ASR 相关

**问题**：ASR 识别失败
- 检查 ASR 服务是否启动
- 验证 `ASR_URI` 配置是否正确
- 检查音频格式和质量

**问题**：连接超时
```python
# 增加 config.py 中的超时时间
ASR_TIMEOUT = 120
```

### Docker 相关

**问题**：容器无法启动
```bash
# 查看详细日志
docker logs voice-text-tts

# 检查端口占用
docker port voice-text-tts
```

**问题**：音频处理失败
```bash
# 验证 FFmpeg
docker exec voice-text-tts ffmpeg -version
```

## 开发指南

### 项目依赖

主要依赖项：
- `gradio>=6.2.0` - Web 框架
- `websockets` - WebSocket 通信
- `pydub` - 音频处理
- `numpy` - 数值计算
- `requests` - HTTP 请求

### 添加新功能

1. **新增 ASR 后端**：继承 `ASRBackend` 类
2. **添加 TTS 模式**：修改 `config.py` 中的 `API_MODE`
3. **扩展音色预设**：修改预设存储格式

### 代码结构

```
voice_text_tts/
├── app.py              # Gradio 界面定义
├── asr_client.py       # ASR 客户端封装
├── asr_backends.py     # ASR 后端抽象
└── config.py           # 配置管理
```

## 相关文档

- [ASR 项目指南](ASR_PROJECT_GUIDE.md) - ASR 功能详细说明
- [FunASR 参考](FUNASR_REFERENCE.md) - FunASR 使用参考
- [TTS 模型服务](tts_model/README.md) - TTS Docker 部署和代码更新
- [voice_text_tts/README.md](voice_text_tts/README.md) - 应用详细文档
- [voice_text_tts_docker/README.md](voice_text_tts_docker/README.md) - Docker 部署文档
- [asr_server_mock/README.md](asr_server_mock/README.md) - ASR 服务器文档

## 分支信息

- **主分支**：`develop`
- **历史分支**：`develop_ASR`（ASR 语音识别集成）、`develop_smooth`（流式音频播放）
- **状态**：活跃开发

## 许可证

MIT License

## 更新日志

### 2026-01-28
- 优化 Docker 部署配置
- 添加音色预设管理功能
- 完善项目文档结构

### 2026-01-23
- 集成 ASR 语音识别功能
- 实现 FunASR 后端支持
- 添加 WebSocket 通用后端

---

**开发者**：郭浩然
**项目状态**：开发中
**最后更新**：2026-01-28
