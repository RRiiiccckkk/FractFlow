# 🎤 香港科技大学广州智能语音助手

HKUST-GZ Intelligent Voice Assistant - 极简版，集成网络搜索功能

## ✨ 核心功能

### 🎙️ 实时语音交互
- **自然对话**: 支持连续的语音对话，AI响应自然流畅
- **实时音频流**: 基于千问Omni的实时语音技术
- **智能打断**: 开始说话时自动打断AI回答
- **音量检测**: 自动检测说话音量，智能启动录音

### 🌐 **网络搜索功能** ⭐ NEW
- **智能触发**: AI遇到无法回答的问题时自动启动搜索
- **搜索引擎**: 支持DuckDuckGo、Google、百度搜索
- **内容提取**: 自动浏览搜索结果并提取关键信息
- **PDF支持**: 自动识别和解析PDF文件内容
- **回答增强**: 基于搜索结果重新生成详细回答

### 🤖 AI增强指令
AI助手会在以下情况主动使用网络搜索：
- 遇到最新信息查询（如"今天天气"、"最新新闻"）
- 专业知识问题（如技术文档、学术资料）
- 不确定的信息（AI会说"让我搜索确认一下"）
- 实时数据查询（股价、汇率、实时状态等）

## 🔧 安装与配置

### 环境要求
- Python 3.8+
- 有效的千问API密钥
- 稳定的网络连接（用于搜索功能）

### 快速开始
```bash
# 1. 配置API密钥
cp voice_config.py.example voice_config.py
# 编辑voice_config.py，添加你的千问API密钥

# 2. 安装依赖
pip install pyaudio numpy duckduckgo-search beautifulsoup4 httpx

# 3. 运行语音助手
python simple_voice_assistant.py
```

## 🎯 使用方法

### 基础对话
- 直接说话提问
- 等待AI音频和文字回答
- 说话时会自动打断AI

### 网络搜索场景
```
👤 用户: "今天北京的天气怎么样？"
🤖 AI: "让我为您搜索最新的天气信息。我需要搜索。"
🔍 [系统自动搜索天气信息]
💬 AI: "根据搜索结果，北京今天晴天，气温15-25度..."

👤 用户: "Python的装饰器是什么？"
🤖 AI: "这个问题比较专业，让我搜索详细资料。我需要搜索。"
🔍 [系统自动搜索技术资料]
💬 AI: "根据搜索结果，Python装饰器是一种设计模式..."
```

## 🔍 搜索功能详解

### 触发机制
AI会在以下情况自动触发搜索：
- 说出"我需要搜索"等关键词
- 遇到时效性信息查询
- 专业知识超出训练范围

### 支持的搜索引擎
- **DuckDuckGo** (默认): 隐私友好，无地域限制
- **Google**: 结果丰富，需要良好网络环境
- **百度**: 中文内容丰富，适合国内网络环境

### 搜索优化
- 自动提取关键信息
- 内容长度智能控制
- 结果质量过滤
- PDF文档内容解析

## 📊 性能特性

- **响应速度**: 平均延迟 < 2秒
- **搜索效率**: 3-5个结果，1个详细浏览
- **内容限制**: 单次搜索最大3000字符
- **错误处理**: 完善的异常处理和重试机制

## 🛠️ 故障排除

### 语音问题
```bash
# 检查麦克风权限
# macOS: 系统偏好设置 > 安全性与隐私 > 麦克风
# 重启应用程序
```

### 搜索问题
```bash
# 检查网络连接
ping google.com

# 检查依赖安装
pip list | grep -E "(duckduckgo|beautifulsoup4|httpx)"

# 使用百度搜索（国内网络）
# 修改simple_voice_assistant.py中的search_engine="baidu"
```

### API连接问题
```bash
# 检查API密钥配置
grep -i "dashscope\|qwen" voice_config.py

# 检查网络连接
curl -I https://dashscope.aliyuncs.com
```

## 🎮 交互示例

### 日常询问 + 自动搜索
```
👤 "今天有什么重要新闻吗？"
🤖 "让我为您搜索今天的重要新闻。我需要搜索。"
🔍 [搜索最新新闻]
💬 "根据搜索结果，今天的重要新闻包括..."

👤 "ChatGPT最新版本有什么功能？"  
🤖 "这是比较新的信息，让我搜索最新资料。我需要搜索。"
🔍 [搜索技术更新]
💬 "根据搜索结果，ChatGPT最新版本..."
```

### 技术问题 + 深度搜索
```
👤 "如何在Python中实现多线程？"
🤖 "这个问题比较专业，让我搜索详细的技术文档。我需要搜索。"
🔍 [搜索编程教程]
💬 "根据搜索结果，Python多线程可以通过threading模块..."
```

## 🔧 开发说明

### 架构设计
```
simple_voice_assistant.py
├── 语音交互核心 (QwenRealtimeVoiceClient)
├── 搜索功能集成 (WebSearch)
├── 触发词检测 (TriggerDetection)
├── 回答增强 (ResponseEnhancement)
└── 错误处理 (ErrorHandling)
```

### 自定义搜索引擎
```python
# 在perform_web_search方法中修改
search_result = await web_search_and_browse(
    query=question,
    search_engine="google",  # 改为 "baidu" 或 "google"
    num_results=5,          # 搜索结果数量
    max_browse=2,           # 浏览结果数量
    max_length=5000         # 内容长度限制
)
```

### 添加自定义触发词
```python
# 在__init__方法中修改search_triggers列表
self.search_triggers = [
    "我做不到", "我不知道", "我无法", 
    "我需要搜索",  # 标准触发词
    "查一查",      # 添加自定义触发词
    "搜索一下"     # 添加自定义触发词
]
```

## 📈 版本历史

- **v2.0.0** - 集成网络搜索功能
  - AI智能搜索触发
  - 多搜索引擎支持  
  - PDF文档解析
  - 回答质量增强

- **v1.0.0** - 基础语音交互
  - 实时语音对话
  - 智能打断功能
  - 极简化设计

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

MIT License - 详见LICENSE文件 