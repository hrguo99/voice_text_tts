#!/bin/bash

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

CONTAINER_NAME="voice-text-tts"

echo -e "${YELLOW}停止 Voice Text TTS 容器...${NC}"

if docker ps | grep -q "$CONTAINER_NAME"; then
    docker stop "$CONTAINER_NAME"
    echo -e "${GREEN}✓ 容器已停止${NC}"
else
    echo -e "${YELLOW}容器未运行${NC}"
fi
