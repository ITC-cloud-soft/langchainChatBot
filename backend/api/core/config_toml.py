"""
TOML設定ファイルのパーサーとシリアライザー

このモジュールでは、TOML設定ファイルの読み込み、保存、管理機能を提供します。
"""

import os
import toml
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import logging
from copy import deepcopy

from config_models import ChatbotConfig

logger = logging.getLogger(__name__)


class TomlConfigManager:
    """TOML設定ファイルを管理するクラス"""
    
    def __init__(self, config_path: str = "config.toml"):
        """
        TOML設定マネージャーを初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = Path(config_path)
        self.config: ChatbotConfig = ChatbotConfig()
        self._ensure_config_file()
    
    def _ensure_config_file(self):
        """設定ファイルが存在することを確認し、存在しない場合は作成"""
        try:
            if not self.config_path.exists():
                logger.info(f"Config file not found at {self.config_path}, creating with defaults")
                self.save_config()
            else:
                self.load_config()
        except Exception as e:
            logger.error(f"Error ensuring config file: {e}")
            raise
    
    def load_config(self) -> ChatbotConfig:
        """
        TOML設定ファイルを読み込む
        
        Returns:
            ChatbotConfig: 読み込んだ設定オブジェクト
        """
        try:
            if not self.config_path.exists():
                logger.warning(f"Config file not found at {self.config_path}, using defaults")
                self.config = ChatbotConfig()
                return self.config
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = toml.load(f)
            
            # Pydanticモデルで検証
            self.config = ChatbotConfig(**config_data)
            logger.info(f"Config loaded from {self.config_path}")
            return self.config
        except Exception as e:
            logger.error(f"Error loading config from {self.config_path}: {e}")
            # エラー時はデフォルト設定を返す
            self.config = ChatbotConfig()
            return self.config
    
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
            config_dict = config.dict()
            
            # ディレクトリが存在しない場合は作成
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                toml.dump(config_dict, f)
            
            logger.info(f"Config saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving config to {self.config_path}: {e}")
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
        return self.load_config()
    
    def update_config(self, section: str, key: str, value: Any) -> bool:
        """
        特定の設定値を更新
        
        Args:
            section: 設定セクション名
            key: 設定キー名
            value: 設定値
            
        Returns:
            bool: 更新が成功したかどうか
        """
        try:
            if hasattr(self.config, section):
                section_obj = getattr(self.config, section)
                if hasattr(section_obj, key):
                    # 型変換を試みる
                    field_type = type(getattr(section_obj, key))
                    if field_type == bool and isinstance(value, str):
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    elif field_type == int:
                        value = int(value)
                    elif field_type == float:
                        value = float(value)
                    elif field_type == list and isinstance(value, str):
                        # JSON形式の文字列をリストに変換
                        import json
                        value = json.loads(value)
                    
                    setattr(section_obj, key, value)
                    return self.save_config()
            
            logger.error(f"Invalid config path: {section}.{key}")
            return False
        except Exception as e:
            logger.error(f"Error updating config {section}.{key}: {e}")
            return False
    
    def update_nested_config(self, path: List[str], value: Any) -> bool:
        """
        ネストされた設定値を更新
        
        Args:
            path: 設定へのパス（例: ['llm', 'temperature']）
            value: 設定値
            
        Returns:
            bool: 更新が成功したかどうか
        """
        try:
            if len(path) < 2:
                logger.error(f"Path must have at least 2 elements: {path}")
                return False
            
            section = path[0]
            key = path[1]
            
            # セクションとキーを更新
            if hasattr(self.config, section):
                section_obj = getattr(self.config, section)
                if hasattr(section_obj, key):
                    # 型変換を試みる
                    field_type = type(getattr(section_obj, key))
                    if field_type == bool and isinstance(value, str):
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    elif field_type == int:
                        value = int(value)
                    elif field_type == float:
                        value = float(value)
                    elif field_type == list and isinstance(value, str):
                        # JSON形式の文字列をリストに変換
                        import json
                        value = json.loads(value)
                    
                    setattr(section_obj, key, value)
                    return self.save_config()
            
            logger.error(f"Invalid config path: {'.'.join(path)}")
            return False
        except Exception as e:
            logger.error(f"Error updating nested config {'.'.join(path)}: {e}")
            return False
    
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
            logger.error(f"Error getting section {section_name}: {e}")
            return None
    
    def get_value(self, path: List[str]) -> Any:
        """
        ネストされた設定値を取得
        
        Args:
            path: 設定へのパス（例: ['llm', 'temperature']）
            
        Returns:
            設定値。存在しない場合はNone
        """
        try:
            if len(path) < 2:
                logger.error(f"Path must have at least 2 elements: {path}")
                return None
            
            section = path[0]
            key = path[1]
            
            if hasattr(self.config, section):
                section_obj = getattr(self.config, section)
                if hasattr(section_obj, key):
                    return getattr(section_obj, key)
            
            return None
        except Exception as e:
            logger.error(f"Error getting value for path {'.'.join(path)}: {e}")
            return None
    
    def validate_config(self) -> Dict[str, Any]:
        """
        設定を検証
        
        Returns:
            検証結果を含む辞書
        """
        try:
            # Pydanticモデルで検証
            validated_config = ChatbotConfig(**self.config.dict())
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
            logger.error(f"Error resetting config to defaults: {e}")
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
            config_dict = self.config.dict()
            
            if format.lower() == 'toml':
                with open(export_file, 'w', encoding='utf-8') as f:
                    toml.dump(config_dict, f)
            elif format.lower() == 'json':
                import json
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False, default=str)
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
            
            logger.info(f"Config exported to {export_path} in {format} format")
            return True
        except Exception as e:
            logger.error(f"Error exporting config to {export_path}: {e}")
            return False
    
    def import_config(self, import_path: str, format: str = 'toml', merge: bool = True) -> bool:
        """
        設定をインポート
        
        Args:
            import_path: インポート元のパス
            format: インポート形式（'toml'または'json'）
            merge: 既存の設定とマージするかどうか
            
        Returns:
            bool: インポートが成功したかどうか
        """
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                logger.error(f"Import file not found: {import_path}")
                return False
            
            if format.lower() == 'toml':
                with open(import_file, 'r', encoding='utf-8') as f:
                    config_data = toml.load(f)
            elif format.lower() == 'json':
                import json
                with open(import_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            else:
                logger.error(f"Unsupported import format: {format}")
                return False
            
            # インポートした設定を検証
            imported_config = ChatbotConfig(**config_data)
            
            if merge:
                # 既存の設定とマージ
                current_dict = self.config.dict()
                imported_dict = imported_config.dict()
                
                # 深いマージを実行
                merged_dict = self._deep_merge(current_dict, imported_dict)
                self.config = ChatbotConfig(**merged_dict)
            else:
                # 上書き
                self.config = imported_config
            
            # 保存
            success = self.save_config()
            if success:
                logger.info(f"Config imported from {import_path} in {format} format")
            
            return success
        except Exception as e:
            logger.error(f"Error importing config from {import_path}: {e}")
            return False
    
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


# グローバル設定マネージャーインスタンス
config_manager = TomlConfigManager()


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
    def OPENAI_API_BASE(self) -> str:
        return self._config.llm.api_base
    
    @property
    def OPENAI_API_KEY(self) -> str:
        return self._config.llm.api_key
    
    @property
    def OPENAI_MODEL_NAME(self) -> str:
        return self._config.llm.model_name
    
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


# グローバル設定インスタンス
settings = Settings()