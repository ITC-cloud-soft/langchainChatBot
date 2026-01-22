# Novu WebSocket リアルタイム通知設定ガイド

## 📋 概要

このドキュメントでは、Novu WebSocket を使用したリアルタイム通知の実装方法を説明します。

## 🔐 認証の仕組み

### Token の種類

**Subscriber Token（購読者トークン）**:
- ✅ **各ユーザーごとに1つ**のトークンを生成
- ✅ HMAC-SHA256 アルゴリズムを使用
- ✅ Novu API Key を秘密鍵として使用
- ✅ 確定的（同じユーザーIDから常に同じトークンを生成）

### Token 生成式

```
Token = HMAC-SHA256(subscriberId, NOVU_API_KEY)
```

**例**:
```python
import hmac
import hashlib

subscriber_id = "1"  # ユーザーID
api_key = "c47cfb7a083c4e27f9d1b523a20ed59f"  # Novu API Key

message = subscriber_id.encode('utf-8')
secret = api_key.encode('utf-8')

hmac_hash = hmac.new(secret, message, hashlib.sha256)
token = hmac_hash.hexdigest()

print(f"Subscriber Token: {token}")
```

---

## 🔄 完全な認証フロー

```
┌──────────────┐              ┌──────────────┐              ┌──────────────┐
│   Frontend   │              │   Backend    │              │  Novu WS     │
│  (Browser)   │              │   (API)      │              │  Server      │
└──────┬───────┘              └──────┬───────┘              └──────┬───────┘
       │                             │                             │
       │ 1. ユーザーログイン           │                             │
       ├────────────────────────────>│                             │
       │                             │                             │
       │ 2. Access Token 取得         │                             │
       │<────────────────────────────┤                             │
       │                             │                             │
       │ 3. Subscriber Token 要求     │                             │
       │    GET /api/notifications/  │                             │
       │        subscriber-token     │                             │
       ├────────────────────────────>│                             │
       │    Authorization: Bearer    │                             │
       │    {access_token}           │                             │
       │                             │                             │
       │                             │ 4. ユーザーID を取得          │
       │                             │    (JWT から)               │
       │                             │                             │
       │                             │ 5. HMAC Token 生成          │
       │                             │    HMAC-SHA256(            │
       │                             │      user_id,              │
       │                             │      NOVU_API_KEY          │
       │                             │    )                       │
       │                             │                             │
       │ 6. Subscriber Token 返却     │                             │
       │<────────────────────────────┤                             │
       │    { subscriberToken: "..." }                            │
       │                             │                             │
       │ 7. WebSocket 接続開始                                      │
       │    io(socketUrl, {                                       │
       │      auth: { token }                                     │
       │    })                       │                             │
       ├─────────────────────────────────────────────────────────>│
       │                             │                             │
       │                             │                             │ 8. Token 検証
       │                             │                             │    - Token を
       │                             │                             │      デコード
       │                             │                             │    - HMAC 再計算
       │                             │                             │    - 一致確認
       │                             │                             │
       │ 9. 接続確立 ✅                │                             │
       │<─────────────────────────────────────────────────────────┤
       │    event: 'connect'         │                             │
       │                             │                             │
       │                             │                             │
       │ 10. 新しい通知を受信          │                             │
       │<─────────────────────────────────────────────────────────┤
       │    event: 'notification_received'                        │
       │    data: { ... }            │                             │
       │                             │                             │
       │ 11. 未読数を自動更新          │                             │
       │    (リロード不要)            │                             │
       │                             │                             │
```

---

## 🛠️ 実装詳細

### 1. Backend 実装

#### 1.1 Novu Adapter に Token 生成メソッドを追加

**ファイル**: `backend/api/adapters/novu_adapter.py`

```python
import hmac
import hashlib

class NovuAdapter:
    def __init__(self, api_key: Optional[str] = None, backend_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("NOVU_API_KEY")
        self.backend_url = backend_url or os.getenv("NOVU_API_URL", "http://localhost:3000")
        # ... 他の初期化コード
    
    def get_subscriber_token(self, subscriber_id: str) -> str:
        """
        Subscriber用のHMAC tokenを生成
        
        Args:
            subscriber_id: 購読者ID（ユーザーID）
            
        Returns:
            HMAC token文字列
        """
        # Novu API KeyをシークレットとしてHMAC-SHA256でトークンを生成
        message = subscriber_id.encode('utf-8')
        secret = self.api_key.encode('utf-8')
        
        hmac_hash = hmac.new(secret, message, hashlib.sha256)
        token = hmac_hash.hexdigest()
        
        logger.info(f"Generated subscriber token for: {subscriber_id}")
        return token
```

#### 1.2 API エンドポイントを追加

**ファイル**: `backend/api/controllers/notification_controller.py`

```python
from pydantic import BaseModel

class SubscriberTokenResponse(BaseModel):
    subscriberToken: str

@router.get("/subscriber-token", response_model=SubscriberTokenResponse)
async def get_subscriber_token(
    current_user = Depends(get_current_user),
    novu_adapter: NovuAdapter = Depends(get_novu_adapter)
):
    """
    Novu WebSocket接続用のsubscriber tokenを取得
    """
    try:
        subscriber_id = str(current_user.user_id)
        token = novu_adapter.get_subscriber_token(subscriber_id)
        return {"subscriberToken": token}
    except Exception as e:
        logger.error(f"Failed to get subscriber token: {str(e)}")
        raise HTTPException(status_code=500, detail="Subscriber tokenの取得に失敗しました")
```

---

### 2. Frontend 実装

#### 2.1 WebSocket 接続を Token 認証に更新

**ファイル**: `frontend/src/hooks/useNovuNotifications.ts`

```typescript
// 初期化とWebSocket接続
useEffect(() => {
  // 初期データ取得
  fetchNotifications(0, false);
  fetchUnreadCount();

  // WebSocket接続用のsubscriber tokenを取得
  const initWebSocket = async () => {
    try {
      // Backend APIからsubscriber tokenを取得
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

      // WebSocket接続（subscriber tokenを使用）
      const socket = io(socketUrl, {
        transports: ['websocket', 'polling'],
        auth: {
          token: subscriberToken,  // ← HMAC token を使用
        },
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 5,
      });

      socketRef.current = socket;

      // 接続成功
      socket.on('connect', () => {
        console.log('✅ Novu WebSocket connected');
      });

      // 新しい通知を受信
      socket.on('notification_received', (notification: Notification) => {
        console.log('📬 New notification received:', notification);
        setNotifications((prev) => [notification, ...prev]);
        setUnreadCount((prev) => prev + 1);

        // ブラウザ通知を表示
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification(notification.content, {
            body: notification.payload?.content || '',
            icon: '/logo.jpg',
          });
        }
      });

      // 接続エラー
      socket.on('connect_error', (err) => {
        console.error('❌ WebSocket connection error:', err);
      });

      // 切断
      socket.on('disconnect', (reason) => {
        console.log('🔌 WebSocket disconnected:', reason);
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
    }
  };
}, [subscriberId, applicationIdentifier, socketUrl, backendUrl, fetchNotifications, fetchUnreadCount]);
```

---

## 🌐 環境変数設定

### Backend 環境変数

**ファイル**: `docker-compose.full.dev.yml`

```yaml
chatbot-backend:
  environment:
    # Novu通知設定
    - NOVU_API_KEY=c47cfb7a083c4e27f9d1b523a20ed59f  # ← Token 生成に使用
    - NOVU_API_URL=http://novu-api:3000
```

### Frontend 環境変数

**ファイル**: `docker-compose.full.dev.yml`

```yaml
chatbot-frontend:
  build:
    args:
      # Novu 通知設定（构建时环境变量）
      VITE_NOVU_APP_ID: "waSFEThbij4o"
      VITE_NOVU_API_URL: "http://localhost:3000"
      VITE_NOVU_WS_URL: "http://localhost:3002"      # ← WebSocket URL
      VITE_BACKEND_URL: "http://localhost:8000"      # ← Backend API URL
```

---

## 🧪 テスト方法

### 1. Backend と Frontend をビルド

```bash
cd /path/to/project
docker compose -f docker-compose.full.dev.yml up -d --build chatbot-backend chatbot-frontend
```

### 2. ブラウザで確認

1. http://localhost:3001 にアクセス
2. ログイン（例: admin/admin123）
3. F12 でコンソールを開く
4. 以下のログを確認：

```
✅ Novu WebSocket connected
```

### 3. 通知を送信してテスト

別のターミナルで：

```bash
cd langchainChatBot/novu-integration/template/ssflow
python ssflow_tool.py send 1
```

### 4. 期待される動作

- ✅ コンソールに `📬 New notification received: {...}` が表示される
- ✅ 通知ベルのバッジ数が自動的に増える（リロード不要）
- ✅ ブラウザ通知が表示される（許可している場合）

---

## 🔍 トラブルシューティング

### 問題 1: WebSocket が接続後すぐに切断される

**症状**:
```
✅ WebSocket connected successfully!
🔌 Disconnected: io server disconnect
```

**原因**: Token が提供されていない、または無効

**解決策**:
1. Backend API `/api/notifications/subscriber-token` が正常に動作しているか確認
2. ブラウザコンソールで token が取得できているか確認：
   ```javascript
   // コンソールで実行
   fetch('http://localhost:8000/api/notifications/subscriber-token', {
     headers: {
       'Authorization': 'Bearer ' + localStorage.getItem('access_token')
     }
   }).then(r => r.json()).then(console.log)
   ```

### 問題 2: "No token was found during connection process"

**症状**: Novu WebSocket サーバーのログに以下が表示される：
```
"No token was found during counnection process for ..."
```

**原因**: WebSocket 接続時に `auth.token` が送信されていない

**解決策**:
1. Frontend の `useNovuNotifications.ts` で `auth: { token: subscriberToken }` が設定されているか確認
2. `subscriberToken` が正しく取得できているか確認

### 問題 3: Backend API が 500 エラーを返す

**症状**: `/api/notifications/subscriber-token` が失敗する

**原因**: `NOVU_API_KEY` 環境変数が設定されていない

**解決策**:
```bash
# Backend コンテナの環境変数を確認
docker exec chatbot-backend env | grep NOVU_API_KEY

# 出力例:
# NOVU_API_KEY=c47cfb7a083c4e27f9d1b523a20ed59f
```

---

## 📊 セキュリティ考慮事項

### ✅ 安全な実装

1. **Token は Backend で生成**
   - Frontend は Token を生成できない
   - Novu API Key は Backend のみが知っている

2. **JWT 認証を使用**
   - `/api/notifications/subscriber-token` は JWT で保護されている
   - ログインしたユーザーのみが自分の Token を取得できる

3. **Token は確定的**
   - 同じユーザーIDから常に同じ Token を生成
   - データベースに保存する必要がない
   - 漏洩しても再生成可能

### ⚠️ 注意事項

1. **NOVU_API_KEY を保護**
   - 環境変数として設定
   - Git にコミットしない
   - Frontend に公開しない

2. **HTTPS を使用**（本番環境）
   - WebSocket 接続は `wss://` を使用
   - Token の盗聴を防ぐ

---

## 📚 参考リンク

- [Novu 公式ドキュメント](https://docs.novu.co/)
- [Novu WebSocket API](https://docs.novu.co/platform/websockets)
- [Socket.IO 認証](https://socket.io/docs/v4/middlewares/#sending-credentials)

---

## ✅ チェックリスト

実装が完了したら、以下を確認してください：

- [ ] Backend に `get_subscriber_token()` メソッドを追加
- [ ] Backend に `/api/notifications/subscriber-token` API を追加
- [ ] Frontend で Token を取得してから WebSocket 接続
- [ ] 環境変数 `NOVU_API_KEY` が設定されている
- [ ] 環境変数 `VITE_NOVU_WS_URL` が設定されている
- [ ] ブラウザコンソールで `✅ Novu WebSocket connected` が表示される
- [ ] 通知送信時にリアルタイムで未読数が更新される

---

**最終更新**: 2026-01-22
