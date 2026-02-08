# AI 智能输入法助手 - 后端服务设计

## 概述

为智能输入法客户端（Mac/Windows）提供 AI 文本生成服务。接收第三方系统请求，调用 Agent 生成文本，流式推送给前端输入法。

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
  "message": "Processing started"
}
```

### 2. WebSocket `/ws/{userId}`

前端输入法连接此端点接收流式结果。

**推送消息格式：**
```json
{"type": "chunk", "content": "生成的文本片段..."}
{"type": "done"}
{"type": "error", "message": "错误信息"}
```

## 数据流

```
1. HTTP POST 请求到达
   └─ 参数: { text, buttonId, roleId, userId }

2. 加载配置
   └─ 根据 buttonId + roleId 从配置文件读取 prompt 模板

3. 获取记忆
   └─ 通过 Agno 获取该 userId 的记忆数据（所有角色共享）

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
│   └── websocket.py         # WebSocket /ws/{userId}
├── services/
│   ├── agent.py             # Agno Agent 封装
│   └── connection.py        # WebSocket 连接管理器
└── requirements.txt
```

## 核心模块说明

### ConnectionManager

管理 WebSocket 连接池。

```python
class ConnectionManager:
    connections: dict[str, WebSocket]  # userId → WebSocket

    async def connect(userId: str, websocket: WebSocket)
    async def disconnect(userId: str)
    async def send_chunk(userId: str, content: str)
    async def send_done(userId: str)
    async def send_error(userId: str, message: str)
```

### AgentService

封装 Agno Agent 调用。

```python
class AgentService:
    async def process_stream(
        text: str,
        prompt_template: str,
        userId: str
    ) -> AsyncGenerator[str, None]:
        # 1. 获取用户记忆
        # 2. 组装完整 prompt
        # 3. 调用 Agno Agent
        # 4. yield 生成的文本片段
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

- **Scope**: 按 userId 隔离，所有角色共享同一份记忆
- **实现**: 使用 Agno 框架内置记忆系统
- **内容**: 用户偏好、对话历史、知识库

## 待实现（后续）

- [ ] 用户认证（API Key / JWT）
- [ ] 更多 button 功能
- [ ] 配置热更新
- [ ] 监控和日志
