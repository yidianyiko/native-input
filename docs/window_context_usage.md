# Window Context Usage Guide

## Overview

窗口上下文功能允许应用程序在热键触发时捕获当前活动窗口的信息，并在处理完成后恢复焦点到原窗口。

## 功能特性

### 1. 自动捕获窗口上下文

当用户按下热键时，系统会自动捕获以下信息：

- **窗口标识**：窗口句柄 (hwnd)、标题、类名
- **进程信息**：进程 ID、进程名称
- **窗口状态**：可见性、活动状态
- **位置信息**：窗口坐标和尺寸（可选）
- **元数据**：触发时间、触发源（哪个热键）

### 2. 持久化窗口信息

所有窗口信息都可以序列化为 JSON 格式，支持：

```python
# 转换为字典
context_dict = window_context.to_dict()

# 转换为 JSON
context_json = window_context.to_json()

# 从 JSON 恢复
context = WindowContext.from_json(context_json)
```

### 3. 智能窗口恢复

系统使用多重策略确保能够恢复到正确的窗口：

1. **主策略**：使用窗口句柄 (hwnd)
2. **备用策略**：使用进程 ID + 窗口类名
3. **兜底策略**：使用进程名 + 窗口标题

## 使用方法

### 在浮动窗口中使用

```python
# 1. 获取捕获的窗口上下文
context = floating_window.get_captured_context()
if context:
    print(f"当前窗口: {context.get_display_name()}")
    print(f"进程: {context.process_name}")
    print(f"触发源: {context.trigger_source}")

# 2. 获取上下文信息（字典格式）
info = floating_window.get_context_info()
print(f"窗口标题: {info['window_title']}")
print(f"进程名: {info['process_name']}")

# 3. 恢复到原窗口
success = floating_window.restore_original_window()
if success:
    print("焦点已恢复到原窗口")

# 4. 注入文本到原窗口
text = "处理后的文本"
success = floating_window.inject_to_original_window(text, restore_focus=True)
if success:
    print("文本已注入到原窗口")

# 5. 清除上下文
floating_window.clear_context()
```

### 在热键管理器中使用

```python
# 获取当前窗口上下文
context = hotkey_manager.get_current_window_context()

# 恢复窗口焦点
success = hotkey_manager.restore_window_context()

```

### 直接使用 WindowContextManager

```python
from src.services.system.window_context import WindowContextManager
from src.services.system.window_service import create_window_service

# 创建服务
window_service = create_window_service()
context_manager = WindowContextManager(window_service)

# 捕获上下文
context = context_manager.capture_context(trigger_source="manual_test")

# 恢复上下文
success = context_manager.restore_context(context)

```

## 数据结构

### WindowContext

```python
@dataclass
class WindowContext:
    # 窗口标识
    hwnd: int                          # 窗口句柄
    title: str                         # 窗口标题
    class_name: str                    # 窗口类名
    
    # 进程信息
    process_id: int                    # 进程 ID
    process_name: str                  # 进程名称
    
    # 窗口状态
    is_visible: bool                   # 是否可见
    is_active: bool                    # 是否活动
    
    # 位置信息（可选）
    position: Optional[Dict[str, int]] # {x, y, width, height}
    
    # 元数据
    timestamp: str                     # ISO 格式时间戳
    trigger_source: str                # 触发源标识
```

### 示例 JSON 输出

```json
{
  "hwnd": 132456,
  "title": "Document.txt - Notepad",
  "class_name": "Notepad",
  "process_id": 12345,
  "process_name": "notepad.exe",
  "is_visible": true,
  "is_active": true,
  "position": {
    "x": 100,
    "y": 100,
    "width": 800,
    "height": 600
  },
  "timestamp": "2024-01-15T10:30:45.123456",
  "trigger_source": "QUICK_TRANSLATE"
}
```

## 工作流程

### 典型使用场景

1. **用户按下热键** (例如 Ctrl+Shift+T)
   - 热键管理器捕获当前窗口上下文
   - 记录窗口信息到 WindowContext 对象
   - 触发浮动窗口显示

2. **用户在浮动窗口中操作**
   - 输入或编辑文本
   - 选择 AI 功能（翻译、润色等）
   - 等待处理完成

3. **处理完成后**
   - 选项 A：自动恢复到原窗口并注入文本
   - 选项 B：用户手动复制结果
   - 选项 C：保持浮动窗口显示

4. **清理**
   - 关闭浮动窗口时清除上下文
   - 或保留上下文用于下次操作

## 配置选项

### 在 settings.toml 中配置

```toml
[window_context]
# 是否启用窗口上下文捕获
enabled = true

# 是否捕获窗口位置信息
capture_position = true

# 历史记录最大数量
max_history_size = 10

# 是否在处理完成后自动恢复焦点
auto_restore_focus = true

# 是否在注入文本后自动隐藏浮动窗口
auto_hide_after_inject = true
```

## 调试和监控

### 日志输出

系统会自动记录以下日志：

```
INFO: Window context captured: Document.txt - Notepad (notepad.exe)
DEBUG: Context details: WindowContext(hwnd=132456, title='Document.txt...', process=notepad.exe, pid=12345)
INFO: Restoring focus to: Document.txt - Notepad (notepad.exe)
INFO: Window focus restored successfully
```

## 最佳实践

1. **总是检查上下文有效性**
   ```python
   context = floating_window.get_captured_context()
   if context and context.is_valid():
       # 使用上下文
   ```

2. **处理恢复失败的情况**
   ```python
   if not floating_window.restore_original_window():
       # 提示用户或使用备用方案
       logger.warning("无法恢复到原窗口")
   ```

3. **及时清理上下文**
   ```python
   # 在窗口关闭时清理
   def closeEvent(self, event):
       self.clear_context()
       super().closeEvent(event)
   ```

4. **使用上下文信息优化用户体验**
   ```python
   context = floating_window.get_captured_context()
   if context and context.process_name == "chrome.exe":
       # 针对浏览器优化处理逻辑
   ```

## 故障排除

### 问题：无法捕获窗口上下文

**可能原因**：
- WindowService 未初始化
- 权限不足（某些系统窗口需要管理员权限）
- Windows API 调用失败

**解决方案**：
```python
# 检查 WindowService 是否可用
if hotkey_manager.window_service:
    print("WindowService 已初始化")
else:
    print("WindowService 未初始化，请检查初始化日志")
```

### 问题：无法恢复窗口焦点

**可能原因**：
- 目标窗口已关闭
- 窗口句柄已失效
- 目标窗口被最小化

**解决方案**：
```python
# 使用多重策略恢复
context = floating_window.get_captured_context()
if context:
    # 尝试恢复
    if not floating_window.restore_original_window():
        # 备用方案：直接注入到当前活动窗口
        floating_window.inject_to_active_window(text)
```

## 性能考虑

- 窗口上下文捕获非常快速（< 10ms）
- 上下文对象内存占用很小（< 1KB）
- 历史记录默认限制为 10 条，可配置
- 不会影响热键响应速度

## 安全性

- 不记录窗口内容，只记录元数据
- 进程信息仅用于窗口识别
- 可以随时清除历史记录
- 不会持久化到磁盘（除非显式保存）
