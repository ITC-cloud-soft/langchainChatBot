import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  CircularProgress,
  InputAdornment,
  Divider,
  useTheme,
} from '@mui/material';
import {
  History as HistoryIcon,
  Search as SearchIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Folder as FolderIcon,
} from '@mui/icons-material';
import SessionCard from '../SessionCard';

interface Session {
  session_id: string;
  title?: string;
  user_id?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  metadata?: Record<string, unknown>;
  message_count?: number;
}

interface SessionSidebarProps {
  sessions: Session[];
  selectedSession: Session | null;
  onSessionSelect: (session: Session) => void;
  onSessionCreate: () => void;
  onSessionDelete: (session: Session) => void;
  onSessionUpdate: (session: Session, title: string) => void;
  onDeleteAllSessions: () => void;
  isLoading?: boolean;
}

export const SessionSidebar: React.FC<SessionSidebarProps> = ({
  sessions = [],
  selectedSession,
  onSessionSelect,
  onSessionCreate,
  onSessionDelete,
  onSessionUpdate,
  onDeleteAllSessions,
  isLoading = false,
}) => {
  const theme = useTheme();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'updated' | 'created' | 'title'>('updated');

  // メモ化されたフィルタリングとソート
  const filteredSessions = useMemo(() => {
    if (!Array.isArray(sessions)) return [];

    const query = searchQuery.toLowerCase();
    return sessions
      .filter(session =>
        !query ||
        session.title?.toLowerCase().includes(query) ||
        session.session_id.toLowerCase().includes(query)
      )
      .sort((a, b) => {
        switch (sortBy) {
          case 'updated':
            return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
          case 'created':
            return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
          case 'title':
            return (a.title || '').localeCompare(b.title || '');
          default:
            return 0;
        }
      });
  }, [sessions, searchQuery, sortBy]);

  return (
    <Box
      sx={{
        height: '100%',
        maxHeight: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        backgroundColor: 'background.paper',
      }}
    >
      {/* ヘッダー */}
      <Box
        sx={{
          p: 3,
          borderBottom: 1,
          borderColor: 'divider',
          backgroundColor: 'background.paper',
          flexShrink: 0,
        }}
      >
        {/* タイトル */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <HistoryIcon sx={{ mr: 1.5, color: 'primary.main' }} />
          <Typography
            variant="h6"
            sx={{
              fontWeight: 600,
              color: 'text.primary',
            }}
          >
            チャット履歴
          </Typography>
          <Chip
            label={sessions.length}
            size="small"
            sx={{
              ml: 1.5,
              fontSize: '0.75rem',
              height: 20,
              backgroundColor: 'primary.main',
              color: 'primary.contrastText',
            }}
          />
        </Box>

        {/* アクションボタン */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 1, mb: 3 }}>
          <Button
            onClick={onSessionCreate}
            variant="contained"
            size="small"
            startIcon={<AddIcon />}
            sx={{
              flex: 1,
              fontSize: '0.8rem',
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 500,
            }}
          >
            新規作成
          </Button>
          {sessions.length > 0 && (
            <Button
              onClick={onDeleteAllSessions}
              variant="outlined"
              size="small"
              color="error"
              startIcon={<DeleteIcon />}
              sx={{
                flex: 1,
                fontSize: '0.8rem',
                borderRadius: 2,
                textTransform: 'none',
                fontWeight: 500,
              }}
            >
              全て削除
            </Button>
          )}
        </Box>

        {/* 検索とソート */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            fullWidth
            size="small"
            placeholder="セッションを検索..."
            variant="outlined"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
                backgroundColor: 'background.default',
              },
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" sx={{ color: 'text.secondary' }} />
                </InputAdornment>
              ),
            }}
          />

          <FormControl size="small" fullWidth>
            <InputLabel sx={{ fontSize: '0.875rem' }}>並び替え</InputLabel>
            <Select
              value={sortBy}
              label="並び替え"
              onChange={(e) => setSortBy(e.target.value as any)}
              sx={{
                borderRadius: 2,
                '& .MuiOutlinedInput-notchedOutline': {
                  borderRadius: 2,
                },
              }}
            >
              <MenuItem value="updated">更新日時</MenuItem>
              <MenuItem value="created">作成日時</MenuItem>
              <MenuItem value="title">タイトル</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Box>

      {/* セッションリスト */}
      <Box
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          p: 2,
          height: 'auto',
          minHeight: 0,
          maxHeight: 'none',
          flexShrink: 1,
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
        }}
      >
        {isLoading ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              height: '200px',
              textAlign: 'center',
            }}
          >
            <CircularProgress size={32} sx={{ mb: 2 }} />
            <Typography variant="body2" color="text.secondary">
              セッションを読み込み中...
            </Typography>
          </Box>
        ) : filteredSessions.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              height: '200px',
              textAlign: 'center',
              p: 3,
            }}
          >
            <FolderIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2, opacity: 0.5 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              {searchQuery ? '検索結果がありません' : 'セッションがありません'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {searchQuery ? '別のキーワードで検索してください' : '新しいチャットを始めましょう'}
            </Typography>
            {!searchQuery && (
              <Button
                onClick={onSessionCreate}
                variant="contained"
                startIcon={<AddIcon />}
                sx={{
                  borderRadius: 2,
                  textTransform: 'none',
                  fontWeight: 500,
                }}
              >
                セッションを作成
              </Button>
            )}
          </Box>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {filteredSessions.map((session) => (
              <SessionCard
                key={session.session_id}
                session={session}
                isSelected={selectedSession?.session_id === session.session_id}
                onSelect={onSessionSelect}
                onUpdate={onSessionUpdate}
                onDelete={onSessionDelete}
              />
            ))}
          </Box>
        )}
      </Box>
    </Box>
  );
};
