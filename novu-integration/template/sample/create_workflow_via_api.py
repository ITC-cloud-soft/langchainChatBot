"""
Novu Workflow を API 経由で作成するスクリプト

Dashboard の UI 制限を回避し、完全な設定（Action ボタン、Redirect URL など）を含む
ワークフローをプログラムで作成します。
"""

import requests
import os
import json

# 設定
NOVU_API_KEY = os.getenv("NOVU_API_KEY", "c47cfb7a083c4e27f9d1b523a20ed59f")
NOVU_API_URL = os.getenv("NOVU_API_URL", "http://localhost:3000")


def create_welcome_workflow(notification_group_id: str = None):
    """ウェルカム通知ワークフローを API 経由で作成
    
    Args:
        notification_group_id: 通知グループID（指定しない場合は自動取得）
    """
    
    # 通知グループIDが指定されていない場合は取得
    if not notification_group_id:
        groups = get_notification_groups()
        if groups:
            notification_group_id = groups[0].get('_id')
        else:
            print("❌ 通知グループが見つかりません")
            return None
    
    url = f"{NOVU_API_URL}/v1/workflows"
    
    headers = {
        "Authorization": f"ApiKey {NOVU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 完全なワークフロー定義
    workflow_data = {
        "name": "Welcome Notification API",
        "notificationGroupId": notification_group_id,
        "tags": ["onboarding", "welcome"],
        "description": "新用户欢迎通知 - 包含完整的 Action 按钮配置",
        "steps": [
            {
                "template": {
                    "type": "in_app",
                    "content": "{{userName}}，很高兴你加入我们。点击下方按钮开始探索!",
                    "subject": "欢迎来到我们的平台!",
                    "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed={{userName}}",
                    "cta": {
                        "type": "redirect",
                        "data": {
                            "url": "/dashboard"
                        },
                        "action": {
                            "buttons": [
                                {
                                    "type": "primary",
                                    "content": "开始使用",
                                    "url": "/getting-started"
                                },
                                {
                                    "type": "secondary", 
                                    "content": "查看教程",
                                    "url": "/tutorials"
                                }
                            ]
                        }
                    }
                },
                "active": True,
                "shouldStopOnFail": False,
                "filters": []
            }
        ],
        "active": True,
        "draft": False,
        "critical": False,
        "preferenceSettings": {
            "email": True,
            "sms": True,
            "in_app": True,
            "chat": True,
            "push": True
        }
    }
    
    print("📤 ワークフローを作成中...")
    print(f"   Name: {workflow_data['name']}")
    print(f"   Description: {workflow_data['description']}")
    
    try:
        response = requests.post(url, json=workflow_data, headers=headers)
        
        if response.status_code in [200, 201]:
            print("\n✅ ワークフロー作成成功!")
            result = response.json()
            workflow_id = result.get('data', {}).get('_id', 'N/A')
            print(f"   Workflow ID: {workflow_id}")
            print(f"\n📊 レスポンス:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return result
        else:
            print(f"\n❌ 作成失敗: {response.status_code}")
            print(f"   エラー: {response.text}")
            
            # エラーが既存のワークフローの場合
            if "already exists" in response.text.lower() or response.status_code == 409:
                print("\n💡 ヒント: 同じ名前のワークフローが既に存在します")
                print("   Dashboard で既存のワークフローを削除するか、")
                print("   update_workflow_via_api.py を使用して更新してください")
            
            return None
            
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        return None


def get_notification_groups():
    """通知グループ一覧を取得（ワークフロー作成に必要）"""
    
    url = f"{NOVU_API_URL}/v1/notification-groups"
    
    headers = {
        "Authorization": f"ApiKey {NOVU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            groups = result.get('data', [])
            
            print("\n📋 利用可能な通知グループ:")
            for group in groups:
                print(f"   - {group.get('name')}: {group.get('_id')}")
            
            return groups
        else:
            print(f"⚠️  グループ取得失敗: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return []


def update_existing_workflow(workflow_id: str):
    """既存のワークフローを更新
    
    Args:
        workflow_id: 更新するワークフローの ID
    """
    
    url = f"{NOVU_API_URL}/v1/workflows/{workflow_id}"
    
    headers = {
        "Authorization": f"ApiKey {NOVU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 更新データ（作成時と同じ構造）
    update_data = {
        "name": "Welcome Notification",
        "tags": ["onboarding", "welcome"],
        "description": "新用户欢迎通知 - 包含完整的 Action 按钮配置",
        "steps": [
            {
                "template": {
                    "type": "in_app",
                    "content": "{{userName}}，很高兴你加入我们。点击下方按钮开始探索!",
                    "subject": "欢迎来到我们的平台!",
                    "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed={{userName}}",
                    "cta": {
                        "type": "redirect",
                        "data": {
                            "url": "/dashboard"
                        },
                        "action": {
                            "buttons": [
                                {
                                    "type": "primary",
                                    "content": "开始使用",
                                    "url": "/getting-started"
                                },
                                {
                                    "type": "secondary",
                                    "content": "查看教程",
                                    "url": "/tutorials"
                                }
                            ]
                        }
                    }
                },
                "active": True
            }
        ],
        "active": True
    }
    
    print(f"\n📤 ワークフローを更新中...")
    print(f"   Workflow ID: {workflow_id}")
    
    try:
        response = requests.put(url, json=update_data, headers=headers)
        
        if response.status_code == 200:
            print("\n✅ ワークフロー更新成功!")
            result = response.json()
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return result
        else:
            print(f"\n❌ 更新失敗: {response.status_code}")
            print(f"   エラー: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        return None


def main():
    """メイン実行関数"""
    
    print("=" * 60)
    print("Novu Workflow API 経由作成")
    print("=" * 60)
    
    # 通知グループを取得
    print("\n🔍 通知グループを確認中...")
    groups = get_notification_groups()
    
    if not groups:
        print("\n⚠️  通知グループが見つかりません")
        print("   デフォルトグループを使用します")
    
    # ワークフローを作成
    print("\n" + "=" * 60)
    print("ワークフロー作成")
    print("=" * 60)
    
    result = create_welcome_workflow()
    
    if result:
        print("\n" + "=" * 60)
        print("✅ 完了!")
        print("=" * 60)
        print("\n次のステップ:")
        print("1. Dashboard (http://localhost:4200) で新しいワークフローを確認")
        print("2. test_welcome_workflow.py を実行してテスト")
        print("3. Activity Feed で通知を確認")
    else:
        print("\n" + "=" * 60)
        print("⚠️  作成に失敗しました")
        print("=" * 60)
        print("\nトラブルシューティング:")
        print("1. Dashboard で既存の 'Welcome Notification' を削除")
        print("2. または、update_existing_workflow() を使用して更新")


if __name__ == "__main__":
    main()
