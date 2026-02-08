# AI 智能输入法助手 - 后端服务设计

## 概述

为智能输入法客户端（Mac/Windows）提供 AI 文本生成服务。接收第三方系统请求，调用 Agent 生成文本，流式推送给前端输入法。

## MVP 范围与假设（必须满足）

本设计目标是快速开发 MVP，明确做出以下约束以降低复杂度：

- **部署形态**: 运行在用户自有服务器上，**单机单实例**，FastAPI/uvicorn **单进程单 worker**（必须使用 `--workers 1`）。
- **连接模型**: 输入法前端先建立 WebSocket 连接，再由第三方系统调用 HTTP POST 触发生成。
- **并发策略（MVP）**: 同一 `userId` **同一时刻只允许 1 个活跃请求**。新的请求会取消旧请求（Best-effort）。
- **可靠性（MVP）**: 不做跨进程/跨实例路由、不做持久化队列；断线/重启时进行中的请求会终止。

## 系统架构

```
┌─────────────────┐     HTTP POST      ┌─────────────────┐     WebSocket     ┌─────────────────┐
│   第三方系统     │ ─────────────────→ │   Agent服务     │ ←───────────────→ │   前端输入法     │
│  (请求发起方)    │   text/buttonId    │   (本项目)      │    流式推送结果    │  (Mac/Windows)  │
│                 │   roleId/userId    │                 │                   │                 │
└─────────────────┘                    └─────────────────┘                   └─────────────────┘
```

## 技术栈

- **框架**: Python + FastAPI
- **Agent**: Agno 框架（含记忆系统）
- **通信**: HTTP POST（接收请求）+ WebSocket（推送结果）
- **配置**: YAML 文件存储 prompt 模板

## 接口定义

### 1. HTTP POST `/api/process`

接收第三方系统的处理请求。

**请求头（MVP 安全最小实现）：**
- `X-API-Key: <key>`（服务端配置一个固定 key；不匹配则 401）

**请求体：**
```json
{
  "text": "用户输入的文本",
  "buttonId": "polish",
  "roleId": "work_email",
  "userId": "user_123"
}
```

**响应：**
```json
{
  "status": "ok",
  "requestId": "req_8f3c7c0b",
  "message": "Processing started"
}
```

**错误（MVP）：**
- 401：API Key 不正确
- 404：找不到对应 `buttonId/roleId` 配置
- 409：该 `userId` 当前没有 WebSocket 连接（要求先连 WS）
- 413：文本过长（需限制长度，如 8k-32k 字符，按模型能力调整）

### 1.1 HTTP POST `/api/cancel`（MVP 建议实现）

取消指定请求（Best-effort）。

**请求体：**
```json
{
  "userId": "user_123",
  "requestId": "req_8f3c7c0b"
}
```

**响应：**
```json
{ "status": "ok" }
```

### 2. WebSocket `/ws/{userId}`

前端输入法连接此端点接收流式结果。

**推送消息格式：**
```json
{"type": "start", "requestId": "req_8f3c7c0b"}
{"type": "chunk", "requestId": "req_8f3c7c0b", "seq": 1, "content": "生成的文本片段..."}
{"type": "done", "requestId": "req_8f3c7c0b"}
{"type": "error", "requestId": "req_8f3c7c0b", "code": "PROMPT_NOT_FOUND", "message": "错误信息"}
```

**前端可选发送（用于取消）：**
```json
{"type": "cancel", "requestId": "req_8f3c7c0b"}
```

## 数据流

```
1. HTTP POST 请求到达
   └─ 参数: { text, buttonId, roleId, userId }

2. 加载配置
   └─ 根据 buttonId + roleId 从配置文件读取 prompt 模板

3. 获取记忆
   └─ 通过 Agno 获取该 userId + roleId 的记忆数据（避免跨场景污染）

4. 组装 Agent 输入
   └─ prompt模板 + 用户text + 记忆上下文

5. 调用 Agno Agent
   └─ 流式生成文本

6. 推送结果
   └─ 根据 userId 找到 WebSocket 连接
   └─ 边生成边推送
   └─ 推送完成后发送 done 标记
```

## 项目结构

```
agents-service/
├── main.py                  # FastAPI 入口，挂载路由
├── config/
│   └── prompts.yaml         # buttonId + roleId → prompt 配置
├── routers/
│   ├── process.py           # HTTP POST /api/process
│   ├── cancel.py            # HTTP POST /api/cancel（可选）
│   └── websocket.py         # WebSocket /ws/{userId}
├── services/
│   ├── agent.py             # Agno Agent 封装
│   ├── connection.py        # WebSocket 连接管理器
│   └── requests.py          # in-flight 请求状态与取消（MVP 内存态）
└── requirements.txt
```

## 核心模块说明

### ConnectionManager

管理 WebSocket 连接池。

```python
class ConnectionManager:
    # MVP: 每个 userId 只保留一个“当前连接”（新连接替换旧连接）。
    # 如果后续要支持多端同时在线，可改为 userId -> {connId -> WebSocket}
    connections: dict[str, WebSocket]  # userId → WebSocket

    async def connect(userId: str, websocket: WebSocket)
    async def disconnect(userId: str)
    async def send_start(userId: str, requestId: str)
    async def send_chunk(userId: str, requestId: str, seq: int, content: str)
    async def send_done(userId: str, requestId: str)
    async def send_error(userId: str, requestId: str, code: str, message: str)
```

### RequestRegistry（MVP 建议）

在内存里记录每个 `userId` 当前活跃的 `requestId` 与取消句柄，用于实现：
- “同一 userId 只允许一个活跃请求”
- 新请求到来时取消旧请求
- `/api/cancel` 或 WS `cancel` 触发取消

```python
class RequestRegistry:
    active_request: dict[str, str]  # userId -> requestId
    cancel_flags: dict[str, asyncio.Event]  # requestId -> Event (set() to cancel)
```

### AgentService

封装 Agno Agent 调用。

```python
class AgentService:
    async def process_stream(
        text: str,
        prompt_template: str,
        userId: str,
        roleId: str,
        requestId: str,
        cancel: "asyncio.Event"
    ) -> AsyncGenerator[str, None]:
        # 1. 获取用户记忆
        # 2. 组装完整 prompt
        # 3. 调用 Agno Agent
        # 4. yield 生成的文本片段
        # 5. cancel.is_set() 时尽快停止并清理
```

### PromptLoader

加载和渲染 prompt 模板。

```python
class PromptLoader:
    def get_prompt(buttonId: str, roleId: str, text: str) -> str
        # 从 prompts.yaml 读取模板
        # 替换 {text} 占位符
```

## 配置文件格式

`config/prompts.yaml`:

```yaml
roles:
  work_email:
    name: "工作邮件"
    description: "正式商务场景"
  social_chat:
    name: "社交聊天"
    description: "轻松日常对话"
  tech_writing:
    name: "技术写作"
    description: "技术文档和代码相关"

buttons:
  polish:
    name: "润色"
    prompts:
      work_email: "请用正式商务语气润色以下内容，保持专业性：\n\n{text}"
      social_chat: "请用轻松友好的语气润色以下内容：\n\n{text}"
      tech_writing: "请润色以下技术内容，保持准确性和清晰度：\n\n{text}"

  expand:
    name: "扩写"
    prompts:
      work_email: "请扩展以下内容，补充必要的商务细节：\n\n{text}"
      social_chat: "请扩展以下内容，使其更生动有趣：\n\n{text}"
      tech_writing: "请扩展以下技术内容，补充必要的说明和示例：\n\n{text}"

  translate:
    name: "翻译"
    prompts:
      work_email: "请将以下内容翻译成专业的商务英语：\n\n{text}"
      social_chat: "请将以下内容翻译成地道的日常英语：\n\n{text}"
      tech_writing: "请将以下内容翻译成准确的技术英语：\n\n{text}"
```

## 记忆策略

- **Scope（MVP 推荐）**: 按 `userId + roleId` 隔离，避免不同场景互相污染
- **实现**: 使用 Agno 框架内置记忆系统
- **内容**: 用户偏好、对话历史、知识库

## 待实现（后续）

- [ ] 用户认证（API Key / JWT）
- [ ] 更多 button 功能
- [ ] 配置热更新
- [ ] 监控和日志
- [ ] 多实例部署（需要 Redis/队列解耦与连接路由；MVP 不支持）
