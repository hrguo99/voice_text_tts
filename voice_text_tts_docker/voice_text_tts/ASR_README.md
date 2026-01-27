# ASR 通用接口详细文档

## 架构设计

```
app.py (应用层)
    ↓
asr_client.py (客户端层)
    ↓
asr_backends.py (后端抽象层)
    ├── FunASRBackend
    ├── GenericWebSocketASRBackend
    └── 自定义后端
    ↓
config.py (配置层)
```

## 核心组件

### asr_backends.py

**ASRBackend** - 抽象基类
```python
class ASRBackend(ABC):
    @abstractmethod
    async def connect(self) -> bool: pass

    @abstractmethod
    async def disconnect(self): pass

    @abstractmethod
    async def transcribe(self, audio_path: str, callback=None) -> str: pass
```

**FunASRBackend** - FunASR 服务实现
- 支持 2pass、offline、online 模式
- 支持热词、ITN
- 完整的 FunASR 协议实现

**GenericWebSocketASRBackend** - 通用 WebSocket 实现
- 适用于任何 WebSocket ASR 服务
- 可自定义初始化和结束消息

**ASRBackendFactory** - 工厂类
```python
# 创建后端
backend = ASRBackendFactory.create_backend("funasr", **config)

# 注册自定义后端
ASRBackendFactory.register_backend("myasr", MyASRBackend)
```

### asr_client.py

**ASRClient** - 通用客户端
```python
client = ASRClient(
    backend_type="funasr",  # 后端类型
    uri="ws://localhost:10095/ws",
    mode="2pass-offline"
)

# 同步接口
result = transcribe_audio_sync("audio.wav", backend_type="funasr")

# 异步接口
async with ASRClient(backend_type="funasr") as client:
    result = await client.transcribe_audio_file("audio.wav")
```

## FunASR 模式详解

### offline 模式
离线批量识别，准确率高，适合已录制的音频文件。

```python
ASR_BACKEND_CONFIG = {
    "funasr": {
        "mode": "offline",
        "chunk_size": [5, 10, 5],
    }
}
```

### online 模式
流式识别，实时性好，适合实时语音输入。

```python
ASR_BACKEND_CONFIG = {
    "funasr": {
        "mode": "online",
        "chunk_size": [5, 10, 5],
    }
}
```

### 2pass-offline 模式（推荐）
两遍识别，第一遍快速，第二遍精细，兼顾速度和准确率。

```python
ASR_BACKEND_CONFIG = {
    "funasr": {
        "mode": "2pass-offline",
        "chunk_size": [5, 10, 5],
    }
}
```

### 2pass-online 模式
两遍识别的流式版本。

```python
ASR_BACKEND_CONFIG = {
    "funasr": {
        "mode": "2pass-online",
        "chunk_size": [5, 10, 5],
    }
}
```

## 完整配置示例

### FunASR 完整配置

```python
ASR_BACKEND_CONFIG = {
    "funasr": {
        # 连接配置
        "uri": "ws://localhost:10095/ws",

        # 模式配置
        "mode": "2pass-offline",
        "chunk_size": [5, 10, 5],
        "chunk_interval": 10,

        # 性能配置
        "encoder_chunk_look_back": 4,
        "decoder_chunk_look_back": 0,

        # 功能配置
        "hotwords": '{"阿里巴巴": 20, "华为": 20}',
        "use_itn": True,
    }
}
```

### 通用 WebSocket 完整配置

```python
ASR_BACKEND_CONFIG = {
    "websocket": {
        "uri": "ws://localhost:8080/asr",
        "init_message": {"is_speaking": True},
        "end_message": {"is_speaking": False},
    }
}
```

## 扩展自定义后端

### 完整示例

```python
import asyncio
from typing import Optional, Callable
from asr_backends import ASRBackend, ASRBackendFactory

class CustomASRBackend(ASRBackend):
    """自定义 ASR 后端示例"""

    def __init__(self, api_key: str = "", **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.client = None

    async def connect(self) -> bool:
        """连接到 ASR 服务"""
        import logging
        logging.info(f"连接到自定义 ASR 服务")

        # 模拟连接
        self.client = {"connected": True}
        return True

    async def disconnect(self):
        """断开连接"""
        if self.client:
            self.client = None

    async def transcribe(
        self,
        audio_path: str,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """转录音频"""
        import os

        if progress_callback:
            progress_callback("读取音频文件")

        # 检查文件
        if not os.path.exists(audio_path):
            if progress_callback:
                progress_callback("音频文件不存在")
            return None

        if progress_callback:
            progress_callback("识别中...")

        # 模拟识别延迟
        await asyncio.sleep(0.5)

        # 返回模拟结果
        return "这是自定义后端的识别结果"

# 注册后端
ASRBackendFactory.register_backend("custom", CustomASRBackend)

# 使用自定义后端
if __name__ == "__main__":
    from asr_client import transcribe_audio_sync

    result = transcribe_audio_sync(
        "test.wav",
        backend_type="custom",
        api_key="your-api-key"
    )
    print(f"识别结果: {result}")
```

## 高级用法

### 进度回调

```python
def progress_handler(msg):
    print(f"[进度] {msg}")

result = transcribe_audio_sync(
    "audio.wav",
    progress_callback=progress_handler
)
```

### 连接复用

```python
import asyncio
from asr_client import ASRClient

async def transcribe_multiple():
    async with ASRClient(backend_type="funasr") as client:
        # 复用同一个连接识别多个文件
        for i in range(10):
            result = await client.transcribe_audio_file(f"audio{i}.wav")
            print(f"文件 {i}: {result}")

asyncio.run(transcribe_multiple())
```

### 异步并发

```python
import asyncio
from asr_client import ASRClient

async def transcribe_concurrent():
    async with ASRClient(backend_type="funasr") as client:
        # 并发识别多个文件
        tasks = [
            client.transcribe_audio_file(f"audio{i}.wav")
            for i in range(10)
        ]
        results = await asyncio.gather(*tasks)
        return results

results = asyncio.run(transcribe_concurrent())
```

## 错误处理

### 常见错误及解决方案

**1. 连接失败**
```python
# 检查服务是否启动
import websockets
async with websockets.connect("ws://localhost:10095/ws") as ws:
    print("连接成功")
```

**2. 识别结果为空**
```python
# 检查音频文件
import os
if os.path.exists("audio.wav"):
    print(f"文件大小: {os.path.getsize('audio.wav')} 字节")
```

**3. 超时错误**
```python
# 增加超时时间
result = transcribe_audio_sync(
    "audio.wav",
    backend_type="funasr"
)
```

## 调试技巧

### 启用详细日志

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 使用后端时查看详细日志
result = transcribe_audio_sync("audio.wav")
```

### 测试后端

```python
# 测试特定后端
from asr_backends import ASRBackendFactory

backend = ASRBackendFactory.create_backend(
    "funasr",
    uri="ws://localhost:10095/ws"
)

# 测试连接
async def test():
    connected = await backend.connect()
    print(f"连接状态: {connected}")
    await backend.disconnect()

asyncio.run(test())
```

## 性能优化

### 批量识别优化

```python
# 使用连接池避免重复连接
async with ASRClient(backend_type="funasr") as client:
    for audio_file in audio_list:
        result = await client.transcribe_audio_file(audio_file)
```

### 内存优化

```python
# 对于大文件，使用流式处理
ASR_BACKEND_CONFIG = {
    "funasr": {
        "mode": "online",  # 流式模式
        "chunk_size": [5, 10, 5],
    }
}
```

## 参考资源

- [FunASR 官方文档](https://github.com/alibaba-damo-academy/FunASR)
- [WebSocket 协议](https://tools.ietf.org/html/rfc6455)
- [项目主文档](README.md)
