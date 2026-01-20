/**
 * Flow参数フォームを含むチャットメッセージコンポーネント
 */

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
  messageId?: string;
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
  
  // ローカル状態でフォーム状態を管理（即座のUI更新のため）
  const [localFormStatus, setLocalFormStatus] = useState<FormStatus | null>(null);
  const [localFormData, setLocalFormData] = useState<Record<string, any> | null>(null);
  
  // metadataが変更されたら、ローカル状態をリセット（データベースの状態を優先）
  useEffect(() => {
    if (metadata?.form_status && metadata.form_status !== 'pending') {
      setLocalFormStatus(null);
      setLocalFormData(null);
    }
  }, [metadata?.form_status]);
  
  // ローカル状態が設定されている場合はそれを使用、なければmetadataから取得
  const formStatus = localFormStatus || metadata?.form_status || 'pending';
  const savedFormData = localFormData || metadata?.form_data || {};
  
  console.log('[ChatMessageWithForm] Form data:', {
    formStatus,
    savedFormData,
    savedFormData_json: JSON.stringify(savedFormData),
    metadata_form_data: metadata?.form_data,
    metadata_form_data_json: JSON.stringify(metadata?.form_data),
    localFormData
  });

  useEffect(() => {
    console.log('[ChatMessageWithForm] useEffect triggered', { 
      messageId, 
      metadata, 
      form_status: metadata?.form_status,
      content_preview: content.substring(0, 100)
    });
    
    // metadataにparams定義がある場合は、それを使用
    if (metadata?.params && metadata?.flow_id) {
      console.log('[ChatMessageWithForm] Using params from metadata:', metadata.params);
      setFlowData({
        flowId: metadata.flow_id,
        flowName: metadata.flow_name || `Flow ${metadata.flow_id}`,
        params: metadata.params
      });
      return;
    }
    
    // metadataにparamsがない場合は、contentから解析
    if (role === 'assistant' && isFlowParamMessage(content)) {
      const parsed = parseFlowParamMessage(content);
      if (parsed) {
        console.log('[ChatMessageWithForm] Parsed params from content:', parsed);
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
  }, [content, role, metadata]);

  const handleFlowSubmit = async (flowId: string, values: Record<string, any>) => {
    try {
      console.log('[ChatMessageWithForm] handleFlowSubmit called', { flowId, messageId, values });
      
      // 即座にローカル状態を更新してUIを反映
      setLocalFormStatus('submitted');
      setLocalFormData(values);
      
      // バックエンドAPIを呼び出してデータベースを更新
      if (messageId) {
        console.log('[ChatMessageWithForm] Calling updateFormStatus API', { messageId });
        await updateFormStatus(messageId, 'submitted', values);
        console.log('[ChatMessageWithForm] Form status updated to submitted in database');
      } else {
        console.warn('[ChatMessageWithForm] No messageId provided, skipping database update');
      }
      
      const paramsJson = JSON.stringify(values);
      const message = `EXECUTE_FLOW:${flowId}:${paramsJson}`;
      
      if (onFlowExecuted) {
        onFlowExecuted({
          type: 'send_message',
          message
        });
      }
      
    } catch (error) {
      console.error('Flow submission error:', error);
      // エラーが発生した場合はローカル状態をリセット
      setLocalFormStatus(null);
      setLocalFormData(null);
      setExecutionError(
        error instanceof Error ? error.message : 'パラメータ送信中にエラーが発生しました'
      );
    }
  };

  const handleCancel = async () => {
    try {
      // 即座にローカル状態を更新してUIを反映
      setLocalFormStatus('cancelled');
      setLocalFormData(savedFormData);
      
      // バックエンドAPIを呼び出してデータベースを更新
      if (messageId) {
        await updateFormStatus(messageId, 'cancelled', savedFormData);
        console.log('Form status updated to cancelled in database');
      }
    } catch (error) {
      console.error('Form cancellation error:', error);
      // エラーが発生した場合はローカル状態をリセット
      setLocalFormStatus(null);
      setLocalFormData(null);
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

  // Flow実行結果の表示（新しいFlowResultDisplayコンポーネントを使用）
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
  if (executionError) {
    return (
      <Box sx={{ mb: 2 }}>
        <Alert severity="error">
          ❌ 実行失敗: {executionError}
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
