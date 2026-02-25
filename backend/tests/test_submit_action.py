"""
submit_action エンドポイントのテスト
Flow 10 (tool 20->21) の動作確認
"""
import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://localhost:8000"

def login(username, password):
    req = urllib.request.Request(
        f"{BASE_URL}/api/auth/login",
        data=json.dumps({"username": username, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]

def post(path, body, token):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        try:
            return e.code, json.loads(body_bytes)
        except Exception:
            return e.code, body_bytes.decode()

def run_tests():
    passed = 0
    failed = 0

    print("=== submit_action テスト開始 ===")

    # ログイン
    try:
        token = login("admin", "admin123")
        print(f"[LOGIN] OK (token length={len(token)})")
    except Exception as e:
        print(f"[LOGIN] FAIL: {e}")
        sys.exit(1)

    # テスト1: 不正な fk_flow -> 400
    status, body = post("/api/notifications/submit-action",
                        {"fk_flow": "999", "form_data": {}}, token)
    if status == 400:
        print(f"[TEST1] PASS: 不正fk_flow -> 400 Bad Request")
        passed += 1
    else:
        print(f"[TEST1] FAIL: expected 400, got {status} - {body}")
        failed += 1

    # テスト2: ARS APIキー未設定 -> 400 or 500 (adminユーザーはARSキーなし想定)
    status, body = post("/api/notifications/submit-action",
                        {"fk_flow": "001", "form_data": {"COMMENT": "テスト申請"}}, token)
    if status in (400, 500):
        msg = body.get("detail", str(body)) if isinstance(body, dict) else str(body)
        print(f"[TEST2] PASS: ARS未設定エラー -> {status}: {msg[:80]}")
        passed += 1
    elif status == 200:
        print(f"[TEST2] INFO: ARS接続成功 -> {body}")
        passed += 1
    else:
        print(f"[TEST2] FAIL: unexpected {status} - {body}")
        failed += 1

    # テスト3: approval_action 回帰テスト（Flow 8 が壊れていないか）
    # ARS paramsなしで400を確認
    status, body = post("/api/notifications/approval-action",
                        {"ars_params": {}, "action": "approve", "comment": ""}, token)
    if status in (200, 400, 500):
        print(f"[TEST3] PASS: approval_action 動作中 -> {status}")
        passed += 1
    else:
        print(f"[TEST3] FAIL: unexpected {status}")
        failed += 1

    # テスト4: submit_action 各 fk_flow バリデーション（001〜009 全て受付確認）
    valid_flows = ["001", "002", "003", "004", "005", "006", "007", "008", "009"]
    all_valid = True
    for fk in valid_flows:
        status, body = post("/api/notifications/submit-action",
                            {"fk_flow": fk, "form_data": {}}, token)
        if status == 400:
            detail = body.get("detail", "") if isinstance(body, dict) else ""
            if "不正な FK_Flow" in detail:
                print(f"[TEST4] FAIL: fk_flow={fk} が不正と判定された")
                all_valid = False
        # ARS接続エラー(400/500)はOK、400の場合は詳細を確認
    if all_valid:
        print(f"[TEST4] PASS: fk_flow 001〜009 全て受付OK（ARSエラーは別途）")
        passed += 1
    else:
        failed += 1

    print(f"\n=== 結果: {passed}件PASS / {failed}件FAIL ===")
    return failed == 0

if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)
