#!/usr/bin/env python3
"""
HKUST(GZ) AI Assistant 统一入口
支持学术问答模式和语音交互模式
"""

import asyncio
import os
import sys
from typing import Literal, Optional, Dict, Any
from enum import Enum

# 确保项目路径在Python路径中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager

class AssistantMode(Enum):
    """助手模式枚举"""
    ACADEMIC_QA = "academic_qa"      # 学术问答模式
    VOICE_INTERACTION = "voice_interaction"  # 语音交互模式

class HKUSTAIAssistant:
    """HKUST(GZ) AI Assistant 主类"""
    
    def __init__(self, mode: AssistantMode = AssistantMode.ACADEMIC_QA):
        """
        初始化AI助手
        
        Args:
            mode: 助手模式，默认为学术问答模式
        """
        self.mode = mode
        self.agent: Optional[Agent] = None
        self.is_initialized = False
        
        # 根据模式配置不同的系统提示
        self.system_prompts = {
            AssistantMode.ACADEMIC_QA: self._get_academic_qa_prompt(),
            AssistantMode.VOICE_INTERACTION: self._get_voice_interaction_prompt()
        }
    
    def _get_academic_qa_prompt(self) -> str:
        """获取学术问答模式的系统提示"""
        return """你是HKUST(GZ) AI Assistant，香港科技大学广州的学术智能助手。

🎓 **核心功能**：
- 回答学术问题和研究咨询
- 提供课程信息和学习指导
- 协助论文写作和研究方法
- 解答科研相关问题

📚 **专业领域**：
- 计算机科学与工程
- 人工智能与机器学习
- 数据科学与分析
- 创新创业
- 跨学科研究

💡 **交互特点**：
- 学术严谨但易于理解
- 提供具体的学习建议
- 引用可靠的学术资源
- 鼓励创新思维

请用专业但友好的方式回答学术相关问题，帮助用户在学习和研究中取得进步。"""

    def _get_voice_interaction_prompt(self) -> str:
        """获取语音交互模式的系统提示"""
        return """你是HKUST(GZ) AI Assistant，香港科技大学广州的智能语音助手，具备语音合成和对话功能。

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

    async def initialize(self) -> Dict[str, Any]:
        """
        初始化助手系统
        
        Returns:
            初始化结果
        """
        try:
            # 创建配置
            config = ConfigManager(
                provider='qwen',
                custom_system_prompt=self.system_prompts[self.mode]
            )
            
            # 创建Agent
            self.agent = Agent(config=config)
            
            # 如果是语音交互模式，注册语音助手工具
            if self.mode == AssistantMode.VOICE_INTERACTION:
                self.agent.add_tool(
                    tool_path="tools/core/guang_voice_assistant/guang_voice_assistant_mcp.py",
                    tool_name="guang_voice_assistant"
                )
            
            # 启动Agent
            await self.agent.initialize()
            self.is_initialized = True
            
            return {
                "success": True,
                "mode": self.mode.value,
                "message": f"HKUST(GZ) AI Assistant 已启动 - {self.mode.value} 模式"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "助手初始化失败"
            }
    
    async def process_query(self, query: str) -> str:
        """
        处理用户查询
        
        Args:
            query: 用户查询内容
            
        Returns:
            助手回复
        """
        if not self.is_initialized or not self.agent:
            return "❌ 助手尚未初始化，请先调用 initialize() 方法"
        
        try:
            response = await self.agent.process_query(query)
            return response
        except Exception as e:
            return f"❌ 处理查询时出现错误: {str(e)}"
    
    async def switch_mode(self, new_mode: AssistantMode) -> Dict[str, Any]:
        """
        切换助手模式
        
        Args:
            new_mode: 新的模式
            
        Returns:
            切换结果
        """
        if self.mode == new_mode:
            return {
                "success": True,
                "message": f"已经处于 {new_mode.value} 模式"
            }
        
        # 关闭当前Agent
        if self.is_initialized and self.agent:
            await self.agent.shutdown()
        
        # 切换到新模式
        self.mode = new_mode
        self.is_initialized = False
        
        # 重新初始化
        result = await self.initialize()
        
        if result["success"]:
            result["message"] = f"已切换到 {new_mode.value} 模式"
        
        return result
    
    async def shutdown(self) -> Dict[str, Any]:
        """
        关闭助手系统
        
        Returns:
            关闭结果
        """
        try:
            if self.is_initialized and self.agent:
                await self.agent.shutdown()
                self.is_initialized = False
                
            return {
                "success": True,
                "message": "助手系统已安全关闭"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "关闭系统时出现错误"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取助手状态
        
        Returns:
            当前状态信息
        """
        return {
            "mode": self.mode.value,
            "initialized": self.is_initialized,
            "available_modes": [mode.value for mode in AssistantMode]
        }

# 便捷的快速启动函数
async def quick_start_academic_mode() -> HKUSTAIAssistant:
    """快速启动学术问答模式"""
    assistant = HKUSTAIAssistant(AssistantMode.ACADEMIC_QA)
    await assistant.initialize()
    return assistant

async def quick_start_voice_mode() -> HKUSTAIAssistant:
    """快速启动语音交互模式"""
    assistant = HKUSTAIAssistant(AssistantMode.VOICE_INTERACTION)
    await assistant.initialize()
    return assistant

# 统一的命令行入口
async def main():
    """主函数 - 提供交互式选择"""
    print("🎓 欢迎使用 HKUST(GZ) AI Assistant")
    print("=" * 50)
    print("请选择模式:")
    print("1. 📚 学术问答模式 - 专注学术咨询和研究支持")
    print("2. 🎤 语音交互模式 - 支持语音对话和倪校语音包")
    
    while True:
        try:
            choice = input("\n请输入模式编号 (1 或 2): ").strip()
            
            if choice == "1":
                assistant = await quick_start_academic_mode()
                print("✅ 学术问答模式已启动！")
                break
            elif choice == "2":
                assistant = await quick_start_voice_mode()
                print("✅ 语音交互模式已启动！")
                break
            else:
                print("❌ 请输入有效的模式编号 (1 或 2)")
                continue
                
        except KeyboardInterrupt:
            print("\n👋 再见！")
            return
    
    # 交互循环
    print("\n💬 开始对话 (输入 'quit' 退出):")
    print("-" * 30)
    
    try:
        while True:
            user_input = input("\n👤 您: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                break
            
            if not user_input:
                continue
            
            response = await assistant.process_query(user_input)
            print(f"🤖 助手: {response}")
            
    except KeyboardInterrupt:
        print("\n\n🛑 用户中断")
    finally:
        print("\n🧹 正在关闭系统...")
        await assistant.shutdown()
        print("✅ 系统已安全关闭")

if __name__ == "__main__":
    # 检查API密钥
    if not os.getenv("QWEN_API_KEY") and not os.getenv("DASHSCOPE_API_KEY"):
        print("🚨 错误: 未找到Qwen/DashScope API密钥")
        print("请设置 QWEN_API_KEY 或 DASHSCOPE_API_KEY 环境变量")
        sys.exit(1)
    
    asyncio.run(main()) 