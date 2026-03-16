"""
通知サービス - Novuアダプターとローカルデータベースを統合
"""
import logging
import requests
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
        
        # Novu API設定を一度だけ取得（環境変数必須）
        self.novu_api_url = os.getenv("NOVU_API_URL")
        if not self.novu_api_url:
            raise ValueError(
                "NOVU_API_URL environment variable is required. "
                "Please set it to your Novu API endpoint (e.g., http://novu-api:3000 or https://api.novu.co)"
            )
        
        self.novu_api_key = os.getenv("NOVU_API_KEY")
        if not self.novu_api_key:
            raise ValueError(
                "NOVU_API_KEY environment variable is required. "
                "Please set it to your Novu API key."
            )
    
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
    
    async def list_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        page: int = 0,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        通知リストを取得 (Novu Messages APIから直接取得し、ローカルDBのpayloadとマージ)
        
        Args:
            user_id: ユーザーID
            unread_only: 未読のみ取得
            page: ページ番号
            limit: 1ページあたりの件数
            
        Returns:
            通知リストと総数
        """
        try:
            # Novu Messages APIから直接取得
            response = requests.get(
                f"{self.novu_api_url}/v1/messages",
                headers={
                    "Authorization": f"ApiKey {self.novu_api_key}",
                    "Content-Type": "application/json"
                },
                params={
                    "subscriberId": user_id,
                    "channel": "in_app",
                    "page": page,
                    "limit": limit
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                notifications = result.get("data", [])
                
                # 未読のみフィルタ
                if unread_only:
                    notifications = [n for n in notifications if not n.get("seen")]
                
                # ローカルDBからpayloadを取得してマージ（AsyncSession対応）
                if isinstance(self.db, AsyncSession):
                    for notification in notifications:
                        transaction_id = notification.get("transactionId")
                        if transaction_id:
                            stmt = select(Notification).where(
                                Notification.novu_notification_id == transaction_id
                            )
                            result_db = await self.db.execute(stmt)
                            local_notif = result_db.scalar_one_or_none()
                            
                            if local_notif and local_notif.payload:
                                # ローカルDBのpayloadでNovuのpayloadを上書き
                                notification["payload"] = local_notif.payload
                
                return {
                    "data": notifications,
                    "total": len(notifications),
                    "page": page,
                    "pageSize": limit
                }
            else:
                logger.error(f"Novu API returned {response.status_code}: {response.text}")
                return {"data": [], "total": 0, "page": page, "pageSize": limit}
            
        except Exception as e:
            logger.error(f"Failed to list notifications for user {user_id}: {str(e)}")
            return {"data": [], "total": 0, "page": page, "pageSize": limit}
    
    def get_unread_count(self, user_id: str) -> int:
        """
        未読通知数を取得 (Novu Messages APIから直接取得)
        
        Args:
            user_id: ユーザーID
            
        Returns:
            未読通知数
        """
        try:
            # Novu Messages APIから直接取得
            response = requests.get(
                f"{self.novu_api_url}/v1/messages",
                headers={
                    "Authorization": f"ApiKey {self.novu_api_key}",
                    "Content-Type": "application/json"
                },
                params={
                    "subscriberId": user_id,
                    "channel": "in_app",
                    "page": 0,
                    "limit": 100
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                messages = result.get("data", [])
                # seenがfalseのものを未読としてカウント
                unread_count = sum(1 for msg in messages if not msg.get("seen", False))
                return unread_count
            else:
                logger.error(f"Novu API returned {response.status_code}: {response.text}")
                return 0
                
        except Exception as e:
            logger.error(f"Failed to get unread count for user {user_id}: {str(e)}")
            return 0
    
    def mark_as_read(
        self,
        user_id: str,
        notification_id: str
    ) -> bool:
        """
        通知を既読としてマーク (Novu Subscribers APIを使用)
        
        Args:
            user_id: ユーザーID (subscriber ID)
            notification_id: 通知ID (Novu message ID)
            
        Returns:
            成功した場合True
        """
        try:
            # Novu Subscribers APIで既読マーク
            response = requests.post(
                f"{self.novu_api_url}/v1/subscribers/{user_id}/messages/markAs",
                json={
                    "messageId": notification_id,
                    "mark": {
                        "seen": True,
                        "read": True
                    }
                },
                headers={
                    "Authorization": f"ApiKey {self.novu_api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code in [200, 201, 204]:
                logger.info(f"Successfully marked notification {notification_id} as read for user {user_id}")
                return True
            else:
                logger.error(f"Novu API returned {response.status_code}: {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {str(e)}")
            return False
    
    def mark_as_seen(
        self,
        user_id: str,
        notification_id: str
    ) -> bool:
        """
        通知を既読としてマーク (seen) - Novu Subscribers APIを使用
        
        Args:
            user_id: ユーザーID (subscriber ID)
            notification_id: 通知ID (Novu message ID)
            
        Returns:
            成功した場合True
        """
        try:
            # Novu Subscribers APIでseenマーク
            response = requests.post(
                f"{self.novu_api_url}/v1/subscribers/{user_id}/messages/markAs",
                json={
                    "messageId": notification_id,
                    "mark": {
                        "seen": True
                    }
                },
                headers={
                    "Authorization": f"ApiKey {self.novu_api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code in [200, 201, 204]:
                return True
            else:
                logger.error(f"Novu API returned {response.status_code}: {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to mark notification as seen: {str(e)}")
            return False
    
    def mark_all_as_read(self, user_id: str) -> bool:
        """
        全通知を既読としてマーク (Novu Messages APIを使用)
        
        Args:
            user_id: ユーザーID (subscriber ID)
            
        Returns:
            成功した場合True
        """
        try:
            # まず未読通知を取得
            response = requests.get(
                f"{self.novu_api_url}/v1/messages",
                params={
                    "subscriberId": user_id,
                    "page": 0,
                    "limit": 100  # 一度に最大100件
                },
                headers={
                    "Authorization": f"ApiKey {self.novu_api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch messages: {response.status_code}")
                return False
            
            data = response.json()
            messages = data.get("data", [])
            
            # 未読メッセージを既読にマーク
            success_count = 0
            for message in messages:
                if not message.get("read"):
                    message_id = message.get("_id")
                    mark_response = requests.post(
                        f"{self.novu_api_url}/v1/subscribers/{user_id}/messages/markAs",
                        json={
                            "messageId": message_id,
                            "mark": {
                                "seen": True,
                                "read": True
                            }
                        },
                        headers={
                            "Authorization": f"ApiKey {self.novu_api_key}",
                            "Content-Type": "application/json"
                        }
                    )
                    
                    if mark_response.status_code in [200, 201, 204]:
                        success_count += 1
            
            logger.info(f"Marked {success_count} messages as read for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {str(e)}")
            return False
    
    def delete_notification(
        self,
        user_id: str,
        notification_id: str
    ) -> bool:
        """
        通知を削除 (Novu Messages APIを使用)
        
        Args:
            user_id: ユーザーID (subscriber ID)
            notification_id: 通知ID (Novu message ID)
            
        Returns:
            成功した場合True
        """
        try:
            # Novu Messages APIで削除
            response = requests.delete(
                f"{self.novu_api_url}/v1/messages/{notification_id}",
                headers={
                    "Authorization": f"ApiKey {self.novu_api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code in [200, 201, 204]:
                logger.info(f"Successfully deleted notification {notification_id} for user {user_id}")
                return True
            else:
                logger.error(f"Novu API returned {response.status_code}: {response.text}")
                return False
            
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
        
        ssflow_url = os.getenv("SSFLOW_URL", "http://192.168.1.78:56145/wwwroot/login.html")
        
        return {
            "title": "新しい承認リクエスト",
            "content": f"{starter_name}さんから{flow_name}の承認リクエストが届きました",
            "type": "workflow_request",
            "workflowData": workflow_data,
            "arsParams": workflow_data,
            "workflowId": work_id,
            "buttons": [
                {
                    "type": "primary",
                    "content": "詳細を確認",
                    "url": f"/api/approval/session/{work_id}"
                },
                {
                    "type": "secondary",
                    "content": "SSFlow へ移動",
                    "url": ssflow_url
                }
            ],
            "notificationType": "ssflow_approval",
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
