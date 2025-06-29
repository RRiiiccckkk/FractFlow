#!/usr/bin/env python3
"""
ni_realtime_voice_interactive_mcp.py
Author: FractFlow Team
Brief: MCP server for Realtime Voice Interactive Assistant - Ni Voice Mode

TOOL_DESCRIPTION = '''
实时语音交互助手 - 倪校音色版（包含声音克隆）

这是一个基于千问Omni + 倪校声音克隆的实时语音对话系统，专为HKUST-GZ设计。

核心功能：
- 🎤 实时语音识别：支持中文语音输入，自动转换为文本
- 🎓 倪校音色合成：使用GPT-SoVITS技术克隆的倪校长声音
- ⚡ 智能快速打断：100-300ms极速响应，支持用户随时打断AI回答
- 🚀 流式TTS播放：每句话生成后立即播放，大幅提升响应速度
- 🛑 多级打断机制：立即音频停止+队列清理+状态重置
- 🔧 动态音量检测：自动适应环境噪音，智能连续性验证

技术特性：
- 分句流式播放：边生成边播放，首句响应<2秒
- 精确打断控制：支持句子级别的精确打断
- API参数优化：更快的文本生成速度

使用方式：
start_ni_realtime_voice_interactive() - 启动倪校音色语音助手
stop_ni_realtime_voice_interactive() - 停止语音助手
get_ni_voice_interactive_status() - 查询运行状态
clone_voice_with_ni(text) - 直接用倪校声音说指定文本

注意事项：
- 需要麦克风和扬声器设备
- 需要倪校TTS服务器运行在 10.120.17.57:9880
- 建议在安静环境中使用以获得最佳体验
'''
"""

import asyncio
import threading
from mcp.server.fastmcp import FastMCP

# Global state
voice_task = None
stop_event = threading.Event()

from tools.core.realtime_voice_interactive.realtime_voice_interactive import RealtimeVoiceInteractiveAgent
from tools.core.realtime_voice_interactive.voice_config import setup_api_keys

mcp = FastMCP("ni_realtime_voice_interactive")

@mcp.tool()
async def start_ni_realtime_voice_interactive() -> str:
    """启动实时语音交互助手 - 倪校音色版（流式TTS优化）"""
    global voice_task, stop_event
    
    try:
        if voice_task and not voice_task.done():
            return "⚠️ 倪校实时语音交互助手已经在运行中"
        
        # Reset stop event
        stop_event.clear()
        
        # Start voice interactive task
        voice_task = asyncio.create_task(_run_ni_voice_interactive_task())
        
        return "✅ 倪校实时语音交互助手已启动（流式TTS优化版）！\n🎓 倪校长现在在听您说话！"
        
    except Exception as e:
        return f"❌ 启动失败：{str(e)}"

@mcp.tool()
async def stop_ni_realtime_voice_interactive() -> str:
    """停止倪校实时语音交互助手"""
    global voice_task, stop_event
    
    try:
        if not voice_task or voice_task.done():
            return "⚠️ 倪校实时语音交互助手未在运行"
        
        # Set stop event
        stop_event.set()
        
        # Cancel the task
        voice_task.cancel()
        
        try:
            await voice_task
        except asyncio.CancelledError:
            pass
        
        return "✅ 倪校实时语音交互助手已停止"
        
    except Exception as e:
        return f"❌ 停止失败：{str(e)}"

@mcp.tool()
def get_ni_voice_interactive_status() -> str:
    """获取倪校实时语音交互助手状态"""
    global voice_task
    
    if not voice_task:
        return "🔴 倪校实时语音交互助手未启动"
    elif voice_task.done():
        return "🟡 倪校实时语音交互助手已停止"
    else:
        return "🟢 倪校实时语音交互助手正在运行中（流式TTS优化版）"

@mcp.tool()
def clone_voice_with_ni(text: str) -> str:
    """使用倪校声音克隆技术播放指定文本"""
    try:
        if not text.strip():
            return "❌ 文本不能为空"
        
        # 导入倪校TTS功能
        from tools.core.realtime_voice_interactive.ni_voice_clone_client.main import play_ni_voice
        
        # 播放倪校声音
        play_ni_voice(text)
        
        return f"✅ 倪校声音播放完成：{text}"
        
    except ImportError:
        return "❌ 倪校TTS模块不可用，请检查服务器连接"
    except Exception as e:
        return f"❌ 播放失败：{str(e)}"

async def _run_ni_voice_interactive_task():
    """运行倪校语音交互任务"""
    from tools.core.realtime_voice_interactive.realtime_voice_interactive import run_realtime_voice_interactive
    
    try:
        await run_realtime_voice_interactive("ni")
    except Exception as e:
        print(f"倪校语音交互任务错误: {e}")

class NiRealtimeVoiceInteractiveServer:
    """倪校实时语音交互MCP服务器"""
    
    def __init__(self):
        self.mcp = mcp

if __name__ == "__main__":
    import sys
    mcp.run(sys.argv) 