#!/usr/bin/env python3
"""
第三方图像生成API测试脚本

这个脚本用于测试第三方图像生成API的连接和功能。
"""

import os
import sys
import asyncio
from datetime import datetime

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 导入自定义的第三方图像智能体
from tools.custom.third_party_image_agent import ThirdPartyImageAgent

async def test_third_party_image_api():
    """测试第三方图像生成API"""
    
    print("🚀 开始测试第三方图像生成API")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # 创建智能体实例
        print("📦 正在创建第三方图像生成智能体...")
        agent = await ThirdPartyImageAgent.create_agent()
        
        # 测试查询列表
        test_queries = [
            "生成一张美丽的日落风景图，保存为sunset_test.png",
            "创建一个可爱的小猫插画，卡通风格",
            "制作一张现代科幻城市的概念图",
        ]
        
        print("🔍 开始执行测试查询...")
        print("-" * 40)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 测试 {i}/{len(test_queries)}: {query}")
            print("⏳ 处理中...")
            
            try:
                result = await agent.process_query(query)
                print(f"✅ 测试 {i} 完成")
                print(f"📄 结果: {result[:200]}..." if len(result) > 200 else f"📄 结果: {result}")
                
            except Exception as e:
                print(f"❌ 测试 {i} 失败: {str(e)}")
            
            print("-" * 40)
        
        # 关闭智能体
        print("\n🔚 正在关闭智能体...")
        await agent.shutdown()
        print("✅ 测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        print("💡 请检查以下几点：")
        print("   1. API密钥是否正确")
        print("   2. 网络连接是否正常")
        print("   3. API服务是否可用")
        print("   4. 配置文件是否正确")

def test_configuration():
    """测试配置信息"""
    print("🔧 检查配置信息")
    print("=" * 40)
    
    # 检查环境变量
    env_vars = [
        'THIRD_PARTY_IMAGE_API_KEY',
        'THIRD_PARTY_IMAGE_BASE_URL', 
        'THIRD_PARTY_IMAGE_MODEL',
        'OPENAI_API_KEY',
        'OPENAI_BASE_URL'
    ]
    
    for var in env_vars:
        value = os.getenv(var, "未设置")
        if value != "未设置":
            # 隐藏API密钥的大部分内容
            if 'API_KEY' in var:
                display_value = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "*" * len(value)
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: {value}")
    
    print("\n💡 如果配置未设置，请:")
    print("   1. 复制 third_party_config.env 的内容到 .env 文件")
    print("   2. 或者在系统中设置环境变量")
    print("   3. 然后重新运行测试")

if __name__ == "__main__":
    print("🖼️  FractFlow 第三方图像生成API测试工具")
    print("=" * 60)
    
    # 检查配置
    test_configuration()
    
    print("\n" + "=" * 60)
    
    # 询问是否继续测试
    if input("📋 是否继续进行API功能测试？(y/N): ").lower().strip() in ['y', 'yes', '是']:
        asyncio.run(test_third_party_image_api())
    else:
        print("📋 测试已取消")
        
    print("\n🎯 如需使用第三方图像生成智能体，运行:")
    print("   python tools/custom/third_party_image_agent.py --interactive")
    print("   python tools/custom/third_party_image_agent.py --query \"您的图像生成需求\"") 