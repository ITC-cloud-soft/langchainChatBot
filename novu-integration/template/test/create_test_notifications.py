"""
テスト通知を作成するスクリプト
"""
import requests
import time

NOVU_API_URL = "http://localhost:3000"
NOVU_API_KEY = "c47cfb7a083c4e27f9d1b523a20ed59f"

def send_notification(subscriber_id: str, user_name: str, message_type: str = "info"):
    """
    通知を送信
    
    Args:
        subscriber_id: 購読者ID（通常はユーザーID）
        user_name: ユーザー名
        message_type: メッセージタイプ（info, success, warning, error）
    """
    headers = {
        "Authorization": f"ApiKey {NOVU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # メッセージタイプに応じた内容
    messages = {
        "info": {
            "title": "新機能のお知らせ",
            "content": f"{user_name}さん、新しい機能が追加されました。ぜひお試しください！",
            "primaryAction": {"label": "詳細を見る", "url": "/features"},
            "secondaryAction": {"label": "後で", "url": "#"}
        },
        "success": {
            "title": "処理が完了しました",
            "content": f"{user_name}さん、リクエストした処理が正常に完了しました。",
            "primaryAction": {"label": "結果を確認", "url": "/results"},
            "secondaryAction": {"label": "閉じる", "url": "#"}
        },
        "warning": {
            "title": "注意が必要です",
            "content": f"{user_name}さん、アカウントの設定を確認してください。",
            "primaryAction": {"label": "設定を確認", "url": "/settings"},
            "secondaryAction": {"label": "後で確認", "url": "#"}
        },
        "error": {
            "title": "エラーが発生しました",
            "content": f"{user_name}さん、処理中にエラーが発生しました。サポートにお問い合わせください。",
            "primaryAction": {"label": "サポート", "url": "/support"},
            "secondaryAction": {"label": "再試行", "url": "#"}
        }
    }
    
    message_data = messages.get(message_type, messages["info"])
    
    payload = {
        "name": "welcome-notification",
        "to": {"subscriberId": subscriber_id},
        "payload": {
            "userName": user_name,
            "title": message_data["title"],
            "content": message_data["content"],
            "primaryAction": message_data["primaryAction"],
            "secondaryAction": message_data["secondaryAction"],
            "redirectUrl": "/dashboard"
        }
    }
    
    try:
        response = requests.post(
            f"{NOVU_API_URL}/v1/events/trigger",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 201:
            result = response.json()
            transaction_id = result.get('data', {}).get('transactionId', 'N/A')
            print(f"✅ [{message_type.upper()}] 通知送信成功: {message_data['title']}")
            print(f"   Transaction ID: {transaction_id}")
            return True
        else:
            print(f"❌ [{message_type.upper()}] 送信失敗: {response.status_code}")
            print(f"   エラー: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def main():
    print("=" * 70)
    print("テスト通知作成スクリプト")
    print("=" * 70)
    
    # テスト用のユーザーID（通常は実際のユーザーIDを使用）
    subscriber_id = "1"  # adminユーザーのID
    user_name = "Admin User"
    
    print(f"\n📤 ユーザー '{user_name}' (ID: {subscriber_id}) に通知を送信します...\n")
    
    # 様々なタイプの通知を作成
    notifications = [
        ("info", "情報通知"),
        ("success", "成功通知"),
        ("warning", "警告通知"),
        ("error", "エラー通知"),
        ("info", "追加の情報通知")
    ]
    
    success_count = 0
    for i, (msg_type, description) in enumerate(notifications, 1):
        print(f"\n【{i}/{len(notifications)}】{description}を送信中...")
        if send_notification(subscriber_id, user_name, msg_type):
            success_count += 1
        
        # API負荷を避けるため少し待機
        if i < len(notifications):
            time.sleep(1)
    
    # 結果サマリー
    print("\n" + "=" * 70)
    print("送信結果")
    print("=" * 70)
    print(f"\n総送信数: {len(notifications)}")
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失敗: {len(notifications) - success_count}")
    
    if success_count == len(notifications):
        print("\n🎉 全ての通知が正常に送信されました！")
        print("\n次のステップ:")
        print("1. ブラウザで http://localhost:3001 にアクセス")
        print("2. admin/admin123 でログイン")
        print("3. 右上の通知ベルアイコンをクリック")
        print("4. 送信された通知を確認")
    else:
        print("\n⚠️  一部の通知の送信に失敗しました")


if __name__ == "__main__":
    main()
