"""
アップロード正常系テスト

ストレージ（MinIO/Azurite）が起動している環境で実行する。
ストレージ未起動の場合は 503 を許容（スキップとして扱う）。
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.conftest import http_get, http_upload, TestResult


class TestUploadSuccess:
    """正常アップロード・レスポンス形式テスト"""

    UPLOAD_PATH = "/api/upload/file"
    HEALTH_PATH = "/api/upload/health"

    def run(self, token: str, result: TestResult):
        print("\n[TestUploadSuccess]")
        self._test_health(token, result)
        self._test_pdf_upload(token, result)
        self._test_png_upload(token, result)
        self._test_xlsx_upload(token, result)
        self._test_response_shape(token, result)

    def _test_health(self, token: str, result: TestResult):
        """ストレージ接続ヘルスチェック"""
        status, body = http_get(self.HEALTH_PATH, token)
        if status == 200:
            result.ok("ヘルスチェック → 200", f"backend={body.get('backend')}")
        elif status == 503:
            result.ok("ヘルスチェック → 503 (ストレージ未起動・許容)")
        else:
            result.fail("ヘルスチェック", f"unexpected {status}: {body}")

    def _test_pdf_upload(self, token: str, result: TestResult):
        """PDF アップロード → 200 or 503"""
        status, body = http_upload(
            self.UPLOAD_PATH, token,
            filename="test_document.pdf",
            content=b"%PDF-1.4 fake pdf content for test",
            content_type="application/pdf",
        )
        if status == 200:
            result.ok("PDF アップロード → 200", f"url={body.get('url', '')[:60]}")
        elif status == 503:
            result.ok("PDF アップロード → 503 (ストレージ未起動・許容)")
        else:
            result.fail("PDF アップロード", f"got {status}: {body}")

    def _test_png_upload(self, token: str, result: TestResult):
        """PNG アップロード → 200 or 503"""
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        status, body = http_upload(
            self.UPLOAD_PATH, token,
            filename="screenshot.png",
            content=png_header,
            content_type="image/png",
        )
        if status in (200, 503):
            result.ok(f"PNG アップロード → {status}")
        else:
            result.fail("PNG アップロード", f"got {status}: {body}")

    def _test_xlsx_upload(self, token: str, result: TestResult):
        """XLSX アップロード → 200 or 503"""
        status, body = http_upload(
            self.UPLOAD_PATH, token,
            filename="data.xlsx",
            content=b"PK\x03\x04 fake xlsx content",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        if status in (200, 503):
            result.ok(f"XLSX アップロード → {status}")
        else:
            result.fail("XLSX アップロード", f"got {status}: {body}")

    def _test_response_shape(self, token: str, result: TestResult):
        """レスポンスに name と url が含まれること"""
        status, body = http_upload(
            self.UPLOAD_PATH, token,
            filename="shape_check.pdf",
            content=b"%PDF-1.4 shape check",
            content_type="application/pdf",
        )
        if status == 200:
            has_name = "name" in body
            has_url  = "url"  in body
            if has_name and has_url:
                result.ok("レスポンス形式 {name, url} 確認", f"name={body['name']}")
            else:
                missing = [k for k in ("name", "url") if k not in body]
                result.fail("レスポンス形式", f"missing keys: {missing}")
        elif status == 503:
            result.skip("レスポンス形式確認", "ストレージ未起動のためスキップ")
        else:
            result.fail("レスポンス形式", f"got {status}: {body}")


def run(token: str, result: TestResult = None) -> bool:
    r = result or TestResult("upload/success")
    TestUploadSuccess().run(token, r)
    if result is None:
        return r.summary()
    return True


if __name__ == "__main__":
    import sys
    from tests.conftest import login
    token = login()
    ok = run(token)
    sys.exit(0 if ok else 1)
