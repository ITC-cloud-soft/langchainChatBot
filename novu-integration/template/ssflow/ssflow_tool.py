"""
SSFlow 承認通知ツール - オールインワン

✅ 検証済み: ボタン付き通知が正常に動作することを確認

使用方法:
    # ワークフローを作成（初回のみ）
    python ssflow_tool.py create-workflow
    
    # テスト通知を送信
    python ssflow_tool.py send <user_id>
    python ssflow_tool.py send 1
    
    # ワークフロー一覧を確認
    python ssflow_tool.py list-workflows

機能:
    - ワークフローの作成
    - テスト通知の送信（ボタン付き）
    - ワークフロー一覧の確認
    - 通知の確認
"""

import requests
import os
import json
import sys
import time

NOVU_API_KEY = os.getenv("NOVU_API_KEY", "c47cfb7a083c4e27f9d1b523a20ed59f")
NOVU_API_URL = os.getenv("NOVU_API_URL", "http://localhost:3000")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
SSFLOW_URL = "http://192.168.1.78:56145/wwwroot/login.html"


def create_workflow():
    """ワークフローを作成"""
    print("=" * 60)
    print("SSFlow 承認通知ワークフロー作成")
    print("=" * 60)
    
    # 通知グループを取得
    groups = get_notification_groups()
    if not groups:
        print("❌ 通知グループが見つかりません")
        return False
    
    notification_group_id = groups[0].get('_id')
    
    url = f"{NOVU_API_URL}/v1/workflows"
    headers = {
        "Authorization": f"ApiKey {NOVU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    workflow_data = {
        "name": "Workflow Approval",
        "notificationGroupId": notification_group_id,
        "tags": ["ssflow", "approval", "workflow"],
        "description": "ワークフロー承認通知 - backend/api/services/notification_service.py で使用",
        "steps": [
            {
                "template": {
                    "type": "in_app",
                    "content": "{{content}}",
                    "subject": "{{title}}",
                    "avatar": "https://api.dicebear.com/7.x/shapes/svg?seed=workflow"
                },
                "active": True,
                "shouldStopOnFail": False,
                "filters": []
            }
        ],
        "active": True,
        "draft": False
    }
    
    print("\n📤 ワークフローを作成中...")
    
    try:
        response = requests.post(url, json=workflow_data, headers=headers)
        
        if response.status_code in [200, 201]:
            print("\n✅ ワークフロー作成成功!")
            result = response.json()
            workflow_id = result.get('data', {}).get('_id', 'N/A')
            trigger_id = result.get('data', {}).get('triggers', [{}])[0].get('identifier', 'N/A')
            
            print(f"   Workflow ID: {workflow_id}")
            print(f"   Trigger ID: {trigger_id}")
            print(f"\n💡 Backend で使用する Trigger ID: {trigger_id}")
            return True
        else:
            print(f"\n❌ 作成失敗: {response.status_code}")
            print(f"   エラー: {response.text}")
            if "already exists" in response.text.lower():
                print("\n💡 同じ名前のワークフローが既に存在します")
            return False
            
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return False


def get_user_id_by_username(username):
    """ユーザー名からユーザーIDを取得"""
    url = f"{BACKEND_API_URL}/api/users"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            users = response.json()
            for user in users:
                if user.get('username') == username or user.get('name') == username:
                    return str(user.get('id'))
            
            print(f"⚠️  ユーザー '{username}' が見つかりません")
            print("\n利用可能なユーザー:")
            for user in users[:5]:  # 最初の5人を表示
                print(f"   - {user.get('username')} (ID: {user.get('id')})")
            return None
        else:
            print(f"⚠️  ユーザー情報取得失敗: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"⚠️  Backend API接続エラー: {e}")
        print(f"   ユーザー名 '{username}' をそのまま使用します")
        return username


def send_notification(user_identifier="test_approver_001"):
    """テスト通知を送信
    
    Args:
        user_identifier: ユーザーID または ユーザー名
    """
    print("=" * 60)
    print("SSFlow 承認通知送信テスト")
    print("=" * 60)
    
    # ユーザーIDを取得（数字でない場合はユーザー名として扱う）
    if not user_identifier.isdigit():
        print(f"\nユーザー名 '{user_identifier}' からIDを検索中...")
        user_id = get_user_id_by_username(user_identifier)
        if not user_id:
            return False
        print(f"✅ ユーザーID取得: {user_id}")
    else:
        user_id = user_identifier
    
    print(f"\n使用ユーザーID: {user_id}")
    
    # サブスクライバーを作成
    print(f"\n👤 サブスクライバーを作成/確認中: {user_id}")
    if not create_subscriber(user_id):
        return False
    
    print("✅ サブスクライバー作成成功!")
    
    # 通知を送信
    print("\n" + "=" * 60)
    print("通知送信")
    print("=" * 60)
    
    url = f"{NOVU_API_URL}/v1/events/trigger"
    headers = {
        "Authorization": f"ApiKey {NOVU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": "ssflow-approval-notification",
        "to": {
            "subscriberId": user_id
        },
        "payload": {
            "title": "新しい承認リクエスト",
            "content": "山田太郎さんから新規プロジェクト承認申請の承認リクエストが届きました",
            "workflowId": "WF-2024-001",
            "flowName": "新規プロジェクト承認申請",
            "starterName": "山田太郎",
            "buttons": [
                {
                    "type": "primary",
                    "content": "詳細を確認",
                    "url": "/api/approval/session/WF-2024-001"
                },
                {
                    "type": "secondary",
                    "content": "SSFlow へ移動",
                    "url": SSFLOW_URL
                }
            ],
            "notificationType": "ssflow_approval"
        }
    }
    
    print(f"📤 SSFlow 承認通知を送信中...")
    print(f"   Subscriber: {user_id}")
    print(f"   Workflow ID: WF-2024-001")
    print(f"   Applicant: 山田太郎")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code in [200, 201]:
            print("\n✅ 通知送信成功!")
            result = response.json()
            transaction_id = result.get('data', {}).get('transactionId', 'N/A')
            print(f"   Transaction ID: {transaction_id}")
            
            # 通知を確認
            time.sleep(3)
            print("\n📬 通知を確認中...")
            check_notifications(user_id)
            
            print("\n" + "=" * 60)
            print("✅ 完了!")
            print("=" * 60)
            print("\n次のステップ:")
            print(f"1. ユーザー '{user_id}' でフロントエンドにログイン")
            print("2. 通知ベルアイコンをクリック")
            print("3. 通知とボタンが表示されることを確認")
            return True
        else:
            print(f"\n❌ 送信失敗: {response.status_code}")
            print(f"   エラー: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return False


def create_subscriber(subscriber_id):
    """サブスクライバーを作成"""
    url = f"{NOVU_API_URL}/v1/subscribers"
    headers = {
        "Authorization": f"ApiKey {NOVU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "subscriberId": subscriber_id,
        "email": f"{subscriber_id}@example.com",
        "firstName": "Test",
        "lastName": "User"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"⚠️  サブスクライバー作成エラー: {e}")
        return False


def check_notifications(subscriber_id):
    """通知を確認"""
    # Novu API の正しいエンドポイントを使用
    url = f"{NOVU_API_URL}/v1/notifications"
    headers = {
        "Authorization": f"ApiKey {NOVU_API_KEY}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            all_notifications = result.get('data', [])
            
            # 指定された subscriber_id の通知のみフィルター
            notifications = [n for n in all_notifications if n.get('to', {}).get('subscriberId') == subscriber_id]
            total = len(notifications)
            
            print(f"✅ 通知取得成功! (総数: {total})")
            
            if notifications:
                latest = notifications[0]
                payload = latest.get('payload', {})
                buttons = payload.get('buttons', [])
                
                print(f"\n📋 最新の通知:")
                print(f"   Title: {payload.get('title', 'N/A')}")
                print(f"   WorkflowId: {payload.get('workflowId', 'N/A')}")
                print(f"   ボタン数: {len(buttons)}")
                
                for i, button in enumerate(buttons, 1):
                    print(f"   ボタン{i}: {button.get('content')} ({button.get('type')})")
        else:
            print(f"⚠️  通知取得失敗: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️  通知確認エラー: {e}")


def list_workflows():
    """ワークフロー一覧を表示"""
    print("=" * 60)
    print("ワークフロー一覧")
    print("=" * 60)
    
    url = f"{NOVU_API_URL}/v1/workflows"
    headers = {
        "Authorization": f"ApiKey {NOVU_API_KEY}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            workflows = result.get('data', [])
            
            print(f"\n📋 見つかったワークフロー数: {len(workflows)}\n")
            
            for workflow in workflows:
                name = workflow.get('name', 'N/A')
                workflow_id = workflow.get('_id', 'N/A')
                triggers = workflow.get('triggers', [])
                trigger_id = triggers[0].get('identifier', 'N/A') if triggers else 'N/A'
                active = "✅" if workflow.get('active') else "❌"
                
                print(f"📌 {name}")
                print(f"   ID: {workflow_id}")
                print(f"   Trigger ID: {trigger_id}")
                print(f"   Active: {active}")
                print()
        else:
            print(f"❌ 取得失敗: {response.status_code}")
            
    except Exception as e:
        print(f"❌ エラー: {e}")


def get_notification_groups():
    """通知グループ一覧を取得"""
    url = f"{NOVU_API_URL}/v1/notification-groups"
    headers = {
        "Authorization": f"ApiKey {NOVU_API_KEY}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('data', [])
        return []
    except:
        return []


def show_help():
    """ヘルプを表示"""
    print("""
SSFlow 承認通知ツール

使用方法:
    python ssflow_tool.py <command> [options]

コマンド:
    create-workflow          ワークフローを作成（初回のみ）
    send <user_id|username>  テスト通知を送信
    list-workflows           ワークフロー一覧を表示
    help                     このヘルプを表示

例:
    # ワークフローを作成
    python ssflow_tool.py create-workflow
    
    # ユーザーID "1" に通知を送信
    python ssflow_tool.py send 1
    
    # ユーザー名 "admin" に通知を送信
    python ssflow_tool.py send admin
    
    # デフォルトユーザーに通知を送信
    python ssflow_tool.py send
    
    # ワークフロー一覧を確認
    python ssflow_tool.py list-workflows
""")


def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "create-workflow":
        create_workflow()
    elif command == "send":
        user_identifier = sys.argv[2] if len(sys.argv) > 2 else "test_approver_001"
        send_notification(user_identifier)
    elif command == "list-workflows":
        list_workflows()
    elif command == "help":
        show_help()
    else:
        print(f"❌ 不明なコマンド: {command}")
        show_help()


if __name__ == "__main__":
    main()
