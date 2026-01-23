#!/bin/bash
# ASR服务快速测试脚本

echo "=========================================="
echo "  ASR服务快速测试"
echo "=========================================="
echo ""

# 检查服务器是否运行
echo "1. 检查ASR服务器状态..."
if ! nc -z localhost 10095 2>/dev/null; then
    echo "✗ ASR服务器未运行"
    echo ""
    echo "请先启动ASR服务器："
    echo "  cd /media/jk-b-047/C14233E584A57CB0/code/guohaoran/asr_server_mock"
    echo "  python asr_server.py"
    echo ""
    exit 1
fi

echo "✓ ASR服务器正在运行"
echo ""

# 运行测试
echo "2. 运行测试客户端..."
python test_client.py --count 3

echo ""
echo "测试完成！"
