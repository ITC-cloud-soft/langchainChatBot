# Function Calling实现方案 (类似Dify)

## 概述

本方案实现了类似Dify的Function Calling功能,可以动态从ARS获取Flows并转换为LLM可调用的函数。

## 架构设计

```
用户请求
  ↓
LLM (支持Function Calling)
  ↓
检测到需要执行Flow → 调用function: execute_flow_5
  ↓
ArsFunctionService 动态获取Flow定义
  ↓
执行ARS Flow
  ↓
返回结果给用户
```

## 核心组件

### 1. ArsFunctionService (`api/services/ars_function_service.py`)

**功能**:
- 从ARS动态获取Flow列表
- 将Flow转换为LangChain StructuredTool
- 生成OpenAI Function Calling格式的函数定义

**主要方法**:
```python
# 获取ARS的Flows
flows = await ArsFunctionService.fetch_flows_from_ars(ars_token)

# 创建LangChain tools
tools = await ArsFunctionService.create_langchain_tools(ars_token)

# 创建OpenAI Function定义
functions = ArsFunctionService.create_function_definitions(flows)
```

### 2. ArsFlowFunction

**功能**:
- 封装单个Flow的执行逻辑
- 提供统一的执行接口
- 转换为LangChain Tool

**示例**:
```python
flow_func = ArsFlowFunction(
    flow_id=5,
    name="CCFLOWシステム申請--仕入計画",
    description="仕入計画の申請フロー",
    ars_token=ars_token
)

# 执行Flow
result = await flow_func.execute(parameters={})

# 转换为LangChain Tool
tool = flow_func.to_langchain_tool()
```

## 支持的LLM Provider

### ✅ 支持Function Calling的Provider:

1. **OpenAI** (GPT-3.5, GPT-4)
   - 原生支持Function Calling
   - 推荐使用

2. **Google Gemini** (gemini-pro)
   - 支持Function Calling
   - 通过LangChain集成

3. **Anthropic Claude** (claude-3系列)
   - 支持Tool Use
   - 类似Function Calling

### ❌ 不支持Function Calling的Provider:

1. **Ollama Qwen**
   - 不支持原生Function Calling
   - 需要使用ReAct模式

2. **其他本地模型**
   - 大多数不支持Function Calling

## 实现步骤

### 步骤1: 检查当前LLM是否支持Function Calling

```python
# 在chat_service.py中检查
provider = config_manager.get_value("llm", "provider")

if provider in ["openai", "google", "anthropic"]:
    # 使用Function Calling模式
    use_function_calling = True
else:
    # 使用ReAct模式
    use_function_calling = False
```

### 步骤2: 动态创建Functions

```python
from api.services.ars_function_service import ArsFunctionService

# 获取用户的ARS token
ars_token = await get_user_ars_token(db, user_id)

# 创建LangChain tools
tools = await ArsFunctionService.create_langchain_tools(ars_token)

# 绑定tools到LLM
llm_with_tools = llm.bind_tools(tools)
```

### 步骤3: 修改chat_service.py支持Function Calling

```python
async def stream_message_with_functions(
    self,
    message: str,
    session_id: str,
    ars_token: str
) -> AsyncGenerator[Dict[str, Any], None]:
    """Function Calling模式的消息处理"""
    
    # 创建tools
    tools = await ArsFunctionService.create_langchain_tools(ars_token)
    
    # 绑定tools到LLM
    llm_with_tools = self.llm.bind_tools(tools)
    
    # 调用LLM
    response = await llm_with_tools.ainvoke(message)
    
    # 检查是否有function call
    if response.tool_calls:
        for tool_call in response.tool_calls:
            # 执行function
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # 查找对应的tool
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool:
                result = await tool.arun(tool_args)
                yield {"type": "function_result", "result": result}
    else:
        # 正常的文本响应
        yield {"type": "text", "content": response.content}
```

### 步骤4: 前端处理Function Calling结果

前端无需修改,因为Function Calling的结果会被转换为正常的文本响应。

## 使用示例

### 场景1: 用户请求执行Flow

**用户输入**:
```
CCFLOWシステム申請--仕入計画を実行します
```

**LLM响应** (Function Calling):
```json
{
  "function_call": {
    "name": "execute_flow_5",
    "arguments": {
      "flow_id": 5,
      "parameters": {}
    }
  }
}
```

**系统执行**:
1. 检测到function_call
2. 调用`execute_flow_5`
3. 执行ARS Flow 5
4. 返回结果给用户

**用户看到的结果**:
```
✅ Flow 5 (CCFLOWシステム申請--仕入計画) を正常に実行しました

実行結果:
{
  "status": "success",
  "data": {...}
}
```

### 场景2: 用户询问可用的Flows

**用户输入**:
```
どんなフローが使えますか?
```

**LLM响应** (正常文本):
```
以下のフローが利用可能です:

1. CCFLOWシステム申請--仕入計画 (Flow 5)
   - 仕入計画の申請を行います

2. CCFLOWシステム申請--入荷返品 (Flow 6)
   - 入荷返品の申請を行います

3. CCFLOWシステム承認フロー (Flow 7)
   - 承認処理を行います
```

## 优势对比

### Function Calling vs ReAct

| 特性 | Function Calling | ReAct |
|------|-----------------|-------|
| **准确性** | ✅ 高 (结构化输出) | ⚠️ 中 (需要解析文本) |
| **可靠性** | ✅ 高 (原生支持) | ⚠️ 中 (依赖提示词) |
| **灵活性** | ✅ 高 (动态函数定义) | ❌ 低 (需要硬编码) |
| **LLM支持** | ⚠️ 仅部分模型 | ✅ 所有模型 |
| **实现复杂度** | ⚠️ 中等 | ✅ 简单 |

## 迁移计划

### 阶段1: 双模式支持 (当前)
- ReAct模式: 用于Ollama等不支持Function Calling的模型
- Function Calling模式: 用于OpenAI/Gemini等支持的模型

### 阶段2: 推荐使用Function Calling
- 在设置页面提示用户切换到支持Function Calling的模型
- 提供模型推荐列表

### 阶段3: 完全迁移 (可选)
- 如果所有用户都使用支持Function Calling的模型
- 可以移除ReAct模式的代码

## 配置要求

### 推荐的LLM配置

**OpenAI**:
```toml
[llm]
provider = "openai"
api_base = "https://api.openai.com/v1"
api_key = "sk-..."
model_name = "gpt-4-turbo-preview"
temperature = 0.7
```

**Google Gemini**:
```toml
[llm]
provider = "google"
api_key = "..."
model_name = "gemini-pro"
temperature = 0.7
```

**Anthropic Claude**:
```toml
[llm]
provider = "anthropic"
api_key = "..."
model_name = "claude-3-opus-20240229"
temperature = 0.7
```

## 测试用例

### 测试1: 执行Flow
```python
# 输入
message = "CCFLOWシステム申請--仕入計画を実行します"

# 期待输出
{
  "success": True,
  "flow_id": 5,
  "flow_name": "CCFLOWシステム申請--仕入計画",
  "result": {...}
}
```

### 测试2: 询问Flow信息
```python
# 输入
message = "仕入計画のフローについて教えて"

# 期待输出
"CCFLOWシステム申請--仕入計画は、仕入計画の申請を行うフローです..."
```

### 测试3: 多个Flow执行
```python
# 输入
message = "仕入計画と入荷返品の両方を実行して"

# 期待输出
# 两个function call依次执行
```

## 注意事项

1. **ARS Token必须有效**
   - Function Calling需要有效的ARS token来获取Flow列表
   - 确保用户已配置ARS API Key

2. **Flow动态更新**
   - Flows在ARS中更新后,需要重新获取
   - 考虑添加缓存机制,定期刷新

3. **错误处理**
   - Function执行失败时,返回友好的错误信息
   - 记录详细的错误日志

4. **性能优化**
   - 缓存Flow列表,避免每次请求都调用ARS API
   - 使用异步执行,提高响应速度

## 下一步

1. ✅ 创建ArsFunctionService
2. ⏳ 修改chat_service.py支持Function Calling
3. ⏳ 添加provider检测逻辑
4. ⏳ 测试Function Calling模式
5. ⏳ 更新前端UI(可选)
