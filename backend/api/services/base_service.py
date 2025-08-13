"""
基底サービスクラス

このモジュールでは、すべてのサービスクラスが継承する基底クラスを提供します。
共通の初期化ロジック、エラーハンドリング、ロギング機能を含みます。
"""

import logging
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

from api.core.utils import default_logger, handle_exceptions
from api.core.config_manager import config_manager


class BaseService(ABC):
    """
    すべてのサービスクラスの基底クラス
    
    共通の初期化ロジック、エラーハンドリング、ロギング機能を提供します。
    """
    
    def __init__(self, logger_name: Optional[str] = None):
        """
        基底サービスクラスを初期化
        
        Args:
            logger_name: ロガー名。Noneの場合はクラス名を使用
        """
        self.logger = logger_name or default_logger
        if not isinstance(self.logger, logging.Logger):
            self.logger = default_logger
        
        self._initialized = False
        self.config = config_manager.get_config()
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        サービスを初期化
        
        Returns:
            bool: 初期化が成功したかどうか
        """
        pass
    
    @property
    def initialized(self) -> bool:
        """
        サービスが初期化されているかどうか
        
        Returns:
            bool: 初期化されているかどうか
        """
        return self._initialized
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        サービスのヘルスチェックを実行
        
        Returns:
            ヘルスチェック結果を含む辞書
        """
        pass
    
    def ensure_initialized(self) -> None:
        """
        サービスが初期化されていることを確認
        
        Raises:
            RuntimeError: サービスが初期化されていない場合
        """
        if not self._initialized:
            raise RuntimeError(f"{self.__class__.__name__} is not initialized")
    
    def update_config(self) -> None:
        """
        設定を更新
        """
        self.config = config_manager.get_config()
        self.logger.info(f"Configuration updated for {self.__class__.__name__}")
    
    def log_error(self, message: str, exception: Exception = None, **kwargs) -> None:
        """
        エラーログを記録
        
        Args:
            message: エラーメッセージ
            exception: 例外オブジェクト
            **kwargs: 追加のログ情報
        """
        log_data = {"service": self.__class__.__name__, **kwargs}
        if exception:
            self.logger.error(f"{message}: {str(exception)}", extra=log_data, exc_info=True)
        else:
            self.logger.error(message, extra=log_data)
    
    def log_info(self, message: str, **kwargs) -> None:
        """
        情報ログを記録
        
        Args:
            message: ログメッセージ
            **kwargs: 追加のログ情報
        """
        log_data = {"service": self.__class__.__name__, **kwargs}
        self.logger.info(message, extra=log_data)
    
    def log_warning(self, message: str, **kwargs) -> None:
        """
        警告ログを記録
        
        Args:
            message: 警告メッセージ
            **kwargs: 追加のログ情報
        """
        log_data = {"service": self.__class__.__name__, **kwargs}
        self.logger.warning(message, extra=log_data)
    
    def log_debug(self, message: str, **kwargs) -> None:
        """
        デバッグログを記録
        
        Args:
            message: デバッグメッセージ
            **kwargs: 追加のログ情報
        """
        pass


class ServiceRegistry:
    """
    サービスレジストリクラス
    
    アプリケーション内のすべてのサービスを管理します。
    """
    
    _instance = None
    _services: Dict[str, BaseService] = {}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceRegistry, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, name: str, service: BaseService) -> None:
        """
        サービスを登録
        
        Args:
            name: サービス名
            service: サービスインスタンス
            
        Raises:
            ValueError: サービスが既に登録されている場合
        """
        if name in cls._services:
            raise ValueError(f"Service '{name}' is already registered")
        cls._services[name] = service
        service.log_info(f"Service registered: {name}")
    
    @classmethod
    def get(cls, name: str) -> BaseService:
        """
        サービスを取得
        
        Args:
            name: サービス名
            
        Returns:
            サービスインスタンス
            
        Raises:
            ValueError: サービスが見つからない場合
        """
        if name not in cls._services:
            raise ValueError(f"Service '{name}' not found")
        return cls._services[name]
    
    @classmethod
    def list_services(cls) -> Dict[str, BaseService]:
        """
        登録されているすべてのサービスを取得
        
        Returns:
            サービス名とサービスインスタンスのマッピング
        """
        return cls._services.copy()
    
    @classmethod
    def get_all(cls) -> Dict[str, BaseService]:
        """
        登録されているすべてのサービスを取得
        
        Returns:
            サービス名とサービスインスタンスのマッピング
        """
        return cls._services.copy()
    
    @classmethod
    def remove(cls, name: str) -> None:
        """
        サービスを削除
        
        Args:
            name: サービス名
            
        Raises:
            ValueError: サービスが見つからない場合
        """
        if name not in cls._services:
            raise ValueError(f"Service '{name}' not found")
        del cls._services[name]
    
    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        サービスが登録されているかどうかを確認
        
        Args:
            name: サービス名
            
        Returns:
            bool: 登録されているかどうか
        """
        return name in cls._services
    
    @classmethod
    async def initialize_all(cls) -> Dict[str, bool]:
        """
        すべてのサービスを初期化
        
        Returns:
            サービス名と初期化結果のマッピング
        """
        results = {}
        all_success = True
        for name, service in cls._services.items():
            try:
                result = await service.initialize()
                results[name] = result
                if result:
                    service.log_info(f"Service initialized successfully: {name}")
                else:
                    service.log_error(f"Failed to initialize service: {name}")
                    all_success = False
            except Exception as e:
                service.log_error(f"Error initializing service: {name}", e)
                results[name] = False
                all_success = False
        cls._initialized = all_success
        return results
    
    @classmethod
    async def health_check_all(cls) -> Dict[str, Dict[str, Any]]:
        """
        すべてのサービスのヘルスチェックを実行
        
        Returns:
            サービス名とヘルスチェック結果のマッピング
        """
        results = {}
        for name, service in cls._services.items():
            try:
                result = await service.health_check()
                results[name] = result
            except Exception as e:
                service.log_error(f"Error during health check: {name}", e)
                results[name] = {"status": "error", "message": str(e)}
        return results
    
    @classmethod
    async def shutdown_all(cls) -> None:
        """
        すべてのサービスをシャットダウン
        """
        for name, service in cls._services.items():
            try:
                if hasattr(service, 'shutdown'):
                    await service.shutdown()
                    service.log_info(f"Service shutdown successfully: {name}")
            except Exception as e:
                service.log_error(f"Error shutting down service: {name}", e)
        cls._services.clear()
        cls._initialized = False
    
    @classmethod
    def clear(cls) -> None:
        """
        すべてのサービスをクリア
        """
        cls._services.clear()
        cls._initialized = False