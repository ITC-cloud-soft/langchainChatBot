# Flow执行与参数收集机制

## 概述

本系统实现了基于ARS的Flow执行机制,支持参数收集和动态多Tool执行。

## 核心特性

### 1. 智能参数收集
- LLM识别用户意图,提取Flow ID
- 自动从ARS获取Flow的参数定义
- 根据参数类型生成交互式表单
- 用户填写参数后执行Flow

### 2. 动态多Tool执行
- Flow包含多个Tool(由ARS定义)
- 每个Tool按顺序执行
- 实时返回每个Tool的执行结果
- 支持成功/失败状态展示

## 执行流程

```
用户输入: "CCFLOWシステム申請--仕入計画を実行"
    ↓
LLM识别Flow (基于ARS系统提示词)
    ↓
返回: {"id": "5", "type": "flow", "name": "CCFLOWシステム申請--仕入計画"}
    ↓
chat_service检测到Flow调用
    ↓
调用 ARSProvider.get_flow_params(flow_id=5)
    ↓
ARS返回参数定义:
{
  "params": [
    {"api_param_name": "UserNo", "param_type": "text"},
    {"api_param_name": "Department", "param_type": "option", "option": [...]}
  ]
}
    ↓
判断是否需要参数:
    ├─ 有参数 → 生成表单返回给用户
    │   ↓
    │   用户填写参数
    │   ↓
    │   提交格式: EXECUTE_FLOW:5:{"UserNo":"12345","Department":"sales"}
    │   ↓
    └─ 无参数 → 直接执行Flow
        ↓
调用 ARS API: POST /execute
    ↓
ARS后端执行Flow中的所有Tools
    ├─ Tool 8: GenSEQ (生成序列号)
    ├─ Tool 9: MakeApply (创建申请)
    └─ Tool N: ...
    ↓
返回每个Tool的执行结果
    ↓
chat_service格式化显示结果
```

## 实现细节

### 1. Flow识别 (ReAct模式)

**位置**: `backend/api/services/chat_service.py:649-656`

```python
# 检测JSON格式: {"id": "X", "type": "flow", "name": "..."}
pattern = r'\{\s*"id"\s*:\s*"?(\d+)"?\s*,\s*"type"\s*:\s*"flow"'
match = re.search(pattern, full_response)

if match:
    flow_id = match.group(1)
    # 获取参数定义...
```

### 2. 参数定义获取

**位置**: `backend/api/services/chat_service.py:658-678`

```python
from api.services.providers.ars_provider import ARSServiceProvider

provider = ARSServiceProvider(api_endpoint=ars_endpoint)
provider.set_api_key(ars_token)

# 获取参数定义
params_result = await provider.get_flow_params(flow_id, context)
```

### 3. 表单生成

**位置**: `backend/api/services/chat_service.py:683-720`

有参数时生成表单:
```markdown
📋 **CCFLOWシステム申請--仕入計画** を実行します

以下のパラメータを入力してください:

- **UserNo** (text)
- **Department** (option)
  選択肢:
  - 営業部 (sales)
  - 開発部 (dev)

---
**Flow ID**: 5
パラメータを入力後、以下の形式で送信してください:
EXECUTE_FLOW:5:{"UserNo":"値","Department":"値"}
```

### 4. 参数提交执行

**位置**: `backend/api/services/chat_service.py:588-647`

用户提交格式:
```
EXECUTE_FLOW:5:{"UserNo":"12345","Department":"sales"}
```

系统解析并执行:
```python
param_submit_pattern = r'EXECUTE_FLOW:(\d+):(.+)'
param_match = re.search(param_submit_pattern, message)

if param_match:
    flow_id = param_match.group(1)
    params_json = param_match.group(2)
    params = json.loads(params_json)
    
    # 执行Flow
    tool = ExecuteFlowTool(ars_token=ars_token)
    result_str = await tool._arun(flow_id=flow_id, parameters=params)
```

### 5. 多Tool执行结果展示

**位置**: `backend/api/services/chat_service.py:614-642`

ARS返回的结果包含多个Tool的执行状态:
```json
{
  "result_data": {
    "CCFLOWシステム申請--仕入計画": [
      {
        "GenSEQ": {
          "result": "success",
          "data": {"WorkID": "123", "FK_Node": "456"},
          "ts": "2025-01-19 15:30:00"
        }
      },
      {
        "MakeApply": {
          "result": "success",
          "data": {"WorkID": "123", "FK_Node": "789"},
          "ts": "2025-01-19 15:30:05"
        }
      }
    ]
  }
}
```

格式化显示:
```markdown
✅ **Flow 5 実行成功!**

### 📋 CCFLOWシステム申請--仕入計画

**ステップ 1: GenSEQ** ✅
- WorkID: `123`
- FK_Node: `456`
- 実行時刻: 2025-01-19 15:30:00

**ステップ 2: MakeApply** ✅
- WorkID: `123`
- FK_Node: `789`
- 実行時刻: 2025-01-19 15:30:05

<details>
<summary>📊 詳細データを表示</summary>
...
</details>
```

## 使用场景

### 场景1: 有参数的Flow

**用户操作**:
1. 发送: "CCFLOWシステム申請--仕入計画を実行"
2. 系统返回参数表单
3. 用户填写: `EXECUTE_FLOW:5:{"UserNo":"12345","Department":"sales"}`
4. 系统执行并返回结果

### 场景2: 无参数的Flow

**用户操作**:
1. 发送: "システムステータス確認を実行"
2. 系统直接执行(无需参数)
3. 返回执行结果

## 参数类型支持

### text (文本输入)
```json
{
  "api_param_name": "UserNo",
  "param_type": "text"
}
```

### option (下拉选择)
```json
{
  "api_param_name": "Department",
  "param_type": "option",
  "option": [
    {"option_label": "営業部", "option_value": "sales"},
    {"option_label": "開発部", "option_value": "dev"}
  ]
}
```

## 关键组件

### ARSServiceProvider
**文件**: `backend/api/services/providers/ars_provider.py`

提供方法:
- `get_tools()`: 获取所有Flow列表
- `get_flow_params()`: 获取Flow的参数定义
- `execute_tool()`: 执行Flow

### ExecuteFlowTool
**文件**: `backend/api/tools/ars_tools.py`

LangChain工具,负责:
- 调用ARS API执行Flow
- 传递参数
- 返回执行结果

### ChatService
**文件**: `backend/api/services/chat_service.py`

核心逻辑:
- ReAct模式解析LLM输出
- 参数表单生成
- 结果格式化展示

## 与ARS的交互

### 1. 获取系统提示词
```
GET /get_message
→ 返回包含所有Flows和Tools的提示词
```

### 2. 获取Flow参数定义
```
GET /flow/{flow_id}/params
→ 返回参数定义列表
```

### 3. 执行Flow
```
POST /execute
Body: {
  "type": "flow",
  "id": 5,
  "params": {"UserNo": "12345", "Department": "sales"}
}
→ 返回所有Tool的执行结果
```

## 优势

1. **用户友好**: 自动生成参数表单,无需记忆格式
2. **类型安全**: 支持多种参数类型,减少输入错误
3. **灵活性**: 有参数显示表单,无参数直接执行
4. **透明性**: 展示每个Tool的执行状态和结果
5. **可扩展**: 易于添加新的参数类型

## 后续改进方向

1. **前端表单UI**: 实现可视化参数输入界面
2. **参数验证**: 添加前端和后端参数验证
3. **参数默认值**: 支持参数默认值
4. **文件上传**: 支持file类型参数
5. **执行历史**: 保存参数历史,方便重复使用
6. **条件参数**: 根据其他参数值动态显示/隐藏参数
