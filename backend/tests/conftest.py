"""
テスト共通設定・ユーティリティ

全テストから共通で使用するヘルパー関数・定数・フィクスチャを定義する。
機能別テストはサブディレクトリに配置し、このファイルをインポートして使用する。

ディレクトリ構成:
  tests/
    conftest.py                  ← 共通設定（このファイル）
    run_all.py                   ← 全テスト一括実行
    upload/                      ← ファイルアップロード機能
      test_upload_validation.py
      test_upload_success.py
      test_upload_auth.py
    notification/                ← 通知・承認機能
      test_novu_integration.py
    flow/                        ← ARS Flow 申請機能
      test_submit_action.py
"""

import os
import json
import urllib.request
import urllib.error
from typing import Tuple

# ──────────────────────────────────────────────
# 共通設定
# ──────────────────────────────────────────────
BASE_URL  = os.getenv("TEST_BASE_URL", "http://127.0.0.1:8000")
TEST_USER = os.getenv("TEST_USER", "admin")
TEST_PASS = os.getenv("TEST_PASS", "admin123")


# ──────────────────────────────────────────────
# HTTP ヘルパー
# ──────────────────────────────────────────────

def login(username: str = TEST_USER, password: str = TEST_PASS) -> str:
    """ログインしてアクセストークンを取得する。"""
    req = urllib.request.Request(
        f"{BASE_URL}/api/auth/login",
        data=json.dumps({"username": username, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["access_token"]


def http_get(path: str, token: str) -> Tuple[int, dict]:
    """GET リクエストを送信する。"""
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}


def http_post(path: str, body: dict, token: str) -> Tuple[int, dict]:
    """JSON POST リクエストを送信する。"""
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}


def http_upload(
    path: str,
    token: str,
    filename: str,
    content: bytes,
    content_type: str = "application/octet-stream",
) -> Tuple[int, dict]:
    """multipart/form-data でファイルをアップロードする。"""
    boundary = "----TestBoundary1234567890"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n"
        f"\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}


# ──────────────────────────────────────────────
# テスト結果集計
# ──────────────────────────────────────────────

class TestResult:
    """テスト結果を集計するクラス。"""

    def __init__(self, suite_name: str = ""):
        self.suite_name = suite_name
        self.passed = 0
        self.failed = 0
        self._verbose = "--verbose" in __import__("sys").argv

    def ok(self, name: str, detail: str = ""):
        self.passed += 1
        suffix = f" ({detail})" if detail and self._verbose else ""
        print(f"  [PASS] {name}{suffix}")

    def fail(self, name: str, detail: str = ""):
        self.failed += 1
        print(f"  [FAIL] {name}: {detail}")

    def skip(self, name: str, reason: str = ""):
        print(f"  [SKIP] {name}: {reason}")

    @property
    def total(self):
        return self.passed + self.failed

    def summary(self) -> bool:
        label = f" ({self.suite_name})" if self.suite_name else ""
        print(f"  --- {self.passed}件PASS / {self.failed}件FAIL{label} ---")
        return self.failed == 0
