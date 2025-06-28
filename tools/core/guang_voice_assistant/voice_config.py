#!/usr/bin/env python3
"""
Voice Config for HKUST-GZ Voice Assistant
Author: FractFlow Team
Brief: Voice interaction configuration for HKUST-GZ
"""

import os

# API密钥配置
def setup_api_keys():
    """设置API密钥"""
    os.environ['QWEN_API_KEY'] = 'sk-683c8dd4b6474ac3b2e28d975d8719fe'
    os.environ['DASHSCOPE_API_KEY'] = 'sk-683c8dd4b6474ac3b2e28d975d8719fe'

# 香港科技大学广州系统指令
HKUST_GZ_SYSTEM_INSTRUCTION = """你是香港科技大学广州的智能语音助手，专门为香港科技大学广州的学生、教职员工和访客提供服务。

你的主要职责：
1. 回答关于香港科技大学广州的各种问题，包括：
   - 学校历史、发展和特色
   - 学院设置、专业介绍
   - 校园设施、生活服务
   - 入学申请、招生政策
   - 学术资源、图书馆服务
   - 校园活动、社团组织
   - 交通指南、周边环境

2. 提供实用的校园服务信息：
   - 课程安排查询
   - 校历和重要日期
   - 联系方式和办公时间
   - 校园地图和导航
   - 紧急联系信息

3. 保持友好、专业、热情的语音交流风格：
   - 用中文自然连贯地回答问题，避免断断续续
   - 语调自然平和，语速适中，表达完整
   - 使用完整的句子，避免过多的停顿和断句
   - 回复内容丰富但条理清晰
   - 语音表达要流畅连贯，就像面对面交谈一样自然

如果遇到不确定的信息，请诚实告知并建议用户联系相关部门获取准确信息。"""

# 语音配置参数
VOICE_CONFIG = {
    "voice": "Chelsie",  # 使用稳定的Chelsie女声
    "temperature": 0.6,  # 降低温度，提高语音连贯性
    "threshold": 0.08,   # 提高语音检测敏感度
    "prefix_padding_ms": 200,     # 增加前缀时间，避免截断
    "silence_duration_ms": 800,   # 用户停止说话0.8秒后AI才回答
}

# 获取完整的系统配置
def get_voice_session_config():
    """获取语音会话配置"""
    return {
        "type": "session.update",
        "session": {
            "modalities": ["text", "audio"],
            "instructions": HKUST_GZ_SYSTEM_INSTRUCTION,
            "voice": VOICE_CONFIG["voice"],
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "turn_detection": {
                "type": "server_vad",
                "threshold": VOICE_CONFIG["threshold"],
                "prefix_padding_ms": VOICE_CONFIG["prefix_padding_ms"],
                "silence_duration_ms": VOICE_CONFIG["silence_duration_ms"]
            },
            "temperature": VOICE_CONFIG["temperature"],
            "max_response_output_tokens": 2048
        }
    }