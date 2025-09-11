import React from 'react';
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

  // メッセージがない場合の表示
  if (!messages || messages.length === 0) {
    return (
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: { xs: 2, sm: 4 },
          backgroundColor: { xs: 'background.default', md: 'grey.50' },
          backgroundImage: {
            xs: 'none',
            md: 'linear-gradient(180deg, rgba(0,0,0,0.02) 0%, rgba(0,0,0,0) 100%)'
          },
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          textAlign: 'center',
          minHeight: 0,
        }}
      >
        <Avatar
          sx={{
            mb: 3,
            bgcolor: 'primary.main',
            width: { xs: 56, md: 64 },
            height: { xs: 56, md: 64 },
            boxShadow: theme.shadows[3],
          }}
        >
          <ChatIcon sx={{ fontSize: { xs: 28, md: 32 } }} />
        </Avatar>

        <Typography
          variant="h6"
          color="text.secondary"
          gutterBottom
          sx={{
            fontSize: { xs: '1.1rem', md: '1.25rem' },
            fontWeight: 500,
            mb: 2,
          }}
        >
          会話を始めましょう
        </Typography>

        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            fontSize: { xs: '0.875rem', md: '1rem' },
            maxWidth: 400,
            lineHeight: 1.6,
          }}
        >
          メッセージを送信してチャットを開始してください
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
          p: { xs: 2, md: 3 },
          backgroundColor: { xs: 'background.default', md: 'grey.50' },
          backgroundImage: {
            xs: 'none',
            md: 'linear-gradient(180deg, rgba(0,0,0,0.02) 0%, rgba(0,0,0,0) 100%)'
          },
          minHeight: 0,
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
        }}
      >
        <Box sx={{ height: '100%', width: '100%' }}>
          <VirtualizedMessageList
            messages={messages}
            itemSize={estimatedItemSize}
            height={600}
            width="100%"
          />
        </Box>
      </Box>
    );
  }

  // 通常リスト
  return (
    <Box
      sx={{
        flex: 1,
        overflow: 'auto',
        p: { xs: 2, md: 3 },
        backgroundColor: { xs: 'background.default', md: 'grey.50' },
        backgroundImage: {
          xs: 'none',
          md: 'linear-gradient(180deg, rgba(0,0,0,0.02) 0%, rgba(0,0,0,0) 100%)'
        },
        minHeight: 0,
        maxWidth: '100%',
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
      }}
    >
      <Box sx={{ maxWidth: '100%', overflow: 'auto', height: '100%' }}>
        {messages.map((message, index) => (
          <OptimizedChatMessage
            key={`${message.timestamp}-${index}`}
            message={message}
            isLast={index === messages.length - 1}
          />
        ))}

      </Box>
    </Box>
  );
};
