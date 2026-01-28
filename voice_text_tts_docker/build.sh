#!/bin/bash

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  Voice Text TTS Docker 构建脚本${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装，请先安装 Docker${NC}"
    exit 1
fi

# 检查必要文件是否存在
echo -e "${YELLOW}[1/5] 检查项目文件...${NC}"
required_files=("app.py" "asr_backends.py" "asr_client.py" "config.py" "requirements.txt")
for file in "${required_files[@]}"; do
    if [ ! -f "$PROJECT_DIR/voice_text_tts/$file" ]; then
        echo -e "${RED}错误: 找不到必需文件 voice_text_tts/$file${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ 所有必需文件存在${NC}"
echo ""

# 复制项目文件到构建目录
echo -e "${YELLOW}[2/5] 准备构建环境...${NC}"
BUILD_DIR="$SCRIPT_DIR/build"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

cp "$PROJECT_DIR/voice_text_tts/app.py" "$BUILD_DIR/"
cp "$PROJECT_DIR/voice_text_tts/app_tabs.py" "$BUILD_DIR/" 2>/dev/null || true
cp "$PROJECT_DIR/voice_text_tts/asr_backends.py" "$BUILD_DIR/"
cp "$PROJECT_DIR/voice_text_tts/asr_client.py" "$BUILD_DIR/"
cp "$PROJECT_DIR/voice_text_tts/config.py" "$BUILD_DIR/"
cp "$PROJECT_DIR/voice_text_tts/requirements.txt" "$BUILD_DIR/"
cp "$SCRIPT_DIR/Dockerfile" "$BUILD_DIR/"
cp "$SCRIPT_DIR/.dockerignore" "$BUILD_DIR/"

echo -e "${GREEN}✓ 构建环境准备完成${NC}"
echo ""

# 构建 Docker 镜像
echo -e "${YELLOW}[3/5] 开始构建 Docker 镜像...${NC}"
cd "$BUILD_DIR"

IMAGE_NAME="voice-text-tts"
IMAGE_TAG="latest"

if docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .; then
    echo -e "${GREEN}✓ Docker 镜像构建成功${NC}"
else
    echo -e "${RED}错误: Docker 镜像构建失败${NC}"
    exit 1
fi
echo ""

# 显示镜像信息
echo -e "${YELLOW}[4/5] 镜像信息:${NC}"
docker images | grep "$IMAGE_NAME"
echo ""

# 清理构建目录（可选）
echo -e "${YELLOW}[5/5] 清理构建目录...${NC}"
cd "$SCRIPT_DIR"
rm -rf "$BUILD_DIR"
echo -e "${GREEN}✓ 清理完成${NC}"
echo ""

# 完成
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  构建完成！${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "${YELLOW}下一步操作:${NC}"
echo -e "  1. 使用以下命令启动容器:"
echo -e "     ${GREEN}cd $SCRIPT_DIR && ./start.sh${NC}"
echo ""
echo -e "  2. 或使用 docker-compose:"
echo -e "     ${GREEN}cd $SCRIPT_DIR && docker-compose up -d${NC}"
echo ""
echo -e "  3. 访问 Web 界面:"
echo -e "     ${GREEN}http://localhost:7863${NC}"
echo ""
