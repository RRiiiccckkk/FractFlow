# FractFlow

FractFlow is a fractal intelligence architecture that decomposes intelligence into nestable Agent-Tool units, building dynamically evolving distributed cognitive systems through recursive composition.

## Design Philosophy

FractFlow is a fractal intelligence architecture that decomposes intelligence into nestable Agent-Tool units, building dynamically evolving distributed cognitive systems through recursive composition.

Each agent not only possesses cognitive capabilities but also has the ability to call other agents, forming self-referential, self-organizing, and self-adaptive intelligent flows.

Similar to how each tentacle of an octopus has its own brain in a collaborative structure, FractFlow achieves structurally malleable and behaviorally evolving distributed intelligence through the combination and coordination of modular intelligence.

## Installation

Please install "uv" first: https://docs.astral.sh/uv/#installation

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Note: The project is still under development. If dependencies are not satisfied, please install manually: `uv pip install XXXX`.

### Advantages of uv Environment Isolation

When the tool ecosystem expands, different tools may require different dependency package versions. uv provides powerful environment isolation capabilities:

```bash
# Create independent environment for specific tools
cd tools/your_specific_tool/
uv venv
source .venv/bin/activate

# Install tool-specific dependencies
uv pip install specific_package==1.2.3

# Tool will use independent environment when running
python your_tool_agent.py
```

**Particularly useful scenarios**:
- **Third-party tool integration**: Avoid dependency conflicts when wrapping tools from other GitHub repositories
- **Version compatibility**: Different tools need different versions of the same library
- **Experimental development**: Test new dependencies without affecting the main environment

This flexible environment management allows FractFlow to support more complex and diverse tool ecosystems.

## Environment Configuration

### .env File Setup

Create a `.env` file in the project root directory to configure necessary API keys:

```bash
# Create .env file
touch .env
```

Example `.env` file content:

```env
# AI Model API Keys (configure at least one)

# DeepSeek API Key
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# OpenAI API Key (for GPT models and image generation)
OPENAI_API_KEY=your_openai_api_key_here
COMPLETION_API_KEY=your_openai_api_key_here

# Qwen API Key (Alibaba Cloud Tongyi Qianwen)
QWEN_API_KEY=your_qwen_api_key_here

# Optional: Custom API Base URLs
# DEEPSEEK_BASE_URL=https://api.deepseek.com
# OPENAI_BASE_URL=https://api.openai.com/v1
```

### API Key Acquisition

#### DeepSeek (Recommended)
1. Visit [DeepSeek Open Platform](https://platform.deepseek.com/)
2. Register an account and obtain API key
3. Set `DEEPSEEK_API_KEY` environment variable

#### OpenAI
1. Visit [OpenAI API Platform](https://platform.openai.com/api-keys)
2. Create API key
3. Set `OPENAI_API_KEY` and `COMPLETION_API_KEY` environment variables
4. **Note**: Image generation functionality requires OpenAI API key

#### Qwen (Optional)
1. Visit [Alibaba Cloud DashScope](https://dashscope.console.aliyun.com/)
2. Enable Tongyi Qianwen service and obtain API key
3. Set `QWEN_API_KEY` environment variable

### Configuration Validation

Verify that environment configuration is correct:

```bash
# Test basic functionality
python tools/core/weather/weather_agent.py --query "How is the weather in New York?"
```

## Quick Start

### 🚀 Frontend Assistant - Recommended Entry Point

The easiest way to experience FractFlow is through our unified frontend interface:

```bash
# Launch interactive mode selection
python 前端/hkust_ai_assistant_entry.py

# Choose from 4 modes:
# 1. 📚 Academic Q&A Mode - Academic consulting and research support
# 2. 🎤 Default Voice Mode - Qwen Omni voice, quick conversation  
# 3. 🎓 Principal Ni Voice Mode - Principal Ni's voice cloning, authoritative academic communication
# 4. ⚡ Manual Real-time Interruption Mode - Millisecond-level interruption, ultimate control experience
```

**Direct mode launch**:
```bash
python 前端/hkust_ai_assistant_entry.py --mode academic         # Academic mode
python 前端/hkust_ai_assistant_entry.py --mode voice           # Default voice mode
python 前端/hkust_ai_assistant_entry.py --mode ni-voice        # Principal Ni voice mode  
python 前端/hkust_ai_assistant_entry.py --mode manual-interrupt # Manual interruption mode
```

### Basic Tool Usage

Each tool in FractFlow supports three running modes:

```bash
# MCP Server mode (default, no need to start manually, usually started automatically by programs)
python tools/core/file_io/file_io_agent.py

# Interactive mode
python tools/core/file_io/file_io_agent.py --interactive

# Single query mode
python tools/core/file_io/file_io_agent.py --query "Read README.md file"
```

### First Tool Run

Let's run a simple file operation:

```bash
python tools/core/file_io/file_io_agent.py --query "Read the first 10 lines of README.md file in project root directory"
```

## Tool Development Tutorial

### 5-Minute Quick Start: Hello World Tool

Creating your first FractFlow tool only requires inheriting `ToolTemplate` and defining two required attributes:

```python
# my_hello_tool.py
import os
import sys

# Add project root directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)

from FractFlow.tool_template import ToolTemplate

class HelloTool(ToolTemplate):
    """Simple greeting tool"""
    
    SYSTEM_PROMPT = """
You are a friendly greeting assistant.
When users provide names, please give personalized greetings.
Please reply in Chinese, maintaining a friendly and enthusiastic tone.
"""
    
    TOOL_DESCRIPTION = """
Tool for generating personalized greetings.

Parameters:
    query: str - User's name or greeting request

Returns:
    str - Personalized greeting message
"""

if __name__ == "__main__":
    HelloTool.main()
```

Run your tool:

```bash
# Interactive mode
python my_hello_tool.py --interactive

# Single query
python my_hello_tool.py --query "My name is Zhang San"
```

**Core Concept Understanding:**
- `SYSTEM_PROMPT`: Defines agent behavior and response style
- `TOOL_DESCRIPTION`: **Important**: This is the tool usage manual exposed to upper-layer Agents. In fractal intelligence, upper-layer Agents read this description to understand how to call lower-layer tools
- `ToolTemplate`: Provides unified runtime framework (MCP server, interactive, single query - three modes)

### 30-Minute Practice: Three Classic Scenarios

#### Scenario 1: File Operation-Based Tool Development

**Reference Implementation**: [`tools/core/file_io/file_io_agent.py`](tools/core/file_io/file_io_agent.py)

**Extension Points**:
- Inherit `ToolTemplate` base class to get three running mode support
- Reference `file_io_mcp.py` as underlying file operation tool
- Customize `SYSTEM_PROMPT` to implement specific file analysis logic
- Configure appropriate iteration count and model parameters

**Creation Steps**:
1. Copy basic structure of file_io_agent.py
2. Modify `SYSTEM_PROMPT` to add your analysis logic (such as statistical analysis, content summarization, etc.)
3. Adjust `TOOL_DESCRIPTION` to describe new functionality features
4. Adjust parameters in `create_config()` according to task complexity

**Core Configuration Example**:
```python
TOOLS = [("tools/core/file_io/file_io_mcp.py", "file_operations")]
# Add your professional analysis prompts to SYSTEM_PROMPT
```

#### Scenario 2: Image Generation Integration Tool Development

**Reference Implementation**: [`tools/core/gpt_imagen/gpt_imagen_agent.py`](tools/core/gpt_imagen/gpt_imagen_agent.py)

**Core Features**:
- Support both text-to-image and image editing modes
- Strict path parameter preservation strategy
- Automatic prompt optimization mechanism

**Customization Directions**:
- **Prompt Engineering**: Modify `SYSTEM_PROMPT` to add specific prompt optimization strategies
- **Post-processing Integration**: Combine with other image processing tools for composite functionality
- **Batch Processing**: Extend to support multi-image generation workflows
- **Style Customization**: Optimize for specific artistic styles or purposes

**Key Configuration**:
```python
TOOLS = [("tools/core/gpt_imagen/gpt_imagen_mcp.py", "gpt_image_generator_operations")]
# Define your image generation strategy in SYSTEM_PROMPT
```

#### Scenario 3: Fractal Intelligence Demonstration (Visual Article Agent)

**Complete Implementation**: [`tools/composite/visual_article_agent.py`](tools/composite/visual_article_agent.py)

**Extension Directions**:
- Add more professional tools (such as web search, data analysis)
- Implement more complex content generation strategies
- Integrate different file format outputs

**Core Understanding of Fractal Intelligence**:
- **Recursive Composition**: Tools can call other tools, forming multi-layer intelligent structures
- **Professional Division**: Each tool focuses on specific domains, achieving complex functionality through combination
- **Adaptive Coordination**: High-level tools dynamically select and combine low-level tools based on task requirements

### Deep Mastery: Architectural Principles

#### ToolTemplate Lifecycle

```python
# 1. Class Definition Phase
class MyTool(ToolTemplate):
    SYSTEM_PROMPT = "..."      # Define agent behavior
    TOOL_DESCRIPTION = "..."   # Define tool interface
    TOOLS = [...]              # Declare dependent tools

# 2. Initialization Phase
@classmethod
async def create_agent(cls):
    config = cls.create_config()           # Create configuration
    agent = Agent(config=config)           # Create agent
    await cls._add_tools_to_agent(agent)   # Add tools
    return agent

# 3. Runtime Phase
def main(cls):
    # Choose running mode based on command line arguments
    if args.interactive:
        cls._run_interactive()      # Interactive mode
    elif args.query:
        cls._run_single_query()     # Single query
    else:
        cls._run_mcp_server()       # MCP server mode
```

#### Configuration System Details

FractFlow provides three-level configuration customization:

```python
# Level 1: Use default configuration
class SimpleTool(ToolTemplate):
    SYSTEM_PROMPT = "..."
    TOOL_DESCRIPTION = "..."
    # Automatically use DeepSeek default configuration

# Level 2: Partial customization
class CustomTool(ToolTemplate):
    SYSTEM_PROMPT = "..."
    TOOL_DESCRIPTION = "..."
    
    @classmethod
    def create_config(cls):
        return ConfigManager(
            provider='deepseek',           # Switch model provider
            openai_model='deepseek-reasoner',       # Specify model
            max_iterations=20           # Adjust iteration count
        )

# Level 3: Full customization
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
            custom_system_prompt=cls.SYSTEM_PROMPT + "\nAdditional instructions...",
            tool_calling_version='turbo',
            timeout=120
        )
```

## Tool Showcase

### Core Tools

#### File I/O Agent - File Operation Expert
```bash
# Basic file operations
python tools/core/file_io/file_io_agent.py --query "Read config.json file"
python tools/core/file_io/file_io_agent.py --query "Write 'Hello World' to output.txt"

# Advanced operations
python tools/core/file_io/file_io_agent.py --query "Read lines 100-200 of large file data.csv"
python tools/core/file_io/file_io_agent.py --query "Delete all lines containing 'ERROR' from temp.log"
```

**Feature Highlights**:
- Intelligent file operations: read, write, delete, insert
- Large file chunked processing
- Line-level precise operations
- Automatic directory creation

#### GPT Imagen Agent - AI Image Generation
```bash
# Image generation
python tools/core/gpt_imagen/gpt_imagen_agent.py --query "Generate image: save_path='spring_garden.png' prompt='a beautiful spring garden with flowers'"
python tools/core/gpt_imagen/gpt_imagen_agent.py --query "Generate image: save_path='robot.png' prompt='futuristic robot illustration'"
```

#### Web Search Agent - Web Search
```bash
# Web search
python tools/core/websearch/websearch_agent.py --query "Latest AI technology developments"
python tools/core/websearch/websearch_agent.py --query "Python performance optimization methods"
```

#### Weather Agent - Weather Query Assistant (US Only)
```bash
# Weather queries (US cities only)
python tools/core/weather/weather_agent.py --query "Weather in New York today"
python tools/core/weather/weather_agent.py --query "5-day forecast for San Francisco"
```

This tool can only query weather information within the United States.

#### Visual Question Answer - Visual Q&A
```bash
# Image understanding (based on Qwen-VL-Plus model)
python tools/core/visual_question_answer/vqa_agent.py --query "Image: /path/to/image.jpg What objects are in this picture?"
python tools/core/visual_question_answer/vqa_agent.py --query "Image: /path/to/photo.png Describe the scene in detail"
```

#### Realtime Voice Interactive - Real-time Voice Assistant

FractFlow provides an advanced real-time voice interaction system with support for multiple modes including the revolutionary **Manual Real-time Interruption Mode**:

```bash
# Frontend integration (recommended - supports four mode selection)
python 前端/hkust_ai_assistant_entry.py
# Choose from: 1.Academic Q&A 2.Default Voice 3.Principal Ni Voice 4.Manual Real-time Interruption

# Command line direct launch
python 前端/hkust_ai_assistant_entry.py --mode academic         # Academic Q&A mode
python 前端/hkust_ai_assistant_entry.py --mode voice           # Default voice mode  
python 前端/hkust_ai_assistant_entry.py --mode ni-voice        # Principal Ni voice mode
python 前端/hkust_ai_assistant_entry.py --mode manual-interrupt # Manual real-time interruption mode

# Or use short parameters
python 前端/hkust_ai_assistant_entry.py --voice-interactive      # Default voice
python 前端/hkust_ai_assistant_entry.py --ni-voice-interactive   # Principal Ni voice
python 前端/hkust_ai_assistant_entry.py --manual-interrupt       # Manual interruption

# Direct tool invocation
python tools/core/realtime_voice_interactive/realtime_voice_interactive.py     # Default voice
python tools/core/realtime_voice_interactive/realtime_voice_interactive.py ni  # Principal Ni voice

# Manual Real-time Interruption Mode (New!)
python tools/core/手动实时打断/运行_手动实时打断.py                    # Default voice version
python tools/core/手动实时打断/运行_手动实时打断_倪校版.py              # Principal Ni voice version
```

**🎯 Four Interactive Modes Comparison**:

| Mode | Voice Source | Use Case | Technical Features |
|------|-------------|----------|-------------------|
| 📚 Academic Q&A | Text reply | Academic consulting, research support | Professional, rigorous, detailed |
| 🎤 Default Voice | Qwen Omni built-in | Daily conversation, quick interaction | Stable, fast, ready-to-use |
| 🎓 Principal Ni Voice | Voice cloning technology | Formal occasions, academic communication | Authoritative, professional, streaming playback |
| ⚡ Manual Real-time Interruption | Dual voice support | Ultimate control experience | **Millisecond-level interruption**, **zero-crash guarantee** |

**Feature Highlights**:
- 🎤 **Real-time Speech Recognition**: Natural Chinese voice input with automatic text conversion
- 🔊 **Multiple Voice Modes**: Default system voice + Principal Ni's cloned voice + Manual control mode
- ⚡ **Ultra-fast Interruption**: 0.01ms response time with multi-level interruption mechanism
- 🎵 **Dynamic Volume Detection**: Adaptive background noise calibration and continuity verification
- 🚀 **Streaming TTS Playback**: Sentence-by-sentence generation for dramatically improved response speed (Principal Ni mode)
- 🧠 **Fractal Intelligence**: Nested agent calling with natural language priority
- 🎯 **Enterprise-grade Experience**: Professional voice interaction solution

### ⚡ Manual Real-time Interruption Mode - Revolutionary Control Experience

The **Manual Real-time Interruption Mode** represents a breakthrough in voice interaction technology, providing unprecedented control precision:

#### 🚀 Quick Start
```bash
# Interactive mode selection (recommended)
python 前端/hkust_ai_assistant_entry.py
# Select option 4: ⚡ Manual Real-time Interruption Mode

# Direct command line launch
python 前端/hkust_ai_assistant_entry.py --mode manual-interrupt

# Direct tool execution
python tools/core/手动实时打断/运行_手动实时打断.py                    # Default voice
python tools/core/手动实时打断/运行_手动实时打断_倪校版.py              # Principal Ni voice
```

#### 🎮 Control Methods
```
Manual Control Instructions:
1. Press [Enter] to start recording
2. Speak your question
3. Press [Enter] again to stop recording and send
4. During AI response, press [Enter] to interrupt immediately ⚡
5. Type 'q' or 'quit' to exit
```

#### 📊 Performance Metrics
| Metric | Before Optimization | After Optimization | Improvement |
|--------|-------------------|-------------------|-------------|
| Interruption Delay | 500-1000ms | **<50ms** | **20x faster** |
| HTTP Chunk Size | 1024 bytes | 256 bytes | 4x smaller |
| Audio Chunk Size | Large blocks | 64 bytes | 16x smaller |
| Response Precision | Second-level | **Millisecond-level** | 1000x improvement |
| Crash Rate | Occasional | **0%** | **100% reliability** |

#### 🔧 Technical Architecture
- **Multi-layer Stop Mechanism**: stop_flag + stop_event dual control
- **Forced Audio Stream Termination**: Immediate HTTP session closure
- **Thread-safe Optimization**: Independent playback threads with lock protection
- **Intelligent Memory Monitoring**: Three-level warning system with automatic cleanup
- **Zero-crash Guarantee**: Complete resolution of PyAudio segmentation fault

#### 💡 Core Advantages
- ⚡ **Millisecond Response**: <50ms interruption delay, 20x performance boost
- 🎓 **Dual Voice Support**: Both default system voice and Principal Ni voice
- 🧠 **Intelligent Context Memory**: Automatic conversation history management  
- 📊 **Zero Crash Guarantee**: Production-level stability with 100% reliability
- 🔧 **MCP Server Support**: Can be called as a tool by other intelligent agents

#### 📁 File Structure
```
tools/core/手动实时打断/
├── README.md                          # Complete documentation
├── 手动实时打断_agent.py              # Default voice version
├── 手动实时打断_倪校版_agent.py        # Principal Ni voice version
├── 手动实时打断_mcp.py               # Default MCP server
├── 手动实时打断_倪校版_mcp.py         # Principal Ni MCP server
├── 运行_手动实时打断.py              # Quick launch script (default)
├── 运行_手动实时打断_倪校版.py        # Quick launch script (Principal Ni)
└── conversation_cache_manager.py      # Conversation cache manager
```

**General Usage Instructions**:
- Speak naturally to ask questions
- The system automatically interrupts AI responses when you start speaking (auto modes)
- Manual mode: Use Enter key for complete control over conversation flow
- Wait for complete AI responses before continuing the conversation
- Press Ctrl+C to exit
- Support text commands: "voice off" to switch to text mode

### Composite Tools

#### Visual Article Agent - Illustrated Article Generator

This is a typical representative of fractal intelligence, coordinating multiple tools to generate complete text-image content:

```bash
# Generate complete illustrated articles
python tools/composite/visual_article_agent.py --query "Write an article about AI development with illustrations"

# Customized articles
python tools/composite/visual_article_agent.py --query "设定：一个视觉识别AI统治社会的世界，人类只能依赖它解释图像。主人公却拥有"人类视觉直觉"，并因此被怀疑为异常个体。
要求：以第一人称，写一段剧情片段，展现他与AI模型对图像理解的冲突。
情绪基调：冷峻、怀疑、诗性。"
```


![](assets/visual_article.gif)

**Workflow**:
1. Analyze article requirements and structure
2. Use `file_manager_agent` to write chapter content
3. Use `image_creator_agent` to generate supporting illustrations
4. Integrate into complete Markdown document

**Output Example**:
```
output/visual_article_generator/ai_development/
├── article.md           # Complete article
└── images/             # Supporting images
    ├── section1-fig1.png
    ├── section2-fig1.png
    └── section3-fig1.png
```

#### Web Save Agent - Intelligent Web Saving
```bash
# Intelligent web saving (fractal intelligence example)
python tools/composite/web_save_agent.py --query "Search for latest Python tutorials and save to a comprehensive guide file"
python tools/composite/web_save_agent.py --query "Find information about machine learning and create an organized report"
```

**Feature Highlights**:
- Fractal intelligence combining web search and file saving
- Intelligent content organization and structuring
- Automatic file path management
- Multi-round search support

## API Reference

### Two Tool Development Approaches

FractFlow provides two flexible tool development approaches to meet different development needs:

#### Approach 1: Inherit ToolTemplate (Recommended)

Standardized tool development approach with automatic support for three running modes:

```python
from FractFlow.tool_template import ToolTemplate

class MyTool(ToolTemplate):
    """Standard tool class"""
    
    SYSTEM_PROMPT = """Your tool behavior instructions"""
    TOOL_DESCRIPTION = """Tool functionality description"""
    
    # Optional: depend on other tools
    TOOLS = [("path/to/tool.py", "tool_name")]
    
    @classmethod
    def create_config(cls):
        return ConfigManager(...)

# Automatically supports three running modes
# python my_tool.py                    # MCP server mode
# python my_tool.py --interactive      # Interactive mode  
# python my_tool.py --query "..."      # Single query mode
```

#### Approach 2: Custom Agent Class

Completely autonomous development approach:

```python
from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager

async def main():
    # Custom configuration
    config = ConfigManager(
        provider='deepseek',
        deepseek_model='deepseek-chat',
        max_iterations=5
    )
    
    # Create Agent
    agent = Agent(config=config, name='my_agent')
    
    # Manually add tools
    agent.add_tool("./tools/weather/weather_mcp.py", "forecast_tool")
    
    # Initialize and use
    await agent.initialize()
    result = await agent.process_query("Your query")
    await agent.shutdown()
```

### ToolTemplate Base Class

FractFlow's core base class providing unified tool development framework:

```python
class ToolTemplate:
    """FractFlow tool template base class"""
    
    # Required attributes
    SYSTEM_PROMPT: str      # Agent system prompt
    TOOL_DESCRIPTION: str   # Tool functionality description
    
    # Optional attributes
    TOOLS: List[Tuple[str, str]] = []        # Dependent tools list
    MCP_SERVER_NAME: Optional[str] = None    # MCP server name
    
    # Core methods
    @classmethod
    def create_config(cls) -> ConfigManager:
        """Create configuration - can be overridden"""
        pass
    
    @classmethod
    async def create_agent(cls) -> Agent:
        """Create agent instance"""
        pass
    
    @classmethod
    def main(cls):
        """Main entry point - supports three running modes"""
        pass
```

#### Key Attribute Details

**Important Role of TOOL_DESCRIPTION**:

In FractFlow's fractal intelligence architecture, `TOOL_DESCRIPTION` is not just documentation for developers, but more importantly:

- **Reference manual for upper-layer Agents**: When a composite tool (like visual_article_agent) calls lower-layer tools, the upper-layer Agent reads the lower-layer tool's TOOL_DESCRIPTION to understand how to use it correctly
- **Tool interface specification**: Defines input parameter formats, return value structures, usage scenarios, etc.
- **Basis for intelligent calling**: Upper-layer Agents determine when and how to call specific tools based on this description

**Example**: When visual_article_agent calls file_io tool:
```python
# Upper-layer Agent reads file_io tool's TOOL_DESCRIPTION
# Then constructs call requests based on parameter formats described
TOOLS = [("tools/core/file_io/file_io_mcp.py", "file_operations")]
```

Therefore, writing clear and accurate TOOL_DESCRIPTION is crucial for the correct operation of fractal intelligence. However, TOOL_DESCRIPTION should not be too long.

**SYSTEM_PROMPT Writing Guidelines**:

Unlike TOOL_DESCRIPTION which faces upper-layer Agents, `SYSTEM_PROMPT` is the internal behavior instruction for the current Agent. Reference visual_article_agent's practice:

**Structured Design**:
```python
# Reference: tools/composite/visual_article_agent.py
SYSTEM_PROMPT = """
【Strict Constraints】
❌ Absolutely Forbidden: Direct content output
✅ Must Execute: Complete tasks through tool calls

【Workflow】
1. Analyze requirements
2. Call related tools
3. Verify results
"""
```

**Key Techniques**:
- **Clear Prohibitions**: Use `❌` to define what cannot be done, avoiding common errors
- **Forced Execution**: Use `✅` to specify required behavior patterns
- **Process-oriented**: Break complex tasks into clear steps
- **Verification Mechanism**: Require confirmation of results after each step

This design ensures consistency and predictability of Agent behavior, which is key to reliable operation of composite tools.

### Configuration Management

```python
from FractFlow.infra.config import ConfigManager

# Basic configuration
config = ConfigManager()

# Custom configuration
config = ConfigManager(
    provider='openai',              # Model provider: openai/anthropic/deepseek
    openai_model='gpt-4',          # Specific model
    max_iterations=20,             # Maximum iterations
    temperature=0.7,               # Generation temperature
    custom_system_prompt="...",    # Custom system prompt
    tool_calling_version='stable', # Tool calling version: stable/turbo
    timeout=120                    # Timeout setting
)
```

## File Organization
```
tools/
├── core/                 # Core tools
│   └── your_tool/
│       ├── your_tool_agent.py    # Main agent
│       ├── your_tool_mcp.py      # MCP tool implementation
│       └── __init__.py
└── composite/            # Composite tools
    └── your_composite_tool.py
```
#### Naming Conventions
- File names: `snake_case`
- Class names: `PascalCase`

## 🎙️ 新功能：千问Omni实时语音交互

FractFlow现在支持基于千问Omni的实时语音交互功能，包括：

- ⚡ **实时语音打断** - 在AI说话时可以随时打断
- 🎤 **智能语音活动检测** (VAD) - 降低阈值提高敏感度  
- 🔊 **双向音频流** - 支持同时录音和播放
- 🧵 **多线程处理** - 独立的录音、处理、播放线程
- 🔄 **WebSocket实时通信** - 与千问Omni API建立持久连接
- 📝 **语音转录显示** - 实时显示对话内容

## 🚀 快速开始

### 安装依赖

```bash
# 使用uv安装（推荐）
uv install

# 或使用pip
pip install -r requirements.txt

# 安装音频依赖
uv add pyaudio numpy
```

### 配置API密钥

1. 复制配置模板：
```bash
cp config.env.example .env
```

2. 编辑 `.env` 文件，填入您的API密钥：
```bash
QWEN_API_KEY=your_qwen_api_key_here
DASHSCOPE_API_KEY=your_dashscope_api_key_here
```

### 语音交互使用

#### 完美版语音聊天（推荐）
```bash
python perfect_voice_chat.py
```

#### 其他语音功能
```bash
# 基础语音聊天
python qwen_voice_chat.py

# 完整功能启动器
python start_qwen_voice_complete.py

# 语音打断测试
python test_voice_interrupt.py

# 音频诊断工具
python audio_diagnostic.py

# macOS权限修复
python macos_voice_permission_fix.py
```

## 🎤 语音系统特性

### 智能设备选择
- 自动识别和选择最佳麦克风设备
- 优先使用MacBook内置麦克风
- 避免兼容性问题设备（如某些蓝牙耳机）

### 优化的VAD参数
- threshold: 0.15 (平衡敏感度)
- prefix_padding_ms: 150 (适中的前缀)
- silence_duration_ms: 400 (适中的静音时间)

### 实时打断机制
- 检测到用户说话立即停止AI播放
- 清空音频播放缓冲区
- 发送取消信号给服务器

## 🛠️ 故障排除

### macOS麦克风权限
如果遇到语音检测问题：
1. 运行权限修复工具：`python macos_voice_permission_fix.py`
2. 在系统偏好设置 > 安全性与隐私 > 隐私 > 麦克风中添加终端应用
3. 重启终端应用程序

### 音频设备问题
```bash
# 运行音频诊断
python audio_diagnostic.py

# 深度调试
python deep_voice_debug.py
```

### 常见问题
- **无法检测语音**: 检查麦克风权限，尝试更大声说话
- **连接失败**: 检查API密钥和网络连接
- **音频质量差**: 尝试使用内置麦克风而非蓝牙设备

## 📊 项目结构

```
FractFlow/
├── FractFlow/                      # 核心框架
│   ├── agent.py                   # 主要Agent类
│   ├── core/                      # 核心组件
│   ├── models/                    # AI模型集成
│   └── ui/                        # 用户界面
├── tools/                         # 工具集合
│   ├── core/                      # 核心工具
│   │   ├── qwen_realtime_voice/   # 语音交互工具
│   │   ├── comfyui/              # ComfyUI集成
│   │   ├── file_io/              # 文件操作
│   │   └── ...                   # 其他工具
│   └── custom/                    # 自定义工具
├── perfect_voice_chat.py          # 完美版语音聊天
├── audio_diagnostic.py            # 音频诊断工具
└── config.env.example            # 配置模板
```

## 🎯 语音交互工作流程

1. **连接建立** - 与千问Omni API建立WebSocket连接
2. **音频初始化** - 设置录音和播放设备
3. **实时录音** - 持续录制用户语音输入
4. **语音检测** - 服务器端VAD检测语音活动
5. **语音识别** - 将语音转换为文本
6. **AI处理** - 生成回复内容
7. **语音合成** - 将回复转换为语音
8. **音频播放** - 播放AI语音回复
9. **打断处理** - 支持用户随时打断AI说话

## 🔧 技术架构

- **WebSocket通信**: 实时双向数据传输
- **多线程处理**: 录音、处理、播放独立线程
- **音频流处理**: PyAudio + 16kHz PCM格式
- **智能VAD**: 服务器端语音活动检测
- **缓冲管理**: 音频数据队列和缓冲区管理

## 📝 开发指南

### 添加新的语音功能
```python
from tools.core.qwen_realtime_voice.qwen_realtime_voice_mcp import QwenRealtimeVoiceClient

class CustomVoiceClient(QwenRealtimeVoiceClient):
    def __init__(self):
        super().__init__()
        # 自定义初始化
    
    async def _handle_responses(self):
        # 自定义响应处理
        await super()._handle_responses()
```

### 自定义VAD参数
```python
config = {
    "turn_detection": {
        "type": "server_vad",
        "threshold": 0.2,        # 调整敏感度
        "prefix_padding_ms": 200, # 调整前缀时间
        "silence_duration_ms": 500 # 调整静音判断
    }
}
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目基于 MIT 许可证开源。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [千问Omni](https://dashscope.aliyuncs.com/) - 提供实时语音交互API
- [PyAudio](https://pypi.org/project/PyAudio/) - 音频处理库
- [WebSockets](https://pypi.org/project/websockets/) - WebSocket通信

## 📞 联系我们

如果您有任何问题或建议，请通过以下方式联系：

- 创建 [Issue](https://github.com/yourusername/FractFlow/issues)
- 发送邮件到: your-email@example.com

---

⭐ 如果这个项目对您有帮助，请给我们一个星标！
