# デジタルヒューマン機能 開発タスクリスト

## フェーズ1: バックエンド改修

-   [ ] **タスク1.1: 設定ファイルの更新**
    -   [ ] `backend/config.toml` に `[byteplus]` セクションを追加し、`appid` と `token` を定義する。
-   [ ] **タスク1.2: 認証情報提供APIの実装**
    -   [ ] `/api/v1/digitalhuman/config` (仮) エンドポイントを作成する。
    -   [ ] `config.toml` からBytePlusの認証情報を読み込み、JSON形式で返す処理を実装する。

## フェーズ2: フロントエンド基盤構築

-   [ ] **タスク2.1: 既存コードの改修**
    -   [ ] `frontend/src/pages/ChatPage.tsx`: デジタルヒューマン表示ロジックの追加
    -   [ ] `frontend/src/components/Layout.tsx`: デジタルヒューマン表示エリアのレイアウト調整
    -   [ ] `frontend/src/hooks/useChatPageState.ts`: デジタルヒューマン関連の状態管理を追加
    -   [ ] `frontend/src/pages/LlmConfigPage.tsx` (または設定画面): BytePlus設定セクションを追加し、`appid`と`token`の入力フォームを実装する。
-   [ ] **タスク2.2: 新規UIコンポーネントの作成**
    -   [ ] `frontend/src/components/DigitalHuman/DigitalHumanButton.tsx`
    -   [ ] `frontend/src/components/DigitalHuman/DigitalHumanView.tsx`
    -   [ ] `frontend/src/components/DigitalHuman/MicrophoneButton.tsx`
-   [ ] **タスク2.3: BytePlus RTC SDKの導入**
    -   [ ] `frontend/package.json` にBytePlus RTC SDKを追加
    -   [ ] SDKの初期化処理を実装
-   [ ] **タスク2.4: カスタムフック `useBytePlus.ts` の作成**
    -   [ ] `frontend/src/hooks/useBytePlus.ts` を新規作成
    -   [ ] フックの基本構造を作成
    -   [ ] 状態管理（接続ステータス、エラーなど）のロジックを追加

## フェーズ3: サービス連携

-   [ ] **タスク3.1: バックエンドとの連携**
    -   [ ] フロントエンドからバックエンドの `/api/v1/digitalhuman/config` を呼び出し、APIキーを取得する処理を実装する。
-   [ ] **タスク3.2: WebSocket接続の実装**
    -   [ ] `useBytePlus.ts` に `connect` / `disconnect` 関数を実装
    -   [ ] バックエンドから取得した認証情報 (`appid`, `token`) を使ってBytePlusに接続するロジックを実装
-   [ ] **タスク3.3: RTCストリームの受信と描画**
    -   [ ] `connect` 成功時にRTCストリームを取得
    -   [ ] 取得したストリームを `DigitalHumanView.tsx` に渡し、`<video>` 要素で再生
-   [ ] **タスク3.4: STT (Speech-to-Text) 連携**
    -   [ ] マイクからの音声データを取得する処理を実装
    -   [ ] 取得した音声データをWebSocket経由でBytePlusに送信
    -   [ ] 変換されたテキストデータを受信

## フェーズ4: 対話フローの実装

-   [ ] **タスク4.1: バックエンド (LLM) との連携**
    -   [ ] STTで得られたテキストを既存のチャットボットバックエンドに送信
    -   [ ] バックエンドからLLMの応答テキストを受信
-   [ ] **タスク4.2: TTS (Text-to-Speech) 連携**
    -   [ ] LLMの応答テキストをWebSocket経由でBytePlusに送信
    -   [ ] TTSから生成された音声ストリームを受信
-   [ ] **タスク4.3: デジタルヒューマンの駆動**
    -   [ ] TTSの音声ストリームをデジタルヒューマン駆動用にBytePlusに送信
    -   [ ] リップシンクされた映像・音声がRTCストリームで更新されることを確認

## フェーズ5: 仕上げとテスト

-   [ ] **タスク5.1: エラーハンドリング**
    -   [ ] WebSocket接続エラー
    -   [ ] APIエラー
    -   [ ] マイクアクセス拒否
-   [ ] **タスク5.2: 統合テスト**
    -   [ ] E2E（End-to-End）での対話フローを確認
    -   [ ] パフォーマンス（遅延）の測定
-   [ ] **タスク5.3: コードリファクタリングとドキュメント整備**
    -   [ ] コードの可読性向上
    -   [ ] 実装に関するコメント追記