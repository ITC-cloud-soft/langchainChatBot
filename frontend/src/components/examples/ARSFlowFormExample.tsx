/**
 * ARS Flow Form 使用例
 * 
 * このファイルは、既存のチャットコンポーネントにFlow参数フォームを統合する方法を示します
 */

import React, { useState } from 'react';
import { Box, Container, Paper } from '@mui/material';
import { ChatMessageWithForm } from '../ChatMessageWithForm';
import { ARSFlowForm } from '../ARSFlowForm';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

/**
 * 使用例: チャットページでの統合
 */
export const ARSFlowFormExample: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'user',
      content: 'CCFLOWシステム申請--仕入計画を実行',
      timestamp: new Date(),
    },
    {
      id: '2',
      role: 'assistant',
      content: `📋 **CCFLOWシステム申請--仕入計画** を実行します

以下のパラメータを入力してください:

- **UserNo** (text)
- **Department** (option)
  選択肢:
  - 営業部 (sales)
  - 開発部 (dev)
  - 総務部 (admin)

---
**Flow ID**: 5
パラメータを入力後、再度送信してください。`,
      timestamp: new Date(),
    },
  ]);

  const handleFlowExecuted = (result: any) => {
    // Flow実行完了後の処理
    console.log('Flow executed:', result);
    
    // 必要に応じて新しいメッセージを追加
    // setMessages(prev => [...prev, newMessage]);
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 3, minHeight: 400 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          {messages.map((message) => (
            <ChatMessageWithForm
              key={message.id}
              content={message.content}
              role={message.role}
              onFlowExecuted={handleFlowExecuted}
            />
          ))}
        </Box>
      </Paper>
    </Container>
  );
};

/**
 * 既存のチャットコンポーネントへの統合方法
 * 
 * 1. ChatMessageWithFormコンポーネントをインポート
 * 2. 既存のメッセージレンダリングロジックを置き換え
 * 
 * Before:
 * ```tsx
 * {messages.map(msg => (
 *   <Box key={msg.id}>
 *     <ReactMarkdown>{msg.content}</ReactMarkdown>
 *   </Box>
 * ))}
 * ```
 * 
 * After:
 * ```tsx
 * {messages.map(msg => (
 *   <ChatMessageWithForm
 *     key={msg.id}
 *     content={msg.content}
 *     role={msg.role}
 *     onFlowExecuted={handleFlowExecuted}
 *   />
 * ))}
 * ```
 */

/**
 * 手動でフォームを制御する場合の例
 */
export const ManualFormControlExample: React.FC = () => {
  const [showForm, setShowForm] = useState(true);

  const handleSubmit = async (flowId: string, values: Record<string, any>) => {
    console.log('Submitting flow:', flowId, values);
    // API呼び出し
    setShowForm(false);
  };

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      {showForm && (
        <ARSFlowForm
          flowId="5"
          flowName="CCFLOWシステム申請--仕入計画"
          params={[
            {
              api_param_name: 'UserNo',
              param_type: 'text',
              required: true,
            },
            {
              api_param_name: 'Department',
              param_type: 'option',
              option: [
                { option_label: '営業部', option_value: 'sales' },
                { option_label: '開発部', option_value: 'dev' },
                { option_label: '総務部', option_value: 'admin' },
              ],
              required: true,
            },
          ]}
          onSubmit={handleSubmit}
          onCancel={() => setShowForm(false)}
        />
      )}
    </Container>
  );
};
