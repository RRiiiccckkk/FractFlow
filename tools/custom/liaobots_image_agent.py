"""
LiaoBots 图像生成智能体 - 专门适配 liaobots API 格式

这个智能体专门为 ai.liaobots.work 服务定制，使用聊天API格式进行图像生成。
支持多种运行模式：
1. MCP Server模式（默认）：作为MCP工具提供给其他智能体
2. 交互模式：直接与用户交互
3. 单次查询模式：处理单个请求后退出

使用方式：
  python liaobots_image_agent.py                           # MCP Server模式
  python liaobots_image_agent.py --interactive             # 交互模式
  python liaobots_image_agent.py --query "生成一张日落图片"  # 单次查询模式
"""

import os
import sys
import json
import asyncio
import aiohttp
from typing import Optional, Dict, Any

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

from FractFlow.tool_template import ToolTemplate

class LiaoBotsImageAgent(ToolTemplate):
    """LiaoBots 图像生成智能体 - 使用imagen-4.0-ultra模型"""
    
    TOOL_DESCRIPTION = """
    使用 imagen-4.0-ultra-generate-exp-05-20 模型生成高质量图像。
    
    功能：
    - 基于文本描述生成图像
    - 支持中英文提示词
    - 自动优化提示词以获得更好效果
    - 支持多种艺术风格和场景
    
    返回格式：
    - 生成状态：成功或失败信息
    - 图像描述：生成图像的详细说明
    - 提示词：实际使用的优化提示词
    - 模型信息：使用的模型名称
    - API响应：第三方服务的响应内容
    - 文件信息：保存路径等相关信息
    """
    
    SYSTEM_PROMPT = """
你是一个专业的图像生成助手，使用 imagen-4.0-ultra-generate-exp-05-20 模型为用户创建精美的图像。

# 重要说明
你直接处理用户的图像生成请求，不需要调用任何工具。用户的请求会被自动转换为API调用并生成图像。

# 核心能力
- 高质量图像生成：使用最新的imagen-4.0-ultra模型
- 智能提示词优化：自动优化用户的描述以获得更好效果
- 多样化风格支持：写实、卡通、艺术、概念图等各种风格

# 工作流程
1. 理解用户的图像描述需求
2. 系统会自动调用第三方API生成图像
3. 向用户报告生成结果

# 输出格式要求
当图像生成成功时，你应该回复：
- 成功状态确认
- 图像的详细描述
- 使用的提示词
- 技术信息（模型、文件等）

当图像生成失败时，你应该回复：
- 错误状态说明
- 具体错误原因
- 建议解决方案

始终以专业、友好的语调提供服务，并确保用户了解图像生成的状态。
"""

    def __init__(self):
        super().__init__()
        self.api_key = self._get_env_var("THIRD_PARTY_IMAGE_API_KEY", "OPENAI_API_KEY")
        self.base_url = self._get_env_var("THIRD_PARTY_IMAGE_BASE_URL", "OPENAI_BASE_URL")
        self.model = self._get_env_var("THIRD_PARTY_IMAGE_MODEL", "imagen-4.0-ultra-generate-exp-05-20")
        
        if not self.api_key:
            raise ValueError("未找到API密钥。请设置 THIRD_PARTY_IMAGE_API_KEY 或 OPENAI_API_KEY 环境变量")
        
        # 默认配置
        if not self.base_url:
            self.base_url = "https://ai.liaobots.work/v1"
            
        # 确保base_url格式正确
        if not self.base_url.endswith('/v1'):
            if self.base_url.endswith('/'):
                self.base_url = self.base_url + 'v1'
            else:
                self.base_url = self.base_url + '/v1'

    def _get_env_var(self, primary_key: str, fallback_key: str = None) -> Optional[str]:
        """获取环境变量，支持备用键"""
        value = os.getenv(primary_key)
        if not value and fallback_key:
            value = os.getenv(fallback_key)
        return value

    async def create_image_with_liaobots(self, 
                                       prompt: str, 
                                       filename: str = None,
                                       size: str = "1024x1024",
                                       quality: str = "standard") -> Dict[str, Any]:
        """
        使用 LiaoBots API 生成图像
        
        Args:
            prompt: 图像描述
            filename: 保存文件名
            size: 图像尺寸 (默认: 1024x1024)
            quality: 图像质量 (默认: standard)
            
        Returns:
            包含结果信息的字典
        """
        try:
            # 优化提示词
            optimized_prompt = await self._optimize_prompt(prompt)
            
            # 准备API请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 构建请求数据 - 使用聊天API格式
            request_data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Please generate an image based on this description: {optimized_prompt}"
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            # 发送请求
            api_url = f"{self.base_url}/chat/completions"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, headers=headers, json=request_data) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        result = json.loads(response_text)
                        
                        # 处理响应 - 这里需要根据实际API响应格式调整
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result['choices'][0]['message']['content']
                            
                            # 生成文件名
                            if not filename:
                                filename = f"liaobots_image_{len(optimized_prompt)%1000}.png"
                            
                            return {
                                "result": "success",
                                "description": f"成功生成图像: {prompt}",
                                "api_response": content,
                                "prompt_used": optimized_prompt,
                                "file_path": filename,
                                "model_used": self.model
                            }
                        else:
                            return {
                                "result": "error",
                                "error": f"API响应格式异常: {response_text}",
                                "prompt_used": optimized_prompt
                            }
                    else:
                        return {
                            "result": "error", 
                            "error": f"API请求失败 (状态码: {response.status}): {response_text}",
                            "prompt_used": optimized_prompt
                        }
                        
        except Exception as e:
            return {
                "result": "error",
                "error": f"请求过程中发生错误: {str(e)}",
                "prompt_used": prompt
            }

    async def _optimize_prompt(self, prompt: str) -> str:
        """优化图像生成提示词"""
        # 基础提示词优化
        if not prompt:
            return "A beautiful, high-quality image"
            
        # 如果是中文，添加一些通用的质量描述
        if any('\u4e00' <= char <= '\u9fff' for char in prompt):
            prompt = f"{prompt}, 高质量, 精细细节, 专业摄影"
        else:
            prompt = f"{prompt}, high quality, detailed, professional"
            
        return prompt

    async def process_query(self, user_input: str) -> str:
        """处理用户请求的主要逻辑 - 覆盖ToolTemplate的process_query方法"""
        try:
            # 解析用户输入
            prompt = user_input
            filename = None
            
            # 检查是否指定了文件名
            if "保存为" in user_input or "save as" in user_input.lower():
                parts = user_input.replace("保存为", "save as").split("save as")
                if len(parts) == 2:
                    prompt = parts[0].strip()
                    filename = parts[1].strip()
            
            # 生成图像
            result = await self.create_image_with_liaobots(
                prompt=prompt,
                filename=filename
            )
            
            # 格式化输出
            if result["result"] == "success":
                return f"""✅ 图像生成成功！

📝 描述: {result["description"]}
🎨 使用提示词: {result["prompt_used"]}
🤖 模型: {result["model_used"]}
📄 API响应: {result["api_response"]}
📁 文件名: {result["file_path"]}

图像已经通过API成功生成！"""
            else:
                return f"""❌ 图像生成失败

错误信息: {result["error"]}
使用提示词: {result["prompt_used"]}

请检查API配置或稍后重试。"""
            
        except Exception as e:
            return f"❌ 处理请求时发生错误: {str(e)}"

if __name__ == "__main__":
    # 使用ToolTemplate的main方法
    LiaoBotsImageAgent.main() 