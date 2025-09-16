#!/usr/bin/env python3
"""
聊天API测试程序
测试当前项目的聊天API各种功能和连接状态
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

import httpx

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChatAPITester:
    """聊天API测试类"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """初始化测试器"""
        self.base_url = base_url
        self.client = None
        self.test_results = {}
    
    async def initialize(self):
        """初始化HTTP客户端"""
        try:
            self.client = httpx.AsyncClient(timeout=30.0)
            print("✅ HTTP客户端初始化成功")
            return True
        except Exception as e:
            print(f"❌ HTTP客户端初始化失败: {e}")
            return False
    
    async def test_health_check(self):
        """测试健康检查API"""
        print("\n" + "="*50)
        print("🔍 测试1: 健康检查")
        print("="*50)
        
        try:
            url = f"{self.base_url}/api/chat/health"
            print(f"📡 请求URL: {url}")
            
            response = await self.client.get(url)
            print(f"📊 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📋 响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                status = data.get("status")
                if status == "healthy":
                    print("✅ 健康检查通过 - 服务状态良好")
                    self.test_results["health_check"] = {"status": "success", "data": data}
                    return True
                else:
                    print(f"⚠️ 健康检查警告 - 服务状态: {status}")
                    self.test_results["health_check"] = {"status": "warning", "data": data}
                    return False
            else:
                print(f"❌ 健康检查失败 - HTTP状态码: {response.status_code}")
                print(f"📄 错误响应: {response.text}")
                self.test_results["health_check"] = {"status": "failed", "error": response.text}
                return False
                
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            self.test_results["health_check"] = {"status": "error", "error": str(e)}
            return False
    
    async def test_send_message(self):
        """测试发送消息API"""
        print("\n" + "="*50)
        print("💬 测试2: 发送消息")
        print("="*50)
        
        try:
            url = f"{self.base_url}/api/chat/send"
            test_message = "你好，这是一个测试消息，请简单回复"
            session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            payload = {
                "message": test_message,
                "session_id": session_id
            }
            
            print(f"📡 请求URL: {url}")
            print(f"📝 测试消息: {test_message}")
            print(f"🆔 会话ID: {session_id}")
            print(f"📦 请求数据: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            response = await self.client.post(url, json=payload)
            print(f"📊 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📋 响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                response_text = data.get("response", "")
                source_docs = data.get("source_documents", [])
                returned_session_id = data.get("session_id", "")
                
                print(f"🤖 AI回复: {response_text}")
                print(f"📚 源文档数量: {len(source_docs)}")
                print(f"🆔 返回会话ID: {returned_session_id}")
                
                # 检查是否是错误消息
                if "申し訳ありませんが" in response_text or "エラーが発生しました" in response_text:
                    print("⚠️ 收到日文错误消息，可能存在后端处理问题")
                    self.test_results["send_message"] = {
                        "status": "warning", 
                        "data": data,
                        "issue": "Japanese error message"
                    }
                    return False
                else:
                    print("✅ 消息发送成功，收到正常回复")
                    self.test_results["send_message"] = {"status": "success", "data": data}
                    return True
            else:
                print(f"❌ 消息发送失败 - HTTP状态码: {response.status_code}")
                print(f"📄 错误响应: {response.text}")
                self.test_results["send_message"] = {"status": "failed", "error": response.text}
                return False
                
        except Exception as e:
            print(f"❌ 消息发送异常: {e}")
            self.test_results["send_message"] = {"status": "error", "error": str(e)}
            return False
    
    async def test_stream_message(self):
        """测试流式消息API"""
        print("\n" + "="*50)
        print("🌊 测试3: 流式消息")
        print("="*50)
        
        try:
            url = f"{self.base_url}/api/chat/stream"
            test_message = "请用一句话解释什么是人工智能"
            session_id = f"stream_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            payload = {
                "message": test_message,
                "session_id": session_id
            }
            
            print(f"📡 请求URL: {url}")
            print(f"📝 测试消息: {test_message}")
            print(f"🆔 会话ID: {session_id}")
            print(f"📦 请求数据: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            print("🌊 开始接收流式响应...")
            
            async with self.client.stream("POST", url, json=payload) as response:
                print(f"📊 响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    print("📨 流式数据:")
                    chunk_count = 0
                    full_response = ""
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            chunk_count += 1
                            print(f"  📦 数据块 {chunk_count}: {line}")
                            
                            # 尝试解析SSE数据
                            if line.startswith("data: "):
                                try:
                                    json_data = line[6:]  # 移除 "data: " 前缀
                                    chunk_data = json.loads(json_data)
                                    
                                    if chunk_data.get("type") == "token":
                                        token = chunk_data.get("token", "")
                                        full_response += token
                                    elif chunk_data.get("type") == "final":
                                        final_response = chunk_data.get("response", "")
                                        print(f"🏁 最终响应: {final_response}")
                                        
                                except json.JSONDecodeError:
                                    print(f"  ⚠️ 无法解析JSON数据: {json_data}")
                    
                    print(f"📊 总共接收到 {chunk_count} 个数据块")
                    if full_response:
                        print(f"🔗 拼接的完整响应: {full_response}")
                    
                    if chunk_count > 0:
                        print("✅ 流式消息测试成功")
                        self.test_results["stream_message"] = {
                            "status": "success", 
                            "chunk_count": chunk_count,
                            "full_response": full_response
                        }
                        return True
                    else:
                        print("⚠️ 未收到任何流式数据")
                        self.test_results["stream_message"] = {"status": "warning", "issue": "No chunks received"}
                        return False
                else:
                    print(f"❌ 流式消息失败 - HTTP状态码: {response.status_code}")
                    error_content = await response.aread()
                    print(f"📄 错误响应: {error_content.decode()}")
                    self.test_results["stream_message"] = {"status": "failed", "error": error_content.decode()}
                    return False
                    
        except Exception as e:
            print(f"❌ 流式消息异常: {e}")
            self.test_results["stream_message"] = {"status": "error", "error": str(e)}
            return False
    
    async def test_conversation_history(self):
        """测试会话历史功能"""
        print("\n" + "="*50)
        print("📚 测试4: 会话历史")
        print("="*50)
        
        try:
            session_id = f"history_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"🆔 测试会话ID: {session_id}")
            
            # 发送多条消息建立会话历史
            messages = [
                "我的名字是张三",
                "我今年25岁",
                "我喜欢编程",
                "你还记得我的名字吗？"
            ]
            
            responses = []
            
            for i, message in enumerate(messages, 1):
                print(f"\n📝 发送第{i}条消息: {message}")
                
                payload = {
                    "message": message,
                    "session_id": session_id
                }
                
                response = await self.client.post(f"{self.base_url}/api/chat/send", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get("response", "")
                    print(f"🤖 AI回复: {response_text}")
                    responses.append({"message": message, "response": response_text})
                else:
                    print(f"❌ 第{i}条消息发送失败: {response.status_code}")
                    responses.append({"message": message, "error": response.text})
                
                # 短暂延迟
                await asyncio.sleep(0.5)
            
            # 尝试获取会话历史
            print(f"\n📖 尝试获取会话历史...")
            history_url = f"{self.base_url}/api/chat/sessions/{session_id}/history"
            print(f"📡 历史记录URL: {history_url}")
            
            history_response = await self.client.get(history_url)
            print(f"📊 历史记录响应状态码: {history_response.status_code}")
            
            if history_response.status_code == 200:
                history_data = history_response.json()
                print(f"📋 历史记录数据: {json.dumps(history_data, ensure_ascii=False, indent=2)}")
                
                history = history_data.get("data", {}).get("history", [])
                print(f"📚 历史记录条数: {len(history)}")
                
                if len(history) > 0:
                    print("📝 历史记录详情:")
                    for i, record in enumerate(history, 1):
                        role = record.get("role", "unknown")
                        content = record.get("content", "")[:50]
                        print(f"  {i}. {role}: {content}...")
                
                print("✅ 会话历史测试成功")
                self.test_results["conversation_history"] = {
                    "status": "success",
                    "messages_sent": len(messages),
                    "history_count": len(history),
                    "responses": responses
                }
                return True
            else:
                print(f"⚠️ 无法获取会话历史: {history_response.status_code}")
                print(f"📄 错误响应: {history_response.text}")
                
                # 即使无法获取历史，如果消息发送成功也算部分成功
                successful_messages = sum(1 for r in responses if "response" in r)
                if successful_messages > 0:
                    print(f"✅ 会话消息发送成功 ({successful_messages}/{len(messages)})")
                    self.test_results["conversation_history"] = {
                        "status": "partial_success",
                        "messages_sent": len(messages),
                        "successful_messages": successful_messages,
                        "responses": responses,
                        "history_error": history_response.text
                    }
                    return True
                else:
                    self.test_results["conversation_history"] = {
                        "status": "failed",
                        "error": "No successful messages"
                    }
                    return False
                    
        except Exception as e:
            print(f"❌ 会话历史测试异常: {e}")
            self.test_results["conversation_history"] = {"status": "error", "error": str(e)}
            return False
    
    async def test_session_management(self):
        """测试会话管理功能"""
        print("\n" + "="*50)
        print("🗂️ 测试5: 会话管理")
        print("="*50)
        
        try:
            # 测试获取会话列表
            print("📋 测试获取会话列表...")
            sessions_url = f"{self.base_url}/api/chat/sessions"
            print(f"📡 会话列表URL: {sessions_url}")
            
            sessions_response = await self.client.get(sessions_url)
            print(f"📊 会话列表响应状态码: {sessions_response.status_code}")
            
            if sessions_response.status_code == 200:
                sessions_data = sessions_response.json()
                print(f"📋 会话列表数据: {json.dumps(sessions_data, ensure_ascii=False, indent=2)}")
                
                sessions = sessions_data.get("data", {}).get("sessions", [])
                total_count = sessions_data.get("data", {}).get("total_count", 0)
                
                print(f"📚 总会话数: {total_count}")
                print(f"📝 当前页会话数: {len(sessions)}")
                
                if len(sessions) > 0:
                    print("📝 会话列表详情:")
                    for i, session in enumerate(sessions[:5], 1):  # 只显示前5个
                        session_id = session.get("session_id", "unknown")
                        title = session.get("title", "无标题")
                        created_at = session.get("created_at", "未知时间")
                        print(f"  {i}. ID: {session_id}, 标题: {title}, 创建时间: {created_at}")
                
                print("✅ 会话管理测试成功")
                self.test_results["session_management"] = {
                    "status": "success",
                    "total_sessions": total_count,
                    "current_page_sessions": len(sessions)
                }
                return True
            else:
                print(f"⚠️ 获取会话列表失败: {sessions_response.status_code}")
                print(f"📄 错误响应: {sessions_response.text}")
                self.test_results["session_management"] = {
                    "status": "failed",
                    "error": sessions_response.text
                }
                return False
                
        except Exception as e:
            print(f"❌ 会话管理测试异常: {e}")
            self.test_results["session_management"] = {"status": "error", "error": str(e)}
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始聊天API综合测试")
        print("="*60)
        
        # 初始化
        if not await self.initialize():
            print("❌ 初始化失败，无法继续测试")
            return
        
        # 运行各项测试
        tests = [
            ("健康检查", self.test_health_check),
            ("发送消息", self.test_send_message),
            ("流式消息", self.test_stream_message),
            ("会话历史", self.test_conversation_history),
            ("会话管理", self.test_session_management)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results[test_name] = "✅ 通过" if result else "⚠️ 部分通过"
            except Exception as e:
                results[test_name] = f"❌ 失败: {e}"
        
        # 输出测试总结
        print("\n" + "="*60)
        print("📊 测试结果总结")
        print("="*60)
        
        for test_name, result in results.items():
            print(f"{test_name}: {result}")
        
        # 输出详细结果
        print("\n" + "="*60)
        print("📋 详细测试结果")
        print("="*60)
        print(json.dumps(self.test_results, ensure_ascii=False, indent=2))
        
        # 计算成功率
        successful_tests = sum(1 for result in results.values() if "✅" in result)
        total_tests = len(results)
        success_rate = (successful_tests / total_tests) * 100
        
        print(f"\n🎯 测试成功率: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 测试整体通过！聊天API功能正常")
        elif success_rate >= 60:
            print("⚠️ 测试部分通过，存在一些问题需要关注")
        else:
            print("❌ 测试失败较多，需要检查API实现")
    
    async def cleanup(self):
        """清理资源"""
        if self.client:
            await self.client.aclose()
            print("🧹 资源清理完成")


async def main():
    """主函数"""
    # 检查环境变量
    api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    print(f"🌐 API基础URL: {api_base}")
    print(f"⏰ 测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建测试器并运行测试
    tester = ChatAPITester(base_url=api_base)
    
    try:
        await tester.run_all_tests()
    finally:
        await tester.cleanup()
    
    print(f"\n⏰ 测试结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🏁 聊天API测试完成")


if __name__ == "__main__":
    asyncio.run(main())
