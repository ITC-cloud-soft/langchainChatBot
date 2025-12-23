"""
User database models for single organization

This module defines SQLAlchemy models for user management:
- Users (with role-based access control)
- No multi-tenant support - single organization only
- All settings managed in config.toml
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship, Session
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.mysql import TEXT, LONGTEXT
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Use the same Base as the existing models
from api.models.database import Base


class UserRole(str, PyEnum):
    """User role enumeration"""
    ADMIN = "admin"      # Can manage settings and users
    USER = "user"        # Can only use chat features


class User(Base):
    """
    User model with role-based access control
    Single organization - no tenant support
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    last_login = Column(DateTime, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user", foreign_keys="ChatSession.user_id_int")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    def to_dict(self, include_password: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value if isinstance(self.role, PyEnum) else self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "extra_metadata": self.extra_metadata
        }
        if include_password:
            data["hashed_password"] = self.hashed_password
        return data


# Utility functions for user operations


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get user by username"""
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email"""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    hashed_password: str,
    full_name: Optional[str] = None,
    role: UserRole = UserRole.USER,
    extra_metadata: Optional[Dict[str, Any]] = None
) -> User:
    """Create a new user"""
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        role=role,
        extra_metadata=extra_metadata or {}
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
