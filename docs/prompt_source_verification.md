# Prompt 来源验证 - 是否一定使用配置文件？

## 核心问题
**我们的 prompt 是不是也一定会使用我们的配置文件中的内容呢？**

## 答案：**是的，但有三级回退机制**

---

## 完整的 Prompt 来源追踪

### 1. Prompt 的唯一注入点

**代码位置：** `src/services/ai/ai_service.py:430`

```python
def _create_agent_instance(self, agent_name: str, agent_config: Dict[str, Any]):
    # 准备Agent参数
    agent_params = {
        'name': agent_config.get('name', agent_name.title()),
        'model': self.current_model_instance,
        'instructions': agent_config.get('prompt', ''),  # ← 唯一的 prompt 注入点！
        'memory': self.memory,
        'knowledge': self.knowledge,
        'add_history_to_messages': True,
        'num_history_runs': 5,
        'markdown': True
    }
    
    # 创建Agent
    agent = Agent(**agent_params)  # ← Agno Agent 创建
```

**关键发现：**
- ✅ Prompt 只在创建 Agent 时注入一次
- ✅ 使用 `agent_config.get('prompt', '')` 获取
- ✅ `agent_config` 来自 `_load_unified_agent_config()`
- ❌ **没有任何地方修改或覆盖 instructions**

### 2. agent_config 的来源

**代码位置：** `src/services/ai/ai_service.py:360-410`

```python
def _get_or_create_agent(self, agent_name: str):
    # 检查缓存
    if agent_name in self.agents:
        return cached_agent
    
    # 加载配置 ← 这里决定 prompt 的来源
    agent_config = self._load_unified_agent_config(agent_name)
    
    # 创建实例
    agent = self._create_agent_instance(agent_name, agent_config)
    
    return agent
```

### 3. 三级配置优先级系统

**代码位置：** `src/services/ai/ai_service.py:490-520`

```python
def _load_unified_agent_config(self, agent_name: str):
    # 优先级 1: Agno 配置
    agno_config = self._load_agno_agent_config(agent_name)
    if agno_config:
        return agno_config  # 返回配置文件中的 prompt
    
    # 优先级 2: 传统配置
    legacy_config = self._load_legacy_agent_config(agent_name)
    if legacy_config:
        return legacy_config  # 返回配置文件中的 prompt
    
    # 优先级 3: 默认配置
    default_config = self._load_default_agent_config(agent_name)
    if default_config:
        return default_config  # 返回硬编码的默认 prompt
    
    return None
```

---

## Prompt 来源详解

### 优先级 1: Agno 配置 (最高优先级)

**配置位置：** `settings.toml` 中的 `[agno.agents.*]`

**代码位置：** `src/services/ai/ai_service.py:530-565`

```python
def _load_agno_agent_config(self, agent_name: str):
    # 读取配置文件
    agno_config_key = f"agno.agents.{agent_name}"
    agno_config = self.config_manager.get(agno_config_key)
    
    if agno_config and isinstance(agno_config, dict):
        if 'prompt' in agno_config or 'instructions' in agno_config:
            return {
                "name": agno_config.get('name', agent_name.title()),
                "prompt": agno_config.get('prompt') or agno_config.get('instructions', ''),
                "temperature": agno_config.get('temperature', 0.3),
                "enabled": agno_config.get('enabled', True),
                "source": "agno"
            }
    
    return None
```

**示例配置：**
```toml
[agno.agents.translation]
enabled = true
prompt = "You are an advanced AI translator with deep understanding of context..."
temperature = 0.2
```

**结果：** ✅ 使用配置文件中的 prompt

---

### 优先级 2: 传统配置

**配置位置：** `settings.toml` 中的 `[agents.*]`

**代码位置：** `src/services/ai/ai_service.py:567-595`

```python
def _load_legacy_agent_config(self, agent_name: str):
    # 读取配置文件
    legacy_config_key = f"agents.{agent_name}"
    legacy_config = self.config_manager.get(legacy_config_key)
    
    if legacy_config and isinstance(legacy_config, dict):
        prompt = legacy_config.get('prompt', '').strip()
        if prompt:
            return {
                "name": default_names.get(agent_name, agent_name.title()),
                "prompt": prompt,
                "temperature": legacy_config.get('temperature', 0.3),
                "enabled": legacy_config.get('enabled', True),
                "source": "legacy"
            }
    
    return None
```

**示例配置：**
```toml
[agents.translation]
enabled = true
prompt = "You are a professional translator..."
temperature = 0.3
```

**结果：** ✅ 使用配置文件中的 prompt

---

### 优先级 3: 默认配置 (最低优先级)

**配置位置：** 硬编码在代码中

**代码位置：** `src/services/ai/ai_service.py:597-650`

```python
def _load_default_agent_config(self, agent_name: str):
    default_configs = self._get_default_agent_configs()
    
    if agent_name in default_configs:
        config = default_configs[agent_name].copy()
        config["source"] = "default"
        return config
    
    return None

def _get_default_agent_configs(self):
    return {
        "translation": {
            "name": "Professional Translator",
            "prompt": "You are a professional translator. Translate the given text to English. Only return the translated text, no explanations.",
            "temperature": 0.3,
            "enabled": True
        },
        "polish": {
            "name": "Text Polisher",
            "prompt": "You are a professional editor. Polish and improve the given text for clarity and readability. Only return the improved text, no explanations.",
            "temperature": 0.3,
            "enabled": True
        },
        "correction": {
            "name": "Grammar Corrector", 
            "prompt": "You are a professional proofreader. Correct grammar and spelling errors in the given text. IMPORTANT: Keep the text in its original language - do not translate. Only return the corrected text, no explanations.",
            "temperature": 0.3,
            "enabled": True
        }
    }
```

**结果：** ⚠️ 使用硬编码的默认 prompt（仅当配置文件中没有时）

---

## Prompt 使用流程验证

### 场景 1: 配置文件中有 agno.agents.translation

```toml
[agno.agents.translation]
enabled = true
prompt = "You are an advanced AI translator..."
temperature = 0.2
```

**执行流程：**
```
_load_unified_agent_config("translation")
    ↓
_load_agno_agent_config("translation")
    ↓
config_manager.get("agno.agents.translation")
    ↓
返回: {
    "prompt": "You are an advanced AI translator...",
    "source": "agno"
}
    ↓
_create_agent_instance(agent_config)
    ↓
Agent(instructions="You are an advanced AI translator...")
```

**结论：** ✅ 使用配置文件中的 prompt

---

### 场景 2: 配置文件中只有 agents.translation

```toml
[agents.translation]
enabled = true
prompt = "You are a professional translator..."
temperature = 0.3
```

**执行流程：**
```
_load_unified_agent_config("translation")
    ↓
_load_agno_agent_config("translation")  → None (不存在)
    ↓
_load_legacy_agent_config("translation")
    ↓
config_manager.get("agents.translation")
    ↓
返回: {
    "prompt": "You are a professional translator...",
    "source": "legacy"
}
    ↓
_create_agent_instance(agent_config)
    ↓
Agent(instructions="You are a professional translator...")
```

**结论：** ✅ 使用配置文件中的 prompt

---

### 场景 3: 配置文件中没有任何配置

```toml
# 没有 [agno.agents.translation]
# 也没有 [agents.translation]
```

**执行流程：**
```
_load_unified_agent_config("translation")
    ↓
_load_agno_agent_config("translation")  → None
    ↓
_load_legacy_agent_config("translation")  → None
    ↓
_load_default_agent_config("translation")
    ↓
返回: {
    "prompt": "You are a professional translator. Translate...",
    "source": "default"
}
    ↓
_create_agent_instance(agent_config)
    ↓
Agent(instructions="You are a professional translator. Translate...")
```

**结论：** ⚠️ 使用硬编码的默认 prompt

---

### 场景 4: 配置文件中 prompt 为空

```toml
[agents.translation]
enabled = true
prompt = ""  # 空字符串
```

**执行流程：**
```
_load_unified_agent_config("translation")
    ↓
_load_agno_agent_config("translation")  → None
    ↓
_load_legacy_agent_config("translation")
    ↓
prompt = legacy_config.get('prompt', '').strip()
if prompt:  # 空字符串，条件为 False
    return config
return None  # ← 返回 None！
    ↓
_load_default_agent_config("translation")
    ↓
返回默认配置
```

**结论：** ⚠️ 空 prompt 会被忽略，使用默认 prompt

---

## Prompt 是否会被修改？

### 检查点 1: Agent 创建后

```python
# 创建 Agent
agent = Agent(instructions=prompt)

# 之后没有任何代码修改 agent.instructions
# 搜索结果显示：没有 agent.instructions = 或 set_instructions() 调用
```

**结论：** ✅ Agent 创建后 prompt 不会被修改

---

### 检查点 2: Agent.run() 调用

**代码位置：** `src/services/ai/ai_service.py:258`

```python
# 使用 Agent 处理文本
response = agent.run(enhanced_input)
```

**agent.run() 的参数：**
- `enhanced_input`: 用户输入的文本（可能包含窗口上下文）
- **没有传递新的 instructions 参数**

**Agno 框架行为：**
- `agent.run(text)` 只传递用户消息
- Agent 内部使用创建时的 `instructions` 作为 system prompt
- 不会修改或覆盖原有的 instructions

**结论：** ✅ 运行时不会修改 prompt

---

### 检查点 3: 上下文增强

**代码位置：** `src/services/ai/ai_service.py:272-350`

```python
def _build_enhanced_input(self, text: str, window_context: Optional[Dict], agent_name: str):
    if not window_context:
        return text
    
    # 构建上下文提示
    context_hint = " | ".join(context_parts)
    
    # 根据 agent 类型添加前缀
    if agent_name == 'translation':
        enhanced = f"[Context: {context_hint}]\n\n{text}"
    elif agent_name == 'polish':
        enhanced = f"[Source: {context_hint}]\n\n{text}"
    
    return enhanced
```

**重要：**
- 上下文信息添加到**用户输入**中
- **不是添加到 system prompt**
- Agent 的 instructions 保持不变

**示例：**
```
System Prompt (instructions): "You are a professional translator..."
User Message: "[Context: Chrome - Google Docs]\n\nHello World"
```

**结论：** ✅ 上下文增强不影响 prompt

---

## 总结

### ✅ Prompt 一定来自配置文件吗？

**答案：不完全是，有三级回退机制**

| 情况 | Prompt 来源 | 是否来自配置文件 |
|------|------------|----------------|
| 配置文件中有 `[agno.agents.X]` 且 prompt 不为空 | 配置文件 | ✅ 是 |
| 配置文件中有 `[agents.X]` 且 prompt 不为空 | 配置文件 | ✅ 是 |
| 配置文件中没有配置或 prompt 为空 | 硬编码默认值 | ❌ 否 |

### 🎯 实际使用建议

**如果你想确保使用配置文件中的 prompt：**

1. **在配置文件中明确定义**
   ```toml
   [agno.agents.translation]
   enabled = true
   prompt = "Your custom prompt here..."
   ```

2. **不要使用空 prompt**
   ```toml
   # ❌ 错误：会回退到默认值
   [agents.translation]
   prompt = ""
   
   # ✅ 正确：使用明确的 prompt
   [agents.translation]
   prompt = "You are a professional translator..."
   ```

3. **检查配置是否生效**
   ```python
   # 在日志中查看
   logger.info(f"Agent instance created: {agent_name} (source: {agent_config.get('source')})")
   
   # source 的值：
   # - "agno": 来自 agno.agents.*
   # - "legacy": 来自 agents.*
   # - "default": 来自硬编码默认值
   ```

### 📊 当前 settings.toml 的情况

```toml
# ✅ 这个会使用配置文件的 prompt
[agno.agents.translation]
prompt = "You are an advanced AI translator..."

# ⚠️ 这个会被上面的覆盖（优先级更低）
[agents.translation]
prompt = "You are a professional translator..."

# ❌ 这个会使用默认 prompt（因为 prompt 为空）
[agents.correction]
prompt = ""

# ❌ 这个会使用默认 prompt（因为 prompt 为空）
[agents.polish]
prompt = ""
```

### 🔍 验证方法

**查看日志确认 prompt 来源：**

```
# 日志示例
Agent instance created: translation (temperature: 0.2, source: agno)
# source: agno → 使用配置文件中的 agno.agents.translation

Agent instance created: correction (temperature: 0.3, source: default)
# source: default → 使用硬编码默认值（因为配置文件中 prompt 为空）
```

---

## 最终答案

### 问：Prompt 是不是一定会使用配置文件中的内容？

**答：不一定，取决于配置文件的内容**

- ✅ **如果配置文件中有非空的 prompt** → 一定使用配置文件
- ❌ **如果配置文件中没有配置或 prompt 为空** → 使用硬编码默认值

### 推荐做法

1. **明确定义所有 agent 的 prompt**
2. **使用 `agno.agents.*` 格式（功能更强）**
3. **不要留空 prompt**
4. **通过日志验证 source 字段**

### 当前需要修复的问题

```toml
# 需要修复：这些 agent 的 prompt 为空
[agents.correction]
prompt = ""  # ← 应该填写或删除此配置

[agents.polish]
prompt = ""  # ← 应该填写或删除此配置
```

**建议：**
- 要么填写完整的 prompt
- 要么删除这些配置项，让系统使用默认值
- 或者使用 `agno.agents.*` 格式定义
