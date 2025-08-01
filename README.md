# MCP Server Context7

A Model Context Protocol (MCP) server providing access to Context7 API for searching and downloading library documentation and source code repositories.

> **🤖 Built with Copilot**: This project was implemented through **Copilot Vibe Coding** - an AI-assisted development approach using GitHub Copilot for rapid prototyping and implementation.

> **About**: This project is a Python port of Upstash's excellent [Context7](https://github.com/upstash/context7/) MCP server, enhanced with additional features like local documentation management and automatic repository cloning.erver Context7

> **⚠️ Important**: This project is provided **as-is** with **no maintenance commitment**. For production use or ongoing support, please fork this repository and maintain your own version.

## Features

- **Search Libraries**: Semantic search across Context7's extensive library database
- **Fetch Documentation**: Download comprehensive documentation for any library
- **Repository Sync**: Automatically clone associated GitHub repositories
- **Local Management**: List and browse downloaded documentation
- **Index Maintenance**: Automatic INDEX.md file management for tracking downloads

## Installation

### Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp_server_context7.git
cd mcp_server_context7

# Run the install script (creates isolated virtual environment)
chmod +x install.sh
./install.sh
```

The install script will:
- ✅ Check Python version (requires 3.10+)
- ✅ Create isolated virtual environment `.venv`
- ✅ Install all dependencies
- ✅ Provide complete MCP configuration examples

### Manual Installation

If you prefer manual control over the installation process:

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp_server_context7.git
cd mcp_server_context7

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows

# Install dependencies
pip install -e .
```

### Verify Installation

```bash
# Test run
./.venv/bin/python mcp_server_context7.py
```

## VS Code MCP Configuration

After installation, you'll have a completely isolated virtual environment. Use the following configuration:

### Auto-generated Configuration

After running `./install.sh`, the script will output complete configuration suitable for your system. Copy and paste to `.vscode/mcp.json`:

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

### Configuration with Proxy

If you need proxy support:

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

### Configuration Advantages

✅ **Complete Isolation**: Uses dedicated virtual environment, doesn't pollute system Python  
✅ **Simple and Reliable**: Directly specify Python interpreter and script path  
✅ **Cross-platform**: Works on Linux, macOS, and Windows  
✅ **Easy to Debug**: Can run tests and troubleshoot directly

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

## Based on Context7

This MCP server is based on the excellent [Context7](https://github.com/upstash/context7/) project by Upstash, which provides semantic search across a vast collection of library documentation.

## License

MIT License - see LICENSE file for details.

## Contributing

**⚠️ Maintenance Notice**: This project is provided as-is without ongoing maintenance commitment. 

If you need features, bug fixes, or long-term support, we recommend:
1. **Fork this repository** for your own use
2. **Create your own maintained version**
3. **Submit pull requests** (they will be reviewed when possible, but no timeline is guaranteed)

For contributing to this repository:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test your changes manually
5. Submit a pull request

**Note**: This project currently does not have automated tests. Please test your changes manually before submitting.

## Support

**⚠️ Limited Support**: This project is provided as-is with limited support.

For issues and questions:
- **First, try forking and fixing issues yourself** - this is the recommended approach
- Check existing GitHub issues to see if your problem has been reported
- Check the Context7 documentation at https://context7.com for API-related questions
- Open a GitHub issue only for critical bugs, but expect limited response

**For commercial or mission-critical use, we strongly recommend forking this repository and maintaining your own version.**

## Project URLs

- Repository: https://github.com/yourusername/mcp_server_context7
- Issues: https://github.com/yourusername/mcp_server_context7/issues

## Documentation

- [English README](README.md)
- [中文 README](README.zh.md)
