# ASR语音识别项目 - 完整指南

本项目包含ASR（自动语音识别）功能的完整实现，包括客户端和模拟服务器。

## 项目结构

```
guohaoran/
├── voice_text_tts/              # 语音合成应用（含ASR客户端）
│   ├── asr_client.py            # ASR WebSocket客户端
│   ├── app.py                   # Gradio应用（集成ASR功能）
│   ├── config.py                # 配置文件（含ASR配置）
│   └── README_ASR.md            # ASR功能详细说明
│
└── asr_server_mock/             # 模拟ASR服务器
    ├── asr_server.py            # WebSocket服务器实现
    ├── test_client.py           # 测试客户端
    ├── README.md                # 服务器文档
    ├── requirements.txt         # 依赖包
    ├── start_server.sh          # 启动脚本
    └── test.sh                  # 测试脚本
```

## 快速开始

### 1. 安装依赖

两个项目都需要安装 `websockets`：

```bash
pip install websockets
```

### 2. 启动ASR服务器

```bash
cd asr_server_mock
python asr_server.py
```

或使用启动脚本：

```bash
cd asr_server_mock
./start_server.sh
```

服务器会监听 `ws://localhost:10095`

### 3. 测试ASR服务器

```bash
cd asr_server_mock
python test_client.py
```

或使用测试脚本：

```bash
cd asr_server_mock
./test.sh
```

### 4. 运行voice_text_tts应用

```bash
cd voice_text_tts
python app.py
```

访问: `http://127.0.0.1:7862`

## 使用场景

### 场景1: 测试ASR客户端

1. 启动模拟ASR服务器
2. 运行测试客户端验证连接
3. 查看识别结果

### 场景2: 集成到Gradio应用

1. 确保ASR服务器运行
2. 启动voice_text_tts应用
3. 在Gradio界面：
   - 上传/录制参考音频
   - **参考音频文本留空**（关键！）
   - 输入要合成的文本
   - 点击"生成语音"
   - 系统自动调用ASR识别音频

### 场景3: 开发和调试

1. 修改模拟服务器的识别结果
2. 调整处理延迟
3. 查看详细日志
4. 测试错误处理

## 配置说明

### voice_text_tts/config.py

```python
# ASR配置
ASR_ENABLED = True  # 是否启用ASR功能
ASR_URI = "ws://localhost:10095/ws"  # ASR服务地址
ASR_TIMEOUT = 60  # 超时时间（秒）
```

### asr_server_mock/asr_server.py

命令行参数：

```bash
python asr_server.py --host localhost --port 10095
```

## WebSocket协议

### 客户端 → 服务器

```json
{
  "type": "audio",
  "data": "音频数据的十六进制字符串"
}
```

### 服务器 → 客户端

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

## 功能特点

### ASR客户端 (voice_text_tts)

✅ 异步WebSocket通信
✅ 同步接口封装
✅ 进度回调支持
✅ 完整错误处理
✅ 音频格式转换
✅ 配置灵活

### 模拟ASR服务器 (asr_server_mock)

✅ 完整WebSocket服务器
✅ 模拟识别过程（1-3秒）
✅ 预设识别结果
✅ 一致的识别结果（相同音频=相同结果）
✅ 详细日志记录
✅ 可配置端口和地址
✅ 测试客户端工具

## 测试命令

### 基础测试

```bash
# 测试单次请求
python test_client.py

# 测试多次请求
python test_client.py --count 5

# 自定义服务器地址
python test_client.py --uri ws://192.168.1.100:10095/ws
```

### 集成测试

```bash
# 1. 启动ASR服务器（终端1）
cd asr_server_mock
python asr_server.py

# 2. 启动Gradio应用（终端2）
cd ../voice_text_tts
python app.py

# 3. 浏览器访问
# http://127.0.0.1:7862
```

## 日志示例

### 服务器日志

```
2024-01-23 10:05:25 - asr_server - INFO - [127.0.0.1:54321] 新客户端连接
2024-01-23 10:05:25 - asr_server - INFO - [127.0.0.1:54321] 收到消息类型: audio
2024-01-23 10:05:25 - asr_server - INFO - [127.0.0.1:54321] 开始识别音频，预计耗时 2.15 秒
2024-01-23 10:05:26 - asr_server - INFO - [127.0.0.1:54321] 正在识别...
2024-01-23 10:05:27 - asr_server - INFO - [127.0.0.1:54321] 识别中...
2024-01-23 10:05:27 - asr_server - INFO - [127.0.0.1:54321] 识别完成: 希望你以后能够做得比我还好呦。
```

### 客户端日志

```
2024-01-23 10:05:25 - test_client - INFO - 连接到ASR服务器: ws://localhost:10095/ws
2024-01-23 10:05:25 - test_client - INFO - ✓ 成功连接到服务器
2024-01-23 10:05:25 - test_client - INFO - 发送模拟音频数据...
2024-01-23 10:05:25 - test_client - INFO - ✓ 音频数据已发送
2024-01-23 10:05:25 - test_client - INFO - 等待识别结果...
2024-01-23 10:05:27 - test_client - INFO - ✓ 收到识别结果
2024-01-23 10:05:27 - test_client - INFO - 识别成功！
2024-01-23 10:05:27 - test_client - INFO - 文本: 希望你以后能够做得比我还好呦。
2024-01-23 10:05:27 - test_client - INFO - 置信度: 0.95
```

## 故障排查

### 问题1: 无法连接到ASR服务器

**检查清单**:
- [ ] ASR服务器是否已启动？
- [ ] 端口号是否正确（默认10095）？
- [ ] 防火墙是否允许连接？
- [ ] 配置文件中ASR_URI是否正确？

**解决方法**:
```bash
# 检查端口是否被监听
netstat -an | grep 10095

# 或使用lsof
lsof -i :10095

# 测试连接
telnet localhost 10095
```

### 问题2: 识别超时

**解决方法**:
```python
# 增加 voice_text_tts/config.py 中的超时时间
ASR_TIMEOUT = 120  # 增加到120秒
```

### 问题3: 模块导入错误

**解决方法**:
```bash
# 确认在正确的目录
cd voice_text_tts

# 安装依赖
pip install websockets

# 测试导入
python -c "from asr_client import transcribe_audio_sync; print('OK')"
```

## 扩展开发

### 替换为真实ASR引擎

修改 `asr_server_mock/asr_server.py` 中的 `_process_audio` 方法：

```python
async def _process_audio(self, websocket, client_id: str, data: dict):
    # 解码音频
    audio_hex = data.get("data", "")
    audio_bytes = bytes.fromhex(audio_hex)

    # 调用真实ASR引擎（示例：FunASR）
    from funasr import AutoModel
    asr_model = AutoModel(model="paraformer-zh")
    result = asr_model.generate(input=audio_bytes)
    result_text = result[0]["text"]

    # 返回结果
    response = {
        "status": "success",
        "text": result_text,
        "confidence": 0.95,
        "processing_time": 1.5,
        "timestamp": datetime.now().isoformat()
    }

    await websocket.send(json.dumps(response))
```

## 相关文档

- [voice_text_tts/README_ASR.md](voice_text_tts/README_ASR.md) - ASR客户端详细说明
- [voice_text_tts/ASR_IMPLEMENTATION.md](voice_text_tts/ASR_IMPLEMENTATION.md) - 实现细节
- [asr_server_mock/README.md](asr_server_mock/README.md) - 服务器文档

## 分支信息

- **分支**: `develop_ASR`
- **基于**: `master`
- **功能**: ASR语音识别集成

## 许可证

MIT License

---

**开发者**: Claude Sonnet 4.5
**日期**: 2026-01-23
**分支**: develop_ASR
