#!/bin/bash
# ===========================================
# Voice Text TTS Docker 一键启动脚本
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

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
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
    if docker compose version &> /dev/null; then
        docker compose build
    else
        docker-compose build
    fi
    print_info "Docker 镜像构建完成"
}

# 启动服务
start_service() {
    print_info "启动服务..."
    if docker compose version &> /dev/null; then
        docker compose up -d
    else
        docker-compose up -d
    fi
    print_info "服务已启动"
}

# 查看日志
view_logs() {
    print_info "查看服务日志（按 Ctrl+C 退出日志查看）..."
    echo ""
    if docker compose version &> /dev/null; then
        docker compose logs -f
    else
        docker-compose logs -f
    fi
}

# 停止服务
stop_service() {
    print_info "停止服务..."
    if docker compose version &> /dev/null; then
        docker compose down
    else
        docker-compose down
    fi
    print_info "服务已停止"
}

# 重启服务
restart_service() {
    print_info "重启服务..."
    stop_service
    start_service
}

# 清理
cleanup() {
    print_info "清理容器和镜像..."
    if docker compose version &> /dev/null; then
        docker compose down -v --rmi all
    else
        docker-compose down -v --rmi all
    fi
    print_info "清理完成"
}

# 显示帮助
show_help() {
    echo "Voice Text TTS Docker 管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start     构建并启动服务（默认）"
    echo "  stop      停止服务"
    echo "  restart   重启服务"
    echo "  logs      查看服务日志"
    echo "  build     仅构建镜像"
    echo "  cleanup   清理容器和镜像"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0              # 构建并启动服务"
    echo "  $0 start        # 构建并启动服务"
    echo "  $0 stop         # 停止服务"
    echo "  $0 logs         # 查看日志"
}

# 主函数
main() {
    local command="${1:-start}"

    case "$command" in
        start)
            check_docker
            check_env_file
            build_image
            start_service
            echo ""
            print_info "=========================================="
            print_info "服务启动成功！"
            print_info "=========================================="
            print_info "访问地址: http://localhost:$(grep SERVER_PORT .env | cut -d'=' -f2)"
            print_info "查看日志: $0 logs"
            print_info "停止服务: $0 stop"
            print_info "=========================================="
            echo ""
            ;;
        stop)
            check_docker
            stop_service
            ;;
        restart)
            check_docker
            restart_service
            ;;
        logs)
            check_docker
            view_logs
            ;;
        build)
            check_docker
            build_image
            ;;
        cleanup)
            check_docker
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
