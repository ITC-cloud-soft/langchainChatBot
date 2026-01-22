# Novu API リファレンス

このドキュメントは、プロジェクトで使用している Novu API のエンドポイントをまとめたものです。

## 📋 目次

- [認証](#認証)
- [Subscribers（購読者）](#subscribers購読者)
- [Notifications（通知）](#notifications通知)
- [Workflows（ワークフロー）](#workflowsワークフロー)
- [Events（イベント）](#eventsイベント)
- [Notification Groups](#notification-groups)

---

## 認証

すべての API リクエストには、以下のヘッダーが必要です：

```http
Authorization: ApiKey YOUR_API_KEY
Content-Type: application/json
```

**API Key の取得方法**:
- Novu Dashboard (http://localhost:4200) にアクセス
- Settings → API Keys から取得

**環境変数**:
```bash
NOVU_API_KEY=c47cfb7a083c4e27f9d1b523a20ed59f
NOVU_API_URL=http://localhost:3000
```

---

## Subscribers（購読者）

### 1. Subscriber を作成

**エンドポイント**: `POST /v1/subscribers`

**説明**: 新しい購読者を作成します。

**リクエスト**:
```json
{
  "subscriberId": "1",
  "email": "user@example.com",
  "firstName": "Test",
  "lastName": "User",
  "phone": "+81-90-1234-5678",
  "avatar": "https://example.com/avatar.jpg",
  "locale": "ja_JP",
  "data": {
    "customField": "value"
  }
}
```

**レスポンス**: `200 OK` / `201 Created`
```json
{
  "data": {
    "_id": "69719fdf303893d0de04e8a6",
    "subscriberId": "1",
    "email": "user@example.com",
    "firstName": "Test",
    "lastName": "User",
    "createdAt": "2026-01-22T03:56:15.849Z",
    "updatedAt": "2026-01-22T07:20:27.778Z"
  }
}
```

**使用例**:
```python
import requests

url = "http://localhost:3000/v1/subscribers"
headers = {
    "Authorization": "ApiKey c47cfb7a083c4e27f9d1b523a20ed59f",
    "Content-Type": "application/json"
}
data = {
    "subscriberId": "1",
    "email": "1@example.com",
    "firstName": "Test",
    "lastName": "User"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

---

### 2. Subscriber を取得

**エンドポイント**: `GET /v1/subscribers/{subscriberId}`

**説明**: 指定された subscriberId の購読者情報を取得します。

**レスポンス**: `200 OK`
```json
{
  "data": {
    "_id": "69719fdf303893d0de04e8a6",
    "subscriberId": "1",
    "email": "1@example.com",
    "firstName": "Test",
    "lastName": "User",
    "channels": [],
    "deleted": false,
    "createdAt": "2026-01-22T03:56:15.849Z",
    "updatedAt": "2026-01-22T07:20:27.778Z"
  }
}
```

**使用例**:
```python
url = "http://localhost:3000/v1/subscribers/1"
headers = {"Authorization": "ApiKey c47cfb7a083c4e27f9d1b523a20ed59f"}

response = requests.get(url, headers=headers)
print(response.json())
```

---

### 3. Subscriber を更新

**エンドポイント**: `PUT /v1/subscribers/{subscriberId}`

**説明**: 購読者情報を更新します。

**リクエスト**:
```json
{
  "email": "newemail@example.com",
  "firstName": "Updated",
  "lastName": "Name"
}
```

---

### 4. Subscriber を削除

**エンドポイント**: `DELETE /v1/subscribers/{subscriberId}`

**説明**: 購読者を削除します。

**レスポンス**: `200 OK`

---

## Notifications（通知）

### 1. 通知一覧を取得

**エンドポイント**: `GET /v1/notifications`

**説明**: すべての通知を取得します（ページネーション対応）。

**クエリパラメータ**:
- `page`: ページ番号（デフォルト: 0）
- `limit`: 1ページあたりの件数（デフォルト: 10）

**レスポンス**: `200 OK`
```json
{
  "page": 0,
  "hasMore": true,
  "pageSize": 10,
  "data": [
    {
      "_id": "6971cfbb31aa9a841588f551",
      "_templateId": "6971bb47303893d0de04ede8",
      "_subscriberId": "69719fdf303893d0de04e8a6",
      "transactionId": "5615cf0b-b19b-41ee-86ed-3fda5de85639",
      "channels": ["in_app"],
      "to": {
        "subscriberId": "1"
      },
      "payload": {
        "title": "新しい承認リクエスト",
        "content": "山田太郎さんから新規プロジェクト承認申請の承認リクエストが届きました",
        "workflowId": "WF-2024-001",
        "buttons": [
          {
            "type": "primary",
            "content": "詳細を確認",
            "url": "/api/approval/session/WF-2024-001"
          }
        ]
      },
      "createdAt": "2026-01-22T07:20:27.123Z"
    }
  ]
}
```

**使用例**:
```python
url = "http://localhost:3000/v1/notifications?page=0&limit=10"
headers = {"Authorization": "ApiKey c47cfb7a083c4e27f9d1b523a20ed59f"}

response = requests.get(url, headers=headers)
data = response.json()

# 特定ユーザーの通知のみフィルター
user_notifications = [n for n in data['data'] 
                      if n.get('to', {}).get('subscriberId') == '1']
```

---

### 2. 通知を既読にする

**エンドポイント**: `POST /v1/notifications/{notificationId}/read`

**説明**: 指定された通知を既読にします。

**レスポンス**: `200 OK`

---

### 3. 通知を削除

**エンドポイント**: `DELETE /v1/notifications/{notificationId}`

**説明**: 指定された通知を削除します。

**レスポンス**: `200 OK`

---

### ⚠️ 利用不可のエンドポイント

以下のエンドポイントは **404 Not Found** を返します：

```
❌ GET /v1/subscribers/{subscriberId}/notifications
```

代わりに `GET /v1/notifications` を使用し、クライアント側でフィルターしてください。

---

## Workflows（ワークフロー）

### 1. ワークフロー一覧を取得

**エンドポイント**: `GET /v1/workflows`

**説明**: すべてのワークフローを取得します。

**レスポンス**: `200 OK`
```json
{
  "data": [
    {
      "_id": "6971c2bf303893d0de04f005",
      "name": "Workflow Approval",
      "triggers": [
        {
          "identifier": "workflow-approval",
          "type": "event"
        }
      ],
      "active": true,
      "draft": false,
      "tags": ["ssflow", "approval", "workflow"],
      "description": "ワークフロー承認通知",
      "steps": [
        {
          "template": {
            "type": "in_app",
            "content": "{{content}}",
            "subject": "{{title}}"
          }
        }
      ]
    }
  ]
}
```

**使用例**:
```python
url = "http://localhost:3000/v1/workflows"
headers = {"Authorization": "ApiKey c47cfb7a083c4e27f9d1b523a20ed59f"}

response = requests.get(url, headers=headers)
workflows = response.json()['data']

for workflow in workflows:
    print(f"Name: {workflow['name']}")
    print(f"Trigger ID: {workflow['triggers'][0]['identifier']}")
    print(f"Active: {workflow['active']}")
```

---

### 2. ワークフローを作成

**エンドポイント**: `POST /v1/workflows`

**説明**: 新しいワークフローを作成します。

**リクエスト**:
```json
{
  "name": "Workflow Approval",
  "notificationGroupId": "6970876109344bb9ae9c0a64",
  "tags": ["ssflow", "approval", "workflow"],
  "description": "ワークフロー承認通知",
  "steps": [
    {
      "template": {
        "type": "in_app",
        "content": "{{content}}",
        "subject": "{{title}}",
        "avatar": "https://api.dicebear.com/7.x/shapes/svg?seed=workflow"
      },
      "active": true,
      "shouldStopOnFail": false,
      "filters": []
    }
  ],
  "active": true,
  "draft": false
}
```

**レスポンス**: `200 OK` / `201 Created`
```json
{
  "data": {
    "_id": "6971c2bf303893d0de04f005",
    "name": "Workflow Approval",
    "triggers": [
      {
        "identifier": "workflow-approval",
        "type": "event"
      }
    ]
  }
}
```

---

### 3. ワークフローを取得

**エンドポイント**: `GET /v1/workflows/{workflowId}`

**説明**: 指定されたワークフローの詳細を取得します。

---

### 4. ワークフローを更新

**エンドポイント**: `PUT /v1/workflows/{workflowId}`

**説明**: ワークフローを更新します。

---

### 5. ワークフローを削除

**エンドポイント**: `DELETE /v1/workflows/{workflowId}`

**説明**: ワークフローを削除します。

---

## Events（イベント）

### イベントをトリガー（通知を送信）

**エンドポイント**: `POST /v1/events/trigger`

**説明**: ワークフローをトリガーして通知を送信します。

**リクエスト**:
```json
{
  "name": "workflow-approval",
  "to": {
    "subscriberId": "1"
  },
  "payload": {
    "title": "新しい承認リクエスト",
    "content": "山田太郎さんから新規プロジェクト承認申請の承認リクエストが届きました",
    "workflowId": "WF-2024-001",
    "flowName": "新規プロジェクト承認申請",
    "starterName": "山田太郎",
    "buttons": [
      {
        "type": "primary",
        "content": "詳細を確認",
        "url": "/api/approval/session/WF-2024-001"
      },
      {
        "type": "secondary",
        "content": "SSFlow へ移動",
        "url": "http://192.168.1.78:56145/wwwroot/login.html"
      }
    ],
    "notificationType": "ssflow_approval"
  }
}
```

**レスポンス**: `200 OK` / `201 Created`
```json
{
  "data": {
    "acknowledged": true,
    "status": "processed",
    "transactionId": "5615cf0b-b19b-41ee-86ed-3fda5de85639"
  }
}
```

**使用例**:
```python
url = "http://localhost:3000/v1/events/trigger"
headers = {
    "Authorization": "ApiKey c47cfb7a083c4e27f9d1b523a20ed59f",
    "Content-Type": "application/json"
}
data = {
    "name": "workflow-approval",
    "to": {"subscriberId": "1"},
    "payload": {
        "title": "新しい承認リクエスト",
        "content": "承認リクエストが届きました",
        "workflowId": "WF-2024-001",
        "buttons": [
            {
                "type": "primary",
                "content": "詳細を確認",
                "url": "/api/approval/session/WF-2024-001"
            }
        ]
    }
}

response = requests.post(url, json=data, headers=headers)
print(f"Transaction ID: {response.json()['data']['transactionId']}")
```

---

## Notification Groups

### Notification Group 一覧を取得

**エンドポイント**: `GET /v1/notification-groups`

**説明**: すべての通知グループを取得します。

**レスポンス**: `200 OK`
```json
{
  "data": [
    {
      "_id": "6970876109344bb9ae9c0a64",
      "name": "General",
      "_organizationId": "6970876109344bb9ae9c0a5c",
      "_environmentId": "6970876109344bb9ae9c0a63",
      "createdAt": "2026-01-21T02:03:45.123Z",
      "updatedAt": "2026-01-21T02:03:45.123Z"
    }
  ]
}
```

**使用例**:
```python
url = "http://localhost:3000/v1/notification-groups"
headers = {"Authorization": "ApiKey c47cfb7a083c4e27f9d1b523a20ed59f"}

response = requests.get(url, headers=headers)
groups = response.json()['data']
notification_group_id = groups[0]['_id']  # ワークフロー作成時に使用
```

---

## 📚 使用例

### 完全な通知送信フロー

```python
import requests

NOVU_API_KEY = "c47cfb7a083c4e27f9d1b523a20ed59f"
NOVU_API_URL = "http://localhost:3000"

headers = {
    "Authorization": f"ApiKey {NOVU_API_KEY}",
    "Content-Type": "application/json"
}

# 1. Subscriber を作成
subscriber_data = {
    "subscriberId": "1",
    "email": "user@example.com",
    "firstName": "Test",
    "lastName": "User"
}
response = requests.post(
    f"{NOVU_API_URL}/v1/subscribers",
    json=subscriber_data,
    headers=headers
)
print(f"Subscriber created: {response.status_code}")

# 2. 通知を送信
event_data = {
    "name": "workflow-approval",
    "to": {"subscriberId": "1"},
    "payload": {
        "title": "新しい承認リクエスト",
        "content": "承認リクエストが届きました",
        "workflowId": "WF-2024-001",
        "buttons": [
            {
                "type": "primary",
                "content": "詳細を確認",
                "url": "/api/approval/session/WF-2024-001"
            }
        ]
    }
}
response = requests.post(
    f"{NOVU_API_URL}/v1/events/trigger",
    json=event_data,
    headers=headers
)
transaction_id = response.json()['data']['transactionId']
print(f"Notification sent: {transaction_id}")

# 3. 通知を確認
response = requests.get(
    f"{NOVU_API_URL}/v1/notifications",
    headers=headers
)
notifications = response.json()['data']
user_notifications = [n for n in notifications 
                      if n.get('to', {}).get('subscriberId') == '1']
print(f"User has {len(user_notifications)} notifications")
```

---

## 🔗 関連リンク

- **Novu Dashboard**: http://localhost:4200
- **Novu API**: http://localhost:3000
- **Novu WebSocket**: http://localhost:3002
- **公式ドキュメント**: https://docs.novu.co/api-reference/overview

---

## 📝 注意事項

### 1. Self-hosted 版の制限

- CTA ボタンは workflow 定義では動作しません
- ボタン情報は **payload に含めて送信**する必要があります

### 2. Subscriber ID のマッピング

- Frontend のユーザーID と Novu の subscriberId を一致させる必要があります
- Backend で適切にマッピングを管理してください

### 3. WebSocket 通知

- リアルタイム通知を受信するには WebSocket 接続が必要です
- WebSocket URL: `http://localhost:3002`
- Frontend で `socket.io-client` を使用して接続

### 4. エラーハンドリング

- すべての API リクエストで適切なエラーハンドリングを実装してください
- 特に `404 Not Found` や `401 Unauthorized` に注意

---

## 🛠️ トラブルシューティング

### 401 Unauthorized

**原因**: API Key が無効または期限切れ

**解決策**:
1. Novu Dashboard で API Key を確認
2. 環境変数 `NOVU_API_KEY` を更新

### 404 Not Found

**原因**: エンドポイントが存在しない、または subscriberId が間違っている

**解決策**:
1. エンドポイントのスペルを確認
2. subscriberId が正しいか確認
3. このドキュメントで正しいエンドポイントを確認

### 通知が届かない

**原因**: Subscriber が存在しない、またはワークフローが無効

**解決策**:
1. Subscriber が作成されているか確認
2. ワークフローが `active: true` になっているか確認
3. Trigger ID が正しいか確認

---

**最終更新**: 2026-01-22
