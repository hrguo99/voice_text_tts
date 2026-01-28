#!/bin/bash

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

CONTAINER_NAME="voice-text-tts"
IMAGE_NAME="voice-text-tts"

echo -e "${YELLOW}======================================${NC}"
echo -e "${YELLOW}  Voice Text TTS Docker 清理脚本${NC}"
echo -e "${YELLOW}======================================${NC}"
echo ""

# 停止并删除容器
if docker ps -a | grep -q "$CONTAINER_NAME"; then
    echo -e "${YELLOW}[1/3] 停止并删除容器...${NC}"
    docker stop "$CONTAINER_NAME" > /dev/null 2>&1
    docker rm "$CONTAINER_NAME" > /dev/null 2>&1
    echo -e "${GREEN}✓ 容器已删除${NC}"
else
    echo -e "${YELLOW}[1/3] 无容器需要删除${NC}"
fi
echo ""

# 删除镜像
if docker images | grep -q "$IMAGE_NAME"; then
    echo -e "${YELLOW}[2/3] 删除 Docker 镜像...${NC}"
    read -p "是否删除镜像 ${IMAGE_NAME}? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker rmi "${IMAGE_NAME}:latest" > /dev/null 2>&1
        echo -e "${GREEN}✓ 镜像已删除${NC}"
    else
        echo -e "${YELLOW}跳过镜像删除${NC}"
    fi
else
    echo -e "${YELLOW}[2/3] 无镜像需要删除${NC}"
fi
echo ""

# 清理数据目录
echo -e "${YELLOW}[3/3] 清理数据目录...${NC}"
read -p "是否删除预设和临时文件? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$(dirname "$0")/presets"/*
    rm -rf "$(dirname "$0")/temp"/*
    echo -e "${GREEN}✓ 数据已清理${NC}"
else
    echo -e "${YELLOW}跳过数据清理${NC}"
fi
echo ""

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  清理完成！${NC}"
echo -e "${GREEN}======================================${NC}"
