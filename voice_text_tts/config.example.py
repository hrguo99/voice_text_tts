"""
API配置文件模板
Fun-CosyVoice3-0.5B-2512 模型配置
复制此文件为 config.py 并根据需要修改配置
"""
import os

# API配置
API_HOST = os.getenv("API_HOST", "127.0.0.1")  # API服务器地址
API_PORT = os.getenv("API_PORT", "50000")  # API服务器端口
API_MODE = os.getenv("API_MODE", "zero_shot")  # 使用zero_shot模式

# prompt_text配置
PROMPT_TEXT = os.getenv("PROMPT_TEXT", "You are a helpful assistant.<|endofprompt|>")  # 默认提示文本

# 音频配置
AUDIO_SAMPLE_RATE = 16000  # 采样率 16kHz
AUDIO_CHANNELS = 1  # 单声道

# 应用配置
SERVER_NAME = os.getenv("SERVER_NAME", "127.0.0.1")  # 服务器地址
SERVER_PORT = int(os.getenv("SERVER_PORT", "7863"))  # 服务器端口

# 文本限制
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "1000"))  # 最大文本长度

# 预设配置
PRESETS_DIR = os.getenv("PRESETS_DIR")  # 预设保存路径，None表示使用系统临时目录，可设置为 "./presets" 或 "/path/to/presets"

# ASR配置
ASR_ENABLED = os.getenv("ASR_ENABLED", "false").lower() == "true"
ASR_BACKEND_TYPE = os.getenv("ASR_BACKEND_TYPE", "funasr")
ASR_BACKEND_CONFIG = {
    "funasr": {
        "uri": "ws://localhost:10095/ws",
        "mode": "2pass-offline",
        "chunk_size": [5, 10, 5],
        "chunk_interval": 10,
        "encoder_chunk_look_back": 4,
        "decoder_chunk_look_back": 0,
        "hotwords": "{}",
        "use_itn": True,
    },
    "websocket": {
        "uri": "ws://localhost:10095/ws",
        "init_message": {"is_speaking": True},
        "end_message": {"is_speaking": False},
    }
}
