# ARS Flow Form 前端集成指南

## 概要

このドキュメントは、ARS Flow動的フォームを既存のチャットボットUIに統合する方法を説明します。

## アーキテクチャ

```
ユーザー入力: "CCFLOWシステム申請を実行"
    ↓
Backend: LLMがFlow IDを識別
    ↓
Backend: Flow参数定義を取得
    ↓
Frontend: Flow参数フォームメッセージを受信
    ↓
Frontend: ChatMessageWithFormが自動的にフォームを表示
    ↓
ユーザー: フォームに入力して送信
    ↓
Frontend: /api/ars/flow/execute を呼び出し
    ↓
Backend: Flowを実行
    ↓
Frontend: 実行結果を表示
```

## 作成されたファイル

### 1. ユーティリティ

**`src/utils/arsFormConverter.ts`**
- ARS参数をFormスキーマに変換
- メッセージからFlow情報を解析
- Flow参数メッセージの判定

### 2. コンポーネント

**`src/components/ARSFlowForm.tsx`**
- MUIベースの動的フォームコンポーネント
- text, number, option, date, file型をサポート
- バリデーション機能
- ローディング状態管理

**`src/components/ChatMessageWithForm.tsx`**
- チャットメッセージとフォームを統合
- 自動的にFlow参数メッセージを検出
- フォーム表示/非表示の管理
- 実行結果の表示

### 3. サービス

**`src/services/arsFlowService.ts`**
- `getFlowParams()` - Flow参数定義取得
- `executeFlow()` - Flow実行
- API通信の抽象化

### 4. 使用例

**`src/components/examples/ARSFlowFormExample.tsx`**
- 統合方法のサンプルコード
- 手動制御の例

## クイックスタート

### ステップ1: 既存のチャットコンポーネントを確認

現在のメッセージレンダリング部分を見つけます:

```tsx
// 例: src/pages/ChatPage.tsx
{messages.map(msg => (
  <Box key={msg.id}>
    <ReactMarkdown>{msg.content}</ReactMarkdown>
  </Box>
))}
```

### ステップ2: ChatMessageWithFormに置き換え

```tsx
import { ChatMessageWithForm } from '../components/ChatMessageWithForm';

{messages.map(msg => (
  <ChatMessageWithForm
    key={msg.id}
    content={msg.content}
    role={msg.role}
    onFlowExecuted={(result) => {
      console.log('Flow executed:', result);
      // 必要に応じて追加処理
    }}
  />
))}
```

### ステップ3: 環境変数を設定

`.env`ファイルに追加:

```env
VITE_API_URL=http://localhost:8000
```

### ステップ4: バックエンドルートを登録

バックエンドの`main.py`または`app.py`に追加:

```python
from api.routes import ars_flow

app.include_router(
    ars_flow.router,
    prefix="/api/ars",
    tags=["ars"]
)
```

## 詳細な使用方法

### 方法1: 自動統合 (推奨)

`ChatMessageWithForm`コンポーネントを使用すると、自動的にFlow参数フォームを検出して表示します。

```tsx
<ChatMessageWithForm
  content={message.content}
  role={message.role}
  onFlowExecuted={(result) => {
    // Flow実行完了時の処理
    addMessage({
      role: 'assistant',
      content: `実行完了: ${JSON.stringify(result)}`,
    });
  }}
/>
```

### 方法2: 手動制御

より細かい制御が必要な場合:

```tsx
import { ARSFlowForm } from '../components/ARSFlowForm';
import { parseFlowParamMessage } from '../utils/arsFormConverter';

const flowData = parseFlowParamMessage(message.content);

if (flowData) {
  return (
    <ARSFlowForm
      flowId={flowData.flowId}
      flowName={flowData.flowName}
      params={flowData.params}
      onSubmit={async (flowId, values) => {
        const result = await executeFlow(flowId, values);
        handleResult(result);
      }}
      onCancel={() => {
        // キャンセル処理
      }}
    />
  );
}
```

## カスタマイズ

### スタイルのカスタマイズ

`ARSFlowForm.tsx`の`sx`プロップを変更:

```tsx
<Paper
  elevation={2}
  sx={{
    p: 2.5,
    backgroundColor: '#f5f5f5', // 背景色を変更
    borderRadius: 2,
    maxWidth: 500,
  }}
>
```

### 新しいフィールドタイプの追加

`arsFormConverter.ts`に新しい型を追加:

```typescript
case 'email':
  properties[api_param_name] = {
    type: 'string',
    title: api_param_name,
    'x-component': 'Input',
    'x-decorator': 'FormItem',
    'x-component-props': {
      type: 'email',
      placeholder: 'email@example.com',
    },
  };
  break;
```

`ARSFlowForm.tsx`にレンダリングロジックを追加:

```tsx
case 'email':
  return (
    <TextField
      key={api_param_name}
      fullWidth
      label={api_param_name}
      type="email"
      value={value}
      onChange={(e) => handleChange(api_param_name, e.target.value)}
      error={!!error}
      helperText={error}
    />
  );
```

### バリデーションルールの追加

```tsx
const validate = (): boolean => {
  const newErrors: Record<string, string> = {};
  
  params.forEach(param => {
    const value = formValues[param.api_param_name];
    
    // 必須チェック
    if (param.required && !value) {
      newErrors[param.api_param_name] = `${param.api_param_name}は必須です`;
    }
    
    // メールフォーマットチェック
    if (param.param_type === 'email' && value) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(value)) {
        newErrors[param.api_param_name] = '有効なメールアドレスを入力してください';
      }
    }
    
    // 数値範囲チェック
    if (param.param_type === 'number' && value) {
      if (param.min !== undefined && value < param.min) {
        newErrors[param.api_param_name] = `${param.min}以上の値を入力してください`;
      }
      if (param.max !== undefined && value > param.max) {
        newErrors[param.api_param_name] = `${param.max}以下の値を入力してください`;
      }
    }
  });
  
  setErrors(newErrors);
  return Object.keys(newErrors).length === 0;
};
```

## トラブルシューティング

### フォームが表示されない

1. メッセージフォーマットを確認:
   ```
   **Flow ID**: 5
   パラメータを入力してください
   ```
   この2つのキーワードが含まれているか確認

2. コンソールログを確認:
   ```tsx
   console.log('Is flow param message:', isFlowParamMessage(content));
   console.log('Parsed flow data:', parseFlowParamMessage(content));
   ```

### API呼び出しが失敗する

1. ネットワークタブで確認:
   - リクエストURL: `http://localhost:8000/api/ars/flow/execute`
   - ステータスコード: 200
   - レスポンス形式

2. 認証トークンを確認:
   ```tsx
   const token = localStorage.getItem('token');
   console.log('Auth token:', token);
   ```

3. CORSエラーの場合、バックエンドのCORS設定を確認

### フォームの値が送信されない

1. `formValues`の状態を確認:
   ```tsx
   console.log('Form values:', formValues);
   ```

2. バリデーションエラーを確認:
   ```tsx
   console.log('Validation errors:', errors);
   ```

## テスト

### ユニットテスト例

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ARSFlowForm } from '../ARSFlowForm';

test('renders form with text input', () => {
  const params = [
    { api_param_name: 'UserNo', param_type: 'text', required: true }
  ];
  
  render(
    <ARSFlowForm
      flowId="5"
      flowName="Test Flow"
      params={params}
      onSubmit={jest.fn()}
    />
  );
  
  expect(screen.getByLabelText('UserNo')).toBeInTheDocument();
});

test('validates required fields', async () => {
  const onSubmit = jest.fn();
  const params = [
    { api_param_name: 'UserNo', param_type: 'text', required: true }
  ];
  
  render(
    <ARSFlowForm
      flowId="5"
      flowName="Test Flow"
      params={params}
      onSubmit={onSubmit}
    />
  );
  
  fireEvent.click(screen.getByText('実行'));
  
  expect(screen.getByText('UserNoは必須です')).toBeInTheDocument();
  expect(onSubmit).not.toHaveBeenCalled();
});
```

## パフォーマンス最適化

### メモ化

```tsx
import { useMemo } from 'react';

const ChatMessageWithForm: React.FC<ChatMessageWithFormProps> = ({ content, role }) => {
  const flowData = useMemo(() => {
    if (role === 'assistant' && isFlowParamMessage(content)) {
      return parseFlowParamMessage(content);
    }
    return null;
  }, [content, role]);
  
  // ...
};
```

### 遅延ロード

```tsx
import { lazy, Suspense } from 'react';

const ARSFlowForm = lazy(() => import('./ARSFlowForm'));

<Suspense fallback={<CircularProgress />}>
  <ARSFlowForm {...props} />
</Suspense>
```

## 今後の拡張

- [ ] ファイルアップロード対応
- [ ] 複数ファイル選択
- [ ] 日付範囲選択
- [ ] 条件付きフィールド表示
- [ ] フォームの保存/復元機能
- [ ] オフライン対応
- [ ] 多言語対応

## 参考リンク

- [Material-UI Documentation](https://mui.com/)
- [React Hook Form](https://react-hook-form.com/)
- [ARS Backend API Documentation](../../backend/docs/API.md)
