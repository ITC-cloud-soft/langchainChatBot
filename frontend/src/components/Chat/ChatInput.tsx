import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Paper,
  useTheme,
} from '@mui/material';
import { Send as SendIcon } from '@mui/icons-material';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  isLoading?: boolean;
  placeholder?: string;
  maxLength?: number;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  value,
  onChange,
  onSend,
  isLoading = false,
  placeholder = "メッセージを入力してください...",
  maxLength = 2000,
  disabled = false,
}) => {
  const theme = useTheme();
  const inputRef = useRef<HTMLInputElement>(null);
  const [isComposing, setIsComposing] = useState(false);

  // 自動フォーカス
  useEffect(() => {
    if (inputRef.current && !isLoading) {
      inputRef.current.focus();
    }
  }, [isLoading]);

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey && !isComposing) {
      event.preventDefault();
      if (value.trim() && !isLoading && !disabled) {
        onSend();
      }
    }
  };

  const handleSend = () => {
    if (value.trim() && !isLoading && !disabled) {
      onSend();
    }
  };

  const isSendDisabled = !value.trim() || isLoading || disabled;
  // Force hot reload

  return (
    <Box
      sx={{
        flexShrink: 0,
        height: 'auto',
        minHeight: '50px',
        maxHeight: '120px',
        borderTop: 1,
        borderColor: 'divider',
        backgroundColor: 'background.paper',
        p: { xs: 1.5, md: 2 },
        display: 'flex',
        alignItems: 'flex-end',
        gap: 1.5,
      }}
    >
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          alignItems: 'flex-end',
          gap: 2,
          maxWidth: '100%',
        }}
      >
        <TextField
          inputRef={inputRef}
          fullWidth
          multiline
          maxRows={3}
          value={value}
          onChange={(e) => {
            if (e.target.value.length <= maxLength) {
              onChange(e.target.value);
            }
          }}
          onKeyPress={handleKeyPress}
          onCompositionStart={() => setIsComposing(true)}
          onCompositionEnd={() => setIsComposing(false)}
          placeholder={placeholder}
          disabled={disabled}
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 3,
              backgroundColor: 'background.default',
              transition: 'all 0.2s ease',
              '& fieldset': {
                borderColor: 'divider',
              },
              '&:hover fieldset': {
                borderColor: 'primary.main',
              },
              '&.Mui-focused fieldset': {
                borderWidth: 2,
                borderColor: 'primary.main',
              },
              '&.Mui-disabled': {
                backgroundColor: 'action.disabledBackground',
              },
            },
            '& .MuiOutlinedInput-input': {
              fontSize: '0.95rem',
              lineHeight: 1.5,
              padding: '10px 14px',
              '&::placeholder': {
                color: 'text.secondary',
                opacity: 0.7,
              },
            },
          }}
        />

        <IconButton
          onClick={handleSend}
          disabled={isSendDisabled}
          sx={{
            width: 64,
            height: 64,
            borderRadius: 3,
            backgroundColor: isSendDisabled ? 'action.disabledBackground' : 'primary.main',
            color: isSendDisabled ? 'action.disabled' : 'primary.contrastText',
            '&:hover': {
              backgroundColor: isSendDisabled ? 'action.disabledBackground' : 'primary.dark',
              transform: isSendDisabled ? 'none' : 'scale(1.05)',
            },
            '&:active': {
              transform: isSendDisabled ? 'none' : 'scale(0.95)',
            },
            transition: 'all 0.2s ease',
            boxShadow: isSendDisabled ? 'none' : theme.shadows[2],
          }}
        >
          <SendIcon sx={{ fontSize: '1.5rem' }} />
        </IconButton>
      </Box>
    </Box>
  );
};
