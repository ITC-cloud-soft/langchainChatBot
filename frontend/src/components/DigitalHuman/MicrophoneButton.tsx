import React from 'react';
import {
  IconButton,
  Tooltip,
  CircularProgress,
  useTheme,
} from '@mui/material';
import {
  Mic as MicIcon,
  MicOff as MicOffIcon,
  Stop as StopIcon,
} from '@mui/icons-material';

interface MicrophoneButtonProps {
  isRecording: boolean;
  isProcessing?: boolean;
  disabled?: boolean;
  onToggleRecording: () => void;
  size?: 'small' | 'medium' | 'large';
}

export const MicrophoneButton: React.FC<MicrophoneButtonProps> = ({
  isRecording,
  isProcessing = false,
  disabled = false,
  onToggleRecording,
  size = 'medium',
}) => {
  const theme = useTheme();

  const getButtonSize = () => {
    switch (size) {
      case 'small':
        return { width: 36, height: 36, fontSize: '1rem' };
      case 'large':
        return { width: 56, height: 56, fontSize: '1.5rem' };
      default:
        return { width: 44, height: 44, fontSize: '1.25rem' };
    }
  };

  const buttonSize = getButtonSize();

  const getButtonColor = () => {
    if (isProcessing) return 'warning';
    if (isRecording) return 'error';
    return 'primary';
  };

  const getTooltipText = () => {
    if (isProcessing) return '音声を処理中...';
    if (isRecording) return '録音を停止';
    return '音声を録音';
  };

  return (
    <Tooltip title={getTooltipText()}>
      <IconButton
        onClick={onToggleRecording}
        disabled={disabled || isProcessing}
        sx={{
          width: buttonSize.width,
          height: buttonSize.height,
          borderRadius: '50%',
          backgroundColor: isRecording
            ? 'error.main'
            : isProcessing
              ? 'warning.main'
              : 'primary.main',
          color: 'white',
          border: `2px solid ${theme.palette.common.white}`,
          boxShadow: isRecording
            ? theme.shadows[4]
            : theme.shadows[2],
          '&:hover': {
            backgroundColor: isRecording
              ? 'error.dark'
              : isProcessing
                ? 'warning.dark'
                : 'primary.dark',
            transform: 'scale(1.05)',
            boxShadow: theme.shadows[6],
          },
          '&:active': {
            transform: 'scale(0.95)',
          },
          '&.Mui-disabled': {
            backgroundColor: 'action.disabledBackground',
            color: 'action.disabled',
            borderColor: 'action.disabled',
            boxShadow: 'none',
          },
          transition: 'all 0.2s ease',
          position: 'relative',
          // 録音中のアニメーション効果
          ...(isRecording && {
            animation: 'pulse 1.5s infinite',
            '@keyframes pulse': {
              '0%': {
                transform: 'scale(1)',
                boxShadow: `0 0 0 0 ${theme.palette.error.main}40`,
              },
              '70%': {
                transform: 'scale(1.05)',
                boxShadow: `0 0 0 10px ${theme.palette.error.main}00`,
              },
              '100%': {
                transform: 'scale(1)',
                boxShadow: `0 0 0 0 ${theme.palette.error.main}00`,
              },
            },
          }),
        }}
      >
        {isProcessing ? (
          <CircularProgress
            size={buttonSize.width * 0.5}
            sx={{
              color: 'white',
              position: 'absolute',
            }}
          />
        ) : isRecording ? (
          <StopIcon sx={{ fontSize: buttonSize.fontSize }} />
        ) : (
          <MicIcon sx={{ fontSize: buttonSize.fontSize }} />
        )}
      </IconButton>
    </Tooltip>
  );
};
