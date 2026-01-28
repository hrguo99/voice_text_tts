#!/bin/bash
# Voice Text TTS - Docker 快速启动脚本

set -e

echo "======================================"
echo "Voice Text TTS - Docker 启动脚本"
echo "======================================"

# 获取脚本所在目录并切换到该目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检测 Docker Compose 命令（支持 V1 和 V2）
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "❌ 错误: Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

echo "🔧 使用: $DOCKER_COMPOSE"
echo ""

# 检查 voice_text_tts 目录是否存在
if [ ! -d "voice_text_tts" ]; then
    echo "⚠️  voice_text_tts 目录不存在"
    echo "📋 正在复制源代码..."
    ./copy-source.sh
fi

# 创建 .env 文件（如果不存在）
if [ ! -f ".env" ]; then
    echo "📝 创建 .env 文件..."
    cp .env.example .env
    echo "✅ .env 文件已创建，请根据需要修改配置"
fi

# 询问是否重新构建
read -p "是否重新构建镜像？(y/N): " rebuild
if [[ $rebuild =~ ^[Yy]$ ]]; then
    echo ""
    echo "🧹 清理旧镜像..."
    if docker images -q voice-text-tts:latest | grep -q .; then
        echo "🗑️  删除旧镜像: voice-text-tts:latest"
        # 停止并删除使用该镜像的容器
        $DOCKER_COMPOSE down 2>/dev/null || true
        # 删除旧镜像
        docker rmi voice-text-tts:latest 2>/dev/null || echo "   (旧镜像正在使用中，将强制重新构建)"
        # 清理悬空镜像
        docker image prune -f >/dev/null 2>&1 || true
    else
        echo "✅ 没有旧镜像需要删除"
    fi
    echo ""
    echo "🔨 构建镜像..."
    $DOCKER_COMPOSE build --no-cache
else
    echo "⚡  使用现有镜像..."
fi

# 停止旧容器
echo "🛑 停止旧容器..."
$DOCKER_COMPOSE down 2>/dev/null || true

# 启动服务
echo "🚀 启动服务..."
$DOCKER_COMPOSE up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查容器状态
if docker ps | grep -q voice_text_tts_app; then
    echo "✅ 服务启动成功！"
    echo ""
    echo "======================================"
    echo "访问地址:"
    echo "  本地: http://localhost:7863"
    echo "  局域网: http://$(hostname -I | awk '{print $1}'):7863"
    echo "======================================"
    echo ""
    echo "查看日志: $DOCKER_COMPOSE logs -f"
    echo "停止服务: $DOCKER_COMPOSE down"
else
    echo "❌ 服务启动失败，请查看日志:"
    echo "   $DOCKER_COMPOSE logs"
    exit 1
fi
