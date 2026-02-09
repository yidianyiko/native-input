#!/usr/bin/env python3
"""
配置一致性检查脚本
检查项目中所有配置管理组件的一致性
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.config import ConfigManager
from src.config.hotkey_config import PynputHotkeyConfig, HotkeyAction


def check_hotkey_consistency():
    """检查热键配置一致性"""
    print("检查热键配置一致性...")
    
    # 初始化配置管理器
    cm = ConfigManager()
    
    # 获取ConfigManager中的热键配置
    config_hotkeys = cm.get_hotkeys()
    
    # 获取PynputHotkeyConfig中的热键配置
    ptc = PynputHotkeyConfig()
    ptc.load_from_config_manager(cm)
    ptc_hotkeys = {action.name: config.hotkey_string for action, config in ptc.get_all_hotkey_configs().items()}
    
    # 检查一致性
    issues = []
    all_keys = set(config_hotkeys.keys()) | set(ptc_hotkeys.keys())
    
    for key in all_keys:
        if key not in config_hotkeys:
            issues.append(f"{key}: 只在PynputHotkeyConfig中存在")
        elif key not in ptc_hotkeys:
            issues.append(f"{key}: 只在ConfigManager中存在")
        elif config_hotkeys[key] != ptc_hotkeys[key]:
            issues.append(f"{key}: ConfigManager='{config_hotkeys[key]}', Pynput='{ptc_hotkeys[key]}'")
        else:
            print(f"{key}: {config_hotkeys[key]}")
    
    if issues:
        print("\n 发现热键配置不一致:")
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print("热键配置完全一致")
        return True


def check_default_config_consistency():
    """检查默认配置一致性"""
    print("\n检查默认配置一致性...")
    
    cm = ConfigManager()
    
    # 检查基本配置是否可以访问
    actual_hotkeys = cm.get("hotkeys", {})
    actual_ui = cm.get("ui", {})
    actual_ai = cm.get("ai_services", {})
    
    print("配置访问检查:")
    print(f"热键配置: {len(actual_hotkeys)} 项")
    print(f"UI配置: {len(actual_ui)} 项")
    print(f"AI服务配置: {len(actual_ai)} 项")
    
    # 简化的配置验证
    if cm.validate():
        print("配置验证通过")
        return True
    else:
        print("配置验证失败")
        return False


def check_config_file_structure():
    """检查配置文件结构"""
    print("\n检查配置文件结构...")
    
    config_file = project_root / "config.json"
    if not config_file.exists():
        print("config.json 文件不存在")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        required_sections = ["hotkeys", "ui", "ai_services", "agents", "system"]
        missing_sections = []
        
        for section in required_sections:
            if section not in config_data:
                missing_sections.append(section)
            else:
                print(f"配置节存在: {section}")
        
        if missing_sections:
            print(f"缺失配置节: {missing_sections}")
            return False
        
        # 检查热键配置结构
        hotkeys = config_data.get("hotkeys", {})
        expected_hotkeys = ["SHOW_FLOATING_WINDOW", "VOICE_INPUT", "QUICK_TRANSLATE", 
                          "QUICK_POLISH", "TOGGLE_RECORDING", "EMERGENCY_STOP"]
        
        missing_hotkeys = []
        for hotkey in expected_hotkeys:
            if hotkey not in hotkeys:
                missing_hotkeys.append(hotkey)
            else:
                print(f"热键配置存在: {hotkey}")
        
        if missing_hotkeys:
            print(f"缺失热键配置: {missing_hotkeys}")
            return False
        
        print("配置文件结构检查通过")
        return True
        
    except json.JSONDecodeError as e:
        print(f"配置文件JSON格式错误: {e}")
        return False
    except Exception as e:
        print(f"配置文件检查失败: {e}")
        return False


def main():
    """主检查函数"""
    print("=" * 50)
    print("AI输入法工具 - 配置一致性检查")
    print("=" * 50)
    
    checks = [
        ("配置文件结构", check_config_file_structure),
        ("热键配置一致性", check_hotkey_consistency),
        ("默认配置一致性", check_default_config_consistency),
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        try:
            if check_func():
                passed += 1
            print()  # 空行分隔
        except Exception as e:
            print(f"{name} 检查失败: {e}")
            print()
    
    print("=" * 50)
    print(f"检查结果: {passed}/{total} 通过")
    
    if passed == total:
        print("所有配置一致性检查通过!")
        return 0
    else:
        print(" 存在配置一致性问题，请修复后重新检查")
        return 1


if __name__ == "__main__":
    sys.exit(main())