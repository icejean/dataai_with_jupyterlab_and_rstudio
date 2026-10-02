# DataAI Third-Party Agent Backend DIY Integration Guide

> For users who want to integrate a new coding agent themselves. As long as your agent supports **MCP client**, you can plug it into DataAI as the "AI Brain" — no changes to any MCP Server core logic required.

See the candidate checklist at [agent-backend-todo.en.md](agent-backend-todo.en.md).

## 0. Why DIY Works

DataAI's "AI Brain" is pluggable. The three built-in backends (OpenClaw / DSH / Claude Code) and any third-party agent you want to add are all fundamentally **MCP clients** — they call DataAI's two **stdio** MCP Servers via the MCP protocol:

| MCP Server | Purpose | Transport |
|---|---|---|
| `jupyter-mcp` | Run Python, export/import data | stdio → ZMQ direct to Jupyter Kernel |
| `r-session` | Run R, export/import data | stdio → HTTP to R API (httpuv) |

Therefore: **the agent only handles conversation and calling MCP tools; where and how Python/R runs is entirely decided by the MCP Server — not by which agent is plugged in.** That's exactly why DIY works.

> **Hard constraint (non-negotiable):** RStudio Server and JupyterHub/JupyterLab run on a **Linux server**. DIY only swaps the "AI Brain"; the two analysis engines and MCP Servers are unchanged.

## 1. Does Your Agent Qualify?

Three conditions, all must hold (**applies to both domestic and international backends**):

1. **MCP client support** — can add a "local stdio MCP server" (command + args + environment variables)
2. **LLM connectivity** — domestic or international models (built-in models, or a configurable endpoint pointing to DeepSeek / GLM / Kimi / MiniMax / Tongyi / OpenAI / Anthropic / Gemini, etc.)
3. **Runs on a Linux server** — TUI or GUI both fine; GUI must also be installable/runnable on the server

> TUI or GUI doesn't matter — being able to call MCP Servers does. But RStudio and JupyterHub/JupyterLab must run on a Linux server — that's DataAI's core requirement, unchanged during DIY.

### Why TUI Comes First

DataAI's workbench is the browser-based **JupyterLab + RStudio**, both of which ship a built-in **Terminal page** (JupyterLab's Terminal panel, RStudio Server's Terminal panel). A TUI agent launches directly in that embedded terminal: open the browser → go to the Terminal page → run `openclaw chat` / `dsh` / `claude` / any TUI agent you've plugged in — **no SSH client, desktop environment, or IDE plugin required**.

By contrast:

- **GUI / IDE agents** need a separate desktop or IDE — DataAI is a "server + browser" architecture with no desktop environment, so they don't fit naturally
- **pure headless CLIs** (only `-p` one-shot execution, no interactive TUI) work, but lack the interactive steering experience

That's why "TUI / CLI" form factors rank higher in the checklist — which is exactly why the three existing backends (OpenClaw / DSH / Claude Code) are all terminal-native.

## 2. Prerequisites: Get the MCP Side Ready First

Before integrating any agent, first start the dependency side of DataAI's two MCP Servers (identical to the existing backends):

```python
# In a JupyterLab cell: register the kernel
from jupyter_mcp import hook
hook.register()
```

```r
# In the RStudio Console: start the R API
options(rsession_api_port = 8226)        # port, must match <R_API_PORT> configured below
options(rsession_api_token = "<token>")  # must match <R_API_TOKEN>
source("r-session-ai/r-session-api.R")
```

```python
# Generate a token (Python environment)
import secrets; secrets.token_urlsafe(24)
```

## 3. Three Universal Steps (works for any agent)

### Step 1: Install the agent

| Backend | Install command | Verify |
|---|---|---|
| Qwen Code | `npm install -g @qwen-code/qwen-code` | `qwen --version` |
| Kimi Code CLI | `pip install kimi-cli` (or `uv tool install kimi-cli`) | `kimi --version` |
| MiniMax Code CLI | `curl -fsSL https://filecdn.minimax.chat/public/install.sh \| bash` | `mcode --version` |
| CodeBuddy Code CLI | `npm install -g @tencent-ai/codebuddy-code` (Node ≥ 18.20) | `codebuddy --version` |
| MiMo-Code | `npm i -g @xiaomi-mimo/cli` or `curl -fsSL https://mimo.xiaomi.com/install \| bash` | `mimo --version` |
| Qoder CN CLI | per Alibaba Cloud Lingma official docs | `qoderclicn --help` |
| OpenCode | `curl -fsSL https://opencode.ai/install \| bash` (or `npm i -g opencode-ai`) | `opencode --version` |
| Gemini CLI | `npm install -g @google/gemini-cli` | `gemini --version` |
| Goose | `brew install goose` (or the official install script) | `goose --version` |
| Codex CLI | `npm install -g @openai/codex` | `codex --version` |
| Crush | `brew install charmbracelet/tap/crush` | `crush --version` |

> Install commands iterate quickly; follow the official docs. After installing, confirm the command is in `$PATH` and call interpreters with **absolute paths**.

### Step 2: Configure the LLM (point to a domestic model)

Point the agent's model at a domestic LLM. Each agent does this differently (env, `login`, config wizard), but all follow the same principle:

- **token only in the local config file, `chmod 600`, never committed**; repo templates keep only the `<YOUR_API_KEY>` placeholder
- switching providers only changes endpoint + token + model

Using DeepSeek's official Anthropic-compatible layer as an example (some agents support an `ANTHROPIC_BASE_URL`-style mechanism):

| Item | Value |
|---|---|
| Base URL | `https://api.deepseek.com/anthropic` |
| Model | `deepseek-v4-pro` |
| API Key | `<YOUR_API_KEY>` (DeepSeek official key) |

Others (GLM / MiniMax / Kimi / full domestic models) follow the same pattern — replace endpoint + token + model.

### Step 3: Configure MCP (core — the only DataAI-specific step)

Mount the two stdio servers below into your agent. **This is the only DataAI-specific configuration; every other step is that agent's own generic setup.**

Standard stdio config (JSON; placeholders in the table below):

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

Placeholder quick reference:

| Placeholder | Description | Example |
|---|---|---|
| `<PYTHON>` | Python with `mcp` / `jupyter-client` / `httpx` (graphrag conda env) | `/usr/lib64/anaconda3/envs/graphrag/bin/python3` |
| `<REPO_PATH>` | Absolute path to the DataAI repo | `/home/ubuntu/dataai_with_jupyterlab_and_rstudio` |
| `<R_API_PORT>` | Must match the R-side `options(rsession_api_port=...)` | `"8226"` (**keep the quotes**) |
| `<R_API_TOKEN>` | Must match `options(rsession_api_token=...)` | generated via `secrets.token_urlsafe(24)` |

> ⚠️ `<R_API_TOKEN>` and `<YOUR_API_KEY>` are sensitive: **write them only to local config, never commit**. Templates keep only placeholders.

## 4. Per-Backend Quick Reference (config location + one command)

The `mcpServers` content from the standard JSON is universal; the only differences are **which file to put it in** and **whether a CLI `add` command exists**.

### 4.1 Qwen Code (Alibaba Tongyi)

- Config file: `~/.qwen/settings.json` (user, global) / `.qwen/settings.json` (project, repo root)
- CLI add (stdio is the default transport, `-t stdio` can be omitted; everything after `--` is the server command itself):

```bash
# jupyter-mcp (no secrets)
qwen mcp add -s user jupyter-mcp <PYTHON> <REPO_PATH>/jupyter_mcp/jupyter-mcp-server.py

# r-session (with env, inject each with -e)
qwen mcp add -s user r-session <PYTHON> <REPO_PATH>/r-session-ai/r-session-mcp-server.py \
  -e R_API_HOST=127.0.0.1 -e R_API_PORT=<R_API_PORT> -e R_API_TOKEN=<R_API_TOKEN> \
  -e R_API_TIMEOUT=300 -e NO_PROXY=127.0.0.1,localhost -e no_proxy=127.0.0.1,localhost
```

- Verify: `qwen mcp list`; inside the TUI, `/mcp` shows connection status.

### 4.2 Kimi Code CLI (Moonshot AI)

- Config file: `~/.kimi-code/mcp.json` (user) / `.kimi-code/mcp.json` (project, takes priority)
- CLI add (stdio local process):

```bash
kimi mcp add --transport stdio jupyter-mcp -- <PYTHON> <REPO_PATH>/jupyter_mcp/jupyter-mcp-server.py
kimi mcp add --transport stdio r-session -- <PYTHON> <REPO_PATH>/r-session-ai/r-session-mcp-server.py
```

- For r-session's env (`R_API_TOKEN` etc.), edit the `env` field in `mcp.json` directly (CLI env support is limited).
- Verify: `kimi mcp list`; `/mcp` inside the TUI.

### 4.3 MiniMax Code CLI (MiniMax)

- Config file: `~/.minimax/mcp.json` (data root can be switched via `MINIMAX_DATA_DIR`)
- No dedicated CLI add command — edit `mcp.json` directly and paste in the standard `mcpServers` object from §3 (the `type: "stdio"` `command`/`args`/`env` fields are identical)
- Verify: `mcode mcp list`; `/mcp`, `/status` inside the TUI.

### 4.4 CodeBuddy Code CLI (Tencent)

- Config file: `~/.codebuddy.json` (user) / `<repo root>/.mcp.json` (project)
- CLI add (the launch command goes after `--`):

```bash
codebuddy mcp add --scope user jupyter-mcp -- <PYTHON> <REPO_PATH>/jupyter_mcp/jupyter-mcp-server.py
codebuddy mcp add --scope user r-session -- <PYTHON> <REPO_PATH>/r-session-ai/r-session-mcp-server.py
```

- For r-session's env, use `add-json` or edit the JSON directly (supports `${VAR}` env expansion).
- Verify: `/mcp` in interactive mode.

### 4.5 MiMo-Code (Xiaomi)

- Config file (official `@xiaomi-mimo/cli`): `.mimocode/mimocode.jsonc` (project) / `~/.config/mimocode/mimocode.jsonc` (global)
- The official CLI uses the `mcp` key (not `mcpServers`), `type: "local"`, and `command` as an array:

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

- CLI also has `mimo mcp add` / `mimo mcp list`.
- ⚠️ Known issue: MCP config occasionally misreads other tools' config (Claude Code/Cursor etc., GitHub issue #76) — always confirm with `mimo mcp list` after integrating.
- Note the distinction: official `@xiaomi-mimo/cli` (command `mimo`) vs the third-party `mimo-tui` (`npm i -g mimo-tui`, config in `~/.mimo-code/config.json`) are two different things.

### 4.6 Qoder CN CLI (Alibaba Tongyi Lingma)

- Tongyi Lingma's commercial closed-source CLI with three modes — TUI / print (`-p`) / `mcp serve`; see official docs for MCP config.
- Same family as Qwen Code; prefer the open-source Qwen Code (4.1) if you want open source.

> 4.7–4.11 below are **international** backends. Commands and config formats iterate quickly — follow each official doc; the core is unchanged: put §3's stdio standard config into each tool's own config system.

### 4.7 OpenCode

- Config file: `~/.config/opencode/opencode.json` (global) / `opencode.json` in the repo root (project)
- Uses the `mcp` key (not `mcpServers`); `command` is an **array**, env uses `environment`:

```jsonc
{
  "mcp": {
    "jupyter-mcp": {
      "type": "local",
      "command": ["<PYTHON>", "<REPO_PATH>/jupyter_mcp/jupyter-mcp-server.py"],
      "enabled": true
    },
    "r-session": {
      "type": "local",
      "command": ["<PYTHON>", "<REPO_PATH>/r-session-ai/r-session-mcp-server.py"],
      "environment": {
        "R_API_HOST": "127.0.0.1",
        "R_API_PORT": "<R_API_PORT>",
        "R_API_TOKEN": "<R_API_TOKEN>",
        "R_API_TIMEOUT": "300"
      },
      "enabled": true
    }
  }
}
```

- Verify: `opencode mcp list`.

### 4.8 Gemini CLI

- Config file: `~/.gemini/settings.json` (user) / `.gemini/settings.json` (project), `mcpServers` key
- CLI add (stdio is the default transport):

```bash
gemini mcp add -s user jupyter-mcp <PYTHON> <REPO_PATH>/jupyter_mcp/jupyter-mcp-server.py
gemini mcp add -s user r-session <PYTHON> <REPO_PATH>/r-session-ai/r-session-mcp-server.py \
  -e R_API_HOST=127.0.0.1 -e R_API_PORT=<R_API_PORT> -e R_API_TOKEN=<R_API_TOKEN> -e R_API_TIMEOUT=300
```

- Verify: `gemini mcp list` or `/mcp` inside the TUI.

### 4.9 Goose

- Config file: `~/.config/goose/config.yaml`, `extensions` key; or interactively `goose configure` → Add Extension → Command-line Extension

```yaml
extensions:
  jupyter-mcp:
    cmd: <PYTHON>
    args: ["<REPO_PATH>/jupyter_mcp/jupyter-mcp-server.py"]
    type: stdio
    enabled: true
  r-session:
    cmd: <PYTHON>
    args: ["<REPO_PATH>/r-session-ai/r-session-mcp-server.py"]
    type: stdio
    envs:
      R_API_HOST: "127.0.0.1"
      R_API_PORT: "<R_API_PORT>"
      R_API_TOKEN: "<R_API_TOKEN>"
    enabled: true
```

- Verify: `goose configure` or `/mcp` inside the TUI.

### 4.10 Codex CLI

- Config file: `~/.codex/config.toml` (global) / `.codex/config.toml` (project), **only `[mcp_servers.<name>]` works** (TOML)

```toml
[mcp_servers.jupyter-mcp]
command = "<PYTHON>"
args = ["<REPO_PATH>/jupyter_mcp/jupyter-mcp-server.py"]

[mcp_servers.r-session]
command = "<PYTHON>"
args = ["<REPO_PATH>/r-session-ai/r-session-mcp-server.py"]

[mcp_servers.r-session.env]
R_API_HOST = "127.0.0.1"
R_API_PORT = "<R_API_PORT>"
R_API_TOKEN = "<R_API_TOKEN>"
R_API_TIMEOUT = "300"
```

- Verify: `codex mcp --help` or `/mcp` inside the TUI.

### 4.11 Crush

- Config file: `crush.json`, uses the `mcp` key (not `mcpServers`); also has a `crush mcp add` command
- stdio config structure is identical to §3's standard JSON (`command` / `args` / `env`), only the root key is `mcp`
- Verify: `crush mcp list` or `/mcp` inside the TUI.

## 5. Verification

After configuring MCP, every agent has a "list MCP status" entry point (`mcp list` or `/mcp` inside the TUI) — you should see both `jupyter-mcp` and `r-session` as **connected**.

Final acceptance: have the agent run each once

- Python: call `jupyter-mcp`'s `run_code` to execute `1+1` (or `import pandas`)
- R: call `r-session`'s `run_code` to execute `1+1` (or `data.frame()`)

Both succeed and results echo back in the Jupyter Kernel / RStudio Console — integration done.

> Tool names may carry a prefix (e.g. Claude Code uses `mcp__jupyter-mcp__run_code`); follow whatever each agent's `/mcp` (or `/tools`) actually displays.

## 6. Security Checklist

- **token only in local config, `chmod 600`, never committed**; repo templates keep only `<R_API_TOKEN>` / `<YOUR_API_KEY>` placeholders
- MCP Servers in **stdio mode** (multi-user safe, see `jupyter_mcp/README.md`); don't switch them to listening network ports
- R API Token is set in R memory via `options()`, never persisted to disk
- Watch proxy env vars: `ALL_PROXY=socks5` crashes r-session's httpx; the MCP Server auto-cleans them. For manual debugging, `unset ALL_PROXY http_proxy https_proxy`

## 7. After Integration: Contribute Back

Align with `claude_code/`'s three artifacts and commit the new backend back to the DataAI repo:

1. `<backend>/README.md` — install / config / launch / verify
2. `<backend>/mcp.json.template` — placeholders redacted (mirrors `claude_code/mcp.json.template`)
3. `<backend>/persona template` — mirrors DSH's `dsh/AGENTS.md` and OpenClaw's `openclaw/MEMORY.md`

When done, check off the corresponding row in [agent-backend-todo.en.md](agent-backend-todo.en.md).

## References

- Existing backend integration examples: [claude_code/README.md](../claude_code/README.md) · [dsh/README.md](../dsh/README.md)
- Official MCP docs for each backend: see the checklist links.
