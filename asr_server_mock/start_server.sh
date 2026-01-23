#!/bin/bash
# ASR服务器启动脚本

echo "=========================================="
echo "  模拟ASR WebSocket服务器"
echo "=========================================="
echo ""

# 检查是否安装了websockets
python -c "import websockets" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "错误: 未安装websockets模块"
    echo "请运行: pip install websockets"
    exit 1
fi

echo "正在启动ASR服务器..."
echo "地址: ws://localhost:10095"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

# 启动服务器
python asr_server.py --host localhost --port 10095
