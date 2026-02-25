/**
 * 通知ベルコンポーネント - Novu統合版
 */
import React, { useState, useCallback } from 'react';
import {
  Badge,
  Drawer,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Button,
  Typography,
  Box,
  CircularProgress,
  Divider,
} from '@mui/material';
import {
  Notifications as BellIcon,
  Close as CloseIcon,
  CheckCircle as CheckIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useNovuNotifications } from '../hooks/useNovuNotifications';
import { useSnackbar } from 'notistack';
import ApprovalFormDialog from './ApprovalFormDialog';
import { authService } from '../services/authService';

interface NotificationBellProps {
  userId: string;
  onNotificationClick?: (notification: any) => void;
}

export default function NotificationBell({ userId, onNotificationClick }: NotificationBellProps) {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [open, setOpen] = useState(false);
  const [approvalDialogOpen, setApprovalDialogOpen] = useState(false);
  const [selectedNotification, setSelectedNotification] = useState<any>(null);

  const {
    notifications,
    unreadCount,
    isLoading,
    error,
    markAsRead,
    markAllAsRead,
    remove,
    fetchMore,
  } = useNovuNotifications({
    subscriberId: userId,
    applicationIdentifier: import.meta.env.VITE_NOVU_APP_ID || '',
    backendUrl: import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000',
    socketUrl: import.meta.env.VITE_NOVU_WS_URL || 'http://localhost:3002',
  });

  // ドロワーを開く
  const handleOpen = useCallback(() => {
    setOpen(true);
  }, []);

  // ドロワーを閉じる
  const handleClose = useCallback(() => {
    setOpen(false);
  }, []);

  // 通知をクリック
  const handleNotificationClick = useCallback(
    async (notification: any) => {
      try {
        // 既読マーク
        if (!notification.read) {
          await markAsRead(notification._id);
        }

        // カスタムハンドラーがあれば実行
        if (onNotificationClick) {
          onNotificationClick(notification);
          return;
        }

        // ワークフロー承認通知の場合
        if (notification.payload?.type === 'workflow_request') {
          // localStorageに保存
          localStorage.setItem('createNewChatType', 'workflow_request');
          localStorage.setItem('createNewChatPayload', JSON.stringify(notification.payload));

          // カスタムイベントを発火
          window.dispatchEvent(
            new CustomEvent('createNewChat', {
              detail: {
                title: notification.payload.title,
                content: notification.payload.content,
                payload: notification.payload,
                type: 'workflow_request',
                showApprovalButtons: true,
              },
            })
          );

          // チャットボットページに遷移
          navigate('/chat');
          handleClose();
        }
      } catch (err) {
        console.error('Failed to handle notification click:', err);
        enqueueSnackbar('通知の処理に失敗しました', { variant: 'error' });
      }
    },
    [markAsRead, onNotificationClick, navigate, handleClose, enqueueSnackbar]
  );

  // 通知を削除
  const handleDelete = useCallback(
    async (e: React.MouseEvent, notificationId: string) => {
      e.stopPropagation();
      try {
        await remove(notificationId);
        enqueueSnackbar('通知を削除しました', { variant: 'success' });
      } catch (err) {
        console.error('Failed to delete notification:', err);
        enqueueSnackbar('通知の削除に失敗しました', { variant: 'error' });
      }
    },
    [remove, enqueueSnackbar]
  );

  // 全て既読
  const handleMarkAllRead = useCallback(async () => {
    try {
      await markAllAsRead();
      enqueueSnackbar('全ての通知を既読にしました', { variant: 'success' });
    } catch (err) {
      console.error('Failed to mark all as read:', err);
      enqueueSnackbar('一括既読に失敗しました', { variant: 'error' });
    }
  }, [markAllAsRead, enqueueSnackbar]);

  // スクロールで追加読み込み
  const handleScroll = useCallback(
    (e: React.UIEvent<HTMLDivElement>) => {
      const target = e.target as HTMLDivElement;
      const isNearBottom =
        target.scrollHeight - target.scrollTop - target.clientHeight < 100;

      if (isNearBottom && !isLoading) {
        fetchMore();
      }
    },
    [isLoading, fetchMore]
  );

  // 通知アイテムのレンダリング
  const renderNotificationItem = useCallback(
    (item: any) => {
      const isUnread = !item.read;
      const isWorkflowRequest = item.payload?.notificationType === 'ssflow_approval' || item.payload?.type === 'workflow_request';
      const isResultNotification = item.payload?.notificationType === 'ssflow_result';
      const ctaButtons = item.cta?.action?.buttons;
      const hasButtons = ctaButtons && ctaButtons.length > 0;

      return (
        <ListItem
          key={item._id}
          onClick={() => handleNotificationClick(item)}
          sx={{
            cursor: 'pointer',
            bgcolor: isUnread ? 'rgba(25, 118, 210, 0.04)' : 'transparent',
            borderLeft: isUnread ? 4 : 0,
            borderColor: 'primary.main',
            borderRadius: 1,
            mb: 1,
            mx: 1,
            transition: 'all 0.2s ease',
            '&:hover': {
              bgcolor: isUnread ? 'rgba(25, 118, 210, 0.08)' : 'rgba(0, 0, 0, 0.04)',
              transform: 'translateX(4px)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            },
          }}
          secondaryAction={
            <IconButton
              edge="end"
              onClick={(e) => handleDelete(e, item._id)}
              size="small"
              sx={{
                opacity: 0.6,
                '&:hover': {
                  opacity: 1,
                  color: 'error.main',
                },
              }}
            >
              <DeleteIcon />
            </IconButton>
          }
        >
          <ListItemText
            primary={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                {isUnread && (
                  <Box
                    sx={{
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      bgcolor: 'primary.main',
                      boxShadow: '0 0 0 3px rgba(25, 118, 210, 0.2)',
                      animation: isUnread ? 'pulse 2s infinite' : 'none',
                      '@keyframes pulse': {
                        '0%, 100%': {
                          boxShadow: '0 0 0 3px rgba(25, 118, 210, 0.2)',
                        },
                        '50%': {
                          boxShadow: '0 0 0 6px rgba(25, 118, 210, 0.1)',
                        },
                      },
                    }}
                  />
                )}
                <Typography
                  variant="body1"
                  sx={{ 
                    fontWeight: isUnread ? 600 : 400,
                    color: isUnread ? 'text.primary' : 'text.secondary',
                    fontSize: '0.95rem',
                  }}
                >
                  {isResultNotification
                    ? (item.payload?.title || `【${item.payload?.actionLabel || '結果'}】${item.payload?.flowName || ''}`)
                    : (item.payload?.flowName || item.payload?.title || '承認リクエスト')}
                </Typography>
              </Box>
            }
            secondary={
              <Box>
                {/* メッセージ本文 */}
                {(item.payload?.content || item.content) && (
                  <Box
                    sx={{
                      px: 1.5,
                      py: 1,
                      mb: 1,
                      bgcolor: isWorkflowRequest ? 'rgba(25,118,210,0.05)' : 'transparent',
                      borderLeft: isWorkflowRequest ? '3px solid' : 'none',
                      borderColor: 'primary.main',
                      borderRadius: isWorkflowRequest ? '0 4px 4px 0' : 0,
                    }}
                  >
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ lineHeight: 1.6, fontSize: '0.875rem', whiteSpace: 'pre-line' }}
                    >
                      {item.payload?.content || item.content}
                    </Typography>
                  </Box>
                )}

                {/* 申請者コメント */}
                {isWorkflowRequest && item.payload?.comment && (
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5, mb: 0.5 }}>
                    <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary', minWidth: 56, pt: 0.1 }}>
                      コメント:
                    </Typography>
                    <Typography variant="caption" sx={{ whiteSpace: 'pre-line', color: 'text.primary' }}>
                      {item.payload.comment}
                    </Typography>
                  </Box>
                )}

                {/* 申請番号 */}
                {isWorkflowRequest && item.payload?.arsParams?.WorkID && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
                    <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary', minWidth: 56 }}>
                      申請番号:
                    </Typography>
                    <Typography variant="caption" sx={{ fontFamily: 'monospace', color: 'text.secondary' }}>
                      {item.payload.arsParams.WorkID}
                    </Typography>
                  </Box>
                )}

                {/* 承認・否認結果通知の詳細情報 */}
                {isResultNotification && (
                  <Box
                    sx={{
                      p: 1.5,
                      bgcolor: item.payload?.actionType === 'approve'
                        ? 'rgba(76, 175, 80, 0.06)'
                        : 'rgba(244, 67, 54, 0.06)',
                      border: '1px solid',
                      borderColor: item.payload?.actionType === 'approve'
                        ? 'rgba(76, 175, 80, 0.3)'
                        : 'rgba(244, 67, 54, 0.3)',
                      borderRadius: 2,
                      mb: 1,
                    }}
                  >
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                      {item.payload?.approverName && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary', minWidth: 64 }}>
                            対応者:
                          </Typography>
                          <Typography variant="caption">{item.payload.approverName}</Typography>
                        </Box>
                      )}
                      {item.payload?.workId && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary', minWidth: 64 }}>
                            申請番号:
                          </Typography>
                          <Typography variant="caption" sx={{ color: 'primary.main' }}>{item.payload.workId}</Typography>
                        </Box>
                      )}
                      {item.payload?.comment && (
                        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                          <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary', minWidth: 64, pt: 0.1 }}>
                            コメント:
                          </Typography>
                          <Typography variant="caption" sx={{ whiteSpace: 'pre-line' }}>{item.payload.comment}</Typography>
                        </Box>
                      )}
                    </Box>
                  </Box>
                )}

                {/* CTA ボタン - ssflow_approval 通知は「詳細」1個に統一 */}
                {hasButtons && isWorkflowRequest && (
                  <Box sx={{ display: 'flex', gap: 1, mt: 1.5, mb: 1 }}>
                    <Button
                      variant="outlined"
                      color="primary"
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedNotification(item);
                        setApprovalDialogOpen(true);
                        if (!item.read) {
                          markAsRead(item._id);
                        }
                      }}
                      sx={{
                        flex: 1,
                        textTransform: 'none',
                        fontSize: '0.8rem',
                        fontWeight: 500,
                        py: 0.75,
                        borderRadius: 1.5,
                        '&:hover': {
                          boxShadow: '0 2px 4px rgba(25, 118, 210, 0.2)',
                          transform: 'translateY(-1px)',
                        },
                        transition: 'all 0.2s ease',
                      }}
                    >
                      詳細情報
                    </Button>
                  </Box>
                )}

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                  <Typography 
                    variant="caption" 
                    sx={{ 
                      color: 'text.disabled',
                      fontSize: '0.75rem',
                    }}
                  >
                    {(() => {
                      // createdAt または created_at フィールドを取得
                      const dateStr = item.createdAt || (item as any).created_at;
                      if (!dateStr) return '';
                      
                      try {
                        const date = new Date(dateStr);
                        if (isNaN(date.getTime())) return '';
                        
                        return date.toLocaleString('ja-JP', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        });
                      } catch (e) {
                        return '';
                      }
                    })()}
                  </Typography>
                  {isUnread && (
                    <Box
                      sx={{
                        px: 1,
                        py: 0.25,
                        bgcolor: 'primary.main',
                        color: 'white',
                        borderRadius: 1,
                        fontSize: '0.65rem',
                        fontWeight: 600,
                      }}
                    >
                      NEW
                    </Box>
                  )}
                </Box>
              </Box>
            }
          />
        </ListItem>
      );
    },
    [handleNotificationClick, handleDelete, markAsRead, navigate]
  );

  return (
    <>
      {/* 通知ベルアイコン */}
      <Badge badgeContent={unreadCount} color="error">
        <IconButton
          color="inherit"
          onClick={handleOpen}
          size="large"
        >
          <BellIcon />
        </IconButton>
      </Badge>

      {/* 通知ドロワー */}
      <Drawer
        anchor="right"
        open={open}
        onClose={handleClose}
        PaperProps={{
          sx: { width: 400 }
        }}
      >
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6">通知</Typography>
          {unreadCount > 0 && (
            <Button
              size="small"
              startIcon={<CheckIcon />}
              onClick={handleMarkAllRead}
            >
              全て既読
            </Button>
          )}
        </Box>
        {error && (
          <Box sx={{ p: 2, color: 'error.main' }}>
            エラーが発生しました: {error.message}
          </Box>
        )}

        {isLoading && notifications.length === 0 ? (
          <Box sx={{ p: 5, textAlign: 'center' }}>
            <CircularProgress />
          </Box>
        ) : notifications.length === 0 ? (
          <Box sx={{ p: 5, textAlign: 'center' }}>
            <Typography color="text.secondary">通知はありません</Typography>
          </Box>
        ) : (
          <Box onScroll={handleScroll} sx={{ height: 'calc(100vh - 80px)', overflowY: 'auto' }}>
            <List>
              {notifications.map((item) => renderNotificationItem(item))}
            </List>
            {isLoading && (
              <Box sx={{ p: 2, textAlign: 'center' }}>
                <CircularProgress size={24} />
              </Box>
            )}
          </Box>
        )}
      </Drawer>

      {/* 承認・否認フォームダイアログ */}
      <ApprovalFormDialog
        open={approvalDialogOpen}
        onClose={() => setApprovalDialogOpen(false)}
        notification={selectedNotification}
        backendUrl={import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}
        authToken={authService.getAccessToken() || ''}
        onActionComplete={(action, message) => {
          enqueueSnackbar(message, { variant: 'success' });
        }}
      />
    </>
  );
}
