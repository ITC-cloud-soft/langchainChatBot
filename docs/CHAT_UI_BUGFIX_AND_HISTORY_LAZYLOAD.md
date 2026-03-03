# チャット画面バグ修正と履歴遅延ロード設計

## 概要

本ドキュメントは 2026-02-26 に実施した以下2件の対応を記録する。

1. チャット画面のレイアウトバグ修正（EXECUTE_FLOW 表示問題・フォーム重叠）
2. チャット履歴の遅延ロード（Lazy Load）実装

---

## 1. チャット画面バグ修正

### 1-1. EXECUTE_FLOW メッセージがユーザー気泡として表示される問題

#### 根本原因

フォーム送信時、フロントエンドは `EXECUTE_FLOW:{flowId}:{params_json}` 形式のメッセージを
バックエンドに送信する。このメッセージが `role=user` として DB に保存・再表示され、
ユーザー吹き出しとして画面に出てしまっていた。

#### 修正内容

**ファイル**: `frontend/src/components/OptimizedChatMessage.tsx`

`role=user` かつ `content.startsWith('EXECUTE_FLOW:')` の場合は `null` を返して非表示にする。

```typescript
if (message.role === 'user' && message.content.startsWith('EXECUTE_FLOW:')) {
  return null;
}
```

---

### 1-2. 申請フォームの重叠問題

#### 根本原因

メッセージ数が 30 件を超えると `react-window` の `FixedSizeList`（仮想スクロール）が有効化される。
`FixedSizeList` は各アイテムを固定高さ 120px + `position: absolute` でレンダリングするため、
可変高さの申請フォーム（`ARSFlowForm`）がコンテナ外にはみ出して重叠していた。

#### 修正内容

**ファイル**: `frontend/src/pages/ChatPage.tsx`

フォームメッセージ（`metadata.params` が存在するメッセージ）がある場合は仮想スクロールを無効化:

```typescript
const hasFormMessages = (messages || []).some(
  msg => msg.metadata?.params
);
const useVirtualization = !hasFormMessages && (messages?.length ?? 0) > 30;
```

**ファイル**: `frontend/src/components/OptimizedChatMessage.tsx`

assistant メッセージコンテナの幅を `fit-content` から `100%` に変更（フォームが幅いっぱいに表示されるよう修正）:

```typescript
// 修正前
width: 'fit-content'
// 修正後
width: '100%'
```

**ファイル**: `frontend/src/components/ARSFlowForm.tsx`

フォームの幅指定を `maxWidth: 700` から `width: '100%'` に変更:

```typescript
// 修正前
sx={{ maxWidth: 700 }}
// 修正後
sx={{ width: '100%' }}
```

---

### 1-3. セッション未存在時に 500 エラーが返る問題

#### 根本原因

`GET /api/chat/sessions/{session_id}/history` で存在しないセッション ID を指定した場合、
`NoResultFound` 例外が捕捉されず 500 Internal Server Error が返っていた。

#### 修正内容

**ファイル**: `backend/api/routes/chat.py`

`NoResultFound` を捕捉し、空の履歴レスポンスを返すよう変更:

```python
from sqlalchemy.exc import NoResultFound

try:
    history = await chat_history_service.get_session_history(...)
except NoResultFound:
    return {"history": [], "has_more": False, "oldest_id": None}
```

---

## 2. チャット履歴遅延ロード（Lazy Load）実装

### 背景

セッション選択時に全メッセージを一括取得していたため、メッセージ数が多いセッションで
初期表示が遅延していた。

### 設計方針

- 初期表示: 最新 15 件のみ取得
- 追加ロード: 上端スクロール到達時に過去 10 件ずつ追加取得
- カーソルベースページネーション（`before_id` パラメータ）を使用

---

### バックエンド変更

#### database.py

**ファイル**: `backend/api/models/database.py`

`get_chat_messages_async()` に以下のパラメータを追加:

| パラメータ | 型 | 説明 |
|---|---|---|
| `before_id` | `int \| None` | このID未満のメッセージを取得（カーソル） |
| `latest_first` | `bool` | `True` の場合降順取得（最新から） |

```python
async def get_chat_messages_async(
    session_id: str,
    limit: int = 50,
    before_id: Optional[int] = None,
    latest_first: bool = False,
) -> list[ChatMessage]:
    query = select(ChatMessage).where(ChatMessage.session_id == session_id)
    if before_id:
        query = query.where(ChatMessage.id < before_id)
    if latest_first:
        query = query.order_by(ChatMessage.id.desc())
    else:
        query = query.order_by(ChatMessage.id.asc())
    query = query.limit(limit)
    ...
```

#### chat_history_service.py

**ファイル**: `backend/api/services/chat_history_service.py`

`get_session_history()` の戻り値に以下を追加:

| フィールド | 型 | 説明 |
|---|---|---|
| `has_more` | `bool` | さらに古いメッセージが存在するか |
| `oldest_id` | `int \| None` | 取得した中で最も古いメッセージの ID |

#### chat.py ルート

**ファイル**: `backend/api/routes/chat.py`

`GET /api/chat/sessions/{session_id}/history` エンドポイントに以下のクエリパラメータを追加:

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `limit` | 15 | 取得件数 |
| `before_id` | `None` | カーソル（このID未満を取得） |

レスポンスに `has_more` / `oldest_id` を追加して返す。

---

### フロントエンド変更

#### api.ts

**ファイル**: `frontend/src/services/api.ts`

`getChatHistory()` に分ページパラメータを追加:

```typescript
getChatHistory: (
  sessionId: string,
  limit?: number,     // デフォルト: 15
  beforeId?: number,  // カーソル
) => axios.get(`/api/chat/sessions/${sessionId}/history`, {
  params: { limit, before_id: beforeId }
})
```

#### ChatPage.tsx

**ファイル**: `frontend/src/pages/ChatPage.tsx`

追加した状態:

```typescript
const [hasMore, setHasMore] = useState(false);
const [oldestId, setOldestId] = useState<number | undefined>(undefined);
const [isLoadingMore, setIsLoadingMore] = useState(false);
```

`loadMoreHistory` 関数:

```typescript
const loadMoreHistory = useCallback(async () => {
  if (!sessionId || isLoadingMore || !hasMore || !oldestId) return;
  setIsLoadingMore(true);
  const response = await chatApi.getChatHistory(sessionId, 10, oldestId);
  const olderMessages = response.data.history || [];
  if (olderMessages.length > 0) {
    actions.setMessages([...formatted, ...(messages || [])]);
    setHasMore(response.data.has_more ?? false);
    setOldestId(response.data.oldest_id ?? undefined);
  } else {
    setHasMore(false);
  }
  setIsLoadingMore(false);
}, [sessionId, isLoadingMore, hasMore, oldestId, messages, actions]);
```

#### ChatMessages.tsx

**ファイル**: `frontend/src/components/Chat/ChatMessages.tsx`

追加した props:

```typescript
interface ChatMessagesProps {
  onLoadMore?: () => void;   // 追加ロードコールバック
  hasMore?: boolean;          // さらに古いメッセージが存在するか
  isLoadingMore?: boolean;    // ロード中フラグ
}
```

スクロールハンドラー（上端到達で追加ロード）:

```typescript
const handleScroll = useCallback(() => {
  if (!messagesContainerRef.current || !onLoadMore || !hasMore || isLoadingMore) return;
  if (messagesContainerRef.current.scrollTop === 0) {
    onLoadMore();
  }
}, [onLoadMore, hasMore, isLoadingMore]);
```

表示要素:

- ロード中: `読み込み中...` テキスト表示
- 追加データあり: `↑ 上にスクロールして過去のメッセージを表示` ガイドテキスト表示

---

## 変更ファイル一覧

### バックエンド

| ファイル | 変更内容 |
|---|---|
| `backend/api/models/database.py` | `get_chat_messages_async` に `before_id` / `latest_first` 追加 |
| `backend/api/services/chat_history_service.py` | `has_more` / `oldest_id` 対応 |
| `backend/api/routes/chat.py` | `limit` / `before_id` クエリパラメータ追加・`NoResultFound` 対応 |

### フロントエンド

| ファイル | 変更内容 |
|---|---|
| `frontend/src/services/api.ts` | `getChatHistory` 分ページパラメータ追加 |
| `frontend/src/pages/ChatPage.tsx` | 遅延ロード状態管理・`loadMoreHistory` 関数・仮想スクロール制御 |
| `frontend/src/components/Chat/ChatMessages.tsx` | `onLoadMore` / `hasMore` / `isLoadingMore` props・上端スクロール検知 |
| `frontend/src/components/OptimizedChatMessage.tsx` | EXECUTE_FLOW 非表示・assistant 幅 100% 修正 |
| `frontend/src/components/ARSFlowForm.tsx` | フォーム幅 `width: 100%` 修正 |

---

**ドキュメントバージョン**: 1.0
**作成日**: 2026-02-26
**対応コミット**: `26e5559` (fix: チャット画面のフォーム重叠バグ修正と履歴遅延ロード実装)
