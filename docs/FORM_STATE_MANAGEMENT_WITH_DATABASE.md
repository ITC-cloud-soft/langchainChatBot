# Flow表单状态管理 - 数据库持久化方案

## 文档信息

- **作成日**: 2026-01-20
- **バージョン**: 1.0.0
- **対象機能**: Flow表单状态的数据库持久化管理
- **関連ドキュメント**: `FLOW_EXECUTION_WITH_PARAMETERS.md`

---

## 1. 概要

### 1.1 背景

現在のFlow表单实现存在以下问题：
- 表单状态仅保存在前端内存中，刷新页面后丢失
- 无法追踪表单的完整生命周期（提交、取消、完成）
- 用户输入的数据在取消操作后会丢失
- 跨设备无法同步表单状态

### 1.2 目的

通过数据库持久化表单状态，实现：
- ✅ 表单状态永久保存，刷新不丢失
- ✅ 完整的状态追踪（pending → submitted/cancelled → completed）
- ✅ 用户输入数据保留（即使取消操作）
- ✅ 跨设备状态同步
- ✅ 简化前端渲染逻辑

### 1.3 技术方案

利用现有的 `ChatMessage` 表的 `message_metadata` 字段（JSON类型）存储表单状态信息，无需新建表。

---

## 2. 数据结构设计

### 2.1 表单消息的 metadata 结构

```json
{
  "message_type": "flow_form",
  "flow_id": "5",
  "flow_name": "CCFLOWシステム申請--仕入計画",
  "form_status": "pending",
  "form_data": {
    "UserNo": "12345",
    "Department": "sales",
    "StartDate": "2024-01-01"
  },
  "submitted_at": "2024-01-19T14:30:00Z",
  "cancelled_at": null,
  "completed_at": null,
  "execution_result": null
}
```

### 2.2 表单状态定义

| 状态 | 説明 | 遷移条件 |
|------|------|---------|
| `pending` | 初期状態、ユーザー入力待ち | 表单生成时 |
| `submitted` | 提交済み、実行待ち | 用户点击"実行"按钮 |
| `cancelled` | キャンセル済み | 用户点击"キャンセル"按钮 |
| `completed` | 実行完了（成功） | 收到成功的执行结果 |
| `error` | 実行失敗 | 收到失败的执行结果 |

### 2.3 状态流转图

```
pending (初期)
  ├─→ submitted (提交) → completed (成功)
  │                    → error (失敗)
  └─→ cancelled (取消)
```

---

## 3. 実装詳細

### 3.1 バックエンド修改

#### 3.1.1 データベースモデル拡張

**ファイル**: `backend/api/models/database.py`

**修改内容**: 添加表单状态更新函数

```python
async def update_message_form_status_async(
    db: AsyncSession,
    message_id: str,
    form_status: str,
    form_data: Optional[Dict[str, Any]] = None,
    execution_result: Optional[Dict[str, Any]] = None
) -> Optional[ChatMessage]:
    """
    メッセージの表单状態を更新
    
    Args:
        db: データベースセッション
        message_id: メッセージID
        form_status: 表单状態 (pending/submitted/cancelled/completed/error)
        form_data: 表单データ
        execution_result: 実行結果（完了時）
        
    Returns:
        更新されたChatMessageオブジェクト
    """
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.message_id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if message:
        metadata = message.message_metadata or {}
        metadata['form_status'] = form_status
        
        # 表单データを保存
        if form_data is not None:
            metadata['form_data'] = form_data
        
        # タイムスタンプを記録
        if form_status == 'submitted':
            metadata['submitted_at'] = datetime.now().isoformat()
        elif form_status == 'cancelled':
            metadata['cancelled_at'] = datetime.now().isoformat()
        elif form_status in ['completed', 'error']:
            metadata['completed_at'] = datetime.now().isoformat()
            if execution_result:
                metadata['execution_result'] = execution_result
        
        message.message_metadata = metadata
        await db.commit()
        await db.refresh(message)
    
    return message


async def get_message_by_id_async(
    db: AsyncSession,
    message_id: str
) -> Optional[ChatMessage]:
    """
    メッセージIDでメッセージを取得
    
    Args:
        db: データベースセッション
        message_id: メッセージID
        
    Returns:
        ChatMessageオブジェクト
    """
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.message_id == message_id)
    )
    return result.scalar_one_or_none()
```

**追加位置**: ファイル末尾（既存の async 関数群の後）

---

#### 3.1.2 API エンドポイント追加

**ファイル**: `backend/api/routes/chat.py`

**修改内容**: 表单状態更新APIを追加

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any

class FormStatusUpdate(BaseModel):
    """表单状態更新リクエスト"""
    form_status: str
    form_data: Optional[Dict[str, Any]] = None
    execution_result: Optional[Dict[str, Any]] = None


@router.patch("/messages/{message_id}/form-status")
async def update_message_form_status(
    message_id: str,
    update_data: FormStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    表单メッセージの状態を更新
    
    Args:
        message_id: メッセージID
        update_data: 更新データ
        db: データベースセッション
        
    Returns:
        更新されたメッセージ情報
    """
    try:
        from api.models.database import update_message_form_status_async
        
        default_logger.info(
            f"Updating form status for message {message_id}: {update_data.form_status}"
        )
        
        message = await update_message_form_status_async(
            db=db,
            message_id=message_id,
            form_status=update_data.form_status,
            form_data=update_data.form_data,
            execution_result=update_data.execution_result
        )
        
        if not message:
            raise HTTPException(
                status_code=404, 
                detail=f"Message {message_id} not found"
            )
        
        return format_success_response(
            data=message.to_dict(),
            message="Form status updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        default_logger.error(f"Error updating form status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{message_id}")
async def get_message(
    message_id: str,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    メッセージIDでメッセージを取得
    
    Args:
        message_id: メッセージID
        db: データベースセッション
        
    Returns:
        メッセージ情報
    """
    try:
        from api.models.database import get_message_by_id_async
        
        message = await get_message_by_id_async(db, message_id)
        
        if not message:
            raise HTTPException(
                status_code=404,
                detail=f"Message {message_id} not found"
            )
        
        return format_success_response(
            data=message.to_dict(),
            message="Message retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        default_logger.error(f"Error retrieving message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

**追加位置**: 既存のチャット関連エンドポイントの後

---

#### 3.1.3 Flow実行時の状態更新

**ファイル**: `backend/api/services/chat_service.py`

**修改内容**: EXECUTE_FLOW メッセージ処理時に表单メッセージを更新

```python
# process_message 関数内で EXECUTE_FLOW を検出した場合
async def process_message(
    self,
    message: str,
    session_id: Optional[str] = None,
    system_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """Process a chat message and return response"""
    # ... 既存のコード ...
    
    # EXECUTE_FLOW メッセージの検出
    if message.startswith("EXECUTE_FLOW:"):
        try:
            parts = message.split(":", 2)
            if len(parts) == 3:
                flow_id = parts[1]
                form_data = json.loads(parts[2])
                
                self.log_info(f"Detected EXECUTE_FLOW: flow_id={flow_id}")
                
                # 直前のメッセージ（表单メッセージ）のIDを取得
                # セッション履歴から最後のassistantメッセージを探す
                if session_id in self.chat_history:
                    messages = self.chat_history[session_id]
                    for msg in reversed(messages):
                        if msg.get("role") == "assistant":
                            # メッセージIDを取得（保存されている場合）
                            form_message_id = msg.get("message_id")
                            if form_message_id:
                                # 表单状態を 'submitted' に更新
                                try:
                                    from api.models.database import update_message_form_status_async
                                    from api.core.database import database_manager
                                    
                                    async with database_manager.get_session() as db_session:
                                        await update_message_form_status_async(
                                            db=db_session,
                                            message_id=form_message_id,
                                            form_status='submitted',
                                            form_data=form_data
                                        )
                                    self.log_info(f"Updated form status to 'submitted' for message {form_message_id}")
                                except Exception as e:
                                    self.log_warning(f"Failed to update form status: {str(e)}")
                            break
                
        except Exception as e:
            self.log_error(f"Error processing EXECUTE_FLOW message", e)
    
    # ... 既存のコード ...
```

**修改位置**: `process_message` 関数の先頭、メッセージ検証の後

---

### 3.2 フロントエンド修改

#### 3.2.1 表单状態サービス作成

**新規ファイル**: `frontend/src/services/formStatusService.ts`

```typescript
/**
 * 表单状態管理サービス
 * バックエンドAPIと連携して表单状態を更新・取得
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export type FormStatus = 'pending' | 'submitted' | 'cancelled' | 'completed' | 'error';

export interface FormStatusUpdateRequest {
  form_status: FormStatus;
  form_data?: Record<string, any>;
  execution_result?: Record<string, any>;
}

export interface FormStatusResponse {
  success: boolean;
  data: {
    message_id: string;
    metadata: {
      form_status: FormStatus;
      form_data?: Record<string, any>;
      submitted_at?: string;
      cancelled_at?: string;
      completed_at?: string;
      execution_result?: any;
    };
  };
  message: string;
}

/**
 * 表单状態を更新
 */
export const updateFormStatus = async (
  messageId: string,
  formStatus: FormStatus,
  formData?: Record<string, any>,
  executionResult?: Record<string, any>
): Promise<FormStatusResponse> => {
  try {
    const response = await axios.patch<FormStatusResponse>(
      `${API_BASE_URL}/api/chat/messages/${messageId}/form-status`,
      {
        form_status: formStatus,
        form_data: formData,
        execution_result: executionResult
      }
    );
    return response.data;
  } catch (error) {
    console.error('Failed to update form status:', error);
    throw error;
  }
};

/**
 * メッセージを取得
 */
export const getMessage = async (messageId: string): Promise<FormStatusResponse> => {
  try {
    const response = await axios.get<FormStatusResponse>(
      `${API_BASE_URL}/api/chat/messages/${messageId}`
    );
    return response.data;
  } catch (error) {
    console.error('Failed to get message:', error);
    throw error;
  }
};
```

---

#### 3.2.2 ChatMessageWithForm コンポーネント修改

**ファイル**: `frontend/src/components/ChatMessageWithForm.tsx`

**修改内容**: データベースから表单状態を読み取り、更新時にAPIを呼び出す

```typescript
import React, { useState, useEffect } from 'react';
import { Box, Typography, Alert } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import { ARSFlowForm } from './ARSFlowForm';
import { FlowResultDisplay } from './FlowResultDisplay';
import { 
  isFlowParamMessage, 
  parseFlowParamMessage,
  FlowFormData 
} from '../utils/arsFormConverter';
import { isFlowResultMessage, parseFlowResultMessage } from '../utils/flowResultParser';
import { updateFormStatus, FormStatus } from '../services/formStatusService';

interface ChatMessageWithFormProps {
  content: string;
  role: 'user' | 'assistant';
  messageId?: string;  // メッセージID追加
  metadata?: {
    form_status?: FormStatus;
    form_data?: Record<string, any>;
    [key: string]: any;
  };
  onFlowExecuted?: (result: any) => void;
}

export const ChatMessageWithForm: React.FC<ChatMessageWithFormProps> = ({
  content,
  role,
  messageId,
  metadata,
  onFlowExecuted,
}) => {
  const [flowData, setFlowData] = useState<FlowFormData | null>(null);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);
  
  // データベースから表单状態を読み取る
  const formStatus = metadata?.form_status || 'pending';
  const savedFormData = metadata?.form_data || {};

  useEffect(() => {
    // メッセージがFlow参数フォームかチェック
    if (role === 'assistant' && isFlowParamMessage(content)) {
      const parsed = parseFlowParamMessage(content);
      if (parsed) {
        setFlowData(parsed);
      }
    }
    
    // メッセージがFlow実行結果かチェック
    if (role === 'assistant' && isFlowResultMessage(content)) {
      const parsed = parseFlowResultMessage(content);
      if (parsed.isFlowResult) {
        setExecutionResult(parsed);
      }
    }
  }, [content, role]);

  const handleFlowSubmit = async (flowId: string, values: Record<string, any>) => {
    try {
      // データベースに表单状態を保存
      if (messageId) {
        await updateFormStatus(messageId, 'submitted', values);
        console.log('Form status updated to submitted');
      }
      
      // 特殊フォーマット: EXECUTE_FLOW:flow_id:params_json
      const paramsJson = JSON.stringify(values);
      const message = `EXECUTE_FLOW:${flowId}:${paramsJson}`;
      
      // 親コンポーネントに通知（メッセージ送信をトリガー）
      if (onFlowExecuted) {
        onFlowExecuted({
          type: 'send_message',
          message
        });
      }
      
    } catch (error) {
      console.error('Flow submission error:', error);
      setExecutionError(
        error instanceof Error ? error.message : 'パラメータ送信中にエラーが発生しました'
      );
    }
  };

  const handleCancel = async () => {
    try {
      // データベースに表单状態を保存（キャンセル）
      if (messageId) {
        // 現在の表单データを取得して保存
        await updateFormStatus(messageId, 'cancelled', savedFormData);
        console.log('Form status updated to cancelled');
      }
    } catch (error) {
      console.error('Form cancellation error:', error);
    }
  };

  // Flow参数フォームの場合
  if (flowData) {
    return (
      <Box sx={{ mb: 2 }}>
        <ARSFlowForm
          flowId={flowData.flowId}
          flowName={flowData.flowName}
          params={flowData.params}
          formStatus={formStatus}
          initialValues={savedFormData}
          onSubmit={handleFlowSubmit}
          onCancel={handleCancel}
        />
      </Box>
    );
  }

  // Flow実行結果の表示
  if (executionResult && executionResult.isFlowResult) {
    return (
      <FlowResultDisplay
        flowId={executionResult.flowId || ''}
        success={executionResult.success || false}
        resultData={executionResult.resultData}
        error={executionResult.error}
      />
    );
  }

  // Flow実行エラーの表示
  if (flowData && executionError) {
    return (
      <Box sx={{ mb: 2 }}>
        <Alert severity="error">
          ❌ <strong>{flowData.flowName}</strong> 実行失敗: {executionError}
        </Alert>
      </Box>
    );
  }

  // 通常のメッセージ
  return (
    <Box
      sx={{
        mb: 2,
        p: 1.5,
        borderRadius: 2,
        backgroundColor: role === 'user' ? '#e3f2fd' : '#f5f5f5',
        maxWidth: '80%',
        alignSelf: role === 'user' ? 'flex-end' : 'flex-start',
      }}
    >
      <ReactMarkdown>{content}</ReactMarkdown>
    </Box>
  );
};
```

**主な変更点**:
1. `messageId` と `metadata` プロパティを追加
2. `formStatus` と `savedFormData` をmetadataから読み取る
3. `handleFlowSubmit` で `updateFormStatus` API を呼び出し
4. `handleCancel` で `updateFormStatus` API を呼び出し

---

#### 3.2.3 ARSFlowForm コンポーネント修改

**ファイル**: `frontend/src/components/ARSFlowForm.tsx`

**修改内容**: `formStatus` プロパティを追加し、状態に応じて表单を制御

```typescript
import React, { useState } from 'react';
import {
  Box,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  FormHelperText,
} from '@mui/material';
import { ARSParam } from '../utils/arsFormConverter';
import { FormStatus } from '../services/formStatusService';

interface ARSFlowFormProps {
  flowId: string;
  flowName: string;
  params: ARSParam[];
  onSubmit: (flowId: string, values: Record<string, any>) => Promise<void>;
  onCancel?: () => void;
  formStatus?: FormStatus;  // 追加
  initialValues?: Record<string, any>;
}

export const ARSFlowForm: React.FC<ARSFlowFormProps> = ({
  flowId,
  flowName,
  params,
  onSubmit,
  onCancel,
  formStatus = 'pending',  // デフォルト値
  initialValues = {},
}) => {
  const [formValues, setFormValues] = useState<Record<string, any>>(initialValues);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // 表单が編集可能かどうか
  const isEditable = formStatus === 'pending';
  
  // 表单が読み取り専用かどうか
  const isReadonly = !isEditable;

  const handleChange = (paramName: string, value: any) => {
    if (!isEditable) return;  // 編集不可の場合は何もしない
    
    setFormValues(prev => ({
      ...prev,
      [paramName]: value,
    }));
    
    // エラーをクリア
    if (errors[paramName]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[paramName];
        return newErrors;
      });
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    params.forEach(param => {
      if (param.required && !formValues[param.api_param_name]) {
        newErrors[param.api_param_name] = `${param.api_param_name}は必須です`;
      }
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) {
      return;
    }
    
    setSubmitting(true);
    setSubmitError(null);
    
    try {
      await onSubmit(flowId, formValues);
      // 状態更新はChatMessageWithFormで行う
    } catch (error) {
      console.error('Flow execution error:', error);
      setSubmitError(
        error instanceof Error ? error.message : 'Flowの実行中にエラーが発生しました'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancelClick = () => {
    if (onCancel) {
      onCancel();
    }
  };

  const renderField = (param: ARSParam) => {
    const { api_param_name, param_type, option } = param;
    const value = formValues[api_param_name] || '';
    const error = errors[api_param_name];

    switch (param_type) {
      case 'text':
        return (
          <TextField
            key={api_param_name}
            fullWidth
            label={api_param_name}
            value={value}
            onChange={(e) => handleChange(api_param_name, e.target.value)}
            error={!!error}
            helperText={error}
            disabled={!isEditable || submitting}
            variant="outlined"
            size="small"
            InputProps={{
              readOnly: isReadonly,
            }}
          />
        );

      case 'number':
        return (
          <TextField
            key={api_param_name}
            fullWidth
            label={api_param_name}
            type="number"
            value={value}
            onChange={(e) => handleChange(api_param_name, e.target.value)}
            error={!!error}
            helperText={error}
            disabled={!isEditable || submitting}
            variant="outlined"
            size="small"
            InputProps={{
              readOnly: isReadonly,
            }}
          />
        );

      case 'option':
        return (
          <FormControl
            key={api_param_name}
            fullWidth
            error={!!error}
            disabled={!isEditable || submitting}
            size="small"
          >
            <InputLabel>{api_param_name}</InputLabel>
            <Select
              value={value}
              onChange={(e) => handleChange(api_param_name, e.target.value)}
              label={api_param_name}
              readOnly={isReadonly}
            >
              {option?.map((opt) => (
                <MenuItem key={opt.option_value} value={opt.option_value}>
                  {opt.option_label}
                </MenuItem>
              ))}
            </Select>
            {error && <FormHelperText>{error}</FormHelperText>}
          </FormControl>
        );

      case 'date':
        return (
          <TextField
            key={api_param_name}
            fullWidth
            label={api_param_name}
            type="date"
            value={value}
            onChange={(e) => handleChange(api_param_name, e.target.value)}
            error={!!error}
            helperText={error}
            disabled={!isEditable || submitting}
            variant="outlined"
            size="small"
            InputLabelProps={{
              shrink: true,
            }}
            InputProps={{
              readOnly: isReadonly,
            }}
          />
        );

      default:
        return (
          <TextField
            key={api_param_name}
            fullWidth
            label={api_param_name}
            value={value}
            onChange={(e) => handleChange(api_param_name, e.target.value)}
            error={!!error}
            helperText={error}
            disabled={!isEditable || submitting}
            variant="outlined"
            size="small"
            InputProps={{
              readOnly: isReadonly,
            }}
          />
        );
    }
  };

  // 状態に応じたメッセージを表示
  const renderStatusMessage = () => {
    switch (formStatus) {
      case 'submitted':
        return (
          <Alert severity="success" sx={{ mt: 2 }}>
            ✅ パラメータが送信されました。実行結果をお待ちください...
          </Alert>
        );
      case 'cancelled':
        return (
          <Alert severity="info" sx={{ mt: 2 }}>
            🚫 操作がキャンセルされました。入力内容は保持されています。
          </Alert>
        );
      case 'completed':
        return (
          <Alert severity="success" sx={{ mt: 2 }}>
            ✅ 実行が完了しました。
          </Alert>
        );
      case 'error':
        return (
          <Alert severity="error" sx={{ mt: 2 }}>
            ❌ 実行中にエラーが発生しました。
          </Alert>
        );
      default:
        return null;
    }
  };

  return (
    <Paper
      elevation={2}
      sx={{
        p: 2.5,
        backgroundColor: isReadonly ? '#fafafa' : '#f5f5f5',
        borderRadius: 2,
        maxWidth: 500,
        opacity: isReadonly ? 0.9 : 1,
      }}
    >
      <Box component="form" onSubmit={handleSubmit}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          📋 {flowName}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {isEditable ? '以下のパラメータを入力してください' : 'パラメータ（読み取り専用）'}
        </Typography>

        {submitError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {submitError}
          </Alert>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {params.map(param => renderField(param))}
        </Box>

        {renderStatusMessage()}

        {isEditable && (
          <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              size="small"
              disabled={submitting}
              startIcon={submitting ? <CircularProgress size={16} /> : null}
              sx={{ flex: 1, py: 0.75 }}
            >
              {submitting ? '実行中...' : '実行'}
            </Button>
          
            {onCancel && (
              <Button
                variant="outlined"
                color="secondary"
                size="small"
                onClick={handleCancelClick}
                disabled={submitting}
                sx={{ minWidth: 80, py: 0.75 }}
              >
                キャンセル
              </Button>
            )}
          </Box>
        )}

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1.5 }}>
          Flow ID: {flowId} | 状態: {formStatus}
        </Typography>
      </Box>
    </Paper>
  );
};
```

**主な変更点**:
1. `formStatus` プロパティを追加
2. `isEditable` と `isReadonly` フラグで表单の編集可否を制御
3. すべての入力フィールドに `disabled` と `readOnly` を適用
4. 状態に応じたメッセージを表示する `renderStatusMessage` 関数を追加
5. ボタンは `pending` 状態の時のみ表示

---

#### 3.2.4 OptimizedChatMessage コンポーネント修改

**ファイル**: `frontend/src/components/OptimizedChatMessage.tsx`

**修改内容**: メッセージIDとmetadataをChatMessageWithFormに渡す

```typescript
interface OptimizedChatMessageProps {
  message: {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
    message_id?: string;  // 追加
    metadata?: Record<string, any>;  // 追加
    sourceDocuments?: Array<{
      content: string;
      metadata: Record<string, unknown>;
    }>;
  };
  isLast: boolean;
  onSendMessage?: (message: string) => void;
}

// ... 既存のコード ...

// アシスタントメッセージの場合、ChatMessageWithFormを使用
if (message.role === 'assistant') {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'flex-start',
        mb: 2,
        animation: isLast ? 'fadeIn 0.3s ease-in' : 'none',
        px: 1,
      }}
    >
      <Box
        sx={{
          maxWidth: { xs: '85%', sm: '70%' },
          minWidth: { xs: '150px', sm: '200px' },
          width: 'fit-content',
        }}
      >
        <ChatMessageWithForm
          content={message.content}
          role={message.role}
          messageId={message.message_id}  // 追加
          metadata={message.metadata}  // 追加
          onFlowExecuted={(result) => {
            if (result.type === 'send_message' && onSendMessage) {
              onSendMessage(result.message);
            }
          }}
        />
        
        {/* タイムスタンプ */}
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{
            display: 'block',
            textAlign: 'left',
            mt: 0.5,
            fontSize: '0.75rem',
            opacity: 0.8,
          }}
        >
          {formattedTime}
        </Typography>
      </Box>
    </Box>
  );
}
```

**主な変更点**:
1. `OptimizedChatMessageProps` に `message_id` と `metadata` を追加
2. `ChatMessageWithForm` に `messageId` と `metadata` を渡す

---

## 4. データフロー

### 4.1 表单生成から完了までのフロー

```
1. LLMがFlow参数フォームを生成
   ↓
2. バックエンドがメッセージを保存（metadata.form_status = 'pending'）
   ↓
3. フロントエンドが表单を表示（編集可能）
   ↓
4. ユーザーが入力して「実行」をクリック
   ↓
5. フロントエンドがAPI呼び出し: PATCH /messages/{id}/form-status
   - form_status: 'submitted'
   - form_data: {...}
   ↓
6. データベースに状態保存
   ↓
7. EXECUTE_FLOW メッセージを送信
   ↓
8. バックエンドがFlow実行
   ↓
9. 実行結果を受信
   ↓
10. バックエンドが表单メッセージを更新
    - form_status: 'completed' or 'error'
    - execution_result: {...}
   ↓
11. フロントエンドが結果を表示
```

### 4.2 キャンセル時のフロー

```
1. ユーザーが「キャンセル」をクリック
   ↓
2. フロントエンドがAPI呼び出し: PATCH /messages/{id}/form-status
   - form_status: 'cancelled'
   - form_data: {...}  // 現在の入力内容を保存
   ↓
3. データベースに状態保存
   ↓
4. 表单が読み取り専用で表示される
   - 入力内容は保持される
   - ボタンは非表示
```

---

## 5. テスト計画

### 5.1 バックエンドテスト

#### 5.1.1 ユニットテスト

```python
# tests/test_form_status.py

async def test_update_form_status_to_submitted():
    """表单状態を submitted に更新できることを確認"""
    # テストコード

async def test_update_form_status_to_cancelled():
    """表单状態を cancelled に更新できることを確認"""
    # テストコード

async def test_form_data_persistence():
    """表单データが正しく保存されることを確認"""
    # テストコード
```

#### 5.1.2 統合テスト

```python
async def test_form_lifecycle():
    """表单の完全なライフサイクルをテスト"""
    # 1. 表单メッセージ作成
    # 2. submitted に更新
    # 3. completed に更新
    # 4. データ取得して検証
```

### 5.2 フロントエンドテスト

#### 5.2.1 コンポーネントテスト

```typescript
// ARSFlowForm.test.tsx

describe('ARSFlowForm', () => {
  it('should render in editable mode when formStatus is pending', () => {
    // テストコード
  });

  it('should render in readonly mode when formStatus is submitted', () => {
    // テストコード
  });

  it('should preserve form data when cancelled', () => {
    // テストコード
  });
});
```

#### 5.2.2 統合テスト

```typescript
describe('Form Status Integration', () => {
  it('should update status to submitted when form is submitted', async () => {
    // テストコード
  });

  it('should update status to cancelled when form is cancelled', async () => {
    // テストコード
  });
});
```

### 5.3 E2Eテスト

```typescript
// e2e/form-status.spec.ts

test('complete form submission flow', async ({ page }) => {
  // 1. チャットページを開く
  // 2. Flow実行を要求
  // 3. 表单が表示されることを確認
  // 4. パラメータを入力
  // 5. 実行ボタンをクリック
  // 6. 表单が読み取り専用になることを確認
  // 7. ページをリロード
  // 8. 表单状態が保持されていることを確認
});

test('form cancellation flow', async ({ page }) => {
  // 1. チャットページを開く
  // 2. Flow実行を要求
  // 3. 表单が表示されることを確認
  // 4. パラメータを入力
  // 5. キャンセルボタンをクリック
  // 6. 表单が読み取り専用になることを確認
  // 7. 入力内容が保持されていることを確認
});
```

---

## 6. マイグレーション

### 6.1 既存データの移行

既存の表单メッセージには `form_status` がないため、初回ロード時にデフォルト値を設定：

```python
# migration script (optional)
async def migrate_existing_form_messages():
    """既存の表单メッセージに form_status を追加"""
    async with database_manager.get_session() as db:
        # FLOW_PARAM を含むメッセージを検索
        result = await db.execute(
            select(ChatMessage).where(
                ChatMessage.content.like('%FLOW_PARAM%')
            )
        )
        messages = result.scalars().all()
        
        for message in messages:
            if not message.message_metadata:
                message.message_metadata = {}
            
            if 'form_status' not in message.message_metadata:
                message.message_metadata['form_status'] = 'pending'
        
        await db.commit()
```

### 6.2 データベースインデックス追加（オプション）

パフォーマンス向上のため、インデックスを追加：

```sql
-- message_type にインデックスを追加
CREATE INDEX idx_message_type ON chat_messages(message_type);

-- metadata の form_status に仮想カラムとインデックスを追加（MySQL 5.7+）
ALTER TABLE chat_messages 
ADD COLUMN form_status_virtual VARCHAR(20) 
GENERATED ALWAYS AS (JSON_UNQUOTE(JSON_EXTRACT(metadata, '$.form_status'))) VIRTUAL;

CREATE INDEX idx_form_status ON chat_messages(form_status_virtual);
```

---

## 7. デプロイ手順

### 7.1 バックエンドデプロイ

```bash
# 1. コードをプル
cd langchainChatBot/backend
git pull origin main

# 2. 依存関係を更新（必要に応じて）
pip install -r requirements.txt

# 3. データベースマイグレーション（必要に応じて）
# python scripts/migrate_form_status.py

# 4. サービス再起動
docker-compose restart backend
```

### 7.2 フロントエンドデプロイ

```bash
# 1. コードをプル
cd langchainChatBot/frontend
git pull origin main

# 2. 依存関係を更新
npm install

# 3. ビルド
npm run build

# 4. サービス再起動
docker-compose restart frontend
```

### 7.3 動作確認

1. チャットページを開く
2. Flow実行を要求
3. 表单が表示されることを確認
4. パラメータを入力して実行
5. 表单が読み取り専用になることを確認
6. ページをリロード
7. 表单状態が保持されていることを確認
8. キャンセル操作も同様にテスト

---

## 8. トラブルシューティング

### 8.1 表单状態が更新されない

**症状**: ボタンをクリックしても表单状態が変わらない

**原因**:
- API呼び出しが失敗している
- message_id が正しく渡されていない

**解決方法**:
1. ブラウザのコンソールでエラーを確認
2. ネットワークタブでAPI呼び出しを確認
3. バックエンドのログを確認

### 8.2 ページリロード後に状態が失われる

**症状**: リロード後に表单が初期状態に戻る

**原因**:
- メッセージ取得時に metadata が含まれていない
- フロントエンドで metadata を正しく読み取っていない

**解決方法**:
1. API レスポンスに metadata が含まれているか確認
2. OptimizedChatMessage で metadata を正しく渡しているか確認

### 8.3 表单データが保存されない

**症状**: キャンセル後に入力内容が消える

**原因**:
- form_data が API に送信されていない
- データベース更新が失敗している

**解決方法**:
1. API リクエストボディを確認
2. バックエンドのログでデータベース更新を確認

---

## 9. 今後の拡張

### 9.1 表单バージョン管理

表单の変更履歴を追跡：

```json
{
  "form_status": "submitted",
  "form_data": {...},
  "form_history": [
    {
      "version": 1,
      "data": {...},
      "updated_at": "2024-01-19T14:00:00Z"
    },
    {
      "version": 2,
      "data": {...},
      "updated_at": "2024-01-19T14:30:00Z"
    }
  ]
}
```

### 9.2 表单検証ルール

サーバーサイドでの検証：

```python
def validate_form_data(flow_id: str, form_data: Dict[str, Any]) -> bool:
    """表单データを検証"""
    # パラメータ定義を取得
    # 必須チェック
    # 型チェック
    # 範囲チェック
    pass
```

### 9.3 表单テンプレート

よく使う表单をテンプレートとして保存：

```typescript
interface FormTemplate {
  template_id: string;
  flow_id: string;
  name: string;
  default_values: Record<string, any>;
}
```

---

## 10. 参考資料

- [FLOW_EXECUTION_WITH_PARAMETERS.md](./FLOW_EXECUTION_WITH_PARAMETERS.md) - Flow実行の基本仕様
- [TWO_STAGE_FLOW_EXECUTION.md](./TWO_STAGE_FLOW_EXECUTION.md) - 2段階実行の詳細
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- React Hook Form: https://react-hook-form.com/
- Material-UI: https://mui.com/

---

## 変更履歴

| 日付 | バージョン | 変更内容 | 担当者 |
|------|----------|---------|--------|
| 2026-01-20 | 1.0.0 | 初版作成 | Cascade |

---

## 承認

| 役割 | 氏名 | 日付 | 署名 |
|------|------|------|------|
| 作成者 | Cascade | 2026-01-20 | - |
| レビュー担当 | - | - | - |
| 承認者 | - | - | - |
