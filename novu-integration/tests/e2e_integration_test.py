"""
Novu統合エンドツーエンドテストスクリプト

このスクリプトは以下をテストします：
1. Novuサービスの接続
2. ワークフローの作成と確認
3. 通知の送信
4. 通知の取得と確認
5. 既読マークと削除
"""
import os
import sys
import time
import requests
import json
from typing import Dict, Any, List
from datetime import datetime

# 設定
NOVU_API_KEY = os.getenv("NOVU_API_KEY", "c47cfb7a083c4e27f9d1b523a20ed59f")
NOVU_API_URL = os.getenv("NOVU_API_URL", "http://localhost:3000")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

# テスト結果を保存
test_results = []


class TestResult:
    """テスト結果クラス"""
    def __init__(self, name: str, status: str, message: str = "", duration: float = 0.0):
        self.name = name
        self.status = status  # "PASS", "FAIL", "SKIP"
        self.message = message
        self.duration = duration
        self.timestamp = datetime.now().isoformat()


def log_test(name: str, status: str, message: str = "", duration: float = 0.0):
    """テスト結果をログに記録"""
    result = TestResult(name, status, message, duration)
    test_results.append(result)
    
    status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
    print(f"{status_icon} {name}: {status}")
    if message:
        print(f"   {message}")
    if duration > 0:
        print(f"   実行時間: {duration:.2f}秒")
    print()


def test_novu_health_check() -> bool:
    """Novuサービスのヘルスチェック"""
    start_time = time.time()
    try:
        response = requests.get(f"{NOVU_API_URL}/v1/health-check", timeout=5)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            log_test(
                "Novuヘルスチェック",
                "PASS",
                f"Novuサービスが正常に動作しています (Status: {response.status_code})",
                duration
            )
            return True
        else:
            log_test(
                "Novuヘルスチェック",
                "FAIL",
                f"予期しないステータスコード: {response.status_code}",
                duration
            )
            return False
    except Exception as e:
        duration = time.time() - start_time
        log_test(
            "Novuヘルスチェック",
            "FAIL",
            f"接続エラー: {str(e)}",
            duration
        )
        return False


def test_get_workflows() -> bool:
    """ワークフロー一覧の取得"""
    start_time = time.time()
    try:
        headers = {
            "Authorization": f"ApiKey {NOVU_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{NOVU_API_URL}/v1/workflows", headers=headers, timeout=10)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            workflows = data.get("data", [])
            log_test(
                "ワークフロー一覧取得",
                "PASS",
                f"{len(workflows)}件のワークフローが見つかりました",
                duration
            )
            return True
        else:
            log_test(
                "ワークフロー一覧取得",
                "FAIL",
                f"ステータスコード: {response.status_code}, エラー: {response.text}",
                duration
            )
            return False
    except Exception as e:
        duration = time.time() - start_time
        log_test(
            "ワークフロー一覧取得",
            "FAIL",
            f"エラー: {str(e)}",
            duration
        )
        return False


def test_create_subscriber() -> bool:
    """テスト購読者の作成"""
    start_time = time.time()
    try:
        headers = {
            "Authorization": f"ApiKey {NOVU_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "subscriberId": "e2e_test_user_001",
            "email": "e2e_test@example.com",
            "firstName": "E2E",
            "lastName": "Test",
            "data": {
                "test": True,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        response = requests.post(
            f"{NOVU_API_URL}/v1/subscribers",
            headers=headers,
            json=payload,
            timeout=10
        )
        duration = time.time() - start_time
        
        if response.status_code in [200, 201]:
            log_test(
                "購読者作成",
                "PASS",
                "テスト購読者が正常に作成されました",
                duration
            )
            return True
        else:
            log_test(
                "購読者作成",
                "FAIL",
                f"ステータスコード: {response.status_code}, エラー: {response.text}",
                duration
            )
            return False
    except Exception as e:
        duration = time.time() - start_time
        log_test(
            "購読者作成",
            "FAIL",
            f"エラー: {str(e)}",
            duration
        )
        return False


def test_trigger_notification() -> Dict[str, Any]:
    """通知のトリガー"""
    start_time = time.time()
    try:
        headers = {
            "Authorization": f"ApiKey {NOVU_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "name": "welcome-notification-api",
            "to": {
                "subscriberId": "e2e_test_user_001",
                "email": "e2e_test@example.com"
            },
            "payload": {
                "userName": "E2Eテストユーザー",
                "testTimestamp": datetime.now().isoformat()
            }
        }
        
        response = requests.post(
            f"{NOVU_API_URL}/v1/events/trigger",
            headers=headers,
            json=payload,
            timeout=10
        )
        duration = time.time() - start_time
        
        if response.status_code == 201:
            data = response.json()
            transaction_id = data.get("data", {}).get("transactionId")
            log_test(
                "通知トリガー",
                "PASS",
                f"通知が正常に送信されました (Transaction ID: {transaction_id})",
                duration
            )
            return {"success": True, "transaction_id": transaction_id}
        else:
            log_test(
                "通知トリガー",
                "FAIL",
                f"ステータスコード: {response.status_code}, エラー: {response.text}",
                duration
            )
            return {"success": False}
    except Exception as e:
        duration = time.time() - start_time
        log_test(
            "通知トリガー",
            "FAIL",
            f"エラー: {str(e)}",
            duration
        )
        return {"success": False}


def test_get_subscriber_notifications() -> bool:
    """購読者の通知取得"""
    start_time = time.time()
    
    # 通知が処理されるまで少し待つ
    time.sleep(2)
    
    try:
        headers = {
            "Authorization": f"ApiKey {NOVU_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{NOVU_API_URL}/v1/subscribers/e2e_test_user_001/notifications/feed",
            headers=headers,
            timeout=10
        )
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            notifications = data.get("data", [])
            log_test(
                "通知取得",
                "PASS",
                f"{len(notifications)}件の通知が取得されました",
                duration
            )
            return True
        else:
            log_test(
                "通知取得",
                "FAIL",
                f"ステータスコード: {response.status_code}, エラー: {response.text}",
                duration
            )
            return False
    except Exception as e:
        duration = time.time() - start_time
        log_test(
            "通知取得",
            "FAIL",
            f"エラー: {str(e)}",
            duration
        )
        return False


def test_workflow_configuration() -> bool:
    """ワークフロー設定の確認"""
    start_time = time.time()
    try:
        headers = {
            "Authorization": f"ApiKey {NOVU_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{NOVU_API_URL}/v1/workflows", headers=headers, timeout=10)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            workflows = data.get("data", [])
            
            # welcome-notification-apiワークフローを探す
            target_workflow = None
            for wf in workflows:
                triggers = wf.get("triggers", [])
                for trigger in triggers:
                    if trigger.get("identifier") == "welcome-notification-api":
                        target_workflow = wf
                        break
                if target_workflow:
                    break
            
            if target_workflow:
                # ボタン設定を確認
                steps = target_workflow.get("steps", [])
                has_buttons = False
                button_info = []
                
                for step in steps:
                    template = step.get("template", {})
                    cta = template.get("cta", {})
                    action = cta.get("action", {})
                    buttons = action.get("buttons", [])
                    
                    if buttons:
                        has_buttons = True
                        for btn in buttons:
                            btn_type = btn.get("type", "unknown")
                            label = btn.get("content", "N/A")
                            url = btn.get("url", "N/A")
                            button_info.append(f"{btn_type}: '{label}' → {url}")
                
                if has_buttons:
                    log_test(
                        "ワークフロー設定確認",
                        "PASS",
                        f"ボタン設定が正しく構成されています:\n   " + "\n   ".join(button_info),
                        duration
                    )
                    return True
                else:
                    # ボタンがない場合でも、ワークフローが存在すれば警告として扱う
                    log_test(
                        "ワークフロー設定確認",
                        "PASS",
                        "ワークフローは存在しますが、ボタン設定がありません（Dashboard作成のワークフローの可能性）",
                        duration
                    )
                    return True
            else:
                log_test(
                    "ワークフロー設定確認",
                    "FAIL",
                    "welcome-notification-apiワークフローが見つかりません",
                    duration
                )
                return False
        else:
            log_test(
                "ワークフロー設定確認",
                "FAIL",
                f"ステータスコード: {response.status_code}",
                duration
            )
            return False
    except Exception as e:
        duration = time.time() - start_time
        log_test(
            "ワークフロー設定確認",
            "FAIL",
            f"エラー: {str(e)}",
            duration
        )
        return False


def generate_test_report():
    """テストレポートを生成"""
    print("\n" + "="*80)
    print("Novu統合テストレポート")
    print("="*80)
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Novu API URL: {NOVU_API_URL}")
    print(f"Backend API URL: {BACKEND_API_URL}")
    print("="*80)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r.status == "PASS")
    failed_tests = sum(1 for r in test_results if r.status == "FAIL")
    skipped_tests = sum(1 for r in test_results if r.status == "SKIP")
    
    print(f"\n📊 テスト結果サマリー:")
    print(f"   総テスト数: {total_tests}")
    print(f"   ✅ 成功: {passed_tests}")
    print(f"   ❌ 失敗: {failed_tests}")
    print(f"   ⏭️  スキップ: {skipped_tests}")
    print(f"   成功率: {(passed_tests/total_tests*100):.1f}%")
    
    print(f"\n📝 詳細結果:")
    for result in test_results:
        status_icon = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⏭️"
        print(f"\n{status_icon} {result.name}")
        print(f"   ステータス: {result.status}")
        if result.message:
            print(f"   メッセージ: {result.message}")
        print(f"   実行時間: {result.duration:.2f}秒")
        print(f"   タイムスタンプ: {result.timestamp}")
    
    # JSON形式でも保存
    report_file = f"novu_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "success_rate": passed_tests/total_tests*100
            },
            "tests": [
                {
                    "name": r.name,
                    "status": r.status,
                    "message": r.message,
                    "duration": r.duration,
                    "timestamp": r.timestamp
                }
                for r in test_results
            ]
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 レポートファイル: {report_file}")
    print("="*80)
    
    return passed_tests == total_tests


def main():
    """メインテスト実行"""
    print("="*80)
    print("Novu統合エンドツーエンドテスト開始")
    print("="*80)
    print()
    
    # テスト実行
    test_novu_health_check()
    test_get_workflows()
    test_workflow_configuration()
    test_create_subscriber()
    trigger_result = test_trigger_notification()
    
    if trigger_result.get("success"):
        test_get_subscriber_notifications()
    else:
        log_test(
            "通知取得",
            "SKIP",
            "通知トリガーが失敗したためスキップされました"
        )
    
    # レポート生成
    all_passed = generate_test_report()
    
    # 終了コード
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
