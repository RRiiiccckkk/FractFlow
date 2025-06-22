#!/usr/bin/env python3
"""
直接测试第三方图像生成API
"""

import os
import json
import asyncio
import aiohttp

async def test_liaobots_api():
    """直接测试LiaoBots API"""
    
    # 配置
    api_key = "doQoKm7g3U4Bw"
    base_url = "https://ai.liaobots.work/v1"
    model = "imagen-4.0-ultra-generate-exp-05-20"
    
    print("🚀 开始测试 LiaoBots 图像生成API")
    print(f"🔑 API密钥: {api_key[:10]}...")
    print(f"🌐 基础URL: {base_url}")
    print(f"🤖 模型: {model}")
    print("=" * 60)
    
    # 准备请求
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # 图像生成提示词
    prompt = "A cute fluffy kitten with big round eyes, looking adorable, soft fur, highly detailed, warm lighting, photorealistic style"
    
    request_data = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": f"Please generate an image based on this description: {prompt}"
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    try:
        print("📤 发送图像生成请求...")
        print(f"💬 提示词: {prompt}")
        print(f"📊 请求数据: {json.dumps(request_data, indent=2)}")
        print()
        
        async with aiohttp.ClientSession() as session:
            api_url = f"{base_url}/chat/completions"
            print(f"🎯 API端点: {api_url}")
            
            async with session.post(api_url, headers=headers, json=request_data) as response:
                print(f"📈 状态码: {response.status}")
                response_text = await response.text()
                
                if response.status == 200:
                    print("✅ 请求成功！")
                    try:
                        result = json.loads(response_text)
                        print("📋 API响应结构:")
                        print(json.dumps(result, indent=2, ensure_ascii=False))
                        
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result['choices'][0]['message']['content']
                            print()
                            print("🎨 生成内容:")
                            print(content)
                            print()
                            print("🎉 图像生成API测试成功！")
                            return True
                        else:
                            print("❌ 响应格式异常，未找到生成内容")
                            return False
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON解析错误: {e}")
                        print(f"📄 原始响应: {response_text}")
                        return False
                else:
                    print(f"❌ 请求失败 (状态码: {response.status})")
                    print(f"📄 错误信息: {response_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ 请求过程中发生错误: {str(e)}")
        return False

async def main():
    """主函数"""
    print("🔬 第三方图像生成API直接测试")
    print()
    
    success = await test_liaobots_api()
    
    print()
    print("=" * 60)
    if success:
        print("✅ 测试完成：API连接和图像生成功能正常")
    else:
        print("❌ 测试失败：请检查API配置或网络连接")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生未预期错误: {e}")
        import traceback
        traceback.print_exc() 