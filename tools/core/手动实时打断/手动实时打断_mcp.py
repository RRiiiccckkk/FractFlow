#!/usr/bin/env python3
"""
FractFlow 手动实时打断语音控制 - MCP服务器版
基于千问Omni实时语音API，支持立即打断AI回答功能
"""

import asyncio
import json
import logging
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from typing import Any, Sequence
import sys
import os

# 添加项目路径支持
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入手动实时打断Agent
from tools.core.手动实时打断.手动实时打断_agent import SimpleManualVoiceController

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("手动实时打断_mcp")

# 创建MCP服务器
server = Server("手动实时打断_mcp")

# 全局变量存储控制器实例
voice_controller = None

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """列出可用的工具"""
    return [
        types.Tool(
            name="start_manual_interrupt_voice_control",
            description="启动手动实时打断语音控制助手",
            inputSchema={
                "type": "object",
                "properties": {
                    "enable_context": {
                        "type": "boolean",
                        "description": "是否启用对话上下文记忆",
                        "default": True
                    },
                    "voice_mode": {
                        "type": "string", 
                        "enum": ["default", "ni"],
                        "description": "语音模式：default(默认音色) 或 ni(倪校音色)",
                        "default": "default"
                    }
                },
                "required": []
            },
        ),
        types.Tool(
            name="interrupt_ai_response",
            description="立即打断AI的回答",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            },
        ),
        types.Tool(
            name="start_recording",
            description="开始录音",
            inputSchema={
                "type": "object", 
                "properties": {},
                "required": []
            },
        ),
        types.Tool(
            name="stop_recording_and_send",
            description="停止录音并发送给AI",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            },
        ),
        types.Tool(
            name="get_conversation_status",
            description="获取当前对话状态",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent]:
    """处理工具调用"""
    global voice_controller
    
    try:
        if name == "start_manual_interrupt_voice_control":
            # 启动手动实时打断语音控制助手
            enable_context = arguments.get("enable_context", True) if arguments else True
            voice_mode = arguments.get("voice_mode", "default") if arguments else "default"
            
            if voice_controller is None:
                voice_controller = SimpleManualVoiceController()
            
            # 初始化连接
            connect_result = await voice_controller.connect()
            if not connect_result["success"]:
                return [types.TextContent(
                    type="text",
                    text=f"❌ 连接失败: {connect_result['error']}"
                )]
            
            # 初始化音频
            audio_result = voice_controller.setup_audio()
            if not audio_result["success"]:
                return [types.TextContent(
                    type="text",
                    text=f"❌ 音频初始化失败: {audio_result['error']}"
                )]
            
            status_text = f"""✅ 手动实时打断语音控制助手已启动！

📋 操作说明：
   • 使用 start_recording 开始录音
   • 使用 stop_recording_and_send 停止录音并发送  
   • 使用 interrupt_ai_response 立即打断AI回答
   • 使用 get_conversation_status 查看对话状态

🎯 特色功能：
   • ⚡ 立即打断AI回答，无延迟
   • 🧠 智能对话上下文记忆
   • 🔊 高质量实时语音交互
   • 📊 完整内存监控和管理

🔧 当前配置：
   • 语音模式: {voice_mode}
   • 上下文记忆: {'启用' if enable_context else '禁用'}
   • 会话ID: {voice_controller.session_id}
"""
            
            return [types.TextContent(type="text", text=status_text)]
            
        elif name == "interrupt_ai_response":
            # 立即打断AI回答
            if voice_controller is None:
                return [types.TextContent(
                    type="text", 
                    text="❌ 请先启动语音控制助手"
                )]
            
            if voice_controller.is_ai_speaking:
                await voice_controller._interrupt_ai()
                return [types.TextContent(
                    type="text",
                    text="⚡ AI已被立即打断"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text="ℹ️ AI当前未在说话，无需打断"
                )]
                
        elif name == "start_recording":
            # 开始录音
            if voice_controller is None:
                return [types.TextContent(
                    type="text",
                    text="❌ 请先启动语音控制助手"
                )]
            
            if voice_controller.is_recording:
                return [types.TextContent(
                    type="text",
                    text="⚠️ 已在录音中，请先停止当前录音"
                )]
            
            voice_controller._start_recording()
            return [types.TextContent(
                type="text", 
                text="🎤 录音已开始，请说话..."
            )]
            
        elif name == "stop_recording_and_send":
            # 停止录音并发送
            if voice_controller is None:
                return [types.TextContent(
                    type="text",
                    text="❌ 请先启动语音控制助手"
                )]
                
            if not voice_controller.is_recording:
                return [types.TextContent(
                    type="text",
                    text="⚠️ 当前未在录音，请先开始录音"
                )]
            
            voice_controller._stop_recording()
            return [types.TextContent(
                type="text",
                text="📤 录音已停止并发送，等待AI回答..."
            )]
            
        elif name == "get_conversation_status":
            # 获取对话状态
            if voice_controller is None:
                return [types.TextContent(
                    type="text",
                    text="❌ 语音控制助手未启动"
                )]
            
            # 获取内存状态
            memory_status = voice_controller._memory_monitor.check_memory_status()
            health_status = voice_controller._health_checker.check_system_health()
            
            # 获取对话缓存信息
            cache_info = ""
            if voice_controller.conversation_cache:
                cache_stats = voice_controller.conversation_cache.get_session_stats()
                cache_info = f"""
📚 对话缓存信息：
   • 总轮数: {cache_stats['total_turns']}
   • 会话时长: {cache_stats['duration_minutes']:.1f}分钟
   • 用户总字数: {cache_stats['user_total_chars']}
   • AI总字数: {cache_stats['ai_total_chars']}"""
            
            status_text = f"""📊 手动实时打断语音控制状态

🔗 连接状态: {'✅ 已连接' if voice_controller.is_connected else '❌ 未连接'}
🎤 录音状态: {'🟢 录音中' if voice_controller.is_recording else '⚪ 空闲'}  
🤖 AI状态: {'🟢 正在回答' if voice_controller.is_ai_speaking else '⚪ 空闲'}
🆔 会话ID: {voice_controller.session_id or '未分配'}

📊 系统状态：
   • 内存使用: {memory_status['current_mb']:.1f}MB (峰值: {memory_status['peak_mb']:.1f}MB)
   • 线程数量: {health_status['thread_count']}
   • 系统健康: {'✅ 正常' if health_status['healthy'] else '⚠️ ' + health_status['warning']}
{cache_info}

⚡ 功能状态：
   • 立即打断: ✅ 可用
   • 实时字幕: ✅ 启用
   • 内存监控: ✅ 运行中
"""
            
            return [types.TextContent(type="text", text=status_text)]
        
        else:
            return [types.TextContent(
                type="text",
                text=f"❌ 未知工具: {name}"
            )]
            
    except Exception as e:
        logger.error(f"工具调用错误: {e}")
        return [types.TextContent(
            type="text",
            text=f"❌ 执行失败: {str(e)}"
        )]

async def main():
    """主函数"""
    # 使用标准输入输出运行MCP服务器
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="手动实时打断_mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main()) 