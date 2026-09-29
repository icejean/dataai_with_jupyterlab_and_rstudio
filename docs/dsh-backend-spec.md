# DeepSeek Harness (DSH) 后端接入 SPEC — DataAI（开源）

> 状态：已验收（2026-09-29 修订：DSH 侧从 headless 改为 **dsh-tui**）
> 关联：本仓库 `openclaw/MEMORY.md`、`jupyter_mcp/`、`r-session-ai/`；Portal 参考 `docs/deepseek-harness-integration.md`

## 1. 背景与目标

DataAI 当前跑在 **OpenClaw** 上，DeepSeek 作为模型（`openai-completions` 兼容层，见 `openclaw.json`）。
本 SPEC 增加 **DSH**（`@deepseek-ai/dsh`，DeepSeek 官方 agent harness）作为**第二个 agent 后端**，适配国内信创环境：

- DeepSeek **原生 harness**（原生 tool-calling、reasoning 模型、国产模型直连）。
- 交互式终端界面 **dsh-tui**（`@deepseek-harness-tui/dsh-tui`）。
- 与 OpenClaw 平级，复用**同一对 MCP Server**（jupyter-mcp + r-session），不改 MCP Server 核心逻辑（仅 r-session 加一个超时 env）。

**使用方式**：DataAI 通过终端窗口使用 AI 辅助——OpenClaw 跑 `openclaw chat`、DSH 跑 `dsh-tui`，**无 wrapper、无 env 切换**（区别于 Portal 的 server 端 `AGENT_BACKEND` 后端服务）。

## 2. 现状盘点（已核实）

### 2.1 MCP Server（源码在仓库，harness 无关）
| 组件 | 工具 | 通信 |
|---|---|---|
| `jupyter_mcp/jupyter-mcp-server.py` | 10 个：`run_code` `list_objects` `preview_data` `get_loaded_packages` `health_check` `read_source` `write_source` `append_source` `export_data` `import_data` | stdio MCP → ZMQ → Jupyter kernel |
| `r-session-ai/` | 8 个：`list_objects` `preview_data` `get_object_info` `run_code` `get_loaded_packages` `health_check` `export_data` `import_data` | stdio MCP → HTTP → httpuv R API（R session 内） |

- 两 server 同名工具靠 **serverName 前缀**区分（OpenClaw：`jupyter-mcp__*` / `r-session__*`；DSH：`mcp__jupyter-mcp__*` / `mcp__r-session__*`）。
- `r-session-mcp-server.py` 读 env `R_API_HOST/PORT/TOKEN`、`MCP_PORT`、`R2PY_SHARED_DIR`；**httpx timeout 写死 30.0**（唯一要改的点）；启动时已清 6 个代理 env。

### 2.2 OpenClaw 配置切换（已就绪）
`~/.openclaw/` 下已有一套场景切换机制：
- `switch-config.sh <target-json>`：停 gateway → cp 目标 json → 同步 `.bak`/清 `.last-good`/删 sqlite last-known-good。
- 场景文件：`openclaw.dataai.json` / `openclaw.portal.json`；记忆：`MEMORY.DataAI.md` / `MEMORY.Portal.md`（`~/.openclaw/workspace/` 下）。
- 当前 DataAI 场景：MCP 指向仓库源码（`~/openclaw_with_jupyterlab_and_rstudio/...`），R 端口 8226。

### 2.3 DSH 现状（已装）
`~/.dsh/` 已就绪：`settings.yaml`（`llm-pi-ai:` 多 provider）、`.credentials.yaml`、`AGENTS.md`（persona，user-global）。**两个 profile 并存**：
- `profiles/headless/` = **Portal**（server 端一次性调用 `dsh --profile headless --session-id ...`）。
- `profiles/dsh-tui/` = **DataAI**（交互式 TUI，`dsh-tui`）。

全局装 `@deepseek-ai/dsh@0.1.2-rc.1` + `@deepseek-harness-tui/dsh-tui@0.11.1`；`dsh-tui` 首次运行自举 profile（内部 `dsh plugin --profile dsh-tui add ...`，需 pnpm）。

## 3. 定位决策（已定）

- **并列**：OpenClaw 与 DSH 是两个并列后端，用户在终端各跑各的命令（`openclaw chat` / `dsh-tui`），无需 wrapper、无需 env 切换——对齐「DataAI 通过终端窗口使用 AI 辅助」的用法。
- OpenClaw 保留（嵌入模式、`baidu-search` skill、`agent-browser` 等专属工具）；DSH 作为 DeepSeek 原生 / 信创路径，二者共用同一对 MCP Server。
- **profile 分属**：DataAI 用 `dsh-tui` profile、Portal 用 `headless` profile，两者 `cordis.patch.yml` 分属不同目录、互不干扰；唯一共享 `~/.dsh/AGENTS.md`（persona），用 `~/.dsh/switch-scene.sh <dataai|portal>` 切换（仅 swap AGENTS.md，对齐 `switch-config.sh` 语义）。

## 4. 总体架构

```
DSH (dsh-tui，交互式 TUI)
 ├─ mcp__jupyter-mcp__* (stdio) ─ jupyter-mcp-server.py ─ ZMQ ─ Jupyter kernel
 └─ mcp__r-session__*   (stdio) ─ r-session-mcp-server.py ─ HTTP ─ httpuv R API (R session)
```

- 工具名映射：`jupyter-mcp__run_code` → `mcp__jupyter-mcp__run_code`；`r-session__run_code` → `mcp__r-session__run_code`。
- DSH 用 `@deepseek-ai/dsh-mcp-client`（stdio，共享 `~/.dsh/profiles/node_modules`），每个 server 一个插件实例，`insert:` 包裹（id-targeted 叠加，直接写会当 override 报错）。
- profile 名 `dsh-tui`，bundle = `@deepseek-ai/dsh-base` + `@deepseek-harness-tui/dsh-tui`，`patchReload: live`（headless 是 `startup`）。

## 5. 交付物

### 5.1 仓库新增（`~/openclaw_with_jupyterlab_and_rstudio/`）
```
dsh/
├── README.md                          # DSH(dsh-tui) 接入说明（安装/配置/启动/验证）
├── AGENTS.md                          # 静态 persona（从 openclaw/MEMORY.md 改写，提交源码，用户自己拷贝）
├── profiles/dsh-tui/
│   ├── package.json                   # bundles: dsh-base + dsh-tui（参考，dsh-tui 自举可生成）
│   ├── cordis.yml                     # 空 []（参考）
│   └── cordis.patch.yml.template      # 模型 + 挂两个 MCP（占位符）
└── credentials.yaml.template          # 只放键名，无明文
docs/dsh-backend-spec.md               # 本文档
```
（**无 `dataai-agent`** —— 终端直接跑 `openclaw chat` / `dsh-tui`。）

### 5.2 仓库改动
- `r-session-ai/r-session-mcp-server.py`：`httpx.Client(timeout=30.0)` → `timeout=float(os.environ.get("R_API_TIMEOUT", "30"))`（默认 30，向后兼容）。
- 仓库 hygiene：
  - 仓库 `openclaw/openclaw.json` MCP 路径已改指仓库源码；`R_API_TOKEN` 为 x 占位符（脱敏态）。OpenClaw runtime 读 `~/.openclaw/openclaw.json`（= `~/.openclaw/openclaw.dataai.json` 的拷贝，真值在那里），repo `openclaw/openclaw.json` 不在 runtime 链上。
  - `mcp-examples/r-session.R`（连接示例：设 `options(rsession_api_port/token)` 后 source `r-session-api.R`）为占位符（脱敏态）并纳入跟踪；真 token 在 runtime `~/.openclaw/workspace/r-session.R`（Jean 从这里 source 拉起 R API）。连接示例三件套在 `mcp-examples/`：`r-session.R`（R 端）/ `test.py`（console 模式 `hook.register()`）/ `test.ipynb`（notebook 模式）。

### 5.3 运行时（每用户 `~/.dsh/`，不入库）
- `profiles/dsh-tui/cordis.patch.yml`：由模板生成真实 profile（填真实路径/端口/token）。
- `~/.dsh/AGENTS.md`：persona，user-global；`~/.dsh/switch-scene.sh` 切 DataAI/Portal persona（仅 swap AGENTS.md，profile 已分属无需切 cordis.patch.yml）。

## 6. 关键设计点

### 6.1 cordis.patch.yml（DataAI 场景，profile dsh-tui）
```yaml
# 模型：DeepSeek 官方（默认 deepseek-v4-flash）
- id: agent-default-model
  config:
    provider: deepseek-official
    model: deepseek-v4-flash

# MCP：jupyter-mcp（stdio），工具名 mcp__jupyter-mcp__*
- insert:
    - id: mcp-jupyter-mcp
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: jupyter-mcp
        transport: stdio
        command: /usr/lib64/anaconda3/envs/graphrag/bin/python
        args: [/home/ubuntu/openclaw_with_jupyterlab_and_rstudio/jupyter_mcp/jupyter-mcp-server.py]
        env: { R2PY_SHARED_DIR: "<HOME>/.dsh/workspace/r2py", JUPYTER_MCP_TIMEOUT: "300" }   # 见 6.4/6.6
        toolCallTimeoutMs: 300000

# MCP：r-session（stdio），工具名 mcp__r-session__*
- insert:
    - id: mcp-r-session
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: r-session
        transport: stdio
        command: /usr/lib64/anaconda3/envs/graphrag/bin/python
        args: [/home/ubuntu/openclaw_with_jupyterlab_and_rstudio/r-session-ai/r-session-mcp-server.py]
        # env 透传已支持（见 6.3；R_API_TOKEN 必须显式写在 env 里）
        env: { R_API_HOST: 127.0.0.1, R_API_PORT: "8226", R_API_TOKEN: "<TOKEN>", R_API_TIMEOUT: "300", R2PY_SHARED_DIR: "<HOME>/.dsh/workspace/r2py" }
        toolCallTimeoutMs: 300000
```

### 6.2 AGENTS.md（静态，手写提交，不写 sync 脚本）
`dsh/AGENTS.md` 是**静态 persona**，从 `openclaw/MEMORY.md` 手写改写、提交到源码；用户自己拷贝到 `~/.dsh/AGENTS.md`。DataAI 用户是专业数据分析师个人用户，自配无碍。
- **改写要点**：`OpenClaw`→`DeepSeek Harness`；`~/.openclaw/workspace`→`~/.dsh/workspace`；`~/.openclaw/openclaw.json`→`~/.dsh/profiles/dsh-tui/cordis.patch.yml`。
- **OpenClaw 专属段落剥离**：嵌入式模式限制、`agent-browser`、`baidu-search` skill、邮件处理——非数据分析场景必需、DSH 下无对应实现，直接剥离；保留通用知识与守则（整体定位、Python/R 用法、中文字体、R↔Python 交换、Claude Code CLI、R 端安全守则）。
- **工具名**：`openclaw/MEMORY.md` 不硬编码工具名（已核实），无需前缀替换；agent 靠 `listTools` 运行时发现。

### 6.3 r-session 的 env 透传（已 spike：支持）
`@deepseek-ai/dsh-mcp-client` 的 stdio 配置**支持 `env` 字段**（`StdioConfig.env: Record<string,string>`；`lib/index.js` `buildChildEnv()`）。
- 子进程 env = `scrubbedParentEnv()` + 配置 `env`（配置项叠加在清洗后的父 env 之上，显式覆盖存活）。
- ⚠️ 父 env 会清洗掉匹配 `/KEY|PASSWORD|SECRET|TOKEN/i` 与 `DSH_*` 的变量——`R_API_TOKEN` 属被清洗类，**必须显式写在 config `env` 里**（写在 env 里的会存活）。
- 结论：直接 `env: { R_API_HOST, R_API_PORT, R_API_TOKEN, R2PY_SHARED_DIR }`，无需 shell 包装。

### 6.4 两层超时（参考 Portal 文档 §4 教训）
- **服务端执行上限**：r-session 桥 httpx（→ `R_API_TIMEOUT` env）；jupyter-mcp 自身 `JUPYTER_MCP_TIMEOUT`。
- **DSH 客户端超时**：`toolCallTimeoutMs` 默认 60s，两个 MCP client 都要显式设 ≥ 服务端上限（长 ML 训练 / 大 data.table）。
- 原则：客户端超时**不得小于**服务端执行超时。模板已把 `R_API_TIMEOUT`/`JUPYTER_MCP_TIMEOUT` 都设为 `"300"`，与 `toolCallTimeoutMs: 300000` 对齐。

### 6.5 模型与凭证（密文不入库）
- 仓库默认只用 DeepSeek：`agent-default-model` = `deepseek-official` + `deepseek-v4-flash`，凭证 `.credentials.yaml` 只 `DEEPSEEK_API_KEY`。
- **多 provider 不随仓库发布**：DataAI 面向会写代码的专业数据分析师，需 GLM/MiniMax/星环等自行配 DSH 的 `settings.yaml`（`llm-pi-ai:`，`apiKeyEnv` 引用 key 名）——README 给一段参考即可（可借鉴 Portal `docs/dsh-multi-provider-config.md`）。
- 模板只放键名占位，真实密文只在 `~/.dsh/`（本机，0600）。

### 6.6 r2py 共享目录（已定：由后端 env 变量决定）
- MCP server 默认 `~/.openclaw/workspace/r2py` 保持不变（OpenClaw 向后兼容，不改代码）。
- DSH 场景在 `cordis.patch.yml` 两个 MCP client 的 env 里设 `R2PY_SHARED_DIR`（统一覆盖 r-session 的 `R_SHARED_DIR` 与 jupyter-mcp 的 `JUPYTER_SHARED_DIR`）指向 `~/.dsh/workspace/r2py`——DSH 用户可能没装 OpenClaw，没有 `~/.openclaw/workspace` 目录。
- ⚠️ `R2PY_SHARED_DIR` 的 `~` 不会被 MCP server 展开（`os.path.expanduser` 只作用于默认值），模板须用绝对路径（用户自填 `<HOME>`）。
- 两个 server 必须指向**同一目录**，R↔Python 交换才通。

## 7. 验收标准

1. dsh-tui 跑 DataAI 场景：`mcp__jupyter-mcp__run_code` 执行 Python、`mcp__r-session__run_code` 执行 R（R API 在 RStudio 起，端口 8226）。
2. persona 加载为 DataAI 场景（非 Portal）。
3. 长 R 任务不撞 30s 桥超时（`R_API_TIMEOUT` 生效）。
4. DataAI 与 Portal 的 DSH profile 分属（`dsh-tui` vs `headless`），persona 切换（`switch-scene.sh`）往返无残留。

## 8. 待拍板决策

1. ~~并列 vs 替换~~ → **已定：并列**，终端直接跑 `openclaw chat` / `dsh-tui`，无 wrapper、无 env 切换。
2. ~~AGENTS.md 生成方式~~ → **已定：静态 `dsh/AGENTS.md` 手写提交，不写 sync 脚本**。
3. ~~OpenClaw 专属段落~~ → **已定：剥离**（嵌入式模式/`agent-browser`/`baidu-search`/邮件，非数据分析必需）。
4. ~~r2py 共享目录~~ → **已定：由后端 env 决定**，DSH 设 `R2PY_SHARED_DIR` 到 `~/.dsh/workspace/r2py`。
5. ~~多 provider~~ → **已定：仓库默认只 DeepSeek**，多 provider 用户自配 DSH `settings.yaml`，不随仓库发布。
6. ~~headless vs tui~~ → **已定：tui（dsh-tui）**，DataAI 是终端交互式用法，非 Portal 的 server 端 headless。

## 9. 建议实现顺序（已完成）

1. ~~Spike 6.3（env 透传）~~ → **已做：env 支持，无需 shell 包装**。
2. ~~5.2 超时改造 + 6.4 两层超时配置~~ → **已做**（含模板补 `R_API_TIMEOUT`/`JUPYTER_MCP_TIMEOUT`）。
3. ~~5.1 `dsh/` 模板 + 静态 AGENTS.md~~ → **已做**（profile `dsh-tui`）。
4. ~~文档 + 验收~~ → **已做**（E2E 用 `dsh --profile dsh-tui --dump-config` 验证 compose；MCP 直连验证 Python/R 执行）。
