#!/bin/bash
# 复制 voice_text_tts 代码到 docker 打包目录

set -e

echo "======================================"
echo "复制源代码到 Docker 目录"
echo "======================================"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 源代码目录和目标目录
SOURCE_DIR="../voice_text_tts"
TARGET_DIR="$SCRIPT_DIR/voice_text_tts"

echo "📂 源目录: $SOURCE_DIR"
echo "📂 目标目录: $TARGET_DIR"
echo ""

# 检查源目录是否存在
if [ ! -d "$SOURCE_DIR" ]; then
    echo "❌ 错误: 找不到源目录 $SOURCE_DIR"
    exit 1
fi

# 删除旧的复制（如果存在）
if [ -d "$TARGET_DIR" ]; then
    echo "🗑️  删除旧的复制..."
    rm -rf "$TARGET_DIR"
fi

# 创建目标目录
echo "📁 创建目标目录..."
mkdir -p "$TARGET_DIR"

# 复制文件
echo "📋 复制文件..."
rsync -av --progress \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='.git' \
    --exclude='.gitignore' \
    --exclude='*.log' \
    --exclude='.DS_Store' \
    --exclude='Thumbs.db' \
    --exclude='venv/' \
    --exclude='env/' \
    --exclude='.venv/' \
    --exclude='dist/' \
    --exclude='build/' \
    --exclude='*.egg-info/' \
    "$SOURCE_DIR/" "$TARGET_DIR/"

echo ""
echo "✅ 复制完成！"
echo ""
echo "目标目录内容:"
ls -lh "$TARGET_DIR"
