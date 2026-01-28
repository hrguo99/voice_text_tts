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

# 输出文件名（带时间戳）
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="${SCRIPT_DIR}/${IMAGE_NAME}-${TIMESTAMP}.tar.gz"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  Voice Text TTS 镜像导出脚本${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装${NC}"
    exit 1
fi

# 检查镜像是否存在
if ! docker images | grep -q "$IMAGE_NAME"; then
    echo -e "${RED}错误: 镜像 ${FULL_IMAGE} 不存在${NC}"
    echo -e "${YELLOW}请先运行 ./build.sh 构建镜像${NC}"
    exit 1
fi

# 显示镜像信息
echo -e "${BLUE}镜像信息:${NC}"
docker images "$FULL_IMAGE" --format "  大小: {{.Size}}\n  创建时间: {{.CreatedSince}}"
echo ""

# 导出镜像
echo -e "${YELLOW}[1/2] 导出镜像到 tar 文件...${NC}"
echo -e "  输出文件: ${GREEN}${OUTPUT_FILE}${NC}"
echo ""

docker save "$FULL_IMAGE" | gzip > "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 镜像导出成功${NC}"
else
    echo -e "${RED}错误: 镜像导出失败${NC}"
    exit 1
fi
echo ""

# 显示文件信息
echo -e "${YELLOW}[2/2] 导出完成${NC}"
FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
echo ""

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  导出完成！${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "${BLUE}文件信息:${NC}"
echo -e "  文件路径: ${GREEN}${OUTPUT_FILE}${NC}"
echo -e "  文件大小: ${GREEN}${FILE_SIZE}${NC}"
echo ""
echo -e "${BLUE}使用方法:${NC}"
echo -e "  1. 将以下文件复制到目标机器:"
echo -e "     - ${GREEN}${OUTPUT_FILE}${NC}"
echo -e "     - ${GREEN}${SCRIPT_DIR}/import-and-start.sh${NC}"
echo ""
echo -e "  2. 在目标机器上运行:"
echo -e "     ${GREEN}./import-and-start.sh $(basename "$OUTPUT_FILE")${NC}"
echo ""
