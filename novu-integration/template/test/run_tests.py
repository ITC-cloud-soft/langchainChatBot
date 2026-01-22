"""
Novu通知システム統合テストスイート

使用方法:
    python run_tests.py              # 全てのテストを実行
    python run_tests.py --quick      # クイックテスト（通知機能のみ）
    python run_tests.py --workflow   # ワークフローテストのみ
"""

import requests
import time
import sys
import argparse
from typing import Optional

# 設定
BACKEND_URL = "http://localhost:8000"
NOVU_API_URL = "http://localhost:3000"
NOVU_API_KEY = "c47cfb7a083c4e27f9d1b523a20ed59f"


class TestRunner:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
    
    def login(self) -> bool:
        """バックエンドにログイン"""
        print("\n🔐 ログイン中...")
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/auth/login",
                json={"username": "admin", "password": "admin123"}
            )
            
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                print("✅ ログイン成功")
                return True
            else:
                print(f"❌ ログイン失敗: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ ログインエラー: {e}")
            return False
    
    def test_notification_list(self) -> bool:
        """通知リスト取得テスト"""
        print("\n【テスト1】通知リスト取得")
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/notifications/?page=0&limit=10",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                count = len(data.get('data', []))
                print(f"✅ 成功: {count}件の通知を取得")
                self.test_results.append(("通知リスト取得", True, count))
                return True
            else:
                print(f"❌ 失敗: {response.status_code}")
                self.test_results.append(("通知リスト取得", False, response.status_code))
                return False
        except Exception as e:
            print(f"❌ エラー: {e}")
            self.test_results.append(("通知リスト取得", False, str(e)))
            return False
    
    def test_unread_count(self) -> bool:
        """未読数取得テスト"""
        print("\n【テスト2】未読数取得")
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/notifications/unread-count",
                headers=self.headers
            )
            
            if response.status_code == 200:
                count = response.json().get('unread', 0)
                print(f"✅ 成功: 未読数 {count}件")
                self.test_results.append(("未読数取得", True, count))
                return True
            else:
                print(f"❌ 失敗: {response.status_code}")
                self.test_results.append(("未読数取得", False, response.status_code))
                return False
        except Exception as e:
            print(f"❌ エラー: {e}")
            self.test_results.append(("未読数取得", False, str(e)))
            return False
    
    def test_mark_as_read(self) -> bool:
        """既読マークテスト"""
        print("\n【テスト3】既読マーク")
        try:
            # 通知を取得
            response = requests.get(
                f"{BACKEND_URL}/api/notifications/?page=0&limit=1",
                headers=self.headers
            )
            
            if response.status_code != 200:
                print("⚠️  スキップ: 通知が取得できません")
                self.test_results.append(("既読マーク", None, "通知なし"))
                return True
            
            notifications = response.json().get('data', [])
            if not notifications:
                print("⚠️  スキップ: 通知が0件です")
                self.test_results.append(("既読マーク", None, "通知なし"))
                return True
            
            notification_id = notifications[0].get('_id')
            
            # 既読マーク
            mark_response = requests.post(
                f"{BACKEND_URL}/api/notifications/{notification_id}/read",
                headers=self.headers
            )
            
            if mark_response.status_code == 200:
                print(f"✅ 成功: 通知 {notification_id[:8]}... を既読にマーク")
                self.test_results.append(("既読マーク", True, notification_id[:8]))
                return True
            else:
                print(f"❌ 失敗: {mark_response.status_code}")
                self.test_results.append(("既読マーク", False, mark_response.status_code))
                return False
        except Exception as e:
            print(f"❌ エラー: {e}")
            self.test_results.append(("既読マーク", False, str(e)))
            return False
    
    def test_mark_all_read(self) -> bool:
        """全既読マークテスト"""
        print("\n【テスト4】全通知既読マーク")
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/notifications/mark-all-read",
                headers=self.headers
            )
            
            if response.status_code == 200:
                print("✅ 成功: 全通知を既読にマーク")
                self.test_results.append(("全既読マーク", True, "OK"))
                return True
            else:
                print(f"❌ 失敗: {response.status_code}")
                self.test_results.append(("全既読マーク", False, response.status_code))
                return False
        except Exception as e:
            print(f"❌ エラー: {e}")
            self.test_results.append(("全既読マーク", False, str(e)))
            return False
    
    def test_delete_notification(self) -> bool:
        """通知削除テスト"""
        print("\n【テスト5】通知削除")
        try:
            # 通知を取得
            response = requests.get(
                f"{BACKEND_URL}/api/notifications/?page=0&limit=1",
                headers=self.headers
            )
            
            if response.status_code != 200:
                print("⚠️  スキップ: 通知が取得できません")
                self.test_results.append(("通知削除", None, "通知なし"))
                return True
            
            notifications = response.json().get('data', [])
            if not notifications:
                print("⚠️  スキップ: 通知が0件です")
                self.test_results.append(("通知削除", None, "通知なし"))
                return True
            
            notification_id = notifications[0].get('_id')
            
            # 削除
            delete_response = requests.delete(
                f"{BACKEND_URL}/api/notifications/{notification_id}",
                headers=self.headers
            )
            
            if delete_response.status_code == 200:
                print(f"✅ 成功: 通知 {notification_id[:8]}... を削除")
                self.test_results.append(("通知削除", True, notification_id[:8]))
                return True
            else:
                print(f"❌ 失敗: {delete_response.status_code}")
                self.test_results.append(("通知削除", False, delete_response.status_code))
                return False
        except Exception as e:
            print(f"❌ エラー: {e}")
            self.test_results.append(("通知削除", False, str(e)))
            return False
    
    def test_send_notification(self) -> bool:
        """通知送信テスト"""
        print("\n【テスト6】通知送信（Novu API）")
        try:
            headers = {
                "Authorization": f"ApiKey {NOVU_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "name": "welcome-notification",
                "to": {"subscriberId": "1"},
                "payload": {
                    "userName": "Test User",
                    "primaryAction": {"label": "开始使用", "url": "/dashboard"},
                    "secondaryAction": {"label": "查看教程", "url": "/tutorials"},
                    "redirectUrl": "/dashboard"
                }
            }
            
            response = requests.post(
                f"{NOVU_API_URL}/v1/events/trigger",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 201:
                transaction_id = response.json().get('data', {}).get('transactionId', 'N/A')
                print(f"✅ 成功: Transaction ID {transaction_id[:8]}...")
                self.test_results.append(("通知送信", True, transaction_id[:8]))
                return True
            else:
                print(f"❌ 失敗: {response.status_code}")
                self.test_results.append(("通知送信", False, response.status_code))
                return False
        except Exception as e:
            print(f"❌ エラー: {e}")
            self.test_results.append(("通知送信", False, str(e)))
            return False
    
    def print_summary(self):
        """テスト結果サマリーを表示"""
        print("\n" + "=" * 70)
        print("テスト結果サマリー")
        print("=" * 70)
        
        passed = sum(1 for _, result, _ in self.test_results if result is True)
        failed = sum(1 for _, result, _ in self.test_results if result is False)
        skipped = sum(1 for _, result, _ in self.test_results if result is None)
        total = len(self.test_results)
        
        print(f"\n総テスト数: {total}")
        print(f"✅ 成功: {passed}")
        print(f"❌ 失敗: {failed}")
        print(f"⚠️  スキップ: {skipped}")
        
        if failed == 0:
            print("\n🎉 全てのテストが成功しました！")
            return True
        else:
            print(f"\n⚠️  {failed}件のテストが失敗しました")
            print("\n失敗したテスト:")
            for name, result, detail in self.test_results:
                if result is False:
                    print(f"  ❌ {name}: {detail}")
            return False


def run_quick_tests():
    """クイックテスト（通知機能のみ）"""
    print("=" * 70)
    print("Novu通知システム - クイックテスト")
    print("=" * 70)
    
    runner = TestRunner()
    
    if not runner.login():
        sys.exit(1)
    
    runner.test_notification_list()
    runner.test_unread_count()
    runner.test_mark_as_read()
    
    success = runner.print_summary()
    sys.exit(0 if success else 1)


def run_full_tests():
    """全テスト実行"""
    print("=" * 70)
    print("Novu通知システム - 全機能テスト")
    print("=" * 70)
    
    runner = TestRunner()
    
    if not runner.login():
        sys.exit(1)
    
    # 通知送信テスト
    runner.test_send_notification()
    
    # 処理待機
    print("\n⏳ 通知処理を待機中（3秒）...")
    time.sleep(3)
    
    # 通知機能テスト
    runner.test_notification_list()
    runner.test_unread_count()
    runner.test_mark_as_read()
    runner.test_mark_all_read()
    runner.test_delete_notification()
    
    success = runner.print_summary()
    
    if success:
        print("\n📝 次のステップ:")
        print("  1. ブラウザで http://localhost:3001 にアクセス")
        print("  2. admin/admin123 でログイン")
        print("  3. 通知ベルアイコンをクリックしてUIをテスト")
    
    sys.exit(0 if success else 1)


def run_workflow_tests():
    """ワークフローテストのみ"""
    print("=" * 70)
    print("Novu ワークフローテスト")
    print("=" * 70)
    
    print("\n💡 ワークフローテストは個別のスクリプトを使用してください:")
    print("  - test_welcome_workflow.py  : Welcome通知ワークフロー")
    print("  - test_api_workflow.py      : API作成ワークフロー")


def main():
    parser = argparse.ArgumentParser(description='Novu通知システムテストスイート')
    parser.add_argument('--quick', action='store_true', help='クイックテスト（通知機能のみ）')
    parser.add_argument('--workflow', action='store_true', help='ワークフローテスト情報を表示')
    
    args = parser.parse_args()
    
    if args.quick:
        run_quick_tests()
    elif args.workflow:
        run_workflow_tests()
    else:
        run_full_tests()


if __name__ == "__main__":
    main()
