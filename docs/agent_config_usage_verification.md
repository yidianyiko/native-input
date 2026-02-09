# Agent 配置文件使用验证

## 问题
**我们的软件会使用配置文件来初始化 Agent 吗？**

## 答案：**是的，会使用！**

---

## 完整的执行流程追踪

### 1. 用户操作流程

```
用户按下热键 (Win+Shift+O)
    ↓
FloatingWindow 显示
    ↓
用户在下拉框选择 Agent (例如: "🌐 翻译助手")
    ↓
用户输入文本
    ↓
触发 AI 处理
```

### 2. Agent 选择器的填充

**代码位置：** `src/ui/windows/floating_window/ui_components.py:383-450`

```python
def populate_function_selector(self, function_selector, ai_service_manager, ...):
    # 1. 从 AI Service Manager 获取可用 agents
    available_agents = ai_service_manager.get_available_agents()
    # 返回: ['translation', 'polish', 'correction', 'custom_agent', ...]
    
    # 2. 为每个 agent 添加到下拉框
    for agent_key in available_agents:
        function_selector.addItem(display_text, agent_key)
        # agent_key 就是配置文件中的 agent 名称！
```

### 3. get_available_agents() 的实现

**代码位置：** `src/services/ai/ai_service.py:650-690`

```python
def get_available_agents(self) -> List[str]:
    available_agents = set()
    
    # 步骤 1: 从 agno.agents.* 配置中发现
    agno_agents = self._discover_agno_agents()
    # 读取 settings.toml 中的 [agno.agents.*] 配置
    # 例如: ['translation', 'custom_agent', 'disabled_agent']
    
    # 步骤 2: 从 agents.* 配置中发现
    legacy_agents = self._discover_legacy_agents()
    # 读取 settings.toml 中的 [agents.*] 配置
    # 例如: ['translation', 'polish', 'correction']
    
    # 步骤 3: 添加默认 agents
    default_agents = ['translation', 'polish', 'correction']
    
    # 步骤 4: 过滤启用的 agents
    for agent_name in available_agents:
        config = self._load_unified_agent_config(agent_name)
        if config.get('enabled', True):
            enabled_agents.append(agent_name)
    
    return enabled_agents
```

### 4. 文本处理流程

**代码位置：** `src/ui/widgets/async_processor.py:145-150`

```python
# 用户选择的 agent_name 被传递到这里
result = self.ai_service_manager.process_text(
    request.text,           # 用户输入的文本
    request.agent_name,     # 例如: "translation"
    window_context=request.window_context
)
```

### 5. Agent 创建流程

**代码位置：** `src/services/ai/ai_service.py:218-250`

```python
def process_text(self, text: str, agent_name: str = "translation", ...):
    # agent_name 来自用户在 UI 中的选择
    # 例如: "translation", "custom_agent", "polish"
    
    # 获取或创建 Agent
    agent = self._get_or_create_agent(agent_name)
    
    # 使用 Agent 处理文本
    response = agent.run(enhanced_input)
```

### 6. 配置加载流程

**代码位置：** `src/services/ai/ai_service.py:360-410`

```python
def _get_or_create_agent(self, agent_name: str):
    # 检查缓存
    if agent_name in self.agents:
        return cached_agent
    
    # 加载配置（这里使用配置文件！）
    agent_config = self._load_unified_agent_config(agent_name)
    # 返回: {
    #     'name': 'Professional Translator',
    #     'prompt': 'You are an advanced AI translator...',
    #     'temperature': 0.2,
    #     'enabled': True,
    #     'source': 'agno'  # 或 'legacy' 或 'default'
    # }
    
    # 创建 Agent 实例
    agent = self._create_agent_instance(agent_name, agent_config)
    
    return agent
```

### 7. Agent 实例化

**代码位置：** `src/services/ai/ai_service.py:412-470`

```python
def _create_agent_instance(self, agent_name: str, agent_config: Dict):
    # 从配置中提取 prompt
    prompt = agent_config.get('prompt')
    # 例如: "You are an advanced AI translator with deep understanding..."
    
    # 创建 Agno Agent
    agent = Agent(
        name=agent_config.get('name'),
        model=self.current_model_instance,
        instructions=prompt,  # ← 配置文件中的 prompt 在这里使用！
        temperature=agent_config.get('temperature'),
        memory=self.memory,
        knowledge=self.knowledge,
        ...
    )
    
    return agent
```

---

## 配置文件的实际使用

### 当前 settings.toml 中的配置

```toml
# 这些配置会被读取和使用！

[agents.translation]
enabled = true
prompt = "You are a professional translator..."
temperature = 0.3

[agno.agents.translation]
enabled = true
prompt = "You are an advanced AI translator..."  # ← 这个会被使用（优先级更高）
temperature = 0.2
model = "gpt-4"

[agno.agents.custom_agent]
enabled = true
prompt = "You are a helpful AI assistant..."  # ← 这个也会被使用
temperature = 0.4
```

### 配置如何影响 Agent

1. **Agent 列表**
   - UI 下拉框中显示的 agent 列表来自配置文件
   - `get_available_agents()` 扫描配置文件中的所有 agent

2. **Agent 行为**
   - 每个 agent 的 `prompt` 决定了它的行为
   - `temperature` 控制输出的随机性
   - `enabled` 控制是否在 UI 中显示

3. **动态更新**
   - 修改配置文件后，可以通过 `reload_agent_config()` 重新加载
   - 下次使用该 agent 时会使用新配置

---

## 验证示例

### 示例 1: 使用配置文件中的 translation agent

```
用户操作:
1. 打开 FloatingWindow
2. 选择 "🌐 翻译助手" (对应 agent_name="translation")
3. 输入 "你好世界"

执行流程:
1. get_available_agents() 
   → 从配置文件读取，发现 "translation" agent
   
2. process_text("你好世界", "translation")
   → _get_or_create_agent("translation")
   → _load_unified_agent_config("translation")
   → 读取 settings.toml 中的 [agno.agents.translation]
   → prompt = "You are an advanced AI translator..."
   
3. Agent(instructions=prompt)
   → 使用配置文件中的 prompt 创建 agent
   
4. agent.run("你好世界")
   → 使用配置的 prompt 处理文本
   → 返回: "Hello World"
```

### 示例 2: 使用自定义 agent

```
配置文件添加:
[agno.agents.code_reviewer]
enabled = true
prompt = "You are a code review expert. Analyze the code and provide feedback."
temperature = 0.3

用户操作:
1. 重启应用（或调用 reload_agent_config）
2. 打开 FloatingWindow
3. 下拉框中会出现 "Code Reviewer" 选项
4. 选择并使用

执行流程:
1. get_available_agents()
   → 发现 "code_reviewer" 在配置文件中
   → 返回列表包含 "code_reviewer"
   
2. UI 显示 "Code Reviewer" 选项

3. 用户选择后，使用配置文件中的 prompt 创建 agent
```

---

## 结论

### ✅ **确认：配置文件被完整使用**

1. **Agent 发现**
   - `get_available_agents()` 扫描配置文件
   - 所有 `[agents.*]` 和 `[agno.agents.*]` 都会被发现

2. **Agent 创建**
   - `_load_unified_agent_config()` 读取配置
   - `prompt`, `temperature`, `enabled` 等都从配置文件读取

3. **Agent 行为**
   - 配置文件中的 `prompt` 直接传递给 Agno Agent
   - 作为 `instructions` 参数，控制 agent 的行为

4. **动态配置**
   - 支持三级优先级：agno.agents.* > agents.* > 默认
   - 支持运行时重新加载配置

### 📋 **配置文件的作用**

| 配置项 | 作用 | 示例 |
|--------|------|------|
| `enabled` | 控制 agent 是否在 UI 中显示 | `true`/`false` |
| `prompt` | 定义 agent 的行为和角色 | "You are a translator..." |
| `temperature` | 控制输出的随机性 | `0.2` (更确定) - `1.0` (更随机) |
| `max_tokens` | 限制输出长度 | `1000` |
| `model` | 指定使用的模型 | `"gpt-4"` |

### 🎯 **最佳实践建议**

1. **使用 agno.agents.* 格式**
   - 功能更强大
   - 支持更多配置选项

2. **避免配置冲突**
   - 不要同时定义 `agents.X` 和 `agno.agents.X`
   - 选择一种格式并坚持使用

3. **清晰的 prompt**
   - 每个 agent 都应该有明确的 prompt
   - 避免空 prompt

4. **合理的命名**
   - agent_name 应该简洁且有意义
   - 例如: `translation`, `code_review`, `summarize`
