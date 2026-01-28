#!/bin/bash

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

CONTAINER_NAME="voice-text-tts"

echo -e "${YELLOW}查看 Voice Text TTS 容器日志...${NC}"
echo -e "${GREEN}按 Ctrl+C 退出${NC}"
echo ""

if docker ps | grep -q "$CONTAINER_NAME"; then
    docker logs -f --tail 100 "$CONTAINER_NAME"
else
    echo -e "${YELLOW}容器未运行${NC}"
    echo ""
    echo -e "${YELLOW}查看历史日志:${NC}"
    docker logs --tail 100 "$CONTAINER_NAME"
fi
