"""
TOML設定ファイルのPydanticモデル定義

このモジュールでは、TOML設定ファイルの構造をPydanticモデルとして定義します。
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


# プロバイダー別のデフォルト設定
PROVIDER_DEFAULTS = {
    "openai": {
        "api_base": "https://api.openai.com/v1",
        "model_name": "gpt-3.5-turbo"
    },
    "anthropic": {
        "api_base": "https://api.anthropic.com",
        "model_name": "claude-3-sonnet-20240229"
    },
    "gemini": {
        "api_base": "https://generativelanguage.googleapis.com/v1",
        "model_name": "gemini-pro"
    },
    "カスタム": {
        "api_base": "",
        "model_name": ""
    }
}


class AppConfig(BaseModel):
    """アプリケーション設定"""
    name: str = Field(default="チャットボットシステム", description="アプリケーション名")
    version: str = Field(default="1.0.0", description="アプリケーションバージョン")
    debug: bool = Field(default=False, description="デバッグモード")


class BackendConfig(BaseModel):
    """バックエンド設定"""
    host: str = Field(default="0.0.0.0", description="バックエンドサーバーのホスト")
    port: int = Field(default=8000, ge=1, le=65535, description="バックエンドサーバーのポート")
    reload: bool = Field(default=True, description="開発モードでの自動リロード")


class FrontendConfig(BaseModel):
    """フロントエンド設定"""
    host: str = Field(default="localhost", description="フロントエンドサーバーのホスト")
    port: int = Field(default=3000, ge=1, le=65535, description="フロントエンドサーバーのポート")


class CorsConfig(BaseModel):
    """CORS設定"""
    origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="許可するオリジンのリスト"
    )
    
    @field_validator('origins')
    @classmethod
    def validate_origins(cls, v):
        if not v:
            raise ValueError("CORS origins cannot be empty")
        return v



class QdrantConfig(BaseModel):
    """Qdrant設定"""
    host: str = Field(default="localhost", description="Qdrantサーバーのホスト")
    port: int = Field(default=6333, ge=1, le=65535, description="QdrantサーバーのHTTPポート")
    grpc_port: int = Field(default=6334, ge=1, le=65535, description="QdrantサーバーのgRPCポート")
    collection_name: str = Field(default="chatbot_knowledge", description="Qdrantコレクション名")
    api_key: Optional[str] = Field(default=None, description="Qdrant APIキー")



class EmbeddingConfig(BaseModel):
    """埋め込みモデル設定"""
    provider: str = Field(default="ollama", description="埋め込みプロバイダー")
    base_url: str = Field(default="http://localhost:11434", description="埋め込みAPIのベースURL")
    model_name: str = Field(default="nomic-embed-text:latest", description="埋め込みモデル名")
    api_key: str = Field(default="", description="埋め込みAPIのキー")
    dimension: int = Field(default=768, ge=1, description="埋め込みベクトルの次元数")
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v):
        valid_providers = ["ollama", "openai", "カスタム"]
        if v not in valid_providers:
            raise ValueError(f"Provider must be one of {valid_providers}")
        return v


class LoggingConfig(BaseModel):
    """ログ設定"""
    level: str = Field(default="INFO", description="ログレベル")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="ログフォーマット")
    file: str = Field(default="app.log", description="ログファイル名")


class LlmConfig(BaseModel):
    """LLM設定"""
    provider: str = Field(default="openai", description="LLMプロバイダー")
    api_base: str = Field(default="https://api.openai.com/v1", description="LLM APIのベースURL")
    api_key: str = Field(default="nokey", description="LLM APIのキー")
    model_name: str = Field(default="gpt-3.5-turbo", description="使用するLLMモデル名")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="生成の多様性（0.0-2.0）")
    max_tokens: int = Field(default=128000, ge=1, description="最大トークン数")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="トークン選択の確率閾値（0.0-1.0）")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="頻度ペナルティ（-2.0-2.0）")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="存在ペナルティ（-2.0-2.0）")
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v):
        valid_providers = ["openai", "anthropic", "gemini", "カスタム"]
        if v not in valid_providers:
            raise ValueError(f"Provider must be one of {valid_providers}")
        return v
    
    @model_validator(mode='before')
    @classmethod
    def set_provider_defaults(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """プロバイダーに基づいてデフォルト値を設定"""
        provider = data.get('provider', 'openai')
        
        # プロバイダーが変更された場合、対応するデフォルト値を設定
        if provider in PROVIDER_DEFAULTS:
            defaults = PROVIDER_DEFAULTS[provider]
            
            # api_baseが明示的に設定されていない場合、デフォルト値を使用
            if 'api_base' not in data or data['api_base'] in ["", "http://localhost:11434/v1"]:
                data['api_base'] = defaults['api_base']
            
            # model_nameが明示的に設定されていない場合、デフォルト値を使用
            if 'model_name' not in data or not data['model_name']:
                data['model_name'] = defaults['model_name']
        
        return data
    
    @field_validator('api_base')
    @classmethod
    def validate_api_base(cls, v, values):
        """プロバイダーに応じたAPI Base URLのバリデーション"""
        provider = values.data.get('provider') if hasattr(values, 'data') else 'openai'
        
        # カスタム以外のプロバイダーでは、空のURLを許可しない
        if provider != "カスタム" and not v:
            defaults = PROVIDER_DEFAULTS.get(provider, {})
            if defaults.get('api_base'):
                v = defaults['api_base']
        
        return v


class UploadConfig(BaseModel):
    """アップロード設定"""
    directory: str = Field(default="./uploads", description="アップロードファイルの保存先ディレクトリ")
    max_file_size: int = Field(default=10485760, ge=1, description="最大ファイルサイズ（バイト単位、10MB）")


class ChatConfig(BaseModel):
    """チャット設定"""
    max_history: int = Field(default=10, ge=1, le=50, description="履歴に保持する最大メッセージ数")
    prompt_template: str = Field(
        default="""以下の会話履歴とコンテキストを使用して、最後の質問に答えてください。

会話履歴:
{chat_history}

コンテキスト:
{context}

質問: {question}

回答:""",
        description="チャットプロンプトテンプレート"
    )
    user_label: str = Field(default="ユーザー", description="ユーザーラベル")
    assistant_label: str = Field(default="アシスタント", description="アシスタントラベル")
    
    @field_validator('prompt_template')
    @classmethod
    def validate_prompt_template(cls, v):
        """プロンプトテンプレートのバリデーション"""
        required_placeholders = ['{chat_history}', '{context}', '{question}']
        for placeholder in required_placeholders:
            if placeholder not in v:
                raise ValueError(f"Prompt template must contain {placeholder}")
        return v


class DatabaseConfig(BaseModel):
    """データベース設定"""
    host: str = Field(default="localhost", description="MySQLサーバーのホスト")
    port: int = Field(default=3306, ge=1, le=65535, description="MySQLサーバーのポート")
    username: str = Field(default="root", description="MySQLユーザー名")
    password: str = Field(default="", description="MySQLパスワード")
    database: str = Field(default="chatbot", description="データベース名")
    ssl: bool = Field(default=False, description="SSL接続を使用するかどうか")
    pool_size: int = Field(default=20, ge=1, le=100, description="コネクションプールサイズ")
    max_overflow: int = Field(default=30, ge=1, le=50, description="最大オーバーフロー接続数")
    pool_recycle: int = Field(default=3600, ge=300, description="コネクション再利用時間（秒）")
    echo_sql: bool = Field(default=False, description="SQLログを出力するかどうか")



class SecurityConfig(BaseModel):
    """セキュリティ設定"""
    secret_key: str = Field(default="your-secret-key-here", description="JWTシークレットキー")
    algorithm: str = Field(default="HS256", description="JWTアルゴリズム")
    access_token_expire_minutes: int = Field(default=30, ge=1, description="アクセストークンの有効期限（分）")


class ChatbotConfig(BaseModel):
    """メイン設定モデル"""
    app: AppConfig = Field(default_factory=AppConfig)
    backend: BackendConfig = Field(default_factory=BackendConfig)
    frontend: FrontendConfig = Field(default_factory=FrontendConfig)
    cors: CorsConfig = Field(default_factory=CorsConfig)
    qdrant: QdrantConfig = Field(default_factory=QdrantConfig)
    llm: LlmConfig = Field(default_factory=LlmConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    upload: UploadConfig = Field(default_factory=UploadConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    chat: ChatConfig = Field(default_factory=ChatConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    @field_validator('cors')
    @classmethod
    def validate_cors_with_frontend(cls, v, values):
        """CORS設定とフロントエンド設定の整合性チェック"""
        if 'frontend' in values.data:
            frontend_host = values.data['frontend'].host
            frontend_port = values.data['frontend'].port
            frontend_url = f"http://{frontend_host}:{frontend_port}"
            
            if frontend_url not in v.origins:
                raise ValueError(f"CORS origins must include frontend URL: {frontend_url}")
        return v
    
    @field_validator('backend')
    @classmethod
    def validate_backend_port(cls, v, values):
        """バックエンドポートの重複チェック"""
        if 'frontend' in values.data and v.port == values.data['frontend'].port:
            raise ValueError("Backend and frontend ports must be different")
        return v