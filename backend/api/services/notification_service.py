"""
通知サービス - Novuアダプターとローカルデータベースを統合
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from api.adapters.novu_adapter import NovuAdapter
from api.models.notification import Notification, NotificationStatus

logger = logging.getLogger(__name__)


class NotificationService:
    """通知サービス - ビジネスロジック層"""
    
    def __init__(self, novu_adapter: NovuAdapter, db_session: Session):
        """
        通知サービスの初期化
        
        Args:
            novu_adapter: Novuアダプター
            db_session: データベースセッション
        """
        self.novu = novu_adapter
        self.db = db_session
    
    def send_workflow_approval(
        self,
        receiver_id: str,
        workflow_data: Dict[str, Any],
        sender_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        chatbot_id: Optional[str] = None
    ) -> Notification:
        """
        ワークフロー承認通知を送信
        
        Args:
            receiver_id: 受信者ID
            workflow_data: ワークフローデータ
            sender_id: 送信者ID
            tenant_id: テナントID
            chatbot_id: チャットボットID
            
        Returns:
            作成された通知オブジェクト
        """
        try:
            # 1. Novu購読者を作成/更新
            self.novu.create_subscriber(
                subscriber_id=receiver_id,
                data={"tenant_id": tenant_id, "chatbot_id": chatbot_id}
            )
            
            # 2. ペイロードを構築
            payload = self._build_approval_payload(workflow_data)
            
            # 3. ローカルデータベースに記録を作成
            notification = Notification(
                tenant_id=tenant_id,
                chatbot_id=chatbot_id,
                sender_id=sender_id,
                receiver_id=receiver_id,
                title=payload["title"],
                content=payload["content"],
                category="workflow_request",
                payload=payload,
                status=NotificationStatus.PENDING
            )
            self.db.add(notification)
            self.db.flush()
            
            # 4. Novuワークフローをトリガー
            novu_notification_id = self.novu.trigger_workflow(
                workflow_id="workflow-approval",
                subscriber_id=receiver_id,
                payload=payload,
                tenant=tenant_id
            )
            
            # 5. Novu通知IDを保存
            notification.novu_notification_id = novu_notification_id
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Workflow approval notification sent: {notification.id}")
            return notification
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to send workflow approval notification: {str(e)}")
            raise
    
    def send_system_notification(
        self,
        receiver_id: str,
        title: str,
        content: str,
        category: str = "system",
        payload: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None
    ) -> Notification:
        """
        システム通知を送信
        
        Args:
            receiver_id: 受信者ID
            title: タイトル
            content: 内容
            category: カテゴリ
            payload: カスタムペイロード
            tenant_id: テナントID
            
        Returns:
            作成された通知オブジェクト
        """
        try:
            # 1. Novu購読者を確認
            self.novu.create_subscriber(
                subscriber_id=receiver_id,
                data={"tenant_id": tenant_id}
            )
            
            # 2. ローカルデータベースに記録を作成
            notification = Notification(
                tenant_id=tenant_id,
                receiver_id=receiver_id,
                title=title,
                content=content,
                category=category,
                payload=payload or {},
                status=NotificationStatus.PENDING
            )
            self.db.add(notification)
            self.db.flush()
            
            # 3. Novuワークフローをトリガー
            novu_payload = {
                "title": title,
                "content": content,
                "category": category,
                "notificationId": str(notification.id),
                **(payload or {})
            }
            
            novu_notification_id = self.novu.trigger_workflow(
                workflow_id="system-notification",
                subscriber_id=receiver_id,
                payload=novu_payload,
                tenant=tenant_id
            )
            
            # 4. Novu通知IDを保存
            notification.novu_notification_id = novu_notification_id
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"System notification sent: {notification.id}")
            return notification
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to send system notification: {str(e)}")
            raise
    
    def list_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        page: int = 0,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        通知リストを取得 (Novuから)
        
        Args:
            user_id: ユーザーID
            unread_only: 未読のみ取得
            page: ページ番号
            limit: 1ページあたりの件数
            
        Returns:
            通知リストと総数
        """
        try:
            # Novuから通知を取得
            result = self.novu.get_notifications(
                subscriber_id=user_id,
                page=page,
                limit=limit
            )
            
            notifications = result.get("data", [])
            total_count = result.get("totalCount", 0)
            
            # 未読のみフィルタ
            if unread_only:
                notifications = [n for n in notifications if not n.get("read")]
            
            return {
                "data": notifications,
                "totalCount": total_count if not unread_only else len(notifications),
                "page": page,
                "pageSize": limit
            }
            
        except Exception as e:
            logger.error(f"Failed to list notifications for user {user_id}: {str(e)}")
            return {"data": [], "totalCount": 0, "page": page, "pageSize": limit}
    
    def get_unread_count(self, user_id: str) -> int:
        """
        未読通知数を取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            未読通知数
        """
        try:
            count = self.novu.get_unseen_count(subscriber_id=user_id, seen=False)
            return count
        except Exception as e:
            logger.error(f"Failed to get unread count for user {user_id}: {str(e)}")
            return 0
    
    def mark_as_read(
        self,
        user_id: str,
        notification_id: str
    ) -> bool:
        """
        通知を既読としてマーク
        
        Args:
            user_id: ユーザーID
            notification_id: 通知ID (Novu message ID)
            
        Returns:
            成功した場合True
        """
        try:
            # Novuで既読マーク
            success = self.novu.mark_message_as_read(
                subscriber_id=user_id,
                message_id=notification_id
            )
            
            if success:
                # ローカルデータベースも更新
                notification = self.db.query(Notification).filter(
                    Notification.novu_notification_id == notification_id,
                    Notification.receiver_id == user_id
                ).first()
                
                if notification:
                    notification.status = NotificationStatus.READ
                    notification.read_at = datetime.utcnow()
                    self.db.commit()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {str(e)}")
            return False
    
    def mark_as_seen(
        self,
        user_id: str,
        notification_id: str
    ) -> bool:
        """
        通知を既読としてマーク (seen)
        
        Args:
            user_id: ユーザーID
            notification_id: 通知ID (Novu message ID)
            
        Returns:
            成功した場合True
        """
        try:
            success = self.novu.mark_message_as_seen(
                subscriber_id=user_id,
                message_id=notification_id
            )
            return success
            
        except Exception as e:
            logger.error(f"Failed to mark notification as seen: {str(e)}")
            return False
    
    def mark_all_as_read(self, user_id: str) -> bool:
        """
        全通知を既読としてマーク
        
        Args:
            user_id: ユーザーID
            
        Returns:
            成功した場合True
        """
        try:
            success = self.novu.mark_all_messages_as_read(subscriber_id=user_id)
            
            if success:
                # ローカルデータベースも更新
                self.db.query(Notification).filter(
                    Notification.receiver_id == user_id,
                    Notification.status != NotificationStatus.READ
                ).update({
                    "status": NotificationStatus.READ,
                    "read_at": datetime.utcnow()
                })
                self.db.commit()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {str(e)}")
            return False
    
    def delete_notification(
        self,
        user_id: str,
        notification_id: str
    ) -> bool:
        """
        通知を削除
        
        Args:
            user_id: ユーザーID
            notification_id: 通知ID (Novu message ID)
            
        Returns:
            成功した場合True
        """
        try:
            # Novuから削除
            success = self.novu.delete_message(
                subscriber_id=user_id,
                message_id=notification_id
            )
            
            if success:
                # ローカルデータベースも更新 (論理削除)
                notification = self.db.query(Notification).filter(
                    Notification.novu_notification_id == notification_id,
                    Notification.receiver_id == user_id
                ).first()
                
                if notification:
                    notification.deleted_at = datetime.utcnow()
                    self.db.commit()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete notification: {str(e)}")
            return False
    
    def sync_subscriber(
        self,
        user_id: str,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        avatar: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        ユーザーをNovu購読者として同期
        
        Args:
            user_id: ユーザーID
            email: メールアドレス
            first_name: 名
            last_name: 姓
            avatar: アバターURL
            data: カスタムデータ
            
        Returns:
            成功した場合True
        """
        try:
            self.novu.create_subscriber(
                subscriber_id=user_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                avatar=avatar,
                data=data
            )
            logger.info(f"Subscriber synced: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync subscriber {user_id}: {str(e)}")
            return False
    
    def _build_approval_payload(
        self,
        workflow_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        承認通知のペイロードを構築
        
        Args:
            workflow_data: ワークフローデータ
            
        Returns:
            完全なペイロード
        """
        work_id = workflow_data.get("WorkID", "")
        flow_name = workflow_data.get("FlowName", "")
        starter_name = workflow_data.get("StarterName", "")
        
        return {
            "title": "新しい承認リクエスト",
            "content": f"{starter_name}さんから{flow_name}の承認リクエストが届きました",
            "type": "workflow_request",
            "workflowData": workflow_data,
            "actions": [
                {
                    "id": "approve",
                    "label": "承認",
                    "type": "primary",
                    "action": "approve"
                },
                {
                    "id": "reject",
                    "label": "否認",
                    "type": "secondary",
                    "action": "reject"
                }
            ],
            "formSchema": {
                "type": "approval",
                "fields": [
                    {
                        "id": "comment",
                        "type": "textarea",
                        "label": "コメント",
                        "placeholder": "承認/否認の理由を入力してください",
                        "required": False
                    }
                ]
            },
            "showApprovalButtons": True
        }
    
    def get_notification_by_id(
        self,
        notification_id: str
    ) -> Optional[Notification]:
        """
        ローカルデータベースから通知を取得
        
        Args:
            notification_id: 通知ID (ローカルDB)
            
        Returns:
            通知オブジェクト、存在しない場合はNone
        """
        try:
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id
            ).first()
            return notification
            
        except Exception as e:
            logger.error(f"Failed to get notification {notification_id}: {str(e)}")
            return None
