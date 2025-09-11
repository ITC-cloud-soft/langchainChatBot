# チャットボットフロントエンド

React + TypeScriptを使用したチャットボットフロントエンドアプリケーションです。Material-UIを採用し、チャット機能、LLM設定管理、ナレッジベース管理を提供します。

## 機能

- **リアルタイムチャット**: WebSocketによるストリーミングチャット、セッション管理、参照ドキュメント表示、Markdownサポート、自動スクロールインターフェース。
- **LLM設定管理**: 動的設定、モデル選択、パラメータ調整、設定テスト、リセット機能。
- **ナレッジベース管理**: ドキュメントアップロード、ディレクトリバッチ処理、検索、CRUD操作。
- **レスポンシブデザイン**: Material-UIによるモダンなUI。
- **パフォーマンス最適化**: 仮想化メッセージリスト、コードスプリッティング、メモ化。

## 技術スタック

- **React 18**: モダンなUIフレームワーク
- **TypeScript**: 型安全な開発
- **Material-UI v5**: UIコンポーネントライブラリ
- **React Router v6**: ルーティング
- **Axios**: HTTPクライアント（インターセプター付き）
- **React Hook Form**: フォーム管理
- **notistack**: 通知コンポーネント
- **react-markdown**: マークダウン表示
- **Vite**: ビルドツール
- **pnpm**: パッケージマネージャー（推奨）
- **テスト**: Vitest + React Testing Library

## インストール

### 前提条件

- Node.js >= 16.0.0
- pnpm（推奨）

### セットアップ

```bash
# frontendディレクトリに移動
cd frontend

# 依存関係インストール
pnpm install

# 環境ファイル作成
cp .env.example .env
# .envを編集してAPI URLを設定
```

## 開発

### 開発サーバー起動

```bash
# 開発サーバー
pnpm dev              # http://localhost:3000

# HTTPS開発サーバー
pnpm dev:https

# ビルドとテスト
pnpm build            # 本番ビルド
pnpm test             # テスト実行
pnpm test:coverage    # カバレッジレポート
pnpm test:unit        # ユニットテスト
pnpm test:integration # インテグレーションテスト

# コード品質
pnpm lint             # ESLint
pnpm lint:fix         # ESLint自動修正
pnpm type-check       # TypeScript検証
pnpm format           # Prettierフォーマット
```

アプリケーションに http://localhost:3000 でアクセス。

### 本番ビルド

```bash
# 本番ビルド
pnpm build

# 本番ビルドプレビュー
pnpm preview

# ビルドアーティファクトクリーン
pnpm build:clean
```

## 環境変数

frontendディレクトリに `.env` ファイルを作成：

```env
# バックエンドAPI URL
REACT_APP_API_URL=http://localhost:8000

# 環境（development/production）
REACT_APP_ENVIRONMENT=development

# ログレベル（debug/info/warn/error）
REACT_APP_LOG_LEVEL=info

# バージョン情報
REACT_APP_VERSION=1.0.0
```

## プロジェクト構造

```
frontend/src/
├── components/           # 再利用可能なUIコンポーネント
│   ├── common/          # 共有コンポーネント (DataTable, ErrorAlert, FileUploadArea, LoadingSpinner, PageContainer, SearchBar, StatusChip など)
│   ├── ChatInput.tsx    # チャット入力コンポーネント
│   ├── Layout.tsx       # メイン layout
│   └── VirtualizedMessageList.tsx  # パフォーマンス最適化メッセージリスト
├── pages/               # ページコンポーネント
│   ├── ChatPage.tsx     # チャットインターフェース
│   ├── LlmConfigPage.tsx # LLM設定
│   └── KnowledgePage.tsx # ナレッジベース管理
├── hooks/              # カスタムReact hooks
│   ├── useApi.ts       # API通信
│   ├── useChatState.ts # チャット状態管理
│   └── useConfig.ts    # 設定管理
├── services/           # APIサービス
│   └── api.ts          # 中央APIクライアント
└── utils/              # ユーティリティ関数
    ├── config.ts       # 設定ユーティリティ
    ├── index.ts        # 一般ユーティリティ
    └── logger.ts       # ログユーティリティ
```

## キー機能

### チャットインターフェース

- リアルタイムメッセージストリーミング
- セッション管理
- 参照ドキュメント表示
- Markdownサポート
- 自動スクロール
- メッセージ履歴

### LLM設定

- 設定のインポート/エクスポート
- モデル選択
- パラメータ調整
- 設定テスト
- デフォルトリセット

### ナレッジベース管理

- ドキュメントアップロード
- ディレクトリバッチアップロード
- ドキュメント検索
- コレクション管理
- ドキュメント削除

## API統合

フロントエンドは `src/services/api.ts` を通じてバックエンドAPIと統合：

- **ベースURL**: `REACT_APP_API_URL` で設定可能
- **認証**: localStorageに保存されたBearerトークン
- **エラーハンドリング**: 401/403/404/500エラーの自動処理

### APIモジュール

- `chatApi`: チャットメッセージ送信、ストリーミング、履歴
- `llmConfigApi`: LLM設定CRUD操作
- `knowledgeApi`: ナレッジベースドキュメント管理
- `healthApi`: システムヘルスチェック
- `configApi`: 設定管理

## 設定

### パスエイリアス

TypeScriptパスエイリアス設定:
- `@/*` → `src/*`
- `@/components/*` → `src/components/*`
- `@/utils/*` → `src/utils/*`
- `@/hooks/*` → `src/hooks/*`
- `@/pages/*` → `src/pages/*`
- `@/services/*` → `src/services/*`

### バックエンド接続

開発中、リクエストは `package.json` のプロキシ設定により `http://localhost:8000` にプロキシされます。

## テスト戦略

- **フレームワーク**: Vitest with React Testing Library
- **カバレッジ**: @vitest/coverage-v8 (50%+閾値)
- **タイプ**: Unit tests, integration tests, component tests
- **モッキング**: Axiosモッキング via `__mocks__/axios.js`

実行:
```bash
pnpm test             # すべてのテスト
pnpm test:coverage    # カバレッジレポート
```

## Dockerデプロイ

- **開発**: docker-compose.dev.yml
- **本番**: docker-compose.prod.yml
- **ステージング**: docker-compose.staging.yml

サービス:
- **frontend**: React (port 3000)

ログ確認:
```bash
docker-compose logs -f frontend
```

## ブラウザサポート

- Chrome (最新)
- Firefox (最新)
- Safari (最新)
- Edge (最新)

## 貢献

1. 既存のコードスタイルに従う
2. TypeScriptで型安全性を確保
3. 新機能にテストを書く
4. 必要に応じてドキュメントを更新

## ライセンス

MIT License