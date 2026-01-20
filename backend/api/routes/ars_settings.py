"""
ARS Settings API endpoints

This module provides endpoints for managing ARS (Application Resource Service) API tokens:
- Get ARS token for current user
- Save/Update ARS token for current user
"""

import os
import time
import logging
from typing import Annotated, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db_session
from api.models.user import (
    get_ars_token_by_user,
    create_or_update_ars_token,
    get_ars_system_prompt_by_user,
    ApiArsToken
)
from api.middleware import CurrentUser, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Get ARS endpoint from environment variable
ARS_API_ENDPOINT = os.getenv("ARS_API_ENDPOINT", "http://localhost:5050")

# In-memory cache for ARS tokens (5 minutes expiry)
_token_cache = {
    'users': {},  # {user_id: {'token': token_value, 'last_updated': timestamp}}
    'expiry': 300  # Cache expiry in seconds
}


# Pydantic models
class ArsSettingsResponse(BaseModel):
    """ARS settings response model"""
    data: dict
    systemPrompt: Optional[str] = None
    lastUpdated: Optional[str] = None


class ArsSettingsSaveRequest(BaseModel):
    """ARS settings save request model"""
    apiKey: str = Field(..., description="ARS API key")


class ArsSettingsTestRequest(BaseModel):
    """ARS settings test request model"""
    apiKey: str = Field(..., description="ARS API key to test")
    apiEndpoint: Optional[str] = Field(default=None, description="ARS API endpoint")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    retryCount: int = Field(default=3, description="Number of retries")


@router.get("/ars-settings", response_model=ArsSettingsResponse)
async def get_ars_settings(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    Get ARS settings for current user
    
    Returns the ARS API key stored for the current user.
    Uses caching to improve performance.
    """
    user_id = current_user.user_id
    logger.info(f"ARS設定の取得: ユーザーID = {user_id}")
    
    # Check cache
    current_time = time.time()
    user_cache = _token_cache['users'].get(user_id)
    
    if user_cache and current_time - user_cache['last_updated'] < _token_cache['expiry']:
        # Use cached token
        token = user_cache['token']
        logger.info(f"キャッシュからのトークン: {token[:5] if token else 'empty'}...")
    else:
        # Fetch from database and update cache
        logger.info("キャッシュが無効または期限切れ、データベースからトークンを取得")
        ars_token = await get_ars_token_by_user(db, user_id)
        
        if ars_token:
            token = ars_token.token
            # Update cache
            _token_cache['users'][user_id] = {
                'token': token,
                'last_updated': current_time
            }
        else:
            token = ''
    
    # Get system prompt if exists
    system_prompt_obj = await get_ars_system_prompt_by_user(db, user_id)
    system_prompt = system_prompt_obj.prompt if system_prompt_obj else None
    last_updated = system_prompt_obj.updated_at.isoformat() if system_prompt_obj else None
    
    return ArsSettingsResponse(
        data={"apiKey": token},
        systemPrompt=system_prompt,
        lastUpdated=last_updated
    )


@router.post("/ars-settings", status_code=status.HTTP_201_CREATED)
async def save_ars_settings(
    request: ArsSettingsSaveRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    Save ARS settings for current user
    
    Creates or updates the ARS API key for the current user.
    """
    user_id = current_user.user_id
    api_key = request.apiKey
    
    logger.info(f"ARS設定の保存: ユーザーID = {user_id}, API Key = {api_key[:5] if api_key else 'empty'}...")
    
    try:
        # Create or update token
        ars_token = await create_or_update_ars_token(
            db=db,
            user_id=user_id,
            token=api_key,
            token_type="token"
        )
        
        logger.info("データベース更新成功")
        
        # Update cache
        _token_cache['users'][user_id] = {
            'token': api_key,
            'last_updated': time.time()
        }
        logger.info("キャッシュが更新されました")
        
        return {"result": "success", "message": "ARS設定を保存しました"}
        
    except Exception as e:
        logger.error(f"ARS設定の保存に失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ARS設定の保存中にエラーが発生しました: {str(e)}"
        )


@router.post("/ars-settings/test")
async def test_ars_connection(
    request: ArsSettingsTestRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    Test ARS connection
    
    Tests the connection to ARS service with provided credentials.
    This is a placeholder - actual implementation would make a real API call to ARS.
    """
    user_id = current_user.user_id
    logger.info(f"ARS接続テスト: ユーザーID = {user_id}")
    
    # Use provided endpoint or default from environment
    endpoint = request.apiEndpoint or ARS_API_ENDPOINT
    
    # TODO: Implement actual ARS connection test
    # For now, just validate that the API key is not empty
    if not request.apiKey or request.apiKey.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="APIキーが空です"
        )
    
    # Simulate connection test
    logger.info(f"ARS接続テスト成功 (シミュレーション): {endpoint}")
    
    return {
        "result": "success",
        "message": "ARS接続テストに成功しました",
        "endpoint": endpoint,
        "timeout": request.timeout
    }


@router.post("/ars-settings/update-prompt")
async def update_system_prompt(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    Manually trigger system prompt update from ARS
    
    Fetches the latest system prompt from ARS API and saves it to database.
    """
    from api.services.ars_service import ArsService
    
    user_id = current_user.user_id
    logger.info(f"手動システムプロンプト更新: ユーザーID = {user_id}")
    
    try:
        # Trigger update for current user
        system_prompt = await ArsService.update_system_prompt_for_user(db, user_id)
        
        if system_prompt:
            logger.info(f"システムプロンプト更新成功: ユーザーID = {user_id}")
            return {
                "result": "success",
                "message": "システムプロンプトを更新しました",
                "prompt": system_prompt[:100] + "..." if len(system_prompt) > 100 else system_prompt
            }
        else:
            logger.warning(f"システムプロンプト更新失敗: ユーザーID = {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="システムプロンプトの取得に失敗しました。APIキーが正しく設定されているか確認してください。"
            )
            
    except Exception as e:
        logger.error(f"システムプロンプト更新エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"システムプロンプトの更新中にエラーが発生しました: {str(e)}"
        )
