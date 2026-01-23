# ASR语音识别功能说明

## 功能概述

在 `develop_ASR` 分支中，我们新增了ASR（Automatic Speech Recognition，自动语音识别）功能。当用户在"参考音频文本"输入框中留空时，系统会自动调用ASR服务对参考音频进行语音识别，将识别结果作为参考音频文本。

## 配置说明

### 1. ASR配置项（config.py）

```python
# ASR配置
ASR_ENABLED = True  # 是否启用ASR功能
ASR_URI = "ws://localhost:10095/ws"  # ASR服务WebSocket地址
ASR_TIMEOUT = 60  # ASR识别超时时间（秒）
```

### 2. 配置参数说明

- **ASR_ENABLED**: 控制是否启用ASR功能
  - `True`: 启用ASR，当参考音频文本为空时自动识别
  - `False`: 禁用ASR，用户必须手动输入参考音频文本

- **ASR_URI**: ASR服务的WebSocket服务器地址
  - 默认地址: `ws://localhost:10095/ws`
  - 需要根据实际部署的ASR服务地址进行修改

- **ASR_TIMEOUT**: ASR识别的超时时间（单位：秒）
  - 默认值: 60秒
  - 可根据音频长度调整

## ASR服务部署

### 支持的ASR服务

本项目的ASR客户端设计为通用的WebSocket客户端，支持多种ASR服务。以下是一些常见的ASR服务选项：

#### 1. FunASR（推荐）

FunASR是阿里巴巴开源的语音识别工具包。

**安装：**
```bash
pip install funasr
```

**启动ASR服务器：**
```bash
# 使用默认端口10095
funasr-server --port 10095 --hotword

# 或者使用docker部署
docker run -p 10095:10095 \
  -v /path/to/models:/models \
  registry.cn-hangzhou.aliyuncs.com/funasr/funasr-runtime-sdk-cpu:latest
```

**WebSocket地址：**
```
ws://localhost:10095/ws
```

#### 2. Paraformer

Paraformer是阿里达摩院开源的非自回归端到端语音识别模型。

**安装：**
```bash
pip install paraformer
```

#### 3. Whisper

OpenAI的Whisper模型也需要配合WebSocket服务器使用。

**安装：**
```bash
pip install openai-whisper
```

#### 4. 其他ASR服务

只要提供WebSocket接口的ASR服务都可以，需要根据实际服务的协议格式调整 `asr_client.py` 中的消息格式。

## ASR客户端说明

### 文件位置
```
voice_text_tts/asr_client.py
```

### 主要类和方法

#### ASRClient类

```python
class ASRClient:
    def __init__(self, uri: str = "ws://localhost:10095/ws")
    async def connect(self) -> bool
    async def disconnect(self)
    async def transcribe_audio_file(
        self,
        audio_path: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]
```

#### 同步接口

```python
def transcribe_audio_sync(
    audio_path: str,
    asr_uri: str = "ws://localhost:10095/ws",
    progress_callback: Optional[Callable[[str], None]] = None
) -> Optional[str]
```

### 使用示例

```python
from asr_client import transcribe_audio_sync

# 转录音频文件
result = transcribe_audio_sync(
    "audio.wav",
    asr_uri="ws://localhost:10095/ws",
    progress_callback=lambda msg: print(f"[进度] {msg}")
)

if result:
    print(f"识别结果: {result}")
else:
    print("识别失败")
```

## 工作流程

1. **用户操作**:
   - 上传或录制参考音频
   - 在"参考音频文本"输入框留空
   - 输入要合成的文本
   - 点击"生成语音"按钮

2. **系统处理**:
   - 检测到参考音频文本为空
   - 调用ASR服务识别参考音频
   - 将识别结果作为参考音频文本
   - 继续执行TTS语音合成

3. **进度提示**:
   - 显示ASR连接状态
   - 显示识别进度
   - 识别成功后显示识别结果摘要
   - 识别失败则提示用户手动输入

## 适配不同ASR服务

如果需要使用其他ASR服务，可能需要修改 `asr_client.py` 中的以下部分：

### 1. 消息格式

在 `_send_audio_data` 方法中：

```python
async def _send_audio_data(self, audio_data: bytes):
    # 根据ASR服务的协议调整消息格式
    message = {
        "type": "audio",
        "data": audio_data.hex()  # 可能需要base64编码或其他格式
    }
    await self.websocket.send(json.dumps(message))
```

### 2. 响应解析

在 `_receive_result` 方法中：

```python
async def _receive_result(self) -> Optional[str]:
    response = await self.websocket.recv()
    result = json.loads(response)

    # 根据ASR服务的响应格式调整
    text = result.get("text", "")
    # 或: text = result.get("result", "")
    # 或: text = result.get("transcription", "")

    return text
```

## 故障排查

### 问题1: ASR连接失败

**症状**: 提示"ASR语音识别失败"或"连接ASR服务器失败"

**解决方案**:
1. 检查ASR服务是否已启动
2. 检查 `ASR_URI` 配置是否正确
3. 检查网络连接和防火墙设置
4. 查看ASR服务日志

### 问题2: ASR识别结果为空

**症状**: ASR服务连接成功但返回空文本

**解决方案**:
1. 检查音频文件格式是否支持
2. 检查音频质量是否清晰
3. 检查ASR服务的响应格式，可能需要调整解析代码
4. 查看ASR服务日志确认是否接收到音频数据

### 问题3: 识别速度慢

**症状**: ASR识别耗时过长

**解决方案**:
1. 增加 `ASR_TIMEOUT` 配置值
2. 检查音频文件大小
3. 检查ASR服务性能
4. 考虑使用更高效的ASR模型

## 开发和测试

### 运行ASR客户端测试

```bash
cd voice_text_tts
python asr_client.py
```

注意：需要先准备好测试音频文件 `test.wav`。

### 运行完整应用

```bash
cd voice_text_tts
python app.py
```

访问: `http://127.0.0.1:7862`

## 依赖项

```bash
pip install websockets
```

其他依赖已在项目主依赖中包含。

## 注意事项

1. **ASR服务必须先启动**: 确保ASR WebSocket服务已启动并可访问
2. **音频格式**: ASR服务支持的音频格式可能不同，建议使用WAV格式（16kHz, 单声道）
3. **网络延迟**: WebSocket通信可能受网络影响，建议ASR服务部署在同一内网
4. **并发处理**: 当前实现为同步调用，如需并发处理需要额外优化

## 后续改进方向

1. 支持流式ASR识别（边录音边识别）
2. 添加ASR服务健康检查
3. 支持多种ASR服务自动切换
4. 添加ASR识别结果缓存
5. 优化错误处理和重试机制

## 相关文件

- `voice_text_tts/asr_client.py` - ASR客户端实现
- `voice_text_tts/config.py` - ASR配置
- `voice_text_tts/app.py` - 集成ASR到Gradio界面
