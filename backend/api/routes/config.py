"""
設定管理のAPIエンドポイント

このモジュールでは、TOML設定ファイルを操作するためのAPIエンドポイントを提供します。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Body, Query
from pydantic import BaseModel, Field

from api.core.config_watcher import config_updater, ConfigChange, ConfigUpdateResult
from api.core.config_manager import config_manager
from api.core.utils import handle_exceptions, default_logger, format_success_response

router = APIRouter()


# 設定更新リクエストモデル
class ConfigUpdateRequest(BaseModel):
    """設定更新リクエストモデル"""
    section: str = Field(..., description="設定セクション名")
    field: str = Field(..., description="設定フィールド名")
    value: Any = Field(..., description="設定値")
    description: str = Field("", description="変更の説明")


# 設定更新レスポンスモデル
class ConfigUpdateResponse(BaseModel):
    """設定更新レスポンスモデル"""
    success: bool
    message: str
    changes: List[Dict[str, Any]] = []


# 設定取得レスポンスモデル
class ConfigGetResponse(BaseModel):
    """設定取得レスポンスモデル"""
    section: str
    field: str
    value: Any


# 変更履歴レスポンスモデル
class ChangeHistoryResponse(BaseModel):
    """変更履歴レスポンスモデル"""
    timestamp: datetime
    section: str
    field: str
    old_value: Any
    new_value: Any
    user: str
    description: str


# 設定エクスポートリクエストモデル
class ConfigExportRequest(BaseModel):
    """設定エクスポートリクエストモデル"""
    export_path: str = Field(..., description="エクスポート先のパス")
    format: str = Field(default="toml", description="エクスポート形式（'toml'または'json'）")


# 設定インポートリクエストモデル
class ConfigImportRequest(BaseModel):
    """設定インポートリクエストモデル"""
    import_path: str = Field(..., description="インポート元のパス")
    format: str = Field(default="toml", description="インポート形式（'toml'または'json'）")


@router.post("/update", response_model=ConfigUpdateResponse)
async def update_config(request: ConfigUpdateRequest):
    """
    設定を更新
    
    Args:
        request: 設定更新リクエスト
        
    Returns:
        設定更新レスポンス
    """
    try:
        # Use config manager to update configuration
        result = config_manager.set_value(request.section, request.field, request.value)
        
        if result.success:
            # Get change history
            changes = []
            if hasattr(config_manager, 'change_history') and config_manager.change_history:
                latest_change = config_manager.change_history[-1]
                changes = [{
                    "timestamp": datetime.fromtimestamp(latest_change.timestamp).isoformat(),
                    "section": latest_change.section,
                    "field": latest_change.field,
                    "old_value": latest_change.old_value,
                    "new_value": latest_change.new_value,
                    "user": latest_change.user,
                    "description": latest_change.description
                }]
            
            return ConfigUpdateResponse(
                success=True,
                message=result.message,
                changes=changes
            )
        else:
            return ConfigUpdateResponse(
                success=False,
                message=result.message,
                changes=[]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating config: {str(e)}")


@router.get("/get/{section}/{field}", response_model=ConfigGetResponse)
async def get_config(section: str, field: str):
    """
    設定値を取得
    
    Args:
        section: 設定セクション名
        field: 設定フィールド名
        
    Returns:
        設定取得レスポンス
    """
    try:
        # Get value from config manager
        value = config_manager.get_value(section, field)
        if value is None:
            raise HTTPException(status_code=404, detail=f"Config {section}.{field} not found")
        
        return ConfigGetResponse(
            section=section,
            field=field,
            value=value
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting config: {str(e)}")


@router.get("/sections", response_model=List[str])
async def get_sections():
    """
    利用可能な設定セクションの一覧を取得
    
    Returns:
        設定セクション名のリスト
    """
    try:
        # Get sections from config manager
        config = config_manager.get_config()
        return list(config.__dict__.keys())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sections: {str(e)}")


@router.get("/section/{section}", response_model=Dict[str, Any])
async def get_section(section: str):
    """
    特定の設定セクションを取得
    
    Args:
        section: 設定セクション名
        
    Returns:
        設定セクションの内容
    """
    try:
        # Get section from config manager
        section_data = config_manager.get_section(section)
        if section_data is None:
            raise HTTPException(status_code=404, detail=f"Section {section} not found")
        
        return section_data.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting section: {str(e)}")


@router.get("/history", response_model=List[ChangeHistoryResponse])
async def get_change_history(
    section: Optional[str] = Query(None, description="フィルタリングするセクション名"),
    field: Optional[str] = Query(None, description="フィルタリングするフィールド名"),
    limit: Optional[int] = Query(None, ge=1, description="取得する履歴の最大数")
):
    """
    変更履歴を取得
    
    Args:
        section: フィルタリングするセクション名
        field: フィルタリングするフィールド名
        limit: 取得する履歴の最大数
        
    Returns:
        変更履歴のリスト
    """
    try:
        # Get change history from config manager
        history = config_manager.get_change_history(section, field, limit)
        
        return [
            ChangeHistoryResponse(
                timestamp=datetime.fromtimestamp(change.timestamp),
                section=change.section,
                field=change.field,
                old_value=change.old_value,
                new_value=change.new_value,
                user=change.user,
                description=change.description
            )
            for change in history
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting change history: {str(e)}")


@router.post("/rollback/{timestamp}")
async def rollback_config(timestamp: float):
    """
    指定したタイムスタンプまで設定をロールバック
    
    Args:
        timestamp: ロールバック先のタイムスタンプ
        
    Returns:
        設定更新レスポンス
    """
    try:
        # Rollback using config manager
        result = config_manager.rollback_to_timestamp(timestamp)
        
        if result.success:
            changes = [
                {
                    "timestamp": datetime.fromtimestamp(change.timestamp).isoformat(),
                    "section": change.section,
                    "field": change.field,
                    "old_value": change.old_value,
                    "new_value": change.new_value,
                    "user": change.user,
                    "description": change.description
                }
                for change in result.changes
            ]
            
            return ConfigUpdateResponse(
                success=True,
                message=result.message,
                changes=changes
            )
        else:
            return ConfigUpdateResponse(
                success=False,
                message=result.message,
                changes=[]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rolling back config: {str(e)}")


@router.post("/export")
async def export_config(request: ConfigExportRequest):
    """
    設定をエクスポート
    
    Args:
        request: 設定エクスポートリクエスト
        
    Returns:
        エクスポート結果
    """
    try:
        # Export config using config manager
        success = config_manager.export_config(request.export_path, request.format)
        if success:
            return format_success_response(
                message=f"Config exported to {request.export_path}"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to export config")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting config: {str(e)}")


@router.post("/import")
async def import_config(request: ConfigImportRequest):
    """
    設定をインポート
    
    Args:
        request: 設定インポートリクエスト
        
    Returns:
        設定更新レスポンス
    """
    try:
        # Import config using config manager
        result = config_manager.import_config(request.import_path, request.format)
        
        if result.success:
            changes = [
                {
                    "timestamp": datetime.fromtimestamp(change.timestamp).isoformat(),
                    "section": change.section,
                    "field": change.field,
                    "old_value": change.old_value,
                    "new_value": change.new_value,
                    "user": change.user,
                    "description": change.description
                }
                for change in result.changes
            ]
            
            return ConfigUpdateResponse(
                success=True,
                message=result.message,
                changes=changes
            )
        else:
            return ConfigUpdateResponse(
                success=False,
                message=result.message,
                changes=[]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing config: {str(e)}")


@router.post("/reload")
async def reload_config():
    """
    設定を再読み込み
    
    Returns:
        再読み込み結果
    """
    try:
        # Reload config using config manager
        config = config_manager.reload_config()
        return format_success_response(
            data=config.model_dump(),
            message="Config reloaded successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading config: {str(e)}")


@router.post("/reset")
async def reset_config():
    """
    設定をデフォルト値にリセット
    
    Returns:
        リセット結果
    """
    try:
        # Reset config using config manager
        success = config_manager.reset_to_defaults()
        if success:
            config = config_manager.get_config()
            return format_success_response(
                data=config.model_dump(),
                message="Config reset to defaults"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to reset config")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting config: {str(e)}")


@router.get("/validate")
async def validate_config():
    """
    設定を検証
    
    Returns:
        検証結果
    """
    try:
        # Validate config using config manager
        validation_result = config_manager.validate_config()
        return validation_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating config: {str(e)}")


@router.get("/", response_model=Dict[str, Any])
async def get_all_config():
    """
    すべての設定を取得
    
    Returns:
        すべての設定
    """
    try:
        # Get all config using config manager
        config = config_manager.get_config()
        return config.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting config: {str(e)}")