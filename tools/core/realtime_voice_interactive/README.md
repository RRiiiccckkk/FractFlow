# Realtime Voice Interactive Assistant

## 📋 概述

实时语音交互助手是FractFlow分形智能架构的核心语音模块，支持双音色模式(including nixiao)，提供极速打断和实时语音对话功能。

## 🎯 核心特性

### ⚡ 极速打断系统
- **100-300ms响应时间**：业界领先的打断响应速度
- **多级打断机制**：立即音频停止→队列清理→状态重置
- **智能连续性验证**：避免误触发，2/3采样超阈值才触发

### 🔊 智能音量检测
- **动态阈值调整**：自动适应环境噪音
- **背景噪音校准**：前50个采样自动建立基线
- **5ms检测频率**：比标准方案快2倍

### 🚀 流式TTS播放（倪校版）
- **边生成边播放**：每句话生成后立即播放
- **首句响应<2秒**：大幅提升响应速度
- **精确打断控制**：支持句子级别的精确打断

### 🎓 倪校声音克隆技术
- **GPT-SoVITS技术**：高质量声音克隆
- **实时合成**：支持任意文本的倪校声音合成
- **256字节分块播放**：可中断音频播放

## 🏗️ 架构设计

| 组件 | 默认音色版 | 倪校音色版 |
|------|-----------|-----------|
| MCP工具名 | realtime_voice_interactive | ni_realtime_voice_interactive |
| 核心类名 | RealtimeVoiceInteractiveAgent | RealtimeVoiceInteractiveAgent |
| 音频输出 | 系统Chelsie音色 | 倪校声音克隆 |
| TTS模式 | 千问实时音频 | 流式分句播放 |
| 打断能力 | 标准多级打断 | 增强音频中断 |

## 🚀 快速开始

### 直接运行模式

```bash
# 默认音色版本
python realtime_voice_interactive.py default  # 默认音色
python realtime_voice_interactive.py ni       # 倪校音色
```

### Agent模式

```bash
# 默认音色Agent
python realtime_voice_interactive_agent.py --voice-interactive

# 倪校音色Agent
python ni_realtime_voice_interactive_agent.py --voice-interactive
```

### MCP集成模式

```python
# 注册到FractFlow编排器
tools_config = {
    ("tools/core/realtime_voice_interactive/realtime_voice_interactive_mcp.py", "realtime_voice_interactive"),
    ("tools/core/realtime_voice_interactive/ni_realtime_voice_interactive_mcp.py", "ni_realtime_voice_interactive")
}

agent.register_tools(tools_config)
```

## 🔧 API参考

### 默认音色版 MCP工具

```python
from tools.core.realtime_voice_interactive.realtime_voice_interactive_agent import RealtimeVoiceInteractiveAgent

# 启动语音交互
await start_realtime_voice_interactive()

# 停止语音交互
await stop_realtime_voice_interactive()

# 查询状态
status = get_voice_interactive_status()
```

### 倪校音色版 MCP工具

```python
from tools.core.realtime_voice_interactive.ni_realtime_voice_interactive_agent import NiRealtimeVoiceInteractiveAgent

# 启动倪校语音交互
await start_ni_realtime_voice_interactive()

# 停止倪校语音交互
await stop_ni_realtime_voice_interactive()

# 倪校声音克隆
result = clone_voice_with_ni("大家好，我是倪校长！")

# 查询倪校助手状态
status = get_ni_voice_interactive_status()
```

## 📁 目录结构

```
tools/core/realtime_voice_interactive/
├── __init__.py                           # 模块初始化
├── realtime_voice_interactive.py         # 核心实现类
├── voice_config.py                      # 双模式配置
├── realtime_voice_interactive_mcp.py     # 默认音色MCP
├── realtime_voice_interactive_agent.py   # 默认音色Agent
├── ni_realtime_voice_interactive_mcp.py  # 倪校音色MCP
├── ni_realtime_voice_interactive_agent.py # 倪校音色Agent
├── ni_voice_clone_client/               # 倪校TTS客户端
│   ├── __init__.py
│   └── main.py                          # 支持中断的TTS客户端
└── README.md                           # 本文档
```

## ⚙️ 配置说明

### 环境变量

```bash
# 千问API密钥（必需）
export QWEN_API_KEY="your_qwen_api_key"
# 或
export DASHSCOPE_API_KEY="your_dashscope_api_key"

# 倪校TTS服务器地址（倪校版使用）
export NI_TTS_SERVER="http://10.120.17.57:9880"
```

### 音频设备配置

系统会自动检测和配置音频设备：
- **输入设备**：自动选择默认麦克风
- **输出设备**：自动选择默认扬声器
- **采样率**：16000Hz
- **声道数**：单声道

## 🧪 测试与验证

运行完整测试套件：

```bash
python test_voice_assistant.py
```

测试覆盖项目：
- ✅ 模块导入测试
- ✅ 中断机制测试（<10ms响应）
- ✅ 音量检测参数验证
- ✅ 多级打断机制验证
- ✅ 性能响应测试
- ✅ MCP服务器功能测试

## 🔍 故障排除

### 常见问题

1. **麦克风权限问题**
   ```bash
   # macOS: 确保终端有麦克风权限
   系统偏好设置 → 安全性与隐私 → 隐私 → 麦克风
   ```

2. **倪校TTS服务连接失败**
   ```bash
   # 检查服务器连接
   curl -X POST http://10.120.17.57:9880/tts \
     -H "Content-Type: application/json" \
     -d '{"text":"测试","text_lang":"zh"}'
   ```

3. **音频设备检测失败**
   ```bash
   # 安装PyAudio依赖
   pip install pyaudio
   ```

### 调试模式

启用详细日志：

```bash
export FRACTFLOW_DEBUG=1
python realtime_voice_interactive.py ni
```

## 🤝 贡献指南

### 添加新语音模式

1. 在`voice_config.py`中添加新模式配置
2. 修改`realtime_voice_interactive.py`支持新模式
3. 创建对应的MCP服务器文件
4. 添加Agent入口文件
5. 更新README文档

### 性能优化建议

- 调整`volume_threshold`以适应不同环境
- 优化`sentence_buffer_size`以平衡响应速度和准确性
- 根据网络条件调整TTS超时参数

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

- 感谢千问团队提供的Omni实时语音API
- 感谢GPT-SoVITS团队的声音克隆技术
- 感谢FractFlow团队的分形智能架构支持 