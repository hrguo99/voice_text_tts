#!/bin/bash
# Voice Text TTS - Docker 停止和清理脚本

set -e

echo "======================================"
echo "Voice Text TTS - 停止和清理"
echo "======================================"

# 获取脚本所在目录并切换到该目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检测 Docker Compose 命令（支持 V1 和 V2）
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "⚠️  警告: Docker Compose 未找到，尝试使用 docker 命令..."
    DOCKER_COMPOSE="docker compose"
fi

# 停止并删除容器
echo "🛑 停止容器..."
$DOCKER_COMPOSE down 2>/dev/null || true

# 询问是否删除镜像
read -p "是否删除 Docker 镜像？(y/N): " remove_image
if [[ $remove_image =~ ^[Yy]$ ]]; then
    echo "🗑️  删除镜像..."
    docker rmi voice-text-tts:latest 2>/dev/null || true
    echo "✅ 镜像已删除"
fi

# 询问是否清理卷
read -p "是否清理数据卷？(y/N): " remove_volumes
if [[ $remove_volumes =~ ^[Yy]$ ]]; then
    echo "🗑️  清理卷..."
    $DOCKER_COMPOSE down -v 2>/dev/null || true
    echo "✅ 卷已清理"
fi

# 询问是否删除复制的源代码
read -p "是否删除复制的源代码？(y/N): " remove_source
if [[ $remove_source =~ ^[Yy]$ ]]; then
    echo "🗑️  删除源代码..."
    rm -rf voice_text_tts
    echo "✅ 源代码已删除"
fi

echo "✅ 清理完成"
