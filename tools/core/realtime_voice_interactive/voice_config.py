#!/usr/bin/env python3
"""
语音交互配置文件 - 双音色模式
香港科技大学广州智能语音助手
支持默认音色和倪校音色两种模式
"""

import os

# API密钥配置
def setup_api_keys():
    """设置API密钥"""
    os.environ['QWEN_API_KEY'] = 'sk-683c8dd4b6474ac3b2e28d975d8719fe'
    os.environ['DASHSCOPE_API_KEY'] = 'sk-683c8dd4b6474ac3b2e28d975d8719fe'

# 默认音色系统指令
DEFAULT_SYSTEM_INSTRUCTION = """你是香港科技大学广州的智能语音助手，专门为香港科技大学广州的学生、教职员工和访客提供服务。

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

# 倪校音色系统指令
NI_SYSTEM_INSTRUCTION = """你是香港科技大学广州的校长倪哥的语音助手，使用倪校长的亲切风格为大家服务。

你的身份特点：
1. 以倪校长的身份和语调与用户交流
2. 保持校长的亲和力和专业素养
3. 用温暖、关怀的语调回答问题

你的主要职责：
1. 代表倪校长回答关于香港科技大学广州的问题：
   - 学校发展愿景和教育理念
   - 学院建设和学科发展
   - 校园文化和学生生活
   - 国际合作和产学研结合
   - 人才培养和就业前景

2. 提供校长视角的建议：
   - 学习规划和职业发展
   - 校园生活指导
   - 学术研究方向
   - 创新创业机会

3. 保持倪校长特有的交流风格：
   - 亲切温暖，充满关怀
   - 专业权威，富有远见
   - 用中文自然流畅地表达
   - 语调亲和友善，像长辈关怀后辈

欢迎大家来到香港科技大学广州，我是倪校长，很高兴为大家服务！"""

# 基础语音配置参数
BASE_VOICE_CONFIG = {
    "voice": "Chelsie",  # 使用稳定的Chelsie女声
    "temperature": 0.6,  # 降低温度，提高语音连贯性
    "threshold": 0.08,   # 提高语音检测敏感度
    "prefix_padding_ms": 200,     # 增加前缀时间，避免截断
    "silence_duration_ms": 800,   # 用户停止说话0.8秒后AI才回答
}

# 默认音色配置
DEFAULT_VOICE_CONFIG = {
    **BASE_VOICE_CONFIG,
    "instructions": DEFAULT_SYSTEM_INSTRUCTION,
}

# 倪校音色配置（优化响应速度）
NI_VOICE_CONFIG = {
    **BASE_VOICE_CONFIG,
    "instructions": NI_SYSTEM_INSTRUCTION,
    "temperature": 0.4,  # 降低温度提高响应速度
}

# 获取完整的系统配置
def get_voice_session_config(voice_mode="default"):
    """获取语音会话配置
    
    Args:
        voice_mode (str): 音色模式，"default" 或 "ni"
    
    Returns:
        dict: 会话配置字典
    """
    config = DEFAULT_VOICE_CONFIG if voice_mode == "default" else NI_VOICE_CONFIG
    
    return {
        "modalities": ["text", "audio"],
        "instructions": config["instructions"],
        "voice": config["voice"],
        "input_audio_format": "pcm16",
        "output_audio_format": "pcm16",
        "turn_detection": {
            "type": "server_vad",
            "threshold": config["threshold"],
            "prefix_padding_ms": config["prefix_padding_ms"],
            "silence_duration_ms": config["silence_duration_ms"]
        },
        "temperature": config["temperature"],
        "max_response_output_tokens": 1024 if voice_mode == "ni" else 2048  # 倪校模式限制回答长度提高速度
    } 