# ARS Flow执行 - 双模式实现方案

## 📋 概述

实现兼容**Function Calling**和**ReAct**的双模式ARS flow执行方案:
- **当前(Ollama Qwen)**: 使用ReAct模式
- **未来(OpenAI/Gemini)**: 自动切换到Function Calling

---

## ✅ 已完成的工作

### 1. ARS工具创建 ✅
- `backend/api/tools/ars_tools.py` - 已修复API endpoint
  - 正确的URL: `/execute` (不是 `/api/flows/{id}/execute`)
  - 正确的认证: `api_key` header (不是 `Bearer token`)
  - 正确的payload格式: `{"type": "flow", "id": int, "params": {}}`

### 2. 路由修改 ✅
- `backend/api/routes/chat.py` - 已添加ars_token参数传递

---

## 🔧 需要实现的功能

### 方案1: ReAct模式 (当前Ollama Qwen)

#### 步骤1: 修改ARS系统提示词

在ARS系统提示词中添加ReAct格式指导:

```
当用户要求执行flow时,请按以下格式回答:

ACTION: execute_flow
FLOW_ID: <flow的ID号>
REASON: <执行这个flow的原因>

例如:
用户: "帮我执行仕入计划的申请"
你的回答:
ACTION: execute_flow
FLOW_ID: 5
REASON: 用户要求执行仕入计划申请,对应Flow 5
```

#### 步骤2: 在chat_service.py中添加ReAct响应解析

在`stream_message`方法中,LLM生成响应后,检测ReAct格式:

```python
# 在获取full_response后,检测ReAct格式
react_result = await self._parse_react_response(full_response, ars_token)
if react_result:
    # 执行flow成功,生成新的响应
    if react_result.get("success"):
        final_response = f"✅ Flow {react_result['flow_id']} 执行成功!\n\n{json.dumps(react_result.get('result'), ensure_ascii=False, indent=2)}"
    else:
        final_response = f"❌ Flow {react_result['flow_id']} 执行失败: {react_result.get('error')}"
    
    # 替换原始响应
    full_response = final_response
```

添加解析方法:

```python
async def _parse_react_response(self, response: str, ars_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """解析LLM的ReAct格式响应"""
    import re
    
    action_pattern = r'ACTION:\s*execute_flow'
    flow_id_pattern = r'FLOW_ID:\s*(\d+)'
    
    if re.search(action_pattern, response, re.IGNORECASE):
        flow_id_match = re.search(flow_id_pattern, response, re.IGNORECASE)
        if flow_id_match:
            flow_id = flow_id_match.group(1)
            
            from api.tools.ars_tools import ExecuteFlowTool
            tool = ExecuteFlowTool(ars_token=ars_token)
            result_str = await tool._arun(flow_id=flow_id)
            return json.loads(result_str)
    
    return None
```

---

### 方案2: Function Calling (未来OpenAI/Gemini)

当切换到OpenAI/Gemini时,在`stream_message`中启用工具绑定:

```python
# 检测LLM是否支持Function Calling
from api.core.config_manager import config_manager
provider = config_manager.get_value("llm", "provider") or "openai"

if provider in ["openai", "anthropic", "google"]:  # 支持Function Calling
    # 创建工具
    from api.tools.ars_tools import create_ars_tools
    tools = create_ars_tools(ars_token=ars_token)
    
    # 绑定工具到LLM
    streaming_llm = streaming_llm.bind_tools(tools)
    
    # LLM会自动决定何时调用工具
```

---

## 🎯 实现优先级

### 立即实现 (当前session)
1. ✅ 修复ARS API调用 (已完成)
2. ⏳ 添加ReAct响应解析到chat_service.py
3. ⏳ 更新ARS系统提示词,添加ReAct格式指导
4. ⏳ 测试ReAct模式

### 未来实现 (切换到OpenAI/Gemini时)
1. 启用Function Calling
2. 测试Function Calling模式
3. 对比两种模式的效果

---

## 📝 测试用例

### ReAct模式测试

**测试1: 直接指定flow ID**
```
用户: "执行flow 5"
期望: Qwen生成ReAct格式 → 系统执行flow → 返回结果
```

**测试2: 自然语言描述**
```
用户: "帮我执行仕入计划的申请"
期望: Qwen理解意图 → 生成ReAct格式 → 系统执行flow 5 → 返回结果
```

### Function Calling模式测试

**测试1: 自然语言**
```
用户: "帮我执行仕入计划的申请"
期望: LLM自动调用execute_flow(flow_id="5") → 返回结果
```

---

## ⚠️ 注意事项

1. **ARS API endpoint**: 必须使用 `/execute`,不是 `/api/flows/{id}/execute`
2. **认证方式**: 使用 `api_key` header,不是 `Bearer token`
3. **Payload格式**: `{"type": "flow", "id": int(flow_id), "params": {}}`
4. **ReAct格式**: 必须在系统提示词中明确指导Qwen使用特定格式
5. **错误处理**: 两种模式都需要处理ARS API返回的错误

---

## 🚀 下一步行动

由于代码编辑过程中出现了多次语法错误,建议:

1. **手动实现**: 参考本文档,手动修改chat_service.py
2. **测试ARS API**: 先确保ARS API可以正常调用
3. **逐步实现**: 先实现ReAct模式,测试通过后再考虑Function Calling

---

## 📞 需要确认的问题

1. **ARS服务状态**: ARS后端是否正在运行?
2. **ARS API Token**: 数据库中是否已保存正确的ARS API key?
3. **测试环境**: 是否可以访问 `http://ars-backend:5050/execute`?
