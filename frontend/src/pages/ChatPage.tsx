import React, { useState, useEffect, memo, useCallback, startTransition } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  CircularProgress,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  AppBar,
  Toolbar,
  Badge,
  Menu,
  MenuItem,
  Card,
  CardContent,
  Grid,
  FormControl,
  InputLabel,
  Select,
  OutlinedInput,
  InputAdornment,
  Tabs,
  Tab,
  Fab,
  useTheme,
  useMediaQuery,
  Avatar,
  alpha,
  ListItemIcon,
  Tooltip,
} from '@mui/material';
import {
  Send as SendIcon,
  ExpandMore as ExpandMoreIcon,
  Source as SourceIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Add as AddIcon,
  Search as SearchIcon,
  Download as DownloadIcon,
  BarChart as BarChartIcon,
  FilterList as FilterListIcon,
  Close as CloseIcon,
  Save as SaveIcon,
  MoreVert as MoreVertIcon,
  Menu as MenuIcon,
  Chat as ChatIcon,
  Folder as FolderIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';

import { chatApi } from '../services/api';
import SessionCard from '../components/SessionCard';
import VirtualizedMessageList from '../components/VirtualizedMessageList';
import OptimizedChatMessage from '../components/OptimizedChatMessage';
import ChatInput from '../components/ChatInput';
import { useChatState } from '../hooks/useChatState';
import { useChatStreaming, ChatMessage } from '../hooks/useChatStreaming';
import { useScroll } from '../hooks/useScroll';
import { useResponsive, useResponsiveLayout } from '../hooks/useResponsive';
import { useChatPageState } from '../hooks/useChatPageState';
import { useChatPageHandlers } from '../hooks/useChatPageHandlers';
import ConfirmationDialog from '../components/common/ConfirmationDialog';

// パフォーマンス最適化のためのユーティリティ関数
const formatTimestamp = (timestamp: string): string => {
  try {
    return new Date(timestamp).toLocaleString('ja-JP');
  } catch (error) {
    return timestamp;
  }
};

// 画面サイズに基づいて動的な高さを計算するフック
const useDynamicHeight = () => {
  const [heights, setHeights] = useState({
    chatHeader: 60, // デフォルト値
    chatInput: 120, // デフォルト値を増加
    availableHeight: window.innerHeight,
  });

  useEffect(() => {
    const updateHeights = () => {
      // より正確な高さ取得のため、少し遅延して実行
      requestAnimationFrame(() => {
        const chatHeader = document.querySelector('[data-chat-header]')?.clientHeight || 70;
        const chatInput = document.querySelector('[data-chat-input]')?.clientHeight || 120;
        
        setHeights(prev => ({
          chatHeader,
          chatInput,
          availableHeight: window.innerHeight,
        }));
      });
    };

    // 初回実行
    updateHeights();

    // ウィンドウサイズ変更時に更新
    window.addEventListener('resize', updateHeights);
    
    // DOM変更を監視（よりターゲットを絞って）
    const observer = new MutationObserver(updateHeights);
    observer.observe(document.querySelector('[data-chat-header]')?.parentElement || document.body, {
      childList: true,
      subtree: true,
      attributes: true,
    });

    return () => {
      window.removeEventListener('resize', updateHeights);
      observer.disconnect();
    };
  }, []);

  // 1画面に収まるように調整 - より適切な高さ計算
  // ヘッダー、入力エリア、余白を考慮して残りの高さを計算
  const reservedHeight = heights.chatHeader + heights.chatInput + 40; // 余白を増加
  const maxMessagesHeight = Math.max(300, heights.availableHeight - reservedHeight);
  const messagesAreaHeight = Math.min(maxMessagesHeight, heights.availableHeight * 0.75); // 画面の75%を上限に変更

  return {
    messagesAreaHeight,
    chatHeaderHeight: heights.chatHeader,
    chatInputHeight: heights.chatInput,
  };
};

// メモ化されたセッション管理コンポーネント
const SessionManager = memo(
  ({
    sessions,
    selectedSession,
    onSessionSelect,
    onSessionCreate,
    onSessionDelete,
    onSessionUpdate,
    onDeleteAllSessions,
    isLoading,
  }: {
    sessions: any[];
    selectedSession: any | null;
    onSessionSelect: (session: any) => void;
    onSessionCreate: () => void;
    onSessionDelete: (session: any) => void;
    onSessionUpdate: (session: any, title: string) => void;
    onDeleteAllSessions: () => void;
    isLoading: boolean;
  }) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [sortBy, setSortBy] = useState<'updated' | 'created' | 'title'>('updated');

    // メモ化されたフィルタリングとソート - パフォーマンス改善
    const filteredSessions = React.useMemo(() => {
      if (!Array.isArray(sessions)) return [];

      const query = searchQuery.toLowerCase();
      return sessions
        .filter(
          session =>
            !query ||
            session.title?.toLowerCase().includes(query) ||
            session.session_id.toLowerCase().includes(query),
        )
        .sort((a, b) => {
          switch (sortBy) {
            case 'updated':
              return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
            case 'created':
              return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
            case 'title':
              return (a.title || '').localeCompare(b.title || '');
            default:
              return 0;
          }
        });
    }, [sessions, searchQuery, sortBy]);

    return (
      <Box 
        data-session-manager
        sx={{ 
          height: '100%', 
          maxHeight: '100%',
          display: 'flex', 
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
        {/* ヘッダー */}
        <Box sx={{ 
          p: 2, 
          borderBottom: 1, 
          borderColor: 'divider', 
          bgcolor: 'background.paper',
          flexShrink: 0,
          height: 'auto',
          maxHeight: '120px'
        }}>
          {/* 一段目：チャット履歴タイトル */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <HistoryIcon sx={{ mr: 1 }} />
          <Typography
            variant="h6"
            sx={{ fontWeight: 'bold' }}
          >
            チャット履歴
          </Typography>
          <Chip
            label={sessions.length}
            size="small"
            sx={{ ml: 1, fontSize: '0.75rem', height: 20 }}
          />
        </Box>

        {/* 二段目：ボタン群 */}
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mb: 2 }}>
          <Button
            onClick={onSessionCreate}
            variant="contained"
            size="small"
            startIcon={<AddIcon />}
            sx={{ fontSize: '0.8rem' }}
          >
            セッション作成
          </Button>
          {sessions.length > 0 && (
            <Button
              onClick={onDeleteAllSessions}
              variant="outlined"
              size="small"
              color="error"
              startIcon={<DeleteIcon />}
              sx={{ fontSize: '0.8rem' }}
            >
              全て削除
            </Button>
          )}
        </Box>

          {/* 検索とソート */}
          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
            <TextField
              fullWidth
              size="small"
              placeholder="セッションを検索..."
              variant="outlined"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
              }}
            />
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>並び替え</InputLabel>
              <Select
                value={sortBy}
                label="並び替え"
                onChange={e => setSortBy(e.target.value as any)}
              >
                <MenuItem value="updated">更新日時</MenuItem>
                <MenuItem value="created">作成日時</MenuItem>
                <MenuItem value="title">タイトル</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Box>

        {/* セッションリスト */}
        <Box 
          data-session-list
          sx={{ 
            flexGrow: 1, 
            overflow: 'auto', 
            p: 1, 
            height: 'auto',
            minHeight: 0,
            maxHeight: 'none',
            flexShrink: 1,
            '&::-webkit-scrollbar': {
              width: '8px',
            },
            '&::-webkit-scrollbar-track': {
              background: 'rgba(0, 0, 0, 0.1)',
              borderRadius: '4px',
            },
            '&::-webkit-scrollbar-thumb': {
              background: 'rgba(0, 0, 0, 0.4)',
              borderRadius: '4px',
              '&:hover': {
                background: 'rgba(0, 0, 0, 0.6)',
              },
            },
          }}>
          {isLoading ? (
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100%',
              }}
            >
              <CircularProgress />
            </Box>
          ) : filteredSessions.length === 0 ? (
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100%',
                textAlign: 'center',
                p: 3,
              }}
            >
              <HistoryIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {searchQuery ? '検索結果がありません' : 'セッションがありません'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {searchQuery ? '別のキーワードで検索してください' : '新しいチャットを始めましょう'}
              </Typography>
              {!searchQuery && (
                <Button
                  onClick={onSessionCreate}
                  variant="contained"
                  sx={{ mt: 2 }}
                  startIcon={<AddIcon />}
                >
                  セッションを作成
                </Button>
              )}
            </Box>
          ) : (
            <Box sx={{ display: 'grid', gap: 2 }}>
              {filteredSessions.map(session => (
                <SessionCard
                  key={session.session_id}
                  session={session}
                  isSelected={selectedSession?.session_id === session.session_id}
                  onSelect={onSessionSelect}
                  onUpdate={onSessionUpdate}
                  onDelete={onSessionDelete}
                />
              ))}
            </Box>
          )}
        </Box>
      </Box>
    );
  },
);

SessionManager.displayName = 'SessionManager';

// パフォーマンス最適化のためのメモ化されたコンポーネント
const useOptimizedRendering = (messages: any[]) => {
  return React.useMemo(() => {
    const safeMessages = Array.isArray(messages) ? messages : [];
    return {
      useVirtualization: safeMessages.length > 30, // 30メッセージ以上で仮想化
      estimatedItemSize: 120,
    };
  }, [messages.length]);
};

// メインのChatPageコンポーネント - パフォーマンス最適化
const ChatPage: React.FC = () => {
  const theme = useTheme();
  const { enqueueSnackbar } = useSnackbar();

  // レスポンシブ設定
  const responsive = useResponsive();
  const { layout } = useResponsiveLayout();
  const { isMobile, fontSize, padding, borderRadius, spacing } = responsive;


  // 状態管理フックの使用
  const { state, actions } = useChatState();
  const { messages, sessions, selectedSession, sessionId, isLoading, isSessionsLoading, error } =
    state;

  // スクロール管理
  const { containerRef, scrollToBottomIfNeeded } = useScroll({ threshold: 100 });

  // ストリーミング処理 - メモ化されたコールバック
  const messageUpdateCallback = useCallback(
    (updater: (prev: ChatMessage[]) => ChatMessage[]) => {
      const currentMessages = state.messages || [];
      const newMessages = updater(currentMessages);
      actions.setMessages(newMessages);
    },
    [actions, state.messages],
  );

  const { sendMessage: sendStreamingMessage } = useChatStreaming({
    sessionId,
    onMessageUpdate: messageUpdateCallback,
    onLoadingChange: actions.setLoading,
    onUpdateLastMessage: actions.updateLastMessage,
  });

  // パフォーマンス最適化のためのフック
  const { useVirtualization, estimatedItemSize } = useOptimizedRendering(messages);

  // 動的高さ計算フック
  const { messagesAreaHeight } = useDynamicHeight();

  // 状態をカスタムフックに分離して再レンダリングを最小化
  const chatPageState = useChatPageState();
  const {
    inputMessage,
    setInputMessage,
    activeTab,
    setActiveTab,
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

  // 一括削除関連の状態
  const [deleteAllDialogOpen, setDeleteAllDialogOpen] = useState(false);

  // イベントハンドラをカスタムフックに分離
  const chatState = { state, actions };
  const handlers = useChatPageHandlers(chatPageState, chatState);
  const {
    loadSessions,
    handleCreateSession,
    handleSelectSession,
    handleUpdateSession,
    handleDeleteSession,
        handleNavigationChange,
  } = handlers;

  // 一括削除ハンドラー
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

  // ナビゲーションアイテムのメモ化 - パフォーマンス改善
  const navigationItems = React.useMemo(() => {
    const sessionCount = Array.isArray(sessions) ? sessions.length : 0;
    return [
      { id: 'chat', label: 'チャット', icon: <ChatIcon /> },
      { id: 'history', label: '履歴', icon: <HistoryIcon />, badge: sessionCount },
    ];
  }, [sessions]);

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

  // セッションが変更されても特に何もしない（自動タイトル生成機能を削除）

  // メッセージ追加時のスクロール処理 - パフォーマンス改善
  useEffect(() => {
    const safeMessages = Array.isArray(messages) ? messages : [];
    scrollToBottomIfNeeded(safeMessages.length);
  }, [messages, scrollToBottomIfNeeded]);


  // メッセージ送信処理 - メモ化とパフォーマンス改善
  const handleSendMessage = useCallback(async () => {
    if (!inputMessage?.trim()) return;

    try {
      await sendStreamingMessage(inputMessage);
      clearInputMessage();
    } catch (error) {
      console.error('Error sending message:', error);
    }
  }, [inputMessage, sendStreamingMessage, clearInputMessage]);

  // ナビゲーションの変更を処理 - パフォーマンス改善
  const handleNavigationChangeLocal = useCallback(
    (tabId: string) => {
      handleNavigationChange(tabId, isMobile);
    },
    [handleNavigationChange, isMobile],
  );

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

  return (
    <Box
      sx={{
        height: '80vh',
        maxHeight: '80vh',
        minHeight: '80vh',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.default',
        overflow: 'hidden',
        position: 'relative',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        borderRadius: 0,
      }}
    >
  
      {/* メインコンテンツエリア - レスポンシブ対応 */}
      <Box
        sx={{
          flexGrow: 1,
          display: 'flex',
          overflow: 'hidden',
          flexDirection: { xs: 'column', md: 'row' },
          height: '100%',
          maxHeight: '100%',
          minHeight: 0,
          flexShrink: 0,
        }}
      >
        {/* サイドナビゲーション (デスクトップ) */}
        {!isMobile && (
          <Box
            sx={{
              width: 'clamp(280px, 25vw, 400px)',
              borderRight: 1,
              borderColor: 'divider',
              display: 'flex',
              flexDirection: 'column',
              bgcolor: 'background.paper',
              transition: 'width 0.3s ease',
              height: '100%',
              maxHeight: '100%',
              minHeight: 0,
              overflow: 'hidden',
              flexShrink: 0,
            }}
          >
            <SessionManager
              sessions={sessions}
              selectedSession={selectedSession}
              onSessionSelect={handleSelectSession}
              onSessionCreate={handleCreateSession}
              onSessionDelete={handleDeleteSession}
              onSessionUpdate={handleUpdateSession}
              onDeleteAllSessions={() => setDeleteAllDialogOpen(true)}
              isLoading={isSessionsLoading}
            />
          </Box>
        )}

        {/* メインチャットエリア */}
        <Box
          sx={{
            flexGrow: 1,
            display: 'flex',
            flexDirection: 'column',
            minWidth: 0,
            height: '100%',
            maxHeight: '100%',
            overflow: 'hidden',
            flexShrink: 0,
          }}
        >
          <Paper
            elevation={0}
            sx={{
              flexGrow: 1,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              bgcolor: 'background.default',
              borderRadius: { xs: 0, md: 2 },
              border: { xs: 'none', md: 1 },
              borderColor: 'divider',
              height: '100%',
            }}
          >
            {/* チャットヘッダー - レスポンシブ対応 */}
            <Box
              data-chat-header
              sx={{
                p: { xs: 1, md: padding('small') },
                borderBottom: 1,
                borderColor: 'divider',
                bgcolor: 'background.paper',
                backdropFilter: 'blur(10px)',
                flexShrink: 0, // 高さを固定
                minHeight: { xs: '45px', md: '55px' }, // 最小高さを設定
                height: 'auto', // コンテンツに合わせて高さを調整
                maxHeight: '70px', // 最大高さを制限
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: 1,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0 }}>
                  <Typography
                    variant="subtitle1"
                    sx={{
                      fontSize: fontSize('medium'),
                      fontWeight: 'medium',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {selectedSession
                      ? selectedSession.title || '無題のセッション'
                      : '新しいチャット'}
                  </Typography>
                  {selectedSession && (
                    <Chip
                      label={selectedSession.is_active ? 'アクティブ' : '非アクティブ'}
                      size="small"
                      color={selectedSession.is_active ? 'success' : 'default'}
                      sx={{ fontSize: '0.7rem', height: 20 }}
                    />
                  )}
                </Box>
                {isMobile && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 0.5, sm: 1 } }}>
                    <Tooltip title="履歴">
                      <IconButton
                        onClick={() => setDrawerOpen(true)}
                        size="small"
                        sx={{ p: { xs: 0.75, sm: 1 } }}
                      >
                        <HistoryIcon sx={{ fontSize: { xs: '1.2rem', sm: '1.5rem' } }} />
                      </IconButton>
                    </Tooltip>
                  </Box>
                )}
              </Box>
            </Box>

            {/* チャットメッセージエリア - レスポンシブ対応 & パフォーマンス最適化 */}
            <Box
              ref={containerRef}
              data-chat-messages
              sx={{
                flex: 1, // 残りのスペースを自動的に割り当て
                overflow: 'auto',
                p: padding('small'),
                backgroundColor: isMobile ? 'background.default' : 'grey.50',
                backgroundImage: isMobile
                  ? 'none'
                  : 'linear-gradient(180deg, rgba(0,0,0,0.02) 0%, rgba(0,0,0,0) 100%)',
                minHeight: 0,
                '&::-webkit-scrollbar': {
                  width: '10px',
                },
                '&::-webkit-scrollbar-track': {
                  background: 'rgba(0, 0, 0, 0.1)',
                  borderRadius: '5px',
                },
                '&::-webkit-scrollbar-thumb': {
                  background: 'rgba(0, 0, 0, 0.4)',
                  borderRadius: '5px',
                  '&:hover': {
                    background: 'rgba(0, 0, 0, 0.6)',
                  },
                },
              }}
            >
              {!Array.isArray(messages) || messages.length === 0 ? (
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center',
                    height: '100%',
                    textAlign: 'center',
                    p: { xs: 2, sm: 4 },
                  }}
                >
                  <Avatar
                    sx={{
                      mb: spacing(2),
                      bgcolor: 'primary.main',
                      width: isMobile ? 56 : 64,
                      height: isMobile ? 56 : 64,
                      boxShadow: 3,
                    }}
                  >
                    <ChatIcon sx={{ fontSize: fontSize('large') }} />
                  </Avatar>
                  <Typography
                    variant="h6"
                    color="text.secondary"
                    gutterBottom
                    sx={{ fontSize: fontSize('medium') }}
                  >
                    会話を始めましょう
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ fontSize: fontSize('small'), maxWidth: 400 }}
                  >
                    メッセージを送信してチャットを開始してください
                  </Typography>
                  {isMobile && (
                    <Button
                      variant="outlined"
                      onClick={() => setDrawerOpen(true)}
                      sx={{ mt: 3 }}
                      startIcon={<HistoryIcon />}
                    >
                      履歴から選択
                    </Button>
                  )}
                </Box>
              ) : useVirtualization ? (
                // 仮想化リスト（大量のメッセージ用）
                <Box sx={{ height: '100%', width: '100%' }}>
                  <VirtualizedMessageList
                    messages={messages}
                    itemSize={estimatedItemSize}
                    height={600}
                    width="100%"
                  />
                </Box>
              ) : (
                // 通常リスト（少量のメッセージ用）
                <Box sx={{ maxWidth: '100%', overflow: 'auto', height: '100%' }}>
                  {messages.map((message, index) => (
                    <OptimizedChatMessage
                      key={`${message.timestamp}-${index}`}
                      message={message}
                      isLast={index === messages.length - 1}
                    />
                  ))}
                </Box>
              )}
            </Box>

            {/* 入力エリア - レスポンシブ対応 & パフォーマンス最適化 */}
            <Divider />
            <Box
              data-chat-input
              sx={{
                flexShrink: 0,
                height: '70px',
                minHeight: '70px',
                maxHeight: '70px',
                overflow: 'hidden',
                borderTop: 1,
                borderColor: 'divider',
                bgcolor: 'background.paper',
              }}
            >
              <ChatInput
                inputMessage={inputMessage}
                setInputMessage={setInputMessage}
                onSendMessage={handleSendMessage}
                isLoading={isLoading}
                isMobile={isMobile}
                spacing={spacing}
                borderRadius={borderRadius}
                fontSize={fontSize}
                padding={padding}
              />
            </Box>
          </Paper>
        </Box>
      </Box>

      {/* モバイル用サイドドロワー - レスポンシブ対応 */}
      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        PaperProps={{
          sx: {
            width: { xs: 260, sm: 280 },
            backgroundImage: 'linear-gradient(180deg, rgba(0,0,0,0.01) 0%, rgba(0,0,0,0) 100%)',
          },
        }}
      >
        <Box sx={{ p: { xs: 1.5, sm: 2 } }}>
          <Box
            sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}
          >
            <Typography
              variant="h6"
              sx={{
                fontWeight: 'bold',
                fontSize: { xs: '1.1rem', sm: '1.25rem' },
              }}
            >
              メニュー
            </Typography>
            <IconButton onClick={() => setDrawerOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Box>

          {/* ユーザー情報エリア */}
          <Box
            sx={{ mb: 3, p: 2, bgcolor: alpha(theme.palette.primary.main, 0.05), borderRadius: 2 }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar sx={{ width: 40, height: 40, bgcolor: 'primary.main' }}>
                <PersonIcon />
              </Avatar>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                  ユーザー
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  オンライン
                </Typography>
              </Box>
            </Box>
          </Box>

          {/* ナビゲーションアイテム */}
          <List>
            {navigationItems.map(item => (
              <ListItem
                key={item.id}
                button
                selected={activeTab === item.id}
                onClick={() => handleNavigationChangeLocal(item.id)}
                sx={{
                  borderRadius: 2,
                  mb: 0.5,
                  transition: 'all 0.2s ease',
                  '&.Mui-selected': {
                    backgroundColor: alpha(theme.palette.primary.main, 0.1),
                    color: 'primary.main',
                    borderLeft: '3px solid',
                    borderColor: 'primary.main',
                  },
                  '&:hover': {
                    backgroundColor: alpha(theme.palette.primary.main, 0.05),
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  <Box sx={{ color: activeTab === item.id ? 'primary.main' : 'inherit' }}>
                    {item.icon}
                  </Box>
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{
                    fontSize: '0.95rem',
                    fontWeight: activeTab === item.id ? 'medium' : 'normal',
                  }}
                />
                {item.badge !== undefined && (
                  <Badge badgeContent={item.badge} color="secondary" sx={{ ml: 1 }} />
                )}
              </ListItem>
            ))}
          </List>
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
          <TextField
            autoFocus
            margin="dense"
            label="タイトル"
            fullWidth
            variant="outlined"
            value={sessionDialogTitle}
            onChange={e => setSessionDialogTitle(e.target.value)}
            placeholder="セッションのタイトルを入力してください"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSessionDialogOpen(false)}>キャンセル</Button>
          <Button onClick={handleCreateSession} variant="contained">
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
              onChange={e => setSearchQuery(e.target.value)}
              onKeyPress={e => {
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

          {isSearchLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : searchResults && Array.isArray(searchResults) && searchResults.length > 0 ? (
            <List>
              {searchResults.map((result, index) => (
                <ListItem
                  key={index}
                  button
                  onClick={() => {
                    if (result.session) {
                      handleSelectSession(result.session);
                      setSearchDialogOpen(false);
                    }
                  }}
                  sx={{
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    mb: 1,
                  }}
                >
                  <ListItemText
                    primary={
                      <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                        {result.message.content.substring(0, 100)}
                        {result.message.content.length > 100 ? '...' : ''}
                      </Typography>
                    }
                    secondary={
                      <Typography variant="caption" color="text.secondary">
                        {result.session.title || '無題'} -{' '}
                        {new Date(result.message.timestamp).toLocaleDateString('ja-JP')}
                      </Typography>
                    }
                  />
                </ListItem>
              ))}
            </List>
          ) : searchQuery ? (
            <Typography variant="body2" color="text.secondary" sx={{ p: 2, textAlign: 'center' }}>
              検索結果がありません
            </Typography>
          ) : (
            <Typography variant="body2" color="text.secondary" sx={{ p: 2, textAlign: 'center' }}>
              キーワードを入力して検索してください
            </Typography>
          )}
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

      {/* グローバルスタイル */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        /* 親画面スクロール完全禁止 */
        body, html {
          overflow: hidden !important;
          height: 100vh !important;
          max-height: 100vh !important;
          margin: 0 !important;
          padding: 0 !important;
        }
        
        /* 全体のページレイアウトを画面全体に */
        #root {
          height: 100vh !important;
          max-height: 100vh !important;
          overflow: hidden !important;
          margin: 0 !important;
          padding: 0 !important;
        }
        
        /* チャットページ全体の高さを画面全体に */
        .MuiBox-root {
          max-height: 100vh !important;
          overflow: hidden !important;
        }
        
        /* SessionManagerの高さ制限を緩和 */
        [data-session-manager] {
          height: 100% !important;
          max-height: 100% !important;
          overflow: hidden !important;
          display: flex !important;
          flex-direction: column !important;
        }
        
        /* セッションリストの高さ制限を緩和（個別スクロール） */
        [data-session-list] {
          height: auto !important;
          max-height: none !important;
          overflow-y: auto !important;
          overflow-x: hidden !important;
          flex-shrink: 1 !important;
          flex-grow: 1 !important;
        }
        
        /* チャットメッセージエリアの高さ制限（個別スクロール） */
        [data-chat-messages] {
          height: auto !important;
          flex: 1 !important; /* 残りのスペースを自動的に割り当て */
          overflow-y: auto !important;
          overflow-x: hidden !important;
          flex-shrink: 1 !important;
          flex-grow: 1 !important;
        }
        
        /* 入力エリアの高さを適切に設定 */
        [data-chat-input] {
          height: auto !important;
          max-height: 120px !important;
          min-height: 80px !important;
          flex-shrink: 0 !important;
          overflow: hidden !important;
          border-top: 1px solid rgba(0, 0, 0, 0.12) !important;
          background-color: rgba(255, 255, 255, 0.98) !important;
        }
        
        /* Material-UIコンテナの高さ制限を画面全体に */
        .MuiPaper-root {
          max-height: 100vh !important;
          overflow: hidden !important;
        }
      `}</style>
    </Box>
  );
};

export default ChatPage;
