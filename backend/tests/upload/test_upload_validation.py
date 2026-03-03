"""
アップロードバリデーションテスト

拡張子制限・ファイルサイズ上限の検証。
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.conftest import http_upload, TestResult


class TestUploadValidation:
    """バリデーション境界値テスト"""

    UPLOAD_PATH = "/api/upload/file"

    def run(self, token: str, result: TestResult):
        print("\n[TestUploadValidation]")
        self._test_disallowed_extension_exe(token, result)
        self._test_disallowed_extension_sh(token, result)
        self._test_disallowed_extension_js(token, result)
        self._test_oversize_file(token, result)
        self._test_allowed_extensions(token, result)

    def _test_disallowed_extension_exe(self, token: str, result: TestResult):
        """不許可拡張子 .exe → 400"""
        status, body = http_upload(
            self.UPLOAD_PATH, token,
            filename="malware.exe",
            content=b"MZ fake exe",
            content_type="application/octet-stream",
        )
        if status == 400:
            result.ok("不許可拡張子(.exe) → 400", body.get("detail", "")[:60])
        else:
            result.fail("不許可拡張子(.exe)", f"expected 400, got {status}")

    def _test_disallowed_extension_sh(self, token: str, result: TestResult):
        """不許可拡張子 .sh → 400"""
        status, body = http_upload(
            self.UPLOAD_PATH, token,
            filename="script.sh",
            content=b"#!/bin/bash\necho hello",
            content_type="text/plain",
        )
        if status == 400:
            result.ok("不許可拡張子(.sh) → 400")
        else:
            result.fail("不許可拡張子(.sh)", f"expected 400, got {status}")

    def _test_disallowed_extension_js(self, token: str, result: TestResult):
        """不許可拡張子 .js → 400"""
        status, body = http_upload(
            self.UPLOAD_PATH, token,
            filename="exploit.js",
            content=b"alert(1)",
            content_type="text/javascript",
        )
        if status == 400:
            result.ok("不許可拡張子(.js) → 400")
        else:
            result.fail("不許可拡張子(.js)", f"expected 400, got {status}")

    def _test_oversize_file(self, token: str, result: TestResult):
        """ファイルサイズ超過 (10.1MB, 上限10MB) → 400"""
        large_content = b"x" * (10 * 1024 * 1024 + 1)  # 10MB+1byte（最小超過）
        status, body = http_upload(
            self.UPLOAD_PATH, token,
            filename="toobig.pdf",
            content=large_content,
            content_type="application/pdf",
        )
        if status == 400:
            result.ok("サイズ超過(11MB) → 400", body.get("detail", "")[:60])
        else:
            result.fail("サイズ超過(11MB)", f"expected 400, got {status}")

    def _test_allowed_extensions(self, token: str, result: TestResult):
        """許可拡張子一覧が全て受け付けられること（400 Bad Request でないこと）"""
        allowed = [
            ("sample.pdf",  b"%PDF fake",  "application/pdf"),
            ("data.xlsx",   b"PK fake",    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("doc.docx",    b"PK fake",    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            ("img.png",     b"\x89PNG\r\n\x1a\n" + b"\x00" * 10, "image/png"),
            ("photo.jpg",   b"\xff\xd8\xff" + b"\x00" * 10, "image/jpeg"),
            ("archive.zip", b"PK\x03\x04",  "application/zip"),
        ]
        all_ok = True
        for filename, content, ctype in allowed:
            status, body = http_upload(
                self.UPLOAD_PATH, token,
                filename=filename, content=content, content_type=ctype,
            )
            if status == 400:
                detail = body.get("detail", "")
                if "許可されていません" in detail or "not allowed" in detail.lower():
                    result.fail(f"許可拡張子({filename})", f"incorrectly rejected: {detail}")
                    all_ok = False
        if all_ok:
            result.ok("許可拡張子 全6種 バリデーション通過")


def run(token: str, result: TestResult = None) -> bool:
    r = result or TestResult("upload/validation")
    TestUploadValidation().run(token, r)
    if result is None:
        return r.summary()
    return True


if __name__ == "__main__":
    import sys
    from tests.conftest import login
    token = login()
    ok = run(token)
    sys.exit(0 if ok else 1)
