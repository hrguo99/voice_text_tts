#!/bin/bash
# TTS 模型 Docker 容器代码更新脚本
# 将本地修改的代码复制到运行中的 Docker 容器

set -e

CONTAINER_NAME="fun-cosyvoice3-tts"  # 请根据实际情况修改
LOCAL_CODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE_CODE_DIR="/app"  # 容器内代码目录

echo "=========================================="
echo "TTS 模型 Docker 代码更新脚本"
echo "=========================================="
echo ""
echo "本地代码目录: ${LOCAL_CODE_DIR}"
echo "容器名称: ${CONTAINER_NAME}"
echo "容器内目录: ${REMOTE_CODE_DIR}"
echo ""

# 检查容器是否运行
if ! docker ps | grep -q "${CONTAINER_NAME}"; then
    echo "❌ 错误: 容器 ${CONTAINER_NAME} 未运行"
    echo ""
    echo "请检查容器名称，运行中的容器："
    docker ps --format "table {{.Names}}\t{{.Status}}"
    exit 1
fi

echo "✅ 找到运行中的容器: ${CONTAINER_NAME}"
echo ""

# 询问要更新的文件
echo "请选择要更新的文件："
echo "  1) server.py (FastAPI 服务器)"
echo "  2) client.py (测试客户端)"
echo "  3) 全部更新"
echo ""
read -p "请输入选项 (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "📤 复制 server.py 到容器..."
        docker cp "${LOCAL_CODE_DIR}/server.py" "${CONTAINER_NAME}:${REMOTE_CODE_DIR}/server.py"
        echo "✅ server.py 已更新"
        ;;
    2)
        echo ""
        echo "📤 复制 client.py 到容器..."
        docker cp "${LOCAL_CODE_DIR}/client.py" "${CONTAINER_NAME}:${REMOTE_CODE_DIR}/client.py"
        echo "✅ client.py 已更新"
        ;;
    3)
        echo ""
        echo "📤 复制所有代码文件到容器..."
        docker cp "${LOCAL_CODE_DIR}/server.py" "${CONTAINER_NAME}:${REMOTE_CODE_DIR}/server.py"
        docker cp "${LOCAL_CODE_DIR}/client.py" "${CONTAINER_NAME}:${REMOTE_CODE_DIR}/client.py"
        echo "✅ 所有文件已更新"
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "⚠️  注意: 代码更新后需要重启容器才能生效"
echo ""
read -p "是否立即重启容器？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔄 重启容器..."
    docker restart ${CONTAINER_NAME}
    echo "✅ 容器已重启"
    echo ""
    echo "💡 查看日志: ./logs.sh"
else
    echo ""
    echo "💡 手动重启命令: docker restart ${CONTAINER_NAME}"
fi
