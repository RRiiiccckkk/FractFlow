"""
Voice Agent - Unified Interface

This module provides a unified interface for voice interaction that can run in multiple modes:
1. MCP Server mode (default): Provides AI-enhanced voice operations as MCP tools
2. Interactive mode: Runs as an interactive voice agent with ASR/TTS capabilities
3. Single query mode: Processes a single voice query and exits

Usage:
  python voice_agent.py                        # MCP Server mode (default)
  python voice_agent.py --audio-interactive    # Audio interactive mode
  python voice_agent.py --interactive          # Interactive mode
  python voice_agent.py --query "..."          # Single query mode
"""

import os
import sys
import threading
import time
import asyncio
import pyaudio
import wave
import webrtcvad
import pygame
import langid
from transformers import AutoModelForCausalLM, AutoTokenizer
from funasr import AutoModel
import edge_tts

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(project_root)

# Import the FractFlow ToolTemplate
from FractFlow.tool_template import ToolTemplate

# --- 配置huggingFace国内镜像 ---
# os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

class VoiceAgent(ToolTemplate):
    """Voice interaction agent using ToolTemplate"""
    
    SYSTEM_PROMPT = """
你是一个智能语音助手，专门处理语音交互任务。

# 核心能力
- 语音识别（ASR）：将用户语音转换为文本
- 自然语言理解：理解用户意图并生成合适的回复
- 语音合成（TTS）：将文本回复转换为语音输出
- 实时打断：支持在语音播放过程中被用户打断

# 工作流程
1. 接收用户的语音输入
2. 使用ASR将语音转换为文本
3. 理解用户意图并生成回复
4. 使用TTS将回复转换为语音
5. 播放语音回复，同时监听用户打断

# 输出格式要求
你的回复应该包含以下信息：
- asr_result: 语音识别结果
- user_intent: 用户意图分析
- response_text: 生成的文本回复
- tts_status: 语音合成状态
- interrupt_detected: 是否检测到打断

# 重要特性
- 支持多语言识别和回复
- 实时打断机制，提升交互体验
- 保持对话的连贯性和上下文理解
- 回复简洁明了，适合语音交互

始终提供准确、及时的语音交互服务，确保用户体验流畅自然。
"""
    
    TOOLS = [
        # 可以在这里添加其他工具，如文件操作、网络搜索等
        # ("tools/core/file_io/file_io_agent.py", "file_manager"),
        ("tools/core/weather/weather_mcp.py", "forecast"),
    ]
    
    MCP_SERVER_NAME = "voice_agent"
    
    TOOL_DESCRIPTION = """Provides intelligent voice interaction capabilities including ASR, TTS, and real-time interruption.
    
    Parameters:
        query: str - Voice interaction request or text input for processing
        
    Returns:
        str - Voice interaction result including ASR, response, and TTS status
        
    Features:
        - Speech-to-Text (ASR) using SenseVoice
        - Text-to-Speech (TTS) using Edge TTS
        - Real-time interruption detection
        - Multi-language support
        - LLM-powered conversation
    """
    
    # Class-level variables for voice processing
    _voice_processor = None
    
    @classmethod
    def _get_voice_processor(cls):
        """Get or create voice processor instance"""
        if cls._voice_processor is None:
            cls._voice_processor = VoiceProcessor()
        return cls._voice_processor
    
    @classmethod
    def create_config(cls):
        """Custom configuration for Voice agent"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        return ConfigManager(
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=10,  # Voice interactions may need more iterations
            custom_system_prompt=cls.SYSTEM_PROMPT,
            tool_calling_version='turbo'
        )
    
#     @classmethod
#     async def _mcp_tool_function(cls, query: str) -> str:
#         """Enhanced MCP tool function with voice processing capabilities"""
#         try:
#             # Get voice processor
#             voice_processor = cls._get_voice_processor()
            
#             # Process the query through voice pipeline
#             result = await voice_processor.process_text_query(query)
            
#             return f"""
# Voice Agent Processing Result:
# - Query: {query}
# - ASR Status: Text input (no ASR needed)
# - Response: {result['response_text']}
# - TTS Status: Ready for synthesis
# - Language: {result.get('language', 'auto')}
# - Interrupt Status: None (text input)
# """
#         except Exception as e:
#             return f"Voice Agent Error: {str(e)}"

if __name__ == "__main__":
    VoiceAgent.main() 