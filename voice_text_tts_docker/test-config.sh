#!/bin/bash
# 快速测试脚本 - 验证 Docker 配置是否正确

set -e

echo "======================================"
echo "Docker 配置测试"
echo "======================================"

# 获取脚本所在目录并切换到该目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📂 当前目录: $(pwd)"
echo ""

# 检查 voice_text_tts 目录
if [ -d "voice_text_tts" ]; then
    echo "✅ voice_text_tts 目录存在"
else
    echo "⚠️  voice_text_tts 目录不存在（将自动复制）"
fi

# 检查关键文件
if [ -f "Dockerfile" ]; then
    echo "✅ Dockerfile 存在"
else
    echo "❌ Dockerfile 不存在"
    exit 1
fi

if [ -f "docker-compose.yml" ]; then
    echo "✅ docker-compose.yml 存在"
else
    echo "❌ docker-compose.yml 不存在"
    exit 1
fi

if [ -f ".env.example" ]; then
    echo "✅ .env.example 存在"
else
    echo "❌ .env.example 不存在"
    exit 1
fi

# 如果 voice_text_tts 不存在，检查源目录
if [ ! -d "voice_text_tts" ]; then
    echo ""
    if [ -d "../voice_text_tts" ]; then
        echo "✅ 源代码目录存在 (../voice_text_tts)"
        echo ""
        echo "💡 提示: 运行 ./build.sh 或 ./start.sh 时会自动复制源代码"
    else
        echo "❌ 源代码目录不存在 (../voice_text_tts)"
        echo "   请确保 voice_text_tts 目录在父目录中"
        exit 1
    fi
else
    # 检查 voice_text_tts 中的关键文件
    if [ -f "voice_text_tts/app.py" ]; then
        echo "✅ app.py 存在"
    else
        echo "❌ app.py 不存在"
        exit 1
    fi

    if [ -f "voice_text_tts/requirements.txt" ]; then
        echo "✅ requirements.txt 存在"
    else
        echo "❌ requirements.txt 不存在"
        exit 1
    fi
fi

echo ""
echo "✅ 所有检查通过！"
echo ""
echo "接下来可以运行: ./build.sh 或 ./start.sh"
