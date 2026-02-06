# Voice Text TTS - AI 助手项目指南

本文档帮助 AI 助手快速理解项目架构和协助开发。

## 项目概述

基于 Gradio 的语音合成（TTS）和语音识别（ASR）应用，支持零样本语音克隆和 Docker 部署。

## 项目结构

```
voice_text_tts/
├── voice_text_tts/              # 核心应用
│   ├── app.py                   # Gradio 主程序
│   ├── app_tabs.py              # UI 组件
│   ├── asr_backends.py          # ASR 后端抽象
│   ├── asr_client.py            # ASR 客户端
│   ├── config.py                # 配置文件
│   └── requirements.txt
│
├── voice_text_tts_docker/       # Docker 部署
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── build.sh / start.sh
│   └── presets/                 # 音色预设存储
│
└── tts_model/                   # TTS 模型服务
```

## 核心组件

| 文件 | 职责 |
|------|------|
| `app.py` | Gradio UI 主程序，AudioConverter, VoicePresetManager |
| `asr_backends.py` | ASR 后端抽象（ASRBackend, FunASRBackend, WebSocketBackend） |
| `asr_client.py` | ASR 客户端（WebSocket 通信） |
| `config.py` | 配置管理（环境变量） |

## 技术栈

- **前端**: Gradio 6.3.0
- **语言**: Python 3.13
- **音频**: FFmpeg, pydub, numpy
- **TTS**: Fun-CosyVoice3-0.5B-2512 (Port 50000)
- **ASR**: FunASR (Port 10095)
- **Docker**: Python 3.13 Slim

## 关键配置

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `API_HOST` | 127.0.0.1 | TTS API 地址 |
| `API_PORT` | 50000 | TTS API 端口 |
| `SERVER_PORT` | 7864 | Web 服务端口 |
| `ASR_ENABLED` | false | 是否启用 ASR |
| `ASR_BACKEND_TYPE` | funasr | ASR 后端类型 |
| `PRESETS_DIR` | None | 预设保存路径 |

### ASR 配置

```python
ASR_BACKEND_CONFIG = {
    "funasr": {
        "uri": "ws://localhost:10095/ws",
        "mode": "2pass-offline",
    }
}
```

## 快速启动

```bash
# 本地启动
cd voice_text_tts
pip install -r requirements.txt
python app.py

# Docker 启动
cd voice_text_tts_docker
./build.sh && ./start.sh
```

## 常用命令

```bash
# Git
git checkout develop_ASR      # 主分支

# Docker
docker logs -f voice-text-tts  # 查看日志
./voice_text_tts_docker/stop.sh # 停止容器

# ASR 测试
python -c "from asr_client import transcribe_audio_sync; print(transcribe_audio_sync('audio.wav').text)"
```

## 提交规范

- `feat:` - 新功能
- `fix:` - 缺陷修复
- `chore:` - 构建/工具链/依赖更新
- `docs:` - 文档更新
- `refactor:` - 代码重构

示例：`feat(ui): 添加实时音频流式播放功能`

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| TTS 连接失败 | 检查 `config.py` 中 `API_HOST`/`API_PORT`，确认 TTS 服务运行在 50000 |
| ASR 连接失败 | 检查 `ASR_URI` 配置，确认 ASR 服务运行在 10095 |
| Docker 容器启动失败 | `docker logs voice-text-tts` 查看日志 |
| 音频处理失败 | 验证 FFmpeg：`docker exec voice-text-tts ffmpeg -version` |

## AI 助手协作提示

1. **修改前先阅读**：使用 `Read` 工具阅读文件内容
2. **关注配置**：配置支持环境变量，保持兼容性
3. **Docker 注意**：预设存储在持久化卷 `presets/`
4. **ASR 抽象**：继承 `ASRBackend` 可扩展新后端
5. **遵循提交规范**：使用约定式提交格式

## 项目信息

- **主分支**: `develop_ASR`
- **当前分支**: `develop_smooth`
- **开发者**: 郭浩然
