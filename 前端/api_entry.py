#!/usr/bin/env python3
"""
HKUST(GZ) AI Assistant API入口
为前端提供简洁的调用接口
"""

import asyncio
import os
import sys
from typing import Dict, Any, Optional

# 确保项目根目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # 前端文件夹的上级目录就是项目根目录
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from hkust_ai_assistant_entry import HKUSTAIAssistant, AssistantMode

class HKUSTAssistantAPI:
    """HKUST AI Assistant API接口"""
    
    def __init__(self):
        self.assistant: Optional[HKUSTAIAssistant] = None
    
    async def start_academic_mode(self) -> Dict[str, Any]:
        """
        启动学术问答模式
        
        Returns:
            启动结果
        """
        try:
            if self.assistant:
                await self.assistant.shutdown()
            
            self.assistant = HKUSTAIAssistant(AssistantMode.ACADEMIC_QA)
            result = await self.assistant.initialize()
            
            return {
                "success": True,
                "mode": "academic_qa",
                "message": "学术问答模式已启动",
                "description": "专注于学术咨询、研究支持和课程指导"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "启动学术模式失败"
            }
    
    async def start_voice_mode(self) -> Dict[str, Any]:
        """
        启动语音交互模式
        
        Returns:
            启动结果
        """
        try:
            if self.assistant:
                await self.assistant.shutdown()
            
            self.assistant = HKUSTAIAssistant(AssistantMode.VOICE_INTERACTION)
            result = await self.assistant.initialize()
            
            return {
                "success": True,
                "mode": "voice_interaction",
                "message": "语音交互模式已启动",
                "description": "支持语音对话、倪校长语音包和复合指令",
                "features": [
                    "实时语音对话",
                    "倪校长声音克隆",
                    "语音识别和合成",
                    "复合指令处理"
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "启动语音模式失败"
            }
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """
        处理用户消息
        
        Args:
            message: 用户输入的消息
            
        Returns:
            处理结果
        """
        if not self.assistant or not self.assistant.is_initialized:
            return {
                "success": False,
                "error": "Assistant not initialized",
                "message": "助手尚未初始化，请先选择模式"
            }
        
        try:
            response = await self.assistant.process_query(message)
            
            return {
                "success": True,
                "response": response,
                "mode": self.assistant.mode.value
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "处理消息时出现错误"
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """
        获取当前状态
        
        Returns:
            状态信息
        """
        if not self.assistant:
            return {
                "initialized": False,
                "mode": None,
                "available_modes": ["academic_qa", "voice_interaction"]
            }
        
        status = self.assistant.get_status()
        return {
            "initialized": status["initialized"],
            "mode": status["mode"],
            "available_modes": status["available_modes"],
            "ready": status["initialized"]
        }
    
    async def shutdown(self) -> Dict[str, Any]:
        """
        关闭助手
        
        Returns:
            关闭结果
        """
        try:
            if self.assistant:
                await self.assistant.shutdown()
                self.assistant = None
            
            return {
                "success": True,
                "message": "助手已安全关闭"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "关闭助手时出现错误"
            }

# 全局API实例
_api_instance: Optional[HKUSTAssistantAPI] = None

def get_api() -> HKUSTAssistantAPI:
    """获取API实例（单例模式）"""
    global _api_instance
    if _api_instance is None:
        _api_instance = HKUSTAssistantAPI()
    return _api_instance

# 便捷的直接调用函数
async def start_academic_assistant() -> Dict[str, Any]:
    """直接启动学术助手"""
    api = get_api()
    return await api.start_academic_mode()

async def start_voice_assistant() -> Dict[str, Any]:
    """直接启动语音助手"""
    api = get_api()
    return await api.start_voice_mode()

async def send_message(message: str) -> Dict[str, Any]:
    """发送消息给助手"""
    api = get_api()
    return await api.process_message(message)

async def get_assistant_status() -> Dict[str, Any]:
    """获取助手状态"""
    api = get_api()
    return await api.get_status()

async def shutdown_assistant() -> Dict[str, Any]:
    """关闭助手"""
    api = get_api()
    return await api.shutdown()

# 测试复合指令的专用函数
async def test_composite_commands():
    """测试复合指令功能"""
    print("🧪 测试复合指令功能")
    print("=" * 40)
    
    # 启动语音模式
    result = await start_voice_assistant()
    if not result["success"]:
        print(f"❌ 启动失败: {result['message']}")
        return
    
    print("✅ 语音交互模式已启动")
    
    # 测试复合指令
    test_commands = [
        "请用倪校长的声音和我进行语音交互",
        "启动倪校语音模式",
        "开始语音交互，用倪校长声音回复",
        "让倪校长介绍香港科技大学广州"
    ]
    
    for i, command in enumerate(test_commands, 1):
        print(f"\n🧪 测试{i}: {command}")
        response = await send_message(command)
        
        if response["success"]:
            print(f"✅ 响应: {response['response'][:100]}{'...' if len(response['response']) > 100 else ''}")
        else:
            print(f"❌ 错误: {response['message']}")
    
    # 关闭助手
    await shutdown_assistant()
    print("\n✅ 测试完成")

if __name__ == "__main__":
    # 检查API密钥
    if not os.getenv("QWEN_API_KEY") and not os.getenv("DASHSCOPE_API_KEY"):
        print("🚨 错误: 未找到API密钥")
        print("请设置 QWEN_API_KEY 或 DASHSCOPE_API_KEY 环境变量")
        sys.exit(1)
    
    # 运行复合指令测试
    asyncio.run(test_composite_commands()) 