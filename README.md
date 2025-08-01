# MCP Server Context7

A Model Context Protocol (MCP) server that provides access to Context7 API for searching and downloading library documentation and source repositories.

## Features

- **Search Libraries**: Semantic search across Context7's extensive library database
- **Fetch Documentation**: Download comprehensive documentation for any library
- **Repository Sync**: Automatically clone associated GitHub repositories
- **Local Management**: List and browse downloaded documentation
- **Index Maintenance**: Automatic INDEX.md file management for tracking downloads

## Installation

### 快速安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/yourusername/mcp_server_context7.git
cd mcp_server_context7

# 运行安装脚本（会创建隔离的虚拟环境）
chmod +x install.sh
./install.sh
```

安装脚本会：
- ✅ 检查 Python 版本（需要 3.10+）
- ✅ 创建隔离的虚拟环境 `.venv`
- ✅ 安装所有依赖项
- ✅ 提供完整的 MCP 配置示例

### 手动安装

如果您更喜欢手动控制安装过程：

```bash
# 克隆仓库
git clone https://github.com/yourusername/mcp_server_context7.git
cd mcp_server_context7

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -e .
```

### 验证安装

```bash
# 测试运行
./.venv/bin/python mcp_server_context7.py
```

## VS Code MCP Configuration

安装完成后，您将获得一个完全隔离的虚拟环境。使用以下配置：

### 自动生成的配置

运行 `./install.sh` 后，脚本会输出适合您系统的完整配置。复制并粘贴到 `.vscode/mcp.json`：

```json
{
  "servers": {
    "context7": {
      "command": "/path/to/mcp_server_context7/.venv/bin/python",
      "args": ["/path/to/mcp_server_context7/mcp_server_context7.py"],
      "env": {
        "CLIENT_IP_ENCRYPTION_KEY": "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
      }
    }
  }
}
```

### 带代理的配置

如果需要代理支持：

```json
{
  "servers": {
    "context7": {
      "command": "/path/to/mcp_server_context7/.venv/bin/python",
      "args": ["/path/to/mcp_server_context7/mcp_server_context7.py"],
      "env": {
        "CLIENT_IP_ENCRYPTION_KEY": "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
        "http_proxy": "http://127.0.0.1:8890",
        "HTTP_PROXY": "http://127.0.0.1:8890",
        "https_proxy": "http://127.0.0.1:8890", 
        "HTTPS_PROXY": "http://127.0.0.1:8890",
        "all_proxy": "socks5://127.0.0.1:8890"
      }
    }
  }
}
```

### 配置优势

✅ **完全隔离**: 使用专用虚拟环境，不污染系统 Python  
✅ **简单可靠**: 直接指定 Python 解释器和脚本路径  
✅ **跨平台**: 适用于 Linux、macOS 和 Windows  
✅ **易于调试**: 可以直接运行测试和排错

## Usage

### Running the MCP Server

```bash
python mcp_server_context7.py
```

### Available Tools

1. **search_libraries(query, client_ip=None)**
   - Search for libraries matching a query
   - Returns formatted results with library details

2. **fetch_library_documentation(library_id, topic=None, tokens=None, client_ip=None, save_to_file=True, sync_repo=False, search_query=None)**
   - Download library documentation
   - Optionally sync source code repository
   - Automatically maintains INDEX.md

3. **list_downloaded_libraries(base_dir=".kms/context7/km-base")**
   - List all previously downloaded libraries
   - Shows file sizes, modification dates, and repository status

4. **get_library_content(filename, base_dir=".kms/context7/km-base", max_chars=10000)**
   - Read content from downloaded documentation
   - Supports content truncation for large files

### Example Usage

```python
# Search for libraries
results = search_libraries("fastapi web framework")

# Download documentation with repository sync
doc = fetch_library_documentation(
    library_id="tiangolo/fastapi",
    search_query="fastapi web framework",
    sync_repo=True
)

# List downloaded libraries
libraries = list_downloaded_libraries()

# Read library content
content = get_library_content("tiangolo_fastapi.md", max_chars=5000)
```

## Configuration

### Environment Variables

- `CLIENT_IP_ENCRYPTION_KEY`: 64-character hex key for encrypting client IP (optional)

### Directory Structure

```
.kms/context7/
├── km-base/                    # Documentation storage
│   ├── INDEX.md               # Auto-maintained index
│   ├── library_name.md        # Documentation files
│   └── library_name_repo/     # Cloned repositories
└── scripts/                   # Reserved for future CLI tools
```

## Development

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run linting
ruff check .

# Run formatting
black .

# Run type checking
mypy mcp_server_context7.py
```

## Based on Context7

This MCP server is based on the excellent [Context7](https://github.com/upstash/context7/) project by Upstash, which provides semantic search across a vast collection of library documentation.

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test your changes manually
5. Submit a pull request

**Note**: This project currently does not have automated tests. Please test your changes manually before submitting.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the Context7 documentation at https://context7.com

## Project URLs

- Repository: https://github.com/yourusername/mcp_server_context7
- Issues: https://github.com/yourusername/mcp_server_context7/issues
