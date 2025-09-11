import React, { useState, useEffect, useCallback, startTransition } from 'react';
import {
  Box,
  Paper,
  Drawer,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  InputAdornment,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  Close as CloseIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';

// サービスとフック
import { chatApi } from '../services/api';
import { useChatState } from '../hooks/useChatState';
import { useChatStreaming, ChatMessage } from '../hooks/useChatStreaming';
import { useChatPageState } from '../hooks/useChatPageState';
import { useChatPageHandlers } from '../hooks/useChatPageHandlers';

// コンポーネント
import { ChatLayout } from '../components/Chat/ChatLayout';
import { ChatHeader } from '../components/Chat/ChatHeader';
import { ChatMessages } from '../components/Chat/ChatMessages';
import { ChatInput } from '../components/Chat/ChatInput';
import { SessionSidebar } from '../components/Chat/SessionSidebar';
import ConfirmationDialog from '../components/common/ConfirmationDialog';

// 型定義
interface Session {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

// パフォーマンス最適化のためのユーティリティ関数
const formatTimestamp = (timestamp: string): string => {
  try {
    return new Date(timestamp).toLocaleString('ja-JP');
  } catch (error) {
    return timestamp;
  }
};

// メインのChatPageコンポーネント - リファクタリング済み
const ChatPage: React.FC = () => {
  const theme = useTheme();
  const { enqueueSnackbar } = useSnackbar();

  // レスポンシブ設定
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // 状態管理フックの使用
  const { state, actions } = useChatState();
  const { messages, sessions, selectedSession, sessionId, isLoading, isSessionsLoading, error } =
    state;

  console.log('ChatPage render:', { messages, isLoading, sessionId });

  // ストリーミング処理 - メモ化されたコールバック
  const messageUpdateCallback = useCallback(
    (updater: (prev: ChatMessage[]) => ChatMessage[]) => {
      const currentMessages = state.messages || [];
      const newMessages = updater(currentMessages);
      console.log('Message update callback:', { 
        currentMessages, 
        newMessages, 
        messageCount: newMessages.length 
      });
      actions.setMessages(newMessages);
    },
    [state.messages, actions]
  );

  const { sendMessage: sendStreamingMessage } = useChatStreaming({
    sessionId,
    onMessageUpdate: messageUpdateCallback,
    onLoadingChange: actions.setLoading,
    onUpdateLastMessage: actions.updateLastMessage,
  });

  // パフォーマンス最適化のためのフック
  const useVirtualization = messages.length > 30;
  const estimatedItemSize = 120;

  // 状態をカスタムフックに分離して再レンダリングを最小化
  const chatPageState = useChatPageState();
  const {
    inputMessage,
    setInputMessage,
    drawerOpen,
    setDrawerOpen,
    searchQuery,
    setSearchQuery,
    searchResults,
    setSearchResults,
    isSearchLoading,
    setIsSearchLoading,
    searchDialogOpen,
    setSearchDialogOpen,
    sessionDialogOpen,
    setSessionDialogOpen,
    sessionDialogTitle,
    setSessionDialogTitle,
    clearInputMessage,
    closeAllDialogs,
  } = chatPageState;

  // イベントハンドラをカスタムフックに分離
  const chatState = { state, actions };
  const handlers = useChatPageHandlers(chatPageState, chatState);
  const {
    loadSessions,
    handleCreateSession,
    handleSelectSession,
    handleUpdateSession,
    handleDeleteSession,
  } = handlers;

  // 一括削除関連の状態
  const [deleteAllDialogOpen, setDeleteAllDialogOpen] = useState(false);

  const handleDeleteAllSessions = useCallback(async () => {
    try {
      const response = await chatApi.deleteAllSessions();
      if (response.success) {
        enqueueSnackbar(`${response.data.deleted_sessions}件のセッションを削除しました`, {
          variant: 'success'
        });
        // セッションリストをクリア
        actions.setSessions([]);
        // 選択中のセッションもクリア
        actions.setSelectedSession(null);
        // メッセージもクリア
        actions.setMessages([]);
      } else {
        enqueueSnackbar('セッションの削除に失敗しました', { variant: 'error' });
      }
    } catch (error: any) {
      console.error('Error deleting all sessions:', error);
      enqueueSnackbar('セッションの削除に失敗しました', { variant: 'error' });
    }
    setDeleteAllDialogOpen(false);
  }, [actions, enqueueSnackbar]);

  // メッセージ追加時のスクロール処理 - パフォーマンス改善
  useEffect(() => {
    const safeMessages = Array.isArray(messages) ? messages : [];
    // スクロール処理は各コンポーネント内で管理
  }, [messages]);

  // メッセージ送信処理 - メモ化とパフォーマンス改善
  const handleSendMessage = useCallback(async () => {
    if (!inputMessage?.trim()) return;

    console.log('Sending message:', inputMessage);
    const messageToSend = inputMessage;
    
    // 送信前に入力をクリア
    clearInputMessage();

    try {
      await sendStreamingMessage(messageToSend);
      console.log('Message sent successfully');
    } catch (error) {
      console.error('Error sending message:', error);
      // エラー時は入力を復元
      setInputMessage(messageToSend);
    }
  }, [inputMessage, sendStreamingMessage, clearInputMessage, setInputMessage]);

  // セッション検索処理
  const handleSearchLocal = useCallback(async () => {
    if (!searchQuery?.trim()) return;

    setIsSearchLoading(true);
    try {
      const response = await chatApi.searchChatHistory(searchQuery, 1, 20);
      if (response.success) {
        setSearchResults(response.data.results || []);
      } else {
        enqueueSnackbar('検索に失敗しました', { variant: 'error' });
      }
    } catch (error) {
      console.error('Search error:', error);
      enqueueSnackbar('検索に失敗しました', { variant: 'error' });
    } finally {
      setIsSearchLoading(false);
    }
  }, [searchQuery, enqueueSnackbar]);

  // コンポーネントマウント時に初期化
  useEffect(() => {
    const initializeSessions = async () => {
      try {
        const response = await chatApi.getSessions(1, 50);
        if (response.success) {
          const sessions = response.data.sessions || [];
          actions.setSessions(sessions);
        }
      } catch (error) {
        console.error('Failed to initialize sessions:', error);
      }
    };

    initializeSessions();
    actions.setSessionId(`session_${Date.now()}`);
  }, []);

  return (
    <Box
      sx={{
        height: '100vh',
        maxHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'background.default',
        overflow: 'hidden',
      }}
    >
      <ChatLayout
        isMobile={isMobile}
        header={
          <ChatHeader
            selectedSession={selectedSession}
            isMobile={isMobile}
            onMobileMenuClick={() => setDrawerOpen(true)}
          />
        }
        messages={
          <ChatMessages
            messages={messages}
            isLoading={isLoading}
            selectedSession={selectedSession}
            useVirtualization={useVirtualization}
            estimatedItemSize={estimatedItemSize}
          />
        }
        input={
          <ChatInput
            value={inputMessage}
            onChange={setInputMessage}
            onSend={handleSendMessage}
            isLoading={isLoading}
            placeholder="メッセージを入力してください..."
          />
        }
      />

      {/* モバイル用サイドドロワー */}
      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        PaperProps={{
          sx: {
            width: { xs: 280, sm: 320 },
            backgroundImage: 'linear-gradient(180deg, rgba(0,0,0,0.01) 0%, rgba(0,0,0,0) 100%)',
          },
        }}
      >
        <Box sx={{ p: 2 }}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 3,
              pb: 2,
              borderBottom: 1,
              borderColor: 'divider'
            }}
          >
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              メニュー
            </Typography>
            <Button
              onClick={() => setDrawerOpen(false)}
              sx={{ minWidth: 'auto', p: 1 }}
            >
              <CloseIcon />
            </Button>
          </Box>

          <SessionSidebar
            sessions={sessions}
            selectedSession={selectedSession}
            onSessionSelect={(session) => {
              handleSelectSession(session);
              setDrawerOpen(false);
            }}
            onSessionCreate={handleCreateSession}
            onSessionDelete={handleDeleteSession}
            onSessionUpdate={handleUpdateSession}
            onDeleteAllSessions={() => setDeleteAllDialogOpen(true)}
            isLoading={isSessionsLoading}
          />
        </Box>
      </Drawer>

      {/* 新規セッション作成ダイアログ */}
      <Dialog
        open={sessionDialogOpen}
        onClose={() => setSessionDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>新しいセッションを作成</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <TextField
              fullWidth
              value={sessionDialogTitle}
              onChange={(e) => setSessionDialogTitle(e.target.value)}
              placeholder="セッションのタイトルを入力してください"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSessionDialogOpen(false)}>キャンセル</Button>
          <Button
            onClick={handleCreateSession}
            variant="contained"
          >
            作成
          </Button>
        </DialogActions>
      </Dialog>

      {/* 検索ダイアログ */}
      <Dialog
        open={searchDialogOpen}
        onClose={() => setSearchDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>チャット履歴を検索</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <TextField
              fullWidth
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleSearchLocal();
                }
              }}
              placeholder="検索キーワードを入力してください"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <Button onClick={handleSearchLocal} disabled={isSearchLoading}>
                      検索
                    </Button>
                  </InputAdornment>
                ),
              }}
            />
          </Box>

          {/* 検索結果表示部分は省略（必要に応じて実装） */}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSearchDialogOpen(false)}>閉じる</Button>
        </DialogActions>
      </Dialog>

      {/* 一括削除確認ダイアログ */}
      <ConfirmationDialog
        open={deleteAllDialogOpen}
        title="全てのセッションを削除"
        message={`${sessions.length}件のセッションと関連する全てのメッセージが削除されます。この操作は元に戻せません。`}
        confirmText="全て削除"
        cancelText="キャンセル"
        confirmColor="error"
        onConfirm={handleDeleteAllSessions}
        onCancel={() => setDeleteAllDialogOpen(false)}
      />
    </Box>
  );
};

export default ChatPage;
