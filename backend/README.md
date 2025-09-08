# チャットボットバックエンド

FastAPIとLangChainを使用したチャットボットバックエンドです。MySQLとQdrantをサポートし、LLM統合、ナレッジベース管理、リアルタイムチャット機能を提供します。

## 機能

- FastAPIバックエンド（非同期サポート）
- LangChainによるAI/MLオーケストレーション（OpenAI互換LLMとOllamaエンベディング）
- Qdrantベクトルデータベース
- MySQLリレーショナルデータベース
- TOMLベースの設定管理（ホットリロード対応）
- JWT認証
- WebSocketによるリアルタイムチャット
- RESTful APIエンドポイント
- テストとコード品質ツール（pytest, black, mypyなど）

## インストール

### uv使用（推奨）

```bash
# 依存関係インストール
uv sync

# バージョン指定が必要な場合
SETUPTOOLS_SCM_PRETEND_VERSION_FOR_CHATBOT_BACKEND=1.0.0 uv sync
```

### pip使用

```bash
pip install -e ".[dev]"
```

## 開発

### サーバー起動

```bash
# 開発モード（自動リロード）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 本番モード
uvicorn main:app --host 0.0.0.0 --port 8000
```

### コード品質とテスト

```bash
# テスト実行
pytest --cov=api --cov-report=term-missing
pytest -m unit  # ユニットテスト
pytest -m integration  # インテグレーションテスト

# フォーマット
black .
isort .

# リンター
flake8 .
mypy api/

# セキュリティスキャン
bandit -r .
```

## 設定

アプリケーションはTOML設定ファイルを使用します。`config.toml.example` を `config.toml` にコピーして編集：

```bash
cp config.toml.example config.toml
```

環境変数テンプレートもコピー：

```bash
cp .env.example .env
```

### 設定セクション

- `[app]`: アプリケーション設定（debugなど）
- `[backend]`: サーバー設定（host, port, reload）
- `[qdrant]`: ベクトルDB設定（host, port）
- `[mysql]`: MySQL設定（host, port, database, user, password）
- `[ollama]`: Ollamaエンベディングモデル設定（base_url, embedding_model）
- `[llm]`: LLM設定（base_url, api_key, model_name）
- `[embedding]`: エンベディング設定
- `[upload]`: ファイルアップロード設定
- `[security]`: セキュリティ設定（secret_key）

### 重要な設定ファイル

- `config.toml`: メイン設定ファイル（機密情報含む、git未コミット）
- `.env`: 環境変数（機密情報含む、git未コミット）
- `config.toml.example`: 設定テンプレート
- `.env.example`: 環境変数テンプレート

### 必須設定

アプリケーション起動前に設定：

1. **LLM設定** (`config.toml`):
   - `llm.api_key`: LLMサービスAPIキー
   - `llm.base_url`: LLMサービスベースURL
   - `llm.model_name`: 使用モデル名

2. **データベース設定** (`config.toml`):
   - `mysql.password`: MySQLパスワード
   - `security.secret_key`: JWTシークレットキー

3. **環境変数** (`.env`):
   - `SECRET_KEY`: JWTシークレットキー（config.tomlでも設定可能）
   - `CONFIG_PATH`: 設定ファイルパス（オプション、デフォルト: config.toml）
   - `LOG_LEVEL`: ログレベル（オプション、デフォルト: INFO）

### 設定例

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

## アーキテクチャ

### バックエンド構造

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

## APIドキュメント

サーバー起動後、アクセス：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPIスキーマ: http://localhost:8000/openapi.json

### 主要エンドポイント

- `GET /health` - ヘルスチェック
- `POST /api/chat/send` - チャットメッセージ送信
- `POST /api/chat/stream` - ストリーミング応答
- `GET /api/chat/sessions/{session_id}/history` - チャット履歴取得
- `DELETE /api/chat/sessions/{session_id}` - セッション削除
- `GET /api/llm/config` - LLM設定取得
- `POST /api/llm/config` - LLM設定更新
- `POST /api/llm/config/test` - LLM設定テスト
- `GET /api/llm/models` - 利用可能モデル取得
- `POST /api/llm/config/reset` - 設定リセット
- `POST /api/knowledge/document` - ドキュメント追加
- `POST /api/knowledge/documents/upload` - ファイルアップロード
- `POST /api/knowledge/directory` - ディレクトリ追加
- `POST /api/knowledge/search` - ナレッジ検索
- `GET /api/knowledge/collection` - コレクション情報
- `GET /api/knowledge/documents` - ドキュメント一覧
- `DELETE /api/knowledge/documents/{doc_id}` - ドキュメント削除
- `DELETE /api/knowledge/collection` - コレクションクリア
- `GET /api/config` - 現在設定取得
- `POST /api/config/update` - 設定更新

## テスト戦略

- **フレームワーク**: pytest with async support
- **カバレッジ**: pytest-cov with HTML reports
- **マーカー**: unit, integration, api, slow
- **要件**: 設定可能なカバレッジ閾値
- **非同期モード**: auto for async/await support

実行:
```bash
make test  # Makefile使用推奨
# または
pytest --cov=api --cov-report=term-missing
```

## Dockerデプロイ

- **開発**: docker-compose.dev.yml
- **本番**: docker-compose.prod.yml
- **ステージング**: docker-compose.staging.yml

サービス:
- **backend**: FastAPI (port 8000)

ボリューム:
- `./uploads`: ファイルアップロードディレクトリ

ログ確認:
```bash
docker-compose logs -f backend
```

## セキュリティ考慮事項

- JWTベース認証
- CORS設定
- 入力検証とサニタイズ
- ファイルアップロードセキュリティ
- 環境変数管理
- Banditによるセキュリティスキャン

## パフォーマンス最適化

- Async/await for I/O operations
- 接続プーリング
- 効率的なデータベースクエリ
- ストリーミング応答
- バックグラウンドタスク処理

## ライセンス

MIT License