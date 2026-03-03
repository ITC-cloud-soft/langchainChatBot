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

## フロントエンド表単UIの実装（完了）

### ARSFlowForm コンポーネント
**ファイル**: `frontend/src/components/ARSFlowForm.tsx`

テキスト入力・プルダウン・ファイルアップロードを含む MUI ベースの動的フォームコンポーネント。

#### 自動入力フィールド
ログインユーザー情報および ARS Flow 11 経由の社員情報を自動セット:

```typescript
// ARS API 経由で社員情報を取得
const res = await fetch(
  `${API_BASE}/api/users/employee-info?username=${encodeURIComponent(user.username)}`,
  { headers: { Authorization: `Bearer ${token}` } }
);
// content_name / content_company / content_dept
// AFFILIATION_KAISHACODE / AFFILIATION_BUSHOCODE を自動入力
```

自動セットされるフィールド（hidden）:
- `content_empno`: ログインユーザー名（社員番号）
- `AgentMode`: `'0'`（固定）
- `AutoApprovalMode`: `'N'`（固定）

#### バリデーション
送信ボタン押下時に以下を検証:

| フィールド | ルール |
|---|---|
| `FK_Flow` | 必須（申請フローを選択してください） |
| `COMMENT` | 必須 |
| `content_name` | 必須（氏名） |
| `content_company` | 必須（会社名称） |
| `content_dept` | 必須（所属） |
| `AFFILIATION_KAISHACODE` | 必須 + `/^\d+$/`（数字のみ） |
| `AFFILIATION_BUSHOCODE` | 必須 + `/^\d+$/`（数字のみ） |
| `UPLOAD_FILES` | 任意 |

#### MainTblName_value 組み立て
送信前に `assembleMaintblnameValue()` でフィールドを JSON 構造に変換:

```typescript
result['MainTblName_value'] = JSON.stringify({
  COMMENT:          formValues['COMMENT'],
  SUMMRY:           JSON.stringify({ AgentMode, AutoApprovalMode, content: [...] }),
  AFFILIATION_INFO: { APPLICANT_AFFILIATION: { KAISHACODE, BUSHOCODE, ... } },
  UPLOAD_FILES:     formValues['UPLOAD_FILES'] || '[]',
});
```

CORP_NAME / DEPART_NAME / KANZI_NAME / EMPLOYEE_NO は SSFlow 側の `AddEmployeeInfo` が自動設定するため送信値から除外。

#### 申請内容アコーディオン UI（折りたたみ）
`MainTblName_value` グループは MUI `Accordion` でデフォルト閉じ状態:
- バリデーションエラー発生時: ボーダー赤 + ヘッダーに `⚠ 未入力または入力エラーがあります` を赤字表示
- 折りたたみ状態でもエラーを視覚的に確認可能

#### フォーム入力値の保持（submitted 状態）
`ChatMessageWithForm` コンポーネントの `expandFormData()` にて、
submitted 状態の `form_data` から `MainTblName_value` を逆パースし、
再表示時にフォームフィールドへ展開して入力値を復元。

#### フォーム状態管理（FormStatus）
```typescript
type FormStatus = 'pending' | 'submitted' | 'cancelled';
```
- `pending`: 入力可能
- `submitted` / `cancelled`: 読み取り専用表示（フィールド disabled）

### FlowResultDisplay コンポーネント
**ファイル**: `frontend/src/components/FlowResultDisplay.tsx`

実行結果の表示改善: `result_data` のキー（フロー名）を優先表示。
`result_data` が空の場合は `Flow {id}` にフォールバック。

---

## 後続改善方向

1. **パラメータデフォルト値**: 設定画面からのデフォルト値プリセット対応
2. **ファイルアップロード強化**: 複数ファイル・進捗表示
3. **実行履歴**: パラメータ入力履歴の保存と再利用
4. **条件パラメータ**: 他パラメータ値に基づく動的表示/非表示
