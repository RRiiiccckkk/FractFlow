#!/usr/bin/env python3
"""
HKUST(GZ) AI Assistant 统一入口
支持学术问答模式和语音交互模式
"""

import asyncio
import os
import sys
import argparse
from typing import Literal, Optional, Dict, Any
from enum import Enum

# 确保项目根目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # 前端文件夹的上级目录就是项目根目录
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager

class AssistantMode(Enum):
    """助手模式枚举"""
    ACADEMIC_QA = "academic_qa"                    # 学术问答模式
    VOICE_INTERACTION = "voice_interaction"        # 语音交互模式（默认音色）
    NI_VOICE_INTERACTION = "ni_voice_interaction"  # 倪校语音交互模式

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
        self.voice_active = False  # 语音模式激活状态
        
        # 根据模式配置不同的系统提示
        self.system_prompts = {
            AssistantMode.ACADEMIC_QA: self._get_academic_qa_prompt(),
            AssistantMode.VOICE_INTERACTION: self._get_voice_interaction_prompt(),
            AssistantMode.NI_VOICE_INTERACTION: self._get_ni_voice_interaction_prompt()
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

🎤 **语音模式激活**：
当用户要求"切换到语音模式"、"启动语音交互"、"开始语音对话"时，
你需要提醒用户使用命令：
- 命令行启动: 添加 --voice-interactive 参数
- 交互中切换: 输入 'voice' 或 '语音模式'

请用专业但友好的方式回答学术相关问题，帮助用户在学习和研究中取得进步。"""

    def _get_voice_interaction_prompt(self) -> str:
        """获取语音交互模式的系统提示（默认音色）"""
        return """你是HKUST(GZ) AI Assistant，香港科技大学广州的智能语音助手，使用默认音色进行语音交互。

🎤 **默认语音对话功能**：
- 启动和停止实时语音对话助手（默认千问Omni音色）
- 支持语音识别和语音合成
- 支持实时打断功能
- 快速响应，适合日常对话

📋 **使用规则**：
1. 语音对话请求：使用 start_realtime_voice_interactive()
2. 停止请求：使用 stop_realtime_voice_interactive()

💡 **特点**：
- 使用千问Omni内置语音，稳定可靠
- 低延迟，适合快速对话
- 无需额外配置，开箱即用

如果用户需要倪校长声音，请建议他们选择倪校语音交互模式。"""

    def _get_ni_voice_interaction_prompt(self) -> str:
        """获取倪校语音交互模式的系统提示"""
        return """你是HKUST(GZ) AI Assistant，香港科技大学广州的智能语音助手，专为倪校长音色设计。

🎓 **倪校长专属语音功能**：
- 启动倪校长音色的实时语音对话
- 支持声音克隆技术
- 流式TTS播放，自然语音节奏
- 企业级语音交互体验

🎙️ **语音指令优先级**：
- "启动倪校语音助手" → 使用 start_ni_realtime_voice_interactive()
- "停止倪校语音助手" → 使用 stop_ni_realtime_voice_interactive()
- "启动语音助手" → 使用 start_ni_realtime_voice_interactive()（在倪校模式中优先倪校助手）
- "停止语音助手" → 使用 stop_ni_realtime_voice_interactive()
- 单次声音克隆：使用 clone_voice_with_ni(text="要说的内容")

💡 **特色功能**：
- 🎓 倪校长专属音色（声音克隆技术）
- 🚀 流式分句播放，自然语音节奏
- ⚡ 极速打断机制（0.01ms响应时间）
- 🎯 权威性学术对话体验

📋 **使用建议**：
- 适合正式场合和学术交流
- 提供权威性的语音回复
- 营造专业的交互氛围

请根据用户需求选择合适的工具来完成任务。在倪校语音交互模式中，默认使用倪校音色相关工具。"""

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
            
            # 根据模式注册相应的语音助手工具
            if self.mode == AssistantMode.VOICE_INTERACTION:
                # 默认语音交互模式：只注册默认语音工具
                self.agent.add_tool(
                    tool_path="tools/core/realtime_voice_interactive/realtime_voice_interactive_mcp.py",
                    tool_name="realtime_voice_interactive"
                )
            elif self.mode == AssistantMode.NI_VOICE_INTERACTION:
                # 倪校语音交互模式：同时注册两种工具
                self.agent.add_tool(
                    tool_path="tools/core/realtime_voice_interactive/realtime_voice_interactive_mcp.py",
                    tool_name="realtime_voice_interactive"
                )
                self.agent.add_tool(
                    tool_path="tools/core/realtime_voice_interactive/ni_realtime_voice_interactive_mcp.py",
                    tool_name="ni_realtime_voice_interactive"
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
    
    async def activate_voice_mode(self) -> Dict[str, Any]:
        """
        在当前会话中激活语音模式
        
        Returns:
            激活结果
        """
        try:
            if self.mode not in [AssistantMode.VOICE_INTERACTION, AssistantMode.NI_VOICE_INTERACTION]:
                # 切换到默认语音交互模式
                switch_result = await self.switch_mode(AssistantMode.VOICE_INTERACTION)
                if not switch_result["success"]:
                    return switch_result
            
            self.voice_active = True
            
            # 根据当前模式返回不同的指令
            if self.mode == AssistantMode.NI_VOICE_INTERACTION:
                return {
                    "success": True,
                    "message": "倪校语音模式已激活",
                    "voice_command": "启动倪校语音助手",  # 专门给倪校模式的启动指令
                    "instructions": [
                        "🎓 倪校长音色已启用",
                        "🚀 流式TTS播放已激活", 
                        "⚡ 极速打断机制已就绪",
                        "📋 输入 'voice off' 来关闭语音模式"
                    ]
                }
            else:
                return {
                    "success": True,
                    "message": "默认语音模式已激活", 
                    "voice_command": "启动语音助手",  # 默认模式的启动指令
                    "instructions": [
                        "🎤 千问Omni语音已启用",
                        "🔊 语音输出已启用", 
                        "⚡ 实时打断功能已就绪",
                        "📋 输入 'voice off' 来关闭语音模式"
                    ]
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "激活语音模式失败"
            }
    
    async def deactivate_voice_mode(self) -> Dict[str, Any]:
        """
        关闭语音模式，返回文本模式
        
        Returns:
            关闭结果
        """
        try:
            self.voice_active = False
            
            # 根据当前模式返回不同的停止指令
            if self.mode == AssistantMode.NI_VOICE_INTERACTION:
                stop_command = "停止倪校语音助手"
            else:
                stop_command = "停止语音助手"
            
            return {
                "success": True,
                "message": "已返回文本模式",
                "voice_stop_command": stop_command,
                "instructions": [
                    "💬 当前为文本交互模式",
                    "🎤 输入 'voice' 或 '语音模式' 来重新激活语音"
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "关闭语音模式失败"
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
        
        # 检查语音模式切换指令
        if query.lower() in ['voice', '语音模式', 'voice on', '启动语音', '开始语音']:
            result = await self.activate_voice_mode()
            if result["success"]:
                # 根据模式启动相应的语音助手
                voice_command = result.get("voice_command", "启动语音助手")
                voice_start = await self.agent.process_query(voice_command)
                return f"{result['message']}\n\n{voice_start}\n\n" + "\n".join(result["instructions"])
            else:
                return result["message"]
        
        elif query.lower() in ['voice off', '关闭语音', '文本模式', 'text mode']:
            result = await self.deactivate_voice_mode()
            if result["success"]:
                # 根据模式停止相应的语音助手
                stop_command = result.get("voice_stop_command", "停止语音助手")
                voice_stop = await self.agent.process_query(stop_command)
                return f"{result['message']}\n\n{voice_stop}\n\n" + "\n".join(result["instructions"])
            else:
                return result["message"]
        
        try:
            response = await self.agent.process_query(query)
            
            # 如果语音模式激活，添加语音状态提示
            if self.voice_active:
                response += "\n\n🎤 [语音模式已激活 | 输入 'voice off' 关闭]"
            
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
    """快速启动默认语音交互模式"""
    assistant = HKUSTAIAssistant(AssistantMode.VOICE_INTERACTION)
    await assistant.initialize()
    return assistant

async def quick_start_ni_voice_mode() -> HKUSTAIAssistant:
    """快速启动倪校语音交互模式"""
    assistant = HKUSTAIAssistant(AssistantMode.NI_VOICE_INTERACTION)
    await assistant.initialize()
    return assistant

# 统一的命令行入口
async def main():
    """主函数 - 支持命令行参数和交互式选择"""
    parser = argparse.ArgumentParser(description='HKUST(GZ) AI Assistant')
    parser.add_argument('--mode', '-m', choices=['academic', 'voice', 'ni-voice'], 
                       help='启动模式: academic (学术问答)、voice (默认语音交互) 或 ni-voice (倪校语音交互)')
    parser.add_argument('--voice-interactive', '-v', action='store_true',
                       help='直接启动默认语音交互模式')
    parser.add_argument('--ni-voice-interactive', '-n', action='store_true',
                       help='直接启动倪校语音交互模式')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='启动交互模式 (默认)')
    parser.add_argument('--query', '-q', type=str,
                       help='单次查询模式')
    
    args = parser.parse_args()
    
    print("🎓 欢迎使用 HKUST(GZ) AI Assistant")
    print("=" * 50)
    
    # 确定启动模式
    if args.ni_voice_interactive or args.mode == 'ni-voice':
        mode = AssistantMode.NI_VOICE_INTERACTION
        print("🎓 启动倪校语音交互模式")
    elif args.voice_interactive or args.mode == 'voice':
        mode = AssistantMode.VOICE_INTERACTION
        print("🎤 启动默认语音交互模式")
    elif args.mode == 'academic':
        mode = AssistantMode.ACADEMIC_QA
        print("📚 启动学术问答模式")
    elif args.query:
        # 单次查询默认用学术模式
        mode = AssistantMode.ACADEMIC_QA
        print("📝 单次查询模式")
    else:
        # 交互式选择模式
        print("请选择模式:")
        print("1. 📚 学术问答模式 - 专注学术咨询和研究支持")
        print("2. 🎤 默认语音交互模式 - 千问Omni语音，快速对话")
        print("3. 🎓 倪校语音交互模式 - 倪校长音色，权威学术交流")
        
        while True:
            try:
                choice = input("\n请输入模式编号 (1、2 或 3): ").strip()
                
                if choice == "1":
                    mode = AssistantMode.ACADEMIC_QA
                    print("✅ 学术问答模式已选择！")
                    break
                elif choice == "2":
                    mode = AssistantMode.VOICE_INTERACTION
                    print("✅ 默认语音交互模式已选择！")
                    break
                elif choice == "3":
                    mode = AssistantMode.NI_VOICE_INTERACTION
                    print("✅ 倪校语音交互模式已选择！")
                    break
                else:
                    print("❌ 请输入有效的模式编号 (1、2 或 3)")
                    continue
                    
            except KeyboardInterrupt:
                print("\n👋 再见！")
                return
    
    # 初始化助手
    assistant = HKUSTAIAssistant(mode)
    init_result = await assistant.initialize()
    
    if not init_result["success"]:
        print(f"❌ 初始化失败: {init_result['message']}")
        return
    
    print(f"✅ {init_result['message']}")
    
    # 处理单次查询
    if args.query:
        response = await assistant.process_query(args.query)
        print(f"\n🤖 助手: {response}")
        await assistant.shutdown()
        return
    
    # 语音交互模式特殊提示
    if args.voice_interactive or mode == AssistantMode.VOICE_INTERACTION:
        print("\n🎤 默认语音交互模式说明:")
        print("- 使用千问Omni内置语音")
        print("- 快速响应，适合日常对话")
        print("- 支持实时打断功能")
        print("- 说 'voice off' 或 '文本模式' 可切换到文本模式")
    elif args.ni_voice_interactive or mode == AssistantMode.NI_VOICE_INTERACTION:
        print("\n🎓 倪校语音交互模式说明:")
        print("- 使用倪校长专属音色（声音克隆技术）")
        print("- 流式TTS播放，自然语音节奏")
        print("- 极速打断机制（0.01ms响应时间）")
        print("- 适合正式场合和学术交流")
        print("- 说 'voice off' 或 '文本模式' 可切换到文本模式")
    
    # 交互循环
    print("\n💬 开始对话:")
    print("📋 特殊指令:")
    print("   - 'voice' 或 '语音模式': 激活语音交互")
    print("   - 'voice off' 或 '文本模式': 关闭语音交互") 
    print("   - 'quit', 'exit', '退出': 结束对话")
    print("-" * 50)
    
    # 如果是倪校语音模式，自动激活语音功能
    if mode == AssistantMode.NI_VOICE_INTERACTION:
        print("\n🎓 正在自动启动倪校语音交互功能...")
        voice_result = await assistant.activate_voice_mode()
        if voice_result["success"]:
            voice_command = voice_result.get("voice_command", "启动倪校语音助手")
            voice_response = await assistant.agent.process_query(voice_command)
            print(f"✅ {voice_result['message']}")
            print(f"🤖 助手: {voice_response}")
            for instruction in voice_result["instructions"]:
                print(f"   {instruction}")
        else:
            print(f"❌ 自动启动失败: {voice_result['message']}")
            print("💡 您可以手动输入 'voice' 来启动语音功能")
    
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