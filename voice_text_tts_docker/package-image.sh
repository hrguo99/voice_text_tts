#!/bin/bash
# ===========================================
# Voice Text TTS Docker 镜像打包脚本
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

# 检查镜像是否存在
check_image() {
    if ! docker images | grep -q "voice-text-tts"; then
        print_error "Docker 镜像不存在！"
        echo ""
        print_info "请先运行 ./build.sh 构建镜像"
        exit 1
    fi
    print_info "Docker 镜像检查通过"
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

# 打包 Docker 镜像
package_image() {
    VERSION=$(get_version)
    IMAGE_NAME="voice-text-tts"
    PACKAGE_FILE="build/${IMAGE_NAME}-docker-image-${VERSION}.tar.gz"

    print_info "开始打包 Docker 镜像..."
    echo ""

    # 获取镜像信息
    IMAGE_ID=$(docker images -q ${IMAGE_NAME}:latest)
    IMAGE_SIZE=$(docker images ${IMAGE_NAME}:latest --format "{{.Size}}")

    print_info "镜像信息:"
    echo "  名称: ${IMAGE_NAME}:latest"
    echo "  ID: ${IMAGE_ID}"
    echo "  大小: ${IMAGE_SIZE}"
    echo ""

    # 导出镜像
    print_info "正在导出镜像（这可能需要几分钟）..."
    docker save ${IMAGE_NAME}:latest | gzip > "${PACKAGE_FILE}"

    # 获取打包文件大小
    PACKAGE_SIZE=$(du -h "${PACKAGE_FILE}" | cut -f1)

    echo ""
    print_info "打包完成！"
    echo ""
    print_blue "=========================================="
    print_info "镜像文件: ${PACKAGE_FILE}"
    print_info "压缩后大小: ${PACKAGE_SIZE}"
    print_blue "=========================================="
    echo ""

    # 创建部署脚本
    print_info "创建镜像导入脚本..."
    cat > "build/import-image.sh" << 'IMPEOF'
#!/bin/bash
# ===========================================
# Docker 镜像导入脚本
# ===========================================

set -e

GREEN='\033[0;32m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# 检查参数
if [ -z "$1" ]; then
    echo "用法: $0 <镜像文件.tar.gz>"
    echo ""
    echo "示例:"
    echo "  $0 voice-text-tts-docker-image-20260123_180929.tar.gz"
    exit 1
fi

IMAGE_FILE="$1"

if [ ! -f "$IMAGE_FILE" ]; then
    echo "错误: 镜像文件不存在: $IMAGE_FILE"
    exit 1
fi

print_info "开始导入 Docker 镜像..."
echo "文件: $IMAGE_FILE"
echo ""

# 解压并导入镜像
print_info "正在导入镜像（这可能需要几分钟）..."
gunzip -c "$IMAGE_FILE" | docker load

echo ""
print_info "镜像导入完成！"
echo ""
print_info "查看镜像:"
echo "  docker images | grep voice-text-tts"
echo ""
print_info "运行容器:"
echo "  ./run.sh"
IMPEOF

    chmod +x "build/import-image.sh"

    print_info "导入脚本已创建: build/import-image.sh"
    echo ""

    # 复制一键部署脚本到 build 目录
    print_info "复制一键部署脚本到 build 目录..."
    cp deploy.sh build/

    # 复制说明文档到 build 目录
    print_info "复制说明文档到 build 目录..."
    cp DEPLOY_GUIDE.md build/
    cp README.md build/

    print_info "部署文件已准备完成"
    echo ""

    # 创建 README
    print_info "创建部署说明..."
    cat > "build/IMAGE_DEPLOY_README.md" << 'READMEEOF'
# Docker 镜像部署说明

## 📦 镜像文件说明

镜像文件为压缩的 Docker 镜像，文件名格式：`voice-text-tts-docker-image-YYYYMMDD_HHMMSS.tar.gz`

## 🚀 快速部署

### 方法一：使用导入脚本（推荐）

```bash
# 1. 解压镜像包（如果需要）
tar -xzf voice-text-tts-docker-image-YYYYMMDD_HHMMSS.tar.gz

# 2. 导入镜像
chmod +x import-image.sh
./import-image.sh voice-text-tts-docker-image-YYYYMMDD_HHMMSS.tar.gz

# 3. 验证镜像
docker images | grep voice-text-tts

# 4. 准备配置文件
cp .env.example .env
vim .env  # 根据需要修改配置

# 5. 启动容器
./run.sh start
```

### 方法二：手动导入

```bash
# 1. 导入镜像
gunzip -c voice-text-tts-docker-image-YYYYMMDD_HHMMSS.tar.gz | docker load

# 2. 查看导入的镜像
docker images | grep voice-text-tts

# 3. 启动容器
./run.sh start
```

## 📋 镜像信息

导入后的镜像信息：
- **镜像名称**: voice-text-tts
- **镜像标签**: latest
- **基础镜像**: python:3.12-slim
- **包含组件**:
  - Gradio 5.x
  - Python 3.12
  - ffmpeg 及音频处理库
  - 完整的应用程序代码

## ⚙️ 环境要求

### Docker 环境
- Docker >= 20.10
- 至少 2GB 可用内存
- 至少 5GB 可用磁盘空间

### 外部依赖
- TTS API 服务（运行在宿主机 50000 端口）
- 容器会通过 `host.docker.internal` 访问宿主机 API

## 🔧 配置说明

在启动容器前，需要创建 `.env` 文件：

```bash
# API 配置
API_HOST=host.docker.internal  # 访问宿主机
API_PORT=50000                 # TTS API 端口

# Gradio 配置
SERVER_PORT=7862               # Web 服务端口
GRADIO_SHARE=true              # 启用公网分享（可选）

# ASR 配置（可选）
ASR_ENABLED=false              # 是否启用语音识别
```

## 📝 注意事项

1. **镜像大小**: 解压后的镜像较大（约 2-3GB），请确保有足够磁盘空间
2. **导入时间**: 镜像导入可能需要 5-10 分钟，取决于系统性能
3. **网络配置**: 容器使用 `--add-host=host.docker.internal:host-gateway` 访问宿主机
4. **端口冲突**: 默认使用 7862 端口，如有冲突请在 `.env` 中修改

## 🔍 故障排查

### 镜像导入失败

```bash
# 检查磁盘空间
df -h

# 检查 Docker 状态
docker info

# 查看导入日志
docker load -i voice-text-tts-docker-image-YYYYMMDD_HHMMSS.tar.gz
```

### 容器启动失败

```bash
# 查看容器日志
docker logs voice_text_tts_app

# 检查容器状态
docker ps -a | grep voice_text_tts_app

# 进入容器调试
./run.sh shell
```

### 无法连接 API 服务

```bash
# 测试容器到宿主机的连接
docker exec voice_text_tts_app curl http://host.docker.internal:50000

# 检查 hosts 配置
docker exec voice_text_tts_app cat /etc/hosts
```

## 🔄 更新镜像

如果有新版本镜像：

```bash
# 1. 停止并删除旧容器
./run.sh stop
./run.sh rm

# 2. 删除旧镜像
docker rmi voice-text-tts:latest

# 3. 导入新镜像
./import-image.sh voice-text-tts-docker-image-new-version.tar.gz

# 4. 启动新容器
./run.sh start
```

## 📞 技术支持

如遇问题，请检查：
- Docker 版本是否符合要求
- 系统资源是否充足
- 网络配置是否正确
- API 服务是否正常运行
READMEEOF

    print_info "部署说明已创建: build/IMAGE_DEPLOY_README.md"
    echo ""

    print_info "部署步骤:"
    echo "  1. 将镜像文件和 import-image.sh 复制到目标服务器"
    echo "  2. 运行: ./import-image.sh ${IMAGE_NAME}-docker-image-${VERSION}.tar.gz"
    echo "  3. 查看详细说明: cat IMAGE_DEPLOY_README.md"
    echo ""
}

# 显示帮助
show_help() {
    echo "Voice Text TTS Docker 镜像打包脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --no-clean    不清理旧的打包文件"
    echo "  -h, --help    显示此帮助信息"
    echo ""
    echo "说明:"
    echo "  此脚本将导出 Docker 镜像为 tar.gz 压缩包"
    echo "  导出的镜像可用于在其他机器上部署"
    echo ""
    echo "示例:"
    echo "  $0              # 打包镜像"
    echo "  $0 --no-clean   # 打包镜像但不清理旧文件"
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
    print_info "Voice Text TTS Docker 镜像打包工具"
    print_blue "=========================================="
    echo ""

    check_image

    if [ "$CLEAN_OLD" = true ]; then
        clean_old_packages
    else
        mkdir -p build
    fi

    package_image

    print_info "✅ 镜像打包完成！"
    echo ""
    print_info "查看打包文件: ls -lh build/"
}

# 执行主函数
main "$@"
