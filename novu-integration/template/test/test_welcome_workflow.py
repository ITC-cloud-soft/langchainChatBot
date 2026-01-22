"""
Novu Welcome Notification Workflow テストスクリプト

このスクリプトは、welcome-notification ワークフローをテストするために使用します。
"""

import requests
import os
import sys
from typing import Optional

# 設定
NOVU_API_KEY = os.getenv("NOVU_API_KEY", "c47cfb7a083c4e27f9d1b523a20ed59f")
NOVU_API_URL = os.getenv("NOVU_API_URL", "http://localhost:3000")


def trigger_welcome_notification(
    user_id: str, 
    user_name: str, 
    user_email: str
) -> Optional[dict]:
    """ウェルカム通知をトリガー
    
    Args:
        user_id: ユーザーID (subscriberId)
        user_name: ユーザー名 (通知内容に表示)
        user_email: ユーザーメールアドレス
        
    Returns:
        APIレスポンス (成功時) または None (失敗時)
    """
    
    if not NOVU_API_KEY:
        print("❌ エラー: NOVU_API_KEY が設定されていません")
        print("環境変数を設定するか、.env ファイルに追加してください:")
        print('  export NOVU_API_KEY="novu_xxxxxx"')
        return None
    
    url = f"{NOVU_API_URL}/v1/events/trigger"
    
    headers = {
        "Authorization": f"ApiKey {NOVU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": "welcome-notification",
        "to": {
            "subscriberId": user_id,
            "email": user_email
        },
        "payload": {
            "userName": user_name,
            "primaryAction": {
                "label": "开始使用",
                "url": "/getting-started"
            },
            "secondaryAction": {
                "label": "查看教程",
                "url": "/tutorials"
            },
            "redirectUrl": "/dashboard"
        }
    }
    
    print(f"\n📤 通知を送信中...")
    print(f"   Workflow: welcome-notification")
    print(f"   User ID: {user_id}")
    print(f"   User Name: {user_name}")
    print(f"   Email: {user_email}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            print(f"\n✅ 通知送信成功!")
            result = response.json()
            print(f"   Transaction ID: {result.get('data', {}).get('transactionId', 'N/A')}")
            print(f"\n📊 レスポンス:")
            print(f"   {result}")
            return result
        else:
            print(f"\n❌ 送信失敗: {response.status_code}")
            print(f"   エラー: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 接続エラー: Novu API に接続できません")
        print(f"   URL: {NOVU_API_URL}")
        print(f"   Novu サービスが起動しているか確認してください:")
        print(f"   docker-compose -f docker-compose.novu.yml ps")
        return None
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        return None


def check_novu_health() -> bool:
    """Novu API のヘルスチェック
    
    Returns:
        True if healthy, False otherwise
    """
    try:
        url = f"{NOVU_API_URL}/v1/health-check"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Novu API は正常に動作しています ({NOVU_API_URL})")
            return True
        else:
            print(f"⚠️  Novu API が異常なステータスを返しました: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Novu API に接続できません: {NOVU_API_URL}")
        print(f"   Novu サービスが起動しているか確認してください")
        return False
    except Exception as e:
        print(f"❌ ヘルスチェックエラー: {e}")
        return False


def main():
    """メイン実行関数"""
    
    print("=" * 60)
    print("Novu Welcome Notification Workflow テスト")
    print("=" * 60)
    
    # ヘルスチェック
    print("\n🔍 Novu API ヘルスチェック...")
    if not check_novu_health():
        print("\n⚠️  Novu API が利用できません。テストを中止します。")
        sys.exit(1)
    
    # テストケース1: 基本的な通知
    print("\n" + "=" * 60)
    print("テストケース 1: 基本的なウェルカム通知")
    print("=" * 60)
    
    result1 = trigger_welcome_notification(
        user_id="test-user-001",
        user_name="張三",
        user_email="zhangsan@example.com"
    )
    
    # テストケース2: 別のユーザー
    print("\n" + "=" * 60)
    print("テストケース 2: 別のユーザー")
    print("=" * 60)
    
    result2 = trigger_welcome_notification(
        user_id="test-user-002",
        user_name="李四",
        user_email="lisi@example.com"
    )
    
    # テストケース3: 英語名のユーザー
    print("\n" + "=" * 60)
    print("テストケース 3: 英語名のユーザー")
    print("=" * 60)
    
    result3 = trigger_welcome_notification(
        user_id="test-user-003",
        user_name="John Doe",
        user_email="john.doe@example.com"
    )
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    
    success_count = sum([1 for r in [result1, result2, result3] if r is not None])
    total_count = 3
    
    print(f"\n成功: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n✅ すべてのテストが成功しました!")
        print("\n次のステップ:")
        print("1. Novu Dashboard (http://localhost:4200) にアクセス")
        print("2. 左側メニューの 'Activity Feed' をクリック")
        print("3. 送信された通知を確認")
        print("\nまたは、フロントエンドアプリで通知ベルアイコンを確認してください。")
    else:
        print(f"\n⚠️  {total_count - success_count} 件のテストが失敗しました")
        print("\nトラブルシューティング:")
        print("1. NOVU_API_KEY が正しく設定されているか確認")
        print("2. Workflow Identifier が 'welcome-notification' であることを確認")
        print("3. Dashboard で workflow が Active になっているか確認")
        sys.exit(1)


if __name__ == "__main__":
    main()
