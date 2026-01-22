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

interface NotificationBellProps {
  userId: string;
  onNotificationClick?: (notification: any) => void;
}

export default function NotificationBell({ userId, onNotificationClick }: NotificationBellProps) {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [open, setOpen] = useState(false);

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
    [markAsRead, onNotificationClick, navigate, handleClose]
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
    [remove]
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
  }, [markAllAsRead]);

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
      const isWorkflowRequest = item.payload?.type === 'workflow_request';

      return (
        <ListItem
          key={item._id}
          onClick={() => handleNotificationClick(item)}
          sx={{
            cursor: 'pointer',
            bgcolor: isUnread ? 'action.hover' : 'transparent',
            borderLeft: isUnread ? 4 : 0,
            borderColor: 'primary.main',
            '&:hover': {
              bgcolor: 'action.selected',
            },
          }}
          secondaryAction={
            <IconButton
              edge="end"
              onClick={(e) => handleDelete(e, item._id)}
              size="small"
            >
              <DeleteIcon />
            </IconButton>
          }
        >
          <ListItemText
            primary={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {isUnread && (
                  <Box
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      bgcolor: 'primary.main',
                    }}
                  />
                )}
                <Typography
                  variant="body1"
                  sx={{ fontWeight: isUnread ? 600 : 400 }}
                >
                  {item.payload?.title || item.content}
                </Typography>
              </Box>
            }
            secondary={
              <Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {item.payload?.content || ''}
                </Typography>

                {/* ワークフロー情報 */}
                {isWorkflowRequest && item.payload?.workflowData && (
                  <Box
                    sx={{
                      p: 1,
                      bgcolor: 'grey.100',
                      borderRadius: 1,
                      fontSize: '0.75rem',
                      mb: 1,
                    }}
                  >
                    <div>WorkID: {item.payload.workflowData.WorkID}</div>
                    <div>FlowName: {item.payload.workflowData.FlowName}</div>
                    <div>申請者: {item.payload.workflowData.StarterName}</div>
                  </Box>
                )}

                <Typography variant="caption" color="text.disabled">
                  {new Date(item.createdAt).toLocaleString('ja-JP')}
                </Typography>
              </Box>
            }
          />
        </ListItem>
      );
    },
    [handleNotificationClick, handleDelete]
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
    </>
  );
}
