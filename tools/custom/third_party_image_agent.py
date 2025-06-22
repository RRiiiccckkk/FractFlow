"""
Third Party Image Generation Agent - 使用第三方API的图像生成智能体

这个智能体使用第三方图像生成API服务，提供高质量的图像生成功能。
支持多种运行模式：
1. MCP Server模式（默认）：作为MCP工具提供给其他智能体
2. 交互模式：直接与用户交互
3. 单次查询模式：处理单个请求后退出

使用方式：
  python third_party_image_agent.py                           # MCP Server模式
  python third_party_image_agent.py --interactive             # 交互模式
  python third_party_image_agent.py --query "生成一张日落图片"  # 单次查询模式
"""

import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

from FractFlow.tool_template import ToolTemplate

class ThirdPartyImageAgent(ToolTemplate):
    """第三方图像生成智能体 - 使用imagen-4.0-ultra模型"""
    
    SYSTEM_PROMPT = """
你是一个专业的图像生成助手，使用高质量的imagen-4.0-ultra模型为用户创建精美的图像。

# 核心能力
- 高质量图像生成：使用imagen-4.0-ultra-generate模型
- 智能提示词优化：自动改进用户的描述
- 多样化风格支持：写实、艺术、卡通等各种风格
- 详细参数控制：尺寸、质量、风格等精细调整

# 工作流程
1. **理解需求**: 分析用户的图像生成需求
2. **优化提示词**: 将用户描述转化为高质量的英文提示词
3. **生成图像**: 调用imagen-4.0-ultra模型生成图像
4. **保存文件**: 将图像保存到指定路径
5. **反馈结果**: 提供生成结果和文件路径

# 提示词优化策略
- 添加质量描述词：high quality, detailed, professional
- 包含风格信息：photorealistic, artistic, cinematic
- 指定技术参数：4K, HDR, sharp focus
- 避免负面词汇：blur, low quality, distorted

# 输出格式要求
- operation_status: 操作状态描述
- optimized_prompt: 优化后的提示词
- image_path: 生成图像的保存路径
- generation_info: 生成参数信息
- success: 操作成功状态
- error_message: 错误信息（如有）

# 文件命名规范
- 默认保存路径：output/third_party_images/
- 文件名格式：YYYYMMDD_HHMMSS_description.png
- 自动创建目录结构
"""
    
    TOOLS = [
        ("tools/core/gpt_imagen/gpt_imagen_mcp.py", "image_generator")
    ]
    
    MCP_SERVER_NAME = "third_party_image_agent"
    
    TOOL_DESCRIPTION = """
第三方高质量图像生成智能体，使用imagen-4.0-ultra模型。

# 主要功能
- 高质量图像生成
- 智能提示词优化
- 多种风格支持
- 精确参数控制

# 输入格式
使用自然语言描述图像需求，例如：
- "生成一张日落风景图"
- "创建一个科幻机器人的插画"
- "制作一张美食摄影图片"
- "生成抽象艺术风格的图像"

可选参数：
- 保存路径：指定图像保存位置
- 风格要求：指定艺术风格
- 尺寸要求：指定图像尺寸

# 返回结构
- operation_status: 详细操作状态
- optimized_prompt: 优化的生成提示词
- image_path: 生成图像文件路径
- generation_info: 生成参数和模型信息
- success: 操作成功标识
- error_message: 错误信息（失败时）

# 使用示例
- "生成一张春天花园的风景图，保存为spring_garden.png"
- "创建一个未来城市的科幻插画，写实风格"
- "制作一张温馨的咖啡厅内景图"
"""
    
    @classmethod
    def create_config(cls):
        """为第三方图像生成智能体创建自定义配置"""
        from FractFlow.infra.config import ConfigManager
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # 优先使用环境变量，如果没有则使用硬编码值
        api_key = os.getenv('THIRD_PARTY_IMAGE_API_KEY', 'doQoKm7g3U4Bw')
        base_url = os.getenv('THIRD_PARTY_IMAGE_BASE_URL', 'https://ai.liaobots.work/v1')
        model = os.getenv('THIRD_PARTY_IMAGE_MODEL', 'imagen-4.0-ultra-generate-exp-05-20')
        
        return ConfigManager(
            # 主要智能体配置（用于对话和任务处理）
            provider='deepseek',
            deepseek_model='deepseek-chat',
            max_iterations=8,
            custom_system_prompt=cls.SYSTEM_PROMPT,
            
            # 图像生成API配置（用于实际的图像生成）
            openai_api_key=api_key,
            openai_base_url=base_url,
            openai_model=model,
            
            # 工具调用配置
            tool_calling_version='stable',
            tool_calling_temperature=0.1,
            tool_calling_max_retries=3,
            
            # 针对图像生成的特殊配置
            tool_calling_base_url=base_url,
            tool_calling_model=model
        )

if __name__ == "__main__":
    ThirdPartyImageAgent.main() 