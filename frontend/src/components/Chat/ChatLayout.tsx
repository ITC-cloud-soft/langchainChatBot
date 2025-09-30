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
        height: '100%',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        backgroundColor: 'background.default',
        position: 'relative',
      }}
    >
      {/* メインコンテンツエリア */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          overflow: 'hidden',
          flexDirection: 'column',
          minHeight: 0,
          position: 'relative',
        }}
      >
        {/* メインチャットエリア */}
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            minWidth: 0,
            minHeight: 0,
            height: '100%',
          }}
        >
          {/* チャットヘッダー */}
          <Box sx={{ flexShrink: 0 }}>
            {header}
          </Box>

          {/* チャットメッセージエリア */}
          <Box
            sx={{
              flex: 1,
              minHeight: 0,
              display: 'flex',
              flexDirection: 'column',
              position: 'relative',
              backgroundColor: 'background.default',
            }}
          >
            {messages}
          </Box>

          {/* 入力エリア */}
          <Box sx={{ flexShrink: 0 }}>
            {input}
          </Box>
        </Box>
      </Box>
    </Box>
  );
};
