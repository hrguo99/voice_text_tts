# 快速使用指南

## 一、启动ASR服务器

```bash
cd asr_server_mock
python asr_server.py
```

**输出**:
```
2024-01-23 10:00:00 - asr_server - INFO - 启动ASR服务器: ws://localhost:10095
2024-01-23 10:00:00 - asr_server - INFO - ASR服务器已启动在 ws://localhost:10095
按 Ctrl+C 停止服务器
```

## 二、测试ASR服务器

**新开一个终端**:

```bash
cd asr_server_mock
python test_client.py
```

**输出**:
```
==================================================
识别结果:
==================================================
{
  "status": "success",
  "text": "希望你以后能够做得比我还好呦。",
  "confidence": 0.95
}
==================================================
```

## 三、运行voice_text_tts应用

**再开一个终端**:

```bash
cd voice_text_tts
python app.py
```

浏览器访问: `http://127.0.0.1:7862`

## 四、测试完整流程

### 在Gradio界面中操作：

1. ✅ **上传或录制参考音频**
   - 点击"上传音频"标签上传文件
   - 或点击"录制音频"标签进行录音

2. ⚠️ **参考音频文本留空**（重要！）
   - 不要在这个输入框输入任何内容
   - 系统会自动调用ASR识别

3. ✅ **输入要合成的文本**
   - 在"输入文本"框输入：`你好，这是一个测试。`

4. ✅ **点击"生成语音"按钮**
   - 系统会自动：
     1. 连接ASR服务器
     2. 识别参考音频
     3. 使用识别结果作为参考文本
     4. 生成合成语音

5. ✅ **查看结果**
   - 进度条显示识别和合成进度
   - 生成完成后可以播放音频

## 常用命令

```bash
# 启动ASR服务器（使用默认配置）
cd asr_server_mock && python asr_server.py

# 启动ASR服务器（自定义端口）
python asr_server.py --port 10096

# 测试ASR服务器（单次）
python test_client.py

# 测试ASR服务器（多次）
python test_client.py --count 5

# 启动Gradio应用
cd ../voice_text_tts && python app.py
```

## 目录结构

```
asr_server_mock/
├── asr_server.py      # 运行这个启动服务器
├── test_client.py     # 运行这个测试服务器
├── start_server.sh    # Linux启动脚本
├── test.sh           # Linux测试脚本
└── README.md         # 详细文档

voice_text_tts/
├── app.py            # 运行这个启动Gradio应用
├── asr_client.py     # ASR客户端（自动调用）
├── config.py         # 配置文件
└── README_ASR.md     # 详细文档
```

## 故障排除

### 问题1: "ModuleNotFoundError: No module named 'websockets'"

**解决**:
```bash
pip install websockets
```

### 问题2: "连接ASR服务器失败"

**解决**:
- 确认ASR服务器已启动
- 检查端口10095是否被占用
- 查看 `voice_text_tts/config.py` 中 `ASR_URI` 配置

### 问题3: Gradio界面无法访问

**解决**:
- 确认app.py已启动
- 检查端口7862是否被占用
- 浏览器访问: `http://127.0.0.1:7862`

## 下一步

- 📖 阅读详细文档: [README.md](README.md)
- 🔧 配置ASR服务: 修改 `config.py`
- 🚀 替换为真实ASR引擎
- 📝 查看完整指南: [../ASR_PROJECT_GUIDE.md](../ASR_PROJECT_GUIDE.md)

## 需要帮助？

查看详细文档：
- [ASR项目完整指南](../ASR_PROJECT_GUIDE.md)
- [ASR客户端说明](../voice_text_tts/README_ASR.md)
- [模拟服务器文档](README.md)
