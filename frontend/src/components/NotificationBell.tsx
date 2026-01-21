/**
 * 通知ベルコンポーネント - Novu統合版
 */
import React, { useState, useCallback } from 'react';
import { Badge, Drawer, List, Button, Empty, Spin, message } from 'antd';
import { BellOutlined, CloseOutlined, CheckOutlined } from '@ant-design/icons';
import { useRouter } from 'next/navigation';
import { useNovuNotifications } from '../hooks/useNovuNotifications';

interface NotificationBellProps {
  userId: string;
  onNotificationClick?: (notification: any) => void;
}

export default function NotificationBell({ userId, onNotificationClick }: NotificationBellProps) {
  const router = useRouter();
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
    applicationIdentifier: process.env.NEXT_PUBLIC_NOVU_APP_ID || '',
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
          router.push('/chatbot');
          handleClose();
        }
      } catch (err) {
        console.error('Failed to handle notification click:', err);
        message.error('通知の処理に失敗しました');
      }
    },
    [markAsRead, onNotificationClick, router, handleClose]
  );

  // 通知を削除
  const handleDelete = useCallback(
    async (e: React.MouseEvent, notificationId: string) => {
      e.stopPropagation();
      try {
        await remove(notificationId);
        message.success('通知を削除しました');
      } catch (err) {
        console.error('Failed to delete notification:', err);
        message.error('通知の削除に失敗しました');
      }
    },
    [remove]
  );

  // 全て既読
  const handleMarkAllRead = useCallback(async () => {
    try {
      await markAllAsRead();
      message.success('全ての通知を既読にしました');
    } catch (err) {
      console.error('Failed to mark all as read:', err);
      message.error('一括既読に失敗しました');
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
        <List.Item
          key={item._id}
          onClick={() => handleNotificationClick(item)}
          className={`notification-item ${isUnread ? 'unread' : ''}`}
          style={{
            cursor: 'pointer',
            backgroundColor: isUnread ? '#f0f7ff' : 'transparent',
            borderLeft: isUnread ? '4px solid #1890ff' : '4px solid transparent',
            padding: '12px 16px',
            transition: 'all 0.3s',
          }}
          actions={[
            <Button
              key="delete"
              type="text"
              size="small"
              icon={<CloseOutlined />}
              onClick={(e) => handleDelete(e, item._id)}
              style={{ color: '#999' }}
            />,
          ]}
        >
          <List.Item.Meta
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {isUnread && (
                  <span
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: '#1890ff',
                    }}
                  />
                )}
                <span style={{ fontWeight: isUnread ? 600 : 400 }}>
                  {item.payload?.title || item.content}
                </span>
              </div>
            }
            description={
              <div>
                <div style={{ marginBottom: '8px', color: '#666' }}>
                  {item.payload?.content || ''}
                </div>

                {/* ワークフロー情報 */}
                {isWorkflowRequest && item.payload?.workflowData && (
                  <div
                    style={{
                      padding: '8px',
                      backgroundColor: '#f5f5f5',
                      borderRadius: '4px',
                      fontSize: '12px',
                    }}
                  >
                    <div>WorkID: {item.payload.workflowData.WorkID}</div>
                    <div>FlowName: {item.payload.workflowData.FlowName}</div>
                    <div>申請者: {item.payload.workflowData.StarterName}</div>
                  </div>
                )}

                <div style={{ marginTop: '8px', fontSize: '12px', color: '#999' }}>
                  {new Date(item.createdAt).toLocaleString('ja-JP')}
                </div>
              </div>
            }
          />
        </List.Item>
      );
    },
    [handleNotificationClick, handleDelete]
  );

  return (
    <>
      {/* 通知ベルアイコン */}
      <Badge count={unreadCount} offset={[-5, 5]}>
        <Button
          type="text"
          icon={<BellOutlined style={{ fontSize: '20px' }} />}
          onClick={handleOpen}
          style={{ border: 'none' }}
        />
      </Badge>

      {/* 通知ドロワー */}
      <Drawer
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>通知</span>
            {unreadCount > 0 && (
              <Button
                type="link"
                size="small"
                icon={<CheckOutlined />}
                onClick={handleMarkAllRead}
              >
                全て既読
              </Button>
            )}
          </div>
        }
        placement="right"
        width={400}
        open={open}
        onClose={handleClose}
        bodyStyle={{ padding: 0 }}
      >
        {error && (
          <div style={{ padding: '16px', color: 'red' }}>
            エラーが発生しました: {error.message}
          </div>
        )}

        {isLoading && notifications.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center' }}>
            <Spin size="large" />
          </div>
        ) : notifications.length === 0 ? (
          <Empty
            description="通知はありません"
            style={{ marginTop: '40px' }}
          />
        ) : (
          <div onScroll={handleScroll} style={{ height: '100%', overflowY: 'auto' }}>
            <List
              dataSource={notifications}
              renderItem={renderNotificationItem}
              split={true}
            />
            {isLoading && (
              <div style={{ padding: '16px', textAlign: 'center' }}>
                <Spin />
              </div>
            )}
          </div>
        )}
      </Drawer>

      <style jsx>{`
        .notification-item:hover {
          background-color: #fafafa !important;
        }
      `}</style>
    </>
  );
}
