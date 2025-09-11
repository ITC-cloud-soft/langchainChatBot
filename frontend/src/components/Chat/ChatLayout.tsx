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
        maxHeight: 'calc(100vh - 0px)',
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
          minHeight: 0,
        }}
      >
        {/* メインチャットエリア */}
        <Box
          sx={{
            flexGrow: 1,
            display: 'flex',
            flexDirection: 'column',
            minWidth: 0,
            minHeight: 0,
          }}
        >
          {/* チャットヘッダー */}
          <Box sx={{ flexShrink: 0 }}>
            {header}
          </Box>

          {/* チャットメッセージエリア */}
          <Box sx={{ flexGrow: 1, minHeight: 0, pb: 0 }}>
            {messages}
          </Box>

          {/* 入力エリア */}
          <Box sx={{ flexShrink: 0, pb: 0 }}>
            {input}
          </Box>
        </Box>
      </Box>
    </Box>
  );
};
