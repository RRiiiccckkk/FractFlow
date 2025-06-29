#!/usr/bin/env python3
"""
测试广广语音助手的完整功能
包括新的 --voice-interactive 模式
"""

import asyncio
import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(current_dir)
sys.path.append(project_root)

from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager

async def test_voice_interactive_mode():
    """测试语音交互模式"""
    print("🎤 测试广广语音助手 - Voice Interactive 模式")
    print("=" * 50)
    
    # 创建配置
    config = ConfigManager(
        provider='qwen',
        custom_system_prompt="""
你是广广语音助手，支持语音交互和倪校长声音克隆。

🎙️ 核心功能：
- 启动/停止语音助手
- 倪校长语音包
- 复合指令处理

请根据用户指令调用相应的工具函数。
"""
    )
    
    # 创建Agent
    agent = Agent(config=config)
    
    # 添加语音助手工具
    agent.add_tool(
        tool_path="tools/core/realtime_voice_interactive/realtime_voice_interactive_mcp.py",
        tool_name="realtime_voice_interactive"
    )
    
    try:
        # 初始化Agent
        await agent.initialize()
        print("✅ Agent初始化成功")
        
        # 测试用例
        test_queries = [
            "启动语音助手",
            "请用倪校长的声音说：欢迎使用HKUST广州语音助手！",
            "请用倪校长的声音和我进行语音交互",
            "停止语音助手"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📋 测试 {i}: {query}")
            print("-" * 30)
            
            try:
                result = await agent.process_query(query)
                print(f"✅ 结果: {result}")
            except Exception as e:
                print(f"❌ 错误: {e}")
            
            # 等待一下，避免请求过快
            await asyncio.sleep(1)
    
    finally:
        await agent.shutdown()
        print("\n🛑 测试完成，Agent已关闭")

async def test_mode_switching():
    """测试模式切换功能"""
    print("\n🔄 测试模式切换功能")
    print("=" * 50)
    
    # 导入前端助手
    from 前端.hkust_ai_assistant_entry import HKUSTAIAssistant, AssistantMode
    
    # 创建学术模式助手
    assistant = HKUSTAIAssistant(AssistantMode.ACADEMIC_QA)
    
    try:
        # 初始化
        await assistant.initialize()
        print("✅ 学术模式助手初始化成功")
        
        # 测试学术问题
        response = await assistant.process_query("什么是深度学习？")
        print(f"📚 学术回答: {response[:100]}...")
        
        # 测试语音模式激活
        response = await assistant.process_query("voice")
        print(f"🎤 语音激活: {response}")
        
        # 测试语音指令
        response = await assistant.process_query("启动语音助手")
        print(f"🎙️ 语音指令: {response}")
        
        # 关闭语音模式
        response = await assistant.process_query("voice off")
        print(f"💬 文本模式: {response}")
        
    finally:
        await assistant.shutdown()
        print("🛑 模式切换测试完成")

async def test_command_line_modes():
    """测试命令行模式"""
    print("\n📝 测试命令行参数支持")
    print("=" * 50)
    
    print("✅ 支持的命令行参数:")
    print("  python 前端/hkust_ai_assistant_entry.py --voice-interactive")
    print("  python 前端/hkust_ai_assistant_entry.py --mode voice")
    print("  python 前端/hkust_ai_assistant_entry.py --mode academic")
    print("  python 前端/hkust_ai_assistant_entry.py --query '测试问题'")
    print()
    print("✅ 工具级别语音交互:")
    print("  python tools/core/realtime_voice_interactive/realtime_voice_interactive_agent.py --voice-interactive")
    print("  python tools/core/file_io/file_io_agent.py --voice-interactive")
    print("  python tools/core/websearch/websearch_agent.py --voice-interactive")

if __name__ == "__main__":
    print("🚀 FractFlow Voice Interactive 功能测试")
    print("=" * 60)
    
    # 检查API密钥
    if not os.getenv("QWEN_API_KEY") and not os.getenv("DASHSCOPE_API_KEY"):
        print("🚨 警告: 未找到Qwen API密钥，某些功能可能无法正常工作")
    
    asyncio.run(test_voice_interactive_mode())
    asyncio.run(test_mode_switching())
    asyncio.run(test_command_line_modes())
    
    print("\n🎉 所有测试完成！")
    print("💡 使用提示:")
    print("   1. 运行 'python 前端/hkust_ai_assistant_entry.py --voice-interactive' 体验语音模式")
    print("   2. 在任何文本交互中输入 'voice' 激活语音功能")  
    print("   3. 使用 'voice off' 返回文本模式")
    print("   4. 所有工具都支持 --voice-interactive 参数") 