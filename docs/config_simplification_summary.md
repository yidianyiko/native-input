# 配置系统简化总结

## 修改日期
2025-10-19

## 修改目标
简化 Agent 配置系统，只使用 `[agents.*]` 作为唯一配置来源

---

## 修改内容

### 1. 代码修改

#### 1.1 `src/services/ai/ai_service.py`

**删除的功能：**
- ❌ 删除 `_load_agno_agent_config()` - Agno 专用配置加载
- ❌ 删除 `_load_legacy_agent_config()` - 传统配置加载（重命名）
- ❌ 删除 `_load_default_agent_config()` - 默认配置回退
- ❌ 删除 `_get_default_agent_configs()` - 硬编码默认配置
- ❌ 删除 `_get_default_agent_names()` - 默认名称映射
- ❌ 删除 `_discover_agno_agents()` - Agno 配置发现
- ❌ 删除 `_discover_legacy_agents()` - 传统配置发现
- ❌ 删除 `get_default_agents()` 静态方法 - UI 组件使用的默认配置

**简化的功能：**
- ✅ `_load_unified_agent_config()` → `_load_agent_config()`
  - 只从 `agents.*` 读取配置
  - 验证 prompt 不为空
  - 返回标准化配置

- ✅ `get_available_agents()`
  - 只扫描 `agents.*` 配置
  - 过滤空 prompt 和禁用的 agents
  - 返回启用的 agent 列表

- ✅ `_get_or_create_agent()`
  - 简化配置变更检测
  - 只比较 prompt 内容

- ✅ `get_agent_config_info()`
  - 移除 `source` 字段（不再需要）
  - 移除 `model` 字段（不再支持）

#### 1.2 `src/ui/settings/pages/agent_page.py`

**修改：**
- ❌ 删除对 `AIService.get_default_agents()` 的引用
- ✅ 直接从配置文件读取所有 agents
- ✅ 验证 prompt 不为空

#### 1.3 `src/ui/windows/floating_window/ui_components.py`

**修改：**
- ❌ 删除对 `AIService.get_default_agents()` 的引用
- ✅ 简化 fallback 逻辑

---

### 2. 配置文件修改

#### 2.1 `settings.toml`

**删除的配置：**
```toml
# ❌ 删除重复的 translation 配置
[agents.translation]
prompt = "You are a professional translator..."

# ❌ 删除 text_polisher（重命名为 polish）
[agents.text_polisher]

# ❌ 删除 error_corrector（重命名为 correction）
[agents.error_corrector]

# ❌ 删除所有 agno.agents.* 配置
[agno.agents.translation]
[agno.agents.custom_agent]
[agno.agents.disabled_agent]
```

**保留的配置：**
```toml
# ✅ 标准化的 agent 配置
[agents.translation]
enabled = true
name = "翻译助手"
prompt = "You are a professional translator..."
temperature = 0.3
max_tokens = 1000

[agents.polish]
enabled = true
name = "润色助手"
prompt = "You are a professional editor..."
temperature = 0.3
max_tokens = 1000

[agents.correction]
enabled = true
name = "纠错助手"
prompt = "You are a professional proofreader..."
temperature = 0.3
max_tokens = 1000
```

---

## 新的配置规则

### 配置格式

```toml
[agents.{agent_name}]
enabled = true              # 是否启用（必需）
name = "显示名称"            # UI 显示名称（可选，默认为 agent_name.title()）
prompt = "System prompt"    # Agent 的 system prompt（必需，不能为空）
temperature = 0.3           # 温度参数（可选，默认 0.3）
max_tokens = 1000           # 最大 token 数（可选）
```

### 必需字段

- ✅ `enabled`: 必须为 `true` 才会显示在 UI 中
- ✅ `prompt`: 必须非空，否则会被忽略

### 可选字段

- `name`: 显示名称，默认使用 `agent_name.title()`
- `temperature`: 温度参数，默认 `0.3`
- `max_tokens`: 最大 token 数，默认无限制

---

## 配置验证

### 有效配置示例

```toml
[agents.my_agent]
enabled = true
name = "我的助手"
prompt = "You are a helpful assistant."
temperature = 0.5
max_tokens = 2000
```

### 无效配置示例

```toml
# ❌ 无效：prompt 为空
[agents.bad_agent1]
enabled = true
prompt = ""

# ❌ 无效：没有 prompt
[agents.bad_agent2]
enabled = true
name = "Bad Agent"

# ❌ 无效：disabled
[agents.bad_agent3]
enabled = false
prompt = "This won't be loaded"
```

---

## 代码行为变化

### 之前（三级优先级）

```
1. 尝试 agno.agents.{name}
2. 尝试 agents.{name}
3. 使用硬编码默认值
```

### 现在（单一来源）

```
1. 只从 agents.{name} 读取
2. 如果不存在或 prompt 为空 → 报错，不创建 agent
```

---

## 日志变化

### 之前

```
Agent instance created: translation (temperature: 0.2, source: agno)
Agent instance created: polish (temperature: 0.3, source: legacy)
Agent instance created: correction (temperature: 0.3, source: default)
```

### 现在

```
Loaded configuration for agent: translation
Agent translation created and cached
Found 3 enabled agents: ['correction', 'polish', 'translation']
```

---

## 迁移指南

### 如果你有 `agno.agents.*` 配置

**迁移步骤：**

1. 将配置移动到 `agents.*`
   ```toml
   # 之前
   [agno.agents.my_agent]
   prompt = "..."
   
   # 之后
   [agents.my_agent]
   prompt = "..."
   ```

2. 删除 `agno.agents.*` 配置

### 如果你依赖默认配置

**迁移步骤：**

1. 在 `settings.toml` 中明确定义所有 agents
   ```toml
   [agents.translation]
   enabled = true
   prompt = "You are a professional translator..."
   ```

2. 不要留空 prompt

---

## 优势

### ✅ 简化

- 只有一个配置来源
- 代码更简洁
- 更容易理解和维护

### ✅ 明确

- 配置必须明确定义
- 不会有隐藏的默认值
- 行为更可预测

### ✅ 可控

- 所有配置都在配置文件中
- 用户完全控制 agent 行为
- 没有硬编码的回退

---

## 注意事项

### ⚠️ 破坏性变化

- 如果配置文件中没有定义 agent，将无法使用
- 空 prompt 会导致 agent 不可用
- 需要手动迁移 `agno.agents.*` 配置

### ⚠️ 升级建议

1. 备份当前的 `settings.toml`
2. 确保所有需要的 agents 都在 `[agents.*]` 中定义
3. 确保所有 prompt 都非空
4. 测试所有 agents 是否正常工作

---

## 测试清单

- [ ] 所有 agents 都能在 UI 中显示
- [ ] 选择 agent 后能正常处理文本
- [ ] 修改配置后能正确重新加载
- [ ] 空 prompt 的 agent 不会显示
- [ ] 禁用的 agent 不会显示
- [ ] 日志中没有错误信息

---

## 相关文件

- `src/services/ai/ai_service.py` - 核心 AI 服务
- `src/ui/settings/pages/agent_page.py` - Agent 设置页面
- `src/ui/windows/floating_window/ui_components.py` - UI 组件
- `settings.toml` - 配置文件
