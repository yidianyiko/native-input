# reInput AI 输入法数据库使用指南

## 1. 数据库系统概述

reInput AI 输入法使用 SQLite 数据库来存储用户使用历史和上下文信息，为 AI 提供丰富的上下文数据。数据库系统采用分层架构设计：

### 架构层次

* **数据模型层** (`models.py`) - 定义数据实体类

* **数据库管理层** (`database_manager.py`) - 处理连接、表创建、迁移

* **业务服务层** (`database_service.py`) - 提供高级 CRUD 操作接口

* **迁移系统** (`migration.py`) - 处理数据库版本升级

### 核心实体关系

```
User (用户)
  ↓
AppWindow (应用窗口)
  ↓
WindowContext (窗口上下文/会话)
  ↓
Message (消息) - 包含 type 字段区分用户原始输入和 AI 处理后的消息
```

### 数据库文件位置

* 默认路径：`{项目根目录}/data/reInput.db`

* 自动创建 `data` 目录（如果不存在）

* 使用 WAL 模式提高并发性能

## 2. 数据库初始化时机和方法

### 自动初始化

数据库服务在创建时会自动初始化：

```python
from src.services.database import DatabaseService

# 创建服务时自动初始化数据库
db_service = DatabaseService()
```

### 依赖注入容器中的初始化

在应用启动时，数据库服务通过依赖注入容器自动注册和初始化：

```python
# src/core/container.py 中的自动注册
def _setup_default_registrations(self):
    # Register database service as singleton
    self.register_singleton(
        IDatabaseService,
        DatabaseService()  # 这里会自动初始化数据库
    )
```

### 手动初始化（如果需要）

```python
from src.services.database import DatabaseManager

db_manager = DatabaseManager()
success = db_manager.initialize_database()
if not success:
    logger.error("数据库初始化失败")
```

## 3. 如何在代码中使用数据库接口

### 方法一：通过依赖注入容器（推荐）

```python
from src.core.container import get_database_service

# 获取数据库服务实例
db_service = get_database_service()

# 使用数据库服务
user = db_service.create_user("张三")
```

### 方法二：直接创建实例

```python
from src.services.database import DatabaseService

# 直接创建数据库服务实例
db_service = DatabaseService()

# 使用数据库服务
user = db_service.create_user("李四")
```

### 方法三：在业务逻辑类中注入

```python
from src.core.interfaces import IDatabaseService

class MyBusinessLogic:
    def __init__(self, db_service: IDatabaseService):
        self.db_service = db_service
    
    def process_user_input(self, user_input: str):
        # 使用数据库服务
        user = self.db_service.get_user("user_123")
        # ... 业务逻辑
```

## 4. 各个实体的 CRUD 操作示例

### User（用户）操作

```python
# 创建用户
user = db_service.create_user("用户名", user_id="optional_id")

# 获取用户
user = db_service.get_user("user_id")

# 更新用户
updated_user = db_service.update_user("user_id", display_name="新用户名")

# 删除用户
success = db_service.delete_user("user_id")

# 获取所有用户
users = db_service.get_all_users()
```

### AppWindow（应用窗口）操作

```python
# 创建或获取应用窗口
app_window = db_service.get_or_create_app_window(
    process_name="notepad.exe",
    window_title="记事本"
)

# 获取应用窗口
app_window = db_service.get_app_window("window_id")

# 更新应用窗口
updated_window = db_service.update_app_window(
    "window_id",
    process_name="new_process.exe",
    window_title="新标题"
)

# 删除应用窗口
success = db_service.delete_app_window("window_id")
```

### WindowContext（窗口上下文）操作

```python
# 创建窗口上下文
context = db_service.create_window_context(
    user_id="user_123",
    window_id="window_456",
    agent_type="text_optimizer"
)

# 获取窗口上下文
context = db_service.get_window_context("context_id")

# 更新消息数量
updated_context = db_service.update_window_context_message_count(
    "context_id", 
    new_count=5
)

# 删除窗口上下文
success = db_service.delete_window_context("context_id")

# 获取用户的所有上下文
contexts = db_service.get_user_window_contexts("user_id")
```

### Message（消息）操作

```python
# 创建用户输入消息
user_message = db_service.create_message(
    context_id="context_123",
    role="user",
    message_type="user_input",  # 用户原始输入
    content="用户输入的文本"
)

# 创建 AI 输出消息
ai_message = db_service.create_message(
    context_id="context_123",
    role="assistant",
    message_type="ai_output",  # AI 处理后的输出
    content="AI 优化后的文本"
)

# 获取消息
message = db_service.get_message("message_id")

# 获取上下文的所有消息
messages = db_service.get_context_messages("context_id")

# 获取最近的消息（用于 AI 上下文）
recent_messages = db_service.get_recent_messages("context_id", limit=10)

# 删除消息
success = db_service.delete_message("message_id")
```

## 5. 依赖注入容器的使用方法

### 获取容器实例

```python
from src.core.container import get_container

container = get_container()
```

### 注册自定义服务

```python
from src.core.container import get_container
from src.services.database import DatabaseManager, DatabaseService

container = get_container()

# 注册自定义数据库服务（例如使用不同的数据库路径）
custom_db_manager = DatabaseManager("/custom/path/database.db")
custom_db_service = DatabaseService(custom_db_manager)
container.register_singleton(IDatabaseService, custom_db_service)
```

### 解析服务

```python
from src.core.interfaces import IDatabaseService
from src.core.container import resolve

# 方法1：直接解析
db_service = resolve(IDatabaseService)

# 方法2：通过容器解析
container = get_container()
db_service = container.resolve(IDatabaseService)

# 方法3：使用便捷函数
from src.core.container import get_database_service
db_service = get_database_service()
```

## 6. 数据库迁移系统的使用

### 检查迁移状态

```python
from src.services.database.migration import MigrationManager

migration_manager = MigrationManager("data/reInput.db")

# 获取迁移状态
status = migration_manager.get_migration_status()
print(f"当前版本: {status['current_version']}")
print(f"最新版本: {status['latest_version']}")
print(f"需要迁移: {status['needs_migration']}")
```

### 执行迁移

```python
# 迁移到最新版本
success = migration_manager.migrate_up()

# 迁移到指定版本
success = migration_manager.migrate_up(target_version=2)

# 回滚到指定版本
success = migration_manager.migrate_down(target_version=1)
```

### 验证数据库结构

```python
# 验证数据库结构是否正确
is_valid = migration_manager.validate_database_schema()
```

## 7. 性能优化建议

### 异步操作

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def async_database_operation():
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        # 在线程池中执行数据库操作
        result = await loop.run_in_executor(
            executor, 
            db_service.create_user, 
            "用户名"
        )
    return result
```

### 批量操作

```python
# 批量创建消息
messages_data = [
    ("context_1", "user", "user_input", "消息1"),
    ("context_1", "assistant", "ai_output", "回复1"),
    ("context_1", "user", "user_input", "消息2"),
]

for context_id, role, msg_type, content in messages_data:
    db_service.create_message(context_id, role, msg_type, content)
```

### 连接管理

```python
# 数据库管理器自动处理连接池和线程安全
# 无需手动管理连接，使用上下文管理器自动处理事务

from src.services.database import DatabaseManager

db_manager = DatabaseManager()
with db_manager.get_connection() as conn:
    # 在事务中执行多个操作
    cursor = conn.execute("SELECT * FROM users")
    results = cursor.fetchall()
```

## 8. 错误处理和日志记录

### 异常处理

```python
from src.services.database import DatabaseService
from src.utils.loguru_config import get_logger

logger = get_logger(__name__)

try:
    db_service = DatabaseService()
    user = db_service.create_user("测试用户")
    logger.info(f"成功创建用户: {user.user_id}")
except Exception as e:
    logger.error(f"创建用户失败: {e}")
    # 处理错误情况
```

### 常见异常类型

```python
# 数据库连接失败
try:
    db_service = DatabaseService()
except RuntimeError as e:
    logger.error(f"数据库初始化失败: {e}")

# 数据不存在
user = db_service.get_user("non_existent_id")
if user is None:
    logger.warning("用户不存在")

# 数据完整性错误
try:
    # 尝试创建重复的用户ID
    db_service.create_user("用户名", user_id="existing_id")
except Exception as e:
    logger.error(f"数据完整性错误: {e}")
```

## 9. 开发注意事项和最佳实践

### 线程安全

* 数据库服务使用线程本地存储，天然线程安全

* 可以在多线程环境中安全使用

* 每个线程会自动获得独立的数据库连接

### 事务管理

```python
# 使用上下文管理器自动处理事务
with db_manager.get_connection() as conn:
    # 所有操作在同一事务中
    conn.execute("INSERT INTO users ...")
    conn.execute("INSERT INTO app_windows ...")
    # 自动提交或回滚
```

### 数据验证

```python
# 在创建数据前进行验证
def create_user_safely(display_name: str):
    if not display_name or len(display_name.strip()) == 0:
        raise ValueError("用户名不能为空")
    
    if len(display_name) > 100:
        raise ValueError("用户名过长")
    
    return db_service.create_user(display_name.strip())
```

### 资源清理

```python
# 数据库服务会自动处理资源清理
# 但在测试或特殊情况下，可以手动清理
def cleanup_database_connections():
    # 清理线程本地连接
    if hasattr(db_manager, '_local'):
        if hasattr(db_manager._local, 'connection'):
            db_manager._local.connection.close()
            delattr(db_manager._local, 'connection')
```

### 数据库路径配置

```python
# 自定义数据库路径
from src.services.database import DatabaseManager

# 使用自定义路径
custom_db_manager = DatabaseManager("/path/to/custom/database.db")
db_service = DatabaseService(custom_db_manager)
```

## 10. 常见问题和解决方案

### Q1: 数据库文件被锁定

**问题**: Windows 系统下数据库文件被锁定，无法删除或移动

**解决方案**:

```python
import time
import os

def cleanup_with_retry(db_path, max_retries=3):
    for i in range(max_retries):
        try:
            # 确保所有连接都已关闭
            if hasattr(db_manager, '_local'):
                if hasattr(db_manager._local, 'connection'):
                    db_manager._local.connection.close()
            
            # 等待文件锁释放
            time.sleep(0.1)
            
            # 尝试删除文件
            if os.path.exists(db_path):
                os.remove(db_path)
            break
        except PermissionError:
            if i == max_retries - 1:
                raise
            time.sleep(0.5)
```

### Q2: 数据库初始化失败

**问题**: 数据库初始化时出现权限或路径问题

**解决方案**:

```python
import os
from pathlib import Path

def ensure_database_directory():
    db_path = "data/reInput.db"
    db_dir = Path(db_path).parent
    
    # 确保目录存在且有写权限
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # 检查写权限
    if not os.access(db_dir, os.W_OK):
        raise PermissionError(f"没有写权限: {db_dir}")
```

### Q3: 迁移失败

**问题**: 数据库迁移过程中出现错误

**解决方案**:

```python
def safe_migration():
    migration_manager = MigrationManager("data/reInput.db")
    
    # 备份数据库
    import shutil
    backup_path = "data/reInput.db.backup"
    shutil.copy2("data/reInput.db", backup_path)
    
    try:
        # 执行迁移
        success = migration_manager.migrate_up()
        if not success:
            # 恢复备份
            shutil.copy2(backup_path, "data/reInput.db")
            raise RuntimeError("迁移失败，已恢复备份")
    except Exception as e:
        # 恢复备份
        shutil.copy2(backup_path, "data/reInput.db")
        raise e
    finally:
        # 清理备份文件
        if os.path.exists(backup_path):
            os.remove(backup_path)
```

### Q4: 内存使用过高

**问题**: 长时间运行后内存使用过高

**解决方案**:

```python
# 定期清理旧数据
def cleanup_old_data():
    from datetime import datetime, timedelta
    
    # 清理30天前的数据
    cutoff_date = datetime.now() - timedelta(days=30)
    db_service.cleanup_old_data(cutoff_date)

# 在应用中定期调用
import threading
import time

def periodic_cleanup():
    while True:
        time.sleep(24 * 3600)  # 每24小时执行一次
        try:
            cleanup_old_data()
        except Exception as e:
            logger.error(f"数据清理失败: {e}")

# 启动后台清理线程
cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()
```

### Q5: 并发访问问题

**问题**: 多个进程同时访问数据库

**解决方案**:

```python
# SQLite 的 WAL 模式已经启用，支持并发读取
# 如果需要更高的并发性，考虑以下配置

def configure_high_concurrency():
    # 在数据库管理器中已经配置了以下优化:
    # - WAL 模式: 支持并发读取
    # - NORMAL 同步模式: 平衡性能和安全性
    # - 30秒超时: 避免长时间等待
    pass
```

## 总结

reInput AI 输入法的数据库系统提供了完整的数据持久化解决方案，支持用户历史记录、上下文管理和 AI 优化功能。通过合理使用数据库接口和遵循最佳实践，可以确保系统的稳定性和性能。

关键要点：

* 使用依赖注入容器管理数据库服务

* 数据库自动初始化，无需手动配置

* 支持完整的 CRUD 操作和事务管理

* 内置迁移系统支持版本升级

* 线程安全设计，支持并发访问

* 完善的错误处理和日志记录

