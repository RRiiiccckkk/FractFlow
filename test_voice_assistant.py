#!/usr/bin/env python3
"""
Realtime Voice Interactive Test Script
Author: FractFlow Team
Brief: Test script for Realtime Voice Interactive Assistant with enhanced interrupt capabilities
"""

import asyncio
import sys
import os
import threading
import time

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_import_modules():
    """测试模块导入"""
    print("🧪 测试模块导入...")
    
    try:
        # 测试核心模块
        from tools.core.realtime_voice_interactive.realtime_voice_interactive import RealtimeVoiceInteractiveAgent, run_realtime_voice_interactive
        print("✅ RealtimeVoiceInteractiveAgent 导入成功")
        
        # 测试MCP服务器函数
        from tools.core.realtime_voice_interactive.realtime_voice_interactive_mcp import (
            start_realtime_voice_interactive,
            stop_realtime_voice_interactive,
            get_voice_interactive_status
        )
        from tools.core.realtime_voice_interactive.ni_realtime_voice_interactive_mcp import (
            start_ni_realtime_voice_interactive,
            stop_ni_realtime_voice_interactive,
            get_ni_voice_interactive_status,
            clone_voice_with_ni
        )
        print("✅ MCP服务器模块导入成功")
        
        # 测试Agent模块
        from tools.core.realtime_voice_interactive.realtime_voice_interactive_agent import RealtimeVoiceInteractiveAgent
        from tools.core.realtime_voice_interactive.ni_realtime_voice_interactive_agent import NiRealtimeVoiceInteractiveAgent
        print("✅ Agent代理模块导入成功")
        
        # 测试配置模块
        from tools.core.realtime_voice_interactive.voice_config import setup_api_keys, get_voice_session_config
        print("✅ 配置模块导入成功")
        
        # 测试倪校TTS中断功能
        from tools.core.realtime_voice_interactive.ni_voice_clone_client.main import set_interrupt, clear_interrupt, is_interrupted
        print("✅ 倪校TTS中断控制导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_interrupt_mechanism():
    """测试中断机制"""
    print("\n🧪 测试快速中断机制...")
    
    try:
        from tools.core.realtime_voice_interactive.ni_voice_clone_client.main import set_interrupt, clear_interrupt, is_interrupted
        
        # 测试中断信号设置和清除
        clear_interrupt()
        assert not is_interrupted(), "初始状态应该是未中断"
        print("✅ 初始状态检查通过")
        
        set_interrupt()
        assert is_interrupted(), "设置中断后应该是中断状态"
        print("✅ 中断信号设置检查通过")
        
        clear_interrupt()
        assert not is_interrupted(), "清除中断后应该是未中断状态"
        print("✅ 中断信号清除检查通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 中断机制测试失败: {e}")
        return False

def test_voice_agent_init():
    """测试语音助手初始化"""
    print("\n🧪 测试实时语音交互助手初始化...")
    
    try:
        from tools.core.realtime_voice_interactive.realtime_voice_interactive import RealtimeVoiceInteractiveAgent
        
        # 测试默认模式初始化
        agent_default = RealtimeVoiceInteractiveAgent(api_key="test", voice_mode="default")
        assert agent_default.voice_mode == "default"
        assert hasattr(agent_default, 'tts_interrupt_event')
        assert hasattr(agent_default, 'volume_threshold')
        assert hasattr(agent_default, 'background_noise_level')
        print("✅ 默认模式初始化检查通过")
        
        # 测试倪校模式初始化
        agent_ni = RealtimeVoiceInteractiveAgent(api_key="test", voice_mode="ni")
        assert agent_ni.voice_mode == "ni"
        assert hasattr(agent_ni, 'tts_interrupt_event')
        assert hasattr(agent_ni, 'volume_samples')
        print("✅ 倪校模式初始化检查通过")
        
        # 测试改进的音量检测参数
        assert agent_ni.volume_threshold == 25  # 提高的基础阈值
        assert agent_ni.volume_buffer_size == 3  # 连续性检测窗口
        assert agent_ni.calibration_samples == 0  # 校准采样计数
        print("✅ 音量检测参数检查通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 实时语音交互助手初始化测试失败: {e}")
        return False

def test_multilevel_interrupt():
    """测试多级打断机制"""
    print("\n🧪 测试多级打断机制...")
    
    try:
        from tools.core.realtime_voice_interactive.realtime_voice_interactive import RealtimeVoiceInteractiveAgent
        
        # 创建倪校模式agent
        agent = RealtimeVoiceInteractiveAgent(api_key="test", voice_mode="ni")
        
        # 模拟AI正在说话状态
        agent.is_ai_speaking = True
        agent.is_tts_playing = True
        agent.current_ai_response = "这是一个测试回答"
        
        # 测试多级打断
        agent._interrupt_ai_multilevel()
        
        # 验证打断效果
        assert agent.interrupt_detected == True, "应该设置中断检测标志"
        assert agent.is_ai_speaking == False, "应该停止AI说话状态"
        assert agent.is_tts_playing == False, "应该停止TTS播放状态"
        assert agent.tts_interrupt_event.is_set() == True, "应该设置TTS中断事件"
        assert agent.current_ai_response == "", "应该清空当前回答"
        
        print("✅ 多级打断机制检查通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 多级打断机制测试失败: {e}")
        return False

async def test_voice_agent_performance():
    """测试语音助手性能（模拟）"""
    print("\n🧪 测试实时语音交互助手性能响应...")
    
    try:
        from tools.core.realtime_voice_interactive.realtime_voice_interactive import RealtimeVoiceInteractiveAgent
        
        # 创建agent
        agent = RealtimeVoiceInteractiveAgent(api_key="test", voice_mode="ni")
        
        # 模拟快速打断场景
        start_time = time.time()
        
        # 设置AI说话状态
        agent.is_ai_speaking = True
        agent.is_tts_playing = True
        
        # 执行打断
        agent._interrupt_ai_multilevel()
        
        # 计算响应时间
        response_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        print(f"🚀 打断响应时间: {response_time:.2f}ms")
        
        # 验证响应时间在期望范围内（应该小于10ms）
        assert response_time < 10, f"打断响应时间应该小于10ms，实际: {response_time:.2f}ms"
        print("✅ 打断响应时间检查通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 实时语音交互助手性能测试失败: {e}")
        return False

def test_mcp_servers():
    """测试MCP服务器功能"""
    print("\n🧪 测试MCP服务器功能...")
    
    try:
        # 测试默认模式MCP功能
        from tools.core.realtime_voice_interactive.realtime_voice_interactive_mcp import (
            get_voice_interactive_status
        )
        
        # 测试状态查询
        status = get_voice_interactive_status()
        assert isinstance(status, str), "状态应该返回字符串"
        print("✅ 默认模式MCP功能测试通过")
        
        # 测试倪校模式MCP功能
        from tools.core.realtime_voice_interactive.ni_realtime_voice_interactive_mcp import (
            get_ni_voice_interactive_status,
            clone_voice_with_ni
        )
        
        # 测试倪校状态查询
        ni_status = get_ni_voice_interactive_status()
        assert isinstance(ni_status, str), "倪校状态应该返回字符串"
        print("✅ 倪校模式MCP功能测试通过")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP服务器功能测试失败: {e}")
        return False

async def run_all_tests():
    """运行所有测试"""
    print("🏫 Realtime Voice Interactive 增强版测试套件")
    print("🎓 Enhanced Interrupt & Performance Test Suite")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_import_modules()),
        ("中断机制", test_interrupt_mechanism()),
        ("实时语音交互助手初始化", test_voice_agent_init()),
        ("多级打断机制", test_multilevel_interrupt()),
        ("性能响应", await test_voice_agent_performance()),
        ("MCP服务器", test_mcp_servers()),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, result in tests:
        if result:
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！增强版实时语音交互助手已准备就绪！")
        print("\n🚀 新功能亮点:")
        print("   • ⚡ 100-300ms极速打断响应")
        print("   • 🔊 动态音量检测+环境适应")
        print("   • 🛑 多级打断机制")
        print("   • 🎯 智能连续性验证")
        print("   • 🚀 倪校TTS流式播放优化")
        print("   • 🎓 包含倪校声音克隆技术")
    else:
        print(f"⚠️ {total - passed} 个测试失败，请检查相关模块")
    
    return passed == total

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1) 