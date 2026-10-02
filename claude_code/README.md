# DataAI — Claude Code 后端接入

DataAI 支持三个**并列**的 agent 后端，在终端窗口直接启动：

| 后端 | 启动命令 | 定位 |
|---|---|---|
| **OpenClaw**（默认） | `openclaw chat` | 嵌入模式、`baidu-search` skill、`agent-browser` 等专属工具 |
| **DeepSeek Harness / DSH** | `dsh --profile dsh-tui`（别名 `dsh-tui`/`dst`） | DeepSeek 原生 harness、信创、国产模型直连 |
| **Claude Code** | `claude`（在仓库目录） | Anthropic CLI，接入国内 LLM（DeepSeek 等），Vibe Coding |

三者共用同一对 MCP Server（`jupyter-mcp` + `r-session`）。在 RStudio 或 JupyterLab 里开一个终端窗口，跑对应命令即可。

## 1. 为什么用 Claude Code

- Anthropic 官方 CLI（`claude`），成熟的 agentic coding 体验、子代理并行、项目级 `CLAUDE.md` 指令。
- 可通过 `ANTHROPIC_BASE_URL` / `ANTHROPIC_MODEL` 等 env 接入国内 LLM（DeepSeek 官方 Anthropic 兼容层），适合配合 OpenClaw 使用。
- 与 OpenClaw / DSH 平级，复用同一对 MCP Server（jupyter-mcp + r-session），不改 MCP Server 核心逻辑。

## 2. 前提

- 已安装 Claude Code CLI（`claude`），并把模型指向国内 LLM（见 `~/.claude/settings.json` 的 `env` 段）。
- Python：含 `mcp`、`jupyter-client` 的环境（本仓库 MCP server 的 shebang 指向 graphrag conda env）。
- R（`httpuv`、`jsonlite`）+ RStudio Server。

## 3. 配置 LLM（settings.json）

Claude Code 通过 `~/.claude/settings.json` 的 `env` 段接入 LLM（默认 DeepSeek 官方 Anthropic 兼容层）：

```bash
# 复制模板，替换 <YOUR_API_KEY>（若已有 settings.json，只需替换 env.ANTHROPIC_AUTH_TOKEN）
cp claude_code/settings.json.template ~/.claude/settings.json
chmod 600 ~/.claude/settings.json
```

模板内容（`claude_code/settings.json.template`）：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "<YOUR_API_KEY>",
    "ANTHROPIC_MODEL": "deepseek-v4-pro",
    "...": "其余 ANTHROPIC_*_MODEL 均为 deepseek-v4-pro"
  }
}
```

### LLM 占位符说明

| 占位符 | 说明 |
|---|---|
| `<YOUR_API_KEY>` | 你的 LLM API key（默认 DeepSeek 官方 key） |

换 provider（GLM / MiniMax / Kimi / 国产满血版等）：改 `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` + 各 `ANTHROPIC_*_MODEL` 即可。多 provider 由用户自配，不随仓库发布。

> ⚠️ `ANTHROPIC_AUTH_TOKEN` 是敏感值：**只写在本地 `~/.claude/settings.json`**，**不入库**。模板里的 `<YOUR_API_KEY>` 只是占位符。

## 4. 配置 MCP Server

MCP Server 用 stdio 模式（多用户安全，见 `jupyter_mcp/README.md`）。两种挂载方式：

### 方式 A：用户级 `~/.claude.json`（推荐，任何目录启动都生效）

```bash
# jupyter-mcp（无密钥）
claude mcp add -s user jupyter-mcp <PYTHON> <REPO_PATH>/jupyter_mcp/jupyter-mcp-server.py

# r-session（含 R_API_TOKEN，必须显式写在 env 里）
claude mcp add -s user r-session \
  -e R_API_HOST=127.0.0.1 \
  -e "R_API_PORT=<R_API_PORT>" \
  -e "R_API_TOKEN=<R_API_TOKEN>" \
  -e R_API_TIMEOUT=300 \
  -e "NO_PROXY=127.0.0.1,localhost" \
  -e "no_proxy=127.0.0.1,localhost" \
  -- <PYTHON> <REPO_PATH>/r-session-ai/r-session-mcp-server.py
```

### 方式 B：项目级 `.mcp.json`（切到仓库目录后自动加载）

把本目录的 `mcp.json.template` 复制为仓库根 `.mcp.json`，替换占位符即可。首次 `claude` 启动会提示批准（approve）该 server。

### 占位符说明

| 占位符 | 说明 | 示例 |
|---|---|---|
| `<PYTHON>` | 含 mcp/httpx 的 Python | `/usr/lib64/anaconda3/envs/graphrag/bin/python3` |
| `<REPO_PATH>` | DataAI 仓库绝对路径 | `/home/ubuntu/dataai_with_jupyterlab_and_rstudio` |
| `<R_API_PORT>` | R API 端口（与 RStudio 里 `options(rsession_api_port=...)` 一致） | `"8226"`（**保留引号**） |
| `<R_API_TOKEN>` | R API token（与 `options(rsession_api_token=...)` 一致） | 用 `secrets.token_urlsafe(24)` 生成 |

> ⚠️ `R_API_TOKEN` 是敏感值：**只写在本地配置**（`~/.claude.json` 或 gitignored 的 `.mcp.json`），**不入库**。本模板里的 `<R_API_TOKEN>` 只是占位符。

## 5. 启动 R API Server（R 侧）

在 RStudio Console 中：

```r
options(rsession_api_port = 8226)      # 与配置的 R_API_PORT 一致
options(rsession_api_token = "<token>")# 与配置的 R_API_TOKEN 一致
source("r-session-ai/r-session-api.R")
```

## 6. 使用

1. 在 JupyterLab 里 `from jupyter_mcp import hook; hook.register()` 注册 kernel。
2. 在仓库目录（`<REPO_PATH>`）打开终端，运行 `claude`。
3. Claude Code 里 MCP 工具名为 `mcp__jupyter-mcp__*` / `mcp__r-session__*`（比 OpenClaw 的 `jupyter-mcp__*` 多 `mcp__` 前缀）。

## 7. 验证

```bash
# 列出并健康检查已配置的 MCP server（应看到 jupyter-mcp 与 r-session 均 connected）
claude mcp list

# 进 Claude Code 后应能调 mcp__jupyter-mcp__run_code 执行 Python、mcp__r-session__run_code 执行 R
claude
```

## 8. 项目级 CLAUDE.md

仓库根 `CLAUDE.md` 是本后端的 persona/操作指南（对应 DSH 的 `dsh/AGENTS.md`、OpenClaw 的 `openclaw/MEMORY.md`）。Claude Code 在仓库目录启动时自动加载，无需手动拷贝。
