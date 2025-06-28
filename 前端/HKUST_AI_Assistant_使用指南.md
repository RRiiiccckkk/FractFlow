# HKUST(GZ) AI Assistant 使用指南

香港科技大学广州智能助手 - 支持学术问答和语音交互两种模式

## 🎯 功能概览

### 📚 学术问答模式
- **专业定位**：学术咨询和研究支持
- **核心功能**：学术问题解答、论文写作指导、研究方法建议、课程学习支持
- **适用场景**：学生学习、教师研究、学术交流

### 🎤 语音交互模式  
- **专业定位**：智能语音助手和声音克隆
- **核心功能**：实时语音对话、倪校长声音克隆、语音识别合成、复合指令处理
- **适用场景**：语音交互、官方播报、个性化语音服务

## 🚀 快速开始

### 环境准备

```bash
# 1. 设置API密钥（选择其一）
export QWEN_API_KEY="your_qwen_api_key"
export DASHSCOPE_API_KEY="your_dashscope_api_key"

# 2. 安装依赖
uv add pyaudio websockets mcp requests

# 3. 确保TTS服务器运行（可选，用于倪校语音克隆）
# 启动TTS服务器在 localhost:7861
```

### 命令行使用

```bash
# 交互式模式选择
python hkust_ai_assistant_entry.py

# 快速启动学术模式
python -c "
import asyncio
from hkust_ai_assistant_entry import quick_start_academic_mode
asyncio.run(quick_start_academic_mode())
"

# 快速启动语音模式
python -c "
import asyncio
from hkust_ai_assistant_entry import quick_start_voice_mode
asyncio.run(quick_start_voice_mode())
"
```

### 编程接口使用

```python
import asyncio
from api_entry import start_academic_assistant, start_voice_assistant, send_message

async def main():
    # 启动学术模式
    result = await start_academic_assistant()
    if result["success"]:
        print("学术模式已启动")
        
        # 发送学术问题
        response = await send_message("什么是深度学习？")
        print(response["response"])
    
    # 切换到语音模式
    result = await start_voice_assistant()
    if result["success"]:
        print("语音模式已启动")
        
        # 发送复合语音指令
        response = await send_message("请用倪校长的声音和我进行语音交互")
        print(response["response"])

asyncio.run(main())
```

## 🔧 核心功能详解

### 1. 模式选择

#### 学术问答模式
```python
from api_entry import start_academic_assistant

result = await start_academic_assistant()
# result = {
#     "success": True,
#     "mode": "academic_qa", 
#     "message": "学术问答模式已启动",
#     "description": "专注于学术咨询、研究支持和课程指导"
# }
```

#### 语音交互模式
```python
from api_entry import start_voice_assistant

result = await start_voice_assistant()
# result = {
#     "success": True,
#     "mode": "voice_interaction",
#     "message": "语音交互模式已启动", 
#     "description": "支持语音对话、倪校长语音包和复合指令",
#     "features": ["实时语音对话", "倪校长声音克隆", ...]
# }
```

### 2. 消息处理

```python
from api_entry import send_message

# 学术问题示例
response = await send_message("如何写好一篇学术论文？")
print(response["response"])

# 语音指令示例
response = await send_message("请用倪校长的声音说欢迎词")
print(response["response"])

# 复合指令示例
response = await send_message("请用倪校长的声音和我进行语音交互")
print(response["response"])
```

### 3. 状态管理

```python
from api_entry import get_assistant_status, shutdown_assistant

# 获取状态
status = await get_assistant_status()
print(f"当前模式: {status['mode']}")
print(f"是否就绪: {status['ready']}")

# 关闭助手
result = await shutdown_assistant()
print(result["message"])
```

## 🎙️ 语音功能详解

### 单一语音指令

| 指令类型 | 示例指令 | 对应工具调用 |
|---------|---------|-------------|
| 倪校声音克隆 | "请用倪校长的声音说：欢迎词" | `clone_voice_with_ni` |
| 启动语音助手 | "启动语音助手" | `start_simple_voice_assistant` |
| 停止语音助手 | "停止语音助手" | `stop_simple_voice_assistant` |

### 复合指令处理

系统能够理解并执行复合指令，自动按逻辑顺序调用多个工具：

```python
# 复合指令示例
commands = [
    "请用倪校长的声音和我进行语音交互",
    "启动倪校语音模式", 
    "开始语音交互，用倪校长声音回复"
]

for command in commands:
    response = await send_message(command)
    # 系统会自动识别并执行：
    # 1. start_simple_voice_assistant() 
    # 2. clone_voice_with_ni("欢迎使用语音交互功能")
```

### 语音交互特性

- **实时打断**：支持用户随时打断AI回复
- **语音识别**：自动识别用户语音输入
- **语音合成**：将AI回复转换为语音播放
- **倪校声音**：特色的校长声音克隆功能

## 🌐 前端集成指南

### Web API 风格接口

```python
from api_entry import HKUSTAssistantAPI

class WebServer:
    def __init__(self):
        self.assistant_api = HKUSTAssistantAPI()
    
    async def handle_mode_selection(self, mode: str):
        """处理模式选择 POST /api/select-mode"""
        if mode == "academic":
            return await self.assistant_api.start_academic_mode()
        elif mode == "voice":
            return await self.assistant_api.start_voice_mode()
    
    async def handle_chat(self, message: str):
        """处理聊天消息 POST /api/chat"""
        return await self.assistant_api.process_message(message)
    
    async def handle_status(self):
        """获取状态 GET /api/status"""
        return await self.assistant_api.get_status()
```

### 前端调用流程

1. **初始化页面**：调用状态API获取可用模式
2. **模式选择**：用户点击按钮选择学术/语音模式
3. **实时对话**：发送用户消息，接收助手回复
4. **状态跟踪**：监控助手状态和模式信息
5. **资源清理**：页面关闭时调用关闭API

### React 集成示例

```javascript
// React Hook 示例
import { useState, useEffect } from 'react';

function useHKUSTAssistant() {
  const [mode, setMode] = useState(null);
  const [ready, setReady] = useState(false);
  
  const selectMode = async (newMode) => {
    const response = await fetch('/api/select-mode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: newMode })
    });
    const result = await response.json();
    
    if (result.status === 'success') {
      setMode(newMode);
      setReady(true);
    }
  };
  
  const sendMessage = async (message) => {
    const response = await fetch('/api/chat', {
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    return await response.json();
  };
  
  return { mode, ready, selectMode, sendMessage };
}

// 组件使用
function HKUSTAssistant() {
  const { mode, ready, selectMode, sendMessage } = useHKUSTAssistant();
  
  return (
    <div>
      <h1>HKUST(GZ) AI Assistant</h1>
      
      {!ready && (
        <div>
          <button onClick={() => selectMode('academic')}>
            📚 学术问答
          </button>
          <button onClick={() => selectMode('voice')}>
            🎤 语音交互
          </button>
        </div>
      )}
      
      {ready && (
        <ChatInterface sendMessage={sendMessage} mode={mode} />
      )}
    </div>
  );
}
```

## 🔍 故障排除

### 常见问题

1. **API密钥错误**
   ```bash
   # 检查环境变量
   echo $QWEN_API_KEY
   echo $DASHSCOPE_API_KEY
   
   # 重新设置
   export QWEN_API_KEY="your_valid_key"
   ```

2. **倪校语音无法使用**
   ```bash
   # 检查TTS服务器
   curl http://localhost:7861/health
   
   # 如果服务器未运行，启动TTS服务器
   # 参考倪校语音克隆服务器文档
   ```

3. **MCP工具调用失败**
   ```bash
   # 检查工具路径
   ls tools/core/guang_voice_assistant/
   
   # 重新启动助手
   python -c "
   import asyncio
   from api_entry import shutdown_assistant, start_voice_assistant
   asyncio.run(shutdown_assistant())
   asyncio.run(start_voice_assistant())
   "
   ```

4. **音频设备问题**
   ```bash
   # 检查pyaudio安装
   python -c "import pyaudio; print('PyAudio OK')"
   
   # 重新安装音频依赖
   uv add pyaudio
   ```

### 调试模式

```python
import logging
from api_entry import start_voice_assistant, send_message

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 测试功能
result = await start_voice_assistant()
print(f"启动结果: {result}")

response = await send_message("测试消息")
print(f"回复结果: {response}")
```

## 📋 API 参考

### 主要函数

| 函数名 | 参数 | 返回值 | 说明 |
|-------|-----|--------|------|
| `start_academic_assistant()` | 无 | `Dict[str, Any]` | 启动学术模式 |
| `start_voice_assistant()` | 无 | `Dict[str, Any]` | 启动语音模式 |
| `send_message(message)` | `str` | `Dict[str, Any]` | 发送消息 |
| `get_assistant_status()` | 无 | `Dict[str, Any]` | 获取状态 |
| `shutdown_assistant()` | 无 | `Dict[str, Any]` | 关闭助手 |

### 返回值格式

```python
# 成功响应
{
    "success": True,
    "response": "助手回复内容",
    "mode": "academic_qa" | "voice_interaction"
}

# 错误响应  
{
    "success": False,
    "error": "错误信息",
    "message": "用户友好的错误说明"
}

# 状态响应
{
    "initialized": True,
    "mode": "voice_interaction", 
    "available_modes": ["academic_qa", "voice_interaction"],
    "ready": True
}
```

## 🎉 总结

HKUST(GZ) AI Assistant 提供了完整的双模式智能助手解决方案：

✅ **学术问答模式** - 专业的学术支持和研究指导  
✅ **语音交互模式** - 先进的语音交互和声音克隆  
✅ **复合指令处理** - 智能理解复杂的组合需求  
✅ **前端友好接口** - 标准化的API便于集成  
✅ **完整的错误处理** - 健壮的异常管理机制  
✅ **实时状态管理** - 全程状态跟踪和控制  

通过本指南，您可以轻松集成HKUST AI Assistant到您的应用中，为用户提供专业的学术支持和创新的语音交互体验。 