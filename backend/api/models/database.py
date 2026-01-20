"""
Database models for chat history storage

This module defines SQLAlchemy models for storing chat sessions, messages,
and metadata in MySQL database.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, select
from sqlalchemy.orm import relationship, Session
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.mysql import TEXT, LONGTEXT
from sqlalchemy.ext.asyncio import AsyncSession

Base = declarative_base()


class ChatSession(Base):
    """
    Chat session model representing a conversation session (single organization)
    """
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id_int = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=True)
    user_id = Column(String(255), nullable=True, index=True)  # Legacy field, kept for compatibility
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    session_metadata = Column("metadata", JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions", foreign_keys=[user_id_int])
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatSession(session_id='{self.session_id}', created_at='{self.created_at}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id_int": self.user_id_int,
            "session_id": self.session_id,
            "title": self.title,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
            "metadata": self.session_metadata
        }


class ChatMessage(Base):
    """
    Chat message model representing individual messages in a conversation (single organization)
    """
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(255), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String(255), unique=True, index=True, nullable=False)
    role = Column(String(50), nullable=False, index=True)  # 'user', 'assistant', 'system'
    content = Column(LONGTEXT, nullable=False)
    message_type = Column(String(50), default="text", nullable=False)  # 'text', 'file', 'error'
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    source_documents = Column(JSON, nullable=True)  # List of source documents
    error_info = Column(JSON, nullable=True)  # Error information if message failed
    message_metadata = Column("metadata", JSON, nullable=True)
    
    # Relationship with session
    session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(message_id='{self.message_id}', role='{self.role}', session_id='{self.session_id}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "message_id": self.message_id,
            "role": self.role,
            "content": self.content,
            "message_type": self.message_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source_documents": self.source_documents,
            "error_info": self.error_info,
            "metadata": self.message_metadata
        }


class ChatMetadata(Base):
    """
    Chat metadata model for storing additional session metadata
    """
    __tablename__ = "chat_metadata"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(255), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False, unique=True)
    total_messages = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=True)
    last_user_message = Column(String(255), nullable=True)
    last_assistant_message = Column(String(255), nullable=True)
    model_used = Column(String(100), nullable=True)
    language = Column(String(10), default="ja", nullable=False)
    tags = Column(JSON, nullable=True)  # List of tags for categorization
    custom_fields = Column(JSON, nullable=True)  # Custom user-defined fields
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    # Relationship with session
    session = relationship("ChatSession", foreign_keys=[session_id])
    
    def __repr__(self):
        return f"<ChatMetadata(session_id='{self.session_id}', total_messages={self.total_messages})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "total_messages": self.total_messages,
            "total_tokens": self.total_tokens,
            "last_user_message": self.last_user_message,
            "last_assistant_message": self.last_assistant_message,
            "model_used": self.model_used,
            "language": self.language,
            "tags": self.tags,
            "custom_fields": self.custom_fields,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ChatHistoryStats(Base):
    """
    Chat statistics model for aggregating chat data
    """
    __tablename__ = "chat_history_stats"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(String(10), unique=True, nullable=False, index=True)  # YYYY-MM-DD format
    total_sessions = Column(Integer, default=0, nullable=False)
    total_messages = Column(Integer, default=0, nullable=False)
    total_users = Column(Integer, default=0, nullable=False)
    avg_session_length = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
    def __repr__(self):
        return f"<ChatHistoryStats(date='{self.date}', total_sessions={self.total_sessions})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "date": self.date,
            "total_sessions": self.total_sessions,
            "total_messages": self.total_messages,
            "total_users": self.total_users,
            "avg_session_length": self.avg_session_length,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Database utility functions
def create_chat_session(
    db: Session, 
    session_id: str, 
    title: Optional[str] = None, 
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ChatSession:
    """Create a new chat session"""
    session = ChatSession(
        session_id=session_id,
        title=title,
        user_id=user_id,
        metadata=metadata or {}
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Create metadata record
    chat_metadata = ChatMetadata(
        session_id=session_id,
        total_messages=0,
        language="ja"
    )
    db.add(chat_metadata)
    db.commit()
    
    return session


def add_chat_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    message_id: Optional[str] = None,
    message_type: str = "text",
    source_documents: Optional[list] = None,
    error_info: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ChatMessage:
    """Add a new chat message"""
    import uuid
    
    if not message_id:
        message_id = str(uuid.uuid4())
    
    message = ChatMessage(
        session_id=session_id,
        message_id=message_id,
        role=role,
        content=content,
        message_type=message_type,
        source_documents=source_documents,
        error_info=error_info,
        metadata=metadata or {}
    )
    db.add(message)
    
    # Update session metadata
    chat_meta = db.query(ChatMetadata).filter(ChatMetadata.session_id == session_id).first()
    if chat_meta:
        chat_meta.total_messages += 1
        chat_meta.updated_at = datetime.now()
        
        if role == "user":
            chat_meta.last_user_message = content[:255]
        elif role == "assistant":
            chat_meta.last_assistant_message = content[:255]
        
        # Update session updated_at
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if session:
            session.updated_at = datetime.now()
    
    db.commit()
    db.refresh(message)
    return message


def get_chat_session(db: Session, session_id: str) -> Optional[ChatSession]:
    """Get chat session by session_id"""
    return db.query(ChatSession).filter(ChatSession.session_id == session_id).first()


def get_chat_messages(
    db: Session, 
    session_id: str, 
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> list[ChatMessage]:
    """Get chat messages for a session"""
    query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp.asc())
    
    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    
    return query.all()


def get_chat_metadata(db: Session, session_id: str) -> Optional[ChatMetadata]:
    """Get chat metadata by session_id"""
    return db.query(ChatMetadata).filter(ChatMetadata.session_id == session_id).first()


def delete_chat_session(db: Session, session_id: str) -> bool:
    """Delete a chat session and all related data"""
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if session:
        db.delete(session)
        db.commit()
        return True
    return False


def get_active_sessions(db: Session, limit: Optional[int] = None) -> list[ChatSession]:
    """Get active chat sessions"""
    query = db.query(ChatSession).filter(ChatSession.is_active == True).order_by(ChatSession.updated_at.desc())
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


# Async versions of database functions
async def get_chat_session_async(db: AsyncSession, session_id: str) -> Optional[ChatSession]:
    """Get chat session by session_id (async version)"""
    result = await db.execute(select(ChatSession).where(ChatSession.session_id == session_id))
    return result.scalar_one_or_none()


async def get_chat_messages_async(
    db: AsyncSession, 
    session_id: str, 
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> list[ChatMessage]:
    """Get chat messages for a session (async version)"""
    query = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp.asc())
    
    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_chat_metadata_async(db: AsyncSession, session_id: str) -> Optional[ChatMetadata]:
    """Get chat metadata by session_id (async version)"""
    result = await db.execute(select(ChatMetadata).where(ChatMetadata.session_id == session_id))
    return result.scalar_one_or_none()


async def delete_chat_session_async(db: AsyncSession, session_id: str) -> bool:
    """Delete a chat session and all related data (async version)"""
    result = await db.execute(select(ChatSession).where(ChatSession.session_id == session_id))
    session = result.scalar_one_or_none()
    if session:
        await db.delete(session)
        await db.commit()
        return True
    return False


async def get_active_sessions_async(db: AsyncSession, limit: Optional[int] = None) -> list[ChatSession]:
    """Get active chat sessions (async version)"""
    query = select(ChatSession).where(ChatSession.is_active == True).order_by(ChatSession.updated_at.desc())
    
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def create_chat_session_async(
    db: AsyncSession, 
    session_id: str, 
    title: Optional[str] = None, 
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ChatSession:
    """Create a new chat session (async version)"""
    session = ChatSession(
        session_id=session_id,
        title=title,
        user_id=user_id,
        session_metadata=metadata or {}
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    # Create metadata record
    chat_metadata = ChatMetadata(
        session_id=session_id,
        total_messages=0,
        language="ja"
    )
    db.add(chat_metadata)
    await db.commit()
    
    return session


async def add_chat_message_async(
    db: AsyncSession,
    session_id: str,
    role: str,
    content: str,
    message_id: Optional[str] = None,
    message_type: str = "text",
    source_documents: Optional[list] = None,
    error_info: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ChatMessage:
    """Add a new chat message (async version)"""
    import uuid
    
    if not message_id:
        message_id = str(uuid.uuid4())
    
    message = ChatMessage(
        session_id=session_id,
        message_id=message_id,
        role=role,
        content=content,
        message_type=message_type,
        source_documents=source_documents,
        error_info=error_info,
        message_metadata=metadata or {}
    )
    db.add(message)
    
    # Update session metadata
    metadata_result = await db.execute(
        select(ChatMetadata).where(ChatMetadata.session_id == session_id)
    )
    chat_meta = metadata_result.scalar_one_or_none()
    if chat_meta:
        chat_meta.total_messages += 1
        chat_meta.updated_at = datetime.now()
        
        if role == "user":
            chat_meta.last_user_message = content[:255]
        elif role == "assistant":
            chat_meta.last_assistant_message = content[:255]
    
    # Update session timestamp
    update_session = await db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id)
    )
    session = update_session.scalar_one_or_none()
    if session:
        session.updated_at = datetime.now()
    
    await db.commit()
    await db.refresh(message)
    return message


async def update_message_form_status_async(
    db: AsyncSession,
    message_id: str,
    form_status: str,
    form_data: Optional[Dict[str, Any]] = None,
    execution_result: Optional[Dict[str, Any]] = None
) -> Optional[ChatMessage]:
    """
    メッセージの表単状態を更新
    
    Args:
        db: データベースセッション
        message_id: メッセージID
        form_status: 表単状態 (pending/submitted/cancelled/completed/error)
        form_data: 表単データ
        execution_result: 実行結果（完了時）
        
    Returns:
        更新されたChatMessageオブジェクト
    """
    from api.core.utils import default_logger
    logger = default_logger
    
    logger.info(f"[DB UPDATE] Attempting to update message {message_id} to status {form_status}")
    
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.message_id == message_id)
    )
    message = result.scalar_one_or_none()
    
    if message:
        logger.info(f"[DB UPDATE] Found message {message_id}, current metadata: {message.message_metadata}")
        
        # 既存のmetadataをコピーして新しいdictを作成（SQLAlchemyの変更検知のため）
        metadata = dict(message.message_metadata or {})
        metadata['form_status'] = form_status
        
        if form_data is not None:
            metadata['form_data'] = form_data
        
        if form_status == 'submitted':
            metadata['submitted_at'] = datetime.now().isoformat()
        elif form_status == 'cancelled':
            metadata['cancelled_at'] = datetime.now().isoformat()
        elif form_status in ['completed', 'error']:
            metadata['completed_at'] = datetime.now().isoformat()
            if execution_result:
                metadata['execution_result'] = execution_result
        
        # SQLAlchemyのJSON型フィールドの変更を明示的にマーク
        from sqlalchemy.orm.attributes import flag_modified
        message.message_metadata = metadata
        flag_modified(message, "message_metadata")
        
        await db.commit()
        await db.refresh(message)
        
        logger.info(f"[DB UPDATE] Successfully updated message {message_id}, new metadata: {message.message_metadata}")
    else:
        logger.warning(f"[DB UPDATE] Message {message_id} not found in database")
    
    return message


async def get_message_by_id_async(
    db: AsyncSession,
    message_id: str
) -> Optional[ChatMessage]:
    """
    メッセージIDでメッセージを取得
    
    Args:
        db: データベースセッション
        message_id: メッセージID
        
    Returns:
        ChatMessageオブジェクト
    """
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.message_id == message_id)
    )
    return result.scalar_one_or_none()