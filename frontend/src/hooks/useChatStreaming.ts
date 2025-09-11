import { useCallback, useEffect, useRef, useState } from 'react';
import { chatApi } from '../services/api';
import { useSnackbar } from 'notistack';

// ID生成ユーティリティ
const generateMessageId = () => `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sourceDocuments?: Array<{
    content: string;
    metadata: Record<string, unknown>;
  }>;
}

interface UseChatStreamingProps {
  sessionId: string;
  onMessageUpdate: (updater: (prev: ChatMessage[]) => ChatMessage[]) => void;
  onLoadingChange: (isLoading: boolean) => void;
  onUpdateLastMessage: (updates: Partial<ChatMessage>) => void;
}

interface UseChatStreamingReturn {
  sendMessage: (message: string) => Promise<void>;
  isStreaming: boolean;
  error: string | null;
  abortController: AbortController | null;
}

export const useChatStreaming = ({
  sessionId,
  onMessageUpdate,
  onLoadingChange,
  onUpdateLastMessage,
}: UseChatStreamingProps): UseChatStreamingReturn => {
  const { enqueueSnackbar } = useSnackbar();
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (message: string) => {
      if (!message.trim()) return;

      // 前回のストリーミングを中止
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // 新しいAbortControllerを作成
      abortControllerRef.current = new AbortController();
      const { signal } = abortControllerRef.current;

      setIsStreaming(true);
      setError(null);
      onLoadingChange(true);

      try {
        // ユーザーメッセージを追加
        const userMessage: ChatMessage = {
          id: generateMessageId(),
          role: 'user',
          content: message,
          timestamp: new Date().toISOString(),
        };

        // ローディングメッセージを追加
        const loadingMessage: ChatMessage = {
          id: generateMessageId(),
          role: 'assistant',
          content: '応答を待っています...', // ローディングメッセージ
          timestamp: new Date().toISOString(),
        };

        onMessageUpdate(prev => {
          const safePrev = Array.isArray(prev) ? prev : [];
          const newMessages = [...safePrev, userMessage, loadingMessage];
          console.log('Adding messages to chat:', { 
            userMessage, 
            loadingMessage, 
            prevCount: safePrev.length, 
            newCount: newMessages.length,
            newMessages 
          });
          return newMessages;
        });

        // ストリーミングレスポンスを取得
        const stream = await chatApi.streamMessage(message, sessionId);
        let fullResponse = '';
        let sourceDocuments: Array<{
          content: string;
          metadata: Record<string, unknown>;
        }> = [];

        // ストリーミング処理
        try {
          for await (const chunk of stream) {
            if (signal.aborted) break;

            if (chunk.type === 'token') {
              fullResponse += chunk.token;
              // 最後のメッセージを更新
              onUpdateLastMessage({
                content: fullResponse,
              });
            } else if (chunk.type === 'final') {
              fullResponse = chunk.response;
              sourceDocuments = chunk.source_documents || [];
              // 最終レスポンスで更新
              onUpdateLastMessage({
                content: fullResponse,
                sourceDocuments,
              });
            } else if (chunk.type === 'error') {
              throw new Error(chunk.error);
            }
          }
        } catch (streamError) {
          throw streamError;
        }

        // ストリーミング終了後に最終メッセージを確定
        if (fullResponse) {
          onUpdateLastMessage({
            content: fullResponse,
            sourceDocuments,
          });
        }
      } catch (error: any) {
        if (error.name === 'AbortError') {
          // ユーザーによる中止
          onMessageUpdate(prev => {
            const safePrev = Array.isArray(prev) ? prev : [];
            const newMessages = safePrev.slice(0, -1); // ローディングメッセージを削除
            return [
              ...newMessages,
              {
                id: generateMessageId(),
                role: 'assistant',
                content: 'メッセージの送信が中止されました。',
                timestamp: new Date().toISOString(),
              },
            ];
          });
        } else {
          setError(error.message || 'メッセージの送信中にエラーが発生しました');
          enqueueSnackbar('メッセージの送信中にエラーが発生しました', { variant: 'error' });

          // エラーメッセージを追加
          onMessageUpdate(prev => {
            const safePrev = Array.isArray(prev) ? prev : [];
            const newMessages = safePrev.slice(0, -1); // ローディングメッセージを削除
            return [
              ...newMessages,
              {
                id: generateMessageId(),
                role: 'assistant',
                content: '申し訳ありませんが、メッセージの処理中にエラーが発生しました。',
                timestamp: new Date().toISOString(),
              },
            ];
          });
        }
      } finally {
        setIsStreaming(false);
        onLoadingChange(false);
        abortControllerRef.current = null;
      }
    },
    [sessionId, onMessageUpdate, onLoadingChange, onUpdateLastMessage, enqueueSnackbar],
  );

  // コンポーネントのアンマウント時にクリーンアップ
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    sendMessage,
    isStreaming,
    error,
    abortController: abortControllerRef.current,
  };
};
