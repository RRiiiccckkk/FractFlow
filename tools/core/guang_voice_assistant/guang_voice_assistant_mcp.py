"""
guang_voice_assistant_mcp.py
Author: FractFlow Team
Brief: MCP entry for Guang Voice Assistant (HKUST-GZ)
"""

import asyncio
import os
import sys

# HACK: This is a workaround to handle the case where the script is run directly
# by the subprocess in the orchestrator. In that context, the relative imports
# might fail. This ensures the project root is on the Python path.
if __name__ == "__main__" and __package__ is None:
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate up to the project root (FractFlow/)
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
    # Add the project root to the system path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from mcp.server.fastmcp import FastMCP

# 导入 Assistant 类和配置函数
from tools.core.guang_voice_assistant.simple_voice_assistant import SimpleVoiceAssistant, setup_api_keys

mcp = FastMCP("guang_voice_assistant")

# 全局变量，用于保存正在运行的助手实例
_running_assistant: SimpleVoiceAssistant | None = None

# ========== MCP 工具 ==========

@mcp.tool()
async def start_simple_voice_assistant() -> str:
    """
    Starts the real-time voice assistant.
    This tool initializes the assistant, connects to the voice API,
    and starts recording in background threads. It returns immediately.
    """
    global _running_assistant
    if _running_assistant and _running_assistant.is_recording:
        return "⚠️ Assistant is already running."

    try:
        setup_api_keys()
        api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
        if not api_key:
            return "❌ QWEN_API_KEY or DASHSCOPE_API_KEY not found."

        # 创建实例并连接
        _running_assistant = SimpleVoiceAssistant(api_key=api_key)
        connection_result = await _running_assistant.connect()
        if not connection_result.get("success"):
            _running_assistant = None
            return f"❌ Connection failed: {connection_result.get('error', 'Unknown error')}"

        # 启动录音和处理线程
        recording_result = _running_assistant.start_recording()
        if not recording_result.get("success"):
            await _running_assistant.disconnect()
            _running_assistant = None
            return f"❌ Failed to start recording: {recording_result.get('error', 'Unknown error')}"

        return "✅ Voice assistant started. You can now speak. Use 'stop_simple_voice_assistant' to stop."
    except Exception as e:
        if _running_assistant:
            await _running_assistant.disconnect()
        _running_assistant = None
        return f"❌ Failed to start assistant due to an error: {e}"

@mcp.tool()
async def stop_simple_voice_assistant() -> str:
    """
    Stops the currently running real-time voice assistant.
    This disconnects from the API and terminates all background threads.
    """
    global _running_assistant
    if not _running_assistant:
        return "⚠️ Assistant is not running."

    try:
        await _running_assistant.disconnect()
        return "✅ Voice assistant stopped successfully."
    except Exception as e:
        return f"❌ Failed to stop assistant due to an error: {e}"
    finally:
        _running_assistant = None

@mcp.tool()
def clone_voice_with_ni(text: str = "大家好呀，我是香港科技大学广州校长倪哥。欢迎大家来到香港科技大学广州校园，祝大家生活快乐，学业有成。") -> str:
    """Clone voice using Ni's voice clone client (TTS)"""
    try:
        # 首先检查网络连接
        import requests
        test_url = "http://10.120.17.57:9880/tts"
        
        # 测试连接（使用正确的参数格式，注意所有参数都是字符串）
        test_params = {
            "text": "测试",
            "text_lang": "zh", 
            "ref_audio_path": "ref_audio/ni_zh_01.wav",
            "prompt_lang": "zh",
            "text_split_method": "cut5",
            "batch_size": "1",
            "media_type": "wav",
            "streaming_mode": "true"
        }
        try:
            response = requests.post(test_url, json=test_params, timeout=5, stream=True)
            if response.status_code != 200:
                return f"❌ TTS服务器响应错误 {response.status_code}: 可能是参数配置问题或服务器故障"
        except requests.exceptions.ConnectTimeout:
            return "❌ 连接TTS服务超时，请检查网络或服务器状态"
        except requests.exceptions.ConnectionError:
            return "❌ 无法连接到TTS服务器(10.120.17.57:9880)，请确认服务器是否在线"
        except Exception as e:
            return f"❌ 网络检查失败: {str(e)}"
        
        # 网络正常，执行声色克隆
        from .ni_voice_clone_client.main import play_ni_voice
        play_ni_voice(text)
        return f"✅ 倪校声色克隆成功播放: {text[:30]}..."
    except ImportError as e:
        return f"❌ 导入声色克隆模块失败: {str(e)}"
    except Exception as e:
        return f"❌ 声色克隆执行失败: {str(e)}"

if __name__ == "__main__":
    mcp.run() 