"""
通知モデル - データベーステーブル定義
"""
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from api.models.base import Base


class NotificationStatus(enum.StrEnum):
    """通知ステータス"""
    PENDING = "pending"  # 作成済み、未送信
    SENT = "sent"        # 送信済み
    READ = "read"        # 既読


class Notification(Base):
    """通知テーブル"""
    __tablename__ = "notifications"
    
    # 主キー
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 関連ID
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    chatbot_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    connection_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Novu関連
    novu_notification_id = Column(String(255), unique=True, nullable=True, index=True)
    novu_subscriber_id = Column(String(255), nullable=True, index=True)
    
    # ユーザー情報
    sender_id = Column(UUID(as_uuid=True), nullable=True)
    receiver_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # 通知内容
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    category = Column(String(50), nullable=True, index=True)
    payload = Column(JSON, nullable=True)
    
    # ステータス
    status = Column(
        SQLEnum(NotificationStatus),
        default=NotificationStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # タイムスタンプ
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Notification(id={self.id}, title={self.title}, status={self.status})>"
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "chatbot_id": str(self.chatbot_id) if self.chatbot_id else None,
            "connection_id": str(self.connection_id) if self.connection_id else None,
            "novu_notification_id": self.novu_notification_id,
            "novu_subscriber_id": self.novu_subscriber_id,
            "sender_id": str(self.sender_id) if self.sender_id else None,
            "receiver_id": str(self.receiver_id),
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "payload": self.payload,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
    
    def mark_sent(self):
        """送信済みとしてマーク"""
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.utcnow()
    
    def mark_read(self):
        """既読としてマーク"""
        self.status = NotificationStatus.READ
        self.read_at = datetime.utcnow()
    
    def is_read(self) -> bool:
        """既読かどうか"""
        return self.status == NotificationStatus.READ
    
    def is_deleted(self) -> bool:
        """削除済みかどうか"""
        return self.deleted_at is not None


class NotificationSyncLog(Base):
    """通知同期ログテーブル"""
    __tablename__ = "notification_sync_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    novu_notification_id = Column(String(255), nullable=False, index=True)
    local_notification_id = Column(UUID(as_uuid=True), nullable=True)
    sync_direction = Column(String(20), nullable=False)  # 'to_novu' or 'from_novu'
    sync_status = Column(String(20), nullable=False, index=True)  # 'success' or 'failed'
    error_message = Column(Text, nullable=True)
    synced_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<NotificationSyncLog(id={self.id}, status={self.sync_status})>"
