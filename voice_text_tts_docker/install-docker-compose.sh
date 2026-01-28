#!/bin/bash
# Docker Compose 一键安装脚本

set -e

echo "======================================"
echo "Docker Compose 一键安装"
echo "======================================"
echo ""

# 检查是否为 root
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  此脚本需要 sudo 权限"
    sudo "$0" "$@"
    exit $?
fi

echo "📦 正在安装 Docker Compose V2 (推荐版本)..."
echo ""

# 更新包列表
apt-get update

# 安装 Docker Compose V2
apt-get install -y docker-compose-plugin

echo ""
echo "✅ Docker Compose V2 安装完成！"
echo ""

# 验证安装
if docker compose version &> /dev/null; then
    echo "🔍 验证安装:"
    docker compose version
    echo ""
    echo "======================================"
    echo "✅ 安装成功！"
    echo "======================================"
    echo ""
    echo "现在可以运行: ./start.sh"
else
    echo "❌ 安装验证失败"
    exit 1
fi
