"""
アップロード認証テスト

未認証・無効トークンのリクエストが適切に拒否されることを確認する。
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import urllib.request
import urllib.error
from tests.conftest import BASE_URL, TestResult


class TestUploadAuth:
    """認証・認可テスト"""

    def run(self, result: TestResult):
        print("\n[TestUploadAuth]")
        self._test_no_token(result)
        self._test_invalid_token(result)

    def _test_no_token(self, result: TestResult):
        """トークンなしでアップロード → 401/403"""
        boundary = "----TestBoundary"
        body_bytes = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="test.pdf"\r\n'
            f"Content-Type: application/pdf\r\n\r\n"
        ).encode() + b"fake" + f"\r\n--{boundary}--\r\n".encode()

        req = urllib.request.Request(
            f"{BASE_URL}/api/upload/file",
            data=body_bytes,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                result.fail("未認証リクエスト", f"expected 401/403 but got {resp.status}")
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 422):
                result.ok(f"未認証リクエスト → {e.code}")
            else:
                result.fail("未認証リクエスト", f"unexpected {e.code}")

    def _test_invalid_token(self, result: TestResult):
        """無効トークンでアップロード → 401"""
        boundary = "----TestBoundary"
        body_bytes = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="test.pdf"\r\n'
            f"Content-Type: application/pdf\r\n\r\n"
        ).encode() + b"fake" + f"\r\n--{boundary}--\r\n".encode()

        req = urllib.request.Request(
            f"{BASE_URL}/api/upload/file",
            data=body_bytes,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Authorization": "Bearer invalid_token_xyz",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                result.fail("無効トークン", f"expected 401 but got {resp.status}")
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                result.ok(f"無効トークン → {e.code}")
            else:
                result.fail("無効トークン", f"unexpected {e.code}")


def run(result: TestResult = None) -> bool:
    r = result or TestResult("upload/auth")
    TestUploadAuth().run(r)
    if result is None:
        return r.summary()
    return True


if __name__ == "__main__":
    import sys
    ok = run()
    sys.exit(0 if ok else 1)
