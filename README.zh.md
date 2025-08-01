# MCP Server Context7

一个模型上下文协议（MCP）服务器，提供对 Context7 API 的访问，用于搜索和下载库文档和源代码仓库。

> **🤖 由 Copilot 构建**：本项目通过 **Copilot Vibe Coding** 实现 - 一种使用 GitHub Copilot 进行快速原型开发和实现的 AI 辅助开发方法。

> **说明**：本项目是 Upstash 的优秀项目 [Context7](https://github.com/upstash/context7/) 的 Python 移植版本，在原有 MCP 服务器功能基础上增加了本地文档管理、自动仓库克隆等功能特性。

> **⚠️ 重要提醒**：本项目按**现状**提供，**不承诺维护**。如需生产环境使用或持续支持，请 fork 此仓库并维护您自己的版本。

## 功能特性

- **搜索库**：在 Context7 的广泛库数据库中进行语义搜索
- **获取文档**：下载任何库的综合文档
- **仓库同步**：自动克隆相关的 GitHub 仓库
- **本地管理**：列出和浏览已下载的文档
- **索引维护**：自动维护 INDEX.md 文件用于跟踪下载

## 安装

### 快速安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/jussker/mcp_server_context7.git
cd mcp_server_context7

# 运行安装脚本（创建隔离的虚拟环境）
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
git clone https://github.com/jussker/mcp_server_context7.git
cd mcp_server_context7

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -e .
```

### UV 安装

如果您使用 `uv` 包管理器：

```bash
# 直接从 Git 仓库安装
uv add git+https://github.com/jussker/mcp_server_context7.git

# 或者克隆后本地安装
git clone https://github.com/jussker/mcp_server_context7.git
cd mcp_server_context7
uv add -e .
```

### 验证安装

```bash
# 测试运行
./.venv/bin/python mcp_server_context7.py
```

## VS Code MCP 配置

### UV 安装（推荐）

如果您使用 `uv` 包管理器，使用这个配置：

```json
{
  "servers": {
    "context7": {
      "command": "uv",
      "args": ["run", "python3", "-m", "mcp_server_context7"],
      "env": {
        "CLIENT_IP_ENCRYPTION_KEY": "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
      }
    }
  }
}
```

### 快速安装 / 手动安装

如果您使用 `./install.sh` 或手动安装，使用这个配置：

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

### 需要代理支持？

如果您需要代理支持，只需在上述任意配置中添加代理环境变量：

```json
{
  "env": {
    "CLIENT_IP_ENCRYPTION_KEY": "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
    "http_proxy": "http://127.0.0.1:8890",
    "HTTP_PROXY": "http://127.0.0.1:8890",
    "https_proxy": "http://127.0.0.1:8890", 
    "HTTPS_PROXY": "http://127.0.0.1:8890",
    "all_proxy": "socks5://127.0.0.1:8890"
  }
}
```

### 配置优势

✅ **完全隔离**：使用专用虚拟环境，不污染系统 Python  
✅ **简单可靠**：直接指定 Python 解释器和脚本路径  
✅ **跨平台**：适用于 Linux、macOS 和 Windows  
✅ **易于调试**：可以直接运行测试和排错

## 使用方法

### 运行 MCP 服务器

**如果通过 UV 安装：**
```bash
uv run python -m mcp_server_context7
```

**如果通过快速安装或手动安装：**
```bash
# 从项目目录
python mcp_server_context7.py
# 或
./.venv/bin/python mcp_server_context7.py
```

### 可用工具

1. **search_libraries(query, client_ip=None)**
   - 搜索匹配查询的库
   - 返回格式化的结果和库详情

2. **fetch_library_documentation(library_id, topic=None, tokens=None, client_ip=None, save_to_file=True, sync_repo=False, search_query=None)**
   - 下载库文档
   - 可选择同步源代码仓库
   - 自动维护 INDEX.md

3. **list_downloaded_libraries(base_dir=".kms/context7/km-base")**
   - 列出所有已下载的库
   - 显示文件大小、修改日期和仓库状态

4. **get_library_content(filename, base_dir=".kms/context7/km-base", max_chars=10000)**
   - 读取已下载文档的内容
   - 支持大文件的内容截断

### 使用示例

```python
# 搜索库
results = search_libraries("fastapi web framework")

# 下载文档并同步仓库
doc = fetch_library_documentation(
    library_id="tiangolo/fastapi",
    search_query="fastapi web framework",
    sync_repo=True
)

# 列出已下载的库
libraries = list_downloaded_libraries()

# 读取库内容
content = get_library_content("tiangolo_fastapi.md", max_chars=5000)
```

## 配置

### 环境变量

- `CLIENT_IP_ENCRYPTION_KEY`：用于加密客户端 IP 的 64 字符十六进制密钥（可选）

### 目录结构

```
.kms/context7/
├── km-base/                    # 文档存储
│   ├── INDEX.md               # 自动维护的索引
│   ├── library_name.md        # 文档文件
│   └── library_name_repo/     # 克隆的仓库
└── scripts/                   # 预留给未来的 CLI 工具
```

## 开发

### 开发环境设置

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行代码检查
ruff check .

# 运行代码格式化
black .

# 运行类型检查
mypy mcp_server_context7.py
```

## 基于 Context7

本 MCP 服务器基于 Upstash 的优秀项目 [Context7](https://github.com/upstash/context7/)，该项目提供了在大量库文档集合中进行语义搜索的功能。

## 许可证

MIT 许可证 - 详见 LICENSE 文件

## 贡献

**⚠️ 维护说明**：本项目按现状提供，不承诺持续维护。

如果您需要功能、错误修复或长期支持，我们建议：
1. **Fork 此仓库**供您自己使用
2. **创建您自己的维护版本**
3. **提交拉取请求**（如有可能会审查，但不保证时间）

贡献到此仓库：
1. Fork 仓库
2. 创建功能分支
3. 进行更改
4. 手动测试您的更改
5. 提交拉取请求

**注意**：本项目目前没有自动化测试。请在提交前手动测试您的更改。

## 支持

**⚠️ 有限支持**：本项目按现状提供，支持有限。

对于问题和疑问：
- **首先尝试自己 fork 和修复问题** - 这是推荐的方法
- 检查现有的 GitHub 问题，看看您的问题是否已被报告
- 对于 API 相关问题，请查看 https://context7.com 的 Context7 文档
- 仅对关键错误开启 GitHub 问题，但请期待有限的响应

**对于商业或关键任务使用，我们强烈建议 fork 此仓库并维护您自己的版本。**

## 项目链接

- 仓库：https://github.com/jussker/mcp_server_context7
- 问题反馈：https://github.com/jussker/mcp_server_context7/issues

## 文档

- [English README](README.md)
- [中文 README](README.zh.md)
