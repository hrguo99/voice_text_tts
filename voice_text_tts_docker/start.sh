#!/bin/bash

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  Voice Text TTS Docker 启动脚本${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装，请先安装 Docker${NC}"
    exit 1
fi

# 检查镜像是否存在
IMAGE_NAME="voice-text-tts"
IMAGE_TAG="latest"

if ! docker images | grep -q "$IMAGE_NAME"; then
    echo -e "${YELLOW}警告: 镜像 ${IMAGE_NAME}:${IMAGE_TAG} 不存在${NC}"
    echo -e "${YELLOW}请先运行构建脚本: ./build.sh${NC}"
    echo ""
    read -p "是否现在构建镜像？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        "$SCRIPT_DIR/build.sh"
        if [ $? -ne 0 ]; then
            echo -e "${RED}构建失败，退出${NC}"
            exit 1
        fi
    else
        echo -e "${RED}退出${NC}"
        exit 1
    fi
fi

# 创建必要的目录
echo -e "${YELLOW}[1/4] 创建数据目录...${NC}"
mkdir -p "$SCRIPT_DIR/presets"
mkdir -p "$SCRIPT_DIR/temp"
echo -e "${GREEN}✓ 数据目录已创建${NC}"
echo ""

# 停止并删除已存在的容器
CONTAINER_NAME="voice-text-tts"
if docker ps -a | grep -q "$CONTAINER_NAME"; then
    echo -e "${YELLOW}[2/4] 停止并删除已存在的容器...${NC}"
    docker stop "$CONTAINER_NAME" > /dev/null 2>&1
    docker rm "$CONTAINER_NAME" > /dev/null 2>&1
    echo -e "${GREEN}✓ 旧容器已清理${NC}"
else
    echo -e "${YELLOW}[2/4] 无需清理旧容器${NC}"
fi
echo ""

# 启动容器
echo -e "${YELLOW}[3/4] 启动 Docker 容器...${NC}"

# 配置环境变量
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-50000}"
SERVER_PORT="${SERVER_PORT:-7863}"
ASR_ENABLED="${ASR_ENABLED:-false}"

docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    -p "${SERVER_PORT}:7863" \
    -e API_HOST="$API_HOST" \
    -e API_PORT="$API_PORT" \
    -e SERVER_NAME="0.0.0.0" \
    -e SERVER_PORT="7863" \
    -e ASR_ENABLED="$ASR_ENABLED" \
    -e ASR_BACKEND_TYPE="funasr" \
    -e MAX_TEXT_LENGTH="1000" \
    -v "$SCRIPT_DIR/presets:/app/presets" \
    -v "$SCRIPT_DIR/temp:/app/temp" \
    "${IMAGE_NAME}:${IMAGE_TAG}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 容器启动成功${NC}"
else
    echo -e "${RED}错误: 容器启动失败${NC}"
    exit 1
fi
echo ""

# 等待服务启动
echo -e "${YELLOW}[4/4] 等待服务启动...${NC}"
sleep 5

# 检查容器状态
if docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${GREEN}✓ 服务运行正常${NC}"
else
    echo -e "${RED}错误: 容器未正常运行${NC}"
    echo -e "${YELLOW}查看日志:${NC}"
    docker logs "$CONTAINER_NAME"
    exit 1
fi
echo ""

# 完成
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  启动完成！${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "${BLUE}容器信息:${NC}"
echo -e "  容器名称: ${GREEN}$CONTAINER_NAME${NC}"
echo -e "  镜像: ${GREEN}${IMAGE_NAME}:${IMAGE_TAG}${NC}"
echo -e "  Web 地址: ${GREEN}http://localhost:${SERVER_PORT}${NC}"
echo ""
echo -e "${BLUE}常用命令:${NC}"
echo -e "  查看日志: ${GREEN}docker logs -f $CONTAINER_NAME${NC}"
echo -e "  停止容器: ${GREEN}docker stop $CONTAINER_NAME${NC}"
echo -e "  重启容器: ${GREEN}docker restart $CONTAINER_NAME${NC}"
echo -e "  删除容器: ${GREEN}docker rm -f $CONTAINER_NAME${NC}"
echo ""
echo -e "${BLUE}配置说明:${NC}"
echo -e "  预设目录: ${GREEN}$SCRIPT_DIR/presets${NC}"
echo -e "  临时目录: ${GREEN}$SCRIPT_DIR/temp${NC}"
echo ""
