# DataAI 第三方 Agent 后端接入清单

> 本文档跟踪「可选第三方 Coding Agent 后端」的 DIY 接入进度。核心结论：**任何支持 MCP client 的 Coding Agent 都能接入 DataAI**，TUI 还是 GUI 不重要，能调 MCP Server 即可。

## 背景

DataAI 现有三个**内置**后端，共用同一对 stdio MCP Server（`jupyter-mcp` + `r-session`）：

| 后端 | 启动命令 | 许可 |
|---|---|---|
| OpenClaw（默认） | `openclaw chat` | 开源 |
| DeepSeek Harness / DSH | `dsh --profile dsh-tui` | 开源 |
| Claude Code | `claude`（仓库目录） | 商业闭源（Anthropic） |

「AI 大脑」这一层是**插拔式**的：Agent 只负责对话 + 通过 MCP 协议调用 `jupyter-mcp`（执行 Python）与 `r-session`（执行 R）。Python/R 到底跑在哪、怎么跑，由 MCP Server 决定，与接哪个 Agent 无关。

> **核心约束（不可改）：** RStudio Server 与 JupyterHub/JupyterLab 必须运行在 **Linux 服务器**上。下面列出的候选，接入的只是最上层的「AI 大脑」，两个分析引擎与 MCP Server 均不变。

## 候选清单

图例：

- **许可**：开源 = 可自由集成到开源 DataAI 线；闭源免费 = 个人版免费、商业授权需另议
- **MCP 客户端**：能否添加本地 **stdio** MCP server（DataAI 的 MCP 是 stdio 模式）
- **优先级**：★★★ 强烈建议 / ★★☆ 可选 / ★☆☆ 观察
- **状态**：☐ 待 DIY 接入；接入完成（产出对齐 `claude_code/` 的三件套）后改为 ✅

### 国内

| 状态 | 后端 | 厂商 | 许可 | 形态 | MCP 客户端 | 国内 LLM | 优先级 | 指南 |
|---|---|---|---|---|---|---|---|---|
| ☐ | **Qwen Code** | 阿里通义 | 开源 Apache-2.0 | TUI / CLI | stdio·SSE·HTTP·OAuth | Qwen3-Coder（可 BYOK） | ★★★ | [§4.1](diy-backend-integration-guide.md#41-qwen-code阿里通义) |
| ☐ | **Kimi Code CLI** | 月之暗面 | 开源 Apache-2.0 | TUI（terminal-first） | stdio·HTTP·SSE | Kimi K2.5 / Moonshot | ★★★ | [§4.2](diy-backend-integration-guide.md#42-kimi-code-cli月之暗面) |
| ☐ | **MiniMax Code CLI** | MiniMax | 开源 MIT | TUI / Headless / ACP | stdio·http·streamable-http·sse | M3 + DeepSeek/Kimi/GLM 等 16 模型 | ★★☆ | [§4.3](diy-backend-integration-guide.md#43-minimax-code-climinimax) |
| ☐ | **CodeBuddy Code CLI** | 腾讯 | 闭源免费（个人版） | TUI / CLI | stdio·HTTP·SSE | 混元 + DeepSeek 等 | ★★☆ | [§4.4](diy-backend-integration-guide.md#44-codebuddy-code-cli腾讯) |
| ☐ | **MiMo-Code** | 小米 | 开源 MIT | TUI | local MCP | 小米 MiMo + 75+ 模型 | ★★☆ | [§4.5](diy-backend-integration-guide.md#45-mimo-code小米) |
| ☐ | **Qoder CN CLI** | 阿里通义灵码 | 闭源免费（个人版） | TUI / print / mcp serve | MCP（可反向当 server） | 通义灵码 | ★☆☆ | [§4.6](diy-backend-integration-guide.md#46-qoder-cn-cli阿里通义灵码) |
| ☐ | **ZCode CLI** | 智谱 | 待核实 | CLI / ACP | MCP tools | GLM | ★☆☆ | 待核实 |
| ☐ | **DeepSeek-TUI** | 社区（非官方） | 待核实 | TUI | MCP | DeepSeek | 观察 | 待核实 |

### 国外

| 状态 | 后端 | 厂商 | 许可 | 形态 | MCP 客户端 | 默认模型 / BYOK | 优先级 | 指南 |
|---|---|---|---|---|---|---|---|---|
| ☐ | **OpenCode** | opencode-ai（社区） | 开源 | TUI / CLI | local / remote MCP | 75+ 模型（BYOK） | ★★★ | [§4.7](diy-backend-integration-guide.md#47-opencode) |
| ☐ | **Gemini CLI** | Google | 开源 Apache-2.0 | TUI / CLI | stdio·SSE·HTTP | Gemini（免费额度，可 BYOK） | ★★☆ | [§4.8](diy-backend-integration-guide.md#48-gemini-cli) |
| ☐ | **Goose** | Block / Linux Foundation | 开源 Apache-2.0 | TUI / CLI | stdio（3000+ MCP 生态） | 多模型 | ★★☆ | [§4.9](diy-backend-integration-guide.md#49-goose) |
| ☐ | **Codex CLI** | OpenAI | 开源（Rust） | TUI / CLI | stdio·HTTP | GPT-5.x-Codex（可 BYOK） | ★★☆ | [§4.10](diy-backend-integration-guide.md#410-codex-cli) |
| ☐ | **Crush** | Charm | NOASSERTION | TUI | stdio·HTTP·SSE | 多模型 | ★☆☆ | [§4.11](diy-backend-integration-guide.md#411-crush) |
| ☐ | **Aider** | 开源社区 | Apache-2.0 | CLI | MCP（部分支持） | 多模型 | ★☆☆ | 待核实 |

> 国外后端同样遵循「支持 MCP client 即可接入」的判据。**OpenCode** 是 MiMo-Code 的上游（小米 MiMo 即其 fork），社区最活跃、BYOK 75+ 模型；**Gemini CLI** / **Goose** / **Codex CLI** 均开源且 MCP 成熟；**Crush**（Charm）终端体验最佳但许可为 NOASSERTION；**Aider** 偏 git-native、MCP 为部分支持。国外后端默认接国外模型，同样可 BYOK 指向国内 LLM（DeepSeek / GLM 等）。

## 优先级说明

1. **Qwen Code / Kimi Code CLI（★★★）**：开源、terminal-first、MCP client 成熟、`mcp add` 子命令齐全，形态最贴近现有 Claude Code 后端，接入成本最低；国内用户用本土账号/模型零门槛。
2. **MiniMax Code CLI（★★☆）**：MIT + **BYOK 一个 Key 调 16 个国产模型**，对「一条命令换模型」的中小组织用户有吸引力。
3. **CodeBuddy Code CLI（★★☆）**：腾讯自研、国内首家支持 MCP，但闭源（个人版免费），与开源 DataAI 线定位有张力，适合「不想开源、只要免费能用」的用户。
4. **MiMo-Code（★★☆）**：小米开源（OpenCode fork）、支持 75+ 模型，但较新，MCP 配置偶有读取其他工具配置的 bug（见 GitHub issue），接入需实测。
5. **Qoder CN CLI（★☆☆）**：通义灵码商用闭源，与 Qwen Code 同门（可优先选开源的 Qwen Code）。
6. **ZCode CLI / DeepSeek-TUI（待核实）**：前者智谱成熟度待核，后者为社区项目、非 DeepSeek 官方，接入前先核实维护者与稳定性。

## 完成接入的产出物（对齐现有后端）

每接入一个后端，产出与 `claude_code/` 一致的三个文件：

1. `<backend>/README.md` —— 安装 / 配置 / 启动 / 验证
2. `<backend>/mcp.json.template`（或该后端对应的配置模板）—— 占位符脱敏，不入库真实 token
3. `<backend>/persona 模板`（`AGENTS.md` / `CLAUDE.md` / 记忆文件，对应 DSH 的 `dsh/AGENTS.md`、OpenClaw 的 `openclaw/MEMORY.md`）—— 告诉 AI 如何驱动这套环境

> 具体动手步骤见 [DIY 接入指南](diy-backend-integration-guide.md)。
