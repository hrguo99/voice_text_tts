#!/bin/bash
# 检测 Docker Compose 版本

echo "======================================"
echo "Docker 环境检测"
echo "======================================"
echo ""

# 检查 Docker
if command -v docker &> /dev/null; then
    echo "✅ Docker 已安装"
    docker --version
else
    echo "❌ Docker 未安装"
    exit 1
fi

echo ""

# 检查 Docker Compose V2
if docker compose version &> /dev/null; then
    echo "✅ Docker Compose V2 已检测到"
    docker compose version
    COMPOSE_CMD="docker compose"
# 检查 Docker Compose V1
elif command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose V1 已检测到"
    docker-compose --version
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose 未安装"
    exit 1
fi

echo ""
echo "======================================"
echo "推荐命令: $COMPOSE_CMD"
echo "======================================"
echo ""
echo "示例命令:"
echo "  $COMPOSE_CMD up -d"
echo "  $COMPOSE_CMD down"
echo "  $COMPOSE_CMD logs -f"
