# HKUST(GZ) AI Assistant 前端开发包 - 更新日志

## 🚀 v1.0.0 (2024-12-27) - 初始发布

### ✨ 新功能

#### 🎯 双模式架构
- **📚 学术问答模式**：专业的学术咨询和研究支持
- **🎤 语音交互模式**：智能语音助手和声音克隆功能

#### 🔧 核心功能
- **复合指令处理**：智能理解"请用倪校长的声音和我进行语音交互"等复合指令
- **增强系统提示**：orchestrator能够理解并执行复杂的语音指令
- **工具自动调用**：根据用户意图自动选择和调用相应的MCP工具
- **状态管理**：完整的助手状态跟踪和模式切换
- **错误处理**：健壮的异常处理和自动降级机制

#### 🌐 前端集成
- **标准化API**：RESTful风格的API接口设计
- **React Hook**：提供现成的React集成示例
- **Vue.js组合式API**：支持Vue.js前端框架
- **WebSocket支持**：为实时通信预留接口
- **TypeScript友好**：完整的类型定义支持

### 📁 文件结构

```
前端/
├── README.md                           # 前端开发指南
├── CHANGELOG.md                        # 更新日志（本文件）
├── hkust_ai_assistant_entry.py         # 交互式入口
├── api_entry.py                        # API接口模块
└── HKUST_AI_Assistant_使用指南.md       # 详细技术文档
```

### 🔧 技术栈

- **后端框架**：FractFlow + MCP工具系统
- **AI模型**：千问Qwen系列模型
- **语音处理**：PyAudio + WebSocket
- **异步编程**：asyncio + aiohttp
- **配置管理**：环境变量 + JSON配置

### 🎯 API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `start_academic_assistant()` | async | 启动学术问答模式 |
| `start_voice_assistant()` | async | 启动语音交互模式 |
| `send_message(message)` | async | 发送用户消息 |
| `get_assistant_status()` | async | 获取助手状态 |
| `shutdown_assistant()` | async | 关闭助手系统 |

### 🧪 测试覆盖

- ✅ 模式选择和切换
- ✅ 复合指令理解
- ✅ 工具自动调用
- ✅ 错误处理机制
- ✅ 状态管理功能
- ✅ API接口完整性

### 📋 使用示例

#### Python API调用
```python
import asyncio
from api_entry import start_voice_assistant, send_message

async def main():
    # 启动语音模式
    result = await start_voice_assistant()
    print(f"启动结果: {result['message']}")
    
    # 发送复合指令
    response = await send_message("请用倪校长的声音和我进行语音交互")
    print(f"回复: {response['response']}")

asyncio.run(main())
```

#### Web API调用
```javascript
// 启动语音模式
const startResult = await fetch('/api/select-mode', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode: 'voice' })
});

// 发送消息
const chatResult = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: '请用倪校长的声音说欢迎词' })
});
```

## ⚠️ 已知问题

### 🚨 倪校长语音包无法正常运行

**影响版本**：v1.0.0  
**严重程度**：中等  
**问题描述**：
- 倪校长声音克隆功能目前无法正常工作
- 原因：TTS服务器未启动或连接失败（端口7861）
- 错误信息：`curl: (7) Failed to connect to localhost port 7861`

**临时解决方案**：
- ✅ 系统自动降级到文字回复
- ✅ 保持语音识别和合成功能正常
- ✅ 复合指令仍能正确识别和部分执行
- ✅ 所有其他功能正常工作

**修复进度**：
- 🔍 正在调查TTS服务器连接问题
- 📋 计划在v1.1.0中修复

### 🐛 其他已知问题

1. **MCP清理警告**：关闭时偶现TaskGroup异常（不影响功能）
2. **中文路径编码**：Git显示中文文件名为编码格式（不影响功能）

## 🔮 未来规划

### 📅 v1.1.0 - 声音修复版（计划中）
- 🎯 修复倪校长语音包连接问题
- 🔧 优化TTS服务器集成
- 📈 提升语音质量和响应速度

### 📅 v1.2.0 - UI增强版（计划中）
- 🎨 Web前端界面开发
- 📱 移动端响应式设计
- 🎪 交互体验优化

### 📅 v2.0.0 - 企业版（长期规划）
- 👥 多用户会话管理
- 🔐 身份验证和权限控制
- 📊 使用统计和分析
- ☁️ 云端部署支持

## 📞 技术支持

### 🛠️ 问题报告
- **GitHub Issues**：[FractFlow Repository](https://github.com/RRiiiccckkk/FractFlow/issues)
- **文档参考**：`HKUST_AI_Assistant_使用指南.md`

### 🤝 贡献指南
1. Fork仓库并创建功能分支
2. 遵循代码规范和测试要求
3. 提交Pull Request with详细说明
4. 等待代码审查和合并

### 📧 联系方式
- **项目维护者**：FractFlow Team
- **技术支持**：通过GitHub Issues

---

🎓 **HKUST(GZ) AI Assistant** - 让智能助手服务于学术创新  
📅 **最后更新**：2024-12-27  
🔖 **当前版本**：v1.0.0 