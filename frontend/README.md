# フロントエンド - React + TypeScript

モダンなUIを備えたチャットボットのフロントエンドアプリケーションです。Material-UIによる洗練されたデザインと、リアルタイムチャット機能を提供します。

## 🚀 クイックスタート

### インストール

```bash
# 依存関係インストール
pnpm install
# または
npm install
```

### 環境設定

```bash
# 環境変数ファイルコピー
cp .env.example .env
```

`.env`を編集：

```bash
VITE_API_URL=http://localhost:8000
```

### 開発サーバー起動

```bash
# 開発モード
pnpm dev
# または
npm run dev
```

ブラウザで http://localhost:3000 にアクセス

### ビルド

```bash
# プロダクションビルド
pnpm build
# または
npm run build

# ビルド結果をプレビュー
pnpm preview
# または
npm run preview
```

## 📁 ディレクトリ構成

```
frontend/src/
├── components/          # UIコンポーネント
│   ├── common/         # 共通コンポーネント
│   ├── chat/           # チャット関連
│   ├── Layout.tsx      # レイアウト
│   └── ChatInput.tsx   # 入力コンポーネント
├── pages/              # ページコンポーネント
│   ├── ChatPage.tsx    # チャットページ
│   ├── LoginPage.tsx   # ログインページ
│   ├── LlmConfigPage.tsx      # LLM設定
│   ├── KnowledgePage.tsx      # ナレッジ管理
│   └── UserManagementPage.tsx # ユーザー管理
├── services/           # APIクライアント
│   ├── api.ts         # Axiosインスタンス
│   ├── authService.ts # 認証API
│   └── userService.ts # ユーザー管理API
├── contexts/           # React Context
│   └── AuthContext.tsx # 認証コンテキスト
├── hooks/              # カスタムフック
│   ├── useChatState.ts
│   └── useChatStreaming.ts
└── utils/              # ユーティリティ
```

## 🎨 主要機能

### チャット機能

- ✅ リアルタイムストリーミング表示
- ✅ セッション管理（履歴保存・読み込み）
- ✅ Markdownレンダリング
- ✅ コードハイライト
- ✅ 参照ドキュメント表示（RAG）
- ✅ 自動スクロール

### ユーザー管理

- ✅ ログイン/ログアウト
- ✅ JWT認証（自動リフレッシュ）
- ✅ 管理者専用機能
  - ユーザー作成・編集・削除
  - ロール管理（admin/user）
  - ユーザー検索・フィルタリング

### LLM設定管理

- ✅ プロバイダー選択（OpenAI、Anthropic、カスタム）
- ✅ モデル選択
- ✅ パラメータ調整（temperature、max_tokens等）
- ✅ 接続テスト
- ✅ 設定のエクスポート/インポート

### ナレッジベース管理

- ✅ ドキュメントアップロード
- ✅ ドキュメント一覧・検索
- ✅ ドキュメント削除
- ✅ コレクション管理

## 🔐 認証フロー

### ログイン

```
1. ユーザーがログイン情報を入力
   ↓
2. POST /api/auth/login
   ↓
3. Access Token + Refresh Token を取得
   ↓
4. localStorageに保存
   ↓
5. AuthContextの状態更新
   ↓
6. チャットページへリダイレクト
```

### トークン管理

- **Access Token**: 30分有効
- **Refresh Token**: 7日間有効
- **自動リフレッシュ**: Axiosインターセプターで処理

### 認証の使用方法

```tsx
import { useAuth } from '../contexts/AuthContext';

function MyComponent() {
  const { user, isAuthenticated, isAdmin, logout } = useAuth();

  if (!isAuthenticated) {
    return <div>ログインしてください</div>;
  }

  return (
    <div>
      <p>ようこそ、{user?.username}さん</p>
      {isAdmin && <p>管理者権限があります</p>}
      <button onClick={logout}>ログアウト</button>
    </div>
  );
}
```

### プライベートルート

```tsx
import PrivateRoute from './components/auth/PrivateRoute';

// 認証が必要なルート
<Route
  path="/chat"
  element={
    <PrivateRoute>
      <ChatPage />
    </PrivateRoute>
  }
/>

// 管理者のみアクセス可能
<Route
  path="/admin"
  element={
    <PrivateRoute requireAdmin>
      <AdminPage />
    </PrivateRoute>
  }
/>
```

## 🧪 開発

### テスト

```bash
# テスト実行
pnpm test
# または
npm run test

# カバレッジ付き
pnpm test:coverage
```

### コード品質

```bash
# リント
pnpm lint
# または
npm run lint

# フォーマット
pnpm format
```

## 🎨 UIコンポーネント

### Material-UI

このプロジェクトは Material-UI (MUI) v5 を使用しています。

```tsx
import { Button, TextField, Paper } from '@mui/material';

function MyComponent() {
  return (
    <Paper>
      <TextField label="入力" />
      <Button variant="contained">送信</Button>
    </Paper>
  );
}
```

### テーマカスタマイズ

`src/theme.ts`でテーマをカスタマイズできます：

```tsx
import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
  },
});
```

## 📚 技術スタック

- **React 18** - UIフレームワーク
- **TypeScript** - 型安全な開発
- **Material-UI v5** - UIコンポーネント
- **React Router v6** - ルーティング
- **Axios** - HTTPクライアント
- **React Hook Form** - フォーム管理
- **notistack** - 通知コンポーネント
- **react-markdown** - Markdown表示
- **Vite** - ビルドツール
- **Vitest** - テストフレームワーク

## 🔧 設定

### API URL変更

`.env`ファイルで変更：

```bash
VITE_API_URL=http://your-api-server:8000
```

### プロキシ設定（開発時）

`vite.config.ts`でプロキシ設定：

```ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

## 🐛 トラブルシューティング

### ログインできない

**症状**: ログインボタンを押してもエラーが出る

**解決方法**:
1. バックエンドが起動しているか確認
2. `.env`の`VITE_API_URL`が正しいか確認
3. ブラウザのコンソールでエラーメッセージを確認

### トークンが無効になる

**症状**: 一定時間後に401エラーが出る

**解決方法**:
- localStorageをクリアして再ログイン
- バックエンドの`JWT_SECRET_KEY`が変更されていないか確認

### 403エラー（Forbidden）

**症状**: API呼び出しで403エラーが出る

**解決方法**:
- 管理者権限が必要なAPIを一般ユーザーで呼び出していないか確認
- ブラウザのNetworkタブで`Authorization`ヘッダーが送信されているか確認

### Authorizationヘッダーが送信されない

**症状**: APIリクエストにトークンが含まれない

**解決方法**:
- localStorageに`access_token`があるか確認
- Axiosインターセプターが正しく設定されているか確認

## 📱 レスポンシブデザイン

- **デスクトップ**: 最適な表示
- **タブレット**: 適切なレイアウト調整
- **モバイル**: タッチフレンドリーなUI

## ♿ アクセシビリティ

- キーボードナビゲーション対応
- スクリーンリーダー対応
- 適切なコントラスト比
- ARIA属性の適切な使用

## 📄 ライセンス

MIT License

---

**メインドキュメント**: [../README.md](../README.md)
