# SSFlow 承認通知

✅ **検証済み**: ボタン付き通知が正常に動作

SSFlow ワークフロー承認通知を送信し、2つのアクションボタンを提供します。

## 📋 概要

- **通知内容**: 承認リクエストの通知
- **ボタン1**: 詳細を確認 (Primary - 青)
- **ボタン2**: SSFlow へ移動 (Secondary - グレー)

## 🚀 使用方法

### ワークフローを作成（初回のみ）

```bash
python ssflow_tool.py create-workflow
```

### テスト通知を送信

```bash
# ユーザーID "1" に送信
python ssflow_tool.py send 1

# ユーザー名 "admin" に送信（自動的にIDを検索）
python ssflow_tool.py send admin

# デフォルトユーザーに送信
python ssflow_tool.py send
```

### ワークフロー一覧を確認

```bash
python ssflow_tool.py list-workflows
```

### フロントエンドで確認

1. ブラウザで http://localhost:3001 にアクセス
2. ログイン（例: admin/admin123）
3. 通知ベルアイコンをクリック
4. **2つのボタンが表示される** 

## 📦 Backend 統合

`backend/api/services/notification_service.py` で使用：

```python
from api.services.notification_service import NotificationService

notification_service.send_workflow_approval(
    receiver_id="1",
    workflow_data={
        "WorkID": "WF-2024-001",
        "FlowName": "新規プロジェクト承認申請",
        "StarterName": "山田太郎"
    }
)
```

## 📦 重要な実装詳細

### ボタン情報の送信方法

Novu 自托管版では、ボタン情報は **payload に含めて送信**します：

```python
payload = {
    "title": "新しい承認リクエスト",
    "content": "承認リクエストが届きました",
    "workflowId": "WF-2024-001",
    "buttons": [  # ← ボタン情報を payload に含める
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
    ]
}
```

### フロントエンドでの表示

`NotificationBell.tsx` が `payload.buttons` を読み取り、ボタンを表示します。

## � トラブルシューティング

### 通知が表示されない

1. **ユーザーIDを確認**
   - ログインしているユーザーIDと送信先が一致しているか確認
   - ブラウザコンソールで: `console.log(localStorage.getItem('user_id'))`

2. **通知を確認**
   ```bash
   python check_all_workflows.py  # ワークフロー確認
   ```

### ボタンが表示されない

- Frontend が再ビルドされているか確認
- `payload.buttons` が正しく送信されているか確認

## 📄 ファイル構成

```
template/ssflow/
├── README.md                              # このファイル
├── create_ssflow_approval_workflow.py     # ワークフロー作成
├── send_ssflow_notification.py            # テスト通知送信（推奨）
├── test_ssflow_approval_workflow.py       # 詳細テスト
└── check_all_workflows.py                 # ワークフロー確認
```

## 🌐 環境変数

```bash
export NOVU_API_KEY="c47cfb7a083c4e27f9d1b523a20ed59f"
export NOVU_API_URL="http://localhost:3000"
export SSFLOW_URL="http://192.168.1.78:56145/wwwroot/login.html"
```

## ✅ 検証済み機能

- ✅ **Workflow**: `ssflow-approval-notification` が正常に動作
- ✅ **Backend**: `notification_service.send_workflow_approval()` でボタン情報を自動送信
- ✅ **Frontend**: `NotificationBell.tsx` が `payload.buttons` を読み取り、ボタンを表示
- ✅ **ボタン表示**: Primary（青）と Secondary（グレー）の2つのボタンが正しく表示
- ✅ **テスト**: `send_ssflow_notification.py` で簡単にテスト可能

## 📝 実装のポイント

### ボタンが表示される仕組み

1. **Backend** (`notification_service.py`):
   ```python
   payload = {
       "buttons": [
           {"type": "primary", "content": "詳細を確認", "url": "..."},
           {"type": "secondary", "content": "SSFlow へ移動", "url": "..."}
       ]
   }
   ```

2. **Novu**: payload をそのまま保存・配信

3. **Frontend** (`NotificationBell.tsx`):
   ```typescript
   {item.payload?.buttons && item.payload.buttons.length > 0 && (
     <Box>
       {item.payload.buttons.map((button) => (
         <Button variant={button.type === 'primary' ? 'contained' : 'outlined'}>
           {button.content}
         </Button>
       ))}
     </Box>
   )}
   ```

## 🎯 次のステップ

### 「詳細を確認」ボタンの実装

現在、ボタンは表示されますが、クリック時の処理は今後実装予定です：

1. **Backend エンドポイント作成**:
   ```python
   @router.get("/api/approval/session/{workflow_id}")
   async def create_approval_session(workflow_id: str):
       # Bot セッションを作成
       # ワークフロー詳細を返す
   ```

2. **Frontend 処理**:
   - ボタンクリック → Bot チャットを開く
   - セッション情報を表示
   - 承認/却下アクションを提供
