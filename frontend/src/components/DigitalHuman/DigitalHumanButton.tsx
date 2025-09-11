import React from 'react';
import {
  Box,
  IconButton,
  Tooltip,
  Chip,
  useTheme,
} from '@mui/material';
import {
  Videocam as VideocamIcon,
  VideocamOff as VideocamOffIcon,
} from '@mui/icons-material';

interface DigitalHumanButtonProps {
  isConnected: boolean;
  isConnecting?: boolean;
  onToggle: () => void;
  disabled?: boolean;
}

export const DigitalHumanButton: React.FC<DigitalHumanButtonProps> = ({
  isConnected,
  isConnecting = false,
  onToggle,
  disabled = false,
}) => {
  const theme = useTheme();

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Tooltip title={isConnected ? 'デジタルヒューマンを停止' : 'デジタルヒューマンを開始'}>
        <IconButton
          onClick={onToggle}
          disabled={disabled || isConnecting}
          sx={{
            width: 40,
            height: 40,
            borderRadius: 2,
            backgroundColor: isConnected ? 'success.main' : 'grey.300',
            color: isConnected ? 'success.contrastText' : 'text.secondary',
            '&:hover': {
              backgroundColor: isConnected ? 'success.dark' : 'grey.400',
              transform: 'scale(1.05)',
            },
            '&:active': {
              transform: 'scale(0.95)',
            },
            '&.Mui-disabled': {
              backgroundColor: 'action.disabledBackground',
              color: 'action.disabled',
            },
            transition: 'all 0.2s ease',
            boxShadow: isConnected ? theme.shadows[2] : 'none',
          }}
        >
          {isConnected ? (
            <VideocamIcon sx={{ fontSize: '1.25rem' }} />
          ) : (
            <VideocamOffIcon sx={{ fontSize: '1.25rem' }} />
          )}
        </IconButton>
      </Tooltip>

      {/* 接続状態表示 */}
      <Chip
        label={
          isConnecting ? '接続中...' :
          isConnected ? '接続済み' : '未接続'
        }
        size="small"
        color={
          isConnecting ? 'warning' :
          isConnected ? 'success' : 'default'
        }
        sx={{
          fontSize: '0.7rem',
          height: 20,
          fontWeight: 500,
        }}
      />
    </Box>
  );
};
