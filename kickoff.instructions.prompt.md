context7 MCP typescript 版本同步与迁移python版本指引

1. 环境准备
- 检查是否安装 `uv`；若无，运行：`curl -LsSf https://astral.sh/uv/install.sh | sh`
- 检查并激活 Python 虚拟环境：若无则创建并激活：`uv venv` 后 `source .venv/bin/activate`
- 同步项目依赖：`uv sync`

2. 获取参考实现
- 在项目根目录 clone 官方实现：`git clone https://github.com/upstash/context7.git upstash_context7`

3. 对齐实现
- 重点阅读并理解 `upstash_context7/packages/mcp` 下的 TypeScript 最新实现（多跳检索以把握所有相关模块）
- 将最新逻辑和接口对齐到 Python 实现 mcp_server_context7.py
- 规则：  
  - 不带历史包袱（无向后兼容负担），Python 只需与 TypeScript 行为和接口保持一致；  
  - 可按需调整模块/函数划分以符合 Python 风格，但语义和外部接口需一致。

4. 保留与规范化 Python 特性
- 保留 Python 版本中特有功能（例如：下载文件、同步克隆仓库等工具函数）
- 工具函数与模块的注释/文档风格应与现有 Python 代码一致（保持同一注释格式与语言风格）

5. 测试与校验
- 迁移完成后，检查 tests 下的测试用例覆盖范围，新增针对未覆盖逻辑的测试用例
- 运行测试：`pytest -v`，修复失败项直到通过

6. 提交与记录
- 测试通过后提交代码，建议提交信息模板：`chore(mcp): sync implementation with upstash/context7@<commit>`  
- 建议在新分支上完成（例如：`feat/mcp-sync-from-ts`），合并前进行 CI/复审

备注（简短提醒）
- 优先对齐行为与接口；内部实现可按 Python 最佳实践重构。  