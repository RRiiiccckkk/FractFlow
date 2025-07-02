#!/usr/bin/env python3
"""
快速启动 - FractFlow 手动实时打断语音控制倪校版
基于千问Omni实时语音API + 倪校TTS音色 + 终端回车控制
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../../'))
sys.path.insert(0, project_root)

# 直接导入当前目录的模块
sys.path.insert(0, current_dir)
from 手动实时打断_倪校版_agent import main

if __name__ == "__main__":
    print("🎓 正在启动倪校版手动实时打断语音控制...")
    print("⚠️ 确保倪校TTS服务器 (http://10.120.17.57:9880) 正在运行")
    print("=" * 70)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 用户取消，程序退出")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1) 