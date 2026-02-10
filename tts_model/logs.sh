#!/bin/bash
# TTS 模型 Docker 容器日志查看脚本

CONTAINER_NAME="fun-cosyvoice3-tts"

echo "=========================================="
echo "TTS 模型服务实时日志"
echo "=========================================="
echo ""
echo "按 Ctrl+C 退出"
echo ""

docker logs -f ${CONTAINER_NAME} 2>&1
