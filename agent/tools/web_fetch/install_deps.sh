#!/bin/bash

# WebFetch 工具依赖安装脚本

echo "=================================="
echo "WebFetch 工具依赖安装"
echo "=================================="
echo ""

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python 版本: $python_version"
echo ""

# 安装基础依赖
echo "📦 安装基础依赖..."
python3 -m pip install requests

# 检查是否成功
if [ $? -eq 0 ]; then
    echo "✅ requests 安装成功"
else
    echo "❌ requests 安装失败"
    exit 1
fi

echo ""

# 安装推荐依赖
echo "📦 安装推荐依赖（提升内容提取质量）..."
python3 -m pip install readability-lxml html2text

# 检查是否成功
if [ $? -eq 0 ]; then
    echo "✅ readability-lxml 和 html2text 安装成功"
else
    echo "⚠️  推荐依赖安装失败，但不影响基础功能"
fi

echo ""
echo "=================================="
echo "安装完成！"
echo "=================================="
echo ""
echo "运行测试："
echo "  python3 agent/tools/web_fetch/test_web_fetch.py"
echo ""
