# Window Context Quick Start Guide

## 5 分钟快速上手

### 1. 功能已自动启用

窗口上下文功能已经集成到应用中，无需额外配置。当你按下热键时，系统会自动：

- ✅ 捕获当前窗口信息
- ✅ 记录进程和窗口标识
- ✅ 保存触发上下文

### 2. 在代码中使用

#### 在浮动窗口中获取上下文

```python
# 获取捕获的窗口上下文
context = floating_window.get_captured_context()

if context:
    # 显示窗口信息
    print(f"来自窗口: {context.title}")
    print(f"进程: {context.process_name}")
    print(f"触发源: {context.trigger_source}")
```

#### 恢复到原窗口

```python
# 处理完成后，恢复焦点到原窗口
success = floating_window.restore_original_window()

if success:
    print("✅ 已恢复到原窗口")
else:
    print("⚠️ 无法恢复窗口")
```

#### 注入文本到原窗口

```python
# 将处理后的文本注入到原窗口
processed_text = "这是处理后的文本"

success = floating_window.inject_to_original_window(
    processed_text,
    restore_focus=True  # 先恢复焦点再注入
)

if success:
    print("✅ 文本已注入")
```

### 3. 查看上下文信息

```python
# 获取上下文详细信息（字典格式）
info = floating_window.get_context_info()

print(f"窗口标题: {info['window_title']}")
print(f"进程名: {info['process_name']}")
print(f"进程ID: {info['process_id']}")
print(f"触发源: {info['trigger_source']}")
print(f"时间戳: {info['timestamp']}")
```

### 4. 典型使用场景

#### 场景 A：翻译并替换

```python
# 1. 用户按 Ctrl+Shift+T（翻译热键）
# 2. 系统自动捕获窗口上下文
# 3. 浮动窗口显示

# 4. 处理完成后
def on_translation_complete(translated_text):
    # 恢复到原窗口
    floating_window.restore_original_window()
    
    # 等待窗口激活
    time.sleep(0.1)
    
    # 注入翻译结果
    floating_window.inject_to_original_window(translated_text)
    
    # 隐藏浮动窗口
    floating_window.hide()
```

#### 场景 B：显示来源窗口信息

```python
# 在浮动窗口标题栏显示来源
def update_window_title():
    context = floating_window.get_captured_context()
    if context:
        title = f"AI 输入法 - 来自: {context.process_name}"
        floating_window.setWindowTitle(title)
```

#### 场景 C：智能处理

```python
# 根据来源窗口调整处理策略
def process_text(text):
    context = floating_window.get_captured_context()
    
    if context:
        # 针对不同应用使用不同策略
        if "chrome.exe" in context.process_name:
            # 浏览器：可能是网页内容
            return translate_web_content(text)
        elif "code.exe" in context.process_name:
            # VS Code：可能是代码
            return format_code(text)
        else:
            # 默认处理
            return default_process(text)
```

### 5. 测试功能

运行测试脚本验证功能：

```bash
python tests/test_window_context.py
```

预期输出：
```
=== Test 1: Window Context Capture ===
✅ WindowService created
✅ WindowContextManager created
📸 Capturing current window context...
✅ Context captured successfully!

📋 Context Details:
   Window: cmd.exe - python
   HWND: 132456
   Process: cmd.exe (PID: 12345)
   ...

🎉 All tests passed!
```

### 6. 调试技巧

#### 检查是否启用

```python
# 检查热键管理器是否有窗口上下文管理器
if hasattr(hotkey_manager, 'window_context_manager'):
    if hotkey_manager.window_context_manager:
        print("✅ 窗口上下文功能已启用")
    else:
        print("❌ 窗口上下文管理器未初始化")
else:
    print("❌ 热键管理器不支持窗口上下文")
```

#### 查看日志

窗口上下文操作会自动记录日志：

```
INFO: Window context captured: Document.txt - Notepad (notepad.exe)
DEBUG: Context details: WindowContext(hwnd=132456, ...)
INFO: Restoring focus to: Document.txt - Notepad (notepad.exe)
INFO: Window focus restored successfully
```

### 7. 常见问题

**Q: 为什么获取不到上下文？**

A: 检查以下几点：
- WindowService 是否初始化成功
- 是否通过热键触发（手动显示窗口不会捕获上下文）
- 查看日志中是否有错误信息

**Q: 恢复窗口失败怎么办？**

A: 系统会自动尝试多种策略：
1. 使用窗口句柄
2. 使用进程 ID + 类名
3. 使用进程名 + 标题

如果都失败，可能是窗口已关闭或被最小化。

**Q: 如何清除上下文？**

A: 
```python
floating_window.clear_context()
```

### 8. 下一步

- 📖 阅读完整文档：`docs/window_context_usage.md`
- 🔧 查看实现细节：`docs/window_context_implementation.md`
- 🧪 运行测试：`tests/test_window_context.py`
- 💡 查看示例：`src/ui/windows/floating_window/context_integration.py`

### 9. 获取帮助

如果遇到问题：

1. 查看日志文件
2. 运行测试脚本诊断
3. 检查 WindowService 初始化状态
4. 查阅故障排除文档

---

**就这么简单！** 窗口上下文功能已经集成并可以使用了。🎉
