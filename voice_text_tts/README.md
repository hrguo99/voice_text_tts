# 语音生成功能

基于 Gradio 和 Fun-CosyVoice3-0.5B-2512 的语音合成应用，支持通过参考音频和文本生成对应人声的语音。

## 功能特点

- 音频输入支持：上传音频文件和实时麦克风录制
- 音频波形可视化显示
- 自动音频格式转换（支持 WAV、MP3、M4A 转换为模型所需的 WAV 格式）
- 简洁美观的用户界面，白色和浅蓝色主题
- 实时生成语音反馈

## 环境要求

- Python 3.13+
- FFmpeg（用于音频格式转换）

## 安装步骤

### 1. 安装 FFmpeg

**Windows:**
```bash
# 使用 chocolatey
choco install ffmpeg

# 或从官网下载: https://ffmpeg.org/download.html
```

**Linux:**
```bash
sudo apt-get install ffmpeg  # Ubuntu/Debian
sudo yum install ffmpeg      # CentOS/RHEL
```

**macOS:**
```bash
brew install ffmpeg
```

### 2. 安装 Python 依赖

```bash
cd voice_text_tts
pip install -r requirements.txt
```

## 配置 API

在 [config.py](config.py) 文件中配置 Fun-CosyVoice3-0.5B-2512 API 相关设置：

```python
# API配置
API_HOST = "0.0.0.0"  # API服务器地址
API_PORT = "50000"  # API服务器端口
API_MODE = "zero_shot"  # 使用zero_shot模式

# prompt_text配置
PROMPT_TEXT = "希望你以后能够做的比我还好呦。"  # 默认提示文本
```

确保 Fun-CosyVoice3-0.5B-2512 API 服务已启动并运行在配置的地址和端口上。

## 使用方法

启动应用：

```bash
python app.py
```

应用将在 `http://localhost:7860` 启动。

### 使用流程

1. **提供参考音频**
   - 选择"上传音频"选项卡上传音频文件
   - 或选择"录制音频"选项卡使用麦克风实时录制

2. **输入文本**
   - 在文本框中输入要合成的文字内容
   - 建议文本长度在 1000 字符以内

3. **生成语音**
   - 点击"生成语音"按钮
   - 等待生成完成，在右侧播放生成的语音

## 项目结构

```
voice_text_tts/
├── app.py              # 主应用程序
├── requirements.txt    # Python依赖包列表
└── README.md          # 项目说明文档
```

## 支持的音频格式

- **输入格式**: WAV, MP3, M4A
- **模型格式**: WAV（16kHz, 单声道, 16bit PCM）

应用会自动将上传的音频转换为模型所需的格式。

## 注意事项

- 参考音频建议使用清晰、无背景噪音的语音
- 文本长度建议在 1000 字符以内
- 首次使用需要在代码中配置API端点（对用户不可见）
- 确保 FFmpeg 已正确安装并添加到系统路径

## 技术栈

- **前端框架**: Gradio 5.0+
- **音频处理**: FFmpeg, numpy, pydub, wave
- **语言**: Python 3.13
- **语音合成**: Fun-CosyVoice3-0.5B-2512 API (zero_shot模式)

## 开发说明

### 音频转换

`AudioConverter` 类负责将各种格式的音频转换为模型所需的 WAV 格式：
- 采样率: 16kHz
- 声道: 单声道
- 编码: 16bit PCM

### API 集成

`VoiceTTSGenerator` 类实现了 Fun-CosyVoice3-0.5B-2512 API 的 zero_shot 模式调用：

- **tts_text**: 用户输入的要合成的文本
- **prompt_wav**: 用户上传的参考音频文件
- **prompt_text**: 配置的默认提示文本（可在config.py中修改）

API配置在 [config.py](config.py) 文件中完成，用户在前端页面无感知。

### 样式自定义

界面样式通过内联 CSS 定义，可以根据需要在 [app.py](app.py#L109) 中的 `custom_css` 变量中进行修改。

## 许可证

本项目仅供学习和研究使用。

## 联系方式

如有问题或建议，请通过项目 Issues 反馈。
