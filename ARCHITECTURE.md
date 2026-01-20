# 项目架构文档

## 1. 项目概览

该项目是一个基于 **FastAPI** 框架构建的 Python 后端服务，核心功能是提供 **AI Agent（智能体）** 服务。项目采用经典的分层架构（Controller-Service-DAO），集成了 OpenAI 兼容的 LLM 接口，并支持工具（Tools）调用能力。

- **核心框架**: FastAPI + Uvicorn
- **数据库 ORM**: SQLAlchemy + Alembic (数据库迁移)
- **AI 核心**: 自定义的 Agent 循环机制，支持上下文管理与工具调用
- **部署**: Docker 化支持 (`Dockerfile`, `docker-entrypoint.sh`)

## 2. 核心模块结构 (`src/modules`)

项目逻辑主要集中在 `src/modules` 下，分为三层：

### A. 接口层 (`handler/`)
负责处理 HTTP 请求，定义 API 路由。
- **`conversation_handler.py`**: 处理会话创建、聊天交互等请求。
- **`user_handler.py`**: 用户登录、注册、鉴权。
- **`record_handler.py`**: 聊天记录管理。

### B. 业务服务层 (`services/`)
这是 Agent 智能体的核心逻辑所在。
- **`agent/` (核心智能体逻辑)**:
    - `Agent`: 智能体控制器，协调 Prompt 构建、LLM 调用、结果解析和状态管理。
    - `State`: **(Refactored)** 纯数据持有者，负责内存状态管理和持久化，不再包含业务逻辑。
    - `LLMOutputParser`: **(New)** 负责解析 LLM 输出（提取 Thought/Action/Final Answer）。
    - `PromptBuilder`: **(New)** 负责根据历史和上下文渲染 Prompt。
    - `prompt.py`: 存放提示词模板。
- **`service_basis/` (工具箱)**:
    - 实现了 Agent 可调用的具体工具，如订餐 (`MealService`)、天气查询 (`WeatherQuery`)、票务 (`TicketQuery`)、旅行计划 (`TravelPlan`)。
    - `ToolRegistry.py`: 工具注册中心，管理可用工具列表。
- **`business/`**: 常规业务逻辑封装（用户管理、会话管理）。

### C. 数据访问层 (`dbController/`)
负责与数据库交互。
- **`models/`**: SQLAlchemy 数据模型定义 (`User`, `Conversation`, `Record`)。
- **`dao/`**: 数据访问对象，封装具体的 CRUD 操作。
- **`basis/`**: 数据库连接与 Session 管理。

## 3. AI 交互与基础设施 (`src/utils` & `config`)
- **`src/utils/chatgpt.py`**: 封装了与 LLM (如 OpenAI/Qwen) 的交互逻辑，支持流式输出 (`stream=True`)。
- **`src/utils/auth_dependency.py`**: 统一的鉴权依赖。
- **`config/`**: 配置加载器，读取 `config.yaml` 管理数据库、服务端口及 LLM 参数。

## 4. 数据流向示例
当一个聊天请求进来时：
1.  **Handler**: `conversation_handler` 接收请求并校验用户身份。
2.  **Service**: 调用 `Agent` 类，加载历史对话 (`State`)。
3.  **LLM Interaction**: `Agent` 将历史记录 + Prompt 发送给 LLM (`feed_LLM_full`)。
4.  **Tool Execution**: 如果 LLM 决定调用工具（如“查询天气”），Agent 会在 `modules/services/service_basis/` 中找到对应工具执行，并将结果反馈给 LLM。
5.  **Response**: 最终生成的自然语言回复通过 Handler 返回给前端。
---

## 5. 架构审查与潜在问题 (Architectural Review)

### 优点
1.  **清晰的分层架构**: Controller(Handler) -> Service(Business/Agent) -> DAO 的分层清晰，职责明确。
2.  **依赖注入**: `src/app.py` 中使用了 `dependency_overrides` 来注入 Service 实例，便于测试和解耦。
3.  **数据库会话管理**: DAO 层（如 `UserDAO`）使用 `contextmanager` (`with session_scope()`) 管理数据库会话，确保了连接的正确关闭和事务边界，这是处理 SQLAlchemy session 的最佳实践。
4.  **模块化工具**: `ToolRegistry` 设计模式允许方便地扩展新的 Agent 工具。

### 潜在风险与改进建议

#### 1. 系统路径操作
- **现状**: 代码中多处出现 `sys.path.append(str(get_root_path()))`（如 `main.py`, `state.py`）。
- **建议**: 这种做法通常是由于包结构引用问题导致的。标准的 Python 项目应通过相对引用或将项目作为包安装/运行 (`python -m src.app`) 来解决路径问题。硬编码修改 `sys.path` 可能导致不同环境下的行为不一致。

#### 2. Agent 循环控制
- **现状**: Agent 的 `call` 方法中使用 `while True` 循环配合 `looper` 进行思考-行动循环。
- **风险**: 如果 LLM 陷入重复输出或工具调用死循环，虽然有 `looper` 限制次数，但需确保所有异常路径都能正确跳出循环，避免长时间阻塞 HTTP 请求导致超时。

### 已解决的架构问题 (Resolved Issues)

#### 1. 有状态服务 (Statefulness) 与水平扩展
- **原问题**: `AgentManager` 曾在内存中缓存 `Agent` 实例，导致多 Worker 部署时状态不一致。
- **修复**: (2026-01-20) 重构了 `AgentManager` 为无状态模式，每次请求从数据库重建状态，并实现了 `State` 类的纯数据化改造。

#### 2. God Object (`State` 类职责过重)
- **原问题**: `State` 类混合了数据存储、正则解析和 Prompt 构建逻辑，违反单一职责原则。
- **修复**: (2026-01-20) 采用了 Parser/State/Builder 分离模式：
    - `LLMOutputParser` 负责解析。
    - `PromptBuilder` 负责视图构建。
    - `State` 回归纯数据管理。
    - `Agent` 充当控制器协调各组件。