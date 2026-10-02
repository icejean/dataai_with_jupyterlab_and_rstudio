# DataAI Third-Party Agent Backend Integration Checklist

> This document tracks DIY integration progress for **optional third-party coding-agent backends**. The core conclusion: **any coding agent with MCP client support can be integrated into DataAI** — TUI or GUI doesn't matter, as long as it can call MCP Servers.

## Background

DataAI ships with three **built-in** backends, all sharing the same pair of stdio MCP Servers (`jupyter-mcp` + `r-session`):

| Backend | Launch command | License |
|---|---|---|
| OpenClaw (default) | `openclaw chat` | Open source |
| DeepSeek Harness / DSH | `dsh --profile dsh-tui` | Open source |
| Claude Code | `claude` (in the repo directory) | Commercial closed-source (Anthropic) |

The "AI Brain" layer is **pluggable**: the agent only handles conversation + calling `jupyter-mcp` (run Python) and `r-session` (run R) via the MCP protocol. Where and how Python/R runs is decided by the MCP Server — not by which agent is plugged in.

> **Hard constraint (non-negotiable):** RStudio Server and JupyterHub/JupyterLab must run on a **Linux server**. The candidates below only replace the top "AI Brain" layer; the two analysis engines and MCP Servers are unchanged.

## Candidate Checklist

> The list below is **non-exhaustive and provided by way of example only** — it is not limited to the backends listed. Any coding agent with MCP client support can be integrated into DataAI; omission does not imply lack of support or fit. Feel free to integrate any unlisted backend via the [DIY Integration Guide](diy-backend-integration-guide.en.md).

Legend:

- **License**: Open source = freely integrable into the open-source DataAI line; closed-source free = free for personal use, commercial licensing requires separate negotiation
- **MCP client**: whether it can add a local **stdio** MCP server (DataAI's MCP is stdio mode)
- **Priority**: ★★★ strongly recommended / ★★☆ optional / ★☆☆ watch
- **Status**: ☐ pending DIY integration; change to ✅ once integrated (artifacts aligned with `claude_code/`)

### China / Domestic

| Status | Backend | Vendor | License | Form | MCP client | Domestic LLM | Priority | Guide |
|---|---|---|---|---|---|---|---|---|
| ☐ | **Qwen Code** | Alibaba Tongyi | Open source Apache-2.0 | TUI / CLI | stdio·SSE·HTTP·OAuth | Qwen3-Coder (BYOK) | ★★★ | [§4.1](diy-backend-integration-guide.en.md#41-qwen-code-alibaba-tongyi) |
| ☐ | **Kimi Code CLI** | Moonshot AI | Open source Apache-2.0 | TUI (terminal-first) | stdio·HTTP·SSE | Kimi K2.5 / Moonshot | ★★★ | [§4.2](diy-backend-integration-guide.en.md#42-kimi-code-cli-moonshot-ai) |
| ☐ | **MiniMax Code CLI** | MiniMax | Open source MIT | TUI / Headless / ACP | stdio·http·streamable-http·sse | M3 + DeepSeek/Kimi/GLM etc. (16 models) | ★★☆ | [§4.3](diy-backend-integration-guide.en.md#43-minimax-code-cli-minimax) |
| ☐ | **CodeBuddy Code CLI** | Tencent | Closed-source free (personal) | TUI / CLI | stdio·HTTP·SSE | Hunyuan + DeepSeek etc. | ★★☆ | [§4.4](diy-backend-integration-guide.en.md#44-codebuddy-code-cli-tencent) |
| ☐ | **MiMo-Code** | Xiaomi | Open source MIT | TUI | local MCP | Xiaomi MiMo + 75+ models | ★★☆ | [§4.5](diy-backend-integration-guide.en.md#45-mimo-code-xiaomi) |
| ☐ | **Qoder CN CLI** | Alibaba Tongyi Lingma | Closed-source free (personal) | TUI / print / mcp serve | MCP (can reverse as server) | Tongyi Lingma | ★☆☆ | [§4.6](diy-backend-integration-guide.en.md#46-qoder-cn-cli-alibaba-tongyi-lingma) |
| ☐ | **ZCode CLI** | Zhipu | TBD | CLI / ACP | MCP tools | GLM | ★☆☆ | TBD |
| ☐ | **DeepSeek-TUI** | Community (unofficial) | TBD | TUI | MCP | DeepSeek | Watch | TBD |

### International

| Status | Backend | Vendor | License | Form | MCP client | Default model / BYOK | Priority | Guide |
|---|---|---|---|---|---|---|---|---|
| ☐ | **OpenCode** | opencode-ai (community) | Open source | TUI / CLI | local / remote MCP | 75+ models (BYOK) | ★★★ | [§4.7](diy-backend-integration-guide.en.md#47-opencode) |
| ☐ | **Gemini CLI** | Google | Open source Apache-2.0 | TUI / CLI | stdio·SSE·HTTP | Gemini (free tier, BYOK) | ★★☆ | [§4.8](diy-backend-integration-guide.en.md#48-gemini-cli) |
| ☐ | **Goose** | Block / Linux Foundation | Open source Apache-2.0 | TUI / CLI | stdio (3000+ MCP ecosystem) | Multi-model | ★★☆ | [§4.9](diy-backend-integration-guide.en.md#49-goose) |
| ☐ | **Codex CLI** | OpenAI | Open source (Rust) | TUI / CLI | stdio·HTTP | GPT-5.x-Codex (BYOK) | ★★☆ | [§4.10](diy-backend-integration-guide.en.md#410-codex-cli) |
| ☐ | **Crush** | Charm | NOASSERTION | TUI | stdio·HTTP·SSE | Multi-model | ★☆☆ | [§4.11](diy-backend-integration-guide.en.md#411-crush) |
| ☐ | **Aider** | Open-source community | Apache-2.0 | CLI | MCP (partial) | Multi-model | ★☆☆ | TBD |

> International backends follow the same "MCP client support is enough" rule. **OpenCode** is MiMo-Code's upstream (Xiaomi's MiMo is a fork of it), the most active community with BYOK 75+ models; **Gemini CLI** / **Goose** / **Codex CLI** are all open source with mature MCP; **Crush** (Charm) has the best terminal experience but a NOASSERTION license; **Aider** is git-native with only partial MCP support. International backends default to international models, and can equally BYOK-point to domestic LLMs (DeepSeek / GLM, etc.).

## Portal Integration Assessment

> An extra dimension for the **closed-source DataAI Portal**. Portal drives agents as headless services (one process per request, multiple sessions, dynamic context), so beyond "MCP client support" it additionally requires five things:

1. **Headless / one-shot CLI launch** — Portal spawns a process per request, returns when done
2. **Resume by session ID** — Portal keeps sessions; each request passes an id to continue
3. **Cross-process conversation persistence** — the session is written to disk and resumable by a new process
4. **Dynamic context injection after resume** — inject DataAI's current kernel / language / workspace state
5. **MCP Server as a subprocess** — jupyter-mcp / r-session start with the agent and exit together

| Backend | ①headless | ②session-id resume | ③cross-process persist | ④dynamic inject | ⑤MCP subprocess | Verdict |
|---|---|---|---|---|---|---|
| **Kimi Code CLI** | ✅ | ✅ | ✅ | ✅ | ✅ | Top pick |
| **Goose** | ✅ | ✅ | ✅ | ✅ | ⚠️ | Top pick (intl) |
| **MiniMax Code CLI** | ✅ | ✅ | ✅ | ❓ | ✅ | Strong |
| **Qwen Code** | ✅ | ✅ | ✅ | ⚠️ | ✅ | Needs hook |
| **Codex CLI** | ✅ | ⚠️ | ✅ | ⚠️ | ✅ | Needs patch |
| **Gemini CLI** | ✅ | ❌ | ⚠️ | ⚠️ | ✅ | Not ready |
| **OpenCode** | ⚠️ | ⚠️ | ✅ | ⚠️ | ✅ | Needs hook dev |
| **MiMo-Code** | ❌ | ✅ | ✅ | ❌ | ⚠️ | Not ready |

> Tiering:
> - **Top picks**: Kimi Code CLI (①–⑤ native; `resume_hint` returns session_id + resume command, ideal for Portal's id→resume loop); Goose (④ uses `GOOSE_MOIM_MESSAGE_*` per-turn injection, the strongest dynamic context, but a known provider-layer bug can drop the system prompt)
> - **Strong**: MiniMax Code CLI (④ TBD), Qwen Code (④ via hook additionalContext), Codex CLI (④'s `model_instructions_file` is only read on new sessions, conflicting with post-resume injection — needs patch)
> - **Not ready**: Gemini CLI (no headless `--resume`), OpenCode / MiMo-Code (TUI-foreground + hook-dependent)
>
> Vs. DSH: session-id resume (②) is **native** in these open-source CLIs (`-r` / `--session` / `exec resume`) — no patch needed as with DSH; the real patch surface is **④ dynamic context injection** — only Goose (MOIM) and Kimi (`--system-prompt` / AGENTS.md) work out of the box, the rest (Qwen hook, Codex) need development.

## Priority Notes

1. **Qwen Code / Kimi Code CLI (★★★)**: open source, terminal-first, mature MCP client, full `mcp add` subcommands, closest to the existing Claude Code backend and cheapest to integrate; domestic users get zero-friction access with local accounts/models.
2. **MiniMax Code CLI (★★☆)**: MIT + **BYOK — one key drives 16 domestic models**, attractive to small/medium organizations that want "swap models with one command".
3. **CodeBuddy Code CLI (★★☆)**: Tencent's own, the first in China to support MCP, but closed-source (free for personal use) — some tension with the open-source DataAI line; suits users who "don't need open source, just something free that works".
4. **MiMo-Code (★★☆)**: Xiaomi open source (OpenCode fork), 75+ models, but newer with an occasional MCP config bug that reads other tools' config (see GitHub issue) — needs hands-on verification.
5. **Qoder CN CLI (★☆☆)**: Tongyi Lingma commercial closed-source, same family as Qwen Code (prefer the open-source Qwen Code).
6. **ZCode CLI / DeepSeek-TUI (TBD)**: the former needs Zhipu maturity verification; the latter is a community project, not official DeepSeek — verify maintainer and stability before integrating.

## Deliverables for a Completed Integration (aligned with existing backends)

For each integrated backend, produce three files matching `claude_code/`:

1. `<backend>/README.md` — install / config / launch / verify
2. `<backend>/mcp.json.template` (or the backend's own config template) — placeholders redacted, no real tokens committed
3. `<backend>/persona template` (`AGENTS.md` / `CLAUDE.md` / memory file, corresponding to DSH's `dsh/AGENTS.md` and OpenClaw's `openclaw/MEMORY.md`) — tells the AI how to drive this environment

> Step-by-step instructions: [DIY Integration Guide](diy-backend-integration-guide.en.md).
