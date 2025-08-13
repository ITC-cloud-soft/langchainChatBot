# 設定管理システム

## 概要

このチャットボットシステムでは、TOMLベースの設定管理システムを実装しています。`api/core/config_manager.py`モジュールにより、動的な設定更新、ホットリロード、環境変数オーバーライド、設定履歴管理などの機能を提供します。

## 主な機能

### 🔧 統合設定管理
- **TOML設定ファイル**: 人間が読みやすい設定ファイル形式
- **Pydantic検証**: 型安全な設定バリデーション
- **環境変数オーバーライド**: 環境変数による設定上書き
- **ホットリロード**: 設定変更の自動検出と反映

### 📝 設定変更管理
- **変更履歴**: 全ての設定変更の記録
- **ロールバック機能**: 特定時点への設定復元
- **変更通知**: 設定変更のサブスクライバー通知
- **インポート/エクスポート**: 設定のインポートとエクスポート

### 🛡️ セキュリティ
- **シークレット管理**: 環境変数によるシークレット管理
- **設定検証**: 不正な設定値の検出
- **バックアップ復元**: エラー時の自動復元機能

## 設定ファイル構造

### 基本設定 (config.toml)

```toml
[app]
name = "LangChain Chatbot"
version = "1.0.0"
debug = false

[backend]
host = "0.0.0.0"
port = 8000
reload = true

[qdrant]
host = "localhost"
port = 6333
grpc_port = 6334
collection_name = "chatbot_knowledge"

[ollama]
base_url = "http://localhost:11434"
model_name = "nomic-embed-text:latest"

[llm]
api_base = "http://localhost:8000/v1"
api_key = "your-api-key"
model_name = "gpt-3.5-turbo"
temperature = 0.7
max_tokens = 1000
top_p = 1.0
frequency_penalty = 0.0
presence_penalty = 0.0

[embedding]
provider = "ollama"
base_url = "http://localhost:11434"
model_name = "nomic-embed-text:latest"
dimension = 768

[upload]
directory = "./uploads"
max_file_size = 10485760  # 10MB

[security]
secret_key = "your-secret-key"
algorithm = "HS256"
access_token_expire_minutes = 30

[cors]
origins = ["http://localhost:3000"]
```

## ConfigManager クラスの使用方法

### 基本的な使用方法

```python
from api.core.config_manager import config_manager

# 設定の取得
config = config_manager.get_config()

# 特定の設定値を取得
llm_model = config_manager.get_value("llm", "model_name")
qdrant_host = config_manager.get_value("qdrant", "host")

# 設定値の更新
result = config_manager.set_value(
    section="llm",
    field="temperature", 
    value=0.8,
    user="admin",
    description="Increase temperature for more creative responses"
)

if result.success:
    print(f"設定更新成功: {result.message}")
else:
    print(f"設定更新失敗: {result.message}")
```

### 設定変更の監視

```python
def on_llm_temperature_changed(change):
    print(f"LLM温度が変更されました: {change.old_value} -> {change.new_value}")

# 変更をサブスクライブ
config_manager.subscribe_to_changes("llm", "temperature", on_llm_temperature_changed)

# サブスクライブ解除
config_manager.unsubscribe_from_changes("llm", "temperature", on_llm_temperature_changed)
```

### 設定のインポート/エクスポート

```python
# 設定のエクスポート
config_manager.export_config("backup_config.toml", format="toml")
config_manager.export_config("backup_config.json", format="json")

# 設定のインポート
result = config_manager.import_config("new_config.toml", format="toml", merge=True)
```

### 変更履歴の管理

```python
# 変更履歴の取得
history = config_manager.get_change_history()

# 特定セクションの履歴
llm_history = config_manager.get_change_history(section="llm")

# 直近5件の履歴
recent_history = config_manager.get_change_history(limit=5)

# ロールバック
import time
target_timestamp = time.time() - 3600  # 1時間前
result = config_manager.rollback_to_timestamp(target_timestamp)
```

## 環境変数による設定

### サポートされている環境変数

```bash
# Qdrant設定
export QDRANT_HOST="localhost"
export QDRANT_PORT="6333"
export QDRANT_COLLECTION_NAME="chatbot_knowledge"

# LLM設定
export OPENAI_API_BASE="http://localhost:8000/v1"
export OPENAI_API_KEY="your-api-key"
export OPENAI_MODEL_NAME="gpt-3.5-turbo"
export OPENAI_TEMPERATURE="0.7"

# 埋め込み設定
export EMBEDDING_PROVIDER="ollama"
export EMBEDDING_BASE_URL="http://localhost:11434"
export EMBEDDING_MODEL_NAME="nomic-embed-text:latest"

# セキュリティ設定
export SECRET_KEY="your-secret-key"
export ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES="30"

# アップロード設定
export UPLOAD_DIR="./uploads"
export MAX_FILE_SIZE="10485760"

# バックエンド設定
export BACKEND_HOST="0.0.0.0"
export BACKEND_PORT="8000"
export BACKEND_RELOAD="true"
```

## APIエンドポイント

設定管理のためのAPIエンドポイントが利用可能です：

```python
# 設定の取得
GET /api/config

# 設定の更新
POST /api/config/update
{
    "section": "llm",
    "field": "temperature",
    "value": 0.8,
    "description": "Increase temperature"
}

# 変更履歴の取得
GET /api/config/history

# 設定のリセット
POST /api/config/reset
```

## 設定モデル

### ChatbotConfig

```python
@dataclass
class ChatbotConfig:
    app: AppConfig
    backend: BackendConfig
    qdrant: QdrantConfig
    ollama: OllamaConfig
    llm: LLMConfig
    embedding: EmbeddingConfig
    upload: UploadConfig
    security: SecurityConfig
    cors: CorsConfig
    chat: ChatConfig
    database: DatabaseConfig
```

## ベストプラクティス

### 1. 設定ファイルの管理
- 設定ファイルはバージョン管理に含め、機密情報は環境変数で管理
- 開発環境と本番環境で別々の設定ファイルを使用
- 設定変更前に必ずバックアップを作成

### 2. セキュリティ
- APIキーやシークレットは環境変数で管理
- 設定ファイルのアクセス権限を適切に設定
- 変更履歴を監査

### 3. パフォーマンス
- 設定値はキャッシュして頻繁なファイルI/Oを避ける
- 変更通知を使用して必要なコンポーネントのみ更新
- 設定検証は非同期で実行

### 4. エラーハンドリング
- 設定読み込みエラー時はデフォルト値を使用
- 不正な設定値は検証して拒否
- エラー時は自動的にバックアップから復元

## トラブルシューティング

### 一般的な問題

1. **設定ファイルが見つからない**
   - デフォルト設定が自動的に作成されます
   - 環境変数 `CONFIG_PATH` で設定ファイルパスを指定できます

2. **設定のホットリロードが動作しない**
   - ファイル監視が有効になっていることを確認
   - 設定ファイルのパーミッションを確認

3. **環境変数が反映されない**
   - 環境変数の名前と値を確認
   - アプリケーションの再起動が必要な場合があります

### デバッグ方法

```python
# 現在の設定を表示
config = config_manager.get_config()
print(config.model_dump())

# 設定の検証結果を確認
validation = config_manager.validate_config()
print(validation)

# 変更履歴を確認
history = config_manager.get_change_history()
for change in history:
    print(f"{change.timestamp}: {change.section}.{change.field} = {change.new_value}")
```

## テスト

設定管理システムのテスト：

```bash
# 設定管理のテスト
pytest tests/test_config_manager.py

# 設定APIのテスト
pytest tests/test_config_routes.py

# 統合テスト
pytest tests/test_config_integration.py
```

この設定管理システムにより、柔軟で安全な設定管理が可能になり、運用環境での設定変更が容易になります。