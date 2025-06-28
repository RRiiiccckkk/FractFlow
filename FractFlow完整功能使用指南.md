# FractFlow 完整功能使用指南

欢迎使用FractFlow！这是一个分形智能架构，将智能分解为可嵌套的Agent-Tool单元，构建动态演进的分布式认知系统。

## 🚀 快速开始

### 1. 环境安装

```bash
# 安装uv包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆项目
git clone https://github.com/RRiiiccckkk/FractFlow.git
cd FractFlow

# 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
uv pip install -r requirements.txt
```

### 2. 环境配置

创建 `.env` 文件配置API密钥：

```bash
# 创建配置文件
cp config.env.example .env
```

编辑 `.env` 文件，至少配置一个AI模型的API密钥：

```env
# DeepSeek (推荐，性价比高)
DEEPSEEK_API_KEY=your_deepseek_api_key

# OpenAI (需要图像生成功能时必须)
OPENAI_API_KEY=your_openai_api_key
COMPLETION_API_KEY=your_openai_api_key

# 千问 (阿里云)
QWEN_API_KEY=your_qwen_api_key
DASHSCOPE_API_KEY=your_qwen_api_key
```

### 3. 验证安装

```bash
# 测试基础功能
python tools/core/weather/weather_agent.py --query "New York weather today"
```

## 🎯 核心功能概览

FractFlow提供三类主要功能：

### 📚 核心工具 (Core Tools)
- **文件操作**：智能读写、编辑、管理文件
- **图像生成**：AI图像创作和编辑
- **网络搜索**：智能网页搜索和信息提取
- **天气查询**：实时天气信息
- **视觉问答**：图像理解和分析
- **语音交互**：实时语音对话和声音克隆
- **视频处理**：视频分析和处理
- **3D建模**：Blender集成

### 🔄 复合工具 (Composite Tools)  
- **图文文章生成器**：自动生成带插图的文章
- **智能网页保存**：搜索+整理+保存一体化
- **深度视觉推理**：复杂图像分析
- **长视频生成**：视频内容创作

### 🎓 HKUST AI Assistant
- **学术问答模式**：专业的学术咨询和研究支持
- **语音交互模式**：语音对话+倪校长声音克隆

## 📋 详细功能使用

### 🔧 核心工具使用

#### 1. 文件操作 (File I/O)

```bash
# 基础文件操作
python tools/core/file_io/file_io_agent.py --query "读取README.md文件"
python tools/core/file_io/file_io_agent.py --query "在output.txt中写入'Hello World'"

# 高级操作
python tools/core/file_io/file_io_agent.py --query "读取data.csv文件的第100-200行"
python tools/core/file_io/file_io_agent.py --query "删除temp.log中包含'ERROR'的所有行"

# 交互模式
python tools/core/file_io/file_io_agent.py --interactive
```

#### 2. AI图像生成 (GPT Imagen)

```bash
# 图像生成
python tools/core/gpt_imagen/gpt_imagen_agent.py --query "生成图片：save_path='spring_garden.png' prompt='美丽的春天花园'"

# 复杂场景
python tools/core/gpt_imagen/gpt_imagen_agent.py --query "生成图片：save_path='robot.png' prompt='未来科技感机器人，高质量插画风格'"

# 交互模式进行多轮创作
python tools/core/gpt_imagen/gpt_imagen_agent.py --interactive
```

#### 3. 网络搜索 (Web Search)

```bash
# 基础搜索
python tools/core/websearch/websearch_agent.py --query "最新的AI技术发展"
python tools/core/websearch/websearch_agent.py --query "Python性能优化方法"

# 专业搜索
python tools/core/websearch/websearch_agent.py --query "搜索关于深度学习在医疗领域的应用案例"
```

#### 4. 天气查询 (Weather)

```bash
# 美国城市天气查询
python tools/core/weather/weather_agent.py --query "纽约今天天气"
python tools/core/weather/weather_agent.py --query "旧金山未来5天天气预报"
```

#### 5. 视觉问答 (Visual Q&A)

```bash
# 图像理解
python tools/core/visual_question_answer/vqa_agent.py --query "图片：/path/to/image.jpg 这张图片里有什么物品？"

# 详细分析
python tools/core/visual_question_answer/vqa_agent.py --query "图片：/path/to/photo.png 详细描述这个场景"
```

#### 6. 语音交互功能

```bash
# 千问实时语音交互
python tools/core/qwen_realtime_voice/qwen_realtime_voice_agent.py --interactive

# HKUST语音助手（支持倪校长声音克隆）
python 前端/hkust_ai_assistant_entry.py
```

### 🔄 复合工具使用

#### 1. 图文文章生成器 (Visual Article)

这是FractFlow分形智能的典型代表，自动协调多个工具生成完整的图文内容：

```bash
# 生成完整图文文章
python tools/composite/visual_article_agent.py --query "写一篇关于AI发展的文章，要配插图"

# 创意写作
python tools/composite/visual_article_agent.py --query "设定：一个视觉识别AI统治社会的世界。要求：以第一人称写一段剧情片段。情绪基调：冷峻、怀疑、诗性。"

# 技术文档
python tools/composite/visual_article_agent.py --query "写一篇Python入门教程，包含代码示例和概念图解"
```

**输出示例**：
```
output/visual_article_generator/ai_development/
├── article.md           # 完整文章
└── images/             # 配套图片
    ├── section1-fig1.png
    ├── section2-fig1.png
    └── section3-fig1.png
```

#### 2. 智能网页保存 (Web Save)

```bash
# 研究报告生成
python tools/composite/web_save_agent.py --query "搜索最新的Python教程并保存为综合指南文件"

# 市场调研
python tools/composite/web_save_agent.py --query "搜集关于机器学习的信息并创建整理报告"
```

#### 3. 深度视觉推理

```bash
# 复杂图像分析
python tools/composite/deep_visual_reasoning_agent.py --query "分析这张图片的构图、色彩和情感表达：/path/to/complex_image.jpg"
```

#### 4. 长视频生成

```bash
# 视频内容创作
python tools/composite/long_video_generator.py --query "创建一个关于AI发展历程的5分钟解说视频"
```

### 🎓 HKUST AI Assistant 使用

#### 1. 快速启动（支持多种方式）

```bash
# 方式1: 交互式模式选择
python 前端/hkust_ai_assistant_entry.py

# 方式2: 命令行直接指定模式
python 前端/hkust_ai_assistant_entry.py --mode academic    # 学术模式
python 前端/hkust_ai_assistant_entry.py --mode voice      # 语音模式

# 方式3: 直接语音交互模式  
python 前端/hkust_ai_assistant_entry.py --voice-interactive

# 方式4: 单次查询
python 前端/hkust_ai_assistant_entry.py --query "什么是深度学习？"
```

#### 2. 学术问答模式

专业的学术咨询和研究支持：

```bash
# 启动学术模式
python 前端/hkust_ai_assistant_entry.py --mode academic

# 在对话中可以：
👤 您: 如何写好一篇学术论文？
👤 您: 深度学习有哪些主要应用领域？
👤 您: voice  # 切换到语音模式
🤖 助手: 语音模式已激活...
👤 您: voice off  # 返回文本模式
```

#### 3. 语音交互模式

支持语音对话和倪校长声音克隆：

```bash
# 启动语音模式
python 前端/hkust_ai_assistant_entry.py --voice-interactive

# 支持的指令：
👤 您: 启动语音助手
👤 您: 请用倪校长的声音说欢迎词
👤 您: 请用倪校长的声音和我进行语音交互
👤 您: 开始倪校语音模式
👤 您: 停止语音助手
```

**⚠️ 注意**：倪校长语音包目前无法正常运行（TTS服务器连接问题），系统会自动降级到文字回复。

## 🔧 三种运行模式

每个FractFlow工具都支持四种运行模式：

### 1. MCP服务器模式（默认）
```bash
# 作为MCP服务器运行，供其他程序调用
python tools/core/file_io/file_io_agent.py
```

### 2. 交互模式（文本）
```bash
# 进入交互式对话
python tools/core/file_io/file_io_agent.py --interactive
# 然后可以连续输入查询
```

### 3. 语音交互模式（新增）🎤
```bash
# 启动语音交互模式，支持语音输入输出
python tools/core/file_io/file_io_agent.py --voice-interactive

# 或使用简短参数
python tools/core/file_io/file_io_agent.py -v
```

### 4. 音频交互模式
```bash
# 基础音频交互（语音识别+TTS）
python tools/core/file_io/file_io_agent.py --audio-interactive
```

### 5. 单次查询模式
```bash
# 执行单次查询后退出
python tools/core/file_io/file_io_agent.py --query "读取README.md文件"
```

## ✨ 新增功能：统一语音交互

### 🎤 --voice-interactive 模式

所有FractFlow工具现在都支持统一的语音交互模式：

```bash
# 语音交互模式启动任何工具
python tools/core/websearch/websearch_agent.py --voice-interactive
python tools/core/gpt_imagen/gpt_imagen_agent.py --voice-interactive
python tools/composite/visual_article_agent.py --voice-interactive

# HKUST AI Assistant 语音模式
python 前端/hkust_ai_assistant_entry.py --voice-interactive
```

### 🔄 文本到语音模式切换

在任何文本交互中，都可以动态切换到语音模式：

```bash
# 启动文本交互
python 前端/hkust_ai_assistant_entry.py --interactive

# 在对话中输入切换指令：
👤 您: voice
👤 您: 语音模式
👤 您: 启动语音

# 返回文本模式：
👤 您: voice off
👤 您: 文本模式
```

### 🎯 广广语音助手专用工具

```bash
# 专门的语音助手工具
python tools/core/guang_voice_assistant/guang_voice_assistant_agent.py --voice-interactive

# 支持的语音指令：
# - "启动语音助手" 
# - "请用倪校长的声音说欢迎词"
# - "开始倪校语音模式"
# - "停止语音助手"
```

## 💡 高级使用技巧

### 1. 组合工具使用

FractFlow的分形智能允许工具组合使用：

```bash
# 示例：研究报告生成流程
# 1. 网络搜索收集信息
python tools/core/websearch/websearch_agent.py --voice-interactive
# 语音指令: "搜索人工智能在教育领域的应用"

# 2. 生成配图  
python tools/core/gpt_imagen/gpt_imagen_agent.py --voice-interactive
# 语音指令: "生成图片，文件名ai_education.png，内容是AI在教育中的应用场景"

# 3. 整合成文章（自动调用上述工具）
python tools/composite/visual_article_agent.py --voice-interactive
# 语音指令: "写一篇关于AI在教育领域应用的研究报告"
```

### 2. 语音模式最佳实践

```bash
# 建议的语音交互工作流
# 1. 启动语音模式
python 前端/hkust_ai_assistant_entry.py --voice-interactive

# 2. 使用自然语言指令
👤 您: 启动语音助手
👤 您: 请帮我搜索最新的机器学习论文
👤 您: 用倪校长的声音总结搜索结果
👤 您: 停止语音助手

# 3. 灵活切换模式
👤 您: voice off  # 切换到文本模式进行复杂操作
👤 您: voice     # 重新激活语音模式
```

### 3. 自定义配置

可以通过环境变量或代码自定义模型配置：

```python
# 自定义语音交互配置
from FractFlow.infra.config import ConfigManager

config = ConfigManager(
    provider='qwen',               # 支持语音的模型
    qwen_model='qwen-plus',        # 更强的理解能力
    max_iterations=20,             # 增加语音对话轮次
    temperature=0.7,               # 更自然的语音风格
    custom_system_prompt="你是一个专业的语音助手..."
)
```

## 🔍 故障排除

### 常见问题

#### 1. API密钥问题
```bash
# 检查环境变量
echo $DEEPSEEK_API_KEY
echo $OPENAI_API_KEY
echo $QWEN_API_KEY

# 重新设置
export DEEPSEEK_API_KEY="your_key_here"
export QWEN_API_KEY="your_qwen_key_here"
```

#### 2. 语音功能问题
```bash
# 检查语音交互模式
python 前端/hkust_ai_assistant_entry.py --voice-interactive

# 测试基础语音助手
python tools/core/guang_voice_assistant/guang_voice_assistant_agent.py --voice-interactive

# 检查倪校语音包
curl http://localhost:7861/health  # TTS服务器状态
```

#### 3. 模式切换问题
```bash
# 在交互中测试模式切换
python 前端/hkust_ai_assistant_entry.py --interactive
# 输入: voice
# 输入: voice off
# 输入: 语音模式
# 输入: 文本模式
```

#### 4. 依赖问题
```bash
# 重新安装语音相关依赖
uv pip install pyaudio websockets requests

# 检查音频设备
python -c "import pyaudio; print('PyAudio available')"
```

### 调试技巧

```bash
# 启用详细日志
export FRACTFLOW_DEBUG=1
python tools/core/guang_voice_assistant/guang_voice_assistant_agent.py --voice-interactive

# 检查语音工具状态
python tools/core/guang_voice_assistant/guang_voice_assistant_agent.py --interactive
# 输入: 启动语音助手
# 输入: 语音状态查询
```

## 🚀 进阶技巧

### 1. 自定义语音工作流

创建专属的语音工作流脚本：

```python
# voice_workflow.py
import asyncio
from 前端.api_entry import start_voice_assistant, send_message

async def voice_research_workflow(topic):
    """语音研究工作流"""
    await start_voice_assistant()
    
    # 步骤1：启动语音助手
    await send_message("启动语音助手")
    
    # 步骤2：语音指令进行研究
    advice = await send_message(f"请为我的{topic}研究提供建议")
    
    # 步骤3：用倪校长声音总结
    summary = await send_message(f"请用倪校长的声音总结{topic}的研究要点")
    
    # 步骤4：停止语音助手
    await send_message("停止语音助手")
    
    return advice, summary

# 使用
asyncio.run(voice_research_workflow("人工智能"))
```

### 2. 多模态集成（文本+语音）

```python
# multi_modal_agent.py
from FractFlow.tool_template import ToolTemplate

class MultiModalAgent(ToolTemplate):
    SYSTEM_PROMPT = """
你是一个多模态AI助手，能够无缝切换文本和语音交互模式。
根据用户需求智能选择合适的交互方式。

当用户要求语音交互时，启动语音模式；
当用户需要复杂文本处理时，切换到文本模式。
"""
    
    TOOL_DESCRIPTION = """多模态处理工具，支持文本和语音交互"""
    
    TOOLS = [
        ("tools/core/file_io/file_io_mcp.py", "file_ops"),
        ("tools/core/gpt_imagen/gpt_imagen_mcp.py", "image_gen"),
        ("tools/core/guang_voice_assistant/guang_voice_assistant_mcp.py", "voice_assistant")
    ]

# 使用多模态功能
# python multi_modal_agent.py --voice-interactive
```

### 3. 语音指令快捷方式

```bash
# 创建语音指令别名
alias voice-search="python tools/core/websearch/websearch_agent.py --voice-interactive"
alias voice-image="python tools/core/gpt_imagen/gpt_imagen_agent.py --voice-interactive"  
alias voice-article="python tools/composite/visual_article_agent.py --voice-interactive"
alias voice-assistant="python 前端/hkust_ai_assistant_entry.py --voice-interactive"

# 使用别名快速启动
voice-assistant
voice-search
voice-image
```

## 📚 学习资源

### 官方文档
- **项目README**：`README.md` - 基础介绍和安装
- **前端指南**：`前端/README.md` - 前端开发指南
- **更新日志**：`前端/CHANGELOG.md` - 版本历史

### 示例代码
- **核心工具**：`tools/core/` - 基础功能实现
- **复合工具**：`tools/composite/` - 高级应用示例
- **模板代码**：`FractFlow/tool_template.py` - 工具开发模板

### 社区资源
- **GitHub仓库**：https://github.com/RRiiiccckkk/FractFlow
- **Issues**：问题反馈和功能建议
- **Discussions**：使用经验分享

## 🎉 总结

FractFlow为您提供了一个完整的分形智能平台，无论是简单的文件操作、图像生成，还是复杂的学术研究、内容创作，都能找到合适的工具和解决方案。

**核心优势**：
- 🧠 **分形智能**：工具可嵌套组合，实现复杂功能
- 🔧 **灵活配置**：支持多种AI模型和自定义配置
- 🎯 **专业工具**：覆盖文本、图像、语音、视频等多个领域
- 📚 **学术支持**：专门的HKUST AI Assistant学术功能
- 🌐 **前端友好**：标准化API便于集成开发

开始您的FractFlow之旅吧！ 🚀 