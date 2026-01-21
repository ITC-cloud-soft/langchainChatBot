"""
Novu Adapter - Novu APIとの通信を担当するアダプタークラス
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from novu.api import EventApi
from novu.dto import SubscriberDto, TopicDto
from novu.config import NovuConfig

logger = logging.getLogger(__name__)


class NovuAdapter:
    """Novu APIアダプター"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        backend_url: Optional[str] = None
    ):
        """
        Novuアダプターの初期化
        
        Args:
            api_key: Novu API Key (環境変数NOVU_API_KEYから取得可能)
            backend_url: Novu Backend URL (環境変数NOVU_API_URLから取得可能)
        """
        self.api_key = api_key or os.getenv("NOVU_API_KEY")
        self.backend_url = backend_url or os.getenv("NOVU_API_URL", "http://localhost:3000")
        
        if not self.api_key:
            raise ValueError("Novu API key is required. Set NOVU_API_KEY environment variable.")
        
        # Novu設定
        config = NovuConfig()
        config.api_key = self.api_key
        config.backend_url = self.backend_url
        
        # EventApi初期化
        self.event_api = EventApi(config=config)
        
        logger.info(f"NovuAdapter initialized with backend URL: {self.backend_url}")
    
    def create_subscriber(
        self,
        subscriber_id: str,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        avatar: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Novu購読者を作成または更新
        
        Args:
            subscriber_id: 購読者ID (通常はユーザーID)
            email: メールアドレス
            first_name: 名
            last_name: 姓
            phone: 電話番号
            avatar: アバターURL
            data: カスタムデータ
            
        Returns:
            作成/更新された購読者情報
        """
        try:
            subscriber_dto = SubscriberDto(
                subscriber_id=subscriber_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                avatar=avatar,
                data=data or {}
            )
            
            result = self.event_api.subscribers.identify(subscriber_dto)
            logger.info(f"Subscriber created/updated: {subscriber_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create subscriber {subscriber_id}: {str(e)}")
            raise
    
    def trigger_workflow(
        self,
        workflow_id: str,
        subscriber_id: str,
        payload: Dict[str, Any],
        overrides: Optional[Dict[str, Any]] = None,
        actor: Optional[Dict[str, Any]] = None,
        tenant: Optional[str] = None
    ) -> str:
        """
        Novuワークフローをトリガー
        
        Args:
            workflow_id: ワークフローID (例: "workflow-approval")
            subscriber_id: 購読者ID
            payload: 通知ペイロード
            overrides: 通知オーバーライド設定
            actor: アクター情報
            tenant: テナントID
            
        Returns:
            通知ID
        """
        try:
            result = self.event_api.trigger(
                name=workflow_id,
                recipients=[subscriber_id],
                payload=payload,
                overrides=overrides or {},
                actor=actor,
                tenant=tenant
            )
            
            notification_id = result.get("data", {}).get("transactionId")
            logger.info(f"Workflow triggered: {workflow_id} for subscriber: {subscriber_id}, notification_id: {notification_id}")
            return notification_id
            
        except Exception as e:
            logger.error(f"Failed to trigger workflow {workflow_id}: {str(e)}")
            raise
    
    def trigger_bulk(
        self,
        workflow_id: str,
        subscribers: List[str],
        payload: Dict[str, Any]
    ) -> List[str]:
        """
        複数の購読者に対してワークフローを一括トリガー
        
        Args:
            workflow_id: ワークフローID
            subscribers: 購読者IDのリスト
            payload: 通知ペイロード
            
        Returns:
            通知IDのリスト
        """
        try:
            result = self.event_api.trigger_bulk(
                name=workflow_id,
                recipients=subscribers,
                payload=payload
            )
            
            notification_ids = [item.get("transactionId") for item in result.get("data", [])]
            logger.info(f"Bulk workflow triggered: {workflow_id} for {len(subscribers)} subscribers")
            return notification_ids
            
        except Exception as e:
            logger.error(f"Failed to trigger bulk workflow {workflow_id}: {str(e)}")
            raise
    
    def broadcast(
        self,
        workflow_id: str,
        payload: Dict[str, Any],
        tenant: Optional[str] = None
    ) -> str:
        """
        全購読者に通知をブロードキャスト
        
        Args:
            workflow_id: ワークフローID
            payload: 通知ペイロード
            tenant: テナントID
            
        Returns:
            トランザクションID
        """
        try:
            result = self.event_api.broadcast(
                name=workflow_id,
                payload=payload,
                tenant=tenant
            )
            
            transaction_id = result.get("data", {}).get("transactionId")
            logger.info(f"Broadcast triggered: {workflow_id}")
            return transaction_id
            
        except Exception as e:
            logger.error(f"Failed to broadcast workflow {workflow_id}: {str(e)}")
            raise
    
    def cancel_triggered_event(
        self,
        transaction_id: str
    ) -> bool:
        """
        トリガーされたイベントをキャンセル
        
        Args:
            transaction_id: トランザクションID
            
        Returns:
            成功した場合True
        """
        try:
            self.event_api.cancel(transaction_id)
            logger.info(f"Event cancelled: {transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel event {transaction_id}: {str(e)}")
            return False
    
    def get_subscriber(
        self,
        subscriber_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        購読者情報を取得
        
        Args:
            subscriber_id: 購読者ID
            
        Returns:
            購読者情報、存在しない場合はNone
        """
        try:
            result = self.event_api.subscribers.get(subscriber_id)
            return result
            
        except Exception as e:
            logger.error(f"Failed to get subscriber {subscriber_id}: {str(e)}")
            return None
    
    def update_subscriber(
        self,
        subscriber_id: str,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        avatar: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        購読者情報を更新
        
        Args:
            subscriber_id: 購読者ID
            email: メールアドレス
            first_name: 名
            last_name: 姓
            phone: 電話番号
            avatar: アバターURL
            data: カスタムデータ
            
        Returns:
            更新された購読者情報
        """
        try:
            subscriber_dto = SubscriberDto(
                subscriber_id=subscriber_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                avatar=avatar,
                data=data
            )
            
            result = self.event_api.subscribers.update(subscriber_id, subscriber_dto)
            logger.info(f"Subscriber updated: {subscriber_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to update subscriber {subscriber_id}: {str(e)}")
            raise
    
    def delete_subscriber(
        self,
        subscriber_id: str
    ) -> bool:
        """
        購読者を削除
        
        Args:
            subscriber_id: 購読者ID
            
        Returns:
            成功した場合True
        """
        try:
            self.event_api.subscribers.delete(subscriber_id)
            logger.info(f"Subscriber deleted: {subscriber_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete subscriber {subscriber_id}: {str(e)}")
            return False
    
    def get_subscriber_preferences(
        self,
        subscriber_id: str
    ) -> List[Dict[str, Any]]:
        """
        購読者の通知設定を取得
        
        Args:
            subscriber_id: 購読者ID
            
        Returns:
            通知設定のリスト
        """
        try:
            result = self.event_api.subscribers.get_preferences(subscriber_id)
            return result.get("data", [])
            
        except Exception as e:
            logger.error(f"Failed to get preferences for subscriber {subscriber_id}: {str(e)}")
            return []
    
    def update_subscriber_preference(
        self,
        subscriber_id: str,
        template_id: str,
        channel_type: str,
        enabled: bool
    ) -> Dict[str, Any]:
        """
        購読者の特定チャンネルの通知設定を更新
        
        Args:
            subscriber_id: 購読者ID
            template_id: テンプレートID
            channel_type: チャンネルタイプ (in_app, email, sms, push)
            enabled: 有効/無効
            
        Returns:
            更新された設定情報
        """
        try:
            result = self.event_api.subscribers.update_preference(
                subscriber_id=subscriber_id,
                template_id=template_id,
                channel_type=channel_type,
                enabled=enabled
            )
            logger.info(f"Preference updated for subscriber {subscriber_id}, template {template_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to update preference: {str(e)}")
            raise
    
    def get_notifications(
        self,
        subscriber_id: str,
        page: int = 0,
        limit: int = 10,
        feed_identifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        購読者の通知リストを取得
        
        Args:
            subscriber_id: 購読者ID
            page: ページ番号
            limit: 1ページあたりの件数
            feed_identifier: フィードID
            
        Returns:
            通知リストと総数
        """
        try:
            result = self.event_api.subscribers.get_notifications(
                subscriber_id=subscriber_id,
                page=page,
                limit=limit,
                feed_identifier=feed_identifier
            )
            return result
            
        except Exception as e:
            logger.error(f"Failed to get notifications for subscriber {subscriber_id}: {str(e)}")
            return {"data": [], "totalCount": 0, "page": page}
    
    def get_unseen_count(
        self,
        subscriber_id: str,
        seen: bool = False
    ) -> int:
        """
        未読通知数を取得
        
        Args:
            subscriber_id: 購読者ID
            seen: Trueの場合は既読数を取得
            
        Returns:
            未読/既読通知数
        """
        try:
            result = self.event_api.subscribers.get_unseen_count(
                subscriber_id=subscriber_id,
                seen=seen
            )
            count = result.get("data", {}).get("count", 0)
            return count
            
        except Exception as e:
            logger.error(f"Failed to get unseen count for subscriber {subscriber_id}: {str(e)}")
            return 0
    
    def mark_message_as_seen(
        self,
        subscriber_id: str,
        message_id: str
    ) -> bool:
        """
        メッセージを既読としてマーク
        
        Args:
            subscriber_id: 購読者ID
            message_id: メッセージID
            
        Returns:
            成功した場合True
        """
        try:
            self.event_api.subscribers.mark_message_as_seen(
                subscriber_id=subscriber_id,
                message_id=message_id
            )
            logger.info(f"Message marked as seen: {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark message as seen {message_id}: {str(e)}")
            return False
    
    def mark_message_as_read(
        self,
        subscriber_id: str,
        message_id: str
    ) -> bool:
        """
        メッセージを読了としてマーク
        
        Args:
            subscriber_id: 購読者ID
            message_id: メッセージID
            
        Returns:
            成功した場合True
        """
        try:
            self.event_api.subscribers.mark_message_as_read(
                subscriber_id=subscriber_id,
                message_id=message_id
            )
            logger.info(f"Message marked as read: {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark message as read {message_id}: {str(e)}")
            return False
    
    def mark_all_messages_as_read(
        self,
        subscriber_id: str,
        feed_identifier: Optional[str] = None
    ) -> bool:
        """
        全メッセージを読了としてマーク
        
        Args:
            subscriber_id: 購読者ID
            feed_identifier: フィードID (指定した場合、そのフィードのみ)
            
        Returns:
            成功した場合True
        """
        try:
            self.event_api.subscribers.mark_all_messages_as_read(
                subscriber_id=subscriber_id,
                feed_identifier=feed_identifier
            )
            logger.info(f"All messages marked as read for subscriber: {subscriber_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark all messages as read: {str(e)}")
            return False
    
    def delete_message(
        self,
        subscriber_id: str,
        message_id: str
    ) -> bool:
        """
        メッセージを削除
        
        Args:
            subscriber_id: 購読者ID
            message_id: メッセージID
            
        Returns:
            成功した場合True
        """
        try:
            self.event_api.subscribers.delete_message(
                subscriber_id=subscriber_id,
                message_id=message_id
            )
            logger.info(f"Message deleted: {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete message {message_id}: {str(e)}")
            return False
    
    def create_topic(
        self,
        topic_key: str,
        topic_name: str
    ) -> Dict[str, Any]:
        """
        トピックを作成
        
        Args:
            topic_key: トピックキー
            topic_name: トピック名
            
        Returns:
            作成されたトピック情報
        """
        try:
            topic_dto = TopicDto(
                key=topic_key,
                name=topic_name
            )
            result = self.event_api.topics.create(topic_dto)
            logger.info(f"Topic created: {topic_key}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create topic {topic_key}: {str(e)}")
            raise
    
    def add_subscribers_to_topic(
        self,
        topic_key: str,
        subscriber_ids: List[str]
    ) -> bool:
        """
        トピックに購読者を追加
        
        Args:
            topic_key: トピックキー
            subscriber_ids: 購読者IDのリスト
            
        Returns:
            成功した場合True
        """
        try:
            self.event_api.topics.add_subscribers(
                topic_key=topic_key,
                subscribers=subscriber_ids
            )
            logger.info(f"Added {len(subscriber_ids)} subscribers to topic: {topic_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add subscribers to topic {topic_key}: {str(e)}")
            return False
    
    def remove_subscribers_from_topic(
        self,
        topic_key: str,
        subscriber_ids: List[str]
    ) -> bool:
        """
        トピックから購読者を削除
        
        Args:
            topic_key: トピックキー
            subscriber_ids: 購読者IDのリスト
            
        Returns:
            成功した場合True
        """
        try:
            self.event_api.topics.remove_subscribers(
                topic_key=topic_key,
                subscribers=subscriber_ids
            )
            logger.info(f"Removed {len(subscriber_ids)} subscribers from topic: {topic_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove subscribers from topic {topic_key}: {str(e)}")
            return False
