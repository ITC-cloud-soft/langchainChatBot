# バックエンド - FastAPI + LangChain

チャットボットのバックエンドAPIサーバーです。LangChainによるLLM統合、Qdrantによるベクトル検索、MySQLによるデータ管理を提供します。

## 🚀 クイックスタート

### インストール

```bash
# 依存関係インストール（uv推奨）
uv sync

# または pip
pip install -r requirements.txt
```

### 設定

```bash
# 設定ファイルコピー
cp config.toml.example config.toml

# 環境変数設定
cp .env.example .env
```

`config.toml`を編集：

```toml
[llm]
provider = "カスタム"
api_base = "https://api.deepseek.com/v1"
api_key = "your-api-key"
model_name = "deepseek-chat"
```

`.env`を編集：

```bash
JWT_SECRET_KEY=your-super-secret-key-change-in-production
DB_PASSWORD=root
```

### サーバー起動

```bash
# 開発モード（自動リロード）
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 本番モード
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

**初回起動時に自動実行:**
- データベーステーブル作成
- 管理者ユーザー作成（admin / admin123）

## 📁 ディレクトリ構成

```
backend/
├── api/
│   ├── core/              # コアモジュール
│   │   ├── auth.py       # JWT認証
│   │   ├── config_manager.py  # TOML設定管理
│   │   ├── database.py   # データベース接続
│   │   └── qdrant_manager.py  # ベクトルDB管理
│   ├── routes/            # APIエンドポイント
│   │   ├── auth.py       # 認証API
│   │   ├── users.py      # ユーザー管理API
│   │   ├── chat.py       # チャットAPI
│   │   ├── llm_config.py # LLM設定API
│   │   └── knowledge.py  # ナレッジAPI
│   ├── services/          # ビジネスロジック
│   │   ├── chat_service.py
│   │   └── chat_history_service.py
│   ├── models/            # データモデル
│   │   ├── user.py       # ユーザーモデル
│   │   └── database.py   # チャット履歴モデル
│   └── middleware/        # ミドルウェア
│       └── auth_middleware.py
├── scripts/               # ユーティリティ
│   └── quick_setup.py    # セットアップスクリプト
├── config.toml           # 設定ファイル
├── main.py              # エントリーポイント
└── requirements.txt     # 依存関係
```

## 🔧 主要機能

### 認証・認可

- JWT トークンベース認証
- Access Token（30分） + Refresh Token（7日）
- ロールベースアクセス制御（admin/user）
- パスワードハッシュ化（bcrypt）

### チャット機能

- リアルタイムストリーミング応答
- セッション管理
- 履歴保存（MySQL）
- RAG（検索拡張生成）

### ナレッジベース

- ドキュメントアップロード（PDF、TXT、DOCX、MD）
- ベクトル検索（Qdrant）
- Embedding生成（Ollama）

### 設定管理

- TOML形式の設定ファイル
- ホットリロード対応
- 環境変数オーバーライド

## 📡 APIエンドポイント

### 認証（/api/auth）

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| POST | `/login` | ログイン |
| POST | `/logout` | ログアウト |
| POST | `/refresh` | トークンリフレッシュ |
| GET | `/me` | ユーザー情報取得 |
| POST | `/change-password` | パスワード変更 |

### ユーザー管理（/api/users）- 管理者のみ

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| POST | `/` | ユーザー作成 |
| GET | `/` | ユーザー一覧 |
| GET | `/{id}` | ユーザー詳細 |
| PUT | `/{id}` | ユーザー更新 |
| DELETE | `/{id}` | ユーザー削除 |

### チャット（/api/chat）

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| POST | `/send` | メッセージ送信 |
| POST | `/stream` | ストリーミング応答 |
| GET | `/sessions` | セッション一覧 |
| GET | `/sessions/{id}/history` | 履歴取得 |
| DELETE | `/sessions/{id}` | セッション削除 |

### LLM設定（/api/llm）- 管理者のみ

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET | `/config` | 設定取得 |
| POST | `/config` | 設定更新 |
| POST | `/config/test` | 接続テスト |
| GET | `/models` | モデル一覧 |

### ナレッジベース（/api/knowledge）- 管理者のみ

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| POST | `/documents/upload` | アップロード |
| GET | `/documents` | ドキュメント一覧 |
| DELETE | `/documents/{id}` | 削除 |
| POST | `/search` | 検索 |

## 🧪 開発

### テスト

```bash
# 全テスト実行
pytest

# カバレッジ付き
pytest --cov=api

# 特定のマーカーのみ
pytest -m unit
```

### コード品質

```bash
# フォーマット
black .
ruff check .

# 型チェック
mypy api/
```

## 🗄️ データベース

### 必要なサービス

```bash
# Docker Composeで起動
docker-compose up -d

# MySQL（ポート3306）
# Qdrant（ポート6333）
```

### テーブル構成

- **users** - ユーザー情報
- **chat_sessions** - セッション
- **chat_messages** - メッセージ履歴
- **chat_metadata** - メタデータ
- **chat_history_stats** - 統計

### マイグレーション

```bash
# 手動セットアップ（開発時）
python scripts/quick_setup.py

# 本番環境（Alembic使用推奨）
alembic upgrade head
```

## 🔐 セキュリティ

### 設定のベストプラクティス

1. **JWT Secret Key**
   ```bash
   # 強力なキーを生成
   openssl rand -hex 32
   ```

2. **環境変数で上書き**
   ```bash
   export JWT_SECRET_KEY="your-secret-key"
   export DB_PASSWORD="secure-password"
   ```

3. **本番環境**
   - HTTPS必須
   - CORS設定を厳密に
   - レート制限の実装
   - ログ監視

## 📚 依存関係

### 主要パッケージ

- **fastapi** - Webフレームワーク
- **uvicorn** - ASGIサーバー
- **sqlalchemy** - ORM
- **langchain** - LLMオーケストレーション
- **qdrant-client** - ベクトルDB
- **python-jose** - JWT
- **passlib** - パスワードハッシュ

### インストール方法

```bash
# uv（推奨）
uv sync

# pip
pip install -r requirements.txt
```

## 🐛 トラブルシューティング

### データベース接続エラー

```bash
# MySQLが起動しているか確認
docker-compose ps

# 接続情報確認
mysql -h localhost -u root -p
```

### LLM接続エラー

```bash
# config.tomlのapi_keyを確認
# ログでエラー詳細を確認
tail -f logs/app.log
```

### Qdrant接続エラー

```bash
# Qdrantダッシュボードで確認
open http://localhost:6333/dashboard
```

## 📄 API ドキュメント

サーバー起動後、以下にアクセス：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

**メインドキュメント**: [../README.md](../README.md)
