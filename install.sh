#!/bin/bash
# MCP Server Context7 安装脚本

set -e  # 遇到错误立即退出

echo "🚀 安装 MCP Server Context7..."

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# 检查是否有 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3。请先安装 Python 3.10+。"
    exit 1
fi

# 检查 Python 版本
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ 错误: 需要 Python $REQUIRED_VERSION 或更高版本，当前版本: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python 版本检查通过: $PYTHON_VERSION"

# 创建虚拟环境
echo "📦 创建虚拟环境..."
if [ -d "$VENV_DIR" ]; then
    echo "⚠️  虚拟环境已存在，将重新创建..."
    rm -rf "$VENV_DIR"
fi

python3 -m venv "$VENV_DIR"

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 升级 pip
echo "⬆️  升级 pip..."
pip install --upgrade pip

# 安装项目依赖
echo "📚 安装依赖..."
pip install -e .

echo ""
echo "🎉 安装完成！"
echo ""
echo "📝 MCP 配置文件 (.vscode/mcp.json):"
echo '{'
echo '  "servers": {'
echo '    "context7": {'
echo '      "command": "'"$VENV_DIR/bin/python"'",'
echo '      "args": ["'"$SCRIPT_DIR/mcp_server_context7.py"'"],'
echo '      "env": {'
echo '        "CLIENT_IP_ENCRYPTION_KEY": "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"'
echo '      }'
echo '    }'
echo '  }'
echo '}'
echo ""
echo "💡 使用说明:"
echo "1. 复制上面的配置到您的 .vscode/mcp.json 文件"
echo "2. 根据需要修改 CLIENT_IP_ENCRYPTION_KEY"
echo "3. 重启 VS Code 或重新加载 MCP 扩展"
echo ""
echo "🧪 测试运行:"
echo "   $VENV_DIR/bin/python $SCRIPT_DIR/mcp_server_context7.py"
