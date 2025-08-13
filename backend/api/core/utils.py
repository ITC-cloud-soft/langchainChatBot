"""
共通ユーティリティモジュール

このモジュールでは、アプリケーション全体で使用される共通のユーティリティ関数を提供します。
エラーハンドリング、ロギング、バリデーションなどの汎用的な機能を含みます。
"""

import logging
import traceback
from typing import Any, Dict, Optional, Union, List, Callable
from datetime import datetime
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError


class ErrorResponse(BaseModel):
    """標準エラーレスポンスモデル"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = datetime.now().isoformat()


class AppException(Exception):
    """アプリケーション固有の例外基底クラス"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "APP_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppException):
    """バリデーションエラー例外"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class NotFoundException(AppException):
    """リソース未検出例外"""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with id '{resource_id}' not found",
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ConfigurationException(AppException):
    """設定関連の例外"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


def setup_logging(
    name: str, 
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    ロガーのセットアップ
    
    Args:
        name: ロガー名
        level: ログレベル
        format_string: ログフォーマット文字列
        
    Returns:
        設定されたロガーインスタンス
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # ハンドラーが既に存在する場合は追加しない
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def handle_exceptions(logger: logging.Logger):
    """
    例外処理デコレータ
    
    Args:
        logger: 使用するロガーインスタンス
        
    Returns:
        デコレータ関数
    """
    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except AppException as e:
                logger.error(f"Application error in {func.__name__}: {e.message}")
                raise HTTPException(
                    status_code=e.status_code,
                    detail=ErrorResponse(
                        error=e.error_code,
                        message=e.message,
                        details=e.details
                    ).model_dump()
                )
            except ValidationError as e:
                logger.error(f"Validation error in {func.__name__}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=ErrorResponse(
                        error="VALIDATION_ERROR",
                        message="Invalid request data",
                        details={"errors": e.errors()}
                    ).model_dump()
                )
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                logger.error(traceback.format_exc())
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ErrorResponse(
                        error="INTERNAL_ERROR",
                        message="An unexpected error occurred",
                        details={"trace_id": str(datetime.now().timestamp())}
                    ).model_dump()
                )
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AppException as e:
                logger.error(f"Application error in {func.__name__}: {e.message}")
                raise HTTPException(
                    status_code=e.status_code,
                    detail=ErrorResponse(
                        error=e.error_code,
                        message=e.message,
                        details=e.details
                    ).model_dump()
                )
            except ValidationError as e:
                logger.error(f"Validation error in {func.__name__}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=ErrorResponse(
                        error="VALIDATION_ERROR",
                        message="Invalid request data",
                        details={"errors": e.errors()}
                    ).model_dump()
                )
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                logger.error(traceback.format_exc())
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ErrorResponse(
                        error="INTERNAL_ERROR",
                        message="An unexpected error occurred",
                        details={"trace_id": str(datetime.now().timestamp())}
                    ).model_dump()
                )
        
        # 非同期関数か同期関数かを判定
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    必須フィールドのバリデーション
    
    Args:
        data: バリデーション対象のデータ
        required_fields: 必須フィールドのリスト
        
    Raises:
        ValidationException: 必須フィールドが不足している場合
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        raise ValidationException(
            message="Required fields are missing",
            details={"missing_fields": missing_fields}
        )


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    入力テキストのサニタイズ
    
    Args:
        text: サニタイズ対象のテキスト
        max_length: 最大長
        
    Returns:
        サニタイズされたテキスト
    """
    if not text:
        return ""
    
    # 長さの制限
    if len(text) > max_length:
        text = text[:max_length]
    
    # 危険な文字のエスケープ（簡易版）
    text = text.replace("<", "<").replace(">", ">")
    
    return text.strip()


def format_success_response(
    data: Any = None, 
    message: str = "Success",
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    標準成功レスポンスのフォーマット
    
    Args:
        data: レスポンスデータ
        message: 成功メッセージ
        meta: メタデータ
        
    Returns:
        フォーマットされたレスポンス
    """
    response = {
        "success": True,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if meta:
        response["meta"] = meta
    
    return response


def create_pagination_response(
    items: List[Any], 
    total: int, 
    page: int, 
    page_size: int
) -> Dict[str, Any]:
    """
    ページネーションレスポンスの作成
    
    Args:
        items: 現在のページのアイテムリスト
        total: 総アイテム数
        page: 現在のページ番号
        page_size: ページサイズ
        
    Returns:
        ページネーション情報を含むレスポンス
    """
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


# デフォルトロガーの作成
default_logger = setup_logging("chatbot_app")