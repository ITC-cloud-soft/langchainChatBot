"""
Chat history service for managing chat session persistence

This module provides services for storing and retrieving chat history
from MySQL database with async operations.
"""

import json
import uuid
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from sqlalchemy import select, delete, func, and_, or_
from tenacity import retry, stop_after_attempt, wait_exponential

from api.models.database import ChatSession, ChatMessage, ChatMetadata, create_chat_session_async, add_chat_message_async, get_chat_session_async, get_chat_messages_async, get_chat_metadata_async, delete_chat_session_async
from api.core.database import database_manager
from api.core.utils import handle_exceptions, default_logger


class ChatHistoryService:
    """
    Service for managing chat history persistence in MySQL database
    """
    
    def __init__(self):
        self.logger = default_logger
    
    async def initialize(self) -> bool:
        """Initialize chat history service"""
        try:
            # Ensure database manager is initialized
            if not database_manager.is_initialized():
                success = await database_manager.initialize()
                if not success:
                    self.logger.error("Failed to initialize database manager")
                    return False
            
            # Ensure tables exist
            success = await database_manager.create_tables()
            if not success:
                self.logger.error("Failed to create database tables")
                return False
            
            self.logger.info("Chat history service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing chat history service: {str(e)}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def create_session(
        self,
        session_id: Optional[str] = None,
        title: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new chat session"""
        try:
            if not session_id:
                session_id = str(uuid.uuid4())
            
            async with database_manager.get_session() as db_session:
                # Check if session already exists
                existing_session = await get_chat_session_async(db_session, session_id)
                if existing_session:
                    return existing_session.to_dict()
                
                # Create new session
                chat_session = await create_chat_session_async(
                    db=db_session,
                    session_id=session_id,
                    title=title,
                    user_id=user_id,
                    metadata=metadata or {}
                )
                
                self.logger.info(f"Created new chat session: {session_id}")
                return chat_session.to_dict()
                
        except Exception as e:
            self.logger.error(f"Error creating chat session: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_id: Optional[str] = None,
        message_type: str = "text",
        source_documents: Optional[List[Dict[str, Any]]] = None,
        error_info: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add a message to a chat session"""
        try:
            async with database_manager.get_session() as db_session:
                # Check if session exists, create if not
                session = await get_chat_session_async(db_session, session_id)
                if not session:
                    session = await create_chat_session_async(db_session, session_id)
                
                # Add message
                message = await add_chat_message_async(
                    db=db_session,
                    session_id=session_id,
                    role=role,
                    content=content,
                    message_id=message_id,
                    message_type=message_type,
                    source_documents=source_documents,
                    error_info=error_info,
                    metadata=metadata or {}
                )
                
                self.logger.info(f"Added message to session {session_id}: {role}")
                return message.to_dict()
                
        except Exception as e:
            self.logger.error(f"Error adding message to session {session_id}: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def get_session_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get chat history for a session"""
        try:
            async with database_manager.get_session() as db_session:
                # Get session info
                session = await get_chat_session_async(db_session, session_id)
                if not session:
                    raise NoResultFound(f"Session {session_id} not found")
                
                # Get messages
                messages = await get_chat_messages_async(db_session, session_id, limit, offset)
                message_list = [msg.to_dict() for msg in messages]
                
                # Get metadata
                metadata = await get_chat_metadata_async(db_session, session_id)
                metadata_dict = metadata.to_dict() if metadata else {}
                
                return {
                    "session": session.to_dict(),
                    "messages": message_list,
                    "metadata": metadata_dict
                }
                
        except NoResultFound:
            raise
        except Exception as e:
            self.logger.error(f"Error getting session history for {session_id}: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def get_session_list(
        self,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """Get list of chat sessions"""
        try:
            async with database_manager.get_session() as db_session:
                # Build query
                query = select(ChatSession)
                
                if user_id:
                    query = query.where(ChatSession.user_id == user_id)
                
                if active_only:
                    query = query.where(ChatSession.is_active == True)
                
                # Order by updated_at (most recent first)
                query = query.order_by(ChatSession.updated_at.desc())
                
                # Apply pagination
                if limit:
                    query = query.limit(limit)
                if offset:
                    query = query.offset(offset)
                
                result = await db_session.execute(query)
                sessions = result.scalars().all()
                
                # Get total count
                count_query = select(func.count(ChatSession.id))
                if user_id:
                    count_query = count_query.where(ChatSession.user_id == user_id)
                if active_only:
                    count_query = count_query.where(ChatSession.is_active == True)
                
                count_result = await db_session.execute(count_query)
                total_count = count_result.scalar()
                
                return {
                    "sessions": [session.to_dict() for session in sessions],
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset
                }
                
        except Exception as e:
            self.logger.error(f"Error getting session list: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def update_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        is_active: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update a chat session"""
        try:
            async with database_manager.get_session() as db_session:
                session = await get_chat_session_async(db_session, session_id)
                if not session:
                    raise NoResultFound(f"Session {session_id} not found")
                
                # Update fields
                if title is not None:
                    session.title = title
                if is_active is not None:
                    session.is_active = is_active
                if metadata is not None:
                    session.metadata = metadata
                
                session.updated_at = datetime.utcnow()
                await db_session.commit()
                await db_session.refresh(session)
                
                self.logger.info(f"Updated session {session_id}")
                return session.to_dict()
                
        except NoResultFound:
            raise
        except Exception as e:
            self.logger.error(f"Error updating session {session_id}: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def delete_session(self, session_id: str) -> bool:
        """Delete a chat session"""
        try:
            async with database_manager.get_session() as db_session:
                success = await delete_chat_session_async(db_session, session_id)
                if success:
                    self.logger.info(f"Deleted session {session_id}")
                else:
                    self.logger.warning(f"Session {session_id} not found for deletion")
                return success
                
        except Exception as e:
            self.logger.error(f"Error deleting session {session_id}: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def delete_all_sessions(self) -> Dict[str, Any]:
        """Delete all chat sessions"""
        try:
            async with database_manager.get_session() as db_session:
                # Get total count before deletion
                count_query = select(func.count(ChatSession.id))
                count_result = await db_session.execute(count_query)
                total_count = count_result.scalar()
                
                # Delete all chat messages first
                delete_messages_query = delete(ChatMessage)
                await db_session.execute(delete_messages_query)
                
                # Delete all chat sessions
                delete_sessions_query = delete(ChatSession)
                await db_session.execute(delete_sessions_query)
                
                await db_session.commit()
                
                self.logger.info(f"Deleted all {total_count} chat sessions")
                return {
                    "deleted_sessions": total_count,
                    "message": f"Successfully deleted {total_count} chat sessions"
                }
                
        except Exception as e:
            self.logger.error(f"Error deleting all sessions: {str(e)}")
            raise
    
    async def search_sessions(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Dict[str, Any]:
        """Search chat sessions by content"""
        try:
            async with database_manager.get_session() as db_session:
                # Search in message content and session titles
                search_query = select(ChatSession).join(ChatMessage).where(
                    or_(
                        ChatSession.title.ilike(f"%{query}%"),
                        ChatMessage.content.ilike(f"%{query}%")
                    )
                )
                
                if user_id:
                    search_query = search_query.where(ChatSession.user_id == user_id)
                
                # Group by session to avoid duplicates
                search_query = search_query.group_by(ChatSession.id)
                search_query = search_query.order_by(ChatSession.updated_at.desc())
                
                # Apply pagination
                if limit:
                    search_query = search_query.limit(limit)
                if offset:
                    search_query = search_query.offset(offset)
                
                result = await db_session.execute(search_query)
                sessions = result.scalars().all()
                
                return {
                    "sessions": [session.to_dict() for session in sessions],
                    "query": query,
                    "total_count": len(sessions),
                    "limit": limit,
                    "offset": offset
                }
                
        except Exception as e:
            self.logger.error(f"Error searching sessions: {str(e)}")
            raise
    
      
    async def cleanup_old_sessions(self, days_old: int = 30) -> Dict[str, Any]:
        """Clean up old inactive sessions"""
        try:
            async with database_manager.get_session() as db_session:
                # Calculate cutoff date
                cutoff_date = datetime.utcnow() - timedelta(days=days_old)
                
                # Find old inactive sessions
                old_sessions_query = select(ChatSession).where(
                    and_(
                        ChatSession.is_active == False,
                        ChatSession.updated_at < cutoff_date
                    )
                )
                
                result = await db_session.execute(old_sessions_query)
                old_sessions = result.scalars().all()
                
                # Delete old sessions
                deleted_count = 0
                for session in old_sessions:
                    await db_session.delete(session)
                    deleted_count += 1
                
                await db_session.commit()
                
                self.logger.info(f"Cleaned up {deleted_count} old sessions")
                return {
                    "deleted_sessions": deleted_count,
                    "cutoff_date": cutoff_date.isoformat(),
                    "days_old": days_old
                }
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old sessions: {str(e)}")
            raise
    
    async def export_session_data(self, session_id: str, format: str = "json") -> Dict[str, Any]:
        """Export session data in various formats"""
        try:
            # Get session history
            session_data = await self.get_session_history(session_id)
            
            if format.lower() == "json":
                return session_data
            elif format.lower() == "csv":
                # Convert to CSV format
                csv_data = self._convert_to_csv(session_data)
                return {"format": "csv", "data": csv_data}
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            self.logger.error(f"Error exporting session data for {session_id}: {str(e)}")
            raise
    
    def _convert_to_csv(self, session_data: Dict[str, Any]) -> str:
        """Convert session data to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Timestamp", "Role", "Content", "Message Type"])
        
        # Write messages
        for message in session_data["messages"]:
            writer.writerow([
                message["timestamp"],
                message["role"],
                message["content"].replace("\n", " "),
                message["message_type"]
            ])
        
        return output.getvalue()


# Global chat history service instance
chat_history_service = ChatHistoryService()