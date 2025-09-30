import React from 'react';
import {
  Box,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  useTheme,
} from '@mui/material';
import { History as HistoryIcon } from '@mui/icons-material';

interface ChatHeaderProps {
  selectedSession: any;
  isMobile: boolean;
  onMobileMenuClick?: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  selectedSession,
  isMobile,
  onMobileMenuClick,
}) => {
  const theme = useTheme();

  return (
    <Box
      sx={{
        p: { xs: 2, md: 3 },
        borderBottom: '1px solid',
        borderColor: 'rgba(0, 0, 0, 0.08)',
        backgroundColor: 'background.paper',
        backdropFilter: 'blur(20px)',
        flexShrink: 0,
        minHeight: { xs: '64px', md: '72px' },
        height: 'auto',
        maxHeight: '88px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        transition: 'all 0.3s ease',
        '&:hover': {
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
        },
      }}
    >
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 1.5,
          width: '100%',
        }}
      >
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 0, flex: 1 }}>
          <Typography
            variant="h6"
            sx={{
              fontSize: { xs: '1.1rem', md: '1.25rem' },
              fontWeight: 600,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              color: 'text.primary',
              minWidth: 0,
            }}
          >
            {selectedSession
              ? selectedSession.title || '無題のセッション'
              : '新しいチャット'}
          </Typography>
          {selectedSession && (
            <Chip
              label={selectedSession.is_active ? 'アクティブ' : '非アクティブ'}
              size="small"
              color={selectedSession.is_active ? 'success' : 'default'}
              variant="outlined"
              sx={{
                fontSize: '0.75rem',
                height: 24,
                fontWeight: 500,
                borderRadius: 2,
                borderWidth: 1,
                alignSelf: 'flex-start',
                '& .MuiChip-label': {
                  px: 1.5,
                },
              }}
            />
          )}
        </Box>

        {isMobile && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 0.5, sm: 1 }, flexShrink: 0 }}>
            <Tooltip title="履歴" placement="bottom">
              <IconButton
                onClick={onMobileMenuClick}
                size="medium"
                sx={{
                  p: { xs: 1, sm: 1.25 },
                  borderRadius: 2,
                  backgroundColor: 'rgba(14, 165, 233, 0.08)',
                  color: 'primary.main',
                  '&:hover': {
                    backgroundColor: 'rgba(14, 165, 233, 0.15)',
                    transform: 'scale(1.05)',
                  },
                  transition: 'all 0.2s ease',
                }}
              >
                <HistoryIcon sx={{ fontSize: { xs: '1.2rem', sm: '1.5rem' } }} />
              </IconButton>
            </Tooltip>
          </Box>
        )}

        {!isMobile && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexShrink: 0 }}>
            <Tooltip title="履歴" placement="bottom">
              <IconButton
                onClick={onMobileMenuClick}
                size="medium"
                sx={{
                  p: 1.5,
                  borderRadius: 2,
                  backgroundColor: 'rgba(14, 165, 233, 0.08)',
                  color: 'primary.main',
                  '&:hover': {
                    backgroundColor: 'rgba(14, 165, 233, 0.15)',
                    transform: 'scale(1.05)',
                  },
                  transition: 'all 0.2s ease',
                }}
              >
                <HistoryIcon sx={{ fontSize: '1.5rem' }} />
              </IconButton>
            </Tooltip>
          </Box>
        )}
      </Box>
    </Box>
  );
};
