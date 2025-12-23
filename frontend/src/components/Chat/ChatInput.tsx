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

  return (
    <Box
      sx={{
        flexShrink: 0,
        height: 'auto',
        minHeight: { xs: '56px', md: '56px' },
        maxHeight: { xs: '110px', md: '120px' },
        borderTop: '1px solid',
        borderColor: 'rgba(0, 0, 0, 0.08)',
        backgroundColor: 'background.paper',
        backdropFilter: 'blur(20px)',
        p: { xs: 1.5, md: 1.5 },
        display: 'flex',
        alignItems: 'center',
        gap: { xs: 1.5, md: 1.5 },
        position: 'relative',
      }}
    >
        <TextField
          inputRef={inputRef}
          fullWidth
          multiline
          maxRows={2}
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
              borderRadius: 20,
              backgroundColor: 'rgba(255, 255, 255, 0.8)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
              '& fieldset': {
                borderColor: 'rgba(255, 255, 255, 0.3)',
                borderWidth: 1,
              },
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                boxShadow: '0 4px 16px rgba(0, 0, 0, 0.06)',
                '& fieldset': {
                  borderColor: theme.palette.primary.light,
                  borderWidth: 1,
                },
              },
              '&.Mui-focused': {
                backgroundColor: '#ffffff',
                boxShadow: `0 0 0 3px rgba(14, 165, 233, 0.08), 0 8px 24px rgba(0, 0, 0, 0.08)`,
                border: `1px solid ${theme.palette.primary.main}`,
                '& fieldset': {
                  borderWidth: 1,
                  borderColor: theme.palette.primary.main,
                },
              },
              '&.Mui-disabled': {
                backgroundColor: 'rgba(255, 255, 255, 0.5)',
                '& fieldset': {
                  borderColor: theme.palette.grey[300],
                },
              },
            },
            '& .MuiOutlinedInput-input': {
              fontSize: '1rem',
              lineHeight: 1.3,
              padding: '6px 12px',
              '&::placeholder': {
                color: theme.palette.grey[500],
                opacity: 0.8,
                fontWeight: 400,
              },
            },
            '& .MuiOutlinedInput-multiline': {
              padding: 0,
            },
          }}
        />

        <IconButton
          onClick={handleSend}
          disabled={isSendDisabled}
          sx={{
            width: 48,
            height: 48,
            borderRadius: '50%',
            backgroundColor: isSendDisabled ? 'action.disabledBackground' : 'primary.main',
            color: isSendDisabled ? 'action.disabled' : 'primary.contrastText',
            '&:hover': {
              backgroundColor: isSendDisabled ? 'action.disabledBackground' : 'primary.dark',
              transform: isSendDisabled ? 'none' : 'scale(1.05)',
              boxShadow: isSendDisabled ? 'none' : '0 6px 20px rgba(14, 165, 233, 0.25)',
            },
            '&:active': {
              transform: isSendDisabled ? 'none' : 'scale(0.95)',
            },
            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            boxShadow: isSendDisabled ? 'none' : '0 4px 14px rgba(14, 165, 233, 0.2)',
            flexShrink: 0,
          }}
        >
          <SendIcon sx={{ fontSize: '1.3rem' }} />
        </IconButton>
    </Box>
  );
};
