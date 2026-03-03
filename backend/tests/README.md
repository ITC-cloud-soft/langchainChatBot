# テストディレクトリ構成

## ディレクトリ構造

```
tests/
├── conftest.py              # 共通設定・HTTP ユーティリティ・TestResult クラス
├── run_all.py               # 全テスト一括実行エントリーポイント
├── README.md                # このファイル
│
├── upload/                  # ファイルアップロード機能
│   ├── __init__.py
│   ├── test_upload_auth.py       # 認証・認可テスト
│   ├── test_upload_validation.py # 拡張子・サイズバリデーション
│   └── test_upload_success.py    # 正常アップロード・レスポンス形式
│
├── flow/                    # ARS Flow 申請機能
│   ├── __init__.py
│   └── test_submit_action.py     # submit-action / approval-action
│
└── notification/            # 通知機能 (Novu)
    ├── __init__.py
    └── (test_novu_integration.py は pytest 形式 → 直接 pytest で実行)
```

## 実行方法

### 全テスト一括実行

```bash
python tests/run_all.py
python tests/run_all.py --verbose
```

### 機能別スイート実行

```bash
python tests/run_all.py --suite upload        # アップロード系全て
python tests/run_all.py --suite upload/auth   # 認証テストのみ
python tests/run_all.py --suite flow          # Flow 申請テストのみ
```

### 個別ファイル実行

```bash
python tests/upload/test_upload_auth.py
python tests/upload/test_upload_validation.py
python tests/flow/test_submit_action.py
```

### Docker コンテナ内での実行（推奨）

```bash
docker exec chatbot-backend python tests/run_all.py
docker exec chatbot-backend python tests/run_all.py --suite upload
```

## 環境変数

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `TEST_BASE_URL` | `http://localhost:8000` | バックエンドURL |
| `TEST_USER` | `admin` | テストユーザー名 |
| `TEST_PASS` | `admin123` | テストパスワード |

## 新機能テストの追加方法

1. 対応するサブディレクトリにテストファイルを作成する
   - ファイル名: `test_{機能名}.py`
   - テストクラス: `class Test{機能名}:` に `run(self, token, result)` メソッドを実装

2. `run_all.py` の `get_suites()` 関数にエントリーを追加する

```python
from tests.新機能.test_新機能 import Test新機能
# get_suites() 内に追加:
("新機能/xxx", Test新機能(), True),
```

3. `conftest.py` の共通ユーティリティ（`http_get`, `http_post`, `http_upload`, `TestResult`）を活用する

## テスト結果の見方

```
[PASS] テスト名 (詳細情報)   ← 成功
[FAIL] テスト名: 失敗理由    ← 失敗
[SKIP] テスト名: スキップ理由 ← ストレージ未起動など条件付きスキップ
```
