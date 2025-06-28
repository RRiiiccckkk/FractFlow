#!/usr/bin/env python3
"""
run_voice_assistant_test.py
Author: FractFlow Team
Brief: Example script to correctly call the Guang Voice Assistant MCP tool within the FractFlow framework.
"""

import asyncio
import os
import sys

# Ensure the project root is in the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager

async def main():
    """
    Main function to initialize the agent and call the voice assistant tools.
    """
    print("🚀 Initializing FractFlow Agent to test Guang Voice Assistant...")

    # 1. Create a ConfigManager instance and specify the provider.
    # All agent components will now use this configuration.
    # Include custom system prompt for Ni's voice package awareness
    ni_voice_system_prompt = """你是HKUST(GZ) AI Assistant，香港科技大学广州的智能助手，具备语音合成和对话功能。你有以下特殊能力：

🎙️ **倪校长语音包功能**：
当用户要求"用倪校长的声音说..."、"请以倪校长的声音讲出..."、"让倪校长说..."或类似请求时，
你需要调用 clone_voice_with_ni 工具来实现倪校长（香港科技大学广州校长）的声音克隆。

🎤 **语音对话功能**：
- 可以启动和停止实时语音对话助手
- 支持语音识别和语音合成
- 支持实时打断功能

🔄 **复合指令处理**：
- "请用倪校长的声音和我进行语音交互" → 先调用 start_simple_voice_assistant()，再用倪校声音欢迎
- "启动倪校语音模式" → 启动语音助手并设置倪校声音为默认
- "开始语音交互，用倪校长声音回复" → 组合使用两个功能

📋 **使用规则**：
1. 单一倪校声音请求：使用 clone_voice_with_ni(text="要说的内容")
2. 单一语音对话请求：使用 start_simple_voice_assistant()
3. 复合请求：先启动语音助手，再用倪校声音说欢迎词
4. 停止请求：使用 stop_simple_voice_assistant()

💡 **示例场景**：
- "请用倪校长的声音说欢迎词" → 调用 clone_voice_with_ni
- "启动语音助手" → 调用 start_simple_voice_assistant
- "请用倪校长的声音和我进行语音交互" → 调用 start_simple_voice_assistant + clone_voice_with_ni("欢迎使用语音交互功能")
- "开始倪校语音模式" → 启动语音助手并用倪校声音欢迎

请根据用户的具体需求，智能选择合适的工具来完成任务。对于复合请求，请按逻辑顺序执行多个工具调用。"""

    config = ConfigManager(
        provider='qwen',
        custom_system_prompt=ni_voice_system_prompt
    )

    # 2. Initialize the Agent with the configuration.
    agent = Agent(config=config)

    # 3. Add the new voice assistant tool to the agent.
    # The key 'guang_voice_assistant' is a logical name.
    # The value is the path to the MCP server script.
    agent.add_tool(
        tool_path="tools/core/guang_voice_assistant/guang_voice_assistant_mcp.py",
        tool_name="guang_voice_assistant"
    )

    # 4. Start the agent system. (Now called `initialize`)
    # This will initialize the orchestrator and launch the MCP server for our voice tool.
    await agent.initialize()
    print("✅ Agent started, and guang_voice_assistant MCP server should be running.")

    try:
        # --- Test Case 1: Call Ni's Voice Clone ---
        print("\n" + "="*50)
        print("🎙️ Test Case 1: Calling Ni's voice clone tool...")
        query1 = "请用倪校长的声音说：'欢迎来到香港科技大学广州！'"
        print(f"👤 User Query: {query1}")
        
        # The agent's LLM will understand the query and call the 'clone_voice_with_ni' tool.
        response1 = await agent.process_query(query1)
        print(f"🤖 Agent Response: \n{response1}")
        print("="*50)

        # --- Test Case 2: Start the interactive voice assistant ---
        # Note: The interactive assistant is a long-running process.
        print("\n" + "="*50)
        print("🎤 Test Case 2: Attempting to start the interactive voice assistant...")
        query2 = "启动语音对话助手"
        print(f"👤 User Query: {query2}")

        response2 = await agent.process_query(query2)
        print(f"🤖 Agent Response: \n{response2}")
        print("\n⚠️  Note: The interactive assistant is designed for real-time loops.")
        print("This test confirms the tool can be called. To run it fully, you might need a dedicated script.")
        print("="*50)

    except Exception as e:
        print(f"❌ An error occurred during the test: {e}")
    finally:
        # 5. Shut down the agent system.
        # This will terminate the orchestrator and all launched MCP servers.
        print("\n🧹 Shutting down the agent and all tool servers...")
        await agent.shutdown()
        print("✅ System shut down gracefully.")


if __name__ == "__main__":
    # Ensure you have the necessary environment variables set for Qwen.
    if not os.getenv("QWEN_API_KEY") and not os.getenv("DASHSCOPE_API_KEY"):
        print("🚨 Error: API key for Qwen/DashScope not found in environment variables.")
        print("Please set QWEN_API_KEY or DASHSCOPE_API_KEY.")
    else:
        asyncio.run(main()) 