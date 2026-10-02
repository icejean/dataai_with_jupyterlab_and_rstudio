# DataAI 第三方 Agent 后端 DIY 接入指南

> 面向想自己动手接入新 Coding Agent 的用户。只要你的 Agent 支持 **MCP client**，就能把它接到 DataAI 上当「AI 大脑」用，无需改任何 MCP Server 核心逻辑。

候选清单见 [agent-backend-todo.md](agent-backend-todo.md)。

## 0. 为什么能 DIY

DataAI 的「AI 大脑」是插拔式的。三个内置后端（OpenClaw / DSH / Claude Code）和你想接的任何一个第三方 Agent，本质都是 **MCP client**——它们通过 MCP 协议调用 DataAI 暴露的两个 **stdio** MCP Server：

| MCP Server | 用途 | 通信 |
|---|---|---|
| `jupyter-mcp` | 执行 Python、导出/导入数据 | stdio → ZMQ 直连 Jupyter Kernel |
| `r-session` | 执行 R、导出/导入数据 | stdio → HTTP 调 R API（httpuv） |

所以：**Agent 只负责对话和调 MCP 工具；Python/R 跑在哪、怎么跑，完全由 MCP Server 决定，与接哪个 Agent 无关。** 这正是可以 DIY 的原因。

> **核心约束（不可改）：** RStudio Server 与 JupyterHub/JupyterLab 运行在 **Linux 服务器**上。DIY 时只换「AI 大脑」，两个分析引擎与 MCP Server 不变。

## 1. 判断你的 Agent 能不能接

三个条件，全满足即可：

1. **支持 MCP client**——能添加「本地 stdio MCP server」（命令 + 参数 + 环境变量）
2. **能接国内 LLM**——自带国产模型，或能配 endpoint 指向 DeepSeek / GLM / Kimi / MiniMax / 通义等
3. **能跑在 Linux 服务器**——TUI 或 GUI 均可，GUI 也要能装/跑在服务器上

> TUI 还是 GUI 不重要，能调 MCP Server 就行。但 RStudio 和 JupyterHub/JupyterLab 必须跑在 Linux 服务器上——这条是 DataAI 的核心要求，DIY 时不变。

## 2. 前置：先让 MCP 那侧就绪

接入任何 Agent 之前，先把 DataAI 两个 MCP Server 的依赖侧跑起来（与现有后端完全一致）：

```python
# JupyterLab 某个 cell 里：注册 kernel
from jupyter_mcp import hook
hook.register()
```

```r
# RStudio Console 里：启动 R API
options(rsession_api_port = 8226)        # 端口，与下面配置的 <R_API_PORT> 一致
options(rsession_api_token = "<token>")  # 用 secrets::? 见下，与 <R_API_TOKEN> 一致
source("r-session-ai/r-session-api.R")
```

```python
# 生成 token（Python 环境）
import secrets; secrets.token_urlsafe(24)
```

## 3. 通用三步（任何 Agent 都适用）

### 第一步：装 Agent

| 后端 | 安装命令 | 验证 |
|---|---|---|
| Qwen Code | `npm install -g @qwen-code/qwen-code` | `qwen --version` |
| Kimi Code CLI | `pip install kimi-cli`（或 `uv tool install kimi-cli`） | `kimi --version` |
| MiniMax Code CLI | `curl -fsSL https://filecdn.minimax.chat/public/install.sh \| bash` | `mcode --version` |
| CodeBuddy Code CLI | `npm install -g @tencent-ai/codebuddy-code`（Node ≥ 18.20） | `codebuddy --version` |
| MiMo-Code | `npm i -g @xiaomi-mimo/cli` 或 `curl -fsSL https://mimo.xiaomi.com/install \| bash` | `mimo --version` |
| Qoder CN CLI | 阿里云灵码官方文档安装 | `qoderclicn --help` |

> 各后端安装命令迭代较快，以上以官方文档为准。安装后先确认命令在 `$PATH` 中、用**绝对路径**调用解释器。

### 第二步：配 LLM（指向国内模型）

把 Agent 的模型指向国内 LLM。各 Agent 方式不同（env、`login`、配置向导），但都遵循同一原则：

- **token 只写本地配置文件，`chmod 600`，不入库**，仓库模板里只留 `<YOUR_API_KEY>` 占位符
- 换 provider 只改 endpoint + token + model 三个值

以 DeepSeek 官方 Anthropic 兼容层为例（部分 Agent 支持 `ANTHROPIC_BASE_URL` 类机制）：

| 项 | 值 |
|---|---|
| Base URL | `https://api.deepseek.com/anthropic` |
| Model | `deepseek-v4-pro` |
| API Key | `<YOUR_API_KEY>`（DeepSeek 官方 key） |

其余（GLM / MiniMax / Kimi / 国产满血版）同理替换 endpoint + token + model。

### 第三步：配 MCP（核心，DataAI 特有的唯一步骤）

把下面两个 stdio server 挂到你的 Agent。**这是 DataAI 特有的配置，其余步骤都是该 Agent 自带的通用玩法。**

标准 stdio 配置（JSON，占位符见下表）：

```json
{
  "mcpServers": {
    "jupyter-mcp": {
      "type": "stdio",
      "command": "<PYTHON>",
      "args": ["<REPO_PATH>/jupyter_mcp/jupyter-mcp-server.py"]
    },
    "r-session": {
      "type": "stdio",
      "command": "<PYTHON>",
      "args": ["<REPO_PATH>/r-session-ai/r-session-mcp-server.py"],
      "env": {
        "R_API_HOST": "127.0.0.1",
        "R_API_PORT": "<R_API_PORT>",
        "R_API_TOKEN": "<R_API_TOKEN>",
        "R_API_TIMEOUT": "300",
        "NO_PROXY": "127.0.0.1,localhost",
        "no_proxy": "127.0.0.1,localhost"
      }
    }
  }
}
```

占位符速查：

| 占位符 | 说明 | 示例 |
|---|---|---|
| `<PYTHON>` | 含 `mcp` / `jupyter-client` / `httpx` 的 Python（graphrag conda 环境） | `/usr/lib64/anaconda3/envs/graphrag/bin/python3` |
| `<REPO_PATH>` | DataAI 仓库绝对路径 | `/home/ubuntu/dataai_with_jupyterlab_and_rstudio` |
| `<R_API_PORT>` | 与 R 侧 `options(rsession_api_port=...)` 一致 | `"8226"`（**保留引号**） |
| `<R_API_TOKEN>` | 与 `options(rsession_api_token=...)` 一致 | `secrets.token_urlsafe(24)` 生成 |

> ⚠️ `<R_API_TOKEN>` 与 `<YOUR_API_KEY>` 是敏感值：**只写本地配置，不入库**。模板只留占位符。

## 4. 各后端「配置落点 + 一条命令」速查

标准 JSON 里 `mcpServers` 的内容各家通用，差别只在**塞进哪个文件**、以及**是否提供 CLI add 命令**。

### 4.1 Qwen Code（阿里通义）

- 配置文件：`~/.qwen/settings.json`（user，全局）/ `.qwen/settings.json`（project，项目根）
- CLI 添加（stdio 是默认传输，可省 `-t stdio`；`--` 之后是 server 命令本身）：

```bash
# jupyter-mcp（无密钥）
qwen mcp add -s user jupyter-mcp <PYTHON> <REPO_PATH>/jupyter_mcp/jupyter-mcp-server.py

# r-session（带 env，用 -e 逐个注入）
qwen mcp add -s user r-session <PYTHON> <REPO_PATH>/r-session-ai/r-session-mcp-server.py \
  -e R_API_HOST=127.0.0.1 -e R_API_PORT=<R_API_PORT> -e R_API_TOKEN=<R_API_TOKEN> \
  -e R_API_TIMEOUT=300 -e NO_PROXY=127.0.0.1,localhost -e no_proxy=127.0.0.1,localhost
```

- 验证：`qwen mcp list`；进入 TUI 后 `/mcp` 看连接状态。

### 4.2 Kimi Code CLI（月之暗面）

- 配置文件：`~/.kimi-code/mcp.json`（user）/ `.kimi-code/mcp.json`（project，优先）
- CLI 添加（stdio 本地进程）：

```bash
kimi mcp add --transport stdio jupyter-mcp -- <PYTHON> <REPO_PATH>/jupyter_mcp/jupyter-mcp-server.py
kimi mcp add --transport stdio r-session -- <PYTHON> <REPO_PATH>/r-session-ai/r-session-mcp-server.py
```

- r-session 的 env（`R_API_TOKEN` 等）建议直接编辑 `mcp.json` 的 `env` 字段（CLI 对 env 的支持有限）。
- 验证：`kimi mcp list`；TUI 内 `/mcp`。

### 4.3 MiniMax Code CLI（MiniMax）

- 配置文件：`~/.minimax/mcp.json`（数据根目录可用 `MINIMAX_DATA_DIR` 切换）
- 无独立 CLI add 命令，直接编辑 `mcp.json`，把 §3 的标准 `mcpServers` 对象粘进去即可（`type: "stdio"` 的 `command`/`args`/`env` 字段一致）
- 验证：`mcode mcp list`；TUI 内 `/mcp`、`/status`。

### 4.4 CodeBuddy Code CLI（腾讯）

- 配置文件：`~/.codebuddy.json`（user）/ `<项目根>/.mcp.json`（project）
- CLI 添加（`--` 之后写启动命令）：

```bash
codebuddy mcp add --scope user jupyter-mcp -- <PYTHON> <REPO_PATH>/jupyter_mcp/jupyter-mcp-server.py
codebuddy mcp add --scope user r-session -- <PYTHON> <REPO_PATH>/r-session-ai/r-session-mcp-server.py
```

- r-session 的 env 建议用 `add-json` 或直接编辑 JSON（支持 `${VAR}` 环境变量展开）。
- 验证：交互模式 `/mcp`。

### 4.5 MiMo-Code（小米）

- 配置文件（官方 `@xiaomi-mimo/cli`）：`.mimocode/mimocode.jsonc`（project）/ `~/.config/mimocode/mimocode.jsonc`（全局）
- 官方用 `mcp` 键（非 `mcpServers`）、`type: "local"`、`command` 为数组：

```jsonc
{
  "mcp": {
    "jupyter-mcp": {
      "type": "local",
      "command": ["<PYTHON>", "<REPO_PATH>/jupyter_mcp/jupyter-mcp-server.py"]
    },
    "r-session": {
      "type": "local",
      "command": ["<PYTHON>", "<REPO_PATH>/r-session-ai/r-session-mcp-server.py"],
      "env": {
        "R_API_HOST": "127.0.0.1",
        "R_API_PORT": "<R_API_PORT>",
        "R_API_TOKEN": "<R_API_TOKEN>",
        "R_API_TIMEOUT": "300"
      }
    }
  }
}
```

- CLI 也有 `mimo mcp add` / `mimo mcp list`。
- ⚠️ 已知问题：MCP 配置偶会误读 Claude Code/Cursor 等其他工具的配置（GitHub issue #76），接入后务必用 `mimo mcp list` 实测确认。
- 注意区分：官方 `@xiaomi-mimo/cli`（命令 `mimo`）与第三方 `mimo-tui`（`npm i -g mimo-tui`，配置在 `~/.mimo-code/config.json`）是两个东西。

### 4.6 Qoder CN CLI（阿里通义灵码）

- 通义灵码商用闭源 CLI，TUI / print（`-p`）/ `mcp serve` 三种模式，MCP 配置方式以官方文档为准。
- 与 Qwen Code 同门，若追求开源可优先选 4.1 的 Qwen Code。

## 5. 验证

配完 MCP 后，每个 Agent 都有「列出 MCP 状态」的入口（`mcp list` 或 TUI 内 `/mcp`），应看到 `jupyter-mcp` 与 `r-session` 均 **connected**。

最终验收：让 Agent 各执行一次

- Python：调用 `jupyter-mcp` 的 `run_code` 执行 `1+1`（或 `import pandas`）
- R：调用 `r-session` 的 `run_code` 执行 `1+1`（或 `data.frame()`）

两边都能跑通、且结果回显在 Jupyter Kernel / RStudio Console，即接入成功。

> 工具名可能带前缀（如 Claude Code 是 `mcp__jupyter-mcp__run_code`），以各 Agent 的 `/mcp`（或 `/tools`）实际显示为准。

## 6. 安全清单

- **token 只写本地、`chmod 600`、不入库**；仓库模板一律留 `<R_API_TOKEN>` / `<YOUR_API_KEY>` 占位符
- MCP Server 用 **stdio 模式**（多用户安全，见 `jupyter_mcp/README.md`），不要改成监听网络端口
- R API Token 通过 `options()` 设在 R 内存中，不落盘
- 注意代理环境变量：`ALL_PROXY=socks5` 会导致 r-session 的 httpx 崩溃，MCP Server 已自动清理；手工调试可 `unset ALL_PROXY http_proxy https_proxy`

## 7. 接入完成后：贡献回仓库

对齐 `claude_code/` 的三件套，把新后端沉淀回 DataAI 仓库：

1. `<backend>/README.md` —— 安装 / 配置 / 启动 / 验证
2. `<backend>/mcp.json.template` —— 占位符脱敏（对应 `claude_code/mcp.json.template`）
3. `<backend>/persona 模板` —— 对应 DSH 的 `dsh/AGENTS.md`、OpenClaw 的 `openclaw/MEMORY.md`

完成后在 [agent-backend-todo.md](agent-backend-todo.md) 里把对应行勾选为 ✅。

## 参考

- 现有后端接入范例：[claude_code/README.md](../claude_code/README.md) · [dsh/README.md](../dsh/README.md)
- 各后端 MCP 官方文档：见候选清单各行的官方链接
