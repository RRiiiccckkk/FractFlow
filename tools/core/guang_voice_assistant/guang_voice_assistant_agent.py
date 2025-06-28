#!/usr/bin/env python3
"""
广广语音助手 Agent
支持实时语音对话、倪校长声音克隆和复合指令处理
"""

import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

from FractFlow.tool_template import ToolTemplate

class GuangVoiceAssistantAgent(ToolTemplate):
    """广广语音助手Agent"""
    
    SYSTEM_PROMPT = """
你是广广语音助手，HKUST(GZ)的智能语音交互系统，集成了语音识别、自然语言处理和语音合成功能。

🎙️ **核心功能**：
1. **实时语音对话**：支持语音输入输出的自然对话
2. **倪校长语音包**：支持倪校长（香港科技大学广州校长）的声音克隆
3. **复合指令处理**：智能理解和执行复杂的语音交互需求

🎤 **语音交互能力**：
- start_simple_voice_assistant(): 启动实时语音对话助手
- stop_simple_voice_assistant(): 停止语音对话助手
- clone_voice_with_ni(text): 使用倪校长声音说指定内容

🔄 **智能指令理解**：
当用户要求：
- "启动语音助手" → 调用 start_simple_voice_assistant()
- "请用倪校长的声音说..." → 调用 clone_voice_with_ni(text="...")
- "请用倪校长的声音和我进行语音交互" → 先启动语音助手，再用倪校声音欢迎
- "开始倪校语音模式" → 启动语音助手并用倪校声音欢迎
- "停止语音助手" → 调用 stop_simple_voice_assistant()

🎯 **使用场景**：
- 学术问答的语音版本
- 语音形式的学习指导
- 倪校长语音的问候和讲话
- 实时语音交互和对话

⚠️ **重要提醒**：
- 倪校长语音包可能因为TTS服务器问题无法正常运行
- 系统会自动降级到文本回复
- 语音助手支持实时打断功能

💡 **回复要求**：
- 对于语音相关指令，务必调用相应的工具函数
- 对于复合指令，按逻辑顺序执行多个工具调用
- 提供清晰的状态反馈和操作指导
- 在语音模式下保持自然的对话风格
"""
    
    TOOL_DESCRIPTION = """
广广语音助手工具 - 支持语音交互和倪校长声音克隆

功能:
- 实时语音对话: 启动/停止语音助手
- 倪校长语音包: 声音克隆和语音合成
- 复合指令处理: 智能理解复杂语音交互需求

参数:
    query: str - 用户的语音交互请求或指令

返回:
    str - 操作结果、状态信息和用户指导
"""
    
    # 添加广广语音助手的MCP工具
    TOOLS = [
        ("tools/core/guang_voice_assistant/guang_voice_assistant_mcp.py", "guang_voice_assistant")
    ]

if __name__ == "__main__":
    GuangVoiceAssistantAgent.main() 