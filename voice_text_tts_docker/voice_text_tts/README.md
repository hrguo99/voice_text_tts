# 语音生成功能 (Voice Text TTS)

基于 Gradio 和 Fun-CosyVoice3-0.5B-2512 的语音合成应用，支持 ASR 语音识别和多后端支持。

## 功能特点

- 🎤 **音频输入**: 上传音频文件或实时麦克风录制
- 🎙️ **ASR 语音识别**: 自动识别参考音频中的文字
- 🔄 **多 ASR 后端**: 支持 FunASR、通用 WebSocket 等多种后端
- 📊 **波形可视化**: 实时显示音频波形
- 🎵 **自动格式转换**: 支持 WAV、MP3、M4A 转换
- 🎨 **简洁界面**: 白色和浅蓝色主题

## 快速开始

### 1. 安装依赖

```bash
# 安装 FFmpeg
sudo apt-get install ffmpeg  # Linux
brew install ffmpeg          # macOS
choco install ffmpeg         # Windows

# 安装 Python 依赖
pip install -r requirements.txt
```

### 2. 配置

编辑 [config.py](config.py):

```python
# TTS API 配置
API_HOST = "127.0.0.1"
API_PORT = "50000"
API_MODE = "zero_shot"

# ASR 配置
ASR_ENABLED = True
ASR_BACKEND_TYPE = "funasr"  # 或 "websocket"
ASR_BACKEND_CONFIG = {
    "funasr": {
        "uri": "ws://localhost:10095/ws",
        "mode": "2pass-offline",
    }
}
```

### 3. 运行

```bash
python app.py
```

访问: http://127.0.0.1:7862

## 使用方法

### TTS 语音合成

1. 上传或录制参考音频
2. 输入参考音频对应的文字（或点击"提取音频文字"自动识别）
3. 输入要合成的文本
4. 点击"生成语音"

### ASR 语音识别

点击"提取音频文字"按钮自动识别参考音频内容。

```python
from asr_client import transcribe_audio_sync

# 使用默认配置
result = transcribe_audio_sync("audio.wav")

# 指定后端
result = transcribe_audio_sync(
    "audio.wav",
    backend_type="funasr",
    mode="2pass-offline"
)
```

## ASR 后端

### FunASR 后端

支持多种模式：
- `offline` - 离线批量识别
- `online` - 流式识别
- `2pass-offline` - 两遍识别（推荐）
- `2pass-online` - 两遍流式识别

```python
ASR_BACKEND_CONFIG = {
    "funasr": {
        "uri": "ws://localhost:10095/ws",
        "mode": "2pass-offline",
        "chunk_size": [5, 10, 5],
        "hotwords": '{"阿里巴巴": 20}',
    }
}
```

### 通用 WebSocket 后端

适用于任何 WebSocket ASR 服务：

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

    async def disconnect(self):
        # 实现断开逻辑
        pass

    async def transcribe(self, audio_path: str, callback=None) -> str:
        # 实现识别逻辑
        pass

# 注册并使用
ASRBackendFactory.register_backend("myasr", MyASRBackend)
result = transcribe_audio_sync("audio.wav", backend_type="myasr")
```

## 项目结构

```
voice_text_tts/
├── app.py              # Gradio 应用主程序
├── asr_backends.py     # ASR 后端抽象层
├── asr_client.py       # ASR 客户端
├── config.py           # 配置文件
├── requirements.txt    # Python 依赖
├── ASR_README.md       # ASR 详细文档
└── README.md           # 本文档
```

## API 参考

### ASRClient

```python
from asr_client import ASRClient

# 异步使用
async with ASRClient(backend_type="funasr") as client:
    result = await client.transcribe_audio_file("audio.wav")
```

### 配置参数

**FunASR 后端参数:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| uri | str | ws://localhost:10095/ws | 服务器地址 |
| mode | str | 2pass-offline | ASR 模式 |
| chunk_size | list | [5, 10, 5] | 分块大小 |
| hotwords | str | {} | 热词配置 |
| use_itn | bool | True | 是否使用 ITN |

## 技术栈

- **前端**: Gradio 5.0+
- **音频处理**: FFmpeg, numpy, wave
- **ASR**: FunASR, WebSocket
- **TTS**: Fun-CosyVoice3-0.5B-2512
- **语言**: Python 3.13

## 常见问题

### Q: ASR 连接失败？

A: 检查 ASR 服务是否启动，以及 `config.py` 中的 URI 配置是否正确。

### Q: 如何切换 ASR 后端？

A: 修改 `config.py` 中的 `ASR_BACKEND_TYPE` 和 `ASR_BACKEND_CONFIG`。

### Q: 识别结果为空？

A: 检查音频质量、格式，以及 ASR 服务日志。

## 支持

- 详细文档: [ASR_README.md](ASR_README.md)
- 问题反馈: 项目 Issues
