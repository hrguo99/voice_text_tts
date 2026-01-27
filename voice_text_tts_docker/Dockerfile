FROM python:3.12-slim

LABEL maintainer="guohaoran"
LABEL description="Voice Text TTS Application with Gradio Interface"

# 设置工作目录
WORKDIR /app

# 配置 pip 使用国内镜像源（清华大学）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY voice_text_tts/ /app/

# 升级 pip 并安装 Python 依赖（增加超时和重试配置）
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
    --default-timeout=1000 \
    --retries 5 \
    -r requirements.txt

# 暴露端口
EXPOSE 7862

# 设置环境变量（可通过 docker run -e 覆盖）
ENV API_HOST=host.docker.internal
ENV API_PORT=50000
ENV API_MODE=zero_shot
ENV PROMPT_TEXT="You are a helpful assistant.<|endofprompt|>"
ENV SERVER_NAME=0.0.0.0
ENV SERVER_PORT=7862
ENV MAX_TEXT_LENGTH=1000
ENV ASR_ENABLED=false
ENV ASR_BACKEND_TYPE=funasr
# Gradio share 模式（Docker 环境中默认启用以避免 localhost 检查问题）
ENV GRADIO_SHARE=true

# 创建 Docker 环境标识文件（用于应用检测）
RUN touch /.dockerenv

# 健康检查（增加启动等待时间并使用更简单的检查方式）
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.connect(('127.0.0.1', 7862)); s.close()" || exit 1

# 启动应用
CMD ["python", "app.py"]
