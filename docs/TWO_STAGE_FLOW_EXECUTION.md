# 两阶段Flow执行实现

## 概述

实现了类似Dify的两阶段Flow执行机制:

1. **阶段1**: LLM识别Flow → 获取参数定义 → 返回表单给用户
2. **阶段2**: 用户填写参数 → 提交执行Flow

## 架构设计

```
用户输入: "CCFLOWシステム申請--仕入計画を実行"
    ↓
LLM识别Flow (通过ARS系统提示词)
    ↓
返回: {"id": "5", "type": "flow", "name": "CCFLOWシステム申請--仕入計画"}
    ↓
chat_service检测到Flow调用
    ↓
调用 ARSProvider.get_flow_params(flow_id=5)
    ↓
ARS后端返回参数定义:
{
  "params": [
    {"api_param_name": "UserNo", "param_type": "text"},
    {"api_param_name": "Department", "param_type": "option", "option": [...]}
  ]
}
    ↓
chat_service生成表单消息返回给用户:
"📋 CCFLOWシステム申請--仕入計画 を実行します
以下のパラメータを入力してください:
- UserNo (text)
- Department (option)
  選択肢:
  - 営業部 (sales)
  - 開発部 (dev)"
    ↓
用户填写参数后提交
    ↓
前端调用 /api/ars/flow/execute
    ↓
执行Flow并返回结果
```

## 已实现的组件

### 1. ARSServiceProvider 增强

**文件**: `backend/api/services/providers/ars_provider.py`

新增方法:
```python
async def get_flow_params(
    self,
    flow_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    获取Flow的参数定义
    
    Returns:
        {
            "success": True,
            "flow_id": "5",
            "params": [
                {
                    "api_param_name": "UserNo",
                    "param_type": "text"
                },
                {
                    "api_param_name": "Department",
                    "param_type": "option",
                    "option": [
                        {"option_label": "営業部", "option_value": "sales"},
                        ...
                    ]
                }
            ]
        }
    """
```

### 2. Chat Service 修改

**文件**: `backend/api/services/chat_service.py`

修改了ReAct解析逻辑:

**原逻辑**:
```python
检测到Flow → 直接执行 → 返回结果
```

**新逻辑**:
```python
检测到Flow → 获取参数定义 → 
  if 有参数:
    返回表单给用户
  else:
    直接执行Flow
```

### 3. 新增API路由

**文件**: `backend/api/routes/ars_flow.py`

提供两个新接口:

#### 3.1 获取Flow参数定义
```
POST /api/ars/flow/params
Request:
{
  "flow_id": "5"
}

Response:
{
  "success": true,
  "flow_id": "5",
  "flow_name": "CCFLOWシステム申請--仕入計画",
  "params": [...]
}
```

#### 3.2 执行Flow
```
POST /api/ars/flow/execute
Request:
{
  "flow_id": "5",
  "parameters": {
    "UserNo": "12345",
    "Department": "sales"
  }
}

Response:
{
  "success": true,
  "flow_id": "5",
  "result": {...}
}
```

## 使用流程

### 场景1: 有参数的Flow

**步骤1**: 用户发送消息
```
用户: "CCFLOWシステム申請--仕入計画を実行"
```

**步骤2**: LLM识别Flow,系统返回表单
```
📋 **CCFLOWシステム申請--仕入計画** を実行します

以下のパラメータを入力してください:

- **UserNo** (text)
- **Department** (option)
  選択肢:
  - 営業部 (sales)
  - 開発部 (dev)
  - 総務部 (admin)

---
**Flow ID**: 5
パラメータを入力後、再度送信してください。
```

**步骤3**: 用户填写参数(前端需要实现)
```javascript
// 前端解析表单,展示输入界面
// 用户填写: UserNo=12345, Department=sales
```

**步骤4**: 前端提交执行
```javascript
fetch('/api/ars/flow/execute', {
  method: 'POST',
  body: JSON.stringify({
    flow_id: '5',
    parameters: {
      UserNo: '12345',
      Department: 'sales'
    }
  })
})
```

**步骤5**: 返回执行结果
```
✅ **CCFLOWシステム申請--仕入計画** 実行成功!

実行結果:
{
  "申請番号": "REQ-2025-001",
  "ステータス": "承認待ち",
  "申請日時": "2025-01-19 15:30:00"
}
```

### 场景2: 无参数的Flow

**步骤1**: 用户发送消息
```
用户: "システムステータス確認を実行"
```

**步骤2**: LLM识别Flow,系统检测无参数,直接执行
```
✅ **システムステータス確認** 実行成功!

実行結果:
{
  "status": "正常",
  "cpu_usage": "45%",
  "memory_usage": "60%"
}
```

## 前端集成建议

### 1. 检测表单消息

前端需要检测消息中是否包含Flow参数表单:

```javascript
function isFlowParamForm(message) {
  // 检测是否包含 "Flow ID:" 标记
  return message.includes('**Flow ID**:') && 
         message.includes('パラメータを入力してください');
}
```

### 2. 解析参数定义

```javascript
function parseFlowParams(message) {
  // 提取Flow ID
  const flowIdMatch = message.match(/\*\*Flow ID\*\*:\s*(\d+)/);
  const flowId = flowIdMatch ? flowIdMatch[1] : null;
  
  // 提取Flow名称
  const nameMatch = message.match(/📋\s*\*\*(.+?)\*\*/);
  const flowName = nameMatch ? nameMatch[1] : null;
  
  // 解析参数列表
  const params = [];
  const paramPattern = /- \*\*(.+?)\*\* \((.+?)\)/g;
  let match;
  
  while ((match = paramPattern.exec(message)) !== null) {
    const param = {
      name: match[1],
      type: match[2],
      options: []
    };
    
    // 如果是option类型,提取选项
    if (param.type === 'option') {
      const optionPattern = /- (.+?) \((.+?)\)/g;
      const optionText = message.substring(match.index);
      let optMatch;
      
      while ((optMatch = optionPattern.exec(optionText)) !== null) {
        param.options.push({
          label: optMatch[1],
          value: optMatch[2]
        });
      }
    }
    
    params.push(param);
  }
  
  return { flowId, flowName, params };
}
```

### 3. 渲染表单UI

```javascript
function renderFlowParamForm(flowId, flowName, params) {
  const form = document.createElement('form');
  form.className = 'flow-param-form';
  
  // 标题
  const title = document.createElement('h3');
  title.textContent = `${flowName} を実行`;
  form.appendChild(title);
  
  // 参数输入
  params.forEach(param => {
    const fieldDiv = document.createElement('div');
    fieldDiv.className = 'form-field';
    
    const label = document.createElement('label');
    label.textContent = param.name;
    fieldDiv.appendChild(label);
    
    if (param.type === 'text') {
      const input = document.createElement('input');
      input.type = 'text';
      input.name = param.name;
      input.required = true;
      fieldDiv.appendChild(input);
    } else if (param.type === 'option') {
      const select = document.createElement('select');
      select.name = param.name;
      select.required = true;
      
      param.options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.label;
        select.appendChild(option);
      });
      
      fieldDiv.appendChild(select);
    }
    
    form.appendChild(fieldDiv);
  });
  
  // 提交按钮
  const submitBtn = document.createElement('button');
  submitBtn.type = 'submit';
  submitBtn.textContent = '実行';
  submitBtn.onclick = (e) => {
    e.preventDefault();
    executeFlow(flowId, new FormData(form));
  };
  form.appendChild(submitBtn);
  
  return form;
}
```

### 4. 提交执行

```javascript
async function executeFlow(flowId, formData) {
  // 收集参数
  const parameters = {};
  for (const [key, value] of formData.entries()) {
    parameters[key] = value;
  }
  
  // 调用API
  const response = await fetch('/api/ars/flow/execute', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`
    },
    body: JSON.stringify({
      flow_id: flowId,
      parameters: parameters
    })
  });
  
  const result = await response.json();
  
  if (result.success) {
    displayFlowResult(result.result);
  } else {
    displayError(result.error);
  }
}
```

## 配置要求

### 环境变量

```env
ARS_API_ENDPOINT=http://localhost:5001
```

### 路由注册

需要在主应用中注册新路由:

```python
# backend/main.py 或 app.py
from api.routes import ars_flow

app.include_router(
    ars_flow.router,
    prefix="/api/ars",
    tags=["ars"]
)
```

## 测试

### 测试获取参数定义

```bash
curl -X POST http://localhost:8000/api/ars/flow/params \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"flow_id": "5"}'
```

### 测试执行Flow

```bash
curl -X POST http://localhost:8000/api/ars/flow/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "flow_id": "5",
    "parameters": {
      "UserNo": "12345",
      "Department": "sales"
    }
  }'
```

## 优势

1. **用户友好**: 用户不需要记住参数格式,系统自动展示表单
2. **类型安全**: 支持text、option等类型,减少输入错误
3. **灵活性**: 无参数Flow直接执行,有参数Flow展示表单
4. **可扩展**: 易于添加新的参数类型(file、date等)

## 后续改进

1. **参数验证**: 添加前端和后端参数验证
2. **参数默认值**: 支持参数默认值
3. **条件参数**: 根据其他参数值动态显示/隐藏参数
4. **文件上传**: 支持file类型参数
5. **历史记录**: 保存用户填写的参数历史,方便重复使用
