import React from 'react';
import { Box } from '@mui/material';

interface ChatLayoutProps {
  sidebar?: React.ReactNode;
  header: React.ReactNode;
  messages: React.ReactNode;
  input: React.ReactNode;
  isMobile: boolean;
}

export const ChatLayout: React.FC<ChatLayoutProps> = ({
  sidebar,
  header,
  messages,
  input,
  isMobile,
}) => {
  return (
    <Box
      sx={{
        height: '100vh',
        maxHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        backgroundColor: 'background.default',
      }}
    >
      {/* メインコンテンツエリア */}
      <Box
        sx={{
          flexGrow: 1,
          display: 'flex',
          overflow: 'hidden',
          flexDirection: 'column',
          height: '100%',
          maxHeight: '100%',
          minHeight: 0,
          flexShrink: 0,
        }}
      >
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
          {/* チャットヘッダー */}
          {header}

          {/* チャットメッセージエリア */}
          {messages}

          {/* 入力エリア */}
          {input}
        </Box>
      </Box>
    </Box>
  );
};
