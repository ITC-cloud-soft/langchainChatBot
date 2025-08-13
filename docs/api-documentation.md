# APIドキュメント

このドキュメントでは、チャットボットシステムのAPIエンドポイントについて詳細に説明します。

## ベースURL

- **開発環境**: `http://localhost:8000`
- **本番環境**: `https://api.example.com`

## 認証

現在、APIは認証を要求しませんが、将来の拡張のためにJWTトークンベースの認証が計画されています。

## レスポンス形式

すべてのAPIレスポンスはJSON形式で返されます。

### 成功レスポンス
```json
{
  "success": true,
  "data": {
    // レスポンスデータ
  },
  "message": "成功メッセージ"
}
```

### エラーレスポンス
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "エラーメッセージ",
    "details": {
      // 詳細なエラー情報
    }
  }
}
```

## エンドポイント

### チャット関連エンドポイント

#### メッセージ送信

チャットボットにメッセージを送信し、応答を受け取ります。

**エンドポイント**: `POST /api/chat/send`

**リクエストボディ**:
```json
{
  "message": "こんにちは",
  "session_id": "session-123"
}
```

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "response": "こんにちは！お手伝いできることはありますか？",
    "session_id": "session-123",
    "timestamp": "2023-07-20T10:30:00Z"
  },
  "message": "Message sent successfully"
}
```

**エラーコード**:
- `INVALID_INPUT`: 入力データが無効
- `PROCESSING_ERROR`: メッセージ処理中にエラーが発生

#### ストリーミングメッセージ送信

チャットボットにメッセージを送信し、ストリーミングで応答を受け取ります。

**エンドポイント**: `POST /api/chat/stream`

**リクエストボディ**:
```json
{
  "message": "長い質問",
  "session_id": "session-123"
}
```

**レスポンス**: Server-Sent Events (SSE)形式でストリーミングレスポンスを返します。

```
data: {"type": "start", "session_id": "session-123"}

data: {"type": "chunk", "content": "こんにちは"}

data: {"type": "chunk", "content": "！"}

data: {"type": "chunk", "content": "お手伝いできることはありますか？"}

data: {"type": "end", "session_id": "session-123"}
```

**エラーコード**:
- `INVALID_INPUT`: 入力データが無効
- `STREAMING_ERROR`: ストリーミング処理中にエラーが発生

#### チャット履歴取得

指定されたセッションIDのチャット履歴を取得します。

**エンドポイント**: `GET /api/chat/sessions/{session_id}/history`

**パスパラメータ**:
- `session_id`: セッションID

**クエリパラメータ**:
- `limit` (オプション): 取得するメッセージ数（デフォルト: 50）
- `offset` (オプション): オフセット（デフォルト: 0）

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "session_id": "session-123",
    "messages": [
      {
        "id": "msg-1",
        "role": "user",
        "content": "こんにちは",
        "timestamp": "2023-07-20T10:25:00Z"
      },
      {
        "id": "msg-2",
        "role": "assistant",
        "content": "こんにちは！お手伝いできることはありますか？",
        "timestamp": "2023-07-20T10:30:00Z"
      }
    ],
    "total": 2
  },
  "message": "Chat history retrieved successfully"
}
```

**エラーコード**:
- `SESSION_NOT_FOUND`: 指定されたセッションが存在しない

#### チャット履歴削除

指定されたセッションIDのチャット履歴を削除します。

**エンドポイント**: `DELETE /api/chat/sessions/{session_id}`

**パスパラメータ**:
- `session_id`: セッションID

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "session_id": "session-123",
    "deleted_messages": 2
  },
  "message": "Chat history deleted successfully"
}
```

**エラーコード**:
- `SESSION_NOT_FOUND`: 指定されたセッションが存在しない
- `DELETE_ERROR`: 削除中にエラーが発生

### LLM設定関連エンドポイント

#### LLM設定取得

現在のLLM設定を取得します。

**エンドポイント**: `GET /api/llm/config`

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "api_base": "http://localhost:11434/v1",
    "api_key": "sk-...",
    "model_name": "llama3",
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 0.9,
    "frequency_penalty": 0,
    "presence_penalty": 0
  },
  "message": "LLM configuration retrieved successfully"
}
```

#### LLM設定更新

LLM設定を更新します。

**エンドポイント**: `POST /api/llm/config`

**リクエストボディ**:
```json
{
  "api_base": "http://localhost:11434/v1",
  "api_key": "sk-...",
  "model_name": "llama3",
  "temperature": 0.7,
  "max_tokens": 1000,
  "top_p": 0.9,
  "frequency_penalty": 0,
  "presence_penalty": 0
}
```

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "api_base": "http://localhost:11434/v1",
    "api_key": "sk-...",
    "model_name": "llama3",
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 0.9,
    "frequency_penalty": 0,
    "presence_penalty": 0
  },
  "message": "LLM configuration updated successfully"
}
```

**エラーコード**:
- `INVALID_CONFIG`: 設定値が無効
- `UPDATE_ERROR`: 設定更新中にエラーが発生

#### LLM設定テスト

現在のLLM設定を使用してテストメッセージを送信します。

**エンドポイント**: `POST /api/llm/config/test`

**リクエストボディ**:
```json
{
  "test_message": "こんにちは"
}
```

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "response": "こんにちは！テスト成功です。",
    "response_time": 1.5,
    "tokens_used": 25
  },
  "message": "LLM configuration test successful"
}
```

**エラーコード**:
- `TEST_FAILED`: テストに失敗
- `INVALID_CONFIG`: 設定値が無効

#### 利用可能なモデル取得

利用可能なLLMモデルのリストを取得します。

**エンドポイント**: `GET /api/llm/models`

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "id": "llama3",
        "name": "Llama 3",
        "description": "Metaの最新のLLMモデル",
        "parameters": {
          "max_tokens": 4096,
          "supports_streaming": true
        }
      },
      {
        "id": "gpt-3.5-turbo",
        "name": "GPT-3.5 Turbo",
        "description": "OpenAIの高速なLLMモデル",
        "parameters": {
          "max_tokens": 4096,
          "supports_streaming": true
        }
      }
    ]
  },
  "message": "Available models retrieved successfully"
}
```

**エラーコード**:
- `FETCH_ERROR`: モデルリストの取得中にエラーが発生

#### LLM設定リセット

LLM設定をデフォルト値にリセットします。

**エンドポイント**: `POST /api/llm/config/reset`

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "api_base": "http://localhost:11434/v1",
    "api_key": "",
    "model_name": "llama3",
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 0.9,
    "frequency_penalty": 0,
    "presence_penalty": 0
  },
  "message": "LLM configuration reset to defaults"
}
```

### ナレッジ管理関連エンドポイント

#### ドキュメント追加

テキストドキュメントをナレッジベースに追加します。

**エンドポイント**: `POST /api/knowledge/document`

**リクエストボディ**:
```json
{
  "title": "製品ドキュメント",
  "content": "この製品は...",
  "metadata": {
    "source": "manual",
    "category": "product"
  }
}
```

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "document_id": "doc-123",
    "title": "製品ドキュメント",
    "chunks_count": 5,
    "status": "processed"
  },
  "message": "Document added successfully"
}
```

**エラーコード**:
- `INVALID_DOCUMENT`: ドキュメントデータが無効
- `PROCESSING_ERROR`: ドキュメント処理中にエラーが発生

#### ファイルアップロード

ファイルをアップロードしてナレッジベースに追加します。

**エンドポイント**: `POST /api/knowledge/documents/upload`

**リクエスト**: `multipart/form-data`

**フォームデータ**:
- `file`: アップロードするファイル
- `metadata` (オプション): メタデータ（JSON文字列）

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "document_id": "doc-123",
    "filename": "manual.pdf",
    "file_size": 1024000,
    "chunks_count": 25,
    "status": "processed"
  },
  "message": "File uploaded successfully"
}
```

**エラーコード**:
- `INVALID_FILE`: ファイルが無効またはサポートされていない形式
- `UPLOAD_ERROR`: アップロード中にエラーが発生
- `PROCESSING_ERROR`: ファイル処理中にエラーが発生

#### ディレクトリからドキュメント追加

ディレクトリ内のすべてのファイルをナレッジベースに追加します。

**エンドポイント**: `POST /api/knowledge/directory`

**リクエストボディ**:
```json
{
  "directory_path": "/path/to/documents",
  "file_patterns": ["*.pdf", "*.txt"],
  "recursive": true
}
```

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "processed_files": 10,
    "failed_files": 2,
    "total_chunks": 150,
    "details": {
      "processed": [
        {
          "filename": "doc1.pdf",
          "status": "success",
          "chunks": 15
        }
      ],
      "failed": [
        {
          "filename": "doc2.txt",
          "error": "Unsupported format"
        }
      ]
    }
  },
  "message": "Directory processing completed"
}
```

**エラーコード**:
- `INVALID_DIRECTORY`: ディレクトリが存在しない
- `PROCESSING_ERROR`: ディレクトリ処理中にエラーが発生

#### ナレッジ検索

ナレッジベースを検索します。

**エンドポイント**: `POST /api/knowledge/search`

**リクエストボディ**:
```json
{
  "query": "製品の機能",
  "limit": 5,
  "score_threshold": 0.7
}
```

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "document_id": "doc-123",
        "title": "製品ドキュメント",
        "content": "この製品には多くの機能があります...",
        "score": 0.85,
        "metadata": {
          "source": "manual",
          "category": "product"
        }
      }
    ],
    "total_results": 1
  },
  "message": "Search completed successfully"
}
```

**エラーコード**:
- `INVALID_QUERY`: 検索クエリが無効
- `SEARCH_ERROR`: 検索中にエラーが発生

#### コレクション情報取得

Qdrantコレクションの情報を取得します。

**エンドポイント**: `GET /api/knowledge/collection`

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "name": "chatbot_knowledge",
    "vectors_count": 1000,
    "points_count": 1000,
    "segments_count": 1,
    "status": "green",
    "config": {
      "vector_size": 768,
      "distance": "Cosine"
    }
  },
  "message": "Collection info retrieved successfully"
}
```

**エラーコード**:
- `COLLECTION_NOT_FOUND`: コレクションが存在しない
- `FETCH_ERROR': 情報取得中にエラーが発生

#### ドキュメント一覧取得

ナレッジベース内のドキュメント一覧を取得します。

**エンドポイント**: `GET /api/knowledge/documents`

**クエリパラメータ**:
- `limit` (オプション): 取得するドキュメント数（デフォルト: 20）
- `offset` (オプション): オフセット（デフォルト: 0）
- `filter` (オプション): フィルター条件（JSON文字列）

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "documents": [
      {
        "id": "doc-123",
        "title": "製品ドキュメント",
        "source": "manual.pdf",
        "chunks_count": 5,
        "created_at": "2023-07-20T10:30:00Z",
        "metadata": {
          "category": "product"
        }
      }
    ],
    "total": 1
  },
  "message": "Documents retrieved successfully"
}
```

**エラーコード**:
- `FETCH_ERROR`: ドキュメントリスト取得中にエラーが発生

#### ドキュメント削除

指定されたドキュメントをナレッジベースから削除します。

**エンドポイント**: `DELETE /api/knowledge/documents/{doc_id}`

**パスパラメータ**:
- `doc_id`: ドキュメントID

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "document_id": "doc-123",
    "deleted_chunks": 5
  },
  "message": "Document deleted successfully"
}
```

**エラーコード**:
- `DOCUMENT_NOT_FOUND`: 指定されたドキュメントが存在しない
- `DELETE_ERROR`: 削除中にエラーが発生

#### コレクションクリア

ナレッジベースからすべてのドキュメントを削除します。

**エンドポイント**: `DELETE /api/knowledge/collection`

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "deleted_documents": 10,
    "deleted_chunks": 150
  },
  "message": "Collection cleared successfully"
}
```

**エラーコード**:
- `CLEAR_ERROR`: クリア中にエラーが発生

### 設定管理関連エンドポイント

#### 設定取得

現在の設定を取得します。

**エンドポイント**: `GET /api/config`

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "backend": {
      "host": "0.0.0.0",
      "port": 8000,
      "reload": true
    },
    "cors": {
      "origins": ["http://localhost:3000"]
    },
    "qdrant": {
      "host": "qdrant",
      "port": 6333,
      "grpc_port": 6334,
      "collection_name": "chatbot_knowledge"
    },
    "ollama": {
      "base_url": "http://localhost:11434",
      "embedding_model": "nomic-embed-text:latest"
    },
    "llm": {
      "api_base": "http://localhost:11434/v1",
      "api_key": "",
      "model_name": "llama3"
    },
    "security": {
      "secret_key": "your-secret-key",
      "algorithm": "HS256",
      "access_token_expire_minutes": 30
    },
    "upload": {
      "directory": "./uploads",
      "max_file_size": 10485760
    }
  },
  "message": "Configuration retrieved successfully"
}
```

#### 設定更新

設定を更新します。

**エンドポイント**: `POST /api/config/update`

**リクエストボディ**:
```json
{
  "section": "llm",
  "field": "model_name",
  "value": "gpt-3.5-turbo"
}
```

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "section": "llm",
    "field": "model_name",
    "old_value": "llama3",
    "new_value": "gpt-3.5-turbo"
  },
  "message": "Configuration updated successfully"
}
```

**エラーコード**:
- `INVALID_SECTION`: 無効なセクション
- `INVALID_FIELD`: 無効なフィールド
- `INVALID_VALUE`: 無効な値
- `UPDATE_ERROR`: 更新中にエラーが発生

#### 設定エクスポート

設定をファイルにエクスポートします。

**エンドポイント**: `POST /api/config/export`

**リクエストボディ**:
```json
{
  "export_path": "/path/to/config.toml",
  "format": "toml"
}
```

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "export_path": "/path/to/config.toml",
    "format": "toml"
  },
  "message": "Configuration exported successfully"
}
```

**エラーコード**:
- `EXPORT_ERROR`: エクスポート中にエラーが発生

#### 設定インポート

ファイルから設定をインポートします。

**エンドポイント**: `POST /api/config/import`

**リクエストボディ**:
```json
{
  "import_path": "/path/to/config.toml",
  "format": "toml",
  "merge": true
}
```

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "import_path": "/path/to/config.toml",
    "format": "toml",
    "changes": [
      {
        "section": "llm",
        "field": "model_name",
        "old_value": "llama3",
        "new_value": "gpt-3.5-turbo"
      }
    ]
  },
  "message": "Configuration imported successfully"
}
```

**エラーコード**:
- `IMPORT_ERROR`: インポート中にエラーが発生
- `INVALID_FILE`: 無効な設定ファイル

#### 設定リセット

設定をデフォルト値にリセットします。

**エンドポイント**: `POST /api/config/reset`

**レスポンス**:
```json
{
  "success": true,
  "data": {
    "reset_sections": ["llm", "qdrant"]
  },
  "message": "Configuration reset to defaults"
}
```

**エラーコード**:
- `RESET_ERROR`: リセット中にエラーが発生

## エラーコード一覧

| エラーコード | 説明 |
|------------|------|
| `INVALID_INPUT` | 入力データが無効 |
| `PROCESSING_ERROR` | 処理中にエラーが発生 |
| `STREAMING_ERROR` | ストリーミング処理中にエラーが発生 |
| `SESSION_NOT_FOUND` | 指定されたセッションが存在しない |
| `DELETE_ERROR` | 削除中にエラーが発生 |
| `INVALID_CONFIG` | 設定値が無効 |
| `UPDATE_ERROR` | 設定更新中にエラーが発生 |
| `TEST_FAILED` | テストに失敗 |
| `FETCH_ERROR` | データ取得中にエラーが発生 |
| `INVALID_DOCUMENT` | ドキュメントデータが無効 |
| `INVALID_FILE` | ファイルが無効またはサポートされていない形式 |
| `UPLOAD_ERROR` | アップロード中にエラーが発生 |
| `INVALID_DIRECTORY` | ディレクトリが存在しない |
| `INVALID_QUERY` | 検索クエリが無効 |
| `SEARCH_ERROR` | 検索中にエラーが発生 |
| `COLLECTION_NOT_FOUND` | コレクションが存在しない |
| `DOCUMENT_NOT_FOUND` | 指定されたドキュメントが存在しない |
| `CLEAR_ERROR` | クリア中にエラーが発生 |
| `INVALID_SECTION` | 無効なセクション |
| `INVALID_FIELD` | 無効なフィールド |
| `INVALID_VALUE` | 無効な値 |
| `EXPORT_ERROR` | エクスポート中にエラーが発生 |
| `IMPORT_ERROR` | インポート中にエラーが発生 |
| `RESET_ERROR` | リセット中にエラーが発生 |

## レート制限

APIはレート制限を実装しています。現在の制限は以下の通りです：

- **一般エンドポイント**: 100リクエスト/分
- **チャットエンドポイント**: 60リクエスト/分
- **ナレッジ管理エンドポイント**: 30リクエスト/分

レート制限を超えた場合、`429 Too Many Requests`エラーが返されます。

## Webhook

現在、Webhook機能は開発中です。将来のリリースで予定されています。

## バージョン管理

APIはバージョン管理されています。現在のバージョンは`v1`です。URLにバージョンを含めることで、特定のバージョンのAPIにアクセスできます：

```
http://localhost:8000/api/v1/chat/send
```

## 変更ログ

### v1.0.0 (2023-07-20)
- 初版リリース
- チャット機能
- LLM設定管理
- ナレッジ管理
- 設定管理