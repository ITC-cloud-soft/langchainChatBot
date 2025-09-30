"""
User management API endpoints (single organization)

This module provides endpoints for managing users.
Admin users can manage all users.
Regular users can only view their own information.
"""

from typing import Annotated, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from api.core.database import get_db_session
from api.core.auth import PasswordManager
from api.middleware import CurrentUser, get_current_user, get_current_admin_user
from api.models.user import (
    User,
    UserRole,
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    create_user
)

router = APIRouter()


# Pydantic models
class UserCreateRequest(BaseModel):
    """Create user request model"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=255)
    role: str = Field("user", description="User role: admin or user")


class UserUpdateRequest(BaseModel):
    """Update user request model"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, description="User role: admin or user")
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response model"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: str
    updated_at: str
    last_login: Optional[str]


class UserListResponse(BaseModel):
    """List of users response"""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    user_data: UserCreateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_admin_user)],
    db: AsyncSession = Depends(get_db_session)
):
    """
    Create a new user
    
    Only admin users can create new users.
    """
    # Check if username already exists
    existing_user = await get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_data.username}' already exists"
        )
    
    # Check if email already exists
    existing_email = await get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{user_data.email}' already exists"
        )
    
    # Validate role
    if user_data.role not in ["admin", "user"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'admin' or 'user'"
        )
    
    # Hash password
    hashed_password = PasswordManager.hash_password(user_data.password)
    
    # Create user
    user = await create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=UserRole(user_data.role)
    )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value if hasattr(user.role, 'value') else user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None,
        updated_at=user.updated_at.isoformat() if user.updated_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None
    )


@router.get("/", response_model=UserListResponse)
async def list_users(
    current_user: Annotated[CurrentUser, Depends(get_current_admin_user)],
    db: AsyncSession = Depends(get_db_session),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    role_filter: Optional[str] = Query(None, description="Filter by role"),
    search: Optional[str] = Query(None, description="Search by username or email")
):
    """
    List all users
    
    Only admin users can list all users.
    """
    # Build query for all users
    query = select(User)
    
    # Apply filters
    if role_filter:
        query = query.where(User.role == role_filter)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (User.username.like(search_pattern)) | 
            (User.email.like(search_pattern)) |
            (User.full_name.like(search_pattern))
        )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(User.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()
    
    user_responses = [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value if hasattr(user.role, 'value') else user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else None,
            updated_at=user.updated_at.isoformat() if user.updated_at else None,
            last_login=user.last_login.isoformat() if user.last_login else None
        )
        for user in users
    ]
    
    return UserListResponse(
        users=user_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get user by ID
    
    Admin users can view any user.
    Regular users can only view their own information.
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Check permissions
    if not current_user.is_admin() and user.id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own user information"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value if hasattr(user.role, 'value') else user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None,
        updated_at=user.updated_at.isoformat() if user.updated_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_admin_user)],
    db: AsyncSession = Depends(get_db_session)
):
    """
    Update user information
    
    Only admin users can update users.
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Update fields
    if user_data.email is not None:
        # Check if email already exists for another user
        existing_email = await get_user_by_email(db, user_data.email)
        if existing_email and existing_email.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{user_data.email}' already exists"
            )
        user.email = user_data.email
    
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    
    if user_data.role is not None:
        if user_data.role not in ["admin", "user"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be 'admin' or 'user'"
            )
        user.role = UserRole(user_data.role)
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    user.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value if hasattr(user.role, 'value') else user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None,
        updated_at=user.updated_at.isoformat() if user.updated_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_admin_user)],
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a user
    
    Only admin users can delete users.
    Cannot delete yourself.
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Prevent deleting yourself
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own user account"
        )
    
    await db.delete(user)
    await db.commit()
    
    return None
