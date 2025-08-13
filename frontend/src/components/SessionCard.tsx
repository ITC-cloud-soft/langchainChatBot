import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Chip,
  Avatar,
  Tooltip,
  alpha,
  useTheme,
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Chat as ChatIcon,
  Person as PersonIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import { ja } from 'date-fns/locale';

interface ChatSession {
  session_id: string;
  title?: string;
  user_id?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  metadata?: Record<string, unknown>;
  message_count?: number;
}

interface SessionCardProps {
  session: ChatSession;
  isSelected: boolean;
  onSelect: (session: ChatSession) => void;
  onUpdate: (session: ChatSession, title: string) => void;
  onDelete: (session: ChatSession) => void;
}

const SessionCard: React.FC<SessionCardProps> = ({
  session,
  isSelected,
  onSelect,
  onUpdate,
  onDelete,
}) => {
  const theme = useTheme();
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(session.title || '');

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    setMenuAnchor(event.currentTarget);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
  };

  const handleEdit = () => {
    setIsEditing(true);
    setMenuAnchor(null);
  };

  const handleSaveEdit = () => {
    onUpdate(session, editTitle);
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditTitle(session.title || '');
    setIsEditing(false);
  };

  const formatRelativeTime = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), {
        addSuffix: true,
        locale: ja,
      });
    } catch (error) {
      return new Date(dateString).toLocaleDateString('ja-JP');
    }
  };

  const getSessionInitial = (title: string) => {
    return title.charAt(0).toUpperCase();
  };

  const getAvatarColor = (title: string) => {
    const colors = [
      theme.palette.primary.main,
      theme.palette.secondary.main,
      theme.palette.success.main,
      theme.palette.warning.main,
      theme.palette.info.main,
      theme.palette.error.main,
    ];
    const index = title.charCodeAt(0) % colors.length;
    return colors[index];
  };

  const handleCardClick = () => {
    onSelect(session);
  };

  return (
    <>
      <Card
        onClick={handleCardClick}
        sx={{
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          border: '1px solid',
          borderColor: isSelected ? 'primary.main' : 'divider',
          bgcolor: isSelected ? alpha(theme.palette.primary.main, 0.05) : 'background.paper',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: 4,
            borderColor: 'primary.light',
          },
          position: 'relative',
          overflow: 'visible',
        }}
      >
        <CardContent sx={{ p: 2 }}>
          {/* カードヘッダー */}
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              mb: 1,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexGrow: 1 }}>
              <Avatar
                sx={{
                  width: 40,
                  height: 40,
                  bgcolor: getAvatarColor(session.title || '無題'),
                  fontSize: '1rem',
                  fontWeight: 'bold',
                }}
              >
                {getSessionInitial(session.title || '無題')}
              </Avatar>
              <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                <Typography
                  variant="subtitle2"
                  sx={{
                    fontWeight: 'medium',
                    color: isSelected ? 'primary.main' : 'text.primary',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {session.title || '無題のセッション'}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                    {formatRelativeTime(session.updated_at)}
                  </Typography>
                  {session.message_count !== undefined && session.message_count > 0 && (
                    <Chip
                      label={`${session.message_count}`}
                      size="small"
                      sx={{
                        height: 16,
                        fontSize: '0.7rem',
                        bgcolor: alpha(theme.palette.primary.main, 0.1),
                        color: 'primary.main',
                      }}
                    />
                  )}
                </Box>
              </Box>
            </Box>
            <Tooltip title="メニュー">
              <IconButton
                size="small"
                onClick={handleMenuOpen}
                sx={{
                  color: 'text.secondary',
                  '&:hover': { color: 'primary.main' },
                }}
              >
                <MoreVertIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>

          {/* メタデータ情報 */}
          {session.metadata && Object.keys(session.metadata).length > 0 && (
            <Box sx={{ mt: 1.5 }}>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ display: 'block', mb: 0.5 }}
              >
                メタデータ:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {Object.entries(session.metadata)
                  .slice(0, 3)
                  .map(([key, value]) => (
                    <Chip
                      key={key}
                      label={`${key}: ${String(value).substring(0, 20)}${String(value).length > 20 ? '...' : ''}`}
                      size="small"
                      variant="outlined"
                      sx={{
                        fontSize: '0.7rem',
                        height: 20,
                        borderColor: alpha(theme.palette.divider, 0.5),
                      }}
                    />
                  ))}
                {Object.keys(session.metadata).length > 3 && (
                  <Chip
                    label={`+${Object.keys(session.metadata).length - 3}`}
                    size="small"
                    variant="outlined"
                    sx={{
                      fontSize: '0.7rem',
                      height: 20,
                      borderColor: alpha(theme.palette.divider, 0.5),
                    }}
                  />
                )}
              </Box>
            </Box>
          )}

          {/* ステータスインジケーター */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1.5 }}>
            <Chip
              label={session.is_active ? 'アクティブ' : '非アクティブ'}
              size="small"
              color={session.is_active ? 'success' : 'default'}
              sx={{
                height: 20,
                fontSize: '0.7rem',
                fontWeight: 'medium',
              }}
            />
            {session.user_id && (
              <Tooltip title={`ユーザーID: ${session.user_id}`}>
                <Avatar sx={{ width: 20, height: 20 }}>
                  <PersonIcon fontSize="small" />
                </Avatar>
              </Tooltip>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* メニュー */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
        PaperProps={{
          elevation: 3,
          sx: {
            minWidth: 160,
            '& .MuiMenuItem-root': {
              py: 1,
              px: 2,
            },
          },
        }}
      >
        <MenuItem onClick={handleEdit}>
          <EditIcon sx={{ mr: 1, fontSize: 'small' }} />
          タイトルを編集
        </MenuItem>
        <MenuItem
          onClick={() => {
            handleMenuClose();
            onDelete(session);
          }}
          sx={{ color: 'error.main' }}
        >
          <DeleteIcon sx={{ mr: 1, fontSize: 'small' }} />
          削除
        </MenuItem>
      </Menu>

      {/* 編集ダイアログ */}
      <Dialog open={isEditing} onClose={handleCancelEdit} maxWidth="sm" fullWidth>
        <DialogTitle>セッションタイトルを編集</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="タイトル"
            fullWidth
            variant="outlined"
            value={editTitle}
            onChange={e => setEditTitle(e.target.value)}
            placeholder="セッションのタイトルを入力してください"
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelEdit}>キャンセル</Button>
          <Button onClick={handleSaveEdit} variant="contained">
            保存
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default SessionCard;
