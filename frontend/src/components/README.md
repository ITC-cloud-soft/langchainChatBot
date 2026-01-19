# ARS Flow Form コンポーネント

## 📦 含まれるファイル

```
src/
├── components/
│   ├── ARSFlowForm.tsx              # 動的フォームコンポーネント
│   ├── ChatMessageWithForm.tsx      # チャット統合コンポーネント
│   └── examples/
│       └── ARSFlowFormExample.tsx   # 使用例
├── services/
│   └── arsFlowService.ts            # API通信サービス
└── utils/
    └── arsFormConverter.ts          # 変換ユーティリティ
```

## 🚀 クイックスタート

### 1. 既存のチャットコンポーネントを更新

**Before:**
```tsx
{messages.map(msg => (
  <Box key={msg.id}>
    <ReactMarkdown>{msg.content}</ReactMarkdown>
  </Box>
))}
```

**After:**
```tsx
import { ChatMessageWithForm } from './components/ChatMessageWithForm';

{messages.map(msg => (
  <ChatMessageWithForm
    key={msg.id}
    content={msg.content}
    role={msg.role}
    onFlowExecuted={(result) => console.log('Flow完了:', result)}
  />
))}
```

### 2. バックエンドルートを登録

`backend/main.py`:
```python
from api.routes import ars_flow

app.include_router(
    ars_flow.router,
    prefix="/api/ars",
    tags=["ars"]
)
```

### 3. 環境変数を設定

`.env`:
```env
VITE_API_URL=http://localhost:8000
```

## 📖 使用方法

### 自動統合 (推奨)

`ChatMessageWithForm`を使用すると、Flow参数フォームを自動検出して表示します:

```tsx
<ChatMessageWithForm
  content={message.content}
  role={message.role}
  onFlowExecuted={(result) => {
    // Flow実行完了時の処理
    console.log('実行結果:', result);
  }}
/>
```

### 手動制御

より細かい制御が必要な場合:

```tsx
import { ARSFlowForm } from './components/ARSFlowForm';

<ARSFlowForm
  flowId="5"
  flowName="CCFLOWシステム申請"
  params={[
    {
      api_param_name: 'UserNo',
      param_type: 'text',
      required: true
    },
    {
      api_param_name: 'Department',
      param_type: 'option',
      option: [
        { option_label: '営業部', option_value: 'sales' },
        { option_label: '開発部', option_value: 'dev' }
      ]
    }
  ]}
  onSubmit={async (flowId, values) => {
    const result = await executeFlow(flowId, values);
    console.log(result);
  }}
/>
```

## 🎨 サポートされるフィールドタイプ

| タイプ | 説明 | UIコンポーネント |
|--------|------|------------------|
| `text` | テキスト入力 | `TextField` |
| `number` | 数値入力 | `TextField type="number"` |
| `option` | 選択肢 | `Select` |
| `date` | 日付選択 | `TextField type="date"` |
| `file` | ファイル (将来対応) | `Upload` |

## 🔧 カスタマイズ

### スタイル変更

```tsx
<Paper
  sx={{
    backgroundColor: '#your-color',
    borderRadius: 3,
    // ... その他のスタイル
  }}
>
```

### バリデーション追加

`ARSFlowForm.tsx`の`validate()`関数を編集:

```tsx
const validate = (): boolean => {
  const newErrors: Record<string, string> = {};
  
  // カスタムバリデーションロジック
  if (formValues.UserNo && formValues.UserNo.length < 5) {
    newErrors.UserNo = 'UserNoは5文字以上必要です';
  }
  
  setErrors(newErrors);
  return Object.keys(newErrors).length === 0;
};
```

## 🧪 テスト

```bash
# コンポーネントテストを実行
npm run test:components

# 特定のテストファイルを実行
npm test -- ARSFlowForm.test.tsx
```

## 📚 詳細ドキュメント

完全な統合ガイド: [`docs/ARS_FLOW_FORM_INTEGRATION.md`](../docs/ARS_FLOW_FORM_INTEGRATION.md)

## 🐛 トラブルシューティング

### フォームが表示されない

メッセージに以下が含まれているか確認:
- `**Flow ID**: X`
- `パラメータを入力してください`

### API呼び出しエラー

1. バックエンドが起動しているか確認
2. CORS設定を確認
3. 認証トークンを確認

```tsx
console.log('Token:', localStorage.getItem('token'));
```

## 💡 ヒント

- `ChatMessageWithForm`は既存のメッセージレンダリングと互換性があります
- フォームは自動的にバリデーションを行います
- 実行中は自動的にローディング状態になります
- エラーは自動的に表示されます

## 🤝 貢献

バグ報告や機能リクエストは Issue で受け付けています。
