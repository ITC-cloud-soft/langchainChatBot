/**
 * useNovuNotifications フックのテストスイート
 */
import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useNovuNotifications } from '../../hooks/useNovuNotifications';
import { io } from 'socket.io-client';

// Socket.IOのモック
vi.mock('socket.io-client', () => ({
  io: vi.fn(() => ({
    on: vi.fn(),
    emit: vi.fn(),
    disconnect: vi.fn(),
  })),
}));

// Fetchのモック
global.fetch = vi.fn();

// LocalStorageのモック
const localStorageMock = {
  getItem: vi.fn(() => 'mock_token'),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('useNovuNotifications', () => {
  const mockOptions = {
    subscriberId: 'test_user_001',
    applicationIdentifier: 'test_app_id',
    backendUrl: 'http://localhost:8000',
    socketUrl: 'http://localhost:3002',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('初期化', () => {
    it('正しく初期化される', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          data: [],
          totalCount: 0,
        }),
      }).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          unread: 0,
        }),
      });

      const { result } = renderHook(() => useNovuNotifications(mockOptions));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.notifications).toEqual([]);
      expect(result.current.unreadCount).toBe(0);
      expect(result.current.error).toBeNull();
    });

    it('WebSocket接続が確立される', () => {
      (global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => ({ data: [], totalCount: 0 }),
      });

      renderHook(() => useNovuNotifications(mockOptions));

      expect(io).toHaveBeenCalledWith(
        mockOptions.socketUrl,
        expect.objectContaining({
          transports: ['websocket'],
          query: {
            subscriberId: mockOptions.subscriberId,
            applicationIdentifier: mockOptions.applicationIdentifier,
          },
        })
      );
    });
  });

  describe('通知取得', () => {
    it('通知リストを正しく取得する', async () => {
      const mockNotifications = [
        {
          _id: 'notif_1',
          content: 'Test notification 1',
          read: false,
          seen: false,
          createdAt: '2026-01-22T10:00:00Z',
          payload: {},
        },
        {
          _id: 'notif_2',
          content: 'Test notification 2',
          read: true,
          seen: true,
          createdAt: '2026-01-22T09:00:00Z',
          payload: {},
        },
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          data: mockNotifications,
          totalCount: 2,
        }),
      }).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          unread: 1,
        }),
      });

      const { result } = renderHook(() => useNovuNotifications(mockOptions));

      await waitFor(() => {
        expect(result.current.notifications).toHaveLength(2);
      });

      expect(result.current.notifications[0]._id).toBe('notif_1');
      expect(result.current.unreadCount).toBe(1);
    });

    it('取得エラーを正しく処理する', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useNovuNotifications(mockOptions));

      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
      });

      expect(result.current.error?.message).toContain('通知の取得に失敗しました');
      expect(result.current.notifications).toEqual([]);
    });
  });

  describe('既読マーク', () => {
    it('通知を既読にマークできる', async () => {
      const mockNotifications = [
        {
          _id: 'notif_1',
          content: 'Test notification',
          read: false,
          seen: false,
          createdAt: '2026-01-22T10:00:00Z',
          payload: {},
        },
      ];

      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ data: mockNotifications, totalCount: 1 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ unread: 1 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),
        });

      const { result } = renderHook(() => useNovuNotifications(mockOptions));

      await waitFor(() => {
        expect(result.current.notifications).toHaveLength(1);
      });

      await act(async () => {
        await result.current.markAsRead('notif_1');
      });

      expect(result.current.notifications[0].read).toBe(true);
      expect(result.current.unreadCount).toBe(0);
    });

    it('全通知を既読にマークできる', async () => {
      const mockNotifications = [
        {
          _id: 'notif_1',
          content: 'Test 1',
          read: false,
          seen: false,
          createdAt: '2026-01-22T10:00:00Z',
          payload: {},
        },
        {
          _id: 'notif_2',
          content: 'Test 2',
          read: false,
          seen: false,
          createdAt: '2026-01-22T09:00:00Z',
          payload: {},
        },
      ];

      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ data: mockNotifications, totalCount: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ unread: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),
        });

      const { result } = renderHook(() => useNovuNotifications(mockOptions));

      await waitFor(() => {
        expect(result.current.notifications).toHaveLength(2);
      });

      await act(async () => {
        await result.current.markAllAsRead();
      });

      expect(result.current.notifications.every((n) => n.read)).toBe(true);
      expect(result.current.unreadCount).toBe(0);
    });
  });

  describe('通知削除', () => {
    it('通知を削除できる', async () => {
      const mockNotifications = [
        {
          _id: 'notif_1',
          content: 'Test notification',
          read: false,
          seen: false,
          createdAt: '2026-01-22T10:00:00Z',
          payload: {},
        },
      ];

      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ data: mockNotifications, totalCount: 1 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ unread: 1 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),
        });

      const { result } = renderHook(() => useNovuNotifications(mockOptions));

      await waitFor(() => {
        expect(result.current.notifications).toHaveLength(1);
      });

      await act(async () => {
        await result.current.remove('notif_1');
      });

      expect(result.current.notifications).toHaveLength(0);
    });
  });

  describe('追加読み込み', () => {
    it('さらに通知を読み込める', async () => {
      const firstPageNotifications = [
        { _id: 'notif_1', content: 'Test 1', read: false, seen: false, createdAt: '2026-01-22T10:00:00Z', payload: {} },
      ];

      const secondPageNotifications = [
        { _id: 'notif_2', content: 'Test 2', read: false, seen: false, createdAt: '2026-01-22T09:00:00Z', payload: {} },
      ];

      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ data: firstPageNotifications, totalCount: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ unread: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ data: secondPageNotifications, totalCount: 2 }),
        });

      const { result } = renderHook(() => useNovuNotifications(mockOptions));

      await waitFor(() => {
        expect(result.current.notifications).toHaveLength(1);
      });

      await act(async () => {
        await result.current.fetchMore();
      });

      expect(result.current.notifications).toHaveLength(2);
      expect(result.current.notifications[1]._id).toBe('notif_2');
    });
  });

  describe('再取得', () => {
    it('通知リストを再取得できる', async () => {
      const initialNotifications = [
        { _id: 'notif_1', content: 'Test 1', read: false, seen: false, createdAt: '2026-01-22T10:00:00Z', payload: {} },
      ];

      const updatedNotifications = [
        { _id: 'notif_1', content: 'Test 1', read: false, seen: false, createdAt: '2026-01-22T10:00:00Z', payload: {} },
        { _id: 'notif_2', content: 'Test 2', read: false, seen: false, createdAt: '2026-01-22T09:00:00Z', payload: {} },
      ];

      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ data: initialNotifications, totalCount: 1 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ unread: 1 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ data: updatedNotifications, totalCount: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ unread: 2 }),
        });

      const { result } = renderHook(() => useNovuNotifications(mockOptions));

      await waitFor(() => {
        expect(result.current.notifications).toHaveLength(1);
      });

      await act(async () => {
        await result.current.refetch();
      });

      expect(result.current.notifications).toHaveLength(2);
      expect(result.current.unreadCount).toBe(2);
    });
  });

  describe('WebSocketイベント', () => {
    it('新しい通知を受信できる', async () => {
      let notificationReceivedHandler: any;

      const mockSocket = {
        on: vi.fn((event, handler) => {
          if (event === 'notification_received') {
            notificationReceivedHandler = handler;
          }
        }),
        emit: vi.fn(),
        disconnect: vi.fn(),
      };

      (io as any).mockReturnValue(mockSocket);

      (global.fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ data: [], totalCount: 0 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ unread: 0 }),
        });

      const { result } = renderHook(() => useNovuNotifications(mockOptions));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // 新しい通知をシミュレート
      const newNotification = {
        _id: 'notif_new',
        content: 'New notification',
        read: false,
        seen: false,
        createdAt: '2026-01-22T11:00:00Z',
        payload: {},
      };

      act(() => {
        notificationReceivedHandler(newNotification);
      });

      expect(result.current.notifications).toHaveLength(1);
      expect(result.current.notifications[0]._id).toBe('notif_new');
      expect(result.current.unreadCount).toBe(1);
    });
  });
});
