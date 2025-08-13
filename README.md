# チャットボットシステム

MySQLとQdrantを使用したシンプルなチャットボットシステムです。ユーザーが自然言語で対話できるインターフェースを提供し、LLM設定とナレッジ管理機能を備えています。

## 機能

- **チャットボット画面**: ユーザーが自然言語で対話できるインターフェース
- **LLM設定画面**: LLMの設定を管理（API URL、モデル名、パラメータ等）
- **ナレッジ設定画面**: ナレッジベースの管理（ドキュメントの追加、検索、削除）
- **リアルタイム設定変更**: 設定変更がリアルタイムに反映される機能

## アーキテクチャ

### フロントエンド
- **React + TypeScript**: モダンなUIフレームワーク
- **Material-UI**: UIコンポーネントライブラリ
- **Axios**: HTTPクライアント
- **React Router**: ルーティング

### バックエンド
- **FastAPI**: 高性能なPython Webフレームワーク
- **LangChain**: LLMアプリケーションフレームワーク
- **Qdrant**: ベクトルデータベース
- **MySQL**: リレーショナルデータベース
- **Ollama**: 埋め込みモデル

## セットアップ

### 前提条件
- DockerとDocker Composeがインストールされていること
- Ollamaがインストールされ、実行されていること（推奨）

### インストール手順

1. リポジトリをクローンします
```bash
git clone <repository-url>
cd langchainChatBot
```

2. Docker Composeを使用してデータベースサービスを起動します
```bash
docker-compose up -d
```

3. サービスが起動したことを確認します
```bash
docker-compose ps
```

### アクセス方法

- **Qdrant**: http://localhost:6333
- **MySQL**: localhost:3306

## 開発

### ローカル開発環境

#### バックエンドの開発

```bash
cd backend
pip install -e .
# config.tomlを設定
cp config.toml.example config.toml
# config.tomlを編集してAPIキー等を設定
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### フロントエンドの開発

```bash
cd frontend
npm install
npm start
```

### 環境変数

#### バックエンド設定

バックエンドの設定は `config.toml` ファイルで行います。初回起動前にサンプルファイルをコピーして設定してください：

```bash
cd backend
cp config.toml.example config.toml
```

#### 環境変数ファイルの設定

バックエンド用の環境変数ファイルを設定します：

```bash
cd backend
cp .env.example .env
```

フロントエンド用の環境変数はプロジェクトルートに `.env` ファイルを作成します：

```bash
echo "REACT_APP_API_URL=http://localhost:8000" > .env
```

主な環境変数：
- `REACT_APP_API_URL`: バックエンドAPIのURL（フロントエンド用、プロジェクトルートの.env）
- `SECRET_KEY`: JWTシークレットキー（バックエンド用、backend/.env）
- `CONFIG_PATH`: 設定ファイルのパス（バックエンド用、オプション）
- `LOG_LEVEL`: ログレベル（バックエンド用、オプション）

`config.toml` ファイルで設定します：

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
```

#### フロントエンド環境変数

```env
REACT_APP_API_URL=http://localhost:8000
```

## APIエンドポイント

### チャット関連
- `POST /api/chat/send` - メッセージを送信
- `POST /api/chat/stream` - ストリーミングでメッセージを送信
- `GET /api/chat/sessions/{session_id}/history` - チャット履歴を取得
- `DELETE /api/chat/sessions/{session_id}` - チャット履歴を削除

### LLM設定関連
- `GET /api/llm/config` - LLM設定を取得
- `POST /api/llm/config` - LLM設定を更新
- `POST /api/llm/config/test` - LLM設定をテスト
- `GET /api/llm/models` - 利用可能なモデルを取得
- `POST /api/llm/config/reset` - 設定をリセット

### ナレッジ管理関連
- `POST /api/knowledge/document` - ドキュメントを追加
- `POST /api/knowledge/documents/upload` - ファイルをアップロード
- `POST /api/knowledge/directory` - ディレクトリからドキュメントを追加
- `POST /api/knowledge/search` - ナレッジを検索
- `GET /api/knowledge/collection` - コレクション情報を取得
- `GET /api/knowledge/documents` - ドキュメント一覧を取得
- `DELETE /api/knowledge/documents/{doc_id}` - ドキュメントを削除
- `DELETE /api/knowledge/collection` - コレクションをクリア

## 設定ファイル

### config.tomlの設定

`config.toml` ファイルにはAPIキーやデータベース接続情報などの機密情報が含まれています。このファイルは `.gitignore` に追加されており、リポジトリにはコミットされません。

設定が必要な主な項目：
- `llm.api_key`: LLMサービスのAPIキー
- `llm.api_base`: LLMサービスのベースURL
- `database.password`: データベースのパスワード
- `security.secret_key`: JWTのシークレットキー

詳細な設定オプションについては `backend/config.toml.example` を参照してください。

### .envファイルの設定

環境変数ファイルには機密情報が含まれており、`.gitignore` に追加されておりリポジトリにはコミットされません。

#### プロジェクトルートの .env ファイル
フロントエンド用の環境変数を設定：
- `REACT_APP_API_URL`: フロントエンドからバックエンドAPIに接続するURL

#### backend/.env ファイル
バックエンド用の環境変数を設定：
- `SECRET_KEY`: JWTシークレットキー
- その他の環境変数（オプション）

詳細な設定オプションについては `backend/.env.example` を参照してください。

## トラブルシューティング

### 一般的な問題

1. **サービスが起動しない**
   - DockerとDocker Composeが正しくインストールされているか確認してください
   - ポートが他のサービスによって使用されていないか確認してください

2. **フロントエンドからバックエンドに接続できない**
   - CORS設定が正しいか確認してください
   - ファイアウォール設定を確認してください

3. **チャットボットが応答しない**
   - LLM設定が正しいか確認してください
   - Ollamaが実行されているか確認してください

4. **ナレッジベースが機能しない**
   - Qdrantが実行されているか確認してください
   - ナレッジドキュメントが正しく追加されているか確認してください

### ログの確認

```bash
# MySQLのログ
docker-compose logs -f mysql

# Qdrantのログ
docker-compose logs -f qdrant
```

## ライセンス

MIT License