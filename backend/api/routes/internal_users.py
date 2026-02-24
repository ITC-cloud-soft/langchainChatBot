"""
SSFlow連携用の内部APIエンドポイント
認証不要で、SSFlowからのユーザー同期リクエストを処理する
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional

from api.core.database import get_db_session
from api.core.auth import PasswordManager
from api.models.user import (
    get_user_by_username,
    get_user_by_email,
    get_user_by_id,
    create_user,
    User,
    UserRole
)

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
    role: UserRole = UserRole.USER


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
    ソフトデリート済みユーザーは exists=false として返す（POST で upsert させるため）
    
    Args:
        username: 確認するユーザー名
        db: データベースセッション
        
    Returns:
        ユーザー存在確認結果
    """
    user = await get_user_by_username(db, username)
    
    # アクティブなユーザーのみ exists=true とする
    if user and user.is_active:
        return InternalUserCheckResponse(
            exists=True,
            user_id=user.id,
            username=user.username
        )
    
    return InternalUserCheckResponse(exists=False)


@router.post("/", response_model=InternalUserResponse)
async def create_internal_user(
    user_data: InternalUserCreateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    ユーザーを作成または復元・更新する（認証不要・upsert方式）
    SSFlowからの同期リクエスト用
    
    - ユーザーが存在しない場合: 新規作成（HTTP 201）
    - ユーザーが存在する場合（ソフトデリート含む）: is_active を復元し
      email / full_name を最新値で更新（HTTP 200）
    
    Args:
        user_data: ユーザー作成データ
        db: データベースセッション
        
    Returns:
        作成または更新されたユーザー情報
    """
    from fastapi.responses import JSONResponse
    from datetime import datetime

    # ユーザー名で既存ユーザーを検索（ソフトデリート含む）
    existing_user = await get_user_by_username(db, user_data.username)

    if existing_user:
        # --- 既存ユーザー（ソフトデリート含む）: 復元 + 情報更新 ---
        changed = False

        if not existing_user.is_active:
            existing_user.is_active = True
            changed = True

        if existing_user.email != str(user_data.email):
            # メールアドレス変更時は他ユーザーとの重複チェック
            conflict = await get_user_by_email(db, user_data.email)
            if conflict and conflict.id != existing_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{user_data.email}' is already used by another user"
                )
            existing_user.email = str(user_data.email)
            changed = True

        if existing_user.full_name != user_data.full_name:
            existing_user.full_name = user_data.full_name
            changed = True

        if changed:
            existing_user.updated_at = datetime.now()
            await db.commit()
            await db.refresh(existing_user)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": existing_user.id,
                "username": existing_user.username,
                "email": existing_user.email,
                "full_name": existing_user.full_name,
                "role": existing_user.role.value if hasattr(existing_user.role, "value") else existing_user.role,
                "is_active": existing_user.is_active,
            }
        )

    # --- 新規ユーザー作成 ---
    # メールアドレスの重複チェック（同一emailが既存ユーザーに紐付いている場合はスキップして成功扱い）
    existing_email = await get_user_by_email(db, user_data.email)
    if existing_email:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": existing_email.id,
                "username": user_data.username,
                "email": existing_email.email,
                "full_name": user_data.full_name,
                "role": existing_email.role.value if hasattr(existing_email.role, "value") else existing_email.role,
                "is_active": existing_email.is_active,
            }
        )

    # パスワードのハッシュ化
    hashed_password = PasswordManager.hash_password(user_data.password)

    # ユーザー作成
    new_user = await create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role if isinstance(user_data.role, UserRole) else UserRole(user_data.role)
    )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role.value if hasattr(new_user.role, "value") else new_user.role,
            "is_active": new_user.is_active,
        }
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
