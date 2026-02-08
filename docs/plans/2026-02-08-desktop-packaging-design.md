# Agent Service 桌面打包设计

## 概述

将 Agent Service 打包成独立的桌面应用，支持 Windows 和 Mac 平台，以系统托盘形式运行。

## 需求

- **API Key**: 托盘菜单弹窗输入并保存到本机配置文件（`settings.json`），用户无需设置环境变量
- **运行方式**: 系统托盘应用，右键菜单可退出
- **端口**: 固定 18080
- **开机自启**: 默认启用
- **打包形式**: 便携版单文件
- **构建方式**: GitHub Actions 自动构建

## 技术架构

### 工具链

- **PyInstaller**: 将 Python 应用打包成独立可执行文件
- **pystray**: 跨平台系统托盘支持
- **Pillow**: 托盘图标处理

### 最终产物

```
Windows: AgentService.exe (单文件，约 50-80MB)
Mac:     AgentService.app (应用包，约 60-100MB)
```

### 运行流程

```
用户双击启动
    ↓
显示托盘图标
    ↓
后台启动 FastAPI 服务（端口 18080）
    ↓
设置开机自启动
    ↓
托盘菜单可退出
```

### 托盘菜单

- 状态: 运行中 (端口 18080)
- 开机启动: ✓ (可切换)
- 退出

## 项目结构

```
agents-service/
├── app/
│   ├── __init__.py
│   ├── tray.py           # 托盘应用主入口
│   ├── service.py        # FastAPI 服务启动/停止
│   ├── autostart.py      # 开机自启动管理
│   └── icon.png          # 托盘图标
├── build/
│   ├── agent_service.spec # PyInstaller 配置
│   └── assets/           # 打包资源（图标等）
├── .github/
│   └── workflows/
│       └── build.yml     # GitHub Actions 构建脚本
├── main.py               # FastAPI 入口 (保持不变)
└── requirements.txt      # 新增: pystray, Pillow
```

## 模块设计

### tray.py - 托盘应用主入口

```python
# 职责:
# 1. 创建系统托盘图标和菜单
# 2. 启动 FastAPI 服务
# 3. 处理菜单事件 (开机启动切换、退出)
```

### service.py - FastAPI 服务管理

```python
# 职责:
# 1. 在子线程/子进程中启动 uvicorn
# 2. 优雅停止服务
# 3. 检查服务状态
```

### autostart.py - 开机自启动管理

```python
# 职责:
# 1. Windows: 操作注册表 HKCU\Software\Microsoft\Windows\CurrentVersion\Run
# 2. Mac: 创建 ~/Library/LaunchAgents/com.agentservice.plist
# 3. 检查/设置/取消开机启动
```

## GitHub Actions 构建

### 触发条件

- 推送 tag (如 `v1.0.0`)
- 手动触发 (workflow_dispatch)

### 构建矩阵

```yaml
strategy:
  matrix:
    include:
      - os: windows-latest
        artifact: AgentService.exe
      - os: macos-latest
        artifact: AgentService.app
```

### 构建步骤

1. Checkout 代码
2. 设置 Python 3.11
3. 安装依赖
4. 运行 PyInstaller
5. 上传到 GitHub Releases

### 产物命名

```
AgentService-{version}-windows-x64.exe
AgentService-{version}-macos-x64.zip
```

## 配置

### 固定配置

```python
# config.py
PORT = 18080              # 服务端口
HOST = "127.0.0.1"        # 只监听本地
```

### 用户配置 (本机保存)

- `DeepSeek API Key`: 通过托盘菜单 `设置 API Key...` 弹窗输入后保存到应用数据目录下的 `settings.json`

## 依赖更新

```txt
# requirements.txt 新增
pystray>=0.19.0
Pillow>=10.0.0
```

## 测试计划

1. **托盘功能测试**: 图标显示、菜单交互
2. **服务启停测试**: 启动、停止、重启
3. **开机自启测试**: 设置、取消、验证
4. **打包测试**: Windows/Mac 构建产物运行验证
