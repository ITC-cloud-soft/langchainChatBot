# Novu WebSocket リアルタイム通知 - 最終設定ガイド

**最終更新**: 2026-01-22  
**状態**: ✅ 完全動作確認済み

## 概要

Novu self-hosted (v0.24.0) の WebSocket リアルタイム通知システムが完全に実装され、動作確認済みです。

---

## 1. システム構成

### 必要なコンポーネント

1. **Backend (Python/FastAPI)**
   - JWT token 生成
   - Novu API との通信
   - Subscriber token エンドポイント

2. **Frontend (React/TypeScript)**
   - WebSocket 接続管理
   - リアルタイム通知受信
   - UI 更新

3. **Novu Services (Docker)**
   - novu-ws: WebSocket サーバー
   - novu-api: REST API サーバー
   - MongoDB: データベース
   - Redis: キャッシュ

---

## 2. Backend 設定

### 2.1 環境変数

`docker-compose.full.dev.yml`:
```yaml
chatbot-backend:
  environment:
    - NOVU_API_KEY=your_api_key
    - NOVU_API_URL=http://novu-api:3000
    - NOVU_JWT_SECRET=IhkmjMDFgvYO63NXBvLvCo1ywL47RY7HTHMG9WwQnhM=
```

### 2.2 JWT Token 生成

`backend/api/adapters/novu_adapter.py`:
```python
def get_subscriber_token(
    self, 
    subscriber_id: str, 
    environment_id: str = '6970876109344bb9ae9c0a63',
    organization_id: str = '6970876109344bb9ae9c0a5c'
) -> str:
    # Novu API から MongoDB ObjectId を取得
    subscriber = self.subscriber_api.get(subscriber_id)
    subscriber_object_id = getattr(subscriber, '_id', None) or subscriber_id
    
    # JWT payload（最小限の必須フィールド）
    payload = {
        '_id': subscriber_object_id,        # MongoDB ObjectId（必須）
        '_environmentId': environment_id,   # 環境 ID（必須）
        '_organizationId': organization_id, # 組織 ID（必須）
        'aud': 'widget_user',              # 受信者タイプ（必須）
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    
    return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
```

### 2.3 API エンドポイント

`backend/api/controllers/notification_controller.py`:
```python
@router.get("/subscriber-token")
async def get_subscriber_token(
    current_user = Depends(get_current_user),
    novu_adapter: NovuAdapter = Depends(get_novu_adapter)
):
    subscriber_id = str(current_user.user_id)
    token = novu_adapter.get_subscriber_token(subscriber_id)
    return {"subscriberToken": token}
```

---

## 3. Frontend 設定

### 3.1 環境変数

`frontend/Dockerfile`:
```dockerfile
ARG VITE_NOVU_WS_URL=http://localhost:3002
ARG VITE_BACKEND_URL=http://localhost:8000
```

### 3.2 WebSocket 接続

`frontend/src/hooks/useNovuNotifications.ts`:
```typescript
// JWT token を取得
const tokenResponse = await fetch(
  `${backendUrl}/api/notifications/subscriber-token`,
  {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  }
);
const { subscriberToken } = await tokenResponse.json();

// WebSocket 接続
const socket = io(socketUrl, {
  auth: { token: subscriberToken },
  transports: ['websocket', 'polling'],
  reconnection: true
});

// 通知受信（重要: message フィールドを解包）
socket.on('notification_received', (data: any) => {
  const notification = data.message || data;
  const normalizedNotification = {
    ...notification,
    _id: notification._id || notification.id
  };
  
  if (normalizedNotification._id) {
    setNotifications(prev => [normalizedNotification, ...prev]);
    setUnreadCount(prev => prev + 1);
  }
});
```

---

## 4. Novu Services 設定

### 4.1 環境変数

`novu-integration/docker.novu/.env.novu`:
```bash
JWT_SECRET=IhkmjMDFgvYO63NXBvLvCo1ywL47RY7HTHMG9WwQnhM=
```

### 4.2 Docker Compose

`novu-integration/docker.novu/docker-compose.novu.yml`:
```yaml
novu-ws:
  environment:
    - JWT_SECRET=${JWT_SECRET}
    - NODE_ENV=production
```

---

## 5. 重要なポイント

### 5.1 MongoDB ObjectId の使用

**問題**: Novu WS は JWT の `_id` フィールドを WebSocket 房間 ID として使用します。

**解決策**: 
1. Novu API から subscriber の MongoDB ObjectId を動的取得
2. JWT payload の `_id` に ObjectId を設定

```python
# ❌ 間違い
payload = {'_id': subscriber_id}  # "1" (文字列)

# ✅ 正しい
subscriber = self.subscriber_api.get(subscriber_id)
subscriber_object_id = getattr(subscriber, '_id', None)
payload = {'_id': subscriber_object_id}  # "69719fdf303893d0de04e8a6"
```

### 5.2 WebSocket データ構造

**問題**: Novu WS は通知を `{message: {...}}` の形式で送信します。

**解決策**: `message` フィールドを解包してから処理

```typescript
// ❌ 間違い
socket.on('notification_received', (notification) => {
  // notification._id は undefined
});

// ✅ 正しい
socket.on('notification_received', (data) => {
  const notification = data.message || data;
  // notification._id が正しく取得できる
});
```

### 5.3 通知 ID の正規化

**問題**: Novu API は `_id` または `id` フィールドを返す可能性があります。

**解決策**: 両方のフィールドをサポート

```typescript
const normalizedNotification = {
  ...notification,
  _id: notification._id || notification.id
};
```

---

## 6. 動作確認

### 6.1 WebSocket 接続確認

ブラウザコンソールで以下のログを確認：

```
✅ Novu WebSocket connected successfully!
```

### 6.2 リアルタイム通知テスト

```bash
cd langchainChatBot/novu-integration/template/ssflow
python ssflow_tool.py send 1
```

**期待される動作**:
- 📬 コンソールに `📬 New notification received via WebSocket` が表示
- 🔔 通知アイコンの数字が即座に増加
- 📝 新しい通知がリストに表示

### 6.3 Novu WS ログ確認

```bash
docker logs novu-ws --tail 20 | grep "Connection request accepted"
```

**期待される出力**:
```
Connection request accepted for 69719fdf303893d0de04e8a6
Sending event notification_received message to 69719fdf303893d0de04e8a6
```

---

## 7. トラブルシューティング

### 7.1 WebSocket 切断エラー

**症状**: `io server disconnect` エラー

**原因**: JWT token の形式が正しくない

**解決策**:
1. `aud: 'widget_user'` が含まれているか確認
2. `_id` が MongoDB ObjectId であることを確認
3. `_environmentId` と `_organizationId` が正しいか確認

### 7.2 通知が届かない

**症状**: WebSocket 接続は成功するが通知が届かない

**原因**: 房間 ID のミスマッチ

**解決策**:
1. Backend ログで `Retrieved subscriber ObjectId` を確認
2. Novu WS ログで `Connection request accepted for` の ID を確認
3. 両方の ID が一致しているか確認

### 7.3 通知 ID が undefined

**症状**: `POST /api/notifications/undefined/read 404`

**原因**: 通知データの `_id` フィールドが取得できていない

**解決策**:
1. `data.message` からの解包を確認
2. `_id` または `id` フィールドの正規化を確認

---

## 8. 実装済み機能

- ✅ WebSocket リアルタイム接続（JWT 認証）
- ✅ リアルタイム通知プッシュ（ページリフレッシュ不要）
- ✅ 未読数の自動更新
- ✅ 既読機能
- ✅ 削除機能
- ✅ 日付表示
- ✅ データフィルタリング（空データの除外）

---

## 9. 参考資料

- Novu 公式ドキュメント: https://docs.novu.co/
- Novu GitHub: https://github.com/novuhq/novu
- Socket.IO ドキュメント: https://socket.io/docs/

---

**最終確認日**: 2026-01-22  
**動作環境**: Novu v0.24.0 (self-hosted)  
**テスト状況**: ✅ 全機能正常動作確認済み
