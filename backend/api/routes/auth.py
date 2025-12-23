"""
Authentication API endpoints

This module provides authentication endpoints for:
- User login
- Token refresh
- User registration (if enabled)
- Password reset
"""

from typing import Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db_session
from api.core.auth import (
    PasswordManager,
    TokenManager,
    verify_password
)
from api.models.user import (
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    create_user,
    User,
    UserRole
)
from api.middleware import CurrentUser, get_current_user

router = APIRouter()


# Pydantic models
class LoginRequest(BaseModel):
    """Login request model"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class TokenRefreshRequest(BaseModel):
    """Token refresh request model"""
    refresh_token: str = Field(..., description="Refresh token")


class TokenRefreshResponse(BaseModel):
    """Token refresh response model"""
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    """Change password request model"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class UserMeResponse(BaseModel):
    """Current user information response"""
    user_id: int
    username: str
    email: str
    full_name: str | None
    role: str
    is_active: bool
    created_at: str
    last_login: str | None


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    User login endpoint
    
    Authenticates user with username/email and password,
    returns access and refresh tokens
    """
    import logging
    logger = logging.getLogger("chatbot_app")
    
    try:
        logger.info(f"Login attempt for user: {login_data.username}")
        
        # Try to find user by username or email
        logger.info("Querying user by username...")
        user = await get_user_by_username(db, login_data.username)
        if not user:
            logger.info("User not found by username, trying email...")
            user = await get_user_by_email(db, login_data.username)
        
        if not user:
            logger.warning(f"User not found: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        logger.info(f"User found: {user.username}, verifying password...")
        
        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            logger.warning(f"Invalid password for user: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        logger.info("Password verified successfully")
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Inactive user attempted login: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )
    
    # Update last login time
    user.last_login = datetime.now()
    await db.commit()
    
    # Generate tokens
    role_value = user.role.value if hasattr(user.role, 'value') else user.role
    tokens = TokenManager.create_token_pair(
        user_id=user.id,
        role=role_value
    )
    
    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        user={
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": role_value
        }
    )


@router.post("/token", response_model=LoginResponse)
async def login_oauth2(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db_session)
):
    """
    OAuth2 compatible token endpoint
    
    Same as /login but follows OAuth2 password flow specification
    """
    # Try to find user by username
    user = await get_user_by_username(db, form_data.username)
    
    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last login time
    user.last_login = datetime.now()
    await db.commit()
    
    # Generate tokens
    role_value = user.role.value if hasattr(user.role, 'value') else user.role
    tokens = TokenManager.create_token_pair(
        user_id=user.id,
        role=role_value
    )
    
    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        user={
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": role_value
        }
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    refresh_data: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Refresh access token using refresh token
    """
    try:
        # Decode refresh token
        payload = TokenManager.decode_token(refresh_data.refresh_token)
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Extract user info
        user_id = int(payload.get("sub"))
        role = payload.get("role")
        
        # Create new access token
        new_access_token = TokenManager.create_access_token({
            "sub": str(user_id),
            "role": role
        })
        
        return TokenRefreshResponse(
            access_token=new_access_token,
            token_type="bearer"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me", response_model=UserMeResponse)
async def get_current_user_info(
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
):
    """
    Get current user information
    """
    return UserMeResponse(
        user_id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=True,
        created_at=datetime.now().isoformat(),
        last_login=None
    )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session)
):
    """
    Change user password
    """
    
    # Get user from database
    user = await get_user_by_id(db, current_user.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Hash and update new password
    user.hashed_password = PasswordManager.hash_password(password_data.new_password)
    user.updated_at = datetime.now()
    
    await db.commit()
    
    return {"message": "Password changed successfully"}


# アカウント申請機能は削除されました
# スーパーユーザーのみがユーザーと管理者を追加できます


@router.post("/logout")
async def logout(
    current_user: Annotated[CurrentUser, Depends(get_current_user)]
):
    """
    User logout endpoint
    
    Note: JWT tokens are stateless, so logout is handled client-side
    by removing the token. This endpoint is provided for consistency
    and can be extended to implement token blacklisting if needed.
    """
    return {
        "message": "Logged out successfully",
        "note": "Please remove the access token from client storage"
    }
