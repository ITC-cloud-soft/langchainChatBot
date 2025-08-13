import React, { memo } from 'react';
import { Box, TextField, Button, Typography, CircularProgress, Chip } from '@mui/material';
import { Send as SendIcon, Search as SearchIcon } from '@mui/icons-material';

interface ChatInputProps {
  inputMessage: string;
  setInputMessage: (message: string) => void;
  onSendMessage: () => void;
  isLoading: boolean;
  isMobile: boolean;
  spacing: (factor: number, factor2?: number) => string;
  borderRadius: (size: "small" | "medium" | "large") => number;
  fontSize: (size: "small" | "medium" | "large") => string;
  padding: (size: "small" | "medium" | "large") => number;
}

const ChatInput: React.FC<ChatInputProps> = memo(
  ({
    inputMessage,
    setInputMessage,
    onSendMessage,
    isLoading,
    isMobile,
    spacing,
    borderRadius,
    fontSize,
    padding,
  }) => {
    const handleKeyPress = React.useCallback(
      (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          onSendMessage();
        }
      },
      [onSendMessage],
    );

    return (
      <Box
        data-chat-input
        sx={{
          p: padding('small'),
          backgroundColor: 'background.paper',
          borderTop: '1px solid',
          borderColor: 'divider',
          flexShrink: 0, // 高さを固定
          minHeight: '80px', // 最小高さを設定
          maxHeight: '120px', // 最大高さを制限
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-end',
            gap: spacing(0.5),
            flexDirection: isMobile ? 'column' : 'row',
          }}
        >
          <TextField
            fullWidth
            multiline
            maxRows={isMobile ? 3 : 4}
            value={inputMessage}
            onChange={e => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="メッセージを入力してください..."
            variant="outlined"
            disabled={isLoading}
            sx={{
              flexGrow: 1,
              '& .MuiOutlinedInput-root': {
                borderRadius: borderRadius('medium'),
                '&:hover': {
                  borderColor: 'primary.main',
                },
                '& fieldset': {
                  borderColor: 'divider',
                },
              },
              '& .MuiOutlinedInput-input': {
                fontSize: fontSize('small'),
                py: spacing(1),
                '&::-webkit-scrollbar': {
                  width: '6px',
                },
                '&::-webkit-scrollbar-track': {
                  background: 'rgba(0, 0, 0, 0.1)',
                  borderRadius: '3px',
                },
                '&::-webkit-scrollbar-thumb': {
                  background: 'rgba(0, 0, 0, 0.3)',
                  borderRadius: '3px',
                  '&:hover': {
                    background: 'rgba(0, 0, 0, 0.5)',
                  },
                },
              },
            }}
            InputProps={{
              startAdornment: isMobile && (
                <Box component="span" sx={{ mr: 1 }}>
                  <SearchIcon fontSize="small" color="disabled" />
                </Box>
              ),
            }}
          />
          <Button
            variant="contained"
            color="primary"
            endIcon={isLoading ? <CircularProgress size={20} /> : <SendIcon />}
            onClick={onSendMessage}
            disabled={isLoading || !inputMessage?.trim()}
            sx={{
              minWidth: isMobile ? 70 : 90,
              height: isMobile ? 40 : 48,
              borderRadius: borderRadius('medium'),
              fontSize: fontSize('small'),
              whiteSpace: 'nowrap',
              boxShadow: 2,
              '&:hover': {
                boxShadow: 4,
              },
            }}
          >
            {isMobile ? '送信' : '送信'}
          </Button>
        </Box>
      </Box>
    );
  },
);

ChatInput.displayName = 'ChatInput';

export default ChatInput;
