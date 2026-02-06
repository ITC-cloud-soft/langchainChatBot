"""
SSFlow連携用の内部APIエンドポイント
認証不要で、SSFlowからのユーザー同期リクエストを処理する
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional

from api.database import get_db_session
from api.models.user import (
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    create_user,
    User
)
from api.utils.security import get_password_hash

router = APIRouter()


class InternalUserCheckResponse(BaseModel):
    """ユーザー存在確認レスポンス"""
    exists: bool
    user_id: Optional[int] = None
    username: Optional[str] = None


class InternalUserCreateRequest(BaseModel):
    """内部API用ユーザー作成リクエスト"""
    username: str
    email: EmailStr
    full_name: str
    password: str
    role: str = "user"


class InternalUserUpdateRequest(BaseModel):
    """内部API用ユーザー更新リクエスト"""
    email: EmailStr
    full_name: str


class InternalUserResponse(BaseModel):
    """内部API用ユーザーレスポンス"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/check", response_model=InternalUserCheckResponse)
async def check_user_exists(
    username: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    ユーザーが存在するか確認する（認証不要）
    
    Args:
        username: 確認するユーザー名
        db: データベースセッション
        
    Returns:
        ユーザー存在確認結果
    """
    user = await get_user_by_username(db, username)
    
    if user:
        return InternalUserCheckResponse(
            exists=True,
            user_id=user.id,
            username=user.username
        )
    
    return InternalUserCheckResponse(exists=False)


@router.post("/", response_model=InternalUserResponse, status_code=status.HTTP_201_CREATED)
async def create_internal_user(
    user_data: InternalUserCreateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    新規ユーザーを作成する（認証不要）
    SSFlowからの同期リクエスト用
    
    Args:
        user_data: ユーザー作成データ
        db: データベースセッション
        
    Returns:
        作成されたユーザー情報
        
    Raises:
        HTTPException: ユーザー名またはメールアドレスが既に存在する場合
    """
    # ユーザー名の重複チェック
    existing_user = await get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_data.username}' already exists"
        )
    
    # メールアドレスの重複チェック
    existing_email = await get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{user_data.email}' already exists"
        )
    
    # パスワードのハッシュ化
    hashed_password = get_password_hash(user_data.password)
    
    # ユーザー作成
    new_user = await create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    return InternalUserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role.value,
        is_active=new_user.is_active
    )


@router.put("/{username}", response_model=InternalUserResponse)
async def update_internal_user(
    username: str,
    user_data: InternalUserUpdateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    既存ユーザーの情報を更新する（認証不要）
    SSFlowからの同期リクエスト用
    
    Args:
        username: 更新するユーザー名
        user_data: 更新データ
        db: データベースセッション
        
    Returns:
        更新されたユーザー情報
        
    Raises:
        HTTPException: ユーザーが存在しない場合
    """
    # ユーザーの存在確認
    user = await get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )
    
    # メールアドレスの重複チェック（自分以外）
    if user.email != user_data.email:
        existing_email = await get_user_by_email(db, user_data.email)
        if existing_email and existing_email.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{user_data.email}' already exists"
            )
    
    # ユーザー情報を更新
    user.email = user_data.email
    user.full_name = user_data.full_name
    
    await db.commit()
    await db.refresh(user)
    
    return InternalUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active
    )


@router.get("/{username}", response_model=InternalUserResponse)
async def get_internal_user(
    username: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    ユーザー情報を取得する（認証不要）
    
    Args:
        username: 取得するユーザー名
        db: データベースセッション
        
    Returns:
        ユーザー情報
        
    Raises:
        HTTPException: ユーザーが存在しない場合
    """
    user = await get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )
    
    return InternalUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active
    )
