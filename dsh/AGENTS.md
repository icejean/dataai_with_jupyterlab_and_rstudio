# AGENTS.md - DSH 长期记忆

> ⚠️ **此文件是 DeepSeek Harness (DSH) AI Agent 的长期记忆/操作指南**，不是给人看的项目文档。
> 它告诉 DSH（AI 代理）如何驱动 JupyterLab + RStudio 这套数据分析环境。
> 将本文件复制到 `~/.dsh/AGENTS.md`，DSH 每个 session 自动加载为基线上下文。

## 代码生成偏好
- 优先使用 **Claude Code** 生成代码（包括算法实现、全栈开发、脚本编写等）
- 默认编程语言：Python
- Python程序默认运行环境：Conda虚拟环境 `graphrag`
- Claude Code配置文件位置：`~/.claude/settings.json`
- **非交互式调用方式**（DSH 下用 tool-bash 执行）：

  ```bash
  # 最简单的非交互式调用
  echo '<prompt>' | claude --print --model deepseek-v4-pro

  # 允许写文件 + 读文件
  echo '<prompt>' | claude --print --model deepseek-v4-pro --allowedTools "Write,Bash,Read"

  # 沙箱环境（无网络，完全跳过权限确认）
  echo '<prompt>' | claude --print --model deepseek-v4-pro --dangerously-skip-permissions
  ```

## 🏗️ 整体解决方案定位

### Fast-Python-AI，平替 Posit AI

**方案组成：**
| 组件 | 用途 |
|---|---|
| **DeepSeek Harness (DSH)** | AI 代理框架，连接用户 ↔ 工具 ↔ LLM |
| **Claude Code / Vibe Coding** | AI 辅助编码阶段 |
| **R 语言 / RStudio (r-session)** | 数据分析（R 语言） |
| **Python / Jupyter Lab (jupyter-mcp)** | 数据分析（Python 语言） |

**核心优势：**
- 🏠 **数据不出服务器不出境**，内网可配合一体机部署
- 🇨🇳 **国内信创环境已验证**：麒麟 V10 + 鲲鹏 CPU ARM aarch64 + 一体机满血版国产 LLM
- 🔄 **LLM 可按需切换**（DeepSeek / GLM / MiniMax / Kimi / 国产满血版等）
- 🪶 轻量级浏览器界面，易用易部署易维护
- 🔓 完全开源免费
- 📊 AI 不仅应用于**编码阶段**，还应用于**数据分析阶段**，深入了一个维度

---

## 🎯 场景判断：什么时候用 jupyter-mcp

| 场景 | 用什么 | 原因 |
|---|---|---|
| **Jupyter Lab 交互式数据分析**（探索数据、画图、建模） | `jupyter-mcp` | 代码在 kernel 中执行，结果实时显示在 Notebook/Console |
| **写 Python 脚本完成某个任务**（爬虫、处理文件、自动化等） | 直接 exec / tool-bash 执行 | jupyter-mcp 是交互式分析工具，不是通用 Python 执行器 |

**核心原则：** `jupyter-mcp` 只用于 Jupyter Lab 中的交互式数据分析。不要用它执行通用 Python 任务。

---

## Python 交互式数据分析 (Jupyter MCP)

### 架构
```
AI 模型 ⇄ DSH ⇄ MCP (jupyter-mcp) ⇄ ZMQ (jupyter_client) ⇄ Jupyter Lab Kernel
```
- 注册文件：`~/.jupyter-mcp/current`

### 通用工具（两种模式共用）
| 工具 | 功能 |
|---|---|
| `list_objects` | 列出 kernel 中所有变量 |
| `preview_data` | 预览变量详情 |
| `get_loaded_packages` | 列出已加载的包 |
| `health_check` | 检查连接状态 |

### 使用步骤
1. 在 Jupyter Lab 中运行 `from jupyter_mcp import hook; hook.register()`
2. MCP Server 自动连接 kernel
3. 使用 `run_code` 执行分析代码
4. 结果自动显示在 Notebook 或 Console（取决于模式）

---

### 📓 Notebook 模式（.ipynb）

**场景：** JupyterLab 中打开 .ipynb 文件做交互式分析

**启动：** 在 Notebook cell 中运行 `hook.register()`（自动检测为 notebook 模式）

**工作流程：**
1. `run_code` 执行代码 → 自动插入新 Cell 到 .ipynb 文件
2. `jupyterlab-auto-reload` 扩展在 3 秒内自动刷新 Notebook 显示
3. 结果写回 Cell 中，包含执行序号和输出

**可用工具：** `run_code`（自动插 Cell + 写回结果）

**注意：** JupyterHub-singleuser 跑在 base conda 环境（`/usr/lib64/anaconda3/bin/jupyterhub-singleuser`），扩展需安装到 **base 环境的全局路径** `/usr/lib64/anaconda3/share/jupyter/labextensions/`，而非 graphrag 环境（`.../envs/graphrag/share/jupyter/labextensions/`）
  - `jupyterlab-console-adopt` 自定义扩展已安装到此路径 ✅
  - `jupyterlab-auto-reload` 也在这里有一份副本，确保 JupyterHub 能加载

---

### 🐍 .py + Console 模式

**场景：** JupyterLab 中打开 .py 文件 + "Create Console for Editor" 做交互式分析

**启动：** 在 .py 文件或 Console 中运行 `hook.register()`（自动检测为 console 模式）

**工作流程：**
1. `run_code` 执行代码 → **不修改 .py 文件**
2. `jupyterlab-console-adopt` 扩展自动捕获 kernel IOPub 消息
3. 在 Console 中创建 CodeCell 显示源码 + 输出（执行序号 `[1]`、`[2]`...）
4. 代码**不重复执行**，仅捕获已有的执行结果

**原理：** Console 只显示自身 session 的输出（JupyterLab issue #9936）。console-adopt 监听 kernel.iopubMessage（所有 session 的消息），检测外部 execute_input → 创建 CodeCell + 伪 future 捕获后续消息。

**MCP 工具的 Console 可见性：** `export_data` / `import_data` 内部通过 kernel `execute_request` 执行代码，会触发 `execute_input` 消息，因此 `console-adopt` 也能捕获并生成 Console CodeCell（各 1 个）。`run_code` 同理。所有经 kernel 执行的代码，在 `.py + Console` 模式下均可见。

**可用工具：**
| 工具 | 功能 |
|---|---|
| `run_code` | 执行代码（不写回 .py） |
| `read_source` | 读取 .py 源码内容 |
| `write_source` | 写入/覆盖 .py 源码文件 |
| `append_source` | 追加代码到 .py 源码末尾 |

### ⚠️ Python 作图：中文字体配置

**系统可用字体清单（`fc-list :lang=zh`）：**
| 字体文件 | 字体名 | 适用性 |
|---|---|---|
| `SimHei` 黑体 | `SimHei` | ✅ 最佳，ASCII+CJK 完整字符集 |
| `FangSong` 仿宋 | `FangSong` | ✅ 完整字符集 |
| `SimSun` 宋体 | `SimSun` | ✅ 完整字符集 |
| `KaiTi` 楷体 | `KaiTi` | ✅ 完整字符集 |
| `Droid Sans Fallback` | `Droid Sans Fallback` | ❌ 仅 CJK，无 ASCII 字形 |
| `WenQuanYi Micro Hei` | - | ❌ 未安装 |

**在 Jupyter kernel 中作图的正确姿势：**

每次使用 `run_code` 执行 matplotlib 绘图前，必须先设定中文字体，否则中文显示为方框。

```python
# ✅ 标准初始化——放在所有 plot 代码最前面
import matplotlib
matplotlib.rcdefaults()
matplotlib.rcParams['font.sans-serif'] = ['SimHei']     # 黑体，ASCII+CJK 均有
matplotlib.rcParams['axes.unicode_minus'] = False       # 解决负号显示问题
```

> **不要用** `matplotlib.rcParams['font.family'] = 'Droid Sans Fallback'` 或 `FontProperties` 逐个设置——前者因 Droid Sans Fallback 缺失 ASCII 字形会产生大量 `Glyph missing` 警告，后者每个文本元素都要传参太麻烦。`rcParams['font.sans-serif']` 用 `SimHei` 一次性搞定所有中英文混排。

---

### 与 r-session 对比
- `jupyter-mcp`：Python 交互式数据分析，连接 Jupyter kernel，Cell/Console 可见
- `r-session`：R 语言分析，连接 RStudio session，Console 可见
- Jupyter kernel 原生支持 ZMQ 协议，不需要在 kernel 内额外起 HTTP server

## R 语言数据分析

### 通过 MCP Server "r-session" 操作当前 RSession

- R 语言数据分析任务全部通过 MCP Server `r-session` 完成
- 架构：AI 模型 ⇄ DSH ⇄ MCP (r-session) ⇄ R API (httpuv) ⇄ RStudio R Session
- R API 运行在 `http://127.0.0.1:<port>`，通过 `POST /eval` 执行 R 代码
- 端口由 `~/.dsh/profiles/dsh-tui/cordis.patch.yml` 中 `mcp-r-session` 的 `env.R_API_PORT` 配置
- MCP Server 脚本：`r-session-mcp-server.py`；R API 脚本：`r-session-api.R`（均在仓库 `r-session-ai/` 下）

### 使用方式
- 先确认 R API 是否运行：`curl -s -H "Authorization: Bearer <token>" http://127.0.0.1:<port>/health`
- 如果未运行，让用户在 RStudio Console 中执行：
  ```r
  options(rsession_api_port = 用户的端口)
  options(rsession_api_token = "<你的Token>")
  source("r-session-ai/r-session-api.R")
  ```
- 重新加载前先停旧的：`httpuv::stopServer(server)`
- 通过 `curl -X POST http://127.0.0.1:<port>/eval -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"code":"..."}'` 执行 R 代码
- 代码结果和变量直接写入 RStudio 的 RSession，图和输出显示在 RStudio IDE 中

### 可见模式（Console 回显）
- **目标**：让用户在 RStudio Console 中看到执行的源码和输出
- **方法**：先把 R 代码写入 `.R` 文件（放在 `~/.dsh/workspace/R/` 子目录），然后用 `source("R/xxx.R", echo = TRUE)` 执行
- R 相关的所有 .R 文件、中间数据文件等均放入 `R/` 子目录管理
- R API 中 `safe_eval()` 的 `console_echo` 参数控制是否回显到 Console
- 绘图用 `source(echo = TRUE)` 也能正常渲染到 RStudio Plots 面板

### ⚠️ R 作图：回显 Plots 面板的正确姿势（2026.9.30 实测）

**核心：不要打开显式设备，直接 `print(p)` 走默认设备 RStudioGD。**

```r
# ✅ 正确——图进 RStudio Plots 面板
p <- ggplot(...) + theme_minimal(base_family = "SimSun")
print(p)

# ❌ 错误——只写出文件，Plots 面板看不到
agg_png("out.png"); print(p); dev.off()
png("out.png");     print(p); dev.off()
```

- `getOption("device")` 为 `"RStudioGD"` 时，`print(p)` 才会进 Plots 面板
- 脚本开头建议 `graphics.off()` 清掉遗留的显式设备（否则 `dev.cur()` 可能仍是 `agg_png`）
- 执行方式仍按可见模式：写入 `~/.dsh/workspace/R/xxx.R` 后 `source("R/xxx.R", echo = TRUE)`

### ⚠️ R 作图：中文字体只能用 `SimSun`（2026.9.30 实测）

**RStudioGD 设备上，`SimHei` / `黑体` 都解析不到，会静默回退成 `wqy-microhei` 并打印警告：**

```
font family 'SimHei' not found, will use 'wqy-microhei' instead
```

实测各 family 在 RStudioGD 上的解析结果：

| family | RStudioGD 是否可解析 |
|---|---|
| **`SimSun`** | ✅ **可解析，无警告 —— 推荐** |
| `sans` | ✅ |
| `wqy-microhei` | ✅（RStudio 自带回退字体） |
| `SimHei` / `黑体` / `simhei` / `Hei` | ❌ 回退 |
| `SimSun`(中文名`宋体`) / `NSimSun` / `FangSong` / `KaiTi` | ❌ 回退 |
| `Droid Sans Fallback` | ❌ 回退 |

> 原因：`simhei.ttf` 的**内部 family 名只有中文「黑体」**，RStudioGD 按内部 family 名匹配，
> 而 `fc-match SimHei` 能命中只是 fontconfig 的别名机制——两者不是一回事。
> `simsun.ttc` 内部 family 名是英文 `SimSun`，故可解析。
>
> 这与上面 **Python 侧用 `SimHei`** 的结论不同：matplotlib 走 fontconfig/字体文件路径，
> R 的 RStudioGD 走内部 family 名。**R 用 `SimSun`，Python 用 `SimHei`，不要混用。**

标准写法：

```r
theme_cn <- theme_minimal(base_family = "SimSun", base_size = 12) +
  theme(plot.title    = element_text(family = "SimSun", face = "bold"),
        plot.subtitle = element_text(family = "SimSun"),
        axis.title    = element_text(family = "SimSun"),
        axis.text     = element_text(family = "SimSun"),
        legend.text   = element_text(family = "SimSun"),
        legend.title  = element_text(family = "SimSun"))
```

### ⚠️ RMariaDB 把 BIGINT 返回成 raw

`SELECT COUNT(*)` 这类 BIGINT 列经 RMariaDB 回来是 **raw 向量**，直接 `as.numeric()` 会得到
`4.94e-324` 这种垃圾值（实为 1）。两种解法：

```r
# 方案A：SQL 侧转 DOUBLE（推荐，最省事）
dbGetQuery(con, "SELECT CAST(COUNT(*) AS DOUBLE) n FROM t")

# 方案B：R 侧按小端序还原 raw
num1 <- function(x) {
  if (is.raw(x)) { if (!length(x)) return(0); sum(as.numeric(x) * 256^(seq_along(x)-1)) }
  else as.numeric(x)
}
```

### ⚠️ 长输出超限 → 用 `run_with_sink.R` 落盘

R API 输出超过上限会截断（默认 2000 行，可用环境变量 `R_SESSION_OUTPUT_LINE_LIMIT` 调）。
需要完整结果时，用 `R/run_with_sink.R` 落盘再用 read 读：

```r
SRC <- "/home/ubuntu/.dsh/workspace/R/analyze_shanghai_housing.R"
OUT <- "/home/ubuntu/.dsh/workspace/R/analyze_output.txt"
source("R/run_with_sink.R", echo = TRUE)
```

> **已修复（2026.9.30，commit `c0737a3`）：** 早前 R API 的「200 行硬截断 + 报错误报成功/丢输出」
> 两个 bug 已修——现在报错会返回 `❌ 执行出错` + 错误信息 + 报错前的输出，输出上限提到
> 2000 行（可配置）。只有超过上限（或确需落盘）才需要 sink。Python 侧（jupyter-mcp）
> 始终无行数上限、直接 print 即可。

### ⚠️ Python 侧：`.py + Console` 模式不落盘

`.py + Console` 模式下 `run_code` **不修改 `.py` 文件**（见上文说明），
代码只存在于 Console 历史里——**kernel 一重启分析就没了**。
需要可复现时，另外把脚本写盘管理（本仓库放在 `~/.dsh/workspace/py/`，
与 R 的 `R/` 子目录对称）：

```
~/.dsh/workspace/py/analyze_shanghai_housing.py   # 对应 R/ 下三个脚本的 Python 版
```

**验证 matplotlib 中文确实生效的方法**（比看墨迹占比可靠）：

```python
from matplotlib import font_manager as fm
from matplotlib.font_manager import FontProperties
fm.findfont(FontProperties(family="SimHei"), fallback_to_default=False)
# -> /usr/share/fonts/myfonts/simhei.ttf   ✅ 真在用
# 对照：family="DejaVu Sans" 渲染中文会报 26 条 "Glyph xxxxx missing from font"
```

### ⚠️ 变量名禁区（会被 API 误用为函数而 500）

R API 辅助函数住在 `.GlobalEnv`，**给变量起下面这些名字会直接覆盖掉函数**，
下一次调用即报 `没有"ok"这个函数` / 500 错误：

`ok` `err` `safe_eval` `server` `app` `PORT` `HOST` `API_TOKEN` `MAX_ROW`
`obj_to_list` `safe_str` `parse_json_body` `env_port`

误覆盖后按 `r-session-api.R` 第 144/155 行的定义重新赋值 `ok` / `err` 即可恢复
（无需重启 server）。本次实践就踩过一次：`ok <- tryCatch(...)` 把 `ok()` 干掉了。

### 关键端点
| 端点 | 用途 |
|---|---|
| `GET /health` | 健康检查 |
| `GET /env` | 列出 R 环境中的对象 |
| `GET /preview/{name}` | 预览某个对象 |
| `POST /eval` | 执行 R 代码，可修改 session |
| `POST /eval/quiet` | 静默执行 R 代码 |
| `GET /packages` | 列出已加载的包 |

### ⚠️ 注意事项：`rm(list=ls())` 会清掉 API 函数
R API 的辅助函数（`safe_eval`、`ok`、`err`、`server` 等）存储在 `.GlobalEnv` 中。如果用户在 RStudio Console 中执行 `rm(list=ls())`，API 处理器会被一并清除，需重新 `source("r-session-ai/r-session-api.R")` 恢复。

### 多用户验证（2026.6.6）

**结果：方案表现完美 ✅**

- 每个用户的 RSession 是独立 OS 进程，httpuv 各自绑定不同端口，互不干扰
- `httpuv::stopServer(server)` 有效但无声，`stopAllServers()` 也支持
- `httpuv::stopAllServers()` 在另一个 R Session 中调用不会影响当前 R Session
- 适合多用户并行使用，隔离性可靠

### 安全加固：R API Token 认证（2026.6.7）

**背景：** 多用户场景下，R API 绑定 127.0.0.1 但所有本地用户可访问。恶意用户可扫描端口后
`curl http://127.0.0.1:<port>/eval` 执行任意 R 代码，劫持其他用户的 R session。

**方案：** R API + MCP Server 增加 Bearer Token 认证

```
┌─ cordis.patch.yml（mcp-r-session.env）──┐
│ R_API_TOKEN: "<secret>"                 │
└─────────────────────────────────────────┘
     │ 传递给 MCP Server
     ▼
┌─ r-session-mcp-server.py ──────────┐
│ _client_headers["Authorization"]   │
│     = f"Bearer {R_API_TOKEN}"       │
│ → 所有请求自带 Bearer Token         │
└──────────────────────────────────────┘
     │ HTTP 请求
     ▼
┌─ r-session-api.R ─────────────────┐
│ API_TOKEN <- Sys.getenv(...)       │
│ 每个请求验证 Authorization header  │
│ 不匹配 → 401 unauthorized          │
└──────────────────────────────────────┘
```

**API Token 为空时不启用认证**（向后兼容，适合纯单用户场景）。

**多用户部署时每个用户的 Token 应不同：**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

**健康检查（带 Token）：**
```bash
curl -H "Authorization: Bearer <token>" http://127.0.0.1:<port>/health
```

**MCP Server 自动读取 `R_API_TOKEN` 环境变量，在 `cordis.patch.yml` 的 `mcp-r-session.env` 中配置即可。**

### 启动依赖
- shebang 已改为 `graphrag` conda env 的 Python（`/usr/lib64/anaconda3/envs/graphrag/bin/python3`）
- 两个 MCP Server 使用相同 Python 环境

---

## R ↔ Python 双向数据交换 (2026.6.7 最终版)

两个 MCP Server（r-session + jupyter-mcp）各有一对 `export_data` / `import_data` 工具，通过 CSV 文件实现 R Session 和 Jupyter Kernel 之间的数据交换。

### 设计理念
- 跨 session 传的**只限小数据集**，大数据集在该 session 原地处理
- **只用 CSV** — R 和 Python 都原生支持，方案最简单通用
- CSV 类型可能失真，但小数据集一两个 `as.integer()` / `astype()` 就修好了
- 核心原则：**简单通用，偶尔手动修正**

### 架构
```
R Session → R API (httpuv) → r-session-mcp (Python) → CSV
                                                         ↓
Jupyter Kernel ← jupyter-mcp (Python) ← CSV
```

### 工具（固定 CSV格式）

**r-session-mcp：**
| 工具 | 内部实现 |
|---|---|
| `export_data(name)` | R 侧 `data.table::fwrite()` 写 CSV |
| `import_data(path, var_name)` | R 侧 `data.table::fread()` 读 CSV |

**jupyter-mcp：**
| 工具 | 内部实现 |
|---|---|
| `export_data(name)` | Python 侧 `pandas.to_csv()` 写 CSV |
| `import_data(path, var_name)` | Python 侧 `pandas.read_csv()` 读 CSV |

### 类型保真实测结果

**Python → R（`fread`）— 所有类型无损 ✅**
| Python | R | CSV 中间格式 |
|---|---|---|
| int64 | integer | `1` |
| float64 | numeric | `10.5` |
| object (str) | character | `Alice` |
| bool | logical | `True` / `False` |
| datetime64 (日期) | IDate/Date | `2026-06-07` |
| datetime64 (时间) | POSIXct | `2026-06-07 10:30:00` |

**R → Python（`read_csv`）— 日期/时间丢字符串 ❌**
| R | Python | 处理 |
|---|---|---|
| integer/num/char/logical | int64/float64/object/bool | 自动认 ✅ |
| Date / POSIXct | object (string) | `pd.to_datetime(df['col'])` 修复 |

### 共享目录
- **默认位置：** `~/.dsh/workspace/r2py/`（DSH 下由 `cordis.patch.yml` 的 `R2PY_SHARED_DIR` 指定，须写绝对路径）
- **环境变量覆盖：** 设置 `R2PY_SHARED_DIR`（统一）或 `R_SHARED_DIR` / `JUPYTER_SHARED_DIR`（分别覆盖）
- **文件名：** UUID 前缀 + `.csv`

### 使用流程

数据交换有两种方式，选哪种取决于你**是否需要在 Notebook 中看到导出/导入的 Cell**：

| 方式 | .py + Console | Notebook | R Console |
|---|---|---|---|
| **MCP 工具**（`export_data` / `import_data`） | ✅ Console 可见 | ❌ 无 Cell | ✅ Console 可见 |
| **标准代码**（`pd.read_csv` / `fwrite` 等） | ✅ Console 可见 | ✅ 有 Cell | ✅ Console 可见 |

#### 方式一：MCP 工具（快速手递手）
适合不在意 Notebook Cell 显示的场景（调试、后台、.py + Console 模式）。工具自动生成 UUID 文件名。

```
# R → Python
r-session-mcp.export_data(name="df")
jupyter-mcp.import_data(path="...", var_name="df")
df['date'] = pd.to_datetime(df['date'])  # 日期修复

# Python → R
jupyter-mcp.export_data(name="result")
r-session-mcp.import_data(path="...", var_name="result")  # 全类型无损
```

#### 方式二：标准代码（Notebook Cell / Console 双可见）
适合需要在 Notebook 留痕的场景。两边都用原生读写函数，通过 `run_code` / `source(echo=TRUE)` 执行。

```
# ── R 端（写入 R/ 脚本，source(echo=TRUE) 执行）──
# 导出到 CSV 给 Python
fwrite(df, "r2py/df_from_r.csv")
# 从 Python 导入 CSV
result <- fread("r2py/result_from_py.csv")

# ── Python 端（run_code 执行，Notebook 插 Cell / Console 可见）──
# 从 R 导入
summary = pd.read_csv("r2py/summary_r.csv")
# 导出给 R
sales.to_csv("r2py/sales_export.csv", index=False)
```

| 步骤 | R 端（Console 可见） | Python Notebook 端（Cell 可见） | Python .py + Console 端（Console 可见） |
|---|---|---|---|
| 执行分析代码 | `source("R/xxx.R", echo=TRUE)` | `run_code(...)` → 插 Cell | `run_code(...)` → console-adopt 显示 |
| **导出数据** | `fwrite()` 写在 `.R` 脚本中 | `df.to_csv()` 写在 `run_code` 里 | `df.to_csv()` 写在 `run_code` 里 |
| **导入数据** | `fread()` 写在 `.R` 脚本中 | `pd.read_csv()` 写在 `run_code` 里 | `pd.read_csv()` 写在 `run_code` 里 |

> **关于 MCP 工具的 Console 可见性（2026-06-07 优化后）：**
> `export_data` / `import_data` 内部通过 kernel `execute_request` 执行代码，会触发 `execute_input` 消息。
> - `.py + Console` 模式：`console-adopt` 捕获后生成 Console CodeCell，**各 1 个**（已合并多余验证步骤）
> - Notebook 模式：MCP 工具操作不写入 .ipynb 文件，**不会产生 Cell**
>
> 需要 Notebook Cell 可见的导出/导入，用方式二（标准代码 + `run_code`）。

### MCP 配置
在 `~/.dsh/profiles/dsh-tui/cordis.patch.yml` 中：
- r-session：已配 env `R_API_HOST=127.0.0.1`、`R_API_PORT`、`R_API_TOKEN`（端口/Token 各用户不同）
- jupyter-mcp：已配（`R2PY_SHARED_DIR` 与 r-session 指向同一目录）
- 多用户时需注意：
  - 每人**端口不同**（避免端口冲突），通过 `cordis.patch.yml` 中 `mcp-r-session.env.R_API_PORT` 配置
  - 每人**Token 不同**（确保安全隔离）
  - R API Token 优先级：`options(rsession_api_token=...)` > 环境变量 `R_API_TOKEN` > 空（不启用）
- 多用户时只需为每个用户设不同的 `R2PY_SHARED_DIR` 即可隔离
