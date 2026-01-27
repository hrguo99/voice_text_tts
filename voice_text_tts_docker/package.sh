#!/bin/bash
# ===========================================
# Voice Text TTS Docker 打包脚本
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

# 获取版本号（基于日期时间）
get_version() {
    date +"%Y%m%d_%H%M%S"
}

# 清理旧的打包文件
clean_old_packages() {
    if [ -d "build" ]; then
        print_info "清理旧的打包文件..."
        rm -rf build
    fi
    mkdir -p build
    print_info "创建 build 目录"
}

# 打包文件
package_files() {
    VERSION=$(get_version)
    PACKAGE_NAME="voice-text-tts-docker-${VERSION}"
    PACKAGE_FILE="build/${PACKAGE_NAME}.tar.gz"

    print_info "开始打包 Docker 部署文件..."
    echo ""

    # 创建临时目录
    TEMP_DIR=$(mktemp -d)
    mkdir -p "${TEMP_DIR}/${PACKAGE_NAME}"

    # 复制文件到临时目录
    print_info "复制文件到临时目录..."

    # Docker 配置文件
    cp Dockerfile "${TEMP_DIR}/${PACKAGE_NAME}/"
    cp docker-compose.yml "${TEMP_DIR}/${PACKAGE_NAME}/"
    cp .dockerignore "${TEMP_DIR}/${PACKAGE_NAME}/"
    cp .env.example "${TEMP_DIR}/${PACKAGE_NAME}/"

    # 脚本文件
    cp build.sh "${TEMP_DIR}/${PACKAGE_NAME}/"
    cp run.sh "${TEMP_DIR}/${PACKAGE_NAME}/"
    cp package.sh "${TEMP_DIR}/${PACKAGE_NAME}/"

    # 文档
    cp README.md "${TEMP_DIR}/${PACKAGE_NAME}/"
    cp DEPLOY_GUIDE.md "${TEMP_DIR}/${PACKAGE_NAME}/"

    # 复制 voice_text_tts 目录（排除缓存和临时文件）
    print_info "复制 voice_text_tts 目录..."
    mkdir -p "${TEMP_DIR}/${PACKAGE_NAME}/voice_text_tts"

    # 使用 rsync 或 cp 排除不需要的文件
    rsync -av --exclude='__pycache__' \
              --exclude='*.pyc' \
              --exclude='*.pyo' \
              --exclude='*.pyd' \
              --exclude='.DS_Store' \
              --exclude='*.log' \
              voice_text_tts/ "${TEMP_DIR}/${PACKAGE_NAME}/voice_text_tts/"

    # 创建打包
    print_info "创建 tar.gz 压缩包..."
    ORIGINAL_DIR=$(pwd)
    cd "${TEMP_DIR}"
    tar -czf "${PACKAGE_NAME}.tar.gz" "${PACKAGE_NAME}"
    cd "${ORIGINAL_DIR}"

    # 移动到 build 目录
    mv "${TEMP_DIR}/${PACKAGE_NAME}.tar.gz" "build/${PACKAGE_NAME}.tar.gz"

    # 清理临时目录
    rm -rf "${TEMP_DIR}"

    echo ""
    print_info "打包完成！"
    echo ""
    print_blue "=========================================="
    print_info "包文件: build/${PACKAGE_NAME}.tar.gz"
    print_info "大小: $(du -h "build/${PACKAGE_NAME}.tar.gz" | cut -f1)"
    print_blue "=========================================="
    echo ""
    print_info "解压命令:"
    echo "  tar -xzf build/${PACKAGE_NAME}.tar.gz"
    echo ""
    print_info "部署步骤:"
    echo "  1. 解压: tar -xzf build/${PACKAGE_NAME}.tar.gz"
    echo "  2. 进入目录: cd ${PACKAGE_NAME}"
    echo "  3. 复制配置: cp .env.example .env"
    echo "  4. 修改配置: vim .env  # 根据需要修改"
    echo "  5. 构建镜像: ./build.sh"
    echo "  6. 启动服务: ./run.sh"
    echo ""
}

# 显示帮助
show_help() {
    echo "Voice Text TTS Docker 打包脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --no-clean    不清理旧的打包文件"
    echo "  -h, --help    显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0              # 打包文件"
    echo "  $0 --no-clean   # 打包文件但不清理旧文件"
}

# 主函数
main() {
    local CLEAN_OLD=true

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-clean)
                CLEAN_OLD=false
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

    print_blue "=========================================="
    print_info "Voice Text TTS Docker 打包工具"
    print_blue "=========================================="
    echo ""

    if [ "$CLEAN_OLD" = true ]; then
        clean_old_packages
    else
        mkdir -p build
    fi

    package_files

    print_info "✅ 打包完成！"
    echo ""
    print_info "查看打包文件: ls -lh build/"
}

# 执行主函数
main "$@"
