# 開発ガイドライン

このドキュメントでは、チャットボットシステムの開発に関するガイドラインとベストプラクティスについて説明します。

## コーディング規約

### Pythonコーディング規約

#### 全般
- **PEP 8**に準拠したコーディングスタイル
- **型ヒント**の使用（Python 3.8+）
- **docstring**の記述（Googleスタイル）
- **意味のある変数名**と関数名の使用
- **1関数1責任**の原則

#### 例
```python
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

def process_user_input(user_input: str, session_id: str) -> Dict[str, Any]:
    """
    ユーザー入力を処理してレスポンスを生成する
    
    Args:
        user_input: ユーザーからの入力テキスト
        session_id: セッション識別子
        
    Returns:
        処理結果を含む辞書
        
    Raises:
        ValueError: 入力が無効な場合
    """
    if not user_input or not user_input.strip():
        raise ValueError("User input cannot be empty")
    
    try:
        # 処理ロジック
        result = {"response": "Processed", "session_id": session_id}
        logger.info(f"Processed input for session {session_id}")
        return result
    except Exception as e:
        logger.error(f"Error processing input: {e}")
        raise
```

### TypeScriptコーディング規約

#### 全般
- **ESLint**と**Prettier**を使用したコードフォーマット
- **厳格な型チェック**の有効化
- **意味のあるインターフェース**の定義
- **関数型プログラミング**の原則の適用
- **カスタムフック**の適切な使用

#### 例
```typescript
interface UserMessage {
  id: string;
  content: string;
  timestamp: Date;
  sessionId: string;
}

interface ChatResponse {
  response: string;
  sessionId: string;
  timestamp: Date;
}

const processUserMessage = async (
  message: UserMessage
): Promise<ChatResponse> => {
  if (!message.content || message.content.trim() === '') {
    throw new Error('Message content cannot be empty');
  }

  try {
    const response = await chatApi.sendMessage(message);
    return {
      response: response.data.content,
      sessionId: message.sessionId,
      timestamp: new Date(),
    };
  } catch (error) {
    console.error(`Error processing message: ${error}`);
    throw error;
  }
};
```

## プロジェクト構造

### バックエンド構造
```
backend/
├── api/                    # API関連コード
│   ├── core/              # コアモジュール
│   │   ├── config_manager.py    # 統合設定管理
│   │   ├── utils.py            # ユーティリティ
│   │   ├── qdrant_manager.py   # Qdrant管理
│   │   └── config_models.py    # 設定モデル
│   ├── routes/            # APIルート
│   │   ├── chat.py            # チャット関連ルート
│   │   ├── llm_config.py      # LLM設定関連ルート
│   │   ├── knowledge.py       # ナレッジ管理関連ルート
│   │   └── config.py          # 設定管理関連ルート
│   ├── services/          # ビジネスロジック
│   │   ├── chat_service.py    # チャットサービス
│   │   ├── base_service.py    # ベースサービスクラス
│   │   └── chat_history_service.py  # チャット履歴サービス
│   ├── models/            # データモデル
│   │   ├── config_models.py   # 設定関連モデル
│   │   └── database_models.py # データベースモデル
│   └── tests/             # テストコード
├── main.py                # アプリケーションエントリーポイント
├── requirements.txt       # Python依存関係
├── pyproject.toml         # プロジェクト設定
├── pytest.ini            # テスト設定
├── config.toml            # TOML設定ファイル
└── .env                  # 環境変数
```

### フロントエンド構造
```
frontend/
├── src/
│   ├── components/        # 再利用可能なコンポーネント
│   │   ├── common/       # 共通コンポーネント
│   │   │   ├── DataTable.tsx      # データテーブル
│   │   │   ├── ErrorAlert.tsx     # エラーアラート
│   │   │   └── LoadingSpinner.tsx # ローディングスピナー
│   │   ├── ChatInput.tsx    # チャット入力コンポーネント
│   │   ├── Layout.tsx       # メインレイアウト
│   │   └── VirtualizedMessageList.tsx  # 仮想化メッセージリスト
│   ├── pages/            # ページコンポーネント
│   │   ├── ChatPage.tsx     # チャットページ
│   │   ├── LlmConfigPage.tsx # LLM設定ページ
│   │   └── KnowledgePage.tsx # ナレッジ管理ページ
│   ├── hooks/            # カスタムフック
│   │   ├── useApi.ts       # API通信フック
│   │   ├── useChatState.ts # チャット状態管理フック
│   │   └── useConfig.ts    # 設定管理フック
│   ├── services/         # APIサービス
│   │   └── api.ts          # APIクライアント
│   ├── utils/            # ユーティリティ関数
│   ├── types/            # TypeScript型定義
│   └── tests/            # テストコード
├── public/               # 静的アセット
├── package.json          # Node.js依存関係
├── tsconfig.json         # TypeScript設定
├── vite.config.ts        # Vite設定
├── jest.config.js        # テスト設定
└── .env                  # 環境変数
```

## テストガイドライン

### テストの種類
1. **ユニットテスト**: 個々の関数やコンポーネントのテスト
2. **統合テスト**: 複数のコンポーネントやモジュールの連携テスト
3. **APIテスト**: APIエンドポイントのテスト
4. **エンドツーエンドテスト**: ユーザー操作のシミュレーション

### テストカバレッジ
- **最低50%**のコードカバレッジを目指す
- **重要なビジネスロジック**は80%以上カバレッジを目指す
- **エラーハンドリング**のテストを含める

### Pythonテスト例
```python
import pytest
from unittest.mock import Mock, patch
from api.services.chat_service import ChatService
from api.core.config_manager import config_manager

class TestChatService:
    @pytest.fixture
    def chat_service(self):
        return ChatService()
    
    def test_send_message(self, chat_service):
        # テストデータ
        message = "Hello, world!"
        session_id = "test-session"
        
        # モックの設定
        with patch.object(chat_service, '_process_message') as mock_process:
            mock_process.return_value = {"response": "Test response"}
            
            # テスト実行
            result = chat_service.send_message(message, session_id)
            
            # アサーション
            assert result["response"] == "Test response"
            mock_process.assert_called_once_with(message, session_id)
    
    def test_send_message_empty_input(self, chat_service):
        # 空の入力テスト
        with pytest.raises(ValueError):
            chat_service.send_message("", "test-session")
    
    def test_config_integration(self, chat_service):
        # 設定管理との統合テスト
        original_model = config_manager.get_value("llm", "model_name")
        
        # 設定を変更
        config_manager.set_value("llm", "model_name", "test-model")
        
        # 変更が反映されているか確認
        assert config_manager.get_value("llm", "model_name") == "test-model"
        
        # 設定を元に戻す
        config_manager.set_value("llm", "model_name", original_model)
```

### TypeScriptテスト例
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useChat } from '../hooks/useChat';
import { useApi } from '../hooks/useApi';
import { ChatService } from '../services/chat';

// モックの設定
jest.mock('../hooks/useApi');
jest.mock('../services/chat');
const mockedUseApi = useApi as jest.Mocked<typeof useApi>;
const mockedChatService = ChatService as jest.Mocked<typeof ChatService>;

describe('useChat hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('sends message successfully', async () => {
    // APIモックの設定
    const mockApi = {
      post: jest.fn().mockResolvedValue({
        data: { response: 'Test response', sessionId: 'test-session' }
      })
    };
    mockedUseApi.mockReturnValue(mockApi);

    // カスタムフックのテスト
    const { result } = renderHook(() => useChat('test-session'));
    
    // メッセージ送信
    await act(async () => {
      await result.current.sendMessage('Hello, world!');
    });

    // アサーション
    expect(mockApi.post).toHaveBeenCalledWith('/api/chat/send', {
      message: 'Hello, world!',
      session_id: 'test-session'
    });
    expect(result.current.messages).toHaveLength(1);
  });

  test('handles API errors', async () => {
    // APIエラーモック
    const mockApi = {
      post: jest.fn().mockRejectedValue(new Error('API Error'))
    };
    mockedUseApi.mockReturnValue(mockApi);

    const { result } = renderHook(() => useChat('test-session'));
    
    // エラーハンドリングのテスト
    await act(async () => {
      await result.current.sendMessage('Hello, world!');
    });

    expect(result.current.error).toBe('API Error');
  });
});
```

## Gitワークフロー

### ブランチ戦略
- **main**: 本番環境用ブランチ（保護）
- **develop**: 開発用ブランチ
- **feature/**: 機能開発用ブランチ
- **hotfix/**: 緊急修正用ブランチ

### コミットメッセージ規約
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

#### typeの種類
- **feat**: 新機能
- **fix**: バグ修正
- **docs**: ドキュメントのみの変更
- **style**: コードフォーマット（セミコロンなど）
- **refactor**: リファクタリング
- **test**: テストの追加・修正
- **chore**: ビルドプロセスや補助ツールの変更

#### 例
```
feat(chat): add message streaming functionality

Add real-time message streaming to improve user experience.
Messages are now displayed as they are generated by the LLM.

Closes #123
```

### プルリクエストプロセス
1. **ブランチの作成**: `git checkout -b feature/new-feature develop`
2. **変更のコミット**: 小さな単位でコミット
3. **プッシュ**: `git push origin feature/new-feature`
4. **プルリクエストの作成**: developブランチに対して作成
5. **コードレビュー**: 少なくとも1人のレビュアーが必要
6. **CI/CDのパス**: 自動テストがパスすること
7. **マージ**: マージ後、ブランチを削除

## コードレビューガイドライン

### レビューポイント
1. **コードの正確性**: 機能要件を満たしているか
2. **コードの可読性**: 理解しやすいコードか
3. **テストカバレッジ**: 適切なテストがあるか
4. **パフォーマンス**: 効率的な実装か
5. **セキュリティ**: セキュリティ上の問題がないか
6. **一貫性**: プロジェクトのコーディング規約に従っているか

### レビューコメントの例
```
## 全体的な感想
良い実装だと思います。特にエラーハンドリングが適切に行われています。

## 主要なコメント
1. **パフォーマンス**: `process_data`関数で大きなリストを処理する際、メモリ使用量が多くなる可能性があります。ジェネレータを使用した実装を検討してください。
2. **テスト**: エッジケースのテストが不足しています。空の入力やnull値のテストを追加してください。
3. **ドキュメント**: 関数のdocstringに戻り値の型情報を追加してください。

## 軽微なコメント
- 25行目: 変数名を`temp`から`temporary_data`に変更するとより意味が明確になります
- 42行目: マジックナンバー`3000`を定数として定義してください
```

## デバッグガイドライン

### ロギング
- **適切なログレベル**の使用
- **構造化ログ**の出力
- **機密情報**のログ出力禁止

#### Pythonロギング例
```python
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def process_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"Processing request for endpoint", extra={
        "endpoint": request_data.get("endpoint"),
        "method": request_data.get("method"),
        "request_id": request_data.get("request_id")
    })
    
    try:
        # 処理ロジック
        result = {"status": "success"}
        logger.debug("Request processed successfully", extra={"result": result})
        return result
    except Exception as e:
        logger.error(f"Error processing request: {e}", extra={
            "error": str(e),
            "request_id": request_data.get("request_id")
        })
        raise
```

#### TypeScriptロギング例
```typescript
import logger from '../utils/logger';

interface RequestData {
  endpoint: string;
  method: string;
  requestId: string;
}

const processRequest = async (requestData: RequestData) => {
  logger.info('Processing request', {
    endpoint: requestData.endpoint,
    method: requestData.method,
    requestId: requestData.requestId,
  });

  try {
    const result = { status: 'success' };
    logger.debug('Request processed successfully', { result });
    return result;
  } catch (error) {
    logger.error('Error processing request', {
      error: error instanceof Error ? error.message : 'Unknown error',
      requestId: requestData.requestId,
    });
    throw error;
  }
};
```

### デバッグツール
- **VS Code Debugger**: ブレークポイントとステップ実行
- **ブラウザ開発者ツール**: フロントエンドのデバッグ
- **Postman**: APIエンドポイントのテスト
- **Python Debugger (pdb)**: バックエンドのデバッグ

## パフォーマンス最適化

### バックエンド最適化
- **非同期処理**: I/Oバウンドな処理にはasync/awaitを使用
- **キャッシュ**: 頻繁にアクセスするデータはキャッシュ
- **データベースクエリ**: 効率的なクエリの使用
- **メモリ管理**: 大きなデータはストリーム処理

### フロントエンド最適化
- **コード分割**: 動的インポートによるバンドルサイズの削減
- **メモ化**: 再計算の防止
- **仮想化**: 大きなリストの効率的なレンダリング
- **イメージ最適化**: 適切なサイズとフォーマットの使用

## セキュリティガイドライン

### 入力バリデーション
- **サーバーサイドバリデーション**: クライアントサイドのみに依存しない
- **型チェック**: 期待するデータ型の検証
- **長さ制限**: 入力長の制限
- **サニタイズ**: 危険な文字の除去

### 認証と認可
- **JWTトークン**: 状態lessな認証
- **ロールベースアクセス制御**: 適切な権限管理
- **APIキー**: 外部サービスアクセスの制限
- **レート制限**: APIの過剰使用防止

### データ保護
- **HTTPS**: 通信の暗号化
- **環境変数**: 機密情報の管理
- **ハッシュ化**: パスワードの安全な保存
- **ログマスキング**: 機密情報のログ出力防止

## ドキュメント作成ガイドライン

### コードドキュメント
- **docstring**: すべてのパブリック関数とクラスに記述
- **型情報**: パラメータと戻り値の型を明記
- **使用例**: 複雑な関数には使用例を追加
- **例外**: 発生する可能性のある例外を記述

### APIドキュメント
- **OpenAPI仕様**: APIの標準的なドキュメント
- **エンドポイントの説明**: 各エンドポイントの目的と使用方法
- **リクエスト/レスポンス例**: 実際の使用例を提供
- **エラーコード**: 発生する可能性のあるエラーと対処法

### ユーザードキュメント
- **インストールガイド**: セットアップ手順の詳細な説明
- **使用方法**: 機能の使用方法と例
- **トラブルシューティング**: 一般的な問題と解決策
- **FAQ**: よくある質問と回答

## 継続的インテグレーション/継続的デプロイ (CI/CD)

### CI/CDパイプライン
1. **コードのプッシュ**: 自動的にテストが実行
2. **テストの実行**: ユニットテスト、統合テスト、コードカバレッジ
3. **コード品質チェック**: リンター、フォーマッター、セキュリティスキャン
4. **ビルド**: アプリケーションのビルド
5. **デプロイ**: ステージング環境へのデプロイ
6. **承認**: 本番環境へのデプロイ承認
7. **本番デプロイ**: 本番環境へのリリース

### 品質ゲート
- **テストカバレッジ**: 50%以上
- **コード品質**: リンターとフォーマッターのパス
- **セキュリティ**: セキュリティスキャンのパス
- **パフォーマンス**: パフォーマンステストのパス
- **設定検証**: 設定ファイルの妥当性確認

## まとめ

これらのガイドラインに従うことで、一貫性のある高品質なコードを維持し、チームの生産性を向上させることができます。ガイドラインはプロジェクトの進化に合わせて定期的に見直し、更新してください。