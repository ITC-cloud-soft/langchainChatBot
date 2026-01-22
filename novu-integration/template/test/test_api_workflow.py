"""
API経由で作成したワークフローをテストするスクリプト
"""

import requests
import os

NOVU_API_KEY = os.getenv("NOVU_API_KEY", "c47cfb7a083c4e27f9d1b523a20ed59f")
NOVU_API_URL = os.getenv("NOVU_API_URL", "http://localhost:3000")


def trigger_api_workflow(user_id: str, user_name: str, user_email: str):
    """API作成のワークフローをトリガー"""
    
    url = f"{NOVU_API_URL}/v1/events/trigger"
    
    headers = {
        "Authorization": f"ApiKey {NOVU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": "welcome-notification-api",  # API作成のワークフロー識別子
        "to": {
            "subscriberId": user_id,
            "email": user_email
        },
        "payload": {
            "userName": user_name
        }
    }
    
    print(f"\n📤 API作成ワークフローをトリガー中...")
    print(f"   Workflow: welcome-notification-api")
    print(f"   User ID: {user_id}")
    print(f"   User Name: {user_name}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            print(f"\n✅ 通知送信成功!")
            result = response.json()
            print(f"   Transaction ID: {result.get('data', {}).get('transactionId', 'N/A')}")
            return result
        else:
            print(f"\n❌ 送信失敗: {response.status_code}")
            print(f"   エラー: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return None


def main():
    print("=" * 60)
    print("API作成ワークフローテスト")
    print("=" * 60)
    
    # テスト送信
    result = trigger_api_workflow(
        user_id="test-user-api-001",
        user_name="API测试用户",
        user_email="api-test@example.com"
    )
    
    if result:
        print("\n" + "=" * 60)
        print("✅ テスト成功!")
        print("=" * 60)
        print("\n💡 重要な違い:")
        print("   - このワークフローはAPIで作成されました")
        print("   - CTA（ボタン）設定が含まれています:")
        print("     • Primary: '开始使用' → /getting-started")
        print("     • Secondary: '查看教程' → /tutorials")
        print("     • Redirect: /dashboard")
        print("\n📊 確認方法:")
        print("   1. Dashboard (http://localhost:4200) → Activity Feed")
        print("   2. この通知を確認")
        print("   3. ボタンが正しく表示されるか確認")


if __name__ == "__main__":
    main()
