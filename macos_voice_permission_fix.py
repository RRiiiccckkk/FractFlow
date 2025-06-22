#!/usr/bin/env python3
"""
macOS语音权限修复工具
解决macOS系统下的麦克风权限和语音检测问题
"""

import subprocess
import os
import sys
from pathlib import Path

def print_banner():
    """打印横幅"""
    print("\n" + "🍎" * 20)
    print("macOS语音权限修复工具")
    print("解决麦克风权限和语音检测问题")
    print("🍎" * 20)

def check_macos_microphone_permission():
    """检查macOS麦克风权限"""
    print("\n1️⃣ 检查macOS麦克风权限...")
    
    try:
        # 使用AppleScript检查麦克风权限
        script = '''
        tell application "System Events"
            tell process "System Preferences"
                activate
            end tell
        end tell
        '''
        
        print("📋 麦克风权限检查清单:")
        print("   ☐ 系统偏好设置 > 安全性与隐私 > 隐私 > 麦克风")
        print("   ☐ 确保终端应用程序已被授权")
        print("   ☐ 确保Python解释器已被授权")
        print("   ☐ 重新启动终端应用程序")
        
        return True
        
    except Exception as e:
        print(f"❌ 权限检查失败: {e}")
        return False

def get_terminal_app_info():
    """获取当前终端应用信息"""
    print("\n2️⃣ 检测当前终端应用...")
    
    try:
        # 检查父进程来确定终端应用
        parent_pid = os.getppid()
        result = subprocess.run(['ps', '-p', str(parent_pid), '-o', 'comm='], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            terminal_name = result.stdout.strip()
            print(f"🖥️ 当前终端应用: {terminal_name}")
            
            # 检查常见终端应用
            if "Terminal" in terminal_name:
                return "Terminal.app"
            elif "iTerm" in terminal_name:
                return "iTerm.app"
            elif "Code" in terminal_name:
                return "Visual Studio Code"
            else:
                return terminal_name
        else:
            return "未知终端"
            
    except Exception as e:
        print(f"❌ 终端检测失败: {e}")
        return "未知终端"

def open_privacy_settings():
    """打开隐私设置"""
    print("\n3️⃣ 打开系统隐私设置...")
    
    try:
        # 直接打开麦克风隐私设置
        subprocess.run([
            'open', 
            'x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone'
        ])
        print("✅ 已打开麦克风隐私设置")
        return True
    except Exception as e:
        print(f"❌ 无法打开设置: {e}")
        return False

def check_audio_system():
    """检查音频系统状态"""
    print("\n4️⃣ 检查音频系统...")
    
    try:
        # 检查CoreAudio
        result = subprocess.run(['system_profiler', 'SPAudioDataType'], 
                               capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            output = result.stdout
            if "Built-in Microphone" in output or "MacBook Air Microphone" in output:
                print("✅ 检测到内置麦克风")
            else:
                print("⚠️ 未检测到内置麦克风")
            
            if "OPPO" in output:
                print("✅ 检测到OPPO耳机")
            
            return True
        else:
            print("⚠️ 无法获取音频设备信息")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️ 音频系统检查超时")
        return False
    except Exception as e:
        print(f"❌ 音频系统检查失败: {e}")
        return False

def restart_audio_services():
    """重启音频服务"""
    print("\n5️⃣ 重启音频服务...")
    
    try:
        print("🔄 正在重启CoreAudio...")
        subprocess.run(['sudo', 'killall', 'coreaudiod'], check=False)
        print("✅ CoreAudio已重启")
        
        print("🔄 正在重启音频设备...")
        subprocess.run(['sudo', 'kextunload', '/System/Library/Extensions/AppleHDA.kext'], check=False)
        subprocess.run(['sudo', 'kextload', '/System/Library/Extensions/AppleHDA.kext'], check=False)
        print("✅ 音频设备已重启")
        
        return True
    except Exception as e:
        print(f"❌ 重启音频服务失败: {e}")
        print("💡 可能需要管理员权限")
        return False

def provide_step_by_step_guide():
    """提供分步指南"""
    print("\n6️⃣ 详细解决步骤:")
    print("=" * 50)
    
    print("🔧 解决语音检测问题的步骤:")
    print("\n步骤1: 检查麦克风权限")
    print("   • 打开: 系统偏好设置 > 安全性与隐私 > 隐私")
    print("   • 选择: 麦克风")
    print("   • 确保以下应用已被授权:")
    
    terminal_app = get_terminal_app_info()
    print(f"     ✓ {terminal_app}")
    print("     ✓ Python")
    print("     ✓ /usr/bin/python3")
    
    print("\n步骤2: 重新启动应用")
    print("   • 完全退出终端应用程序")
    print("   • 重新打开终端")
    print("   • 重新运行语音测试")
    
    print("\n步骤3: 测试麦克风")
    print("   • 打开QuickTime Player")
    print("   • 文件 > 新建音频录制")
    print("   • 测试录音是否正常")
    
    print("\n步骤4: 选择正确的音频设备")
    print("   • 系统偏好设置 > 声音 > 输入")
    print("   • 选择: 内置麦克风 或 MacBook Air麦克风")
    print("   • 调整输入音量")
    
    print("\n步骤5: 重启音频系统")
    print("   • 运行: sudo killall coreaudiod")
    print("   • 重新启动计算机（如必要）")

def run_quick_fix():
    """运行快速修复"""
    print("\n🚀 运行快速修复...")
    
    # 打开隐私设置
    open_privacy_settings()
    
    print("\n⚠️ 重要提醒:")
    print("1. 在打开的隐私设置中，确保您的终端应用程序有麦克风权限")
    print("2. 如果没有看到您的终端应用，请点击'+'按钮添加")
    print("3. 添加后重新启动终端应用程序")
    print("4. 重新运行语音测试")

def main():
    """主函数"""
    print_banner()
    
    # 运行检查
    check_macos_microphone_permission()
    get_terminal_app_info()
    check_audio_system()
    
    # 提供解决方案
    provide_step_by_step_guide()
    
    # 询问是否运行快速修复
    print("\n" + "=" * 60)
    choice = input("是否运行快速修复? (y/n): ").strip().lower()
    
    if choice in ['y', 'yes', '是']:
        run_quick_fix()
    
    print("\n" + "=" * 60)
    print("🎉 权限检查完成!")
    print("💡 完成设置后，请重新运行: python voice_fix_test.py")

if __name__ == "__main__":
    main() 