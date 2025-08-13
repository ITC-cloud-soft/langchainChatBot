# コード品質チェックツール

このドキュメントでは、プロジェクトで使用しているコード品質チェックツールについて説明します。

## 目次

- [バックエンドツール](#バックエンドツール)
- [フロントエンドツール](#フロントエンドツール)
- [Pre-commitフック](#pre-commitフック)
- [CI/CDパイプラインでの使用](#cicdパイプラインでの使用)
- [ローカルでの実行方法](#ローカルでの実行方法)

## バックエンドツール

### Black

Blackは、Pythonコードのフォーマッターです。一貫したコードスタイルを維持するために使用します。

#### 設定ファイル
- `.black`
- `pyproject.toml`の`[tool.black]`セクション

#### 主な設定
- 行長: 88文字
- ターゲットPythonバージョン: 3.8
- ダブルクォートの使用

#### 実行方法
```bash
# バックエンドディレクトリで
black .
```

### isort

isortは、Pythonのインポート文をソートするツールです。

#### 設定ファイル
- `.isort.cfg`
- `pyproject.toml`の`[tool.isort]`セクション

#### 主な設定
- Blackと互換性のあるプロファイル
- 行長: 88文字
- 既知のファーストパーティ: api

#### 実行方法
```bash
# バックエンドディレクトリで
isort .
```

### flake8

flake8は、Pythonコードのリンターです。コードのスタイルとエラーをチェックします。

#### 設定ファイル
- `.flake8`
- `pyproject.toml`の`[tool.flake8]`セクション

#### 主な設定
- 行長: 88文字
- 無視するエラー: E203, E501, W503
- 除外するディレクトリ: テスト、ビルド成果物など

#### 実行方法
```bash
# バックエンドディレクトリで
flake8 .
```

### mypy

mypyは、Pythonの静的型チェッカーです。型の不一致を検出します。

#### 設定ファイル
- `.mypy.ini`
- `pyproject.toml`の`[tool.mypy]`セクション

#### 主な設定
- Pythonバージョン: 3.8
- 厳密な型チェックを有効化
- 外部ライブラリのインポートエラーを無視

#### 実行方法
```bash
# バックエンドディレクトリで
mypy .
```

### bandit

banditは、Pythonコードのセキュリティ脆弱性を検出するツールです。

#### 設定ファイル
- `.bandit`
- `pyproject.toml`の`[tool.bandit]`セクション

#### 主な設定
- 除外するディレクトリ: tests
- スキップするテスト: B101, B601

#### 実行方法
```bash
# バックエンドディレクトリで
bandit -r .
```

### pytest

pytestは、Pythonのテストフレームワークです。テストの実行とカバレッジレポートの生成に使用します。

#### 設定ファイル
- `pytest.ini`
- `pyproject.toml`の`[tool.pytest.ini_options]`セクション

#### 主な設定
- テストパス: tests
- カバレッジレポートの有効化
- カバレッジの最小要件: 80%

#### 実行方法
```bash
# バックエンドディレクトリで
pytest --cov=api
```

### coverage.py

coverage.pyは、Pythonコードのテストカバレッジを測定するツールです。

#### 設定ファイル
- `.coveragerc`
- `pyproject.toml`の`[tool.coverage]`セクション

#### 主な設定
- ソースディレクトリ: api
- 除外するファイル: テスト、__init__.pyなど
- カバレッジレポートの形式: HTMLとターミナル

#### 実行方法
```bash
# バックエンドディレクトリで
coverage run -m pytest
coverage report
coverage html
```

## フロントエンドツール

### ESLint

ESLintは、JavaScript/TypeScriptコードのリンターです。コードのスタイルとエラーをチェックします。

#### 設定ファイル
- `.eslintrc.js`

#### 主な設定
- パーサー: @typescript-eslint/parser
- 拡張設定: eslint:recommended, @typescript-eslint/recommended
- プラグイン: react, react-hooks, import
- 環境: browser, es2020, node

#### 実行方法
```bash
# フロントエンドディレクトリで
npm run lint
# または
npx eslint src/
```

### Prettier

Prettierは、JavaScript/TypeScriptコードのフォーマッターです。一貫したコードスタイルを維持するために使用します。

#### 設定ファイル
- `.prettierrc`
- `.prettierignore`

#### 主な設定
- セミコロン: 使用
- 末尾のカンマ: ES5スタイル
- シングルクォート: 使用
- 行長: 88文字
- インデント: 2スペース

#### 実行方法
```bash
# フロントエンドディレクトリで
npm run format
# または
npx prettier --write src/
```

### Jest

Jestは、JavaScript/TypeScriptのテストフレームワークです。テストの実行とカバレッジレポートの生成に使用します。

#### 設定ファイル
- `jest.config.js`

#### 主な設定
- テスト環境: jsdom
- セットアップファイル: src/setupTests.js
- カバレッジの最小要件: 80%

#### 実行方法
```bash
# フロントエンドディレクトリで
npm test
# カバレッジ付きでテストを実行
npm run test:coverage
```

## Pre-commitフック

Pre-commitフックは、コミット前に自動的にコード品質チェックを実行する仕組みです。

### 設定ファイル
- `.pre-commit-config.yaml`（ルート、バックエンド、フロントエンド）

### 主なフック
- 末尾の空白の削除
- ファイル末尾の改行の追加
- YAML/JSON/TOMLファイルの検証
- BlackによるPythonコードのフォーマット
- isortによるインポート文のソート
- flake8によるPythonコードのリント
- mypyによる型チェック
- banditによるセキュリティチェック
- ESLintによるJavaScript/TypeScriptコードのリント
- Prettierによるコードのフォーマット

### インストール方法
```bash
# プロジェクトルートで
pip install pre-commit
pre-commit install
```

### 実行方法
```bash
# すべてのファイルに対して手動で実行
pre-commit run --all-files

# 特定のフックのみを実行
pre-commit run black --all-files
```

## CI/CDパイプラインでの使用

### GitHub Actions

CI/CDパイプラインでは、以下のステップでコード品質チェックを実行します。

#### バックエンド
1. Python環境のセットアップ
2. 依存関係のインストール
3. Blackによるフォーマットチェック
4. isortによるインポートチェック
5. flake8によるリント
6. mypyによる型チェック
7. banditによるセキュリティチェック
8. pytestによるテスト実行とカバレッジレポート

#### フロントエンド
1. Node.js環境のセットアップ
2. 依存関係のインストール
3. ESLintによるリント
4. Prettierによるフォーマットチェック
5. Jestによるテスト実行とカバレッジレポート

### 設定ファイル
- `.github/workflows/ci.yml`

## ローカルでの実行方法

### バックエンド

#### 個別のツールを実行
```bash
# バックエンドディレクトリで
# フォーマットチェック
black --check .

# インポートチェック
isort --check-only .

# リント
flake8 .

# 型チェック
mypy .

# セキュリティチェック
bandit -r .

# テスト実行
pytest --cov=api
```

#### すべてのチェックを一度に実行
```bash
# バックエンドディレクトリで
# フォーマットとインポートの修正
black . && isort .

# すべてのチェックを実行
flake8 . && mypy . && bandit -r . && pytest --cov=api
```

### フロントエンド

#### 個別のツールを実行
```bash
# フロントエンドディレクトリで
# リント
npm run lint

# フォーマットチェック
npm run format:check

# テスト実行
npm test

# カバレッジ付きでテストを実行
npm run test:coverage
```

#### すべてのチェックを一度に実行
```bash
# フロントエンドディレクトリで
# リントとフォーマットチェック
npm run lint && npm run format:check

# テスト実行
npm test
```

### プロジェクト全体

#### Makefileの使用
プロジェクトルートにMakefileを作成することで、コマンドを簡略化できます。

```makefile
# バックエンドのチェック
backend-check:
	cd backend && black --check . && isort --check-only . && flake8 . && mypy . && bandit -r . && pytest --cov=api

# フロントエンドのチェック
frontend-check:
	cd frontend && npm run lint && npm run format:check && npm test

# すべてのチェック
check: backend-check frontend-check

# バックエンドのフォーマット
backend-format:
	cd backend && black . && isort .

# フロントエンドのフォーマット
frontend-format:
	cd frontend && npm run format

# すべてのフォーマット
format: backend-format frontend-format
```

#### 実行方法
```bash
# プロジェクトルートで
# すべてのチェックを実行
make check

# すべてのフォーマットを実行
make format
```

## トラブルシューティング

### 一般的な問題

#### Blackとflake8の行長設定の不一致
Blackとflake8の行長設定を同じ値（88文字）に設定してください。

#### mypyの型エラー
外部ライブラリの型エラーは、`.mypy.ini`の`ignore_missing_imports`設定で無視できます。

#### ESLintとPrettierの競合
ESLintの設定でPrettierと競合するルールを無効にしてください。`eslint-config-prettier`を使用することをお勧めします。

#### Pre-commitフックが実行されない
Pre-commitが正しくインストールされているか確認してください。
```bash
pre-commit install
```

#### テストカバレッジが低い
テストを追加してカバレッジを向上させてください。カバレッジレポートは`htmlcov`ディレクトリ（バックエンド）または`coverage`ディレクトリ（フロントエンド）に生成されます。

### デバッグ方法

#### 詳細なログを有効にする
```bash
# バックエンド
flake8 --verbose .
mypy --verbose .

# フロントエンド
npm run lint -- --verbose
```

#### 特定のファイルのみをチェック
```bash
# バックエンド
black path/to/file.py
flake8 path/to/file.py

# フロントエンド
npx eslint path/to/file.tsx
npx prettier --check path/to/file.tsx
```

#### 特定のルールを無視
```bash
# バックエンド
flake8 --ignore=E203,W503 path/to/file.py

# フロントエンド
npx eslint --rule 'no-console: off' path/to/file.tsx
```

## 参考資料

- [Blackドキュメント](https://black.readthedocs.io/)
- [isortドキュメント](https://pycqa.github.io/isort/)
- [flake8ドキュメント](https://flake8.pycqa.org/)
- [mypyドキュメント](https://mypy.readthedocs.io/)
- [banditドキュメント](https://bandit.readthedocs.io/)
- [pytestドキュメント](https://docs.pytest.org/)
- [coverage.pyドキュメント](https://coverage.readthedocs.io/)
- [ESLintドキュメント](https://eslint.org/)
- [Prettierドキュメント](https://prettier.io/)
- [Jestドキュメント](https://jestjs.io/)
- [Pre-commitドキュメント](https://pre-commit.com/)