#!/usr/bin/env python3
"""
音频设备诊断工具
帮助诊断和解决语音检测问题
"""

import time
import numpy as np
import sys
import os

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

# 音频参数
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16 if HAS_PYAUDIO else None

def print_banner():
    """打印诊断横幅"""
    print("\n" + "=" * 60)
    print("🔧 音频设备诊断工具")
    print("🎤 解决语音检测问题")
    print("=" * 60)

def check_pyaudio():
    """检查PyAudio安装"""
    print("\n1️⃣ 检查PyAudio...")
    if not HAS_PYAUDIO:
        print("❌ PyAudio未安装")
        print("💡 解决方案: 运行 'uv add pyaudio' 或 'pip install pyaudio'")
        return False
    
    print(f"✅ PyAudio已安装 (版本: {pyaudio.__version__})")
    return True

def list_audio_devices():
    """列出所有音频设备"""
    print("\n2️⃣ 扫描音频设备...")
    
    if not HAS_PYAUDIO:
        return
    
    p = pyaudio.PyAudio()
    device_count = p.get_device_count()
    
    print(f"🎵 发现 {device_count} 个音频设备:")
    print("-" * 50)
    
    input_devices = []
    
    for i in range(device_count):
        info = p.get_device_info_by_index(i)
        device_type = []
        
        if info['maxInputChannels'] > 0:
            device_type.append("输入")
            input_devices.append(i)
        if info['maxOutputChannels'] > 0:
            device_type.append("输出")
            
        print(f"设备 {i}: {info['name']}")
        print(f"   类型: {' | '.join(device_type)}")
        print(f"   输入通道: {info['maxInputChannels']}")
        print(f"   输出通道: {info['maxOutputChannels']}")
        print(f"   采样率: {info['defaultSampleRate']}")
        print("-" * 50)
    
    # 显示默认设备
    try:
        default_input = p.get_default_input_device_info()
        default_output = p.get_default_output_device_info()
        
        print(f"\n🎤 默认输入设备: {default_input['name']} (ID: {default_input['index']})")
        print(f"🔊 默认输出设备: {default_output['name']} (ID: {default_output['index']})")
    except Exception as e:
        print(f"⚠️ 获取默认设备失败: {e}")
    
    p.terminate()
    return input_devices

def test_microphone_input(device_id=None):
    """测试麦克风输入"""
    print("\n3️⃣ 测试麦克风输入...")
    
    if not HAS_PYAUDIO:
        print("❌ PyAudio不可用")
        return False
    
    p = pyaudio.PyAudio()
    
    try:
        # 创建输入流
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=device_id,
            frames_per_buffer=CHUNK_SIZE
        )
        
        print("🎤 正在测试麦克风...")
        print("📢 请对着麦克风说话 (测试10秒)")
        print("🔊 观察音量指示器:")
        
        max_volume = 0
        total_samples = 0
        active_samples = 0
        
        for i in range(int(10 * SAMPLE_RATE / CHUNK_SIZE)):  # 10秒测试
            data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            
            # 转换为numpy数组分析音量
            audio_data = np.frombuffer(data, dtype=np.int16)
            if len(audio_data) > 0:
                volume = np.sqrt(np.mean(audio_data.astype(np.float64)**2))
                if not np.isnan(volume):
                    max_volume = max(max_volume, volume)
                else:
                    volume = 0
            else:
                volume = 0
            
            total_samples += 1
            if volume > 100:  # 阈值
                active_samples += 1
            
            # 显示音量条
            bar_length = int(volume / 200)  # 缩放显示
            bar = "█" * min(bar_length, 50)
            print(f"\r音量: [{bar:<50}] {volume:.0f} ", end="", flush=True)
            
            time.sleep(0.01)
        
        print(f"\n\n📊 测试结果:")
        print(f"   最大音量: {max_volume:.0f}")
        print(f"   活跃样本: {active_samples}/{total_samples} ({active_samples/total_samples*100:.1f}%)")
        
        if max_volume < 50:
            print("⚠️ 音量过低，可能存在问题:")
            print("   • 检查麦克风是否正常工作")
            print("   • 检查系统音频设置")
            print("   • 检查麦克风权限")
            return False
        elif active_samples < total_samples * 0.1:
            print("⚠️ 检测到的语音活动较少:")
            print("   • 尝试更靠近麦克风说话")
            print("   • 增加说话音量")
        else:
            print("✅ 麦克风工作正常!")
            return True
        
        stream.stop_stream()
        stream.close()
        
    except Exception as e:
        print(f"❌ 麦克风测试失败: {e}")
        return False
    finally:
        p.terminate()

def check_system_permissions():
    """检查系统权限"""
    print("\n4️⃣ 检查系统权限...")
    
    import platform
    system = platform.system()
    
    if system == "Darwin":  # macOS
        print("🍎 macOS系统检查:")
        print("   请确保以下权限已启用:")
        print("   • 系统偏好设置 > 安全性与隐私 > 隐私 > 麦克风")
        print("   • 添加您的终端应用程序（Terminal/iTerm等）")
        print("   • 添加Python解释器")
        
    elif system == "Windows":
        print("🪟 Windows系统检查:")
        print("   请确保以下设置正确:")
        print("   • 设置 > 隐私 > 麦克风")
        print("   • 允许应用访问麦克风")
        print("   • 检查Windows Defender是否阻止")
        
    elif system == "Linux":
        print("🐧 Linux系统检查:")
        print("   请检查以下:")
        print("   • PulseAudio/ALSA配置")
        print("   • 用户是否在audio组中")
        print("   • 设备权限: ls -l /dev/snd/")

def suggest_fixes():
    """建议解决方案"""
    print("\n5️⃣ 常见解决方案:")
    print("=" * 40)
    
    print("🔧 如果语音检测失败，请尝试:")
    print("   1. 重启音频服务")
    print("   2. 更换默认音频设备")
    print("   3. 调整麦克风增益")
    print("   4. 检查耳机/外接麦克风连接")
    print("   5. 重启应用程序")
    
    print("\n💡 VAD参数调优:")
    print("   • threshold: 0.1-0.5 (更低=更敏感)")
    print("   • silence_duration_ms: 300-1000")
    print("   • prefix_padding_ms: 100-500")

def interactive_device_selection():
    """交互式设备选择"""
    if not HAS_PYAUDIO:
        return None
    
    input_devices = list_audio_devices()
    
    if not input_devices:
        print("❌ 未找到可用的输入设备")
        return None
    
    print(f"\n📝 可用输入设备ID: {input_devices}")
    
    try:
        choice = input("\n请选择要测试的设备ID (回车使用默认): ").strip()
        if choice:
            device_id = int(choice)
            if device_id in input_devices:
                return device_id
            else:
                print("❌ 无效的设备ID")
                return None
        return None  # 使用默认设备
    except ValueError:
        print("❌ 请输入有效的数字")
        return None

def main():
    """主诊断流程"""
    print_banner()
    
    # 检查基础环境
    if not check_pyaudio():
        return
    
    # 扫描设备
    input_devices = list_audio_devices()
    
    # 权限检查
    check_system_permissions()
    
    # 交互式设备选择和测试
    print("\n" + "=" * 60)
    choice = input("是否进行麦克风测试? (y/n): ").strip().lower()
    
    if choice in ['y', 'yes', '是']:
        device_id = interactive_device_selection()
        success = test_microphone_input(device_id)
        
        if not success:
            suggest_fixes()
        else:
            print("\n🎉 音频系统工作正常!")
            print("如果语音对话仍有问题，可能是服务器端VAD配置问题")
    
    print("\n" + "=" * 60)
    print("🔧 诊断完成!")
    print("💡 如果问题仍然存在，请检查网络连接和API密钥")

if __name__ == "__main__":
    main() 