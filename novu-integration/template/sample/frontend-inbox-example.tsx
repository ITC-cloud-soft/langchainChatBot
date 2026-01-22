/**
 * Novu Inbox コンポーネントの実装例
 * 
 * カスタムボタンとリダイレクトを含む通知レンダリング
 */

import { Inbox } from '@novu/react';
import { useRouter } from 'next/navigation';

export function NotificationInbox() {
  const router = useRouter();

  return (
    <Inbox
      applicationIdentifier={process.env.NEXT_PUBLIC_NOVU_APP_ID!}
      subscriberId="user-id-here"
      
      // 通知クリック時の処理
      onNotificationClick={(notification) => {
        console.log('通知がクリックされました:', notification);
        
        // payload の redirectUrl を使用
        const redirectUrl = notification.data?.redirectUrl;
        if (redirectUrl) {
          router.push(redirectUrl);
        }
        
        // 通知を既読にマーク
        notification.read();
      }}
      
      // カスタム通知レンダリング
      renderNotification={(notification) => {
        const { primaryAction, secondaryAction } = notification.data || {};
        
        return (
          <div className="p-4 border-b hover:bg-gray-50 cursor-pointer">
            {/* 通知内容 */}
            <div className="mb-3">
              <h4 className="font-semibold text-gray-900">
                {notification.subject}
              </h4>
              <p className="text-sm text-gray-600 mt-1">
                {notification.body}
              </p>
            </div>
            
            {/* アクションボタン */}
            {(primaryAction || secondaryAction) && (
              <div className="flex gap-2 mt-3">
                {/* Primary ボタン */}
                {primaryAction && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation(); // 通知クリックイベントを防ぐ
                      router.push(primaryAction.url);
                      notification.read();
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
                  >
                    {primaryAction.label}
                  </button>
                )}
                
                {/* Secondary ボタン */}
                {secondaryAction && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      router.push(secondaryAction.url);
                      notification.read();
                    }}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 text-sm font-medium"
                  >
                    {secondaryAction.label}
                  </button>
                )}
              </div>
            )}
            
            {/* タイムスタンプ */}
            <div className="text-xs text-gray-400 mt-2">
              {new Date(notification.createdAt).toLocaleString('ja-JP')}
            </div>
          </div>
        );
      }}
      
      // スタイリング
      styles={{
        bellButton: {
          root: {
            position: 'relative',
            cursor: 'pointer'
          }
        }
      }}
    />
  );
}

/**
 * 使用例 (Next.js App Router)
 */
export default function Header() {
  return (
    <header className="flex items-center justify-between p-4 bg-white shadow">
      <h1>My App</h1>
      
      {/* 通知ベルアイコン */}
      <div className="relative">
        <NotificationInbox />
      </div>
    </header>
  );
}
