"""
通知コントローラー - REST APIエンドポイント
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.adapters.novu_adapter import NovuAdapter
from api.services.notification_service import NotificationService
from api.dependencies import get_db, get_current_user, get_novu_adapter
from api.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
    SendWorkflowApprovalRequest,
    SendSystemNotificationRequest,
    MarkReadRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def get_notification_service(
    db: Session = Depends(get_db),
    novu: NovuAdapter = Depends(get_novu_adapter)
) -> NotificationService:
    """通知サービスの依存性注入"""
    return NotificationService(novu_adapter=novu, db_session=db)


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(False, description="未読のみ取得"),
    page: int = Query(0, ge=0, description="ページ番号"),
    limit: int = Query(10, ge=1, le=100, description="1ページあたりの件数"),
    current_user = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    通知リストを取得
    
    - **unread_only**: 未読のみ取得する場合はtrue
    - **page**: ページ番号 (0から開始)
    - **limit**: 1ページあたりの件数 (1-100)
    """
    try:
        result = service.list_notifications(
            user_id=current_user.id,
            unread_only=unread_only,
            page=page,
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"Failed to list notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="通知リストの取得に失敗しました")


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    未読通知数を取得
    """
    try:
        count = service.get_unread_count(user_id=current_user.id)
        return {"unread": count}
    except Exception as e:
        logger.error(f"Failed to get unread count: {str(e)}")
        raise HTTPException(status_code=500, detail="未読数の取得に失敗しました")


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    通知を既読としてマーク
    
    - **notification_id**: Novu通知ID (message ID)
    """
    try:
        success = service.mark_as_read(
            user_id=current_user.id,
            notification_id=notification_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="通知が見つかりません")
        return {"result": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark as read: {str(e)}")
        raise HTTPException(status_code=500, detail="既読マークに失敗しました")


@router.post("/{notification_id}/seen")
async def mark_as_seen(
    notification_id: str,
    current_user = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    通知を既読としてマーク (seen)
    
    - **notification_id**: Novu通知ID (message ID)
    """
    try:
        success = service.mark_as_seen(
            user_id=current_user.id,
            notification_id=notification_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="通知が見つかりません")
        return {"result": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark as seen: {str(e)}")
        raise HTTPException(status_code=500, detail="既読マークに失敗しました")


@router.post("/mark-all-read")
async def mark_all_as_read(
    current_user = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    全通知を既読としてマーク
    """
    try:
        success = service.mark_all_as_read(user_id=current_user.id)
        if not success:
            raise HTTPException(status_code=500, detail="一括既読マークに失敗しました")
        return {"result": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark all as read: {str(e)}")
        raise HTTPException(status_code=500, detail="一括既読マークに失敗しました")


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    通知を削除
    
    - **notification_id**: Novu通知ID (message ID)
    """
    try:
        success = service.delete_notification(
            user_id=current_user.id,
            notification_id=notification_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="通知が見つかりません")
        return {"result": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete notification: {str(e)}")
        raise HTTPException(status_code=500, detail="通知の削除に失敗しました")


@router.post("/send/workflow-approval", response_model=NotificationResponse)
async def send_workflow_approval(
    request: SendWorkflowApprovalRequest,
    current_user = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    ワークフロー承認通知を送信
    
    - **receiver_id**: 受信者ID
    - **workflow_data**: ワークフローデータ
    """
    try:
        notification = service.send_workflow_approval(
            receiver_id=request.receiver_id,
            workflow_data=request.workflow_data,
            sender_id=current_user.id,
            tenant_id=request.tenant_id,
            chatbot_id=request.chatbot_id
        )
        return notification.to_dict()
    except Exception as e:
        logger.error(f"Failed to send workflow approval: {str(e)}")
        raise HTTPException(status_code=500, detail="ワークフロー承認通知の送信に失敗しました")


@router.post("/send/system", response_model=NotificationResponse)
async def send_system_notification(
    request: SendSystemNotificationRequest,
    current_user = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    システム通知を送信
    
    - **receiver_id**: 受信者ID
    - **title**: タイトル
    - **content**: 内容
    - **category**: カテゴリ (オプション)
    - **payload**: カスタムペイロード (オプション)
    """
    try:
        notification = service.send_system_notification(
            receiver_id=request.receiver_id,
            title=request.title,
            content=request.content,
            category=request.category,
            payload=request.payload,
            tenant_id=request.tenant_id
        )
        return notification.to_dict()
    except Exception as e:
        logger.error(f"Failed to send system notification: {str(e)}")
        raise HTTPException(status_code=500, detail="システム通知の送信に失敗しました")


@router.post("/sync-subscriber")
async def sync_subscriber(
    current_user = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    """
    現在のユーザーをNovu購読者として同期
    """
    try:
        success = service.sync_subscriber(
            user_id=current_user.id,
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            avatar=current_user.avatar
        )
        if not success:
            raise HTTPException(status_code=500, detail="購読者の同期に失敗しました")
        return {"result": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync subscriber: {str(e)}")
        raise HTTPException(status_code=500, detail="購読者の同期に失敗しました")
