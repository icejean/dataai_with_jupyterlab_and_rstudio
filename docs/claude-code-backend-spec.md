# Claude Code 后端接入 SPEC — DataAI（开源）

> 状态：已实现（2026-10-02）
> 关联：本仓库 `openclaw/MEMORY.md`、`dsh/AGENTS.md`、`claude_code/`、`CLAUDE.md`；参考 `docs/dsh-backend-spec.md`（DSH 后端接入，同构）

## 1. 背景与目标

DataAI 已支持 **OpenClaw**（默认）与 **DSH**（`dsh --profile dsh-tui`）两个并列 agent 后端。本 SPEC 增加 **Claude Code**（Anthropic 官方 CLI）作为**第三个并列后端**：

- 成熟的 agentic coding CLI：子代理并行、项目级 `CLAUDE.md` 指令、`/compact` 上下文压缩等。
- 可通过 `ANTHROPIC_BASE_URL` / `ANTHROPIC_MODEL` 等 env 接入国内 LLM（DeepSeek 官方 Anthropic 兼容层）。
- 与 OpenClaw / DSH 平级，复用**同一对 MCP Server**（jupyter-mcp + r-session），不改 MCP Server 核心逻辑。

**使用方式**：DataAI 通过终端窗口使用 AI 辅助——OpenClaw 跑 `openclaw chat`、DSH 跑 `dsh --profile dsh-tui`、Claude Code 在仓库目录跑 `claude`，**无 env 切换**。

## 2. 现状盘点（已核实）

### 2.1 MCP Server（源码在仓库，harness 无关）
| 组件 | 工具 | 通信 |
|---|---|---|
| `jupyter_mcp/jupyter-mcp-server.py` | 10 个：`run_code` `list_objects` `preview_data` `get_loaded_packages` `health_check` `read_source` `write_source` `append_source` `export_data` `import_data` | stdio MCP → ZMQ → Jupyter kernel |
| `r-session-ai/r-session-mcp-server.py` | 8 个：`list_objects` `preview_data` `get_object_info` `run_code` `get_loaded_packages` `health_check` `export_data` `import_data` | stdio MCP → HTTP → httpuv R API |

- 两 server 同名工具靠 **serverName 前缀**区分（OpenClaw：`jupyter-mcp__*` / `r-session__*`；DSH / Claude Code：`mcp__jupyter-mcp__*` / `mcp__r-session__*`）。
- `r-session-mcp-server.py` 读 env `R_API_HOST/PORT/TOKEN/TIMEOUT`；httpx timeout 由 `R_API_TIMEOUT` 控制（默认 30，DSH 接入时已改造成 env 可调）。

### 2.2 Claude Code 现状（已装，本机已验）
- Claude Code CLI 已装（本机 v2.1.220），模型经 `~/.claude/settings.json` 的 `env` 段指向 DeepSeek（`ANTHROPIC_BASE_URL` + `ANTHROPIC_MODEL`）。
- MCP 注册位置：`~/.claude.json`（user 级 `mcpServers`）或仓库根 `.mcp.json`（project 级）。
- 本机已实测：`jupyter-mcp` 与 `r-session` 均 `health_check` OK、`run_code('1+1')` 返回 `2`（R API 8226 token 认证通过）。

### 2.3 运行时（每用户，不入库）
- `~/.claude.json`：`mcpServers` 里 jupyter-mcp + r-session（r-session 的 `R_API_TOKEN` 为真值，0600）。
- 仓库根 `CLAUDE.md`：persona，Claude Code 在仓库目录启动时自动加载（**无需拷贝**，区别于 DSH 的 `~/.dsh/AGENTS.md`）。

## 3. 定位决策（已定）

- **并列**：OpenClaw / DSH / Claude Code 三个并列后端，终端各跑各的命令，无 env 切换。
- OpenClaw 保留（嵌入模式、`baidu-search`、`agent-browser` 等专属工具）；Claude Code 作为 Anthropic CLI 路径，三者共用同一对 MCP Server。
- **persona 分属**：OpenClaw 用 `openclaw/MEMORY.md`、DSH 用 `dsh/AGENTS.md`（拷到 `~/.dsh/`）、Claude Code 用仓库根 `CLAUDE.md`（随仓库走，自动加载）。

## 4. 总体架构

```
Claude Code (claude，仓库目录启动)
 ├─ mcp__jupyter-mcp__* (stdio) ─ jupyter-mcp-server.py ─ ZMQ ─ Jupyter kernel
 └─ mcp__r-session__*   (stdio) ─ r-session-mcp-server.py ─ HTTP ─ httpuv R API (R session)
```

- 工具名映射：OpenClaw `jupyter-mcp__run_code` → Claude Code / DSH `mcp__jupyter-mcp__run_code`。
- Claude Code 用内置 MCP 客户端（stdio），每个 server 一个子进程；user 级配置在 `~/.claude.json`，project 级在 `.mcp.json`。

## 5. 交付物

### 5.1 仓库新增（`~/dataai_with_jupyterlab_and_rstudio/`）
```
claude_code/
├── README.md                          # Claude Code 接入说明（安装/配置/启动/验证）
├── mcp.json.template                  # MCP 配置模板（占位符，脱敏）
└── settings.json.template             # LLM 配置模板（API key 占位符，脱敏）
CLAUDE.md                              # 项目级 persona（从 openclaw/MEMORY.md 改写，= dsh/AGENTS.md 的 Claude Code 版）
docs/claude-code-backend-spec.md       # 本文档
```

### 5.2 仓库改动
- 根 `README.md`：`双 Agent 后端` → `三 Agent 后端`；项目结构树加 `claude_code/`；后端选择表加 Claude Code 行；快速开始补 Claude Code 指引。
- 仓库 hygiene：`claude_code/mcp.json.template` 的 `R_API_TOKEN` 为 `<R_API_TOKEN>` 占位符、`claude_code/settings.json.template` 的 `ANTHROPIC_AUTH_TOKEN` 为 `<YOUR_API_KEY>` 占位符（均脱敏态），真值只在运行时 `~/.claude.json` / `~/.claude/settings.json`（本机，0600）。

### 5.3 运行时（每用户，不入库）
- `~/.claude.json`：`mcpServers` 真实配置（真 token）。
- `CLAUDE.md`：仓库内，随仓库走（无需拷贝到 `~/.claude/`）。

## 6. 关键设计点

### 6.1 MCP 配置（`mcpServers`，stdio 模式）
```json
{
  "mcpServers": {
    "jupyter-mcp": {
      "type": "stdio",
      "command": "/usr/lib64/anaconda3/envs/graphrag/bin/python3",
      "args": ["<REPO_PATH>/jupyter_mcp/jupyter-mcp-server.py"]
    },
    "r-session": {
      "type": "stdio",
      "command": "/usr/lib64/anaconda3/envs/graphrag/bin/python3",
      "args": ["<REPO_PATH>/r-session-ai/r-session-mcp-server.py"],
      "env": {
        "R_API_HOST": "127.0.0.1",
        "R_API_PORT": "8226",
        "R_API_TOKEN": "<R_API_TOKEN>",
        "R_API_TIMEOUT": "300",
        "NO_PROXY": "127.0.0.1,localhost",
        "no_proxy": "127.0.0.1,localhost"
      }
    }
  }
}
```

### 6.2 CLAUDE.md（静态 persona，随仓库走，不写 sync 脚本）
`CLAUDE.md` 从 `openclaw/MEMORY.md` 手写改写、提交到仓库根，Claude Code 在仓库目录启动时自动加载，**无需拷贝**（区别于 DSH 的 `dsh/AGENTS.md` → `~/.dsh/AGENTS.md`）。
- **改写要点**：`OpenClaw` → `Claude Code`；配置路径 `~/.openclaw/openclaw.json` → `~/.claude.json` / `.mcp.json`；R 脚本 workspace `~/.dsh/workspace/R/` → `~/.claude/workspace/R/`。
- **OpenClaw 专属段落剥离**：嵌入式模式限制、`agent-browser`、`baidu-search` skill、邮件处理——Claude Code 无对应实现，直接剥离。
- **继承 DSH 版沉淀的实战 gotcha**（与后端无关的环境知识）：Notebook 脏模型刷新、R 用 `SimSun`（Python 用 `SimHei`）不混用、RMariaDB BIGINT `integer64`、长输出 `run_with_sink.R` 落盘、变量名禁区、`run_code` 裸表达式不回显。
- **工具名**：Claude Code 下 MCP 工具为 `mcp__jupyter-mcp__*` / `mcp__r-session__*`；persona 不硬编码工具名，agent 靠运行时 listTools 发现。

### 6.3 R_API_TOKEN 敏感值处理（密文不入库）
- 仓库 `claude_code/mcp.json.template` 的 `R_API_TOKEN` 为 `<R_API_TOKEN>` 占位符；真值只在本机 `~/.claude.json`（0600）。
- R API Token 优先级：`options(rsession_api_token=...)` > 环境变量 `R_API_TOKEN` > 空（不启用）。
- 本机实测：R API 8226 开启 token 认证（无 token 返回 401），`~/.claude.json` 注入真值后 `health_check` 200。

### 6.4 两层超时（参考 Portal/DSH 教训）
- **服务端执行上限**：r-session 桥 httpx（→ `R_API_TIMEOUT` env，已设 `"300"`）；jupyter-mcp 自身 `JUPYTER_MCP_TIMEOUT`。
- **Claude Code 客户端超时**：本 SPEC 先对齐服务端 300s（模板已带 `R_API_TIMEOUT: "300"`）；Claude Code 的 MCP 工具调用客户端超时默认值未显式配置，长任务如需 >300s 需另行确认（属后续调优点，非本次阻塞项）。

### 6.5 代理环境变量
- r-session 经 HTTP 连 `127.0.0.1:8226`，配置里显式设 `NO_PROXY` / `no_proxy` 排除本机回环，避免被 `http_proxy` 等代理变量劫持（同 OpenClaw 配置）。

### 6.6 LLM 配置（密文不入库）
- 仓库默认只用 DeepSeek：`ANTHROPIC_BASE_URL` = `https://api.deepseek.com/anthropic`、`ANTHROPIC_MODEL` = `deepseek-v4-pro`；API key 在 `~/.claude/settings.json` 的 `env.ANTHROPIC_AUTH_TOKEN`。
- **多 provider 不随仓库发布**：需 GLM/MiniMax/Kimi 等自行改 `ANTHROPIC_BASE_URL` + 各 `ANTHROPIC_*_MODEL`（对齐 DSH §6.5 口径）。
- 模板 `claude_code/settings.json.template` 只放 `<YOUR_API_KEY>` 占位，真实 key 只在 `~/.claude/settings.json`（本机，0600）。

## 7. 验收标准

1. `claude mcp list` 显示 `jupyter-mcp` 与 `r-session` 均 connected（已验）。
2. Claude Code 内 `mcp__jupyter-mcp__run_code` 执行 Python、`mcp__r-session__run_code` 执行 R（R API 在 RStudio 起，端口 8226；本机已实测 `1+1` → `2`）。
3. 仓库目录启动 Claude Code 时 `CLAUDE.md` 自动加载为 DataAI persona（非 Portal）。
4. 长 R 任务不撞 30s 桥超时（`R_API_TIMEOUT=300` 生效）。
5. `R_API_TOKEN` 明文不进入仓库（`claude_code/mcp.json.template` 为占位符）。

## 8. 待拍板决策（均已定）

1. ~~并列 vs 替换~~ → **已定：并列**，仓库目录跑 `claude`，无 env 切换。
2. ~~CLAUDE.md 位置~~ → **已定：仓库根**（自动加载、随仓库走，无需拷贝）。
3. ~~MCP 配置位置~~ → **已定：user 级 `~/.claude.json`**（任何目录启动都生效）+ 项目级 `.mcp.json` 可选（见 `claude_code/README.md`）。
4. ~~R_API_TOKEN~~ → **已定：本机注入、不入库**，模板占位符脱敏。
5. ~~超时~~ → **已定：先对齐服务端 300s**，客户端超时后续调优。

## 9. 建议实现顺序（已完成）

1. ~~写入 `~/.claude.json` mcpServers（真 token 本机注入）~~ → **已做**。
2. ~~端到端验证（jupyter-mcp + r-session 的 health_check / run_code）~~ → **已做**（`1+1` → `2`）。
3. ~~`claude_code/` 模板 + README~~ → **已做**。
4. ~~仓库根 `CLAUDE.md` persona~~ → **已做**（继承 DSH 版 gotcha）。
5. ~~根 `README.md` 三后端 + 本文档~~ → **已做**。
