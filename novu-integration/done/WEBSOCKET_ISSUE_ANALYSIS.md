# Novu WebSocket 認証問題の詳細分析

## 🔍 問題の現象

### 観察された動作

1. **ブラウザコンソール**:
   ```
   ✅ Novu WebSocket connected
   🔌 WebSocket disconnected: io server disconnect
   ```

2. **Novu WebSocket サーバーログ**:
   - Socket.IO 接続の記録が**一切ない**
   - 健康チェック（Wget）のログのみ

3. **Backend API**:
   - ✅ Subscriber Token 生成は成功
   - ✅ Token: `e660b8e473b1414d9d802daddf2a4154fb34fc67916b4451027a409267a21623`

## 🧪 実装した認証方式

### 1. Token 生成（Backend）

```python
# backend/api/adapters/novu_adapter.py
def get_subscriber_token(self, subscriber_id: str) -> str:
    message = subscriber_id.encode('utf-8')
    secret = self.api_key.encode('utf-8')  # Novu API Key
    
    hmac_hash = hmac.new(secret, message, hashlib.sha256)
    token = hmac_hash.hexdigest()
    
    return token
```

**生成例**:
- Input: `subscriber_id = "1"`, `api_key = "c47cfb7a083c4e27f9d1b523a20ed59f"`
- Output: `e660b8e473b1414d9d802daddf2a4154fb34fc67916b4451027a409267a21623`

### 2. WebSocket 接続（Frontend）

```typescript
// frontend/src/hooks/useNovuNotifications.ts
const socket = io(socketUrl, {
  transports: ['websocket', 'polling'],
  auth: {
    token: subscriberToken,  // HMAC token
  },
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 5,
});
```

## 🔬 問題の根本原因

### 原因 1: Socket.IO のバージョン不一致

**可能性**: Frontend の Socket.IO クライアントと Novu WS サーバーの Socket.IO バージョンが異なる

**確認方法**:
```bash
# Frontend の Socket.IO バージョン
cat frontend/package.json | grep socket.io-client

# Novu WS の Socket.IO バージョン
docker exec novu-ws cat /usr/src/app/package.json | grep socket.io
```

### 原因 2: 認証方式の不一致

**Novu の期待する認証方式**:

Novu self-hosted 版（v0.24.0）の WebSocket 認証は、以下のいずれかを期待している可能性があります：

1. **Query パラメータ方式**:
   ```typescript
   io(socketUrl, {
     query: {
       subscriberId: '1',
       applicationIdentifier: 'waSFEThbij4o',
     }
   });
   ```

2. **JWT Token 方式**:
   ```typescript
   io(socketUrl, {
     auth: {
       token: 'JWT_TOKEN',  // JWT 形式のトークン
     }
   });
   ```

3. **HMAC Token 方式（我々の実装）**:
   ```typescript
   io(socketUrl, {
     auth: {
       token: 'HMAC_HEX_STRING',  // HMAC-SHA256 の16進数文字列
     }
   });
   ```

**問題**: Novu が期待する形式と我々が送信する形式が一致していない

### 原因 3: Novu WS サーバーの認証ミドルウェア

Novu WS サーバーのログに "No token was found" というメッセージが以前表示されていました。これは：

- サーバーが `auth.token` を認識していない
- または、token の検証に失敗している

## 🔍 詳細な診断

### 1. Novu のソースコードを確認

Novu の WebSocket 認証実装を確認する必要があります：

```bash
# Novu WS のソースコードを確認
docker exec novu-ws find /usr/src/app -name "*.js" -path "*/ws/*" | head -20
```

### 2. Socket.IO のデバッグモードを有効化

Frontend で Socket.IO のデバッグログを有効にする：

```typescript
import { io } from 'socket.io-client';

// デバッグモードを有効化
localStorage.debug = 'socket.io-client:*';

const socket = io(socketUrl, {
  transports: ['websocket', 'polling'],
  auth: {
    token: subscriberToken,
  },
});
```

これにより、詳細な接続ログが表示されます。

### 3. Novu Dashboard の設定を確認

Novu Dashboard (http://localhost:4200) で以下を確認：

1. **Settings → API Keys**:
   - API Key が正しいか
   - Environment が正しいか

2. **Settings → Security**:
   - HMAC 認証が有効になっているか
   - Subscriber Hash が必要か

## 💡 解決策の選択肢

### 選択肢 1: Query パラメータ方式に変更 ⭐ 推奨

**理由**: Novu の古いバージョンや self-hosted 版では、この方式が最も互換性が高い

**実装**:
```typescript
const socket = io(socketUrl, {
  transports: ['websocket', 'polling'],
  query: {
    subscriberId: subscriberId,
    applicationIdentifier: applicationIdentifier,
  },
  reconnection: true,
});
```

**メリット**:
- ✅ シンプル
- ✅ Token 生成不要
- ✅ 互換性が高い

**デメリット**:
- ⚠️ セキュリティが低い（subscriberId が URL に含まれる）
- ⚠️ 認証なし（誰でも他人の通知を受信できる可能性）

### 選択肢 2: JWT Token 方式

**実装**:

Backend で JWT Token を生成：
```python
import jwt
from datetime import datetime, timedelta

def get_subscriber_jwt_token(self, subscriber_id: str) -> str:
    payload = {
        'subscriberId': subscriber_id,
        'environmentId': self.environment_id,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, self.api_key, algorithm='HS256')
    return token
```

Frontend で使用：
```typescript
const socket = io(socketUrl, {
  auth: {
    token: jwtToken,  // JWT token
  },
});
```

**メリット**:
- ✅ セキュリティが高い
- ✅ 有効期限を設定できる

**デメリット**:
- ⚠️ Novu が JWT を期待しているか不明
- ⚠️ 実装が複雑

### 選択肢 3: 定期ポーリング ⭐ 最も確実

**実装**:
```typescript
// 15秒ごとに通知をチェック
const pollInterval = setInterval(() => {
  fetchNotifications(0, false);
  fetchUnreadCount();
}, 15000);
```

**メリット**:
- ✅ WebSocket 認証不要
- ✅ 確実に動作する
- ✅ 実装がシンプル
- ✅ Novu のバージョンに依存しない

**デメリット**:
- ⚠️ リアルタイム性が低い（最大15秒の遅延）
- ⚠️ サーバー負荷が若干高い

### 選択肢 4: Novu Cloud 版を使用

**説明**: Self-hosted 版ではなく、Novu の Cloud 版（SaaS）を使用する

**メリット**:
- ✅ WebSocket 認証が正常に動作
- ✅ 最新機能が使える
- ✅ メンテナンス不要

**デメリット**:
- ⚠️ 有料（無料枠あり）
- ⚠️ データが外部に保存される

## 🎯 推奨アプローチ

### 短期的解決策（今すぐ動作させる）

**定期ポーリング（選択肢 3）を使用**

理由：
1. ✅ 確実に動作する
2. ✅ 実装済み（すぐに使える）
3. ✅ 15秒間隔なら実用的
4. ✅ Novu のバージョンや設定に依存しない

### 長期的解決策（将来的に改善）

**Query パラメータ方式（選択肢 1）を試す**

手順：
1. Frontend の WebSocket 接続を Query パラメータ方式に変更
2. テストして動作するか確認
3. 動作すれば、セキュリティ要件に応じて JWT 方式を検討

## 🧪 テスト手順

### Query パラメータ方式をテストする

1. **Frontend を修正**:
   ```typescript
   // useNovuNotifications.ts
   const socket = io(socketUrl, {
     transports: ['websocket', 'polling'],
     query: {
       subscriberId: subscriberId,
       applicationIdentifier: applicationIdentifier,
     },
   });
   ```

2. **ビルドして再起動**:
   ```bash
   docker compose -f docker-compose.full.dev.yml up -d --build chatbot-frontend
   ```

3. **ログを確認**:
   ```bash
   # Novu WS のログを監視
   docker logs novu-ws -f
   ```

4. **ブラウザで確認**:
   - F12 でコンソールを開く
   - `✅ Novu WebSocket connected` が表示される
   - `🔌 WebSocket disconnected` が**表示されない**

5. **通知を送信**:
   ```bash
   python ssflow_tool.py send 1
   ```

6. **期待される結果**:
   - コンソールに `📬 New notification received` が表示される
   - 未読バッジが自動更新される

## 📊 比較表

| 方式 | セキュリティ | 実装難易度 | 互換性 | リアルタイム性 | 推奨度 |
|------|------------|-----------|--------|--------------|--------|
| Query パラメータ | ⚠️ 低 | ✅ 簡単 | ✅ 高 | ✅ 即時 | ⭐⭐⭐ |
| HMAC Token | ✅ 高 | ⚠️ 中 | ❌ 低 | ✅ 即時 | ⭐ |
| JWT Token | ✅ 高 | ⚠️ 中 | ❓ 不明 | ✅ 即時 | ⭐⭐ |
| 定期ポーリング | ✅ 高 | ✅ 簡単 | ✅ 高 | ⚠️ 15秒遅延 | ⭐⭐⭐⭐ |
| Novu Cloud | ✅ 高 | ✅ 簡単 | ✅ 高 | ✅ 即時 | ⭐⭐⭐⭐⭐ |

## 🔧 次のステップ

### オプション A: 定期ポーリングを使用（推奨）

**理由**: 確実に動作し、実用的

**実装**: すでに完了（コード修正済み）

**必要な作業**:
```bash
docker compose -f docker-compose.full.dev.yml up -d --build chatbot-frontend
```

### オプション B: Query パラメータ方式を試す

**理由**: WebSocket のリアルタイム性を活用したい場合

**必要な作業**:
1. Frontend のコードを修正
2. ビルドしてテスト
3. 動作確認

### オプション C: Novu のサポートに問い合わせ

**理由**: Self-hosted 版の正しい認証方式を確認

**問い合わせ内容**:
- Novu v0.24.0 の WebSocket 認証方式
- HMAC Token の正しい送信方法
- `auth.token` vs `query` パラメータ

## 📚 参考情報

- **Novu バージョン**: 0.24.0
- **Socket.IO**: クライアント/サーバーのバージョン確認が必要
- **認証方式**: Novu 公式ドキュメントに明確な記載なし（self-hosted 版）

---

**結論**: 現時点では**定期ポーリング方式**が最も確実で実用的な解決策です。WebSocket を使用したい場合は、Query パラメータ方式を試すことをお勧めします。
