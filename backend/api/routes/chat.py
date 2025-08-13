"""
Chat API routes for the Chatbot System

This module provides API endpoints for chat functionality.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
import json

from api.core.qdrant_manager import qdrant_manager
from api.core.database import database_manager
from api.core.utils import handle_exceptions, default_logger, format_success_response
from api.services.chat_service import chat_service
from api.services.chat_history_service import chat_history_service

# Create router
router = APIRouter()

# Pydantic models
class ChatMessage(BaseModel):
    """Chat message model"""
    message: str
    session_id: Optional[str] = None
    
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



class ConnectionManager:
    """WebSocket connection manager"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

# Global connection manager
manager = ConnectionManager()

# Chat service is already initialized in main.py

@router.post("/send", response_model=ChatResponse)
async def send_message(chat_message: ChatMessage):
    """Send a message to the chatbot and get a response"""
    try:
        # Debug logging
        default_logger.info(f"Received send request: message='{chat_message.message}', session_id='{chat_message.session_id}'")
        
        # Process message through chat service
        response = await chat_service.process_message(
            message=chat_message.message,
            session_id=chat_message.session_id
        )
        
        return ChatResponse(
            response=response["response"],
            source_documents=response.get("source_documents"),
            session_id=response["session_id"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def stream_message(chat_message: ChatMessage):
    """Stream a chatbot response"""
    # Debug logging
    default_logger.info(f"Received stream request: message='{chat_message.message}', session_id='{chat_message.session_id}'")
    
    async def generate():
        async for chunk in chat_service.stream_message(
            message=chat_message.message,
            session_id=chat_message.session_id
        ):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message
            response = await chat_service.process_message(
                message=message_data.get("message", ""),
                session_id=message_data.get("session_id")
            )
            
            # Send response back to client
            await manager.send_personal_message(
                json.dumps(response),
                websocket
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")

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
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


