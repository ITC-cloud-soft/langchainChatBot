"""
Novu統合テストスイート - 完全なエンドツーエンドテスト
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any

from api.adapters.novu_adapter import NovuAdapter
from api.services.notification_service import NotificationService
from api.models.notification import Notification, NotificationStatus


class TestNovuAdapter:
    """NovuAdapterのユニットテスト"""
    
    @pytest.fixture
    def novu_adapter(self):
        """Novuアダプターのフィクスチャ"""
        with patch.dict('os.environ', {'NOVU_API_KEY': 'test_api_key'}):
            adapter = NovuAdapter(
                api_key='test_api_key',
                backend_url='http://localhost:3000'
            )
            return adapter
    
    def test_adapter_initialization(self, novu_adapter):
        """アダプターの初期化テスト"""
        assert novu_adapter.api_key == 'test_api_key'
        assert novu_adapter.backend_url == 'http://localhost:3000'
        assert novu_adapter.event_api is not None
    
    def test_adapter_initialization_without_api_key(self):
        """API Keyなしでの初期化エラーテスト"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="Novu API key is required"):
                NovuAdapter()
    
    @patch('api.adapters.novu_adapter.EventApi')
    def test_create_subscriber(self, mock_event_api, novu_adapter):
        """購読者作成テスト"""
        mock_event_api.return_value.subscribers.identify.return_value = {
            'data': {'_id': 'sub_123', 'subscriberId': 'user_001'}
        }
        
        result = novu_adapter.create_subscriber(
            subscriber_id='user_001',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        
        assert result is not None
    
    @patch('api.adapters.novu_adapter.EventApi')
    def test_trigger_workflow(self, mock_event_api, novu_adapter):
        """ワークフロートリガーテスト"""
        mock_event_api.return_value.trigger.return_value = {
            'data': {'transactionId': 'txn_123'}
        }
        
        notification_id = novu_adapter.trigger_workflow(
            workflow_id='test-workflow',
            subscriber_id='user_001',
            payload={'message': 'Test notification'}
        )
        
        assert notification_id == 'txn_123'
    
    @patch('api.adapters.novu_adapter.EventApi')
    def test_get_notifications(self, mock_event_api, novu_adapter):
        """通知リスト取得テスト"""
        mock_event_api.return_value.subscribers.get_notifications.return_value = {
            'data': [
                {'_id': 'notif_1', 'content': 'Test 1'},
                {'_id': 'notif_2', 'content': 'Test 2'}
            ],
            'totalCount': 2,
            'page': 0
        }
        
        result = novu_adapter.get_notifications(
            subscriber_id='user_001',
            page=0,
            limit=10
        )
        
        assert len(result['data']) == 2
        assert result['totalCount'] == 2
    
    @patch('api.adapters.novu_adapter.EventApi')
    def test_mark_as_read(self, mock_event_api, novu_adapter):
        """既読マークテスト"""
        mock_event_api.return_value.subscribers.mark_message_as_read.return_value = True
        
        success = novu_adapter.mark_message_as_read(
            subscriber_id='user_001',
            message_id='msg_123'
        )
        
        assert success is True
    
    @patch('api.adapters.novu_adapter.EventApi')
    def test_get_unread_count(self, mock_event_api, novu_adapter):
        """未読数取得テスト"""
        mock_event_api.return_value.subscribers.get_unseen_count.return_value = {
            'data': {'count': 5}
        }
        
        count = novu_adapter.get_unseen_count(subscriber_id='user_001')
        
        assert count == 5


class TestNotificationService:
    """NotificationServiceのユニットテスト"""
    
    @pytest.fixture
    def mock_novu_adapter(self):
        """モックNovuアダプター"""
        adapter = Mock(spec=NovuAdapter)
        adapter.create_subscriber = Mock(return_value={'data': {'_id': 'sub_123'}})
        adapter.trigger_workflow = Mock(return_value='txn_123')
        adapter.get_notifications = Mock(return_value={
            'data': [],
            'totalCount': 0,
            'page': 0
        })
        adapter.get_unseen_count = Mock(return_value=0)
        adapter.mark_message_as_read = Mock(return_value=True)
        adapter.mark_all_messages_as_read = Mock(return_value=True)
        adapter.delete_message = Mock(return_value=True)
        return adapter
    
    @pytest.fixture
    def mock_db_session(self):
        """モックデータベースセッション"""
        session = Mock()
        session.add = Mock()
        session.flush = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.query = Mock()
        return session
    
    @pytest.fixture
    def notification_service(self, mock_novu_adapter, mock_db_session):
        """通知サービスのフィクスチャ"""
        return NotificationService(
            novu_adapter=mock_novu_adapter,
            db_session=mock_db_session
        )
    
    def test_send_workflow_approval(self, notification_service, mock_novu_adapter, mock_db_session):
        """ワークフロー承認通知送信テスト"""
        workflow_data = {
            'WorkID': 'WF001',
            'FlowName': 'テストフロー',
            'StarterName': '山田太郎'
        }
        
        notification = notification_service.send_workflow_approval(
            receiver_id='user_001',
            workflow_data=workflow_data,
            sender_id='user_002',
            tenant_id='tenant_001',
            chatbot_id='bot_001'
        )
        
        # Novu購読者が作成されたことを確認
        mock_novu_adapter.create_subscriber.assert_called_once()
        
        # ワークフローがトリガーされたことを確認
        mock_novu_adapter.trigger_workflow.assert_called_once()
        
        # データベースに保存されたことを確認
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_send_system_notification(self, notification_service, mock_novu_adapter, mock_db_session):
        """システム通知送信テスト"""
        notification = notification_service.send_system_notification(
            receiver_id='user_001',
            title='テスト通知',
            content='これはテストメッセージです',
            category='system',
            tenant_id='tenant_001'
        )
        
        # Novu購読者が確認されたことを確認
        mock_novu_adapter.create_subscriber.assert_called_once()
        
        # ワークフローがトリガーされたことを確認
        mock_novu_adapter.trigger_workflow.assert_called_once()
        
        # データベースに保存されたことを確認
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_list_notifications(self, notification_service, mock_novu_adapter):
        """通知リスト取得テスト"""
        result = notification_service.list_notifications(
            user_id='user_001',
            unread_only=False,
            page=0,
            limit=10
        )
        
        assert 'data' in result
        assert 'totalCount' in result
        assert result['page'] == 0
        
        # Novuから通知が取得されたことを確認
        mock_novu_adapter.get_notifications.assert_called_once()
    
    def test_get_unread_count(self, notification_service, mock_novu_adapter):
        """未読数取得テスト"""
        count = notification_service.get_unread_count(user_id='user_001')
        
        assert count == 0
        mock_novu_adapter.get_unseen_count.assert_called_once()
    
    def test_mark_as_read(self, notification_service, mock_novu_adapter, mock_db_session):
        """既読マークテスト"""
        # モックの通知を設定
        mock_notification = Mock(spec=Notification)
        mock_notification.novu_notification_id = 'msg_123'
        mock_notification.receiver_id = 'user_001'
        mock_notification.status = NotificationStatus.SENT
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_notification
        
        success = notification_service.mark_as_read(
            user_id='user_001',
            notification_id='msg_123'
        )
        
        assert success is True
        mock_novu_adapter.mark_message_as_read.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_mark_all_as_read(self, notification_service, mock_novu_adapter, mock_db_session):
        """全て既読マークテスト"""
        mock_db_session.query.return_value.filter.return_value.update.return_value = 3
        
        success = notification_service.mark_all_as_read(user_id='user_001')
        
        assert success is True
        mock_novu_adapter.mark_all_messages_as_read.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_delete_notification(self, notification_service, mock_novu_adapter, mock_db_session):
        """通知削除テスト"""
        # モックの通知を設定
        mock_notification = Mock(spec=Notification)
        mock_notification.novu_notification_id = 'msg_123'
        mock_notification.receiver_id = 'user_001'
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_notification
        
        success = notification_service.delete_notification(
            user_id='user_001',
            notification_id='msg_123'
        )
        
        assert success is True
        mock_novu_adapter.delete_message.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_sync_subscriber(self, notification_service, mock_novu_adapter):
        """購読者同期テスト"""
        success = notification_service.sync_subscriber(
            user_id='user_001',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            data={'role': 'admin'}
        )
        
        assert success is True
        mock_novu_adapter.create_subscriber.assert_called_once()


class TestNovuIntegrationEndToEnd:
    """エンドツーエンド統合テスト"""
    
    @pytest.fixture
    def integration_config(self):
        """統合テスト設定"""
        return {
            'novu_api_key': 'test_api_key',
            'novu_backend_url': 'http://localhost:3000',
            'test_user_id': 'test_user_001',
            'test_workflow_id': 'welcome-notification-api'
        }
    
    @pytest.mark.integration
    def test_complete_notification_flow(self, integration_config):
        """完全な通知フローのテスト"""
        # このテストは実際のNovuサービスが必要
        # モック環境では@pytest.mark.skipでスキップ
        pytest.skip("Requires live Novu service")
    
    @pytest.mark.integration
    def test_workflow_approval_flow(self, integration_config):
        """ワークフロー承認フローのテスト"""
        pytest.skip("Requires live Novu service")


# テストヘルパー関数
def create_test_notification(
    notification_id: str = 'test_notif_001',
    receiver_id: str = 'user_001',
    status: NotificationStatus = NotificationStatus.SENT
) -> Notification:
    """テスト用通知オブジェクトを作成"""
    return Notification(
        id=notification_id,
        tenant_id='tenant_001',
        receiver_id=receiver_id,
        title='テスト通知',
        content='これはテストメッセージです',
        category='system',
        payload={},
        status=status,
        novu_notification_id='novu_msg_123',
        sent_at=datetime.utcnow()
    )


def create_test_workflow_data() -> Dict[str, Any]:
    """テスト用ワークフローデータを作成"""
    return {
        'WorkID': 'WF001',
        'FlowName': 'テストワークフロー',
        'StarterName': '山田太郎',
        'StartTime': '2026-01-22T10:00:00Z',
        'Description': 'テスト用のワークフロー'
    }


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
