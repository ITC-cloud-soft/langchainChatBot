# Novu Integration - リアルタイム通知システム

**状態**: ✅ 完全動作確認済み (2026-01-22)  
**バージョン**: Novu v0.24.0 (self-hosted)

## 概要

Novu self-hosted を使用したリアルタイム WebSocket 通知システムです。

## 主な機能

- ✅ WebSocket リアルタイム通知（JWT 認証）
- ✅ 未読数の自動更新
- ✅ 既読・削除機能
- ✅ SSFlow ワークフロー通知サポート

## ディレクトリ構成

```
novu-integration/
├── README.md                          # このファイル
├── WEBSOCKET_FINAL_CONFIG.md          # 最終設定ガイド（必読）
├── QUICK_START.md                     # クイックスタート
├── docker.novu/                       # Novu サービス Docker 設定
│   ├── docker-compose.novu.yml
│   ├── .env.novu
│   └── mongo/
└── template/
    └── ssflow/                        # SSFlow 通知送信ツール
```

## クイックスタート

### 1. Novu サービス起動

```bash
cd docker.novu
docker-compose -f docker-compose.novu.yml up -d
```

### 2. Backend・Frontend 起動

```bash
cd ../../
docker-compose -f docker-compose.full.dev.yml up -d
```

### 3. テスト通知送信

```bash
cd novu-integration/template/ssflow
python ssflow_tool.py send 1
```

## 詳細ドキュメント

- **[WEBSOCKET_FINAL_CONFIG.md](./WEBSOCKET_FINAL_CONFIG.md)** - 完全な設定ガイド（必読）
- **[QUICK_START.md](./QUICK_START.md)** - クイックスタートガイド

## トラブルシューティング

問題が発生した場合は、`WEBSOCKET_FINAL_CONFIG.md` の「トラブルシューティング」セクションを参照してください。

## 環境変数

### Backend
- `NOVU_API_KEY`: Novu API キー
- `NOVU_API_URL`: Novu API URL (デフォルト: http://novu-api:3000)
- `NOVU_JWT_SECRET`: JWT シークレット

### Novu WS
- `JWT_SECRET`: JWT シークレット（Backend と同じ値）

## 開発者向け情報

### SSFlow 通知ツール

`template/ssflow/` ディレクトリには、SSFlow ワークフロー承認通知を送信するツールが含まれています。

```bash
cd template/ssflow
python ssflow_tool.py send <user_id>
```

詳細は `template/ssflow/README.md` を参照してください。

---

**最終更新**: 2026-01-22  
**動作確認**: ✅ 全機能正常動作
