# DataAI — DeepSeek Harness (DSH) 后端接入（dsh-tui）

DataAI 支持三个**并列**的 agent 后端，在终端窗口直接启动（DSH 用 `dsh --profile dsh-tui`，可选自建 `dsh-tui`/`dst` 别名）：

| 后端 | 启动命令 | 定位 |
|---|---|---|
| **OpenClaw**（默认） | `openclaw chat` | 嵌入模式、`baidu-search` skill、`agent-browser` 等专属工具 |
| **DeepSeek Harness / DSH** | `dsh --profile dsh-tui`（别名 `dsh-tui`/`dst`） | DeepSeek 原生 harness、信创、国产模型直连 |
| **Claude Code** | `claude`（在仓库目录） | Anthropic CLI，接入国内 LLM、Vibe Coding；见 [claude_code/README.md](../claude_code/README.md) |

三者共用同一对 MCP Server（`jupyter-mcp` + `r-session`）。在 RStudio 或 JupyterLab 里开一个终端窗口，跑对应命令即可。

## 1. 为什么用 DSH

- DeepSeek 官方 harness（`@deepseek-ai/dsh`），原生 tool-calling、reasoning 模型。
- 交互式终端界面（`@deepseek-harness-tui/dsh-tui`），适配国内信创环境（麒麟 V10 + 鲲鹏 ARM + 国产 LLM）。
- OpenClaw 保留（嵌入模式、`baidu-search` skill、`agent-browser` 等专属工具），DSH 作为 DeepSeek 原生 / 信创路径。

## 2. 前提

- Node.js（实测 v24）+ **pnpm**（`dsh plugin add` 安装 profile 需要）。
- Python：含 `mcp`、`httpx` 的环境（本仓库 MCP server 的 shebang 指向 graphrag conda env）。
- R（`httpuv`、`jsonlite`）+ RStudio Server。

## 3. 安装 DSH

```bash
# ① 安装 DSH CLI（`dsh` 命令本身）
sudo npm install -g @deepseek-ai/dsh

# ② 以 plugin 方式安装 dsh-tui（避免全局安装时的包依赖冲突）
dsh plugin --profile dsh-tui add @deepseek-harness-tui/dsh-tui@0.11.1
```

`dsh plugin add` 会初始化 `~/.dsh/profiles/dsh-tui/`（生成 `package.json` / `cordis.yml` / 空的 `cordis.patch.yml`），并把包 hard-link 进 profile 的 `node_modules`。

> ⚠️ plugin 方式**不会**生成独立的 `dsh-tui` 二进制，启动用 `dsh --profile dsh-tui`（见 §6）。不要 `npm install -g @deepseek-harness-tui/dsh-tui`——会把整套依赖平铺进全局，易与其它全局包冲突。

## 4. 配置（`~/.dsh/`）

`dsh plugin add`（§3）已初始化 profile（生成 `package.json` / `cordis.yml` / 空的 `cordis.patch.yml`），直接填下面三份配置：

### ① profile patch（模型 + 两个 MCP server）

```bash
# 复制模板到 dsh-tui profile，替换 <...> 占位符（见下表）
cp dsh/profiles/dsh-tui/cordis.patch.yml.template ~/.dsh/profiles/dsh-tui/cordis.patch.yml
```

> `package.json` / `cordis.yml` 已由 `dsh plugin add` 自动生成，无需手动拷贝（仓库 `dsh/profiles/dsh-tui/` 里那份仅作结构参考）。

### ② 凭证（填入真实 key，chmod 600）

```bash
cp dsh/credentials.yaml.template ~/.dsh/.credentials.yaml
chmod 600 ~/.dsh/.credentials.yaml
```

### ③ persona（原样复制）

```bash
cp dsh/AGENTS.md ~/.dsh/AGENTS.md
```

### 占位符说明（`cordis.patch.yml`）

| 占位符 | 说明 | 示例 |
|---|---|---|
| `<REPO_PATH>` | DataAI 仓库绝对路径 | `/home/ubuntu/dataai_with_jupyterlab_and_rstudio` |
| `<PYTHON>` | 含 mcp/httpx 的 Python | `/usr/lib64/anaconda3/envs/graphrag/bin/python3` |
| `<R_API_PORT>` | R API 端口（与 RStudio 里 `options(rsession_api_port=...)` 一致） | `"8226"`（**保留引号**） |
| `<R_API_TOKEN>` | R API token（与 `options(rsession_api_token=...)` 一致） | 用 `secrets.token_urlsafe(24)` 生成 |
| `<HOME>` | 家目录绝对路径（`R2PY_SHARED_DIR` 用，`~` 不会被展开） | `/home/ubuntu` |

> ⚠️ `R_API_TOKEN` **必须显式写在 `cordis.patch.yml` 的 env 里**——DSH 会清洗掉父环境中匹配 `/KEY|PASSWORD|SECRET|TOKEN/i` 的变量，`R_API_TOKEN` 命中 `TOKEN`，只在显式配置里存活。

## 5. 启动 R API Server（R 侧）

在 RStudio Console 中：

```r
options(rsession_api_port = 8226)      # 与 cordis.patch.yml 的 R_API_PORT 一致
options(rsession_api_token = "<token>")# 与 cordis.patch.yml 的 R_API_TOKEN 一致
source("r-session-ai/r-session-api.R")
```

## 6. 使用

在 JupyterLab 里 `from jupyter_mcp import hook; hook.register()` 后，在 RStudio / JupyterLab 开一个终端窗口：

```bash
# OpenClaw
openclaw chat

# DSH（plugin 安装无独立二进制，用 profile 启动）
dsh --profile dsh-tui
```

plugin 方式没有 `dsh-tui` 命令，可自建别名方便敲（`~/.local/bin` 已在 PATH）：

```bash
cat > ~/.local/bin/dsh-tui <<'EOF'
#!/usr/bin/env bash
exec dsh --profile dsh-tui "$@"
EOF
chmod +x ~/.local/bin/dsh-tui
ln -sf dsh-tui ~/.local/bin/dst    # dst = 短别名
```

此后直接 `dsh-tui` 或 `dst`。

## 7. 验证

```bash
# 确认 profile compose 正确（应看到 agent-default-model + mcp-jupyter-mcp + mcp-r-session）
dsh --profile dsh-tui --dump-config

# 进 TUI 后应能调 mcp__jupyter-mcp__run_code 执行 Python、mcp__r-session__run_code 执行 R
dsh --profile dsh-tui    # 或别名 dsh-tui / dst
```

DSH 下 MCP 工具名为 `mcp__jupyter-mcp__*` / `mcp__r-session__*`（比 OpenClaw 多 `mcp__` 前缀）。

## 8. 多 provider（可选）

仓库默认只用 DeepSeek（`deepseek-official` + `deepseek-v4-flash`）。如需 GLM / MiniMax / 息壤 / LiteLLM 等，自行在 `~/.dsh/settings.yaml` 的 `llm-pi-ai:` 段添加 provider，并在 `~/.dsh/.credentials.yaml` 加对应 `*_API_KEY`（key 名须与 `apiKeyEnv` 一致）。DataAI 面向会写代码的专业数据分析师，多 provider 由用户自配，不随仓库发布。
