#!/usr/bin/env python3
"""
LLM服务测试程序
测试LLM服务的各种功能和连接状态
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

import httpx
from core.config import LLMSettings
from services.llm_service import LLMService

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_direct_api_call():
    """直接测试LLM API调用"""
    print("\n=== 直接API调用测试 ===")
    
    api_base = os.getenv("LLM_API_BASE", "http://localhost:8000")
    timeout = float(os.getenv("LLM_TIMEOUT", "30.0"))
    
    print(f"API Base: {api_base}")
    print(f"Timeout: {timeout}")
    
    # 1. 健康检查
    print("\n1. 健康检查测试:")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_base}/api/chat/health", timeout=5.0)
            print(f"  状态码: {response.status_code}")
            print(f"  响应头: {dict(response.headers)}")
            print(f"  响应体: {response.text}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"  JSON数据: {data}")
                    health_status = data.get("status")
                    print(f"  健康状态: {health_status}")
                except Exception as e:
                    print(f"  JSON解析失败: {e}")
            else:
                print(f"  健康检查失败，状态码: {response.status_code}")
                
    except Exception as e:
        print(f"  健康检查异常: {e}")
    
    # 2. 聊天API测试
    print("\n2. 聊天API测试:")
    try:
        url = f"{api_base}/api/chat/send"
        payload = {
            "message": "你好，这是一个测试消息",
            "session_id": "test_session_001"
        }
        
        print(f"  请求URL: {url}")
        print(f"  请求数据: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=timeout)
            print(f"  状态码: {response.status_code}")
            print(f"  响应头: {dict(response.headers)}")
            print(f"  响应体: {response.text}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"  JSON数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
                except Exception as e:
                    print(f"  JSON解析失败: {e}")
            else:
                print(f"  聊天API调用失败，状态码: {response.status_code}")
                
    except Exception as e:
        print(f"  聊天API调用异常: {e}")
    
    # 3. 流式API测试
    print("\n3. 流式API测试:")
    try:
        url = f"{api_base}/api/chat/stream"
        payload = {
            "message": "请简短回答：什么是人工智能？",
            "session_id": "test_session_002"
        }
        
        print(f"  请求URL: {url}")
        print(f"  请求数据: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, json=payload, timeout=timeout) as response:
                print(f"  状态码: {response.status_code}")
                print(f"  响应头: {dict(response.headers)}")
                
                if response.status_code == 200:
                    print("  流式响应:")
                    async for line in response.aiter_lines():
                        if line.strip():
                            print(f"    {line}")
                else:
                    print(f"  流式API调用失败，状态码: {response.status_code}")
                    content = await response.aread()
                    print(f"  错误内容: {content.decode()}")
                
    except Exception as e:
        print(f"  流式API调用异常: {e}")


async def test_llm_service():
    """测试LLM服务类"""
    print("\n=== LLM服务类测试 ===")
    
    # 创建配置
    config = LLMSettings()
    print(f"配置信息:")
    print(f"  API Base: {config.api_base}")
    print(f"  Timeout: {config.timeout}")
    print(f"  Live Prompt Type: {config.live_prompt_type}")
    
    # 创建服务实例
    llm_service = LLMService(config)
    
    # 1. 初始化测试
    print("\n1. 初始化测试:")
    try:
        success = await llm_service.initialize()
        print(f"  初始化结果: {success}")
    except Exception as e:
        print(f"  初始化失败: {e}")
        return
    
    # 2. 健康检查测试
    print("\n2. 健康检查测试:")
    try:
        health = await llm_service.health_check()
        print(f"  健康状态: {health}")
    except Exception as e:
        print(f"  健康检查失败: {e}")
    
    # 3. 普通响应生成测试
    print("\n3. 普通响应生成测试:")
    try:
        response = await llm_service.generate_response(
            text="你好，请简单介绍一下自己",
            session_id="test_session_003"
        )
        print(f"  响应文本: {response.text}")
        print(f"  元数据: {json.dumps(response.metadata, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"  响应生成失败: {e}")
    
    # 4. 流式响应生成测试
    print("\n4. 流式响应生成测试:")
    try:
        print("  流式响应:")
        async for chunk in llm_service.generate_response_stream(
            text="请用一句话解释什么是机器学习",
            session_id="test_session_004"
        ):
            if chunk.text:
                print(f"    文本块: {chunk.text}")
            if chunk.metadata.get("status"):
                print(f"    状态: {chunk.metadata['status']}")
    except Exception as e:
        print(f"  流式响应生成失败: {e}")
    
    # 5. 会话历史测试
    print("\n5. 会话历史测试:")
    try:
        # 发送几条消息
        await llm_service.generate_response("我的名字是张三", "test_session_005")
        await llm_service.generate_response("我今年25岁", "test_session_005")
        response = await llm_service.generate_response("你还记得我的名字吗？", "test_session_005")
        
        print(f"  最终响应: {response.text}")
        
        # 获取会话历史
        history = llm_service.get_conversation_history("test_session_005")
        print(f"  会话历史 ({len(history)} 条消息):")
        for i, msg in enumerate(history):
            print(f"    {i+1}. {msg.get('role', 'unknown')}: {msg.get('content', '')[:50]}...")
            
    except Exception as e:
        print(f"  会话历史测试失败: {e}")
    
    # 清理
    await llm_service.close()


async def test_environment_variables():
    """测试环境变量配置"""
    print("\n=== 环境变量测试 ===")
    
    env_vars = [
        "LLM_API_BASE",
        "LLM_TIMEOUT", 
        "LLM_LIVE_PROMPT_TYPE"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        print(f"{var}: {value}")
    
    # 检查.env文件
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print(f"\n.env文件存在: {env_file}")
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            llm_lines = [line.strip() for line in lines if line.strip().startswith('LLM_')]
            print("LLM相关配置:")
            for line in llm_lines:
                print(f"  {line}")
    else:
        print(f"\n.env文件不存在: {env_file}")


async def main():
    """主函数"""
    print("LLM服务测试程序")
    print("=" * 50)
    
    # 测试环境变量
    await test_environment_variables()
    
    # 测试直接API调用
    await test_direct_api_call()
    
    # 测试LLM服务类
    await test_llm_service()
    
    print("\n" + "=" * 50)
    print("测试完成")


if __name__ == "__main__":
    asyncio.run(main())
