# 多阶段构建 - 第一阶段：依赖构建
FROM python:3.13-slim AS builder

# 设置工作目录
WORKDIR /build

# 安装构建依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# 多阶段构建 - 第二阶段：运行环境
FROM python:3.13-slim

# 设置元数据
LABEL maintainer="voice_text_tts"
LABEL description="Voice Text TTS Docker Image with Python 3.13"

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# 设置工作目录
WORKDIR /app

# 安装运行时依赖（只安装 FFmpeg）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制项目文件
COPY app.py .
COPY app_tabs.py .
COPY asr_backends.py .
COPY asr_client.py .
COPY config.py .
COPY requirements.txt .

# 创建必要的目录
RUN mkdir -p /app/presets /app/temp

# 暴露端口
EXPOSE 7863

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import socket; s = socket.socket(); s.connect(('127.0.0.1', 7863)); s.close()" || exit 1

# 启动应用
CMD ["python", "app.py"]
