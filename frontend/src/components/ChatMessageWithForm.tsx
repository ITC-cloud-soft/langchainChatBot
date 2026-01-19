/**
 * Flow参数フォームを含むチャットメッセージコンポーネント
 */

import React, { useState, useEffect } from 'react';
import { Box, Typography, Alert } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import { ARSFlowForm } from './ARSFlowForm';
import { 
  isFlowParamMessage, 
  parseFlowParamMessage,
  FlowFormData 
} from '../utils/arsFormConverter';
import { executeFlow } from '../services/arsFlowService';

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
  }, [content, role]);

  const handleFlowSubmit = async (flowId: string, values: Record<string, any>) => {
    try {
      const result = await executeFlow(flowId, values);
      
      if (result.success) {
        setExecutionResult(result.result);
        setShowForm(false);
        setExecutionError(null);
        
        // 親コンポーネントに通知
        if (onFlowExecuted) {
          onFlowExecuted(result);
        }
      } else {
        setExecutionError(result.error || 'Flow実行に失敗しました');
      }
    } catch (error) {
      console.error('Flow execution error:', error);
      setExecutionError(
        error instanceof Error ? error.message : 'Flow実行中にエラーが発生しました'
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

  // Flow実行結果の表示
  if (flowData && !showForm && executionResult) {
    return (
      <Box sx={{ mb: 2 }}>
        <Alert severity="success" sx={{ mb: 1 }}>
          ✅ <strong>{flowData.flowName}</strong> 実行成功!
        </Alert>
        <Box
          sx={{
            backgroundColor: '#f5f5f5',
            borderRadius: 1,
            p: 2,
            fontFamily: 'monospace',
            fontSize: '0.875rem',
            overflow: 'auto',
            maxHeight: 400,
          }}
        >
          <Typography variant="body2" component="pre" sx={{ m: 0 }}>
            {JSON.stringify(executionResult, null, 2)}
          </Typography>
        </Box>
      </Box>
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
