FROM python:3.12-slim

LABEL maintainer="guohaoran"
LABEL description="Voice Text TTS Application with Gradio Interface"

# 设置工作目录
WORKDIR /app

# 配置 pip 使用国内镜像源，并设置不缓存
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# 安装系统依赖并清理（在同一层完成）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 先复制依赖文件，利用 Docker 缓存
COPY voice_text_tts/requirements.txt /app/

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    --default-timeout=1000 \
    --retries 5 \
    -r requirements.txt

# 复制应用代码
COPY voice_text_tts/ /app/

# 清理不需要的文件（文档、示例等）
RUN find /app -type f -name '*.md' -delete && \
    find /app -type f -name '*.txt' ! -name 'requirements.txt' -delete && \
    find /app -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true && \
    find /app -type f -name '*.pyc' -delete && \
    find /app -type f -name '*.pyo' -delete

# 移除编译工具（减小镜像大小）
RUN apt-get remove -y gcc g++ && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* /root/.cache

# 暴露端口
EXPOSE 7863

# 设置环境变量（可通过 docker run -e 覆盖）
ENV API_HOST=host.docker.internal \
    API_PORT=50000 \
    API_MODE=zero_shot \
    PROMPT_TEXT="You are a helpful assistant.<|endofprompt|>" \
    SERVER_NAME=0.0.0.0 \
    SERVER_PORT=7863 \
    MAX_TEXT_LENGTH=1000 \
    ASR_ENABLED=false \
    ASR_BACKEND_TYPE=funasr \
    GRADIO_SHARE=true \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 创建 Docker 环境标识文件（用于应用检测）
RUN touch /.dockerenv

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.connect(('127.0.0.1', 7863)); s.close()" || exit 1

# 启动应用
CMD ["python", "-u", "app.py"]
