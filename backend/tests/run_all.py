"""
全テスト一括実行エントリーポイント

使い方:
  python tests/run_all.py                  # 全テスト実行
  python tests/run_all.py --verbose        # 詳細出力
  python tests/run_all.py --suite upload   # upload スイートのみ実行
  python tests/run_all.py --suite flow     # flow スイートのみ実行

環境変数:
  TEST_BASE_URL  : バックエンドURL (デフォルト: http://localhost:8000)
  TEST_USER      : テストユーザー名 (デフォルト: admin)
  TEST_PASS      : テストパスワード (デフォルト: admin123)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tests.conftest import login, TestResult

# ──────────────────────────────────────────────
# スイート登録
# スイートを追加する場合はここに追記するだけでOK
# ──────────────────────────────────────────────

def get_suites():
    """
    利用可能テストスイート一覧を返す。
    新機能追加時はここに (suite_name, runner_func) を追加する。

    runner_func シグネチャ:
      - 認証不要スイート: run(result: TestResult) -> None
      - 認証必要スイート: run(token: str, result: TestResult) -> None
    """
    from tests.upload.test_upload_auth       import TestUploadAuth
    from tests.upload.test_upload_validation import TestUploadValidation
    from tests.upload.test_upload_success    import TestUploadSuccess
    from tests.flow.test_submit_action       import TestSubmitAction

    return [
        # (スイート名, テストクラスインスタンス, 認証が必要か)
        ("upload/auth",       TestUploadAuth(),       False),
        ("upload/validation", TestUploadValidation(), True),
        ("upload/success",    TestUploadSuccess(),    True),
        ("flow/submit",       TestSubmitAction(),     True),
        # 将来追加例:
        # ("notification/novu", TestNovuIntegration(), True),
        # ("chat/history",      TestChatHistory(),     True),
    ]


def run_all(suite_filter: str = None) -> bool:
    total_result = TestResult("ALL")

    print(f"=== テスト一括実行開始 (BASE_URL={os.getenv('TEST_BASE_URL', 'http://localhost:8000')}) ===")

    # ログイン（認証必要スイート用）
    token = None
    try:
        token = login()
        print(f"[LOGIN] OK\n")
    except Exception as e:
        print(f"[LOGIN] FAIL: {e}")
        sys.exit(1)

    suites = get_suites()
    if suite_filter:
        suites = [(n, t, a) for n, t, a in suites if suite_filter in n]
        if not suites:
            print(f"スイート '{suite_filter}' が見つかりません")
            sys.exit(1)

    for suite_name, tester, needs_auth in suites:
        print(f"\n{'='*50}")
        print(f"Suite: {suite_name}")
        print(f"{'='*50}")
        r = TestResult(suite_name)
        try:
            if needs_auth:
                tester.run(token, r)
            else:
                tester.run(r)
        except Exception as e:
            r.fail(f"[UNEXPECTED ERROR]", str(e))

        r.summary()
        total_result.passed += r.passed
        total_result.failed += r.failed

    print(f"\n{'='*50}")
    print(f"全体結果: {total_result.passed}件PASS / {total_result.failed}件FAIL / 計{total_result.total}件")
    print(f"{'='*50}")
    return total_result.failed == 0


if __name__ == "__main__":
    suite_filter = None
    args = sys.argv[1:]
    if "--suite" in args:
        idx = args.index("--suite")
        if idx + 1 < len(args):
            suite_filter = args[idx + 1]

    ok = run_all(suite_filter)
    sys.exit(0 if ok else 1)
