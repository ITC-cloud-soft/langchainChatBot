"""
Chat API routes for the Chatbot System

This module provides API endpoints for chat functionality.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
import json

from api.core.qdrant_manager import qdrant_manager
from api.core.database import database_manager, get_db_session
from api.core.utils import handle_exceptions, default_logger, format_success_response
from api.services.chat_service import chat_service
from api.services.chat_history_service import chat_history_service
from api.middleware import CurrentUser, get_current_user, get_optional_current_user
from api.models.user import get_ars_system_prompt_by_user
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

# Create router
router = APIRouter()

# Pydantic models
class ChatMessage(BaseModel):
    """Chat message model"""
    message: str
    session_id: Optional[str] = None
    system_prompt: Optional[str] = None
    
    @field_validator('message')
    @classmethod
    def message_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Message must not be empty')
        return v

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    source_documents: Optional[List[Dict[str, Any]]] = None
    session_id: str


class ChatSessionCreate(BaseModel):
    """Chat session creation model"""
    session_id: Optional[str] = None
    title: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None




class ChatSessionUpdate(BaseModel):
    """Chat session update model"""
    title: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatSessionResponse(BaseModel):
    """Chat session response model"""
    id: Optional[int] = None
    session_id: str
    title: Optional[str] = None
    user_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_active: bool
    metadata: Optional[Dict[str, Any]] = None


class ChatSessionListResponse(BaseModel):
    """Chat session list response model"""
    sessions: List[ChatSessionResponse]
    total_count: int
    limit: Optional[int] = None
    offset: Optional[int] = None


class ChatHistoryResponse(BaseModel):
    """Chat history response model"""
    session: ChatSessionResponse
    messages: List[Dict[str, Any]]
    metadata: Dict[str, Any]




# Chat service is already initialized in main.py

@router.post("/send", response_model=ChatResponse)
async def send_message(
    chat_message: ChatMessage,
    current_user: Annotated[Optional[CurrentUser], Depends(get_optional_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """Send a message to the chatbot and get a response"""
    try:
        # Debug logging
        default_logger.info(f"Received send request: message='{chat_message.message}', session_id='{chat_message.session_id}'")
        
        # Get ARS system prompt from database if not provided and user is authenticated
        system_prompt = chat_message.system_prompt
        if not system_prompt and current_user:
            ars_prompt = await get_ars_system_prompt_by_user(db, current_user.user_id)
            if ars_prompt:
                system_prompt = ars_prompt.prompt
                default_logger.info(f"Using ARS system prompt for user {current_user.user_id}")
        
        # Process message through chat service
        response = await chat_service.process_message(
            message=chat_message.message,
            session_id=chat_message.session_id,
            system_prompt=system_prompt
        )
        
        return ChatResponse(**response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def stream_message(
    chat_message: ChatMessage,
    current_user: Annotated[Optional[CurrentUser], Depends(get_optional_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """Stream a chatbot response"""
    # Debug logging
    default_logger.info(f"Received stream request: message='{chat_message.message}', session_id='{chat_message.session_id}'")
    
    # Get ARS system prompt from database if not provided and user is authenticated
    system_prompt = chat_message.system_prompt
    ars_token = None
    
    default_logger.info(f"[ARS DEBUG] stream - current_user: {current_user}, system_prompt from request: {system_prompt}")
    if not system_prompt and current_user:
        default_logger.info(f"[ARS DEBUG] Fetching ARS prompt for user {current_user.user_id}")
        ars_prompt = await get_ars_system_prompt_by_user(db, current_user.user_id)
        default_logger.info(f"[ARS DEBUG] ARS prompt fetched: {ars_prompt}")
        if ars_prompt:
            system_prompt = ars_prompt.prompt
            default_logger.info(f"[ARS DEBUG] Using ARS system prompt for user {current_user.user_id} in stream")
            default_logger.info(f"[ARS DEBUG] System prompt length: {len(system_prompt)} chars")
        else:
            default_logger.info(f"[ARS DEBUG] No ARS prompt found for user {current_user.user_id}")
    else:
        default_logger.info(f"[ARS DEBUG] Skipping ARS prompt fetch - system_prompt: {bool(system_prompt)}, current_user: {bool(current_user)}")
    
    # Get ARS token for flow execution
    if current_user:
        from api.models.user import get_ars_token_by_user
        ars_token_obj = await get_ars_token_by_user(db, current_user.user_id)
        if ars_token_obj:
            ars_token = ars_token_obj.token
            default_logger.info(f"[ARS DEBUG] ARS token retrieved for user {current_user.user_id}")
    
    async def generate():
        async for chunk in chat_service.stream_message(
            message=chat_message.message,
            session_id=chat_message.session_id,
            system_prompt=system_prompt,
            ars_token=ars_token
        ):
            try:
                # JSONシリアライズ時に適切なエンコーディングを保証
                json_str = json.dumps(chunk, ensure_ascii=False, separators=(',', ':'))
                yield f"data: {json_str}\n\n"
            except Exception as e:
                default_logger.error(f"JSON serialization error: {str(e)}, chunk: {chunk}")
                # エラー時はエラーメッセージを返す
                error_chunk = {"type": "error", "error": str(e)}
                yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.get("/sessions/{session_id}/history")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    try:
        history = await chat_service.get_chat_history(session_id)
        return format_success_response(
            data={"session_id": session_id, "history": history},
            message="Chat history retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat history for a session"""
    try:
        success = await chat_service.clear_chat_history(session_id)
        if success:
            return format_success_response(
                message=f"Chat history for session {session_id} cleared successfully"
            )
        else:
            return format_success_response(
                message=f"No chat history found for session {session_id}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# New chat history management endpoints
@router.post("/sessions")
async def create_chat_session(session_data: ChatSessionCreate):
    """Create a new chat session"""
    try:
        default_logger.info(f"Creating session: {session_data}")
        session = await chat_history_service.create_session(
            session_id=session_data.session_id,
            title=session_data.title,
            user_id=session_data.user_id,
            metadata=session_data.metadata
        )
        default_logger.info(f"Session created successfully: {session}")
        return format_success_response(
            data=ChatSessionResponse(**session).model_dump(),
            message="Session created successfully"
        )
    except Exception as e:
        default_logger.error(f"Session creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_chat_sessions(
    user_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    page: Optional[int] = None,
    per_page: Optional[int] = None,
    active_only: bool = True
):
    """Get list of chat sessions"""
    try:
        # Debug logging
        default_logger.info(f"Received sessions request: limit={limit}, offset={offset}, page={page}, per_page={per_page}, user_id={user_id}, active_only={active_only}")
        
        # Handle page/per_page parameters by converting to limit/offset
        if page is not None and per_page is not None:
            limit = per_page
            offset = (page - 1) * per_page
            default_logger.info(f"Converted page={page}, per_page={per_page} to limit={limit}, offset={offset}")
        
        sessions = await chat_history_service.get_session_list(
            user_id=user_id,
            limit=limit,
            offset=offset,
            active_only=active_only
        )
        return format_success_response(
            data={
                "sessions": [ChatSessionResponse(**session) for session in sessions["sessions"]],
                "total_count": sessions["total_count"],
                "limit": sessions["limit"],
                "offset": sessions["offset"]
            },
            message="Chat sessions retrieved successfully"
        )
    except Exception as e:
        default_logger.error(f"Error getting chat sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/full", response_model=ChatHistoryResponse)
async def get_chat_session_full(session_id: str):
    """Get full chat session data including messages and metadata"""
    try:
        default_logger.info(f"🔍 DEBUG: get_chat_session_full called with session_id: {session_id}")
        session_data = await chat_history_service.get_session_history(session_id)
        default_logger.info(f"🔍 DEBUG: session_data retrieved: {session_data}")
        default_logger.info(f"🔍 DEBUG: session keys: {list(session_data.keys()) if session_data else 'None'}")
        default_logger.info(f"🔍 DEBUG: messages count: {len(session_data.get('messages', [])) if session_data else 0}")
        
        return ChatHistoryResponse(
            session=ChatSessionResponse(**session_data["session"]),
            messages=session_data["messages"],
            metadata=session_data["metadata"]
        )
    except Exception as e:
        default_logger.error(f"🔍 DEBUG: Error in get_chat_session_full: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sessions/{session_id}")
async def update_chat_session(session_id: str, session_data: ChatSessionUpdate):
    """Update a chat session"""
    try:
        default_logger.info(f"🔍 DEBUG: Updating session {session_id} with data: {session_data}")
        session = await chat_history_service.update_session(
            session_id=session_id,
            title=session_data.title,
            is_active=session_data.is_active,
            metadata=session_data.metadata
        )
        default_logger.info(f"🔍 DEBUG: Session updated successfully: {session}")
        return format_success_response(
            data=ChatSessionResponse(**session).model_dump(),
            message="Session updated successfully"
        )
    except Exception as e:
        default_logger.error(f"🔍 DEBUG: Error updating session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}/permanent")
async def delete_chat_session(session_id: str):
    """Permanently delete a chat session and all related data"""
    try:
        success = await chat_history_service.delete_session(session_id)
        if success:
            return format_success_response(
                message=f"Chat session {session_id} deleted successfully"
            )
        else:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions")
async def delete_all_chat_sessions():
    """Permanently delete all chat sessions and related data"""
    try:
        result = await chat_history_service.delete_all_sessions()
        return format_success_response(
            message=f"Successfully deleted {result['deleted_sessions']} chat sessions",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@router.get("/search")
async def search_chat_sessions(
    query: str,
    user_id: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    page: Optional[int] = None,
    per_page: Optional[int] = None
):
    """Search chat sessions by content"""
    try:
        # Handle page/per_page parameters by converting to limit/offset
        if page is not None and per_page is not None:
            limit = per_page
            offset = (page - 1) * per_page
        
        results = await chat_history_service.search_sessions(
            query=query,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        return format_success_response(
            data=results,
            message="Search completed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_old_sessions(days_old: int = 30):
    """Clean up old inactive sessions"""
    try:
        result = await chat_history_service.cleanup_old_sessions(days_old=days_old)
        return format_success_response(
            data=result,
            message=f"Cleanup completed: {result['deleted_sessions']} sessions deleted"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/export")
async def export_chat_session(session_id: str, format: str = "json"):
    """Export chat session data"""
    try:
        export_data = await chat_history_service.export_session_data(
            session_id=session_id,
            format=format
        )
        return format_success_response(
            data=export_data,
            message=f"Session {session_id} exported successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def chat_health_check():
    """Comprehensive chat service health check"""
    try:
        # Check chat service health
        chat_health = await chat_service.health_check()
        
        # Check database health
        try:
            db_health = await database_manager.health_check()
        except Exception as db_error:
            db_health = {
                "status": "unhealthy",
                "error": str(db_error)
            }
        
        # Overall health status
        if chat_health["status"] == "healthy" and db_health["status"] == "healthy":
            overall_status = "healthy"
        elif chat_health["status"] == "degraded" or db_health["status"] == "degraded":
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "chat_service": chat_health,
            "database": db_health,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


class FormStatusUpdate(BaseModel):
    """表単状態更新リクエスト"""
    form_status: str
    form_data: Optional[Dict[str, Any]] = None
    execution_result: Optional[Dict[str, Any]] = None


@router.patch("/messages/{message_id}/form-status")
async def update_message_form_status(
    message_id: str,
    update_data: FormStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    表単メッセージの状態を更新
    
    Args:
        message_id: メッセージID
        update_data: 更新データ
        db: データベースセッション
        
    Returns:
        更新されたメッセージ情報
    """
    try:
        from api.models.database import update_message_form_status_async
        
        default_logger.info(
            f"Updating form status for message {message_id}: {update_data.form_status}"
        )
        
        message = await update_message_form_status_async(
            db=db,
            message_id=message_id,
            form_status=update_data.form_status,
            form_data=update_data.form_data,
            execution_result=update_data.execution_result
        )
        
        if not message:
            raise HTTPException(
                status_code=404, 
                detail=f"Message {message_id} not found"
            )
        
        return format_success_response(
            data=message.to_dict(),
            message="Form status updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        default_logger.error(f"Error updating form status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{message_id}")
async def get_message(
    message_id: str,
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    メッセージIDでメッセージを取得
    
    Args:
        message_id: メッセージID
        db: データベースセッション
        
    Returns:
        メッセージ情報
    """
    try:
        from api.models.database import get_message_by_id_async
        
        message = await get_message_by_id_async(db, message_id)
        
        if not message:
            raise HTTPException(
                status_code=404,
                detail=f"Message {message_id} not found"
            )
        
        return format_success_response(
            data=message.to_dict(),
            message="Message retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        default_logger.error(f"Error retrieving message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


