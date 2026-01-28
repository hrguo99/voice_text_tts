#!/bin/bash

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 镜像配置
IMAGE_NAME="voice-text-tts"
IMAGE_TAG="latest"
FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"
CONTAINER_NAME="voice-text-tts"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  Voice Text TTS 一键部署脚本${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装，请先安装 Docker${NC}"
    echo ""
    echo -e "${BLUE}安装 Docker:${NC}"
    echo -e "  Ubuntu/Debian: ${GREEN}curl -fsSL https://get.docker.com | sudo sh${NC}"
    echo -e "  然后将用户添加到 docker 组: ${GREEN}sudo usermod -aG docker \$USER${NC}"
    exit 1
fi

# 查找镜像文件
TAR_FILE="$1"

if [ -z "$TAR_FILE" ]; then
    # 自动查找当前目录下的 tar.gz 文件
    TAR_FILE=$(ls -t "$SCRIPT_DIR"/${IMAGE_NAME}-*.tar.gz 2>/dev/null | head -1)

    if [ -z "$TAR_FILE" ]; then
        echo -e "${RED}错误: 未找到镜像文件${NC}"
        echo ""
        echo -e "${BLUE}使用方法:${NC}"
        echo -e "  ${GREEN}./import-and-start.sh [镜像文件.tar.gz]${NC}"
        echo ""
        echo -e "  示例: ${GREEN}./import-and-start.sh voice-text-tts-20240101_120000.tar.gz${NC}"
        exit 1
    fi
    echo -e "${YELLOW}自动检测到镜像文件: ${TAR_FILE}${NC}"
elif [ ! -f "$TAR_FILE" ]; then
    # 尝试在脚本目录下查找
    if [ -f "$SCRIPT_DIR/$TAR_FILE" ]; then
        TAR_FILE="$SCRIPT_DIR/$TAR_FILE"
    else
        echo -e "${RED}错误: 文件 $TAR_FILE 不存在${NC}"
        exit 1
    fi
fi

echo ""

# 检查镜像是否已存在
NEED_LOAD=true
if docker images | grep -q "$IMAGE_NAME"; then
    echo -e "${YELLOW}检测到镜像已存在${NC}"
    read -p "是否重新加载镜像？(y/n) [n]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        NEED_LOAD=false
        echo -e "${GREEN}跳过镜像加载${NC}"
    fi
fi
echo ""

# 加载镜像
if [ "$NEED_LOAD" = true ]; then
    echo -e "${YELLOW}[1/4] 加载 Docker 镜像...${NC}"
    echo -e "  文件: ${GREEN}$(basename "$TAR_FILE")${NC}"
    echo -e "  大小: ${GREEN}$(du -h "$TAR_FILE" | cut -f1)${NC}"
    echo ""

    gunzip -c "$TAR_FILE" | docker load

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 镜像加载成功${NC}"
    else
        echo -e "${RED}错误: 镜像加载失败${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}[1/4] 跳过镜像加载${NC}"
fi
echo ""

# 创建必要的目录
echo -e "${YELLOW}[2/4] 创建数据目录...${NC}"
mkdir -p "$SCRIPT_DIR/presets"
mkdir -p "$SCRIPT_DIR/temp"
echo -e "${GREEN}✓ 数据目录已创建${NC}"
echo ""

# 停止并删除已存在的容器
if docker ps -a | grep -q "$CONTAINER_NAME"; then
    echo -e "${YELLOW}[3/4] 停止并删除已存在的容器...${NC}"
    docker stop "$CONTAINER_NAME" > /dev/null 2>&1
    docker rm "$CONTAINER_NAME" > /dev/null 2>&1
    echo -e "${GREEN}✓ 旧容器已清理${NC}"
else
    echo -e "${YELLOW}[3/4] 无需清理旧容器${NC}"
fi
echo ""

# 启动容器
echo -e "${YELLOW}[4/4] 启动 Docker 容器...${NC}"

# 配置环境变量
# 注意：容器内使用 host.docker.internal 访问宿主机上的服务
API_HOST="${API_HOST:-host.docker.internal}"
API_PORT="${API_PORT:-50000}"
SERVER_PORT="${SERVER_PORT:-7863}"
ASR_ENABLED="${ASR_ENABLED:-false}"

docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    --add-host=host.docker.internal:host-gateway \
    -p "${SERVER_PORT}:7863" \
    -e API_HOST="$API_HOST" \
    -e API_PORT="$API_PORT" \
    -e SERVER_NAME="0.0.0.0" \
    -e SERVER_PORT="7863" \
    -e ASR_ENABLED="$ASR_ENABLED" \
    -e ASR_BACKEND_TYPE="funasr" \
    -e MAX_TEXT_LENGTH="1000" \
    -e PRESETS_DIR="/app/presets" \
    -v "$SCRIPT_DIR/presets:/app/presets" \
    -v "$SCRIPT_DIR/temp:/app/temp" \
    "${FULL_IMAGE}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 容器启动成功${NC}"
else
    echo -e "${RED}错误: 容器启动失败${NC}"
    exit 1
fi
echo ""

# 等待服务启动
echo -e "${YELLOW}等待服务启动...${NC}"
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
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "${BLUE}容器信息:${NC}"
echo -e "  容器名称: ${GREEN}$CONTAINER_NAME${NC}"
echo -e "  镜像: ${GREEN}${FULL_IMAGE}${NC}"
echo -e "  Web 地址: ${GREEN}http://localhost:${SERVER_PORT}${NC}"
echo ""
echo -e "${BLUE}常用命令:${NC}"
echo -e "  查看日志: ${GREEN}docker logs -f $CONTAINER_NAME${NC}"
echo -e "  停止容器: ${GREEN}./stop.sh${NC} 或 ${GREEN}docker stop $CONTAINER_NAME${NC}"
echo -e "  重启容器: ${GREEN}docker restart $CONTAINER_NAME${NC}"
echo ""
echo -e "${BLUE}环境变量配置:${NC}"
echo -e "  可以在运行前设置以下环境变量:"
echo -e "  ${GREEN}API_HOST${NC}    - TTS API 主机地址 (默认: 127.0.0.1)"
echo -e "  ${GREEN}API_PORT${NC}    - TTS API 端口 (默认: 50000)"
echo -e "  ${GREEN}SERVER_PORT${NC} - Web 服务端口 (默认: 7863)"
echo -e "  ${GREEN}ASR_ENABLED${NC} - 启用语音识别 (默认: false)"
echo ""
echo -e "  示例: ${GREEN}API_HOST=192.168.1.100 ./import-and-start.sh${NC}"
echo ""
