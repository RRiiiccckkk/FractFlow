# HKUST(GZ) AI Assistant 前端开发包

本文件夹包含HKUST(GZ) AI Assistant的前端开发相关文件，支持学术问答和语音交互两种模式。

## 📁 文件结构

```
前端/
├── README.md                           # 本文件 - 前端开发指南
├── hkust_ai_assistant_entry.py         # 主入口文件 - 交互式模式选择
├── api_entry.py                        # API接口文件 - 前端调用接口
└── HKUST_AI_Assistant_使用指南.md       # 详细使用指南
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 设置API密钥（必须）
export QWEN_API_KEY="your_qwen_api_key"
# 或者
export DASHSCOPE_API_KEY="your_dashscope_api_key"

# 安装依赖
cd ..  # 返回项目根目录
uv add pyaudio websockets mcp requests
```

### 2. 运行测试

```bash
# 交互式模式（命令行UI）
python 前端/hkust_ai_assistant_entry.py

# API模式测试
python 前端/api_entry.py
```

## 🎯 两种模式

### 📚 学术问答模式
- **功能**：学术问题解答、论文写作指导、研究方法建议
- **适用**：学生学习、教师研究、学术咨询
- **特点**：专业严谨、引用可靠学术资源

### 🎤 语音交互模式  
- **功能**：实时语音对话、倪校长声音克隆、复合指令处理
- **适用**：语音交互、官方播报、个性化语音服务
- **特点**：支持复合指令，如"请用倪校长的声音和我进行语音交互"

## 🔧 前端集成接口

### 基础API调用

```python
from api_entry import (
    start_academic_assistant,    # 启动学术模式
    start_voice_assistant,       # 启动语音模式 
    send_message,               # 发送消息
    get_assistant_status,       # 获取状态
    shutdown_assistant          # 关闭助手
)

# 使用示例
result = await start_voice_assistant()
if result["success"]:
    response = await send_message("请用倪校长的声音说欢迎词")
    print(response["response"])
```

### Web API风格接口

```python
from api_entry import HKUSTAssistantAPI

api = HKUSTAssistantAPI()

# 模式选择
await api.start_academic_mode()
await api.start_voice_mode()

# 消息处理
result = await api.process_message("用户消息")

# 状态管理
status = await api.get_status()
await api.shutdown()
```

## 🌐 Web前端集成

### React Hook示例

```javascript
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
```

### Vue.js 组合式API示例

```javascript
import { ref, reactive } from 'vue';

export function useHKUSTAssistant() {
  const mode = ref(null);
  const ready = ref(false);
  const status = reactive({
    initialized: false,
    loading: false
  });
  
  const selectMode = async (newMode) => {
    status.loading = true;
    try {
      const response = await fetch('/api/select-mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: newMode })
      });
      const result = await response.json();
      
      if (result.status === 'success') {
        mode.value = newMode;
        ready.value = true;
        status.initialized = true;
      }
    } finally {
      status.loading = false;
    }
  };
  
  return { mode, ready, status, selectMode };
}
```

## ⚠️ 当前已知问题

### 🚨 倪校长语音包无法正常运行

**问题描述**：
- 倪校长声音克隆功能目前无法正常工作
- 原因：TTS服务器未启动或连接失败
- 影响：`clone_voice_with_ni` 工具调用失败

**临时解决方案**：
- 系统会自动降级到文字回复
- 保持其他语音功能（录音、识别、合成）正常工作
- 复合指令仍能正确识别和部分执行

**技术细节**：
```bash
# 检查TTS服务器状态
curl http://localhost:7861/health

# 预期的TTS服务器应该运行在：
# - 地址：localhost:7861
# - 端点：/tts  
# - 方法：POST
# - 格式：JSON {"text": "内容", "batch_size": "1"}
```

**修复方向**：
1. 确保TTS服务器正确启动并运行在端口7861
2. 验证API接口格式和参数
3. 检查网络连接和防火墙设置
4. 确认倪校语音模型文件完整性

## 🔄 开发状态

### ✅ 已完成功能
- ✅ 双模式架构（学术问答 + 语音交互）
- ✅ 复合指令理解和处理
- ✅ 前端友好的API接口
- ✅ 完整的状态管理
- ✅ 错误处理和降级机制
- ✅ 模式无缝切换
- ✅ Web API标准格式

### 🚧 待完善功能
- 🚧 倪校长语音包修复
- 🚧 前端UI界面
- 🚧 实时语音流传输
- 🚧 多用户会话管理
- 🚧 语音质量优化

### 🎯 开发优先级

1. **高优先级**：修复倪校长语音包功能
2. **中优先级**：开发Web前端界面
3. **低优先级**：性能优化和高级功能

## 📋 开发建议

### 前端架构建议
- 使用React/Vue.js + TypeScript
- 采用WebSocket进行实时通信
- 实现渐进式Web应用(PWA)
- 支持移动端响应式设计

### API设计建议
- 遵循RESTful API规范
- 实现WebSocket用于实时语音流
- 添加身份验证和会话管理
- 提供完整的错误码和消息

### 部署建议  
- 使用Docker容器化部署
- 配置负载均衡和高可用
- 实现自动扩缩容
- 监控和日志系统

## 📞 技术支持

如有技术问题，请参考：
1. `HKUST_AI_Assistant_使用指南.md` - 详细技术文档
2. 项目根目录的相关工具文档
3. GitHub Issues进行问题反馈

---

🎓 **HKUST(GZ) AI Assistant** - 让智能助手服务于学术创新 