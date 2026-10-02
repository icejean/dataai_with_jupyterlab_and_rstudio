---
output:
  html_document: default
  word_document: default
---

# Data AI 信创合规技术白皮书

## OpenClaw / DSH + JupyterLab + RStudio 一体化AI数据分析平台

> **版本：v1.3 \| 日期：2026-10-02**

------------------------------------------------------------------------

## 一、概述

### 1.1 方案定位

Data AI 是一套以 AI Agent 为大脑、Python + R 双语言交互式分析引擎为执行体的一体化AI数据分析平台。通过 OpenClaw 或 DSH（DeepSeek Harness，DeepSeek 官方国产原生 harness）连接 LLM（大型语言模型），以 MCP 协议统一调度 JupyterLab 和 RStudio，数据在浏览器界面中完成全流程分析，无需离开内网环境。

### 1.2 信创合规目标

本白皮书旨在论证 Data AI 方案在**监管行业（金融、政务、关键基础设施等）** 的信创合规性，回应审计和采购过程中可能出现的合规质疑。

------------------------------------------------------------------------

## 二、信创监管框架与方案对应关系

### 2.1 信创监管的分层原则

信创监管对信息技术系统的要求采用**分层分类**原则，并非一刀切：

| 层级 | 包含内容 | 监管强度 | 属性 |
|------------------|------------------|------------------|------------------|
| **底座层**（第一梯队） | 中央处理器（CPU）、操作系统、数据库 | **必须信创安全可靠测评** | 关键基础软硬件 |
| **重要应用层**（第二梯队） | 业务中间件、核心业务应用 | **强烈倾向**目录产品，可存在过渡期 | 逐步替换 |
| **工具链与辅助系统**（第三梯队） | IDE、数据分析工具、CI/CD、监控日志 | **不纳入信创监管** | 开发阶段、非生产环境 |

> **依据：** - 工信部《安全可靠测评工作指南（V3.0）》（2025.7） - 中国信息安全测评中心安全可靠测评产品范围（CPU、OS、DB 三大类） - 当前 CNITSEC 安全可靠目录（2023 年第 1 号 \~ 2026 年第 1 号）未包含开发工具类

### 2.2 Data AI 方案分层合规对应

```         
┌─────────────────────────────────────────────────────────┐
│  开发工具层（第三梯队：不纳入信创监管）                    │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐              │
│  │ DSH TUI  │  │ JupyterLab│  │ RStudio  │              │
│  │ MIT       │  │ BSD/Apache│  │ AGPL v3  │              │
│  │ AI Agent  │  │ Python 分析│  │ R 分析   │              │
│  └──────────┘  └───────────┘  └──────────┘              │
│   层级：数据分析工具    非生产运行环境    研发自用范围      │
├─────────────────────────────────────────────────────────┤
│  接口与数据交换层（合规自研）                              │
│  ┌──────────────────┐  ┌──────────────────┐              │
│  │ MCP Server       │  │ r2py 共享目录    │              │
│  │ jupyter-mcp /    │  │ CSV 文件交换     │              │
│  │ r-session-mcp    │  │ R↔Python 同步    │              │
│  │ 自研代码可审计   │  │ 纯文本格式可控    │              │
│  └──────────────────┘  └──────────────────┘              │
├─────────────────────────────────────────────────────────┤
│  LLM 接入层（国产可控）                                   │
│  ┌────────────┐  ┌────────┐  ┌──────────┐               │
│  │ DeepSeek   │  │ GLM    │  │ MiniMax  │               │
│  │ Kimi       │  │ 其他   │  │ Qwen     │               │
│  │ 国产大模型  │  │ 可切换  │  │ 内网部署  │               │
│  └────────────┘  └────────┘  └──────────┘               │
│  ★ 国产 API / 本地部署，数据不出境                         │
├─────────────────────────────────────────────────────────┤
│  底座层（第一梯队：使用信创目录产品兜底）                    │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐           │
│  │ 麒麟 V10 │  │ 统信 UOS V20 │  │ 方德 OS  │           │
│  │ ★ 已认证  │  │ ★ 已认证     │  │ ★ 已认证  │           │
│  └──────────┘  └──────────────┘  └──────────┘           │
│  数据库：GaussDB/ TDSQL / OceanBase / 达梦 等 ★ 已认证     │
│  CPU：鲲鹏 / 飞腾 / 海光 / 龙芯 / 兆芯 ★ 已认证          │
└─────────────────────────────────────────────────────────┘
```

**核心论点：** Data AI 方案不在信创安全可靠测评的品类范围内，底层基础设施由已认证的信创产品兜底，不存在合规缺口。

> **国产原生 AI Agent：** 上图中「AI Agent」层首选 **DeepSeek Harness（DSH）+ DeepSeek Harness TUI（dsh-tui）**——两者均为 DeepSeek 官方 MIT 开源，构成完整的国产原生方案；OpenClaw（MIT）为备选后端。DSH / dsh-tui 直接满足 AI 调度层与编程 Agent 层的国产化要求（详见第六、七节）。

------------------------------------------------------------------------

## 三、开源许可证合规性

### 3.1 组件许可证清单

| 组件 | 许可证 | 合规分析 |
|------------------------|------------------------|------------------------|
| OpenClaw | MIT (核心) / Apache 2.0 (组件) | ✅ 宽松许可，可商用可修改，无分发限制 |
| DSH（DeepSeek Harness）+ dsh-tui（DeepSeek Harness TUI） | MIT | ✅ DeepSeek 官方开源，国产原生，可商用可修改 |
| JupyterLab | BSD 3-Clause | ✅ 极宽松许可 |
| RStudio（开源版） | AGPL v3 | ✅ 作为独立服务使用，不涉及链接传染 |
| Python | PSF License | ✅ 专用许可，极宽松 |
| R Language | GPL v2 | ✅ 运行时环境，非衍生分发 |

### 3.2 架构层面的合规隔离

-   **所有组件以独立进程运行**，通过 HTTP / ZMQ 等标准网络协议通信，不构成"衍生作品"
-   **AGPL v3（RStudio）** 通过网络调用隔离——RStudio Server 作为独立 Web 服务，不嵌入任何应用中
-   **GPL v2（R 语言运行时）** 作为操作系统级运行时环境，使用 R 语言进行数据分析不触发传染条款

### 3.3 自研组件知识产权

-   `r-session-mcp`：自研 MCP Server，代码可全量审计
-   `r-session-api.R`：自研 R API 服务（httpuv），代码可全量审计
-   `jupyter-mcp`：自研 MCP Server，代码可全量审计
-   `hook.py`：自研 kernel 注册脚本，代码可全量审计
-   `jupyterlab-auto-reload`：自研Jupyter Lab extention ，代码可全量审计
-   `jupyterlab-console-adopt`：自研Jupyter Lab extention ，代码可全量审计

------------------------------------------------------------------------

## 四、数据安全与不出境论证

### 4.1 数据流向

```         
┌─────────┐    纯内网      ┌──────────────┐    纯内网      ┌──────────┐
│ 浏览器  │ ◄────────────► │ 企业内网服务器 │ ◄────────────► │ LLM 服务  │
│ 用户    │                 │              │                │ 国产/本地  │
└─────────┘    HTTPS       │ Data AI 方案 │    HTTP       └──────────┘
                            │ 数据全过程    │
                            │ 在内网流转    │
                            └──────────────┘
```

-   **数据不离开企业内网边界**
-   LLM API 调用指向国产大模型（DeepSeek / GLM / MiniMax / Kimi），或在本服务器/内网部署本地模型
-   **不存在数据出境场景**

### 4.2 与 SaaS 方案对比

| 维度       | 大厂 SaaS 方案              | Data AI 一体机方案     |
|------------|-----------------------------|------------------------|
| 数据落位   | 大厂云服务器                | 企业内网服务器（可控） |
| 传输路径   | 内网 → 公司网关 → 公网 → 云 | **全程内网**           |
| 数据审计   | 依赖厂商审计能力            | **自审可控**           |
| 断网可用   | ❌ 不可用                   | ✅ 可离线运行          |
| 供应链风险 | 厂商依赖                    | 多层开源可切换         |

------------------------------------------------------------------------

## 五、LLM 接入合规性

### 5.1 国产 LLM 支持

Data AI 支持自由切换（但不限于）以下国产大模型，均已通过生成式人工智能备案：

| 模型     | 厂商     | API 境内     | 数据不出境 | 备注           |
|----------|----------|--------------|------------|----------------|
| DeepSeek | 深度求索 | ✅ 杭州/北京 | ✅         | 可自部署开源版 |
| GLM      | 智谱 AI  | ✅ 北京      | ✅         | 可自部署开源版 |
| MiniMax  | 稀宇科技 | ✅ 上海      | ✅         | 可自部署开源版 |
| Kimi     | 月之暗面 | ✅ 北京      | ✅         | 可自部署开源版 |
| Qwen     | 阿里巴巴 | ✅ 杭州      | ✅         | 可自部署开源版 |

### 5.2 数据出境合规

-   Data AI 方案**不接入** OpenAI / Claude / Gemini 等境外 LLM
-   如条件允许，可部署开源大模型（DeepSeek v4 flash、GLM-5、Qwen3.5 等）至内网服务器，实现 **完全离线运行**
-   符合《数据安全法》《个人信息保护法》《数据出境安全评估办法》要求

------------------------------------------------------------------------

## 六、AI 编程与智能调度层

### 6.1 架构总览

Data AI 在 LLM 接入层之上，构建了 AI 编程与智能调度层，解决"AI 如何辅助数据分析"这一核心问题。架构如下：

```         
DSH（首选） / OpenClaw (AI 调度 Agent · 双后端)
│
├─ 简单代码 ──► 国产 LLM ──────────── 直接生成执行
│   (SQL / 基础 R / 基础 Python / 绘图)
│
└─ 复杂代码 ──► DeepSeek Harness TUI（首选）/ Claude Code ──► 国产 LLM
    (ML 建模 / 深度学习 / 多步特征工程)
                │
                ▼
┌──────────────────────────────────────────────┐
│        连接活动进程（核心亮点一）              │
│                                              │
│  Jupyter Kernel (Python) ← ZMQ → jupyter-mcp │
│    ★ ZMQ 协议，无端口暴露，天然隔离            │
│                                              │
│  R Session ← HTTP Token → r-session-mcp      │
│    ★ 每用户独立端口 + Bearer Token 授权       │
│                                              │
│  ┌── r2py 共享目录 ──────────────────┐       │
│  │ ~/r2py/ CSV 文件，仅本用户可见    │       │
│  │ 实现 R ↔ Python 数据交互          │       │
│  └──────────────────────────────────┘       │
└──────────────────────────────────────────────┘
         ▲
  连接 LLM AI + ML AI（核心亮点二）
```

### 6.2 两大核心连接

**① 连接活动进程——真正的交互式数据分析**

Data AI 通过 MCP 协议直接连接到用户正在运行的 Jupyter Kernel 和 R Session，AI 生成的代码立即执行、立即在 Notebook / Console 中反馈结果。用户在同一进程中反复迭代修改，这是真正的交互式数据分析，而非"生成代码 → 复制粘贴 → 手动执行"的片段式体验。

这种模式下，AI 不再是"代码生成器"，而是**数据分析助手**：用户提出分析方向，AI 生成并执行代码，结果实时呈现，AI分析数据，根据执行的结果给出分析结论或提出进一步的分析建议，用户据此调整下一步方向——循环迭代直至分析完成。

**② 连接 LLM AI 与 ML AI——全谱系覆盖**

| 能力 | 覆盖范围 | 实现路径 | 生态 |
|------------------|------------------|------------------|------------------|
| LLM AI | 自然语言→代码 | OpenClaw / DSH 调国产 LLM | SQL / 基础分析 / 绘图 |
| ML AI | 机器学习建模 | OpenClaw / DSH → DeepSeek Harness TUI（首选）/ Claude Code → 国产 LLM | Python (PyTorch / TF / scikit-learn) + R (mlr3 / tidymodels) |

大多数数据分析 AI 方案只做"用自然语言写 SQL / 写代码"。Data AI 在此基础上，通过 DeepSeek Harness TUI（首选）/ Claude Code 编码 Agent 连接国产 LLM，可以完成机器学习建模、深度学习、特征工程、超参调优等复杂任务——**一个方案覆盖从简单查询到复杂建模的全谱系数据分析**。

### 6.3 任务分层调度

| 任务复杂度 | 举例 | 执行路径 |
|------------------------|------------------------|------------------------|
| 简单 | SQL 查询、基础 R/Python 脚本、折线图箱线图等常规绘图 | OpenClaw / DSH → 国产 LLM → MCP → Kernel / Session |
| 复杂 | ML 建模、深度学习、多步特征工程、交叉验证 | OpenClaw / DSH → DeepSeek Harness TUI（首选）/ Claude Code → 国产 LLM → MCP → Kernel / Session |

### 6.4 安全架构

合规与安全是不同维度但紧密关联的问题。本节从安全架构角度论证方案的设计可靠性，与等保 2.0 要求（第八节）共同构成完整的安全合规论证。

**① 嵌入式 Agent 模式**

生产环境中，OpenClaw 以 `openclaw chat` 命令运行，**不启动 Gateway 网关服务**（DSH 后端以 `dsh --profile dsh-tui` 终端模式运行，同样无网关暴露）：

-   ❌ 无 HTTP 端口监听
-   ❌ 无 Web 管理界面
-   ❌ 无外部 API 接口暴露
-   ✅ 仅标准 I/O 与用户交互

Agent 在用户终端的进程上下文中执行，所有操作受限于当前 Linux 用户的权限范围。

**② 多用户完全隔离**

```         
服务器 ── Linux 用户隔离
│
├─ 用户 A (linux user) ──────────────────────
│  ├─ openclaw chat / dsh --profile dsh-tui（用户进程，无端口）
│  ├─ RStudio Server（端口 8787-A）
│  │    └─ R API Server（端口 8161-A）
│  │         └─ Bearer Token A
│  ├─ JupyterHub/JupyterLab（端口 8000-A）
│  │    └─ Kernel ← ZMQ（无端口，仅同进程内可见）
│  └─ ~/r2py/（数据交换目录，仅本用户可见）
│
├─ 用户 B (linux user) ──────────────────────
│  ├─ openclaw chat / dsh --profile dsh-tui
│  ├─ RStudio Server（端口 8787-B）
│  │    └─ R API Server（端口 8226-B）
│  │         └─ Bearer Token B
│  ├─ JupyterHub/JupyterLab（端口 8000-B）
│  └─ ~/r2py/
│
★ 全部以普通用户运行，非 root
★ 文件系统、进程、端口全隔离
★ 相当于每个用户运行在 Linux 沙箱中
```

**③ 进程间调用的安全机制**

| 组件 | 通信方式 | 安全措施 |
|------------------------|------------------------|------------------------|
| OpenClaw / DSH ↔ Jupyter Kernel | ZMQ (jupyter-mcp) | ZMQ 绑定 IPC / localhost，无网络端口暴露 |
| OpenClaw / DSH ↔ R Session | HTTP (r-session-mcp) → R API | 每用户独立端口 + Bearer Token 验证 |
| Agent 后端读取用户 Token | openclaw.json / cordis.patch.yml | 各用户自己的配置文件，权限受 Linux 保护 |
| R ↔ Python 数据交换 | CSV 文件（\~/r2py/） | 各用户自己的目录，文件系统权限隔离 |

**R API Token 授权流程：**

```         
用户启动 R API 服务时设定 Token：
  options(rsession_api_port = 8161)
  options(rsession_api_token = "<用户自定义 Token>")
  source("r-session-api.R")

Agent 后端（OpenClaw / DSH）发起调用时：
  openclaw.json / cordis.patch.yml 中配置该用户的 Token →
  MCP Server 读取 Token →
  在 HTTP 请求头部插入 Authorization: Bearer <Token> →
  R API Server 验证 Token 是否与启动时 options() 设定的匹配 →
  匹配 → 放行；不匹配 → 返回 401 Unauthorized
```

**④ Jupyter Kernel 天然隔离**

Jupyter Kernel 通过 ZMQ 协议与 JupyterLab 前端通信，绑定 IPC 或 localhost socket。与 R API Server 不同，Jupyter Kernel **不暴露 HTTP 端口**，没有给其他进程直接调用它的途径——只有启动了该 Kernel 的 JupyterLab 进程可以与之通信。`jupyter-mcp` 通过 hook 方式注册连接到 Kernel，不存在网络层面的暴露面。

### 6.5 合规分析

**OpenClaw（MIT）** - 完全开源可审计 - 非 root 运行，操作权限受 Linux 用户权限天然限制 - 嵌入式模式无网络暴露面，不构成新的攻击面 - 权限可通过 openclaw.json 配置命令白名单进一步收紧

**DSH（DeepSeek Harness，MIT）** - DeepSeek 官方开源 harness，国产原生 - 非 root 运行，操作权限受 Linux 用户权限天然限制 - 终端模式无网络暴露面，不构成新的攻击面 - 信创原生路径，直接满足国产化要求

**DSH TUI（dsh-tui，DeepSeek Harness TUI，MIT）** - DeepSeek 官方交互式 TUI 编程 Agent，与 DSH 同源 - 非 root 运行，终端模式无网络暴露面 - 首选编程 Agent，实测平替 Claude Code

**Claude Code（Anthropic 专有软件）** - **角色定位**：编码工具（历史遗留），已被 DeepSeek Harness TUI 平替，不纳入生产交付清单 - 调用国产 LLM，不走 Anthropic API，数据不出境 - **已被 DSH TUI 完全替代**（见第七节）

**运行环境** - Linux 用户隔离 = 操作系统级安全边界 - 全部组件以普通用户运行，无 root 提权路径 - 等保 2.0 对应：身份鉴别（LDAP / OIDC）、访问控制（用户权限）、安全审计（auditd + 操作日志）

------------------------------------------------------------------------

## 七、国产替代方案

### 7.1 背景

部分监管行业用户要求方案中使用的 AI Agent 与编程 Agent **均为国产产品**。当前方案在「AI 大脑」层内置**双后端**——**OpenClaw（默认，MIT 开源）**与 **DSH（DeepSeek Harness，DeepSeek 官方 MIT 开源）**——二者共用同一对 stdio MCP Server（`jupyter-mcp` + `r-session`）。其中 DSH 与 DeepSeek Harness TUI（dsh-tui）同源，均为 DeepSeek 官方国产原生，直接满足国产化要求；OpenClaw（MIT）全开源，亦不属于需要替换的范畴。**Claude Code（Anthropic）为国外闭源产品，信创环境不纳入交付清单**，其编程 Agent 角色已由国产原生的 dsh-tui 承担（见 7.4）。

> **核心判据：** 任何支持 MCP client 的 Coding Agent 均可接入 DataAI（TUI 还是 GUI 不重要，能调 MCP Server 即可），「AI 大脑」这一层是插拔式的。**核心约束（不可改）：** RStudio Server 与 JupyterHub / JupyterLab 必须运行在 **Linux 服务器**上。

### 7.2 替代需求映射

| 当前组件 | 国产替代目标 | 选型关键要求 |
|------------------------|------------------------|------------------------|
| OpenClaw（AI Agent 框架） | 国产 Agent 后端（**DSH 已内置**） | 支持 MCP 协议、CLI 运行、多用户 Linux 部署 |
| Claude Code（编程 Agent） | 国产编程 Agent（**dsh-tui 已内置**） | CLI 终端运行、支持 MCP 协议、可接国产 LLM、RStudio / JupyterLab 终端内可用 |

### 7.3 内置双后端与插拔式「AI 大脑」

Data AI 在「AI 大脑」层内置**双后端**，共用同一对 stdio MCP Server（`jupyter-mcp` 执行 Python、`r-session` 执行 R）：

| 后端 | 启动命令 | 许可 | 定位 |
|---|---|---|---|
| **OpenClaw（默认）** | `openclaw chat` | 开源（MIT） | 默认 AI 调度 Agent，嵌入式模式无网络暴露 |
| **DSH（DeepSeek Harness）** | `dsh --profile dsh-tui` | 开源（MIT） | DeepSeek 官方国产原生 harness，信创首选 |

> 「AI 大脑」这一层是**插拔式**的：Agent 只负责对话 + 通过 MCP 协议调用 `jupyter-mcp`（执行 Python）与 `r-session`（执行 R）。Python / R 到底跑在哪、怎么跑，由 MCP Server 决定，与接哪个 Agent 无关。

> **关于 Claude Code：** Claude Code（Anthropic）为**国外闭源产品**，信创环境不纳入交付清单，其编程 Agent 角色已由国产原生的 **dsh-tui** 承担（见 7.4）。开源 DataAI 线虽可接入 Claude Code 作为第三后端，但与信创合规属两个不同维度，本节仅论信创维度下的双后端。

**核心论点：** OpenClaw（MIT）与 DSH（DeepSeek 官方 MIT）均为开源，在信创框架下**不属于需要替换的范畴**；DSH 为国产原生后端，直接满足国产化要求。编程 Agent 的国产替代清单见 7.4。无论选择哪个后端，自研的 `jupyter-mcp` 和 `r-session-mcp` 均为标准 MCP Server，Skill 体系为通用设计，**无需修改即可跨后端运行**。

### 7.4 国产编程 Agent 替代清单

内置的 **DeepSeek Harness TUI（dsh-tui）** 为 DeepSeek 官方国产原生方案，与 DSH 同源，原生支持 tool-calling / reasoning，实测可完全平替 Claude Code，是**无需第三方的首选**。此外，国产 Coding Agent CLI 已形成多个可选方案（以下为举例、**包括但不限于**所列，任何支持 MCP client 的 Coding Agent 均可接入），涵盖开源与闭源两类，供有其它生态偏好的用户备选：

| 后端 | 厂商 | 许可 | 形态 | MCP 客户端 | 默认模型 / BYOK | 优先级 |
|---|---|---|---|---|---|---|
| **Qwen Code** | 阿里通义 | 开源 Apache-2.0 | TUI / CLI | stdio·SSE·HTTP·OAuth | Qwen3-Coder（可 BYOK） | ★★★ |
| **Kimi Code CLI** | 月之暗面 | 开源 Apache-2.0 | TUI（terminal-first） | stdio·HTTP·SSE | Kimi K2.5 / Moonshot | ★★★ |
| **MiniMax Code CLI** | MiniMax | 开源 MIT | TUI / Headless / ACP | stdio·http·sse | M3 + DeepSeek/Kimi/GLM 等 16 模型 | ★★☆ |
| **CodeBuddy Code CLI** | 腾讯 | 闭源免费（个人版） | TUI / CLI | stdio·HTTP·SSE | 混元 + DeepSeek 等 | ★★☆ |
| **MiMo-Code** | 小米 | 开源 MIT | TUI | local MCP | 小米 MiMo + 75+ 模型 | ★★☆ |
| **Qoder CN CLI** | 阿里通义灵码 | 闭源免费（个人版） | TUI / mcp serve | MCP | 通义灵码 | ★☆☆ |
| **ZCode CLI** | 智谱 | 待核实 | CLI / ACP | MCP tools | GLM | 待核实 |
| **DeepSeek-TUI** | 社区（非官方） | 待核实 | TUI | MCP | DeepSeek | 观察 |

**优先级说明：**

1. **Qwen Code / Kimi Code CLI（★★★）**：开源、terminal-first、MCP client 成熟，形态最贴近现有 Claude Code 后端，接入成本最低；国内用户本土账号 / 模型零门槛。其中 Kimi Code CLI 定位「Claude Code 的国产替代」，CLI + MCP 完整支持。
2. **MiniMax Code CLI（★★☆）**：MIT + **BYOK 一个 Key 调 16 个国产模型**，对「一条命令换模型」的中小组织用户有吸引力。
3. **CodeBuddy Code CLI（★★☆）**：腾讯自研、国内首家支持 MCP，但闭源（个人版免费），与开源 DataAI 线定位有张力。
4. **MiMo-Code（★★☆）**：小米开源（OpenCode fork）、支持 75+ 模型，但较新，接入需实测。
5. **Qoder CN CLI（★☆☆）**：通义灵码商用闭源，与 Qwen Code 同门（可优先选开源的 Qwen Code）。
6. **ZCode CLI / DeepSeek-TUI（待核实）**：前者智谱成熟度待核，后者为社区项目、非 DeepSeek 官方，接入前先核实维护者与稳定性。

> 上述国产后端默认接国内 LLM，数据全程境内、不出境；均可 BYOK 切换 DeepSeek / GLM 等，满足信创数据不出境要求。

### 7.5 国外备选（BYOK 指向国内 LLM）

对无国产化硬性要求的场景，另提供国外开源备选（同样遵循「支持 MCP client 即可接入」判据），均可 BYOK 指向国内 LLM（DeepSeek / GLM 等），数据不出境：

| 后端 | 厂商 | 许可 | 形态 | MCP 客户端 | 默认模型 / BYOK | 优先级 |
|---|---|---|---|---|---|---|
| **OpenCode** | opencode-ai（社区） | 开源 | TUI / CLI | local / remote MCP | 75+ 模型（BYOK） | ★★★ |
| **Gemini CLI** | Google | 开源 Apache-2.0 | TUI / CLI | stdio·SSE·HTTP | Gemini（免费额度，可 BYOK） | ★★☆ |
| **Goose** | Block / Linux Foundation | 开源 Apache-2.0 | TUI / CLI | stdio（3000+ MCP 生态） | 多模型 | ★★☆ |
| **Codex CLI** | OpenAI | 开源（Rust） | TUI / CLI | stdio·HTTP | GPT-5.x-Codex（可 BYOK） | ★★☆ |
| **Crush** | Charm | NOASSERTION | TUI | stdio·HTTP·SSE | 多模型 | ★☆☆ |
| **Aider** | 开源社区 | Apache-2.0 | CLI | MCP（部分支持） | 多模型 | ★☆☆ |

> 国外后端默认接国外模型，**同样可 BYOK 指向国内 LLM**，数据不出境。**OpenCode** 是 MiMo-Code 的上游、社区最活跃；**Goose** 为国外首选（Block / Linux Foundation 维护，MCP 生态成熟）。

### 7.6 替换后架构

即使采用最严格的国产化替换要求，架构变更仅限「AI 大脑」调度层：

```
多用户 Linux 环境（每个用户独立）
│
├─ 国产 Agent 后端（插拔式「AI 大脑」）────────────
│  （DSH 首选 / OpenClaw / Kimi Code CLI / Qwen Code 等）
│  │
│  ├─ 国产编程 Agent（dsh-tui 首选）← 代替 Claude Code
│  │    （dsh-tui 首选 / Kimi Code CLI / Qwen Code 等）
│  │    └─ 调用国产 LLM
│  │
│  ├─ 直接调国产 LLM（简单代码 / SQL / 绘图）
│  │
│  └─ MCP 协议 ← 调用 jupyter-mcp / r-session-mcp
│       ★ 不改代码，完全兼容
│
├─ RStudio / JupyterLab（终端中运行 Agent CLI）
│
└─ R ↔ Python 数据交换（~/r2py/ CSV 共享）
```

**兼容性保证：** - **MCP 协议**为行业开放标准，国产 Agent 后端与编程 Agent 均原生支持 - **`jupyter-mcp` 和 `r-session-mcp`** 为标准 MCP Server，不依赖特定 Agent 后端，可在任何 MCP Client 端运行 - **Skill 体系**同样为通用设计，国产后端可兼容 - 核心数据分析能力和安全隔离架构**不受替换影响** - 无论选用开源还是大厂闭源方案，需满足在同一服务器的 RStudio / JupyterLab 终端中以 CLI 方式运行的基本集成要求

------------------------------------------------------------------------

## 八、图数据库策略

### 8.1 当前状态（2026.6）

图数据库目前**尚未纳入** CNITSEC 安全可靠测评目录。安全可靠目录仅包含集中式数据库和分布式数据库两个品类。

### 8.2 过渡期方案

```         
┌──────────┐  HTTP/JSON   ┌──────────────┐  Bolt/原生   ┌─────────┐
│ 业务应用  ├─────────────►│ FastAPI       ├────────────►│ Neo4j   │
│          │◄─────────────┤ API 网关层    │◄────────────┤ 社区版  │
└──────────┘   响应JSON   │ ■ 认证鉴权    │             └─────────┘
                          │ ■ 审计日志    │
                          │ ■ 入参校验    │  ├ 可切换 ──► NebulaGraph
                          │ ■ 数据脱敏    │  ├ 可替换 ──► StellarDB
                          │ ■ 限流熔断    │  └ 可替换 ──► TuGraph
                          └──────────────┘
```

**合规要点：** - Neo4j Community Edition 使用 GPL v3 许可，通过 **REST API 隔离封装**（独立进程 + HTTP 通信），不构成衍生作品 - 封装层自研代码可审计，集中实现等保要求（认证、审计、脱敏）

### 8.3 替换预案

当图数据库正式进入安全可靠目录时，只需更换 FastAPI 封装层的底层驱动，业务代码**零修改**：

| 候选产品 | 厂商 | 状态 |
|------------------------|------------------------|------------------------|
| NebulaGraph | 杭州悦数科技 | 开源 Apache 2.0，已有信创适配，推荐优先 |
| StellarDB | 星环科技 | 商业产品，已获得信创数据库行业评选认可 |
| HugeGraph | 华为 → Apache 基金会 | 开源，国产团队 |
| TuGraph | 蚂蚁集团 → Apache 基金会 | 开源 Apache 2.0，蚂蚁集团金融风控基础设施，金融场景验证充分 |

------------------------------------------------------------------------

## 九、供应链安全与自主可控

### 9.1 多供应商可选，避免锁定

Data AI 方案的供应链设计原则：**核心层采用开源生态，接口层自研标准协议，每层均有独立替换路径**。

| 架构层 | Data AI 方案 | 可替换性 |
|------------------------|------------------------|------------------------|
| AI Agent 调度层 | OpenClaw（MIT）/ DSH（DeepSeek 官方 MIT）或国产替代（Kimi Code CLI / Qwen Code 等） | 多方案可选，跨平台兼容 |
| 编程 Agent | DSH TUI（DeepSeek 官方）或国产替代（Kimi Code CLI / CodeBuddy 等） | 多方案可选，CLI + MCP 标准统一 |
| 交互式分析引擎 | JupyterLab（BSD）+ RStudio（AGPL） | 成熟开源，社区长期维护 |
| MCP 数据通道 | 自研 jupyter-mcp + r-session-mcp | 标准 MCP 协议，不依赖特定框架 |
| 底层基础设施 | 国产信创 OS/DB/CPU（麒麟/OceanBase、GaussDB/鲲鹏等） | 信创目录多供应商备选 |

**替代大厂一体化方案时，Data AI 的开源架构有以下特点：** - 每一层均可独立评估、独立替换，不存在单层锁定的风险 - 对于已有大厂生态合作的单位，可在现有基础设施之上叠加 Data AI 分析层，无需全盘推翻 - 开源组件有活跃社区维护，自研组件代码完全可审计

### 9.2 自维护能力

-   全部组件均为成熟开源项目，社区长期维护
-   核心自研组件（MCP Server、API 封装）代码开放可审计
-   底层 OS/DB 使用已过信创认证的商业产品（麒麟/统信/OceanBase、GaussDB等），享受厂商维护服务

------------------------------------------------------------------------

## 十、等保合规配合方案

Data AI 平台在等保 2.0（GB/T 22239-2019）框架下可配合如下：

| 等保要求   | 实现方式                             |
|------------|--------------------------------------|
| 身份鉴别   | JWT / OAuth 2.0 接入企业 LDAP/OIDC   |
| 访问控制   | 接口级细粒度权限                     |
| 安全审计   | 全操作日志：操作人、时间、内容、结果 |
| 数据完整性 | HTTPS 传输加密 + 数据校验            |
| 数据保密性 | 敏感字段脱敏中间层 + 传输/存储加密   |
| 安全配置   | 最小权限原则，默认加固               |
| 漏洞管理   | 定期扫描 + 开源社区安全公告跟踪      |

### 10.1 安全架构与等保对应

以下映射将第六节安全架构设计对齐到等保 2.0 三级要求：

| 等保要求     | 安全架构实现                                         |
|--------------|------------------------------------------------------|
| 安全计算环境 | Linux 用户隔离 + 非 root 运行 + 文件/进程/端口全隔离 |
| 身份鉴别     | LDAP/OIDC + R API Token 双因素级别认证               |
| 访问控制     | Linux 文件权限 + openclaw.json 命令白名单            |
| 安全审计     | Linux auditd + 操作日志（操作人、时间、内容）        |
| 网络防护     | 嵌入式 Agent 零网络暴露 + ZMQ 无端口通信             |

------------------------------------------------------------------------

## 十一、监管行业典型场景合规说明

### 11.1 金融行业（银行/证券/保险）

-   数据 **不出内网**，满足银保监会数据管理规定
-   国产 LLM 满足金融业 AI 应用监管要求
-   可使用信创基础架构（鲲鹏 + 麒麟 + OceanBase、GaussDB）
-   国产化已内置——AI Agent 调度层（DSH）与编程 Agent 层（DSH TUI）均为 DeepSeek 官方国产原生；数据分析工具链（JupyterLab、RStudio）属于第三梯队，不在信创监管范围内，无需替代

### 11.2 政务/公共服务

-   一体机部署，满足"三同步一评估"要求
-   审计日志完备，满足政务系统审计要求
-   完全内网运行，无外联暴露面

### 11.3 关键信息基础设施（CII）

-   底层 OS/DB 使用安全可靠目录产品
-   上层工具链不在信创监管品类范围内
-   AI 调度层：嵌入式 Agent 无网络暴露，多用户完全隔离
-   全部组件自主可控，国产替代方案可行

------------------------------------------------------------------------

## 十二、结论

Data AI 方案（OpenClaw / DSH + JupyterLab + RStudio 一体化数据分析平台）在信创合规框架下**不构成合规风险**：

1.  ✅ **开发工具/数据分析工具不在信创安全可靠测评范围内**，不需要也不存在"信创认证"
2.  ✅ **底层基础设施**（OS、DB、CPU）使用已认证的信创目录产品兜底
3.  ✅ **LLM 全部使用国产 API 或本地部署**，数据不出境
4.  ✅ **许可证合规**——全部组件使用宽松/社区许可，架构隔离消除传染风险
5.  ✅ **AI 调度层安全架构**——嵌入式 Agent 零网络暴露，多用户 Linux 完全隔离，R API Token 授权，Jupyter ZMQ 天然隔离
6.  ✅ **国产化已内置**——AI Agent 后端 DSH + 编程 Agent DSH TUI 均为 DeepSeek 官方国产原生，另有 Qwen Code / Kimi Code CLI 等国产替代，MCP 生态通用兼容
7.  ✅ **自研代码可审计**，整体供应链无单一供应商锁定
8.  ✅ **图数据库采取灰度过渡策略**，预留国产替换接口
9.  ✅ **可配合等保 2.0 各项要求**

**结论：Data AI 方案可在监管行业落地，信创合规性有充分依据。**

------------------------------------------------------------------------

> **免责声明：** 本白皮书基于当前（2026年6月）公开的信创政策与安全可靠测评公告编写。信创政策为动态演进体系，建议在正式立项前咨询信创主管部门或专业测评机构，以获取最新合规指导意见。
