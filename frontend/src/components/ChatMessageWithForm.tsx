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

interface ChatMessageWithFormProps {
  content: string;
  role: 'user' | 'assistant';
  onFlowExecuted?: (result: any) => void;
}

export const ChatMessageWithForm: React.FC<ChatMessageWithFormProps> = ({
  content,
  role,
  onFlowExecuted,
}) => {
  const [flowData, setFlowData] = useState<FlowFormData | null>(null);
  const [showForm, setShowForm] = useState(true);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);

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
      
      // フォームは表示したまま（ユーザーの入力を保持）
    } catch (error) {
      console.error('Flow submission error:', error);
      setExecutionError(
        error instanceof Error ? error.message : 'パラメータ送信中にエラーが発生しました'
      );
    }
  };

  const handleCancel = () => {
    setShowForm(false);
  };

  // Flow参数フォームの場合
  if (flowData && showForm) {
    return (
      <Box sx={{ mb: 2 }}>
        <ARSFlowForm
          flowId={flowData.flowId}
          flowName={flowData.flowName}
          params={flowData.params}
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
