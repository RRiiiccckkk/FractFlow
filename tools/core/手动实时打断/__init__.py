"""
FractFlow 手动实时打断语音控制模块

这是一个基于千问Omni实时语音API的高级语音交互模块，
支持立即打断AI回答、实时字幕显示和智能对话上下文管理。

主要功能：
- ⚡ 立即打断AI回答，无延迟
- 🧠 智能对话上下文记忆
- 🔊 高质量实时语音交互  
- 📊 完整内存监控和管理
- 🎨 实时字幕显示

文件说明：
- 手动实时打断_agent.py: 独立运行版本（终端控制）
- 手动实时打断_mcp.py: MCP服务器版本（与其他智能体联动）
- conversation_cache_manager.py: 对话缓存管理器
"""

from .手动实时打断_agent import SimpleManualVoiceController
from .conversation_cache_manager import ConversationCacheManager

__all__ = [
    'SimpleManualVoiceController',
    'ConversationCacheManager'
]

__version__ = "1.0.0"
__author__ = "FractFlow Team"
__description__ = "手动实时打断语音控制模块 - 支持立即打断AI回答的智能语音交互系统" 