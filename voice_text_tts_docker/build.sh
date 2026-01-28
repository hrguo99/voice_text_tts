#!/bin/bash
# Voice Text TTS - Docker 构建脚本

set -e

echo "======================================"
echo "Voice Text TTS - Docker 构建脚本"
echo "======================================"

# 获取脚本所在目录并切换到该目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装"
    exit 1
fi

# 检查 voice_text_tts 目录是否存在
if [ ! -d "voice_text_tts" ]; then
    echo "⚠️  voice_text_tts 目录不存在"
    echo "📋 正在复制源代码..."
    ./copy-source.sh
fi

# 检查 Dockerfile 是否存在
if [ ! -f "Dockerfile" ]; then
    echo "❌ 错误: 找不到 Dockerfile"
    echo "   当前目录: $(pwd)"
    exit 1
fi

# 删除旧镜像（如果存在）
echo "🧹 清理旧镜像..."
if docker images -q voice-text-tts:latest | grep -q .; then
    echo "🗑️  删除旧镜像: voice-text-tts:latest"
    docker rmi voice-text-tts:latest 2>/dev/null || echo "   (旧镜像已被使用，将在重新构建后自动清理)"
    # 清理悬空镜像
    docker image prune -f >/dev/null 2>&1 || true
else
    echo "✅ 没有旧镜像需要删除"
fi
echo ""

# 构建镜像（使用当前目录作为构建上下文）
echo "🔨 开始构建镜像..."
echo "📂 构建上下文: $(pwd)"
echo "📄 Dockerfile: Dockerfile"
echo ""

docker build -t voice-text-tts:latest .

echo ""
echo "✅ 镜像构建成功！"
echo ""
echo "镜像信息:"
docker images voice-text-tts:latest
echo ""
echo "运行容器:"
echo "  docker run -d --name voice_text_tts_app -p 7863:7863 voice-text-tts:latest"

