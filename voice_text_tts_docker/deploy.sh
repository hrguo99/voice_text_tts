#!/bin/bash
# ===========================================
# Voice Text TTS Docker 镜像一键部署脚本
# ===========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_blue() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_step() {
    echo -e "${BLUE}===>${NC} $1"
}

# 检查 Docker 是否安装
check_docker() {
    print_step "检查 Docker 环境..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装！"
        echo ""
        echo "请先安装 Docker："
        echo "  Ubuntu/Debian: curl -fsSL https://get.docker.com | sh"
        echo "  CentOS/RHEL:   yum install docker"
        exit 1
    fi

    # 检查 Docker 是否运行
    if ! docker info &> /dev/null; then
        print_error "Docker 服务未运行！"
        echo ""
        echo "请启动 Docker 服务："
        echo "  sudo systemctl start docker"
        echo "  或"
        echo "  sudo service docker start"
        exit 1
    fi

    print_info "Docker 环境检查通过"
}

# 检查参数
check_arguments() {
    if [ -z "$1" ]; then
        print_error "缺少镜像文件参数！"
        echo ""
        echo "用法: $0 <镜像文件.tar.gz>"
        echo ""
        echo "示例:"
        echo "  $0 voice-text-tts-docker-image-20260123_181353.tar.gz"
        echo ""
        exit 1
    fi

    IMAGE_FILE="$1"

    if [ ! -f "$IMAGE_FILE" ]; then
        print_error "镜像文件不存在: $IMAGE_FILE"
        exit 1
    fi

    print_info "镜像文件: $IMAGE_FILE"
}

# 导入镜像
import_image() {
    print_step "导入 Docker 镜像..."

    # 检查镜像是否已存在
    if docker images | grep -q "voice-text-tts"; then
        print_warn "镜像 voice-text-tts:latest 已存在"
        echo ""
        read -p "是否删除旧镜像并重新导入？(y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "删除旧镜像..."
            docker rmi voice-text-tts:latest || true
        else
            print_info "使用现有镜像"
            return
        fi
    fi

    # 导入镜像
    print_info "正在导入镜像（这可能需要 5-10 分钟）..."
    gunzip -c "$IMAGE_FILE" | docker load

    print_info "镜像导入完成！"
}

# 创建配置文件
create_config() {
    print_step "创建配置文件..."

    # 检查 .env 文件是否存在
    if [ -f ".env" ]; then
        print_warn ".env 文件已存在"
        read -p "是否使用现有配置？(Y/n): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            print_info "使用现有配置文件"
            return
        fi
    fi

    # 复制示例配置
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_info "已创建 .env 配置文件"
    else
        # 创建默认配置
        cat > .env << 'EOF'
# ===========================================
# Voice Text TTS Docker 环境变量配置
# ===========================================

# API 配置
API_HOST=host.docker.internal
API_PORT=50000
API_MODE=zero_shot

# Prompt 配置
PROMPT_TEXT=You are a helpful assistant.<|endofprompt|>

# 服务器配置
SERVER_PORT=7862

# Gradio Share 模式
GRADIO_SHARE=true

# 文本限制
MAX_TEXT_LENGTH=1000

# ASR 配置
ASR_ENABLED=false
ASR_BACKEND_TYPE=funasr

# ASR FunASR 配置
ASR_FUNASR_URI=ws://localhost:10095/ws
ASR_FUNASR_MODE=2pass-offline
ASR_FUNASR_CHUNK_SIZE=[5, 10, 5]
ASR_FUNASR_CHUNK_INTERVAL=10
ASR_FUNASR_ENCODER_CHUNK_LOOK_BACK=4
ASR_FUNASR_DECODER_CHUNK_LOOK_BACK=0
ASR_FUNASR_HOTWORDS={}
ASR_FUNASR_USE_ITN=true
EOF
        print_info "已创建默认 .env 配置文件"
    fi

    print_warn "请根据需要修改 .env 配置文件"
    echo ""
    read -p "是否现在编辑配置文件？(y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-vi} .env
    fi
}

# 启动容器
start_container() {
    print_step "启动容器..."

    # 提取端口号
    SERVER_PORT=$(grep -E '^SERVER_PORT=' .env 2>/dev/null | cut -d'=' -f2)
    SERVER_PORT=${SERVER_PORT:-7862}

    # 检查端口是否被占用
    if netstat -tuln 2>/dev/null | grep -q ":${SERVER_PORT} "; then
        print_warn "端口 ${SERVER_PORT} 已被占用"
        echo ""
        read -p "是否停止并删除现有容器？(y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker stop voice_text_tts_app 2>/dev/null || true
            docker rm voice_text_tts_app 2>/dev/null || true
        else
            print_error "端口冲突，无法启动容器"
            exit 1
        fi
    fi

    # 停止并删除旧容器
    if docker ps -a | grep -q "voice_text_tts_app"; then
        print_info "停止并删除旧容器..."
        docker stop voice_text_tts_app 2>/dev/null || true
        docker rm voice_text_tts_app 2>/dev/null || true
    fi

    # 启动新容器
    print_info "启动容器..."
    docker run -d \
        --name voice_text_tts_app \
        -p ${SERVER_PORT}:7862 \
        --env-file .env \
        --add-host=host.docker.internal:host-gateway \
        --restart unless-stopped \
        voice-text-tts:latest

    print_info "容器启动成功！"
}

# 等待服务就绪
wait_for_service() {
    print_step "等待服务启动..."

    SERVER_PORT=$(grep -E '^SERVER_PORT=' .env 2>/dev/null | cut -d'=' -f2)
    SERVER_PORT=${SERVER_PORT:-7862}

    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:${SERVER_PORT} > /dev/null 2>&1; then
            print_info "服务已就绪！"
            return 0
        fi

        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done

    echo ""
    print_warn "服务启动超时，但容器正在运行"
}

# 显示结果
show_result() {
    SERVER_PORT=$(grep -E '^SERVER_PORT=' .env 2>/dev/null | cut -d'=' -f2)
    SERVER_PORT=${SERVER_PORT:-7862}

    echo ""
    print_blue "=========================================="
    print_info "部署完成！"
    print_blue "=========================================="
    echo ""
    print_info "访问地址:"
    echo "  本地访问: http://localhost:${SERVER_PORT}"
    echo "  局域网: http://$(hostname -I | awk '{print $1}'):${SERVER_PORT}"
    echo ""
    print_info "容器管理:"
    echo "  查看状态: docker ps | grep voice_text_tts_app"
    echo "  查看日志: docker logs -f voice_text_tts_app"
    echo "  停止容器: docker stop voice_text_tts_app"
    echo "  重启容器: docker restart voice_text_tts_app"
    echo ""
    print_info "配置文件: .env"
    print_info "修改配置后需要重启容器: docker restart voice_text_tts_app"
    echo ""
    print_warn "注意事项:"
    echo "  1. 确保宿主机 TTS API 服务运行在 50000 端口"
    echo "  2. 容器通过 host.docker.internal 访问宿主机 API"
    echo "  3. 如需修改配置，编辑 .env 后重启容器"
    echo ""
}

# 主函数
main() {
    print_blue "=========================================="
    print_info "Voice Text TTS Docker 一键部署工具"
    print_blue "=========================================="
    echo ""

    check_docker
    echo ""
    check_arguments "$@"
    echo ""
    import_image
    echo ""
    create_config
    echo ""
    start_container
    echo ""
    wait_for_service
    echo ""
    show_result
}

# 执行主函数
main "$@"
