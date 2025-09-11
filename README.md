# チャットボットシステム

このプロジェクトは、ReactフロントエンドとFastAPIバックエンドを備えた包括的なチャットボットシステムです。LLM統合、ナレッジベース管理、リアルタイムチャット機能を提供します。LangChainによるAI/MLオーケストレーション、Qdrantによるベクトルストレージ、MySQLによるリレーショナルデータベースをサポートし、多様なデプロイ環境に対応しています。

## 機能

- **チャット機能**: リアルタイムストリーミング応答、セッション管理、参照ドキュメント表示、Markdownサポート、自動スクロールインターフェース。
- **LLM設定**: 動的TOML設定、ホットリロード、環境変数オーバーライド、設定検証、インポート/エクスポート。
- **ナレッジベース**: 複数フォーマットのドキュメントアップロード、ディレクトリバッチ処理、Qdrantによるベクトル検索、ドキュメント管理（CRUD）、Ollamaによるエンベディング生成。
- **リアルタイム設定変更**: 設定変更が即座に反映。
- **デジタルヒューマン統合**: 追加のルートによるサポート。

## アーキテクチャ

### システムアーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │◄──►│   Backend       │◄──►│   Qdrant DB     │
│   (React)       │    │   (FastAPI)     │    │   (Vector DB)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          │                       ▼                       ▼
          │              ┌─────────────────┐    ┌─────────────────┐
          │              │    Ollama       │    │   Config TOML   │
          │              │ (Embedding)     │    │   (Hot-reload) │
          │              └─────────────────┘    └─────────────────┘
          ▼
┌─────────────────┐
│     User        │
└─────────────────┘
          │
          ▼
┌─────────────────┐
│     MySQL       │
└─────────────────┘
```

### フロントエンドアーキテクチャ (React + TypeScript)

- **フレームワーク**: React 18 with TypeScript
- **UIライブラリ**: Material-UI (MUI) v5
- **状態管理**: React hooks (useState, useRef, useEffect)
- **ルーティング**: React Router v6
- **HTTPクライアント**: Axios with interceptors
- **テスト**: Vitest + React Testing Library
- **ビルドツール**: Vite
- **パッケージマネージャー**: pnpm

構造:
```
frontend/src/
├── components/           # 再利用可能なUIコンポーネント
│   ├── common/          # 共有コンポーネント (DataTable, ErrorAlert など)
│   ├── ChatInput.tsx    # チャット入力コンポーネント
│   ├── Layout.tsx       # メイン layout
│   └── VirtualizedMessageList.tsx  # パフォーマンス最適化メッセージリスト
├── pages/               # ページコンポーネント
│   ├── ChatPage.tsx     # チャットインターフェース
│   ├── LlmConfigPage.tsx # LLM設定
│   └── KnowledgePage.tsx # ナレッジベース管理
├── hooks/              # カスタムReact hooks
│   ├── useApi.ts       # API通信
│   ├── useChatState.ts # チャット状態管理
│   └── useConfig.ts    # 設定管理
├── services/           # APIサービス
│   └── api.ts          # 中央APIクライアント
└── utils/              # ユーティリティ関数
```

### バックエンドアーキテクチャ (Python + FastAPI)

- **フレームワーク**: FastAPI with async support
- **AI/ML**: LangChain with OpenAI-compatible LLMs and Ollama embeddings
- **ベクトルデータベース**: Qdrant
- **リレーショナルDB**: MySQL
- **設定**: TOMLベース with hot-reload
- **認証**: JWTトークンサポート
- **リアルタイム**: WebSocketサポート for live chat
- **テスト**: pytest with async support and coverage

構造:
```
backend/api/
├── core/               # コアモジュール
│   ├── config_manager.py    # TOML設定 with hot-reload
│   ├── qdrant_manager.py   # ベクトルDB操作
│   ├── config_watcher.py   # ファイル監視 for 設定変更
│   ├── database.py         # MySQLデータベース
│   └── utils.py            # 共通ユーティリティ
├── routes/             # APIエンドポイント
│   ├── chat.py            # チャット機能
│   ├── llm_config.py      # LLM設定
│   ├── knowledge.py       # ナレッジベース管理
│   ├── config.py          # 設定管理
│   └── digitalhuman.py    # デジタルヒューマン
├── services/           # ビジネスロジック
│   ├── chat_service.py    # チャット処理
│   ├── base_service.py    # サービスベースクラス
│   └── chat_history_service.py  # チャット履歴管理
└── models/             # データモデル
    └── database.py       # DBモデル
```

## セットアップ

### 前提条件
- DockerとDocker Composeがインストールされていること
- Ollamaがインストールされ、実行されていること（推奨）
- Node.js (pnpm用)、Python 3.10+ (uv推奨)

### インストール手順

1. リポジトリをクローンします
```bash
git clone <repository-url>
cd langchain
```

2. 依存関係をインストール（Makefile使用推奨）
```bash
make install-deps
```

3. Docker Composeを使用してデータベースサービスを起動します
```bash
docker-compose up -d
```

4. サービスが起動したことを確認します
```bash
docker-compose ps
```

### アクセス方法
- **フロントエンド**: http://localhost:3000
- **バックエンド**: http://localhost:8000
- **Qdrant**: http://localhost:6333
- **MySQL**: localhost:3306

## 開発

### 開発コマンド（Makefile使用）

```bash
# 依存関係インストール
make install-deps

# コード品質チェック
make check

# テスト実行
make test

# フォーマット
make format

# カバレッジレポート
make coverage-backend
make coverage-frontend

# クリーン
make clean

# 開発サーバー
make dev-backend    # バックエンド (port 8000)
make dev-frontend   # フロントエンド (port 3000)
make dev-up         # Docker開発環境
```

### ローカル開発環境

#### バックエンドの開発
```bash
cd backend
uv sync                    # uv使用推奨
# config.tomlを設定
cp config.toml.example config.toml
# config.tomlを編集
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### フロントエンドの開発
```bash
cd frontend

pnpm install
pnpm dev              # http://localhost:3000
```
or
```bash
npm install
npm run dev
```

### Docker開発
```bash
# 開発環境
docker-compose -f docker-compose.dev.yml up -d

# 本番環境
docker-compose -f docker-compose.prod.yml up -d

# ステージング環境
docker-compose -f docker-compose.staging.yml up -d

# ログ確認
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f qdrant
```

### コード品質チェック
- Pre-commit hooks
- CI/CD with quality gates
- Coverage requirements
- Security scanning (bandit)

## 環境変数と設定ファイル

### config.tomlの設定
バックエンドの設定は `backend/config.toml` で行います。サンプルからコピー：
```bash
cd backend
cp config.toml.example config.toml
```

例:
```toml
[app]
debug = true

[backend]
host = "0.0.0.0"
port = 8000
reload = true

[qdrant]
host = "localhost"
port = 6333

[mysql]
host = "localhost"
port = 3306
database = "chatbot"
user = "chatbot"
password = "chatbotpassword"

[ollama]
base_url = "http://localhost:11434"
embedding_model = "nomic-embed-text:latest"

[llm]
base_url = "http://localhost:11434/v1"
api_key = "nokey"
model_name = "llama3"

[embedding]
# embedding settings

[upload]
# upload params

[security]
secret_key = "your-secret-key"
```

### .envファイルの設定
#### プロジェクトルート .env (フロントエンド)
```env
REACT_APP_API_URL=http://localhost:8000
```

#### backend/.env (バックエンド)
```bash
cd backend
cp .env.example .env
```
- `SECRET_KEY`: JWTシークレットキー
- `CONFIG_PATH`: 設定ファイルパス (オプション)
- `LOG_LEVEL`: ログレベル (オプション)

## APIエンドポイント

### チャット関連
- `POST /api/chat/send` - メッセージ送信
- `POST /api/chat/stream` - ストリーミング応答
- `GET /api/chat/sessions/{session_id}/history` - 履歴取得
- `DELETE /api/chat/sessions/{session_id}` - セッション削除

### LLM設定関連
- `GET /api/llm/config` - 設定取得
- `POST /api/llm/config` - 設定更新
- `POST /api/llm/config/test` - テスト
- `GET /api/llm/models` - モデル一覧
- `POST /api/llm/config/reset` - リセット

### ナレッジ管理関連
- `POST /api/knowledge/document` - ドキュメント追加
- `POST /api/knowledge/documents/upload` - ファイルアップロード
- `POST /api/knowledge/directory` - ディレクトリ追加
- `POST /api/knowledge/search` - 検索
- `GET /api/knowledge/collection` - コレクション情報
- `GET /api/knowledge/documents` - ドキュメント一覧
- `DELETE /api/knowledge/documents/{doc_id}` - 削除
- `DELETE /api/knowledge/collection` - コレクションクリア

### システム関連
- `GET /health` - ヘルスチェック
- `GET /api/config` - 現在設定取得
- `POST /api/config/update` - 設定更新

### デジタルヒューマン関連
- (詳細はroutes/digitalhuman.py参照)

## テスト戦略

### フロントエンドテスト
- **フレームワーク**: Vitest + React Testing Library
- **カバレッジ**: @vitest/coverage-v8 (50%+)
- **タイプ**: Unit, integration, component tests
- 実行: `pnpm test`, `pnpm test:coverage`

### バックエンドテスト
- **フレームワーク**: pytest with async
- **カバレッジ**: pytest-cov
- **マーカー**: unit, integration, api, slow
- 実行: `pytest --cov=api`, `pytest -m unit`

## Dockerデプロイ

### 多環境サポート
- **開発**: docker-compose.dev.yml
- **ステージング**: docker-compose.staging.yml
- **本番**: docker-compose.prod.yml
- **デフォルト**: docker-compose.yml

### サービス
- **qdrant**: ベクトルDB (ports 6333/6334)
- **mysql**: リレーショナルDB (port 3306)
- **backend**: FastAPI (port 8000)
- **frontend**: React (port 3000)

### ボリューム管理
- `qdrant_data`: ベクトルストレージ
- `mysql_data`: MySQLデータ
- `./uploads`: ファイルアップロード

## 開発ワークフロー

### ローカル開発
1. `make install-deps`
2. `make dev-backend`
3. `make dev-frontend`
4. http://localhost:3000 にアクセス

### Docker開発
1. `make dev-up`
2. `docker-compose logs -f [service]`
3. `make dev-down` で停止

## セキュリティ考慮事項

- JWTベース認証
- CORS設定
- 入力検証とサニタイズ
- ファイルアップロードセキュリティ
- 環境変数管理
- Banditによるセキュリティスキャン

## パフォーマンス最適化

### フロントエンド
- 仮想化メッセージリスト
- コードスプリッティング
- メモ化
- 画像最適化
- キャッシング

### バックエンド
- Async/await for I/O
- 接続プーリング
- 効率的なクエリ
- ストリーミング応答
- バックグラウンドタスク

## トラブルシューティング

### 一般的な問題
1. **サービス起動失敗**: Dockerインストール確認、ポート競合確認
2. **フロント-バック接続失敗**: CORS/ファイアウォール確認
3. **チャット応答なし**: LLM/Ollama設定確認
4. **ナレッジ機能なし**: Qdrant実行確認、ドキュメント追加確認

### ログ確認
```bash
docker-compose logs -f mysql
docker-compose logs -f qdrant
docker-compose logs -f backend
```

## ライセンス

MIT License
