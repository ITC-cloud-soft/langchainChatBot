"""
通知スキーマ - リクエスト/レスポンスモデル
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class SendWorkflowApprovalRequest(BaseModel):
    """ワークフロー承認通知送信リクエスト"""
    receiver_id: str = Field(..., description="受信者ID")
    workflow_data: Dict[str, Any] = Field(..., description="ワークフローデータ")
    tenant_id: Optional[str] = Field(None, description="テナントID")
    chatbot_id: Optional[str] = Field(None, description="チャットボットID")


class SendSystemNotificationRequest(BaseModel):
    """システム通知送信リクエスト"""
    receiver_id: str = Field(..., description="受信者ID")
    title: str = Field(..., description="タイトル")
    content: str = Field(..., description="内容")
    category: Optional[str] = Field("system", description="カテゴリ")
    payload: Optional[Dict[str, Any]] = Field(None, description="カスタムペイロード")
    tenant_id: Optional[str] = Field(None, description="テナントID")


class MarkReadRequest(BaseModel):
    """既読マークリクエスト"""
    notification_id: str = Field(..., description="通知ID")


class NotificationResponse(BaseModel):
    """通知レスポンス"""
    id: str
    tenant_id: Optional[str]
    chatbot_id: Optional[str]
    connection_id: Optional[str]
    novu_notification_id: Optional[str]
    novu_subscriber_id: Optional[str]
    sender_id: Optional[str]
    receiver_id: str
    title: str
    content: Optional[str]
    category: Optional[str]
    payload: Optional[Dict[str, Any]]
    status: str
    created_at: Optional[str]
    sent_at: Optional[str]
    read_at: Optional[str]
    deleted_at: Optional[str]


class NotificationListResponse(BaseModel):
    """通知リストレスポンス"""
    data: List[Dict[str, Any]]
    totalCount: int
    page: int
    pageSize: int


class UnreadCountResponse(BaseModel):
    """未読数レスポンス"""
    unread: int


class SSFlowApprovalActionRequest(BaseModel):
    """SSFlow承認・否認アクションリクエスト"""
    ars_params: Dict[str, Any] = Field(..., description="SSFlow arsParams")
    action: str = Field(..., description="承認: approve / 否認: deny")
    comment: Optional[str] = Field("", description="コメント")


class SSFlowSubmitActionRequest(BaseModel):
    """SSFlow申請アクションリクエスト（ARS Flow 10 共通テンプレート用）"""
    fk_flow: str = Field(..., description="SSFlowフローID（例: '001'〜'009'）")
    form_data: Dict[str, Any] = Field(..., description="フォームデータ（MainTblName テーブルの内容）")
    comment: Optional[str] = Field("", description="コメント")
