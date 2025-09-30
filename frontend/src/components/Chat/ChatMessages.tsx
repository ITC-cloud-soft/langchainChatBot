import React, { useEffect, useRef } from 'react';
import { Box, Typography, Avatar, useTheme } from '@mui/material';
import { Chat as ChatIcon } from '@mui/icons-material';
import VirtualizedMessageList from '../VirtualizedMessageList';
import OptimizedChatMessage from '../OptimizedChatMessage';

interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
}

interface ChatMessagesProps {
  messages: ChatMessage[];
  isLoading?: boolean;
  selectedSession: any;
  useVirtualization?: boolean;
  estimatedItemSize?: number;
}

export const ChatMessages: React.FC<ChatMessagesProps> = ({
  messages = [],
  isLoading = false,
  selectedSession,
  useVirtualization = false,
  estimatedItemSize = 120,
}) => {
  const theme = useTheme();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // 自動スクロール機能
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // メッセージが変更された時に自動スクロール
  useEffect(() => {
    const timer = setTimeout(() => {
      scrollToBottom();
    }, 100); // 少し遅延させてDOM更新を待つ

    return () => clearTimeout(timer);
  }, [messages]);

  // ローディング状態が変更された時もスクロール
  useEffect(() => {
    if (!isLoading && messages.length > 0) {
      scrollToBottom();
    }
  }, [isLoading]);

  // メッセージがない場合の表示
  if (!messages || messages.length === 0) {
    return (
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: { xs: 2, sm: 3 },
          backgroundColor: 'background.default',
          backgroundImage: {
            xs: 'none',
            md: 'radial-gradient(circle at 20% 50%, rgba(14, 165, 233, 0.03) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.03) 0%, transparent 50%), radial-gradient(circle at 40% 80%, rgba(6, 214, 160, 0.02) 0%, transparent 50%)'
          },
          backgroundSize: '100% 100%, 100% 100%, 100% 100%',
          backgroundPosition: '0% 0%, 100% 0%, 50% 100%',
          backgroundRepeat: 'no-repeat',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          textAlign: 'center',
          minHeight: 0,
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.8) 0%, rgba(255, 255, 255, 0.4) 100%)',
            pointerEvents: 'none',
          },
        }}
      >
        <Avatar
          sx={{
            mb: 3,
            bgcolor: 'primary.main',
            width: { xs: 64, md: 72 },
            height: { xs: 64, md: 72 },
            boxShadow: '0 8px 32px rgba(14, 165, 233, 0.2)',
            border: '4px solid rgba(255, 255, 255, 0.8)',
            position: 'relative',
            zIndex: 1,
          }}
        >
          <ChatIcon sx={{ fontSize: { xs: 32, md: 36 } }} />
        </Avatar>

        <Typography
          variant="h5"
          color="text.primary"
          gutterBottom
          sx={{
            fontSize: { xs: '1.25rem', md: '1.5rem' },
            fontWeight: 600,
            mb: 2,
            position: 'relative',
            zIndex: 1,
          }}
        >
          会話を始めましょう
        </Typography>

        <Typography
          variant="body1"
          color="text.secondary"
          sx={{
            fontSize: { xs: '0.875rem', md: '1rem' },
            maxWidth: 400,
            lineHeight: 1.7,
            position: 'relative',
            zIndex: 1,
          }}
        >
          メッセージを送信してチャットを開始してください。AIアシスタントがお手伝いします。
        </Typography>
      </Box>
    );
  }

  // 仮想化リストを使用する場合
  if (useVirtualization) {
    return (
      <Box
        sx={{
          flex: 1,
          overflow: 'hidden',
          p: { xs: 1.5, md: 2 },
          backgroundColor: { xs: 'background.default', md: 'grey.50' },
          backgroundImage: {
            xs: 'none',
            md: 'linear-gradient(180deg, rgba(0,0,0,0.02) 0%, rgba(0,0,0,0) 100%)'
          },
          minHeight: 0,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Box sx={{ flex: 1, width: '100%', overflow: 'hidden', position: 'relative' }}>
          <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}>
            <VirtualizedMessageList
              messages={messages}
              itemSize={estimatedItemSize}
            />
          </Box>
        </Box>
      </Box>
    );
  }

  // 通常リスト
  return (
    <Box
      ref={messagesContainerRef}
      sx={{
        flex: 1,
        minHeight: 0,
        overflowY: 'auto',
        overflowX: 'hidden',
        p: { xs: 1, sm: 2, md: 3 },
        backgroundColor: 'background.default',
        backgroundImage: {
          xs: 'none',
          md: 'radial-gradient(circle at 20% 50%, rgba(14, 165, 233, 0.02) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.02) 0%, transparent 50%), radial-gradient(circle at 40% 80%, rgba(6, 214, 160, 0.01) 0%, transparent 50%)'
        },
        backgroundSize: '100% 100%, 100% 100%, 100% 100%',
        backgroundPosition: '0% 0%, 100% 0%, 50% 100%',
        backgroundRepeat: 'no-repeat',
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.6) 0%, rgba(255, 255, 255, 0.2) 100%)',
          pointerEvents: 'none',
        },
        '&::-webkit-scrollbar': {
          width: { xs: '6px', md: '10px' },
        },
        '&::-webkit-scrollbar-track': {
          background: 'rgba(0, 0, 0, 0.08)',
          borderRadius: '5px',
          margin: '4px',
        },
        '&::-webkit-scrollbar-thumb': {
          background: 'rgba(14, 165, 233, 0.5)',
          borderRadius: '5px',
          transition: 'background 0.3s ease',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          '&:hover': {
            background: 'rgba(14, 165, 233, 0.8)',
          },
          '&:active': {
            background: 'rgba(14, 165, 233, 0.9)',
          },
        },
        '&::-webkit-scrollbar-corner': {
          background: 'transparent',
        },
        scrollBehavior: 'smooth',
      }}
    >
      {messages.map((message, index) => (
        <OptimizedChatMessage
          key={`${message.timestamp}-${index}`}
          message={message}
          isLast={index === messages.length - 1}
        />
      ))}
      {/* 自動スクロール用のダミー要素 */}
      <div ref={messagesEndRef} />
    </Box>
  );
};
