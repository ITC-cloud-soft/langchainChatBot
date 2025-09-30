# チャットボットシステム

**ReactフロントエンドとFastAPIバックエンド**を備えた、エンタープライズ向けチャットボットシステムです。

> **Note**: 単一組織向けの設計です。マルチテナント機能は含まれていません。

## ✨ 特徴

- 🏢 **シンプルな設計** - 保守しやすく、カスタマイズが容易
- 💬 **リアルタイムチャット** - ストリーミング応答、セッション管理、Markdown対応
- 🤖 **柔軟なLLM統合** - OpenAI互換API、カスタムLLM対応
- 📚 **ナレッジベース** - ドキュメントアップロード、ベクトル検索（Qdrant）
- 👥 **ユーザー管理** - ロールベースアクセス制御（admin/user）
- 🔐 **JWT認証** - トークンベース認証、自動リフレッシュ
- ⚙️ **ホットリロード設定** - config.tomlの変更を即座に反映

## 🚀 クイックスタート

### 前提条件

- **Docker & Docker Compose** - Qdrant、MySQLの実行
- **Node.js 16+** - フロントエンド
- **Python 3.10+** - バックエンド（uv推奨）
- **Ollama**（オプション） - ローカルLLM/Embedding

### 1. データベース起動

```bash
docker-compose up -d
```

### 2. バックエンド起動

```bash
cd backend

# 依存関係インストール
uv sync

# 設定ファイル作成
cp config.toml.example config.toml
# config.tomlを編集（LLM API Key等）

# サーバー起動
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**初回起動時に自動的に:**
- データベーステーブルが作成されます
- 管理者ユーザー（admin / admin123）が作成されます

### 3. フロントエンド起動

```bash
cd frontend

# 依存関係インストール
pnpm install
# または npm install

# 開発サーバー起動
pnpm dev
# または npm run dev
```

### 4. アクセス

- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **API ドキュメント**: http://localhost:8000/docs
- **Qdrant UI**: http://localhost:6333/dashboard

### 5. ログイン

- **ユーザー名**: `admin`
- **パスワード**: `admin123`

⚠️ **初回ログイン後、必ずパスワードを変更してください！**

## 📁 プロジェクト構成

```
langchainChatBot/
├── backend/              # FastAPIバックエンド
│   ├── api/
│   │   ├── core/        # コアモジュール
│   │   ├── routes/      # APIエンドポイント
│   │   ├── services/    # ビジネスロジック
│   │   ├── models/      # データモデル
│   │   └── middleware/  # 認証ミドルウェア
│   ├── config.toml      # アプリケーション設定
│   ├── main.py          # エントリーポイント
│   └── scripts/         # セットアップスクリプト
│
├── frontend/             # Reactフロントエンド
│   ├── src/
│   │   ├── components/  # UIコンポーネント
│   │   ├── pages/       # ページコンポーネント
│   │   ├── services/    # APIクライアント
│   │   ├── contexts/    # React Context
│   │   └── hooks/       # カスタムフック
│   └── package.json
│
└── docker-compose.yml    # Qdrant、MySQL設定
```

## 🔧 設定

### config.toml（バックエンド）

```toml
[llm]
provider = "カスタム"
api_base = "https://api.deepseek.com/v1"
api_key = "your-api-key"
model_name = "deepseek-chat"
temperature = 0.7

[embedding]
provider = "ollama"
base_url = "http://localhost:11434"
model_name = "nomic-embed-text:latest"

[qdrant]
host = "127.0.0.1"
port = 6333
collection_name = "chatbot_knowledge"

[database]
host = "localhost"
port = 3306
username = "root"
password = "root"
database = "chatbot"
```

### 環境変数（バックエンド）

`backend/.env`を作成：

```bash
# JWT設定
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 管理者パスワード（初回セットアップ時）
SUPER_ADMIN_PASSWORD=admin123

# データベース
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=chatbot
```

### 環境変数（フロントエンド）

`frontend/.env`を作成：

```bash
VITE_API_URL=http://localhost:8000
```

## 📖 主要機能

### チャット機能

- ✅ リアルタイムストリーミング応答
- ✅ セッション管理（履歴保存）
- ✅ 参照ドキュメント表示（RAG）
- ✅ Markdownレンダリング
- ✅ コードハイライト

### ナレッジベース

- ✅ 複数形式サポート（PDF、TXT、DOCX、MD）
- ✅ ディレクトリ一括アップロード
- ✅ ベクトル検索（Qdrant）
- ✅ ドキュメント管理（CRUD）

### ユーザー管理

- ✅ 管理者による新規ユーザー作成
- ✅ ロールベースアクセス制御
  - **admin**: 全機能アクセス（設定変更、ユーザー管理、ナレッジ管理）
  - **user**: チャット機能のみ
- ✅ ユーザー検索・フィルタリング
- ✅ アカウントの有効化/無効化

### LLM設定

- ✅ 動的プロバイダー切り替え（OpenAI、Anthropic、カスタム）
- ✅ モデルパラメータ調整
- ✅ 設定のテスト機能
- ✅ エクスポート/インポート

## 🔐 セキュリティ

### 実装済み

- ✅ JWT トークンベース認証
- ✅ パスワードハッシュ化（bcrypt）
- ✅ ロールベースアクセス制御（RBAC）
- ✅ CORS設定
- ✅ SQL インジェクション対策（ORM使用）
- ✅ XSS対策（入力サニタイズ）

### 本番環境の推奨事項

⚠️ **本番環境では必ず以下を実施してください:**

1. **HTTPS必須** - SSL/TLS証明書の設定
2. **強力なJWT Secret Key** - 環境変数で設定
3. **パスワードポリシー** - 最小文字数、複雑性要件
4. **レート制限** - ログイン試行回数制限
5. **セッション管理** - タイムアウト、同時セッション制限
6. **監査ログ** - ユーザー操作履歴の記録

## 🗄️ データベース

### テーブル構成

- **users** - ユーザー情報（認証・権限）
- **chat_sessions** - チャットセッション
- **chat_messages** - チャットメッセージ履歴
- **chat_metadata** - セッションメタデータ
- **chat_history_stats** - 統計情報

### データベースリセット

```bash
mysql -u root -p
DROP DATABASE IF EXISTS chatbot;
CREATE DATABASE chatbot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;

cd backend
python scripts/quick_setup.py
```

## 📡 APIエンドポイント

### 認証

- `POST /api/auth/login` - ログイン
- `POST /api/auth/logout` - ログアウト
- `POST /api/auth/refresh` - トークンリフレッシュ
- `GET /api/auth/me` - 現在のユーザー情報
- `POST /api/auth/change-password` - パスワード変更

### ユーザー管理（管理者のみ）

- `POST /api/users/` - ユーザー作成
- `GET /api/users/` - ユーザー一覧
- `GET /api/users/{id}` - ユーザー詳細
- `PUT /api/users/{id}` - ユーザー更新
- `DELETE /api/users/{id}` - ユーザー削除

### チャット

- `POST /api/chat/send` - メッセージ送信
- `POST /api/chat/stream` - ストリーミング応答
- `GET /api/chat/sessions` - セッション一覧
- `GET /api/chat/sessions/{session_id}/history` - 履歴取得
- `DELETE /api/chat/sessions/{session_id}` - セッション削除

### ナレッジベース（管理者のみ）

- `POST /api/knowledge/documents/upload` - ドキュメントアップロード
- `GET /api/knowledge/documents` - ドキュメント一覧
- `DELETE /api/knowledge/documents/{doc_id}` - ドキュメント削除
- `POST /api/knowledge/search` - 検索

### LLM設定（管理者のみ）

- `GET /api/llm/config` - 設定取得
- `POST /api/llm/config` - 設定更新
- `POST /api/llm/config/test` - テスト
- `GET /api/llm/models` - モデル一覧

## 🧪 開発

### バックエンド開発

```bash
cd backend

# 依存関係インストール
uv sync

# 開発サーバー起動
uv run uvicorn main:app --reload

# テスト実行
pytest

# コードフォーマット
black .
ruff check .
```

詳細は[backend/README.md](backend/README.md)を参照

### フロントエンド開発

```bash
cd frontend

# 依存関係インストール
pnpm install

# 開発サーバー起動
pnpm dev

# ビルド
pnpm build

# テスト実行
pnpm test
```

詳細は[frontend/README.md](frontend/README.md)を参照

## 🐛 トラブルシューティング

### サーバー起動エラー

**症状**: `uvicorn main:app --reload`でエラーが出る

**解決方法**:
1. データベースが起動しているか確認: `docker-compose ps`
2. `config.toml`が存在するか確認
3. Python依存関係を再インストール: `uv sync`

### ログインできない

**症状**: 403 Forbiddenエラーが出る

**解決方法**:
1. バックエンドログで`Admin user created successfully`を確認
2. ブラウザのLocalStorageをクリア
3. データベースをリセット

### チャット応答がない

**症状**: メッセージを送信しても応答がない

**解決方法**:
1. `config.toml`のLLM設定を確認（API Key、エンドポイント）
2. バックエンドログでエラーメッセージを確認
3. LLM設定画面でテストボタンを押して接続確認

### ナレッジベースが動作しない

**症状**: ドキュメントをアップロードできない

**解決方法**:
1. Qdrantが起動しているか確認: http://localhost:6333/dashboard
2. Ollamaが起動しているか確認（Embedding使用時）: `ollama list`
3. `config.toml`のqdrant設定を確認

## 📚 技術スタック

### バックエンド

- **FastAPI** - 高速なPython Webフレームワーク
- **LangChain** - LLMオーケストレーション
- **SQLAlchemy** - ORM（MySQL対応）
- **Qdrant** - ベクトルデータベース
- **JWT** - 認証トークン
- **uvicorn** - ASGIサーバー

### フロントエンド

- **React 18** - UIフレームワーク
- **TypeScript** - 型安全な開発
- **Material-UI** - UIコンポーネントライブラリ
- **React Router** - ルーティング
- **Axios** - HTTPクライアント
- **Vite** - ビルドツール

## 🔄 将来の拡張

### マルチテナント化への道筋

現在の設計は、必要に応じてマルチテナント化できるよう、モジュール構造を維持しています。

**必要な変更:**
1. `tenants`テーブルを追加
2. `users`、`chat_sessions`等に`tenant_id`を追加
3. 認証ミドルウェアにテナントコンテキストを追加
4. すべてのクエリにテナントフィルタを追加

## 📄 ライセンス

MIT License

## 🤝 貢献

Issue、Pull Requestを歓迎します！

---

**ドキュメント**: [backend/README.md](backend/README.md) | [frontend/README.md](frontend/README.md)

**最終更新**: 2025-09-30
