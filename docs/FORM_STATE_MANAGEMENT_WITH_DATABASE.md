# Flow表单状态管理 - 数据库持久化方案

## 文档信息

- **作成日**: 2026-01-20
- **最終更新日**: 2026-01-20
- **バージョン**: 2.0.0
- **対象機能**: Flow表单状態的数据库持久化管理（metadata.params対応、多Flow隔離性保証）
- **関連ドキュメント**: `FLOW_EXECUTION_WITH_PARAMETERS.md`
- **変更履歴**:
  - 2026-01-20: バージョン2.0.0に更新。metadata.params対応、多Flow隔離性保証を追加。

---

## 1. 概要

### 1.1 背景

現在のFlow表单实现存在以下问题：
- 表单状态仅保存在前端内存中，刷新页面后丢失
- 无法追踪表单的完整生命周期（提交、取消、完成）
- 用户输入的数据在取消操作后会丢失
- 跨设备无法同步表单状态

### 1.2 目的

通过数据库持久化表单状态，实现：
- ✅ 表单状态永久保存，刷新不丢失
- ✅ 完整的状态追踪（pending → submitted/cancelled → completed）
- ✅ 用户输入数据保留（即使取消操作）
- ✅ 跨设备状态同步
- ✅ 简化前端渲染逻辑

### 1.3 技术方案

利用现有的 `ChatMessage` 表的 `message_metadata` 字段（JSON类型）存储表单状态信息，无需新建表。

---

## 2. 数据结构设计

### 2.1 表单消息的 metadata 结构

```json
{
  "message_type": "flow_form",
  "flow_id": "5",
  "flow_name": "CCFLOWシステム申請--仕入計画",
  "form_status": "pending",
  "params": [
    {
      "api_param_name": "UserNo",
      "param_type": "text",
      "required": true
    },
    {
      "api_param_name": "Department",
      "param_type": "option",
      "required": true,
      "option": [
        {"option_label": "営業部", "option_value": "sales"},
        {"option_label": "開発部", "option_value": "dev"}
      ]
    },
    {
      "api_param_name": "StartDate",
      "param_type": "date",
      "required": true
    }
  ],
  "form_data": {
    "UserNo": "12345",
    "Department": "sales",
    "StartDate": "2024-01-01"
  },
  "submitted_at": "2024-01-19T14:30:00Z",
  "cancelled_at": null,
  "completed_at": null,
  "execution_result": null
}
```

**重要**: `params` フィールドには表单パラメータの定義が保存されます。これにより、フロントエンドはcontentを解析せずに直接metadataから表单を構築できます。

### 2.2 表单状态定义

| 状态 | 説明 | 遷移条件 |
|------|------|---------|
| `pending` | 初期状態、ユーザー入力待ち | 表单生成时 |
| `submitted` | 提交済み、実行待ち | 用户点击"実行"按钮 |
| `cancelled` | キャンセル済み | 用户点击"キャンセル"按钮 |
| `completed` | 実行完了（成功） | 收到成功的执行结果 |
| `error` | 実行失敗 | 收到失败的执行结果 |

### 2.3 状态流转图

```
pending (初期)
  ├─→ submitted (提交) → completed (成功)
  │                    → error (失敗)
  └─→ cancelled (取消)
```

---

## 3. 実装詳細

### 3.1 バックエンド修改

#### 3.1.1 データベースモデル拡張

**ファイル**: `backend/api/models/database.py`

**追加関数**:
- `update_message_form_status_async()`: 表单状態を更新（message_id で精確に特定）
- `get_message_by_id_async()`: メッセージIDでメッセージを取得

**重要ポイント**:
```python
# message_id で精確に特定
result = await db.execute(
    select(ChatMessage).where(ChatMessage.message_id == message_id)
)
# metadata を更新
metadata['form_status'] = form_status
metadata['form_data'] = form_data
# タイムスタンプを自動記録
metadata['submitted_at'] = datetime.now().isoformat()
```

---

#### 3.1.2 API エンドポイント追加

**ファイル**: `backend/api/routes/chat.py`

**追加エンドポイント**:
- `PATCH /messages/{message_id}/form-status`: 表单状態を更新
- `GET /messages/{message_id}`: メッセージを取得

**リクエスト例**:
```json
{
  "form_status": "submitted",
  "form_data": {"UserNo": "12345", "Department": "sales"}
}
```

---

#### 3.1.3 表单生成時の metadata 保存

**ファイル**: `backend/api/services/chat_service.py`

**修改内容**: Flow表单生成時に `params` 定義も metadata に保存

```python
# stream_message 関数内、Flow表单生成時
if params:
    # 有参数需要填写,返回表单
    full_response = f"📋 **{flow_name or f'Flow {flow_id}'}** を実行します\n\n"
    full_response += "以下のパラメータを入力してください:\n\n"
    
    for param in params:
        param_name = param.get("api_param_name")
        param_type = param.get("param_type")
        full_response += f"- **{param_name}** ({param_type})\n"
    
    # メタデータとして flow_id と params を埋め込む
    full_response += f"\n---\n**Flow ID**: {flow_id}\n"
    full_response += "パラメータを入力後、再度送信してください。"
    
    # 表单メッセージのメタデータを設定（初期状態: pending）
    form_metadata = {
        "form_status": "pending",
        "flow_id": flow_id,
        "flow_name": flow_name,
        "params": params  # ★重要: パラメータ定義も保存
    }
```

**追加位置**: `stream_message` 関数内、Flow参数取得後

**重要ポイント**:
- `params` 配列全体を metadata に保存することで、フロントエンドは content を解析せずに表单を構築できる
- これにより、content フォーマットが変更されても表单レンダリングに影響しない

---

#### 3.1.4 Flow実行時の状態更新（EXECUTE_FLOW メッセージ処理）

**ファイル**: `backend/api/services/chat_service.py`

**修改内容**: EXECUTE_FLOW メッセージ処理時に表单メッセージを更新（message_id を使用）

```python
# stream_message 関数内で EXECUTE_FLOW を検出した場合
# 新フォーマット: EXECUTE_FLOW:flow_id:message_id:params_json

# 首先检查用户是否提交了Flow参数 (格式: EXECUTE_FLOW:flow_id:message_id:params_json)
param_submit_pattern = r'EXECUTE_FLOW:(\d+):([^:]+):(.+)'
param_match = re.search(param_submit_pattern, message)

if param_match:
    # 用户提交了参数,直接执行Flow
    flow_id = param_match.group(1)
    form_message_id = param_match.group(2)  # ★重要: メッセージから message_id を取得
    params_json = param_match.group(3)
    
    try:
        params = json.loads(params_json)
        self.log_info(f"[ARS REACT] User submitted params for flow {flow_id}, message_id: {form_message_id}, params: {params}")
        
        # 更新表单状態为 'submitted'（使用消息中提供的message_id）
        if form_message_id and form_message_id != 'undefined':
            try:
                from api.models.database import update_message_form_status_async
                from api.core.database import database_manager
                
                async with database_manager.get_session() as db_session:
                    await update_message_form_status_async(
                        db=db_session,
                        message_id=form_message_id,  # ★精確に message_id を指定
                        form_status='submitted',
                        form_data=params
                    )
                self.log_info(f"Updated form status to 'submitted' for message {form_message_id}")
            except Exception as e:
                self.log_warning(f"Failed to update form status: {str(e)}")
        
        # Flow実行処理...
        from api.tools.ars_tools import ExecuteFlowTool
        tool = ExecuteFlowTool(ars_token=ars_token)
        result_str = await tool._arun(flow_id=flow_id, parameters=params)
        # ...
        
    except Exception as e:
        self.log_error(f"[ARS REACT] Error executing flow with params", e)
```

**修改位置**: `stream_message` 関数内、ReAct解析部分

**重要な変更点**:

1. **メッセージフォーマット変更**: `EXECUTE_FLOW:flow_id:params` → `EXECUTE_FLOW:flow_id:message_id:params`
2. **正規表現パターン変更**: `r'EXECUTE_FLOW:(\d+):(.+)'` → `r'EXECUTE_FLOW:(\d+):([^:]+):(.+)'`
3. **精確な message_id 使用**: メッセージから直接 message_id を抽出し、正確に対応する表单を更新
4. **undefined チェック**: message_id が 'undefined' の場合はスキップ

**メリット**:
- 複数の表单が同時に存在しても、正確に対応する表单を更新できる
- "最近のassistantメッセージ"を探す不確実な方法を排除
- 表单の隔離性を保証

---

### 3.2 フロントエンド修改

#### 3.2.1 表单状態サービス作成

**新規ファイル**: `frontend/src/services/formStatusService.ts`

**主要関数**:
- `updateFormStatus(messageId, formStatus, formData)`: 表单状態を更新
- `getMessage(messageId)`: メッセージを取得

**使用例**:
```typescript
await updateFormStatus(messageId, 'submitted', values);
```

---

#### 3.2.2 ChatMessageWithForm コンポーネント修改

**ファイル**: `frontend/src/components/ChatMessageWithForm.tsx`

**重要な変更点**:

1. **metadata.params の優先使用**:
```typescript
if (metadata?.params && metadata?.flow_id) {
  setFlowData({
    flowId: metadata.flow_id,
    flowName: metadata.flow_name,
    params: metadata.params  // contentを解析せずに直接使用
  });
}
```

2. **ローカル状態管理** (即座のUI更新):
```typescript
const [localFormStatus, setLocalFormStatus] = useState<FormStatus | null>(null);
const [localFormData, setLocalFormData] = useState<Record<string, any> | null>(null);
```

3. **messageId 検証**:
```typescript
if (!messageId) {
  setExecutionError('メッセージIDが見つかりません');
  return;
}
```

4. **EXECUTE_FLOW メッセージ新フォーマット**:
```typescript
const message = `EXECUTE_FLOW:${flowId}:${messageId}:${paramsJson}`;
```

---

#### 3.2.3 ARSFlowForm コンポーネント修改

**ファイル**: `frontend/src/components/ARSFlowForm.tsx`

**重要な変更点**:

1. **initialValues の動的更新**:
```typescript
useEffect(() => {
  setFormValues(initialValues);
}, [initialValues]);
```

2. **formStatus による編集制御**:
```typescript
const isEditable = formStatus === 'pending';
const isReadonly = !isEditable;
```

3. **状態に応じたメッセージ表示**: submitted/cancelled/completed/error 各状態でアラートを表示

---

#### 3.2.4 OptimizedChatMessage コンポーネント修改

**ファイル**: `frontend/src/components/OptimizedChatMessage.tsx`

**変更内容**: `message.message_id` と `message.metadata` を `ChatMessageWithForm` に渡す

```typescript
<ChatMessageWithForm
  messageId={message.message_id}
  metadata={message.metadata}
  // ... 他のprops
/>
```

---

## 4. データフロー

### 4.1 表单生成から完了までのフロー

```
1. LLMがFlow参数フォームを生成
   ↓
2. バックエンドがメッセージを保存（metadata.form_status = 'pending'）
   ↓
3. フロントエンドが表单を表示（編集可能）
   ↓
4. ユーザーが入力して「実行」をクリック
   ↓
5. フロントエンドがAPI呼び出し: PATCH /messages/{id}/form-status
   - form_status: 'submitted'
   - form_data: {...}
   ↓
6. データベースに状態保存
   ↓
7. EXECUTE_FLOW メッセージを送信
   ↓
8. バックエンドがFlow実行
   ↓
9. 実行結果を受信
   ↓
10. バックエンドが表单メッセージを更新
    - form_status: 'completed' or 'error'
    - execution_result: {...}
   ↓
11. フロントエンドが結果を表示
```

### 4.2 キャンセル時のフロー

```
1. ユーザーが「キャンセル」をクリック
   ↓
2. フロントエンドがAPI呼び出し: PATCH /messages/{id}/form-status
   - form_status: 'cancelled'
   - form_data: {...}  // 現在の入力内容を保存
   ↓
3. データベースに状態保存
   ↓
4. 表单が読み取り専用で表示される
   - 入力内容は保持される
   - ボタンは非表示
```

---

## 5. 双重状態更新保障機制

### 5.1 概要

表单状態の更新は、フロントエンドAPI呼び出しとバックエンドメッセージ解析の**二重保障機制**で実装されています。

### 5.2 更新フロー

```
ユーザーが「実行」ボタンをクリック
  ↓
【第1段階】フロントエンドAPI呼び出し
  ├─ updateFormStatus(messageId, 'submitted', values)
  ├─ PATCH /api/chat/messages/{messageId}/form-status
  └─ データベース更新 (form_status: 'submitted', form_data: {...})
  ↓
【第2段階】EXECUTE_FLOWメッセージ送信
  ├─ メッセージ: EXECUTE_FLOW:flowId:messageId:params
  ├─ バックエンドが message_id を抽出
  ├─ update_message_form_status_async() を呼び出し
  └─ データベース更新 (同じメッセージを再度更新)
```

### 5.3 メリットとデメリット

**メリット**:
- ✅ **高信頼性**: 第1段階が失敗しても、第2段階で更新される
- ✅ **即座のUI更新**: 第1段階でローカル状態を更新し、APIレスポンスを待たずにUIを反映
- ✅ **データ整合性**: 両方の更新が同じ message_id を使用するため、データの一貫性が保証される

**デメリット**:
- ⚠️ **冗長な更新**: 同じデータを2回更新する（軽微なパフォーマンス影響）
- ⚠️ **競合の可能性**: 2つの更新が同時に発生する場合、理論的には競合の可能性がある

**推奨**:
- 現在の実装を維持（信頼性を優先）
- 将来的にパフォーマンスが問題になる場合は、第1段階のみに統一することを検討

### 5.4 エラーハンドリング

```typescript
// フロントエンド: 第1段階が失敗した場合
try {
  await updateFormStatus(messageId, 'submitted', values);
} catch (error) {
  // ローカル状態をリセット
  setLocalFormStatus(null);
  setLocalFormData(null);
  setExecutionError(error.message);
  return;  // 第2段階に進まない
}

// バックエンド: 第2段階が失敗した場合
try {
  await update_message_form_status_async(...)
} catch (e) {
  self.log_warning(f"Failed to update form status: {str(e)}")
  // エラーをログに記録するが、Flow実行は継続
}
```

---

## 6. 多Flow実行申請の隔離性保証

### 6.1 問題の背景

同一セッション内で複数のFlow表单が同時に存在する場合、以下の問題が発生する可能性があります：

- 表单Aを提出した際に、誤って表单Bの状態が更新される
- 表单データが混在する
- 状態管理が不正確になる

### 6.2 隔離性保証の実装

#### 6.2.1 データベースレベル

```python
# database.py
message_id = Column(String(255), unique=True, index=True, nullable=False)
message_metadata = Column("metadata", JSON, nullable=True)

# 更新時は message_id で精確に特定
result = await db.execute(
    select(ChatMessage).where(ChatMessage.message_id == message_id)
)
```

**保証内容**:
- ✅ 各メッセージは一意の `message_id` (UUID) を持つ
- ✅ データベース更新は `message_id` で精確に特定
- ✅ トランザクション処理により原子性を保証

#### 6.2.2 フロントエンドコンポーネントレベル

```typescript
// 各 ChatMessageWithForm コンポーネントインスタンスは独立した state を持つ
const [flowData, setFlowData] = useState<FlowFormData | null>(null);
const [localFormStatus, setLocalFormStatus] = useState<FormStatus | null>(null);
const [localFormData, setLocalFormData] = useState<Record<string, any> | null>(null);
```

**保証内容**:
- ✅ React は各メッセージに対して独立したコンポーネントインスタンスを作成
- ✅ 各インスタンスの state は完全に隔離される
- ✅ Props (`messageId`, `metadata`) も各メッセージで独立

#### 6.2.3 API呼び出しレベル

```typescript
// フロントエンド: messageId で精確に更新
await updateFormStatus(messageId, 'submitted', values);

// API呼び出し
PATCH /api/chat/messages/{messageId}/form-status
```

**保証内容**:
- ✅ 各API呼び出しは一意の `messageId` を使用
- ✅ 異なる表单の更新が互いに影響しない

#### 6.2.4 EXECUTE_FLOWメッセージレベル

```typescript
// 新フォーマット: message_id を含む
const message = `EXECUTE_FLOW:${flowId}:${messageId}:${paramsJson}`;
```

```python
# バックエンド: メッセージから message_id を抽出
param_submit_pattern = r'EXECUTE_FLOW:(\d+):([^:]+):(.+)'
form_message_id = param_match.group(2)  # 精確な message_id

# 精確に対応する表单を更新
await update_message_form_status_async(
    db=db_session,
    message_id=form_message_id,  # ★精確に指定
    form_status='submitted',
    form_data=params
)
```

**保証内容**:
- ✅ メッセージに `message_id` を埋め込むことで、バックエンドが正確に対応する表单を特定
- ✅ "最近のassistantメッセージ"を探す不確実な方法を排除
- ✅ 複数の表单が同時に存在しても、正確に対応する表单のみを更新

### 6.3 隔離性検証テストケース

```typescript
// E2Eテスト例
test('multiple forms isolation', async ({ page }) => {
  // 1. Flow A の表单を生成
  await page.type('input', 'フロー一覧');
  await page.click('button[type="submit"]');
  await page.type('input', 'Flow A を実行');
  await page.click('button[type="submit"]');
  
  // 2. Flow B の表单を生成
  await page.type('input', 'Flow B を実行');
  await page.click('button[type="submit"]');
  
  // 3. Flow A の表单を提出
  const formA = page.locator('[data-flow-id="A"]');
  await formA.locator('input[name="param1"]').fill('valueA');
  await formA.locator('button:has-text("実行")').click();
  
  // 4. Flow A の状態が submitted になることを確認
  await expect(formA).toContainText('パラメータが送信されました');
  
  // 5. Flow B の状態が pending のままであることを確認
  const formB = page.locator('[data-flow-id="B"]');
  await expect(formB.locator('button:has-text("実行")')).toBeVisible();
  await expect(formB).not.toContainText('パラメータが送信されました');
  
  // 6. ページをリロード
  await page.reload();
  
  // 7. Flow A は submitted、Flow B は pending のままであることを確認
  await expect(formA).toContainText('パラメータが送信されました');
  await expect(formB.locator('button:has-text("実行")')).toBeVisible();
});
```

### 6.4 潜在的な問題と対策

#### 問題1: messageId が undefined の場合

**対策**: フロントエンドで messageId の存在を検証

```typescript
if (!messageId) {
  const errorMsg = 'メッセージIDが見つかりません。フォームを送信できません。';
  setExecutionError(errorMsg);
  return;
}
```

#### 問題2: 競合状態（Race Condition）

**対策**: 双重更新機制により、どちらか一方が成功すれば状態は正しく更新される

#### 問題3: セッション切り替え時の metadata 欠落

**対策**: API レスポンスに必ず `message_id` と `metadata` を含める

```typescript
// useChatPageHandlers.ts
const formattedMessages = apiMessages.map((msg: any) => ({
  role: msg.role,
  content: msg.content,
  timestamp: msg.timestamp,
  message_id: msg.message_id,  // ★必須
  metadata: msg.metadata,      // ★必須
  sourceDocuments: msg.source_documents,
}));
```

---

## 7. テスト・デプロイ・トラブルシューティング

### 7.1 テスト要点

**バックエンド**:
- `update_message_form_status_async()` の動作確認
- 表单ライフサイクル（pending → submitted → completed）

**フロントエンド**:
- formStatus に応じた表示切替
- metadata.params からの表单構築
- ページリロード後の状態保持

**E2E**:
- 表单提出・キャンセル・リロード後の状態確認
- 複数表单の隔離性確認

### 7.2 デプロイ

```bash
# バックエンド
docker-compose restart chatbot-backend

# フロントエンド
docker-compose restart chatbot-frontend
```

### 7.3 動作確認

1. Flow実行要求 → 表单表示
2. パラメータ入力 → 実行
3. ページリロード → 状態保持確認

---

### 7.4 トラブルシューティング

| 問題 | 原因 | 解決方法 |
|------|------|---------|
| 状態が更新されない | API失敗、message_id 不正 | コンソール・ネットワークタブ確認 |
| リロード後に状態消失 | metadata 欠落 | API レスポンス確認 |
| データが保存されない | form_data 未送信 | リクエストボディ確認 |

---

## 10. 参考資料

- [FLOW_EXECUTION_WITH_PARAMETERS.md](./FLOW_EXECUTION_WITH_PARAMETERS.md) - Flow実行の基本仕様
- [TWO_STAGE_FLOW_EXECUTION.md](./TWO_STAGE_FLOW_EXECUTION.md) - 2段階実行の詳細
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- React Hook Form: https://react-hook-form.com/
- Material-UI: https://mui.com/

---

## 変更履歴

| 日付 | バージョン | 変更内容 | 担当者 |
|------|----------|---------|--------|
| 2026-01-20 | 1.0.0 | 初版作成 | Cascade |
| 2026-01-20 | 2.0.0 | metadata.params対応、EXECUTE_FLOWメッセージフォーマット変更（message_id追加）、messageId検証追加、ARSFlowForm initialValues動的更新、双重状態更新保障機制追加、多Flow隔離性保証の章節追加 | Cascade |

---

## 承認

| 役割 | 氏名 | 日付 | 署名 |
|------|------|------|------|
| 作成者 | Cascade | 2026-01-20 | - |
| レビュー担当 | - | - | - |
| 承認者 | - | - | - |
