# Novu WebSocket リアルタイム通知 - クイックスタート

**最終更新**: 2026-01-22  
**所要時間**: 5分  
**難易度**: ⭐⭐☆☆☆

## 🚀 3ステップで起動

### ステップ1: Novu サービス起動 (2分)

```bash
cd novu-integration/docker.novu

# 環境変数ファイルを確認（既に設定済みの場合はスキップ）
# .env.novu ファイルに JWT_SECRET が設定されていることを確認

# Novu サービスを起動
docker-compose -f docker-compose.novu.yml up -d

# サービスが起動するまで待機（約30秒）
docker-compose -f docker-compose.novu.yml logs -f novu-api
```

### ステップ2: Backend・Frontend 起動 (2分)

```bash
cd ../../

# Backend と Frontend を起動
docker-compose -f docker-compose.full.dev.yml up -d

# ログを確認
docker-compose -f docker-compose.full.dev.yml logs -f chatbot-backend
```

### ステップ3: 動作確認 (1分)

```bash
# テスト通知を送信
cd novu-integration/template/ssflow
python ssflow_tool.py send 1

# Frontend にアクセス
# http://localhost:3001
# 通知ベルアイコンをクリックして通知を確認
```

## ✅ サービス確認

### Novu サービスの状態確認

```bash
# すべてのサービスが "Up" 状態であることを確認
docker-compose -f novu-integration/docker.novu/docker-compose.novu.yml ps

# 期待される出力:
# - novu-api      (Up)
# - novu-ws       (Up)
# - novu-worker   (Up)
# - novu-web      (Up)
# - novu-mongo    (Up)
# - novu-redis    (Up)
```

### API 接続テスト

```bash
# Novu API のヘルスチェック
curl http://localhost:3000/v1/health-check
# 期待される出力: {"status":"ok"}

# WebSocket サービスのヘルスチェック
curl http://localhost:3002/health-check
# 期待される出力: {"status":"ok"}
```

### Frontend アクセス

ブラウザで以下にアクセス:

- **Frontend**: <http://localhost:3001>
- **Novu Dashboard**: <http://localhost:4200>

## 📝 次のステップ

### SSFlow 通知の送信

```bash
cd novu-integration/template/ssflow

# ユーザー ID 1 に通知を送信
python ssflow_tool.py send 1

# 複数の通知を送信
python ssflow_tool.py send 1
python ssflow_tool.py send 1
python ssflow_tool.py send 1
```

### WebSocket 接続の確認

ブラウザの開発者ツール（F12）を開き、コンソールで以下のログを確認:

```
✅ Novu WebSocket connected successfully!
📬 New notification received via WebSocket
```

## 🐛 トラブルシューティング

### 問題1: Docker サービスが起動しない

**解決策:**

```bash
# ポート使用状況を確認
netstat -ano | findstr "3000"
netstat -ano | findstr "27017"

# サービスを再起動
cd novu-integration/docker.novu
docker-compose -f docker-compose.novu.yml down
docker-compose -f docker-compose.novu.yml up -d
```

### 問題2: WebSocket 接続エラー

**症状**: コンソールに `io server disconnect` エラー

**解決策:**

1. Backend と Novu WS の `JWT_SECRET` が一致しているか確認
2. Backend ログで JWT token 生成を確認
3. Novu WS ログで接続エラーを確認

```bash
# Backend ログ確認
docker logs chatbot-backend --tail 50 | grep "JWT"

# Novu WS ログ確認
docker logs novu-ws --tail 50 | grep "Connection"
```

### 問題3: 通知が届かない

**症状**: WebSocket 接続は成功するが通知が表示されない

**解決策:**

1. SSFlow ワークフローが Novu Dashboard で作成されているか確認
2. Subscriber が正しく作成されているか確認
3. Backend ログで通知送信を確認

```bash
# Backend ログ確認
docker logs chatbot-backend --tail 50 | grep "notification"
```

## 📚 詳細ドキュメント

- **[WEBSOCKET_FINAL_CONFIG.md](./done/WEBSOCKET_FINAL_CONFIG.md)** - 完全な設定ガイド
- **[README.md](./README.md)** - プロジェクト概要

## 💬 サポート

問題が解決しない場合:

1. `done/WEBSOCKET_FINAL_CONFIG.md` のトラブルシューティングセクションを参照
2. Backend と Novu WS のログを確認
3. Novu 公式ドキュメント: <https://docs.novu.co>

---

**所要時間**: 5分  
**難易度**: ⭐⭐☆☆☆ (簡単)  
**最終更新**: 2026-01-22
