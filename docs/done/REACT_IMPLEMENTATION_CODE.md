# ReAct模式实现代码

## 需要修改的文件

### 1. backend/api/services/chat_service.py

在 `stream_message` 方法中添加以下修改:

#### 修改1: 添加ars_token参数

找到这一行(约第470行):
```python
async def stream_message(
    self,
    message: str,
    session_id: Optional[str] = None,
    system_prompt: Optional[str] = None
) -> AsyncGenerator[Dict[str, Any], None]:
```

修改为:
```python
async def stream_message(
    self,
    message: str,
    session_id: Optional[str] = None,
    system_prompt: Optional[str] = None,
    ars_token: Optional[str] = None
) -> AsyncGenerator[Dict[str, Any], None]:
```

#### 修改2: 在获取full_response后添加ReAct解析

找到这段代码(约第576行):
```python
# Stream tokens
tokens = callback.get_tokens()
full_response = "".join(tokens)
self.log_info(f"Generated {len(tokens)} tokens, response: {full_response[:100]}...")
```

在这段代码之后,添加ReAct解析逻辑:
```python
# Stream tokens
tokens = callback.get_tokens()
full_response = "".join(tokens)
self.log_info(f"Generated {len(tokens)} tokens, response: {full_response[:100]}...")

# === 添加ReAct解析 ===
if ars_token and full_response:
    import re
    import json
    
    # 检测JSON格式的tool调用: {"id": "9", "type": "tool", "name": "..."}
    tool_pattern = r'\{\s*"id"\s*:\s*"(\d+)"\s*,\s*"type"\s*:\s*"tool"'
    match = re.search(tool_pattern, full_response)
    
    if match:
        flow_id = match.group(1)
        self.log_info(f"[ARS REACT] Detected tool call for flow_id={flow_id}")
        
        try:
            from api.tools.ars_tools import ExecuteFlowTool
            tool = ExecuteFlowTool(ars_token=ars_token)
            result_str = await tool._arun(flow_id=flow_id)
            result = json.loads(result_str)
            
            if result.get("success"):
                full_response = f"✅ Flow {flow_id} 実行成功!\n\n実行結果:\n{json.dumps(result.get('result'), ensure_ascii=False, indent=2)}"
            else:
                full_response = f"❌ Flow {flow_id} 実行失敗: {result.get('error')}"
            
            self.log_info(f"[ARS REACT] Flow execution completed, updated response")
        except Exception as e:
            self.log_error(f"[ARS REACT] Error executing flow {flow_id}", e)
            full_response = f"❌ Flow {flow_id} 実行中にエラーが発生しました: {str(e)}"
# === ReAct解析结束 ===

if full_response:
    # トークンを1文字ずつストリーミング
    for i, char in enumerate(full_response):
```

### 2. backend/api/routes/chat.py

找到这段代码(约第164行):
```python
async def generate():
    async for chunk in chat_service.stream_message(
        message=chat_message.message,
        session_id=chat_message.session_id,
        system_prompt=system_prompt
    ):
        yield f"data: {json.dumps(chunk)}\n\n"
```

修改为:
```python
async def generate():
    async for chunk in chat_service.stream_message(
        message=chat_message.message,
        session_id=chat_message.session_id,
        system_prompt=system_prompt,
        ars_token=ars_token
    ):
        yield f"data: {json.dumps(chunk)}\n\n"
```

---

## 实现说明

### ReAct检测逻辑

当前的ARS系统提示词会让LLM返回类似这样的JSON:
```json
{
    "id": "9",
    "type": "tool",
    "name": "CCFLOWシステムフロー1申請"
}
```

我们的ReAct解析会:
1. 检测响应中是否包含这种JSON格式
2. 提取 `id` 字段作为 `flow_id`
3. 调用ARS API执行flow
4. 将执行结果替换原始响应

### 执行流程

```
用户: "CCFLOWシステム申請--仕入計画を実行します"
  ↓
LLM生成响应: "为了执行...请使用工具 {"id": "9", "type": "tool", ...}"
  ↓
ReAct解析: 检测到flow_id=9
  ↓
调用ARS API: POST /execute {"type": "flow", "id": 9, "params": {}}
  ↓
返回执行结果: "✅ Flow 9 実行成功! ..."
```

---

## 测试步骤

1. 修改上述两个文件
2. 重新构建后端:
   ```bash
   docker compose -f docker-compose.full.dev.yml up -d --build chatbot-backend
   ```
3. 在聊天页面发送: "CCFLOWシステム申請--仕入計画を実行します"
4. 应该看到flow真正执行并返回结果

---

## 注意事项

1. **ARS API必须正在运行**: 确保 `http://ars-backend:5050` 可访问
2. **ARS Token必须正确**: 确保数据库中保存了正确的API key
3. **正则表达式匹配**: 如果LLM返回的JSON格式不同,需要调整正则表达式

---

## 如果仍然不工作

检查后端日志:
```bash
docker logs chatbot-backend --tail 100 | grep "ARS REACT"
```

应该看到类似这样的日志:
```
[ARS REACT] Detected tool call for flow_id=9
[ARS REACT] Flow execution completed, updated response
```
