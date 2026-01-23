# 模拟ASR WebSocket服务器

这是一个用于测试ASR客户端功能的模拟WebSocket服务器。

## 功能特点

- ✅ 完整的WebSocket服务器实现
- ✅ 模拟语音识别过程
- ✅ 支持音频数据接收
- ✅ 返回JSON格式的识别结果
- ✅ 可配置服务器地址和端口
- ✅ 详细的日志记录

## 项目结构

```
asr_server_mock/
├── asr_server.py      # ASR服务器实现
├── test_client.py     # 测试客户端脚本
├── README.md          # 本文档
└── requirements.txt   # 依赖包列表
```

## 安装依赖

```bash
pip install -r requirements.txt
```

或直接安装：

```bash
pip install websockets
```

## 使用方法

### 1. 启动ASR服务器

默认配置（localhost:10095）：

```bash
python asr_server.py
```

自定义配置：

```bash
python asr_server.py --host 0.0.0.0 --port 10095
```

参数说明：
- `--host`: 服务器地址（默认: localhost）
- `--port`: 服务器端口（默认: 10095）

启动成功后会看到：

```
2024-01-23 10:00:00 - asr_server - INFO - 启动ASR服务器: ws://localhost:10095
2024-01-23 10:00:00 - asr_server - INFO - 等待客户端连接...
2024-01-23 10:00:00 - asr_server - INFO - ASR服务器已启动在 ws://localhost:10095
2024-01-23 10:00:00 - asr_server - INFO - 按 Ctrl+C 停止服务器
```

### 2. 测试服务器

使用测试客户端脚本：

```bash
# 单次测试
python test_client.py

# 多次测试
python test_client.py --count 5

# 自定义服务器地址
python test_client.py --uri ws://192.168.1.100:10095/ws
```

测试成功示例：

```
==================================================
识别结果:
==================================================
{
  "status": "success",
  "text": "希望你以后能够做得比我还好呦。",
  "confidence": 0.95,
  "processing_time": 2.15,
  "timestamp": "2024-01-23T10:05:30.123456"
}
==================================================
```

### 3. 与voice_text_tts集成

1. 确保ASR服务器已启动（使用默认端口10095）
2. 启动voice_text_tts应用：

```bash
cd ../voice_text_tts
python app.py
```

3. 在Gradio界面中：
   - 上传或录制参考音频
   - **参考音频文本留空**
   - 输入要合成的文本
   - 点击"生成语音"
   - 系统会自动调用ASR服务识别音频

## WebSocket协议

### 请求格式

客户端发送：

```json
{
  "type": "audio",
  "data": "音频数据的十六进制字符串"
}
```

### 响应格式

成功响应：

```json
{
  "status": "success",
  "text": "识别的文本内容",
  "confidence": 0.95,
  "processing_time": 2.15,
  "timestamp": "2024-01-23T10:05:30.123456"
}
```

错误响应：

```json
{
  "status": "error",
  "error": "错误消息",
  "timestamp": "2024-01-23T10:05:30.123456"
}
```

## 模拟识别结果

服务器内置了以下模拟识别结果：

1. 希望你以后能够做得比我还好呦。
2. 你好，我是语音识别助手。
3. 今天的天气真不错。
4. 这是一个测试音频文件。
5. 语音识别功能正在运行中。
6. 请说话，我会帮您识别文字。
7. 人工智能技术正在快速发展。
8. 语音合成的效果越来越好了。
9. 欢迎使用语音识别服务。
10. 这是一个模拟的ASR服务器。

服务器会根据接收到的音频数据选择一个"伪随机"但一致的结果，即相同的音频数据会产生相同的识别结果。

## 日志示例

服务器日志：

```
2024-01-23 10:05:25 - asr_server - INFO - [127.0.0.1:54321] 新客户端连接
2024-01-23 10:05:25 - asr_server - INFO - [127.0.0.1:54321] 收到消息类型: audio
2024-01-23 10:05:25 - asr_server - INFO - [127.0.0.1:54321] 开始识别音频，预计耗时 2.15 秒
2024-01-23 10:05:26 - asr_server - INFO - [127.0.0.1:54321] 正在识别...
2024-01-23 10:05:27 - asr_server - INFO - [127.0.0.1:54321] 识别中...
2024-01-23 10:05:27 - asr_server - INFO - [127.0.0.1:54321] 识别完成: 希望你以后能够做得比我还好呦。
2024-01-23 10:05:28 - asr_server - INFO - [127.0.0.1:54321] 客户端断开连接
```

## 配置voice_text_tts

确保 `voice_text_tts/config.py` 中的ASR配置正确：

```python
ASR_ENABLED = True
ASR_URI = "ws://localhost:10095/ws"  # 与服务器端口一致
ASR_TIMEOUT = 60
```

## 故障排查

### 问题1: 无法连接到ASR服务器

**症状**: `ConnectionRefusedError` 或 `连接被拒绝`

**解决方案**:
1. 确认ASR服务器已启动
2. 检查端口号是否正确（默认10095）
3. 检查防火墙设置

### 问题2: 识别超时

**症状**: 识别时间过长或超时

**解决方案**:
1. 增加 `voice_text_tts/config.py` 中的 `ASR_TIMEOUT` 值
2. 这是模拟服务器，识别时间在1-3秒之间

### 问题3: 无法导入websockets模块

**症状**: `ModuleNotFoundError: No module named 'websockets'`

**解决方案**:
```bash
pip install websockets
```

## 扩展开发

### 添加真实的ASR功能

要替换为真实的ASR引擎，可以修改 `asr_server.py` 中的 `_process_audio` 方法：

```python
async def _process_audio(self, websocket, client_id: str, data: dict):
    # 解码音频数据
    audio_hex = data.get("data", "")
    audio_bytes = bytes.fromhex(audio_hex)

    # 调用真实的ASR引擎
    # 例如: FunASR, Whisper, Paraformer等
    result_text = your_asr_engine.recognize(audio_bytes)

    # 发送结果
    response = {
        "status": "success",
        "text": result_text,
        "confidence": 0.95,
        "processing_time": 1.5,
        "timestamp": datetime.now().isoformat()
    }

    await websocket.send(json.dumps(response))
```

## 注意事项

1. 这是模拟服务器，仅用于测试和开发
2. 识别结果是预设的文本，不是真实的语音识别
3. 处理时间在1-3秒之间随机
4. 生产环境应使用真实的ASR服务

## 相关项目

- [voice_text_tts](../voice_text_tts/) - 语音合成应用（使用ASR功能）
- [README_ASR.md](../voice_text_tts/README_ASR.md) - ASR功能详细说明

## 许可证

MIT License
