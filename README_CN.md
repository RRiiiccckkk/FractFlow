# FractFlow

FractFlow 是一个分形智能架构，将智能分解为可嵌套的 Agent-Tool 单元，通过递归组合构建动态演进的分布式认知系统。

## 设计理念

FractFlow 是一个分形智能架构，将智能分解为可嵌套的 Agent-Tool 单元，通过递归组合构建动态演进的分布式认知系统。

每个智能体不仅具备认知能力，还拥有调用其他智能体的能力，形成自指、自组织、自适应的智能流。

类似章鱼的每个触手都有自己的大脑协作结构，FractFlow 通过模块化智能的组合与协调，实现结构可塑、行为演进的分布式智能形态。

## 安装

请先安装 "uv"：https://docs.astral.sh/uv/#installation

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

注意：项目仍在开发中。如果依赖不满足，请手动安装：`uv pip install XXXX`。

### uv 的环境隔离优势

当工具生态系统扩展时，不同的工具可能需要不同的依赖包版本。uv 提供了强大的环境隔离功能：

```bash
# 为特定工具创建独立环境
cd tools/your_specific_tool/
uv venv
source .venv/bin/activate

# 安装该工具特定的依赖
uv pip install specific_package==1.2.3

# 运行工具时将使用独立环境
python your_tool_agent.py
```

**特别适用场景**：
- **第三方工具集成**：从其他 GitHub 仓库包装工具时，避免依赖冲突
- **版本兼容性**：不同工具需要同一库的不同版本
- **实验性开发**：测试新依赖包时不影响主环境

这种灵活的环境管理让 FractFlow 能够支持更复杂、更多样化的工具生态系统。

## 环境配置

### .env 文件设置

在项目根目录创建 `.env` 文件，配置必要的 API 密钥：

```bash
# 创建 .env 文件
touch .env
```

`.env` 文件内容示例：

```env
# AI 模型 API 密钥（至少配置一个）

# DeepSeek API 密钥
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# OpenAI API 密钥（用于 GPT 模型和图像生成）
OPENAI_API_KEY=your_openai_api_key_here
COMPLETION_API_KEY=your_openai_api_key_here

# Qwen API 密钥（阿里云通义千问）
QWEN_API_KEY=your_qwen_api_key_here

# 可选：自定义 API 基础 URL
# DEEPSEEK_BASE_URL=https://api.deepseek.com
# OPENAI_BASE_URL=https://api.openai.com/v1
```

### API 密钥获取

#### DeepSeek（推荐）
1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com/)
2. 注册账户并获取 API 密钥
3. 设置 `DEEPSEEK_API_KEY` 环境变量

#### OpenAI
1. 访问 [OpenAI API 平台](https://platform.openai.com/api-keys)
2. 创建 API 密钥
3. 设置 `OPENAI_API_KEY` 和 `COMPLETION_API_KEY` 环境变量
4. **注意**：图像生成功能需要 OpenAI API 密钥

#### Qwen（可选）
1. 访问 [阿里云 DashScope](https://dashscope.console.aliyun.com/)
2. 开通通义千问服务并获取 API 密钥
3. 设置 `QWEN_API_KEY` 环境变量

### 配置验证

验证环境配置是否正确：

```bash
# 测试基础功能
python tools/core/weather/weather_agent.py --query "How is the weather in New York?"
```

## 快速开始

### 基础使用

FractFlow 中的每个工具都支持三种运行模式：

```bash
# MCP 服务器模式（默认，无需手动启动，一般由程序自动启动）
python tools/core/file_io/file_io_agent.py

# 交互模式
python tools/core/file_io/file_io_agent.py --interactive

# 单次查询模式
python tools/core/file_io/file_io_agent.py --query "读取 README.md 文件"
```

### 第一个工具运行

让我们运行一个简单的文件操作：

```bash
python tools/core/file_io/file_io_agent.py --query "读取项目根目录的 README.md 文件前10行"
```

## 工具开发教程

### 5分钟快速入门：Hello World 工具

创建你的第一个 FractFlow 工具只需要继承 `ToolTemplate` 并定义两个必需属性：

```python
# my_hello_tool.py
import os
import sys

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

from FractFlow.tool_template import ToolTemplate

class HelloTool(ToolTemplate):
    """简单的问候工具"""
    
    SYSTEM_PROMPT = """
你是一个友好的问候助手。
当用户提供姓名时，请给出个性化的问候。
请用中文回复，保持友好和热情的语调。
"""
    
    TOOL_DESCRIPTION = """
生成个性化问候语的工具。

参数:
    query: str - 用户的姓名或问候请求

返回:
    str - 个性化的问候消息
"""

if __name__ == "__main__":
    HelloTool.main()
```

运行你的工具：

```bash
# 交互模式
python my_hello_tool.py --interactive

# 单次查询
python my_hello_tool.py --query "我叫张三"
```

**核心概念理解：**
- `SYSTEM_PROMPT`：定义智能体的行为和响应方式
- `TOOL_DESCRIPTION`：**重要**：这是暴露给上层Agent的工具使用手册，在分形智能中上层Agent通过阅读这个描述来理解如何调用下层工具
- `ToolTemplate`：提供统一的运行框架（MCP服务器、交互、单次查询三种模式）

### 30分钟实战：三个经典场景

#### 场景1：基于文件操作的工具开发

**参考实现**：[`tools/core/file_io/file_io_agent.py`](tools/core/file_io/file_io_agent.py)

**扩展要点**：
- 继承 `ToolTemplate` 基类，获得三种运行模式支持
- 引用 `file_io_mcp.py` 作为底层文件操作工具
- 自定义 `SYSTEM_PROMPT` 实现特定的文件分析逻辑
- 配置适当的迭代次数和模型参数

**创建步骤**：
1. 复制 file_io_agent.py 的基本结构
2. 修改 `SYSTEM_PROMPT` 添加你的分析逻辑（如统计分析、内容摘要等）
3. 调整 `TOOL_DESCRIPTION` 描述新的功能特性
4. 根据任务复杂度在 `create_config()` 中调整参数

**核心配置示例**：
```python
TOOLS = [("tools/core/file_io/file_io_mcp.py", "file_operations")]
# 添加你的专业分析提示词到 SYSTEM_PROMPT
```

#### 场景2：集成图像生成的工具开发

**参考实现**：[`tools/core/gpt_imagen/gpt_imagen_agent.py`](tools/core/gpt_imagen/gpt_imagen_agent.py)

**核心特点**：
- 支持文本到图像和图像编辑两种模式
- 严格的路径参数保持策略
- 自动提示词优化机制

**自定义方向**：
- **提示词工程**：修改 `SYSTEM_PROMPT` 添加特定的提示词优化策略
- **后处理集成**：结合其他图像处理工具实现复合功能
- **批量处理**：扩展为支持多图像生成的工作流
- **风格定制**：针对特定艺术风格或用途优化

**关键配置**：
```python
TOOLS = [("tools/core/gpt_imagen/gpt_imagen_mcp.py", "gpt_image_generator_operations")]
# 在 SYSTEM_PROMPT 中定义你的图像生成策略
```

#### 场景3：分形智能演示（Visual Article Agent）

**完整实现**：[`tools/composite/visual_article_agent.py`](tools/composite/visual_article_agent.py)

**扩展方向**：
- 添加更多专业工具（如网络搜索、数据分析）
- 实现更复杂的内容生成策略
- 集成不同的文件格式输出

**分形智能核心理解：**
- **递归组合**：工具可以调用其他工具，形成多层智能结构
- **专业分工**：每个工具专注特定领域，通过组合实现复杂功能
- **自适应协调**：高层工具根据任务需求动态选择和组合底层工具

### 深度掌握：架构原理

#### ToolTemplate 生命周期

```python
# 1. 类定义阶段
class MyTool(ToolTemplate):
    SYSTEM_PROMPT = "..."      # 定义智能体行为
    TOOL_DESCRIPTION = "..."   # 定义工具接口
    TOOLS = [...]              # 声明依赖工具

# 2. 初始化阶段
@classmethod
async def create_agent(cls):
    config = cls.create_config()           # 创建配置
    agent = Agent(config=config)           # 创建智能体
    await cls._add_tools_to_agent(agent)   # 添加工具
    return agent

# 3. 运行阶段
def main(cls):
    # 根据命令行参数选择运行模式
    if args.interactive:
        cls._run_interactive()      # 交互模式
    elif args.query:
        cls._run_single_query()     # 单次查询
    else:
        cls._run_mcp_server()       # MCP服务器模式
```

#### 配置系统详解

FractFlow 提供三级配置定制：

```python
# 级别1：使用默认配置
class SimpleTool(ToolTemplate):
    SYSTEM_PROMPT = "..."
    TOOL_DESCRIPTION = "..."
    # 自动使用 DeepSeek 默认配置

# 级别2：部分定制
class CustomTool(ToolTemplate):
    SYSTEM_PROMPT = "..."
    TOOL_DESCRIPTION = "..."
    
    @classmethod
    def create_config(cls):
        return ConfigManager(
            provider='deepseek',           # 切换模型提供商
            openai_model='deepseek-reasoner',       # 指定模型
            max_iterations=20           # 调整迭代次数
        )

# 级别3：完全定制
class AdvancedTool(ToolTemplate):
    SYSTEM_PROMPT = "..."
    TOOL_DESCRIPTION = "..."
    
    @classmethod
    def create_config(cls):
        from dotenv import load_dotenv
        load_dotenv()
        
        return ConfigManager(
            provider='qwen',
            anthropic_model='qwen-plus',
            max_iterations=50,
            temperature=0.7,
            custom_system_prompt=cls.SYSTEM_PROMPT + "\n额外指令...",
            tool_calling_version='turbo',
            timeout=120
        )
```

## 工具展示

### 核心工具

#### File I/O Agent - 文件操作专家
```bash
# 基础文件操作
python tools/core/file_io/file_io_agent.py --query "读取 config.json 文件"
python tools/core/file_io/file_io_agent.py --query "在 output.txt 中写入'Hello World'"

# 高级操作
python tools/core/file_io/file_io_agent.py --query "读取大文件 data.csv 的第100-200行"
python tools/core/file_io/file_io_agent.py --query "删除 temp.log 中包含'ERROR'的所有行"
```

**功能特色：**
- 智能文件操作：读取、写入、删除、插入
- 大文件分块处理
- 行级精确操作
- 自动目录创建

#### GPT Imagen Agent - AI图像生成
```bash
# 图像生成
python tools/core/gpt_imagen/gpt_imagen_agent.py --query "Generate image: save_path='spring_garden.png' prompt='a beautiful spring garden with flowers'"
python tools/core/gpt_imagen/gpt_imagen_agent.py --query "Generate image: save_path='robot.png' prompt='futuristic robot illustration'"
```

#### Web Search Agent - 网络搜索
```bash
# 网络搜索
python tools/core/websearch/websearch_agent.py --query "Latest AI technology developments"
python tools/core/websearch/websearch_agent.py --query "Python performance optimization methods"
```


#### Weather Agent - 天气查询助手（仅限美国地区）
```bash
# 天气查询（仅支持美国城市）
python tools/core/weather/weather_agent.py --query "Weather in New York today"
python tools/core/weather/weather_agent.py --query "5-day forecast for San Francisco"
```

此工具只能查询美国境内的天气信息。

#### Visual Question Answer - 视觉问答
```bash
# 图像理解（基于Qwen-VL-Plus模型）
python tools/core/visual_question_answer/vqa_agent.py --query "Image: /path/to/image.jpg What objects are in this picture?"
python tools/core/visual_question_answer/vqa_agent.py --query "Image: /path/to/photo.png Describe the scene in detail"
```

#### Realtime Voice Interactive - 实时语音交互助手

FractFlow 提供先进的实时语音交互系统，支持默认音色和倪校长声音克隆（including nixiao）：

```bash
# 前端集成版（推荐 - 支持三种模式选择）
python 前端/hkust_ai_assistant_entry.py
# 选择模式 2（默认语音） 或 模式 3（倪校语音）

# 命令行直接启动
python 前端/hkust_ai_assistant_entry.py --mode voice      # 默认语音模式
python 前端/hkust_ai_assistant_entry.py --mode ni-voice   # 倪校语音模式

# 或使用简短参数
python 前端/hkust_ai_assistant_entry.py --voice-interactive      # 默认语音
python 前端/hkust_ai_assistant_entry.py --ni-voice-interactive   # 倪校语音

# 底层工具直接调用
python tools/core/realtime_voice_interactive/realtime_voice_interactive.py     # 默认音色
python tools/core/realtime_voice_interactive/realtime_voice_interactive.py ni  # 倪校音色
```

**🎯 三种交互模式对比**：

| 模式 | 音色来源 | 适用场景 | 技术特点 |
|------|----------|----------|----------|
| 📚 学术问答 | 文本回复 | 学术咨询、研究支持 | 专业、严谨、详细 |
| 🎤 默认语音 | 千问Omni内置 | 日常对话、快速交互 | 稳定、快速、开箱即用 |
| 🎓 倪校语音 | 声音克隆技术 | 正式场合、学术交流 | 权威、专业、流式播放 |

**功能特色**：
- 🎤 **实时语音识别**：自然中文语音输入，自动转换为文本
- 🔊 **双音色模式**：系统默认音色 + 倪校长克隆音色
- ⚡ **极速打断机制**：0.01ms响应时间，多级打断处理
- 🎵 **动态音量检测**：自适应背景噪音校准和连续性验证  
- 🚀 **流式TTS播放**：逐句生成播放，大幅提升响应速度（倪校模式）
- 🧠 **分形智能**：支持嵌套Agent调用，自然语言优先
- 🎯 **企业级体验**：专业级语音交互解决方案

**使用说明**：
- 自然说话提问
- 系统会在您开始说话时自动打断AI回答
- 等待AI完整回答后继续对话
- 按 Ctrl+C 退出系统
- 支持文本指令："voice off" 切换到文本模式

### 复合工具

#### Visual Article Agent - 图文并茂文章生成器

这是分形智能的典型代表，协调多个工具生成完整的图文内容：

```bash
# 生成完整的图文文章
python tools/composite/visual_article_agent.py --query "写一篇关于人工智能发展的文章，包含配图"

# 定制文章
python tools/composite/visual_article_agent.py --query "设定：一个视觉识别AI统治社会的世界，人类只能依赖它解释图像。主人公却拥有“人类视觉直觉”，并因此被怀疑为异常个体。
要求：以第一人称，写一段剧情片段，展现他与AI模型对图像理解的冲突。
情绪基调：冷峻、怀疑、诗性。"
```

![](assets/visual_article.gif)

**工作流程：**
1. 分析文章需求和结构
2. 使用 `file_manager_agent` 写入章节内容
3. 使用 `image_creator_agent` 生成配套插图
4. 整合为完整的 Markdown 文档

**输出示例：**
```
output/visual_article_generator/ai_development/
├── article.md           # 完整文章
└── images/             # 配套图片
    ├── section1-fig1.png
    ├── section2-fig1.png
    └── section3-fig1.png
```

#### Web Save Agent - 网页智能保存
```bash
# 智能网页保存（分形智能示例）
python tools/composite/web_save_agent.py --query "Search for latest Python tutorials and save to a comprehensive guide file"
python tools/composite/web_save_agent.py --query "Find information about machine learning and create an organized report"
```

**功能特色：**
- 结合网络搜索和文件保存的分形智能
- 智能内容组织和结构化
- 自动文件路径管理
- 多轮搜索支持

## API 参考

### 两种工具开发方式

FractFlow 提供两种灵活的工具开发方式，满足不同的开发需求：

#### 方式一：继承 ToolTemplate（推荐）

标准化的工具开发方式，自动支持三种运行模式：

```python
from FractFlow.tool_template import ToolTemplate

class MyTool(ToolTemplate):
    """标准工具类"""
    
    SYSTEM_PROMPT = """你的工具行为指令"""
    TOOL_DESCRIPTION = """工具功能描述"""
    
    # 可选：依赖其他工具
    TOOLS = [("path/to/tool.py", "tool_name")]
    
    @classmethod
    def create_config(cls):
        return ConfigManager(...)

# 自动支持三种运行模式
# python my_tool.py                    # MCP 服务器模式
# python my_tool.py --interactive      # 交互模式  
# python my_tool.py --query "..."      # 单次查询模式
```


#### 方式二：自定义 Agent 类

完全自主的开发方式：

```python
from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager

async def main():
    # 自定义配置
    config = ConfigManager(
        provider='deepseek',
        deepseek_model='deepseek-chat',
        max_iterations=5
    )
    
    # 创建Agent
    agent = Agent(config=config, name='my_agent')
    
    # 手动添加工具
    agent.add_tool("./tools/weather/weather_mcp.py", "forecast_tool")
    
    # 初始化并使用
    await agent.initialize()
    result = await agent.process_query("你的查询")
    await agent.shutdown()
```

### ToolTemplate 基类

FractFlow 的核心基类，提供统一的工具开发框架：

```python
class ToolTemplate:
    """FractFlow 工具模板基类"""
    
    # 必需属性
    SYSTEM_PROMPT: str      # 智能体系统提示
    TOOL_DESCRIPTION: str   # 工具功能描述
    
    # 可选属性
    TOOLS: List[Tuple[str, str]] = []        # 依赖工具列表
    MCP_SERVER_NAME: Optional[str] = None    # MCP服务器名称
    
    # 核心方法
    @classmethod
    def create_config(cls) -> ConfigManager:
        """创建配置 - 可重写"""
        pass
    
    @classmethod
    async def create_agent(cls) -> Agent:
        """创建智能体实例"""
        pass
    
    @classmethod
    def main(cls):
        """主入口 - 支持三种运行模式"""
        pass
```

#### 关键属性详解

**TOOL_DESCRIPTION 的重要作用**：

在FractFlow的分形智能架构中，`TOOL_DESCRIPTION` 不仅仅是给开发者看的文档，更重要的是：

- **上层Agent的参考手册**：当一个复合工具（如visual_article_agent）调用底层工具时，上层Agent会读取底层工具的TOOL_DESCRIPTION来理解如何正确使用它
- **工具接口规范**：定义了工具的输入参数格式、返回值结构、使用场景等
- **智能调用依据**：上层Agent根据这个描述判断何时以及如何调用特定工具

**示例**：在visual_article_agent中调用file_io工具时：
```python
# 上层Agent会读取file_io工具的TOOL_DESCRIPTION
# 然后根据描述中的参数格式来构造调用请求
TOOLS = [("tools/core/file_io/file_io_mcp.py", "file_operations")]
```

因此，编写清晰、准确的TOOL_DESCRIPTION对于分形智能的正确运作至关重要。然而，TOOL_DESCRIPTION 也不要过长。

**SYSTEM_PROMPT 编写要点**：

与TOOL_DESCRIPTION面向上层Agent不同，`SYSTEM_PROMPT` 是当前Agent的内部行为指令。参考visual_article_agent的实践：

**结构化设计**：
```python
# 参考：tools/composite/visual_article_agent.py
SYSTEM_PROMPT = """
【严格约束】
❌ 绝对禁止：直接输出内容
✅ 必须执行：通过工具调用完成任务

【工作流程】
1. 分析需求
2. 调用相关工具
3. 验证结果
"""
```

**关键技巧**：
- **明确禁止**：用 `❌` 定义不能做什么，避免常见错误
- **强制执行**：用 `✅` 指定必须的行为模式
- **流程化**：将复杂任务分解为清晰步骤
- **验证机制**：要求每步操作后确认结果

这种设计确保Agent行为的一致性和可预测性，是复合工具可靠运行的关键。

### 配置管理

```python
from FractFlow.infra.config import ConfigManager

# 基础配置
config = ConfigManager()

# 自定义配置
config = ConfigManager(
    provider='openai',              # 模型提供商：openai/anthropic/deepseek
    openai_model='gpt-4',          # 具体模型
    max_iterations=20,             # 最大迭代次数
    temperature=0.7,               # 生成温度
    custom_system_prompt="...",    # 自定义系统提示
    tool_calling_version='stable', # 工具调用版本：stable/turbo
    timeout=120                    # 超时设置
)
```


## 文件组织
```
tools/
├── core/                 # 核心工具
│   └── your_tool/
│       ├── your_tool_agent.py    # 主要智能体
│       ├── your_tool_mcp.py      # MCP 工具实现
│       └── __init__.py
└── composite/            # 复合工具
    └── your_composite_tool.py
```
#### 命名规范
- 文件名：`snake_case`
- 类名：`PascalCase`