#!/bin/bash
# ===========================================
# Voice Text TTS Docker 镜像构建脚本
# ===========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    print_info "Docker 环境检查通过"
}

# 检查 .env 文件
check_env_file() {
    if [ ! -f .env ]; then
        print_warn ".env 文件不存在，从 .env.example 复制..."
        if [ -f .env.example ]; then
            cp .env.example .env
            print_info ".env 文件已创建，请根据需要修改配置"
        else
            print_error ".env.example 文件不存在"
            exit 1
        fi
    else
        print_info ".env 文件已存在"
    fi
}

# 构建镜像
build_image() {
    print_info "开始构建 Docker 镜像..."
    echo ""

    # 读取镜像名称和标签
    IMAGE_NAME="voice-text-tts"
    IMAGE_TAG="latest"

    # 构建镜像
    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

    echo ""
    print_info "=========================================="
    print_info "Docker 镜像构建完成！"
    print_info "=========================================="
    print_info "镜像名称: ${IMAGE_NAME}:${IMAGE_TAG}"
    print_info ""
    print_info "查看镜像: docker images | grep voice-text-tts"
    print_info "运行服务: ./run.sh"
    print_info "=========================================="
}

# 显示帮助
show_help() {
    echo "Voice Text TTS Docker 镜像构建脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --no-cache    不使用缓存构建"
    echo "  --pull        总是尝试拉取基础镜像的最新版本"
    echo "  -h, --help    显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0              # 构建镜像"
    echo "  $0 --no-cache   # 不使用缓存构建"
}

# 主函数
main() {
    local BUILD_ARGS=""

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-cache)
                BUILD_ARGS="--no-cache"
                shift
                ;;
            --pull)
                BUILD_ARGS="$BUILD_ARGS --pull"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done

    check_docker
    check_env_file
    build_image $BUILD_ARGS
}

# 执行主函数
main "$@"
