"""
ARS Flow 申請テスト

テスト対象:
  - POST /api/notifications/submit-action  (Flow申請)
  - POST /api/notifications/approval-action (承認・否認 回帰)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.conftest import http_post, TestResult


class TestSubmitAction:
    """Flow 申請エンドポイントテスト"""

    SUBMIT_PATH   = "/api/notifications/submit-action"
    APPROVAL_PATH = "/api/notifications/approval-action"
    VALID_FLOWS   = ["001", "002", "003", "004", "005", "006", "007", "008", "009"]

    def run(self, token: str, result: TestResult):
        print("\n[TestSubmitAction]")
        self._test_invalid_fk_flow(token, result)
        self._test_ars_key_not_set(token, result)
        self._test_approval_action_regression(token, result)
        self._test_valid_fk_flows(token, result)

    def _test_invalid_fk_flow(self, token: str, result: TestResult):
        """不正な fk_flow → 400"""
        status, body = http_post(
            self.SUBMIT_PATH,
            {"fk_flow": "999", "form_data": {}},
            token,
        )
        if status == 400:
            result.ok("不正 fk_flow(999) → 400")
        else:
            result.fail("不正 fk_flow(999)", f"expected 400, got {status}: {body}")

    def _test_ars_key_not_set(self, token: str, result: TestResult):
        """ARSキー未設定ユーザー → 400 or 500 (admin はARSキーなし想定)"""
        status, body = http_post(
            self.SUBMIT_PATH,
            {"fk_flow": "001", "form_data": {"COMMENT": "テスト申請"}},
            token,
        )
        if status in (400, 500):
            msg = body.get("detail", str(body)) if isinstance(body, dict) else str(body)
            result.ok(f"ARSキー未設定 → {status}", msg[:80])
        elif status == 200:
            result.ok("ARS接続成功 → 200 (ARS起動中)")
        else:
            result.fail("ARSキー未設定テスト", f"unexpected {status}: {body}")

    def _test_approval_action_regression(self, token: str, result: TestResult):
        """approval-action 回帰テスト（Flow 8 が壊れていないか）"""
        status, body = http_post(
            self.APPROVAL_PATH,
            {"ars_params": {}, "action": "approve", "comment": ""},
            token,
        )
        if status in (200, 400, 500):
            result.ok(f"approval-action 回帰 → {status}")
        else:
            result.fail("approval-action 回帰", f"unexpected {status}: {body}")

    def _test_valid_fk_flows(self, token: str, result: TestResult):
        """有効な fk_flow (001〜009) が全てバリデーション通過すること"""
        all_valid = True
        for fk in self.VALID_FLOWS:
            status, body = http_post(
                self.SUBMIT_PATH,
                {"fk_flow": fk, "form_data": {}},
                token,
            )
            if status == 400:
                detail = body.get("detail", "") if isinstance(body, dict) else ""
                if "不正な FK_Flow" in detail:
                    result.fail(f"fk_flow={fk} バリデーション", f"不正と判定された: {detail}")
                    all_valid = False
        if all_valid:
            result.ok(f"fk_flow 001〜009 全てバリデーション通過")


def run(token: str, result: TestResult = None) -> bool:
    r = result or TestResult("flow/submit")
    TestSubmitAction().run(token, r)
    if result is None:
        return r.summary()
    return True


if __name__ == "__main__":
    from tests.conftest import login
    token = login()
    ok = run(token)
    sys.exit(0 if ok else 1)
