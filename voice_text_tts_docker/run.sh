#!/bin/bash
# ===========================================
# Voice Text TTS Docker 服务运行脚本
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

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    print_info "Docker 环境检查通过"
}

# 检查镜像是否存在
check_image() {
    if ! docker images | grep -q "voice-text-tts"; then
        print_error "Docker 镜像不存在，请先运行 ./build.sh 构建镜像"
        exit 1
    fi
    print_info "Docker 镜像检查通过"
}

# 读取配置
load_config() {
    if [ -f .env ]; then
        # 只提取 SERVER_PORT，避免解析复杂值
        SERVER_PORT=$(grep -E '^SERVER_PORT=' .env 2>/dev/null | cut -d'=' -f2)
        SERVER_PORT=${SERVER_PORT:-7863}
    else
        SERVER_PORT=7863
    fi
}

# 启动服务
start_service() {
    print_info "启动服务..."

    # 停止并删除旧容器
    if docker ps -a | grep -q "voice_text_tts_app"; then
        print_warn "检测到已存在的容器，正在停止并删除..."
        docker stop voice_text_tts_app 2>/dev/null || true
        docker rm voice_text_tts_app 2>/dev/null || true
    fi

    # 启动新容器
    docker run -d \
        --name voice_text_tts_app \
        -p ${SERVER_PORT}:7863 \
        --env-file .env \
        --add-host=host.docker.internal:host-gateway \
        --restart unless-stopped \
        voice-text-tts:latest

    print_info "服务已启动"
}

# 停止服务
stop_service() {
    print_info "停止服务..."

    if docker ps | grep -q "voice_text_tts_app"; then
        docker stop voice_text_tts_app
        print_info "服务已停止"
    else
        print_warn "容器未运行"
    fi
}

# 删除容器
remove_container() {
    print_info "删除容器..."

    if docker ps -a | grep -q "voice_text_tts_app"; then
        docker stop voice_text_tts_app 2>/dev/null || true
        docker rm voice_text_tts_app
        print_info "容器已删除"
    else
        print_warn "容器不存在"
    fi
}

# 重启服务
restart_service() {
    print_info "重启服务..."
    stop_service
    sleep 1
    start_service
}

# 查看日志
view_logs() {
    if docker ps | grep -q "voice_text_tts_app"; then
        print_info "查看服务日志（按 Ctrl+C 退出日志查看）..."
        echo ""
        docker logs -f voice_text_tts_app
    else
        print_error "容器未运行，请先启动服务"
        exit 1
    fi
}

# 查看状态
show_status() {
    print_info "容器状态:"
    echo ""

    if docker ps -a | grep -q "voice_text_tts_app"; then
        docker ps -a | grep voice_text_tts_app
        echo ""

        if docker ps | grep -q "voice_text_tts_app"; then
            print_info "容器运行中"
            print_info "访问地址: http://localhost:${SERVER_PORT}"
        else
            print_warn "容器已停止"
        fi
    else
        print_warn "容器不存在"
    fi
}

# 进入容器
exec_shell() {
    if docker ps | grep -q "voice_text_tts_app"; then
        print_info "进入容器Shell（输入 exit 退出）..."
        docker exec -it voice_text_tts_app /bin/bash
    else
        print_error "容器未运行，请先启动服务"
        exit 1
    fi
}

# 重新构建镜像
rebuild_image() {
    print_info "重新构建镜像..."

    # 停止并删除旧容器
    if docker ps -a | grep -q "voice_text_tts_app"; then
        print_warn "检测到已存在的容器，正在停止并删除..."
        docker stop voice_text_tts_app 2>/dev/null || true
        docker rm voice_text_tts_app 2>/dev/null || true
    fi

    # 构建新镜像
    print_info "开始构建 Docker 镜像（这可能需要几分钟）..."
    docker build -t voice-text-tts:latest -f Dockerfile .

    if [ $? -eq 0 ]; then
        print_info "镜像构建成功！"
        print_info "运行 '$0 start' 启动服务"
    else
        print_error "镜像构建失败"
        exit 1
    fi
}

# 一键部署（构建+启动）
deploy() {
    print_info "开始一键部署..."
    rebuild_image
    echo ""
    start_service
    echo ""
    print_info "=========================================="
    print_info "部署成功！"
    print_info "=========================================="
    print_info "访问地址: http://localhost:${SERVER_PORT}"
    print_info "查看日志: $0 logs"
    print_info "停止服务: $0 stop"
    print_info "=========================================="
    echo ""
}

# 显示帮助
show_help() {
    echo "Voice Text TTS Docker 服务运行脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start     启动服务（默认）"
    echo "  stop      停止服务"
    echo "  restart   重启服务"
    echo "  status    查看服务状态"
    echo "  logs      查看服务日志"
    echo "  shell     进入容器Shell"
    echo "  rebuild   重新构建镜像"
    echo "  deploy    一键部署（构建+启动）"
    echo "  rm        删除容器"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0              # 启动服务"
    echo "  $0 start        # 启动服务"
    echo "  $0 stop         # 停止服务"
    echo "  $0 logs         # 查看日志"
    echo "  $0 shell        # 进入容器"
    echo "  $0 rebuild      # 重新构建镜像"
    echo "  $0 deploy       # 一键部署"
}

# 主函数
main() {
    local command="${1:-start}"

    check_docker
    load_config

    case "$command" in
        start)
            check_image
            start_service
            echo ""
            print_info "=========================================="
            print_info "服务启动成功！"
            print_info "=========================================="
            print_info "访问地址: http://localhost:${SERVER_PORT}"
            print_info "查看日志: $0 logs"
            print_info "停止服务: $0 stop"
            print_info "=========================================="
            echo ""
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            show_status
            ;;
        logs)
            view_logs
            ;;
        shell)
            exec_shell
            ;;
        rebuild)
            rebuild_image
            ;;
        deploy)
            deploy
            ;;
        rm)
            remove_container
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
