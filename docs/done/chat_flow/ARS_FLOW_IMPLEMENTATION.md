# ARS Flow执行功能实现指南

## 📋 当前状态

### ✅ 已完成
1. **ARS系统提示词集成** - 成功应用到聊天中
2. **用户认证** - Token正确传递和验证
3. **ARS工具基础代码** - 已创建 `backend/api/tools/ars_tools.py`

### ❌ 待完成
**Flow执行功能** - 需要集成到chat_service中

---

## 🔍 问题分析

### Dify的实现方式
根据对dify文档的研究:
- **Agent Node**: workflow中的决策中心
- **Agent Strategy**: Function Calling或ReAct
- **工具调用流程**: 用户输入 → LLM推理 → 决定调用工具 → 执行工具 → 返回结果

### 当前系统的限制
- **Ollama Qwen**: 不支持Function Calling
- **未来**: 会切换到OpenAI或Gemini (支持Function Calling)

---

## 🛠️ 实现方案

### 方案1: 关键词触发 (当前Ollama Qwen)
检测用户消息中的关键词,如"执行flow 1",直接调用ARS API

**优点**: 简单快速,不依赖Function Calling  
**缺点**: 不够智能,需要精确匹配关键词

### 方案2: Function Calling (未来OpenAI/Gemini)
LLM自动识别意图并调用工具

**优点**: 智能,类似dify  
**缺点**: 需要LLM支持Function Calling

---

## 📝 实现步骤

### 步骤1: 修改 `chat_service.py`

在 `stream_message` 方法中添加flow检测逻辑:

```python
async def stream_message(
    self,
    message: str,
    session_id: Optional[str] = None,
    system_prompt: Optional[str] = None,
    ars_token: Optional[str] = None  # 新增参数
) -> AsyncGenerator[Dict[str, Any], None]:
    # ... 现有代码 ...
    
    # 在保存用户消息后,添加flow检测
    self._update_history_cache(session_id)
    
    # 检测并执行flow (关键词触发)
    flow_result = await self._detect_and_execute_flow(message, ars_token)
    if flow_result:
        # 生成执行结果的回复
        if flow_result.get("success"):
            response = f"✅ Flow {flow_result['flow_id']} 执行成功！\n\n执行结果：\n{json.dumps(flow_result.get('result', {}), ensure_ascii=False, indent=2)}"
        else:
            response = f"❌ Flow {flow_result['flow_id']} 执行失败。\n\n错误信息：{flow_result.get('error', 'Unknown error')}"
        
        # Stream响应并返回
        for i, char in enumerate(response):
            yield {"type": "token", "token": char, "session_id": session_id, "index": i}
        
        yield {"type": "final", "response": response, "source_documents": [], "session_id": session_id}
        
        # 保存到历史
        self.chat_history[session_id].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        await chat_history_service.add_message(session_id=session_id, role="assistant", content=response, message_type="text")
        self._update_history_cache(session_id)
        return  # 提前返回,不继续正常的LLM处理
    
    # 继续正常的LLM处理...
```

添加flow检测方法:

```python
async def _detect_and_execute_flow(self, message: str, ars_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """检测用户消息中是否包含flow执行意图"""
    import re
    
    # 检测关键词模式
    patterns = [
        r'(?:执行|実行|execute|run)\s*flow\s*(\d+)',
        r'flow\s*(\d+)\s*(?:を)?(?:执行|実行|execute|run)',
        r'(?:执行|実行|execute|run)\s*(?:フロー|流程)\s*(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            flow_id = match.group(1)
            self.log_info(f"[ARS FLOW] Detected flow execution: flow_id={flow_id}")
            
            try:
                from api.tools.ars_tools import ExecuteFlowTool
                tool = ExecuteFlowTool(ars_token=ars_token)
                result_str = await tool._arun(flow_id=flow_id)
                result = json.loads(result_str)
                return result
            except Exception as e:
                self.log_error(f"[ARS FLOW] Error executing flow {flow_id}", e)
                return {"success": False, "flow_id": flow_id, "error": str(e)}
    
    return None
```

### 步骤2: 修改 `chat.py` 路由

在stream endpoint中获取并传递ARS token:

```python
@router.post("/stream")
async def stream_chat(
    chat_message: ChatMessage,
    current_user: Annotated[Optional[CurrentUser], Depends(get_optional_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    # ... 现有代码获取system_prompt ...
    
    # 获取ARS token
    ars_token = None
    if current_user:
        from api.models.user import get_ars_token_by_user
        ars_token_obj = await get_ars_token_by_user(db, current_user.user_id)
        if ars_token_obj:
            ars_token = ars_token_obj.token
            default_logger.info(f"[ARS DEBUG] ARS token retrieved for user {current_user.user_id}")
    
    async def generate():
        async for chunk in chat_service.stream_message(
            message=chat_message.message,
            session_id=chat_message.session_id,
            system_prompt=system_prompt,
            ars_token=ars_token  # 传递token
        ):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## 🧪 测试

### 测试用例1: Flow执行
```
用户输入: "执行flow 5"
期望输出: 
✅ Flow 5 执行成功！

执行结果：
{
  "status": "completed",
  "data": {...}
}
```

### 测试用例2: Flow执行失败
```
用户输入: "执行flow 999"
期望输出:
❌ Flow 999 执行失败。

错误信息：Flow not found
```

### 测试用例3: 正常聊天
```
用户输入: "フロー一覧"
期望输出: (正常的LLM回答,列出flow列表)
```

---

## 🚀 部署步骤

1. 按照上述步骤修改代码
2. 重新构建后端容器: `docker compose -f docker-compose.full.dev.yml up -d --build chatbot-backend`
3. 测试flow执行功能
4. 验证日志中是否有 `[ARS FLOW]` 标记

---

## 📌 注意事项

1. **ARS API endpoint**: 确保环境变量 `ARS_API_ENDPOINT` 正确配置
2. **Token安全**: ARS token存储在数据库中,通过认证用户获取
3. **错误处理**: Flow执行失败时返回友好的错误消息
4. **日志记录**: 所有flow执行都有详细的日志记录

---

## 🔮 未来扩展

当切换到OpenAI/Gemini时,可以升级到Function Calling:

```python
# 使用LangChain Agent
from langchain.agents import create_openai_functions_agent
from api.tools.ars_tools import create_ars_tools

tools = create_ars_tools(ars_token=ars_token)
agent = create_openai_functions_agent(llm, tools, prompt)
result = agent.invoke({"input": message})
```

这样LLM会自动决定何时调用flow执行工具,更加智能。
