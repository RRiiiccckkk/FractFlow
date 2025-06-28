# 广广语音助手 (Guang Voice Assistant)

港科大广州智能语音助手，集成倪校长声音克隆和实时语音对话功能。

## 🎯 核心功能

### 🎙️ 倪校长语音包
- **功能**：实现倪校长（香港科技大学广州校长）的声音克隆
- **使用场景**：欢迎词、官方讲话、教学内容等
- **调用方式**：通过自然语言指令触发

### 🎤 实时语音对话 
- **功能**：支持语音识别、AI对话、语音合成的完整语音交互
- **特色**：千问Omni实时打断功能，自然流畅的对话体验
- **支持**：实时录音、智能响应、音频播放

## 🚀 使用方法

### 通过FractFlow Agent使用

```python
from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager

# 创建包含倪校语音包认知的配置
config = ConfigManager(
    provider='qwen',
    custom_system_prompt="""你是一个智能助手，具备语音合成和对话功能。

🎙️ **倪校长语音包功能**：
当用户要求"用倪校长的声音说..."、"请以倪校长的声音讲出..."、"让倪校长说..."或类似请求时，
你需要调用 clone_voice_with_ni 工具来实现倪校长的声音克隆。

请根据用户的具体需求，智能选择合适的工具来完成任务。"""
)

# 创建Agent并注册工具
agent = Agent(config=config)
agent.add_tool(
    tool_path="tools/core/guang_voice_assistant/guang_voice_assistant_mcp.py",
    tool_name="guang_voice_assistant"
)

# 启动Agent
await agent.initialize()

# 使用示例
response = await agent.process_query("请用倪校长的声音说：欢迎来到港科大广州！")
```

### 自然语言指令示例

#### 🎙️ 倪校长语音克隆
- "请用倪校长的声音说欢迎词"
- "让倪校长讲一段开学致辞"  
- "用倪校长的声音说：大家好，欢迎来到香港科技大学广州"

#### 🎤 语音对话控制
- "启动语音对话助手"
- "开始语音交互"
- "停止语音助手"

## 🛠️ 技术架构

### MCP工具函数

1. **`clone_voice_with_ni(text)`**
   - 使用倪校长语音包进行文本转语音
   - 需要TTS服务器运行在 `localhost:7861`

2. **`start_simple_voice_assistant()`**
   - 启动实时语音对话助手
   - 支持千问Omni实时语音API

3. **`stop_simple_voice_assistant()`**
   - 停止语音助手并清理资源

### 依赖要求

```bash
# 音频处理
uv add pyaudio

# 异步WebSocket
uv add websockets

# MCP框架
uv add mcp

# HTTP请求
uv add requests
```

### 外部服务依赖

1. **倪校TTS服务器**：`http://localhost:7861/tts`
2. **千问Omni API**：需要 `QWEN_API_KEY` 环境变量

## 🎯 设计理念

遵循FractFlow的核心设计理念：

- **自然语言优先**：通过自然语言指令直接调用功能
- **分形智能架构**：工具可嵌套调用，支持复杂对话场景
- **简洁胜于复杂**：避免复杂配置，让LLM自主理解用户意图
- **工具描述即接口**：清晰的工具描述让上层Agent准确调用

## 🔍 故障排除

### 倪校语音克隆无法工作
1. 检查TTS服务器是否运行：`curl http://localhost:7861/health`
2. 确保服务器支持POST请求和JSON格式
3. 检查batch_size参数格式（应为字符串）

### 语音对话连接失败
1. 验证千问API密钥：`echo $QWEN_API_KEY`
2. 检查网络连接到阿里云服务
3. 确认pyaudio音频权限

### MCP通信错误
1. 检查是否有print语句干扰JSON-RPC
2. 确保所有异常都被正确捕获
3. 验证工具函数返回格式

## 📝 更新日志

- **v1.0**: 初始版本，集成基础语音功能
- **v1.1**: 添加倪校语音包支持
- **v1.2**: 优化系统提示，支持自然语言调用
- **v1.3**: 修复MCP通信问题，移除干扰性输出

## 🤝 贡献

欢迎贡献代码和建议！请遵循FractFlow的代码规范和设计理念。 