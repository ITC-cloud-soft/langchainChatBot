/**
 * 通知フック - Novu統合版（WebSocket + REST API）
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

interface Notification {
  _id: string;
  _subscriberId: string;
  _templateId: string;
  content: string;
  payload: Record<string, any>;
  read: boolean;
  seen: boolean;
  createdAt: string;
  lastReadDate?: string;
  lastSeenDate?: string;
  cta?: {
    type: string;
    data: Record<string, any>;
    action?: {
      buttons?: Array<{
        type: string;
        content: string;
      }>;
    };
  };
}

interface UseNovuNotificationsOptions {
  subscriberId: string;
  applicationIdentifier: string;
  backendUrl?: string;
  socketUrl?: string;
  initialFetchCount?: number;
}

interface UseNovuNotificationsReturn {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
  error: Error | null;
  markAsRead: (notificationId: string) => Promise<void>;
  markAsSeen: (notificationId: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  remove: (notificationId: string) => Promise<void>;
  fetchMore: () => Promise<void>;
  refetch: () => Promise<void>;
}

export function useNovuNotifications(
  options: UseNovuNotificationsOptions
): UseNovuNotificationsReturn {
  const {
    subscriberId,
    applicationIdentifier,
    backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000',
    socketUrl = import.meta.env.VITE_NOVU_WS_URL || 'http://localhost:3002',
    initialFetchCount = 10,
  } = options;

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);
  const [page, setPage] = useState<number>(0);
  const [hasMore, setHasMore] = useState<boolean>(true);
  
  const socketRef = useRef<Socket | null>(null);


  // 通知リストを取得（バックエンドAPI経由）
  const fetchNotifications = useCallback(
    async (pageNum: number = 0, append: boolean = false) => {
      try {
        setIsLoading(true);
        setError(null);

        const response = await fetch(
          `${backendUrl}/api/notifications/?page=${pageNum}&limit=${initialFetchCount}`,
          {
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${localStorage.getItem('access_token')}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('通知の取得に失敗しました');
        }

        const data = await response.json();
        let notifications = data.data || [];
        
        // 通知データの正規化とフィルタリング
        notifications = notifications
          .filter((n: any) => n && (n._id || n.id)) // 空データと ID がないデータを除外
          .map((n: any) => ({
            ...n,
            _id: n._id || n.id, // _id がない場合は id を使用
          }));
        
        if (append) {
          setNotifications((prev) => [...prev, ...notifications]);
        } else {
          setNotifications(notifications);
        }

        setHasMore(notifications.length === initialFetchCount);
      } catch (err) {
        setError(err as Error);
        console.error('Failed to fetch notifications:', err);
      } finally {
        setIsLoading(false);
      }
    },
    [backendUrl, initialFetchCount]
  );

  // 未読数を取得（バックエンドAPI経由）
  const fetchUnreadCount = useCallback(async () => {
    try {
      const response = await fetch(`${backendUrl}/api/notifications/unread-count`, {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('未読数の取得に失敗しました');
      }

      const data = await response.json();
      setUnreadCount(data.unread || 0);
    } catch (err) {
      console.error('Failed to fetch unread count:', err);
    }
  }, [backendUrl]);

  // 既読マーク
  const markAsRead = useCallback(
    async (notificationId: string) => {
      try {
        const response = await fetch(
          `${backendUrl}/api/notifications/${notificationId}/read`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${localStorage.getItem('access_token')}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('既読マークに失敗しました');
        }

        // ローカル状態を更新
        setNotifications((prev) =>
          prev.map((n) =>
            n._id === notificationId
              ? { ...n, read: true, lastReadDate: new Date().toISOString() }
              : n
          )
        );

        // 未読数を更新
        setUnreadCount((prev) => Math.max(0, prev - 1));
      } catch (err) {
        console.error('Failed to mark as read:', err);
        throw err;
      }
    },
    [backendUrl]
  );

  // 既読マーク (seen)
  const markAsSeen = useCallback(
    async (notificationId: string) => {
      try {
        const response = await fetch(
          `${backendUrl}/api/notifications/${notificationId}/seen`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${localStorage.getItem('access_token')}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('既読マークに失敗しました');
        }

        // ローカル状態を更新
        setNotifications((prev) =>
          prev.map((n) =>
            n._id === notificationId
              ? { ...n, seen: true, lastSeenDate: new Date().toISOString() }
              : n
          )
        );
      } catch (err) {
        console.error('Failed to mark as seen:', err);
        throw err;
      }
    },
    [backendUrl]
  );

  // 全て既読マーク
  const markAllAsRead = useCallback(async () => {
    try {
      const response = await fetch(`${backendUrl}/api/notifications/mark-all-read`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('一括既読マークに失敗しました');
      }

      // ローカル状態を更新
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, read: true, lastReadDate: new Date().toISOString() }))
      );
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all as read:', err);
      throw err;
    }
  }, [backendUrl]);

  // 通知削除
  const remove = useCallback(
    async (notificationId: string) => {
      try {
        const response = await fetch(
          `${backendUrl}/api/notifications/${notificationId}`,
          {
            method: 'DELETE',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${localStorage.getItem('access_token')}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('通知の削除に失敗しました');
        }

        // 削除前に未読かどうかをチェック
        const notification = notifications.find((n) => n._id === notificationId);
        const wasUnread = notification && !notification.read;

        // ローカル状態から削除
        setNotifications((prev) => prev.filter((n) => n._id !== notificationId));
        
        // 未読通知を削除した場合、未読数を減らす
        if (wasUnread) {
          setUnreadCount((prev) => Math.max(0, prev - 1));
        }
      } catch (err) {
        console.error('Failed to remove notification:', err);
        throw err;
      }
    },
    [backendUrl, notifications]
  );

  // さらに読み込む
  const fetchMore = useCallback(async () => {
    if (!hasMore || isLoading) return;
    const nextPage = page + 1;
    setPage(nextPage);
    await fetchNotifications(nextPage, true);
  }, [page, hasMore, isLoading, fetchNotifications]);

  // 再取得
  const refetch = useCallback(async () => {
    setPage(0);
    await fetchNotifications(0, false);
    await fetchUnreadCount();
  }, [fetchNotifications, fetchUnreadCount]);

  // 初期化とWebSocket接続（JWT Token認証 - aud: 'widget_user' 必須）
  useEffect(() => {
    // 初期データ取得
    fetchNotifications(0, false);
    fetchUnreadCount();

    // WebSocket接続用のJWT tokenを取得
    const initWebSocket = async () => {
      try {
        console.log('🔌 Initializing Novu WebSocket with JWT authentication...');
        
        // Backend APIからJWT tokenを取得
        const tokenResponse = await fetch(
          `${backendUrl}/api/notifications/subscriber-token`,
          {
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${localStorage.getItem('access_token')}`,
            },
          }
        );

        if (!tokenResponse.ok) {
          console.error('Failed to get subscriber token:', tokenResponse.status);
          return;
        }

        const { subscriberToken } = await tokenResponse.json();
        console.log('✅ JWT token obtained from backend');

        // WebSocket接続（JWT tokenを使用）
        console.log(`🔌 Connecting to Novu WebSocket: ${socketUrl}`);
        const socket = io(socketUrl, {
          transports: ['websocket', 'polling'],
          auth: {
            token: subscriberToken,  // JWT token (aud: 'widget_user' を含む)
          },
          reconnection: true,
          reconnectionDelay: 1000,
          reconnectionAttempts: 5,
        });

        socketRef.current = socket;

        // 接続成功
        socket.on('connect', () => {
          console.log('✅ Novu WebSocket connected successfully!');
        });

        // 新しい通知を受信
        socket.on('notification_received', (data: any) => {
          console.log('📬 New notification received via WebSocket:', data);
          
          // Novu WebSocket は通知を { message: {...} } の形式で送信する
          const notification = data.message || data;
          
          console.log('📋 Extracted notification:', notification);
          console.log('📋 Notification ID check:', {
            _id: notification._id,
            id: notification.id,
            hasId: !!(notification._id || notification.id)
          });
          
          // 通知データの正規化
          const normalizedNotification = {
            ...notification,
            _id: notification._id || notification.id, // _id がない場合は id を使用
          };
          
          console.log('✅ Normalized notification:', normalizedNotification);
          
          // ID が存在する場合のみ追加
          if (normalizedNotification._id) {
            console.log('➕ Adding notification to list');
            setNotifications((prev) => [normalizedNotification, ...prev]);
            setUnreadCount((prev) => prev + 1);

            // ブラウザ通知を表示
            if ('Notification' in window && Notification.permission === 'granted') {
              new Notification(normalizedNotification.content, {
                body: normalizedNotification.payload?.content || '',
                icon: '/logo.jpg',
              });
            }
          } else {
            console.warn('⚠️ Notification has no ID, skipping:', notification);
          }
        });

        // 通知が既読になった
        socket.on('notification_read', (data: { notificationId: string }) => {
          setNotifications((prev) =>
            prev.map((n) =>
              n._id === data.notificationId
                ? { ...n, read: true, lastReadDate: new Date().toISOString() }
                : n
            )
          );
          setUnreadCount((prev) => Math.max(0, prev - 1));
        });

        // 接続エラー
        socket.on('connect_error', (err) => {
          console.error('❌ WebSocket connection error:', err);
        });

        // 切断
        socket.on('disconnect', (reason) => {
          console.log('🔌 WebSocket disconnected:', reason);
          if (reason === 'io server disconnect') {
            console.error('⚠️  Server disconnected. Check JWT token format!');
          }
        });
      } catch (err) {
        console.error('Failed to initialize WebSocket:', err);
      }
    };

    initWebSocket();

    // クリーンアップ
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
        console.log('🛑 WebSocket disconnected (cleanup)');
      }
    };
  }, [subscriberId, applicationIdentifier, socketUrl, backendUrl, fetchNotifications, fetchUnreadCount]);

  // ブラウザ通知の許可をリクエスト
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  return {
    notifications,
    unreadCount,
    isLoading,
    error,
    markAsRead,
    markAsSeen,
    markAllAsRead,
    remove,
    fetchMore,
    refetch,
  };
}
