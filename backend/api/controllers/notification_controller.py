"""
通知コントローラー - REST APIエンドポイント
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.adapters.novu_adapter import NovuAdapter
from api.services.notification_service import NotificationService
from api.core.database import get_db_session
from api.middleware.auth_middleware import get_current_user
from api.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
    SendWorkflowApprovalRequest,
    SendSystemNotificationRequest,
    MarkReadRequest,
    SSFlowApprovalActionRequest,
    SSFlowSubmitActionRequest
)
from api.services.ars_service import ArsService
from api.services.ssflow_utils import FK_FLOW_TO_TABLE as _FK_FLOW_TO_TABLE, CCFLOW_FLOW_MAPPING as _CCFLOW_FLOW_MAPPING, build_maintblname_value as _build_maintblname_value
from pydantic import BaseModel
import os
import json
import urllib.request
import urllib.parse

class SubscriberTokenResponse(BaseModel):
    subscriberToken: str

logger = logging.getLogger(__name__)

router = APIRouter()



async def _call_ars_flow(ars_endpoint: str, ars_api_key: str, flow_id: int, params: dict) -> dict:
    """ARS /execute を呼び出す共通ヘルパー（申請・承認共用）"""
    ars_payload = {"id": flow_id, "type": "flow", "params": params}
    ars_req = urllib.request.Request(
        f"{ars_endpoint}/execute",
        data=json.dumps(ars_payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": ars_api_key,
        }
    )
    with urllib.request.urlopen(ars_req, timeout=30) as resp:
        resp_body = resp.read().decode("utf-8")
    return json.loads(resp_body)


def get_novu_adapter() -> NovuAdapter:
    """Novuアダプターの依存性注入"""
    return NovuAdapter()


def get_notification_service(
    db = Depends(get_db_session),
    novu: NovuAdapter = Depends(get_novu_adapter)
) -> NotificationService:
    """通知サービスの依存性注入"""
    return NotificationService(novu_adapter=novu, db_session=db)


@router.get("/")
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
        result = await service.list_notifications(
            user_id=current_user.username,
            unread_only=unread_only,
            page=page,
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"Failed to list notifications: {str(e)}", exc_info=True)
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
        count = service.get_unread_count(user_id=current_user.username)
        return {"unread": count}
    except Exception as e:
        logger.error(f"Failed to get unread count: {str(e)}")
        raise HTTPException(status_code=500, detail="未読数の取得に失敗しました")


@router.get("/subscriber-token", response_model=SubscriberTokenResponse)
async def get_subscriber_token(
    current_user = Depends(get_current_user),
    novu_adapter: NovuAdapter = Depends(get_novu_adapter)
):
    """
    Novu WebSocket接続用のsubscriber tokenを取得
    """
    try:
        subscriber_id = current_user.username
        token = novu_adapter.get_subscriber_token(subscriber_id)
        return {"subscriberToken": token}
    except Exception as e:
        logger.error(f"Failed to get subscriber token: {str(e)}")
        raise HTTPException(status_code=500, detail="Subscriber tokenの取得に失敗しました")


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
            user_id=current_user.username,
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
            user_id=current_user.username,
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
        success = service.mark_all_as_read(user_id=current_user.username)
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
            user_id=current_user.username,
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
            sender_id=current_user.user_id,
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
            user_id=current_user.username,
            email=current_user.email,
            first_name=current_user.full_name
        )
        if not success:
            raise HTTPException(status_code=500, detail="購読者の同期に失敗しました")
        return {"result": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync subscriber: {str(e)}")
        raise HTTPException(status_code=500, detail="購読者の同期に失敗しました")


@router.post("/approval-action")
async def approval_action(
    request: SSFlowApprovalActionRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    SSFlow承認・否認アクションを実行する（ARS flow ID 8経由）

    - **ars_params**: Novu通知のpayload.arsParamsの値
    - **action**: "approve"（承認）または "deny"（否認）
    - **comment**: コメント（オプション）
    """
    try:
        ars = request.ars_params
        action_label = "承認" if request.action == "approve" else "否認"

        # ARS flow ID 8 経由で処理
        ars_endpoint = os.environ.get("ARS_API_ENDPOINT", "http://ars-backend:5050")

        # ユーザーのARS APIキーを取得（共通メソッド）
        ars_api_key = await ArsService.get_required_ars_token(db, current_user.user_id)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 事前チェック: 現在のノードが通知時と一致するか確認
        # 承認済みの場合（FK_Node が変わっている / WFState != 1）は処理しない
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        ssflow_endpoint = os.environ.get("SSFLOW_API_URL", "http://host.docker.internal:56145")
        try:
            check_req = urllib.request.Request(
                f"{ssflow_endpoint}/WF/Comm/Handler.ashx"
                f"?DoType=HttpHandler&DoMethod=GetCurrentNodeInfo"
                f"&HttpHandlerName=BP.WF.HttpHandler.BaseApprovalController",
                data=urllib.parse.urlencode({"WorkID": str(ars.get("WorkID", ""))}).encode("utf-8"),
                method="POST",
            )
            with urllib.request.urlopen(check_req, timeout=10) as check_resp:
                check_body = check_resp.read().decode("utf-8-sig")
            check_data = json.loads(check_body)

            wf_state    = str(check_data.get("WFState", ""))
            flow_status = check_data.get("FlowStatus", "")

            # WFState: 1=進行中, 3=完了, 4=取消/否認
            # ノード番号は申請推移により変わるため比較しない。WFStateのみ確認。
            if wf_state in ("3", "4"):
                last_sender  = check_data.get("LastSenderName", "")
                last_node    = check_data.get("LastNodeName", "")
                next_node    = check_data.get("NextNodeName", "")

                if flow_status == "completed":
                    # フロー全体が完了
                    if last_sender:
                        msg = f"この申請は承認済みです。最終承認者：{last_sender}。フローは完了しています。"
                    else:
                        msg = "この申請は承認済みです。フローは完了しています。"
                elif flow_status == "denied":
                    # 否認/取消
                    if last_sender:
                        msg = f"この申請は否認されています。否認者：{last_sender}。"
                    else:
                        msg = "この申請は否認/取消されています。"
                else:
                    # フォールバック
                    if last_sender:
                        msg = f"この申請は既に処理済みです。承認者：{last_sender}"
                        if last_node and last_node != "END":
                            msg += f"（{last_node}）"
                    else:
                        msg = f"この申請は既に処理済みです（WFState={wf_state}）。"

                return {"result": "already_processed", "message": msg}

            # 進行中だが既に別の担当者が自分のノードを処理済みの場合
            # （WFState=1 でもノードが変わっている = 別の人が処理済み）
            if wf_state == "1":
                next_node    = check_data.get("NextNodeName", "")
                last_sender  = check_data.get("LastSenderName", "")
                if last_sender and next_node:
                    # 自分の申請ノードは既に処理され、次のノードに進んでいる
                    msg = f"この申請は既に処理済みです。承認者：{last_sender}。現在「{next_node}」ノードで承認待ちです。"
                    return {"result": "already_processed", "message": msg}

        except Exception as check_err:
            # チェック失敗時は、ワークフローが完了済み（データ削除済み）と判断
            logger.warning(f"ノード状態確認失敗（ワークフロー完了済みと判断）: {str(check_err)}")
            return {
                "result": "already_processed",
                "message": "この申請は既に処理済みです。ワークフローデータが見つかりません。"
            }

        # 承認: Mode=4, 否認: Mode=5
        mode = "4" if request.action == "approve" else "5"

        # MainTblName の値を取得（動的キー生成用）
        main_tbl_name = ars.get("MainTblName", "")

        # WFComment JSON を構築（MainTblName の値をキーに、コメントを設定）
        wf_comment_json = json.dumps({"WFComment": request.comment or ""}, ensure_ascii=False)

        # tool 14（ログイン）用: 承認者の社員番号（UserNo）を SHAINBANGO として渡す
        user_no = ars.get("UserNo", "")

        # ARS /execute に flow_id=8 で送信
        # params のキーは ARS tool_param_mappings の source_path または source_value に対応
        ars_payload = {
            "id": 8,
            "type": "flow",
            "params": {
                # tool 14（ログイン）用
                "SHAINBANGO":       user_no,
                # tool 18（承認/否認）用パラメータ
                "Mode":             mode,
                "WorkID":           str(ars.get("WorkID", "")),
                "FK_Flow":          ars.get("FK_Flow", ""),
                "FK_Node":          ars.get("FK_Node", ""),
                "NodeID":           ars.get("NodeID", ""),
                "MainTblName":      main_tbl_name,
                # #MainTblName 動的キー生成: MainTblName の値をキーにして WFComment JSON を設定
                "MainTblName_value": wf_comment_json,
            }
        }

        try:
            resp_data = await _call_ars_flow(
                ars_endpoint=ars_endpoint,
                ars_api_key=ars_api_key,
                flow_id=8,
                params=ars_payload["params"]
            )
            logger.info(f"ARS flow 8 approval action [{request.action}] by {current_user.username}: {resp_data}")
            return {"result": "success", "message": f"{action_label}処理が完了しました"}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else str(e)
            logger.error(f"ARS flow 8 error: {e.code} - {err_body}")
            raise HTTPException(status_code=500, detail=f"ARS処理に失敗しました: {err_body}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approval action failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"承認処理に失敗しました: {str(e)}")


@router.get("/flow-options")
async def get_flow_options(
    current_user = Depends(get_current_user)
):
    """
    CCFLOWフロー選択肢を返す（ccflow_flows.json から読み込み）

    レスポンス例:
    [
      {"fk_flow": "001", "label": "商品計画申請", "main_tbl_name": "TT_WF_MERCHANDISE_PLAN"},
      ...
    ]
    """
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "ccflow_flows.json")
    config_path = os.path.normpath(config_path)
    try:
        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("flows", [])
    except FileNotFoundError:
        logger.warning(f"ccflow_flows.json not found at {config_path}, returning defaults")
        return [{"fk_flow": k, "label": k, "main_tbl_name": v} for k, v in _FK_FLOW_TO_TABLE.items()]
    except Exception as e:
        logger.error(f"Failed to read ccflow_flows.json: {e}")
        raise HTTPException(status_code=500, detail=f"フロー設定の読み込みに失敗しました: {str(e)}")


@router.post("/submit-action")
async def submit_action(
    request: SSFlowSubmitActionRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db_session)
):
    """
    SSFlow申請アクションを実行する（ARS Flow 10 共通テンプレート経由）

    - **fk_flow**: SSFlowフローID（例: '001'〜'009'）
    - **form_data**: フォームデータ（MainTblName テーブルの内容）
    - **comment**: コメント（オプション）
    """
    try:
        fk_flow = request.fk_flow
        if fk_flow not in _FK_FLOW_TO_TABLE:
            raise HTTPException(status_code=400, detail=f"不正な FK_Flow: {fk_flow}")

        flow_id = _CCFLOW_FLOW_MAPPING[fk_flow]
        main_tbl_name = _FK_FLOW_TO_TABLE[fk_flow]

        ars_endpoint = os.environ.get("ARS_API_ENDPOINT", "http://ars-backend:5050")

        ars_api_key = await ArsService.get_required_ars_token(db, current_user.user_id)

        # コメントをフォームデータにマージ
        form_data = dict(request.form_data)
        if request.comment:
            form_data["COMMENT"] = request.comment

        # 展開フィールド（COMMENT, AgentMode, content_* 等）を MainTblName_value に組み立て
        maintblname_value = _build_maintblname_value(form_data)

        params = {
            "SHAINBANGO":        current_user.username,
            "FK_Flow":           fk_flow,
            "MainTblName":       main_tbl_name,
            "MainTblName_value": maintblname_value,
        }

        try:
            resp_data = await _call_ars_flow(
                ars_endpoint=ars_endpoint,
                ars_api_key=ars_api_key,
                flow_id=flow_id,
                params=params
            )
            logger.info(f"ARS flow {flow_id} submit action [FK_Flow={fk_flow}] by {current_user.username}: {resp_data}")

            # レスポンスから WorkID を抽出
            work_id = ""
            steps = resp_data.get("steps", [])
            if steps:
                last_step = steps[-1]
                work_id = str(last_step.get("response", {}).get("data", {}).get("WorkID", ""))

            return {
                "result": "success",
                "work_id": work_id,
                "message": f"申請が完了しました" + (f"（申請番号: {work_id}）" if work_id else "")
            }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else str(e)
            logger.error(f"ARS flow {flow_id} error: {e.code} - {err_body}")
            raise HTTPException(status_code=500, detail=f"ARS処理に失敗しました: {err_body}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit action failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"申請処理に失敗しました: {str(e)}")
