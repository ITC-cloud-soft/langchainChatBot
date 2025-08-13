"""
統合設定管理モジュール

このモジュールでは、TOML設定ファイル、環境変数、実行時設定を統一的に管理する機能を提供します。
config_toml.py、config_watcher.py、nested_config.pyの機能を統合し、一貫したインターフェースを提供します。
"""

import os
import toml
from typing import Dict, Any, List, Optional, Union, Callable
from pathlib import Path
import logging
from copy import deepcopy
from dataclasses import dataclass, field

from .config_models import ChatbotConfig, ChatConfig, DatabaseConfig
from .utils import setup_logging, ConfigurationException

logger = setup_logging("config_manager")


@dataclass
class ConfigChange:
    """設定変更を表すデータクラス"""
    timestamp: float
    section: str
    field: str
    old_value: Any
    new_value: Any
    user: str = "system"
    description: str = ""


@dataclass
class ConfigUpdateResult:
    """設定更新結果を表すデータクラス"""
    success: bool
    message: str
    changes: List[ConfigChange] = field(default_factory=list)
    validation_result: Optional[Dict[str, Any]] = None


class ConfigManager:
    """統合設定管理クラス"""
    
    def __init__(self, config_path: str = "config.toml"):
        """
        設定管理クラスを初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = Path(config_path)
        self.config: ChatbotConfig = ChatbotConfig()
        self.change_history: List[ConfigChange] = []
        self.max_history_size = 100
        self.subscribers: Dict[str, List[Callable[[ConfigChange], None]]] = {}
        self.logger = logger
        
        # 設定ファイルの読み込み
        self._load_config()
    
    def _load_config(self) -> None:
        """設定ファイルを読み込む"""
        try:
            if not self.config_path.exists():
                self.logger.info(f"Config file not found at {self.config_path}, creating with defaults")
                self.save_config()
            else:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = toml.load(f)
                
                # Pydanticモデルで検証
                self.config = ChatbotConfig(**config_data)
                self.logger.info(f"Config loaded from {self.config_path}")
            
            # 環境変数で設定を上書き
            self._load_from_env()
        except Exception as e:
            self.logger.error(f"Error loading config from {self.config_path}: {e}")
            # エラー時はデフォルト設定を使用
            self.config = ChatbotConfig()
            # 環境変数からの読み込みを試みる
            self._load_from_env()
    
    def _load_from_env(self) -> None:
        """環境変数から設定を読み込む"""
        try:
            # 環境変数マッピング
            env_mappings = {
                'QDRANT_HOST': ('qdrant', 'host'),
                'QDRANT_PORT': ('qdrant', 'port'),
                'QDRANT_GRPC_PORT': ('qdrant', 'grpc_port'),
                'QDRANT_COLLECTION_NAME': ('qdrant', 'collection_name'),
                'OPENAI_API_BASE': ('llm', 'api_base'),
                'OPENAI_API_KEY': ('llm', 'api_key'),
                'OPENAI_MODEL_NAME': ('llm', 'model_name'),
                'OPENAI_TEMPERATURE': ('llm', 'temperature'),
                'OPENAI_MAX_TOKENS': ('llm', 'max_tokens'),
                'OPENAI_TOP_P': ('llm', 'top_p'),
                'OPENAI_FREQUENCY_PENALTY': ('llm', 'frequency_penalty'),
                'OPENAI_PRESENCE_PENALTY': ('llm', 'presence_penalty'),
                'EMBEDDING_PROVIDER': ('embedding', 'provider'),
                'EMBEDDING_BASE_URL': ('embedding', 'base_url'),
                'EMBEDDING_MODEL_NAME': ('embedding', 'model_name'),
                'EMBEDDING_API_KEY': ('embedding', 'api_key'),
                'EMBEDDING_DIMENSION': ('embedding', 'dimension'),
                'SECRET_KEY': ('security', 'secret_key'),
                'ALGORITHM': ('security', 'algorithm'),
                'ACCESS_TOKEN_EXPIRE_MINUTES': ('security', 'access_token_expire_minutes'),
                'UPLOAD_DIR': ('upload', 'directory'),
                'MAX_FILE_SIZE': ('upload', 'max_file_size'),
                'BACKEND_HOST': ('backend', 'host'),
                'BACKEND_PORT': ('backend', 'port'),
                'BACKEND_RELOAD': ('backend', 'reload'),
            }
            
            for env_var, (section, field) in env_mappings.items():
                env_value = os.getenv(env_var)
                if env_value is not None:
                    # 文字列の前後の空白を削除
                    env_value = env_value.strip()
                    
                    # 型変換を試みる
                    if hasattr(self.config, section):
                        section_obj = getattr(self.config, section)
                        if hasattr(section_obj, field):
                            field_type = type(getattr(section_obj, field))
                            
                            if field_type == bool:
                                env_value = env_value.lower() in ('true', '1', 'yes', 'on')
                            elif field_type == int:
                                env_value = int(env_value)
                            elif field_type == float:
                                env_value = float(env_value)
                            elif field_type == list and isinstance(env_value, str):
                                import json
                                env_value = json.loads(env_value)
                            
                            setattr(section_obj, field, env_value)
            
            self.logger.info("Environment variables loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading environment variables: {e}")
    
    def load_config(self, config_path: str = None) -> None:
        """
        設定ファイルを読み込む（パブリックインターフェース）
        
        Args:
            config_path: 設定ファイルのパス（省略時はデフォルトパスを使用）
        """
        if config_path is not None:
            self.config_path = Path(config_path)
        self._load_config()
    
    def save_config(self, config: ChatbotConfig = None) -> bool:
        """
        設定をTOMLファイルに保存
        
        Args:
            config: 保存する設定オブジェクト。Noneの場合は現在の設定を保存
            
        Returns:
            bool: 保存が成功したかどうか
        """
        try:
            if config is None:
                config = self.config
            
            # Pydanticモデルを辞書に変換
            config_dict = config.model_dump()
            
            # ディレクトリが存在しない場合は作成
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                toml.dump(config_dict, f)
            
            self.logger.info(f"Config saved to {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving config to {self.config_path}: {e}")
            return False
    
    def get_config(self) -> ChatbotConfig:
        """
        現在の設定を取得
        
        Returns:
            ChatbotConfig: 現在の設定オブジェクト
        """
        return self.config
    
    def reload_config(self) -> ChatbotConfig:
        """
        設定を再読み込み
        
        Returns:
            ChatbotConfig: 再読み込みした設定オブジェクト
        """
        self._load_config()
        return self.config
    
    def get_value(self, section: str, field: str) -> Any:
        """
        特定の設定値を取得
        
        Args:
            section: 設定セクション名
            field: 設定フィールド名
            
        Returns:
            設定値。存在しない場合はNone
        """
        try:
            if hasattr(self.config, section):
                section_obj = getattr(self.config, section)
                if hasattr(section_obj, field):
                    return getattr(section_obj, field)
            return None
        except Exception as e:
            self.logger.error(f"Error getting config value {section}.{field}: {e}")
            return None
    
    def set_value(self, section: str, field: str, value: Any, user: str = "api", description: str = "") -> ConfigUpdateResult:
        """
        特定の設定値を更新
        
        Args:
            section: 設定セクション名
            field: 設定フィールド名
            value: 設定値
            user: 更新ユーザー
            description: 変更の説明
            
        Returns:
            設定更新結果
        """
        try:
            # 現在の値を取得
            old_value = self.get_value(section, field)
            
            # 値が変更されていない場合は何もしない
            if old_value == value:
                return ConfigUpdateResult(
                    success=True,
                    message=f"No change needed for {section}.{field}"
                )
            
            # 型変換を試みる
            if hasattr(self.config, section):
                section_obj = getattr(self.config, section)
                if hasattr(section_obj, field):
                    field_type = type(getattr(section_obj, field))
                    
                    if field_type == bool and isinstance(value, str):
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    elif field_type == int:
                        # String stripping for integer configuration values
                        if isinstance(value, str):
                            value = value.strip()
                        value = int(value)
                    elif field_type == float:
                        value = float(value)
                    elif field_type == list and isinstance(value, str):
                        import json
                        value = json.loads(value)
                    elif field_type == str:
                        # String stripping for string configuration values (including URLs)
                        value = value.strip()
                    
                    setattr(section_obj, field, value)
                    
                    # 変更オブジェクトを作成
                    import time
                    change = ConfigChange(
                        timestamp=time.time(),
                        section=section,
                        field=field,
                        old_value=old_value,
                        new_value=value,
                        user=user,
                        description=description
                    )
                    
                    # 変更履歴に追加
                    self._add_to_history(change)
                    
                    # 設定を保存
                    self.save_config()
                    
                    # 変更を通知
                    self._notify_subscribers([change])
                    
                    return ConfigUpdateResult(
                        success=True,
                        message=f"Successfully updated {section}.{field}",
                        changes=[change]
                    )
            
            return ConfigUpdateResult(
                success=False,
                message=f"Invalid config path: {section}.{field}"
            )
        except Exception as e:
            self.logger.error(f"Error updating config {section}.{field}: {e}")
            return ConfigUpdateResult(
                success=False,
                message=f"Error updating {section}.{field}: {str(e)}"
            )
    
    def get_section(self, section_name: str) -> Optional[Any]:
        """
        特定の設定セクションを取得
        
        Args:
            section_name: セクション名
            
        Returns:
            セクションオブジェクト。存在しない場合はNone
        """
        try:
            if hasattr(self.config, section_name):
                return getattr(self.config, section_name)
            return None
        except Exception as e:
            self.logger.error(f"Error getting section {section_name}: {e}")
            return None
    
    def validate_config(self) -> Dict[str, Any]:
        """
        設定を検証
        
        Returns:
            検証結果を含む辞書
        """
        try:
            # Pydanticモデルで検証
            validated_config = ChatbotConfig(**self.config.model_dump())
            return {"valid": True, "config": validated_config}
        except Exception as e:
            return {"valid": False, "errors": str(e)}
    
    def reset_to_defaults(self) -> bool:
        """
        設定をデフォルト値にリセット
        
        Returns:
            bool: リセットが成功したかどうか
        """
        try:
            self.config = ChatbotConfig()
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Error resetting config to defaults: {e}")
            return False
    
    def export_config(self, export_path: str, format: str = 'toml') -> bool:
        """
        設定をエクスポート
        
        Args:
            export_path: エクスポート先のパス
            format: エクスポート形式（'toml'または'json'）
            
        Returns:
            bool: エクスポートが成功したかどうか
        """
        try:
            export_file = Path(export_path)
            config_dict = self.config.model_dump()
            
            if format.lower() == 'toml':
                with open(export_file, 'w', encoding='utf-8') as f:
                    toml.dump(config_dict, f)
            elif format.lower() == 'json':
                import json
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False, default=str)
            else:
                self.logger.error(f"Unsupported export format: {format}")
                return False
            
            self.logger.info(f"Config exported to {export_path} in {format} format")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting config to {export_path}: {e}")
            return False
    
    def import_config(self, import_path: str, format: str = 'toml', merge: bool = True) -> ConfigUpdateResult:
        """
        設定をインポート
        
        Args:
            import_path: インポート元のパス
            format: インポート形式（'toml'または'json'）
            merge: 既存の設定とマージするかどうか
            
        Returns:
            インポート結果
        """
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                return ConfigUpdateResult(
                    success=False,
                    message=f"Import file not found: {import_path}"
                )
            
            if format.lower() == 'toml':
                with open(import_file, 'r', encoding='utf-8') as f:
                    config_data = toml.load(f)
            elif format.lower() == 'json':
                import json
                with open(import_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            else:
                return ConfigUpdateResult(
                    success=False,
                    message=f"Unsupported import format: {format}"
                )
            
            # インポートした設定を検証
            imported_config = ChatbotConfig(**config_data)
            
            if merge:
                # 既存の設定とマージ
                current_dict = self.config.model_dump()
                imported_dict = imported_config.model_dump()
                
                # 深いマージを実行
                merged_dict = self._deep_merge(current_dict, imported_dict)
                self.config = ChatbotConfig(**merged_dict)
            else:
                # 上書き
                self.config = imported_config
            
            # 保存
            success = self.save_config()
            if success:
                self.logger.info(f"Config imported from {import_path} in {format} format")
                return ConfigUpdateResult(
                    success=True,
                    message=f"Successfully imported config from {import_path}"
                )
            else:
                return ConfigUpdateResult(
                    success=False,
                    message=f"Failed to save imported config"
                )
        except Exception as e:
            self.logger.error(f"Error importing config from {import_path}: {e}")
            return ConfigUpdateResult(
                success=False,
                message=f"Error importing config: {str(e)}"
            )
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
        """
        深いマージを実行
        
        Args:
            target: マージ対象の辞書
            source: マージ元の辞書
            
        Returns:
            マージ結果の辞書
        """
        result = deepcopy(target)
        
        for key, value in source.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        
        return result
    
    def _add_to_history(self, change: ConfigChange):
        """
        変更を履歴に追加
        
        Args:
            change: 追加する変更
        """
        self.change_history.append(change)
        
        # 履歴サイズが最大値を超えた場合は古いものを削除
        if len(self.change_history) > self.max_history_size:
            self.change_history = self.change_history[-self.max_history_size:]
    
    def _notify_subscribers(self, changes: List[ConfigChange]):
        """
        変更をサブスクライバーに通知
        
        Args:
            changes: 通知する変更のリスト
        """
        for change in changes:
            key = f"{change.section}.{change.field}"
            if key in self.subscribers:
                for callback in self.subscribers[key]:
                    try:
                        callback(change)
                    except Exception as e:
                        self.logger.error(f"Error notifying subscriber for {key}: {e}")
    
    def subscribe_to_changes(self, section: str, field: str, callback: Callable[[ConfigChange], None]):
        """
        設定変更をサブスクライブ
        
        Args:
            section: 設定セクション名
            field: 設定フィールド名
            callback: 変更通知時に呼び出されるコールバック関数
        """
        key = f"{section}.{field}"
        if key not in self.subscribers:
            self.subscribers[key] = []
        self.subscribers[key].append(callback)
    
    def unsubscribe_from_changes(self, section: str, field: str, callback: Callable[[ConfigChange], None]):
        """
        設定変更のサブスクライブを解除
        
        Args:
            section: 設定セクション名
            field: 設定フィールド名
            callback: 解除するコールバック関数
        """
        key = f"{section}.{field}"
        if key in self.subscribers and callback in self.subscribers[key]:
            self.subscribers[key].remove(callback)
    
    def get_change_history(self, section: Optional[str] = None, field: Optional[str] = None, 
                          limit: Optional[int] = None) -> List[ConfigChange]:
        """
        変更履歴を取得
        
        Args:
            section: フィルタリングするセクション名
            field: フィルタリングするフィールド名
            limit: 取得する履歴の最大数
            
        Returns:
            変更履歴のリスト
        """
        history = self.change_history
        
        # セクションでフィルタリング
        if section is not None:
            history = [change for change in history if change.section == section]
        
        # フィールドでフィルタリング
        if field is not None:
            history = [change for change in history if change.field == field]
        
        # 件数で制限
        if limit is not None:
            history = history[-limit:]
        
        return history
    
    def rollback_to_timestamp(self, timestamp: float) -> ConfigUpdateResult:
        """
        指定したタイムスタンプまで設定をロールバック
        
        Args:
            timestamp: ロールバック先のタイムスタンプ
            
        Returns:
            設定更新結果
        """
        try:
            # タイムスタンプより前の最後の設定状態を取得
            target_config = None
            target_index = -1
            
            # 変更履歴を時系列順にソート
            sorted_history = sorted(self.change_history, key=lambda x: x.timestamp)
            
            # タイムスタンプより前の最後の状態を特定
            for i, change in enumerate(sorted_history):
                if change.timestamp <= timestamp:
                    target_index = i
                else:
                    break
            
            # タイムスタンプより前の状態が存在しない場合、初期状態に戻す
            if target_index == -1:
                target_config = ChatbotConfig()
            else:
                # タイムスタンプより前の変更を適用して設定を再構築
                target_config = ChatbotConfig()
                changes_to_apply = sorted_history[:target_index + 1]
                
                # 各変更を順に適用
                for change in changes_to_apply:
                    if hasattr(target_config, change.section):
                        section_obj = getattr(target_config, change.section)
                        if hasattr(section_obj, change.field):
                            setattr(section_obj, change.field, change.new_value)
            
            # 現在の設定とロールバック後の設定の差分を計算
            changes = []
            if target_config is not None:
                # 設定を更新
                old_config = self.config
                self.config = target_config
                
                # 変更を保存
                self.save_config()
                
                # 変更リストを作成
                # 簡略化のために、ここでは設定全体が変更されたと見なす
                change = ConfigChange(
                    timestamp=timestamp,
                    section="config",
                    field="rollback",
                    old_value=old_config.model_dump(),
                    new_value=target_config.model_dump(),
                    user="system",
                    description=f"Rolled back to timestamp {timestamp}"
                )
                changes.append(change)
            
            return ConfigUpdateResult(
                success=True,
                message=f"Successfully rolled back to timestamp {timestamp}",
                changes=changes
            )
        except Exception as e:
            self.logger.error(f"Error rolling back to timestamp {timestamp}: {e}")
            return ConfigUpdateResult(
                success=False,
                message=f"Error rolling back to timestamp {timestamp}: {str(e)}"
            )


# グローバル設定マネージャーインスタンス
config_manager = ConfigManager()


# 後方互換性のための設定クラス
class Settings:
    """後方互換性のための設定クラス"""
    
    def __init__(self):
        self._config = config_manager.get_config()
    
    def reload(self):
        """設定を再読み込み"""
        self._config = config_manager.reload_config()
    
    @property
    def BACKEND_HOST(self) -> str:
        return self._config.backend.host
    
    @property
    def BACKEND_PORT(self) -> int:
        return self._config.backend.port
    
    @property
    def BACKEND_RELOAD(self) -> bool:
        return self._config.backend.reload
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        return self._config.cors.origins
    
    @property
    def QDRANT_HOST(self) -> str:
        return self._config.qdrant.host
    
    @property
    def QDRANT_PORT(self) -> int:
        return self._config.qdrant.port
    
    @property
    def QDRANT_GRPC_PORT(self) -> int:
        return self._config.qdrant.grpc_port
    
    @property
    def QDRANT_COLLECTION_NAME(self) -> str:
        return self._config.qdrant.collection_name
    
    @property
    def EMBEDDING_PROVIDER(self) -> str:
        return self._config.embedding.provider
    
    @property
    def EMBEDDING_BASE_URL(self) -> str:
        return self._config.embedding.base_url
    
    @property
    def EMBEDDING_MODEL_NAME(self) -> str:
        return self._config.embedding.model_name
    
    @property
    def EMBEDDING_API_KEY(self) -> str:
        return self._config.embedding.api_key
    
    @property
    def EMBEDDING_DIMENSION(self) -> int:
        return self._config.embedding.dimension
    
    @property
    def OPENAI_API_BASE(self) -> str:
        return self._config.llm.api_base
    
    @property
    def OPENAI_API_KEY(self) -> str:
        return self._config.llm.api_key
    
    @property
    def OPENAI_MODEL_NAME(self) -> str:
        return self._config.llm.model_name
    
    @property
    def OPENAI_TEMPERATURE(self) -> float:
        return self._config.llm.temperature
    
    @property
    def OPENAI_MAX_TOKENS(self) -> int:
        return self._config.llm.max_tokens
    
    @property
    def OPENAI_TOP_P(self) -> float:
        return self._config.llm.top_p
    
    @property
    def OPENAI_FREQUENCY_PENALTY(self) -> float:
        return self._config.llm.frequency_penalty
    
    @property
    def OPENAI_PRESENCE_PENALTY(self) -> float:
        return self._config.llm.presence_penalty
    
    @property
    def SECRET_KEY(self) -> str:
        return self._config.security.secret_key
    
    @property
    def ALGORITHM(self) -> str:
        return self._config.security.algorithm
    
    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return self._config.security.access_token_expire_minutes
    
    @property
    def UPLOAD_DIR(self) -> str:
        return self._config.upload.directory
    
    @property
    def MAX_FILE_SIZE(self) -> int:
        return self._config.upload.max_file_size
    
    @property
    def chat(self) -> ChatConfig:
        return self._config.chat
    
    @property
    def database(self) -> DatabaseConfig:
        return self._config.database


# グローバル設定インスタンス
settings = Settings()