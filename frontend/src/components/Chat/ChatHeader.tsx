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
        borderBottom: 1,
        borderColor: 'divider',
        backgroundColor: 'background.paper',
        backdropFilter: 'blur(10px)',
        flexShrink: 0,
        minHeight: { xs: '60px', md: '70px' },
        height: 'auto',
        maxHeight: '80px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0 }}>
          <Typography
            variant="subtitle1"
            sx={{
              fontSize: { xs: '1.1rem', md: '1.25rem' },
              fontWeight: 600,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              color: 'text.primary',
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
              sx={{
                fontSize: '0.7rem',
                height: 20,
                fontWeight: 500,
              }}
            />
          )}
        </Box>
        {isMobile && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 0.5, sm: 1 } }}>
            <Tooltip title="履歴">
              <IconButton
                onClick={onMobileMenuClick}
                size="small"
                sx={{ p: { xs: 0.75, sm: 1 } }}
              >
                <HistoryIcon sx={{ fontSize: { xs: '1.2rem', sm: '1.5rem' } }} />
              </IconButton>
            </Tooltip>
          </Box>
        )}
        {!isMobile && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Tooltip title="履歴">
              <IconButton
                onClick={onMobileMenuClick}
                size="medium"
                sx={{ p: 1.5 }}
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
