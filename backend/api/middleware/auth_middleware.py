"""
Authentication middleware for single organization

This module provides FastAPI dependencies for:
- JWT token validation
- Current user extraction
- Role-based access control
- No multi-tenant support
"""

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db_session
from api.core.auth import TokenManager, AuthorizationManager
from api.models.user import User, get_user_by_id

# HTTP Bearer token scheme
security = HTTPBearer()


class CurrentUser:
    """Current authenticated user context (single organization)"""
    
    def __init__(
        self,
        user_id: int,
        username: str,
        email: str,
        role: str,
        full_name: Optional[str] = None
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.role = role
        self.full_name = full_name
    
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return AuthorizationManager.is_admin(self.role)
    
    def can_manage_settings(self) -> bool:
        """Check if current user can manage settings"""
        return AuthorizationManager.is_admin(self.role)
    
    def require_admin(self) -> None:
        """Raise exception if user is not admin"""
        AuthorizationManager.require_admin(self.role)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "full_name": self.full_name
        }


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db_session)
) -> CurrentUser:
    """
    Extract and validate current user from JWT token
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        CurrentUser object with user information
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    import logging
    logger = logging.getLogger("chatbot_app")
    
    token = credentials.credentials
    logger.info(f"[Auth] Received token: {token[:20]}...")
    
    # Decode token
    try:
        payload = TokenManager.decode_token(token)
        logger.info(f"[Auth] Token decoded successfully. Payload: {payload}")
    except HTTPException as e:
        logger.error(f"[Auth] Token decode failed: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user info from token
    user_id: Optional[int] = None
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    role: str = payload.get("role")
    
    if not user_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database to ensure they still exist and are active
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create CurrentUser context
    role_value = user.role.value if hasattr(user.role, 'value') else user.role
    logger.info(f"[Auth] Creating CurrentUser: username={user.username}, role_from_db={user.role}, role_value={role_value}")
    
    current_user = CurrentUser(
        user_id=user.id,
        username=user.username,
        email=user.email,
        role=role_value,
        full_name=user.full_name
    )
    
    logger.info(f"[Auth] CurrentUser created: role={current_user.role}, is_admin={current_user.is_admin()}")
    return current_user


async def get_current_active_user(
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
) -> CurrentUser:
    """
    Get current active user (convenience wrapper)
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        CurrentUser object
    """
    return current_user


async def get_current_admin_user(
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
) -> CurrentUser:
    """
    Get current user and verify admin role
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        CurrentUser object
        
    Raises:
        HTTPException: If user is not admin
    """
    import logging
    logger = logging.getLogger("chatbot_app")
    logger.info(f"[Admin Check] User: {current_user.username}, Role: {current_user.role}, Is Admin: {current_user.is_admin()}")
    
    current_user.require_admin()
    return current_user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session)
) -> Optional[CurrentUser]:
    """
    Get current user if authenticated, None otherwise
    Useful for endpoints that work both with and without authentication
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        CurrentUser object if authenticated, None otherwise
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    
    try:
        payload = TokenManager.decode_token(token)
        user_id = int(payload.get("sub"))
        
        user = await get_user_by_id(db, user_id)
        if not user or not user.is_active:
            return None
        
        return CurrentUser(
            user_id=user.id,
            username=user.username,
            email=user.email,
            role=user.role.value if hasattr(user.role, 'value') else user.role,
            full_name=user.full_name
        )
    except Exception:
        return None


# Tenant context removed - single organization only
