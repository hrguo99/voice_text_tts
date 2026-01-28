#!/bin/bash
# Voice Text TTS - 完全重新构建脚本

set -e

echo "======================================"
echo "Voice Text TTS - 完全重新构建"
echo "======================================"

# 获取脚本所在目录并切换到该目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装"
    exit 1
fi

# 检测 Docker Compose 命令（支持 V1 和 V2）
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "⚠️  警告: Docker Compose 未找到，将使用 docker compose 命令..."
    DOCKER_COMPOSE="docker compose"
fi

echo "🔧 使用: $DOCKER_COMPOSE"
echo ""

echo "🧹 彻底清理旧资源..."
echo ""

# 停止并删除所有相关容器
echo "1️⃣  停止并删除容器..."
$DOCKER_COMPOSE down 2>/dev/null || true
docker ps -a | grep voice_text_tts_app | awk '{print $1}' | xargs -r docker rm -f 2>/dev/null || true

# 删除旧镜像
echo "2️⃣  删除旧镜像..."
if docker images -q voice-text-tts:latest | grep -q .; then
    docker rmi voice-text-tts:latest -f 2>/dev/null || true
    echo "   ✅ 已删除旧镜像"
else
    echo "   ℹ️  没有旧镜像"
fi

# 清理悬空镜像
echo "3️⃣  清理悬空镜像..."
docker image prune -f >/dev/null 2>&1 || true

# 清理构建缓存
echo "4️⃣  清理构建缓存..."
docker builder prune -f >/dev/null 2>&1 || true

echo ""
echo "📋 重新复制源代码..."
if [ -d "voice_text_tts" ]; then
    rm -rf voice_text_tts
fi
./copy-source.sh

echo ""
echo "🔨 开始全新构建..."
echo "📂 构建上下文: $(pwd)"
echo "📄 Dockerfile: Dockerfile"
echo ""

# 使用 --no-cache 强制重新构建所有层
docker build --no-cache -t voice-text-tts:latest .

echo ""
echo "✅ 镜像构建成功！"
echo ""
echo "镜像信息:"
docker images voice-text-tts:latest
echo ""
echo "是否立即启动容器？"
read -p "启动容器？(y/N): " start_now
if [[ $start_now =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 启动容器..."
    $DOCKER_COMPOSE up -d
    echo ""
    echo "✅ 容器已启动"
    echo ""
    echo "访问地址:"
    echo "  本地: http://localhost:7863"
    echo "  局域网: http://$(hostname -I | awk '{print $1}'):7863"
    echo ""
    echo "查看日志: $DOCKER_COMPOSE logs -f"
fi
