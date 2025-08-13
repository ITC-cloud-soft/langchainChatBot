# システムアーキテクチャ図

## 高レベルアーキテクチャ

```mermaid
graph TB
    subgraph "ユーザーインターフェース"
        U[ユーザー]
        FE[フロントエンド<br/>React + TypeScript]
    end
    
    subgraph "アプリケーション層"
        BE[バックエンド<br/>FastAPI]
        CS[チャットサービス<br/>ChatService]
        LS[LLMサービス<br/>LangChain]
    end
    
    subgraph "データ層"
        QB[Qdrant<br/>ベクトルDB]
        CF[設定ファイル<br/>TOML]
    end
    
    subgraph "外部サービス"
        OL[Ollama<br/>埋め込みモデル]
        LM[LLM API<br/>OpenAI/Ollama]
    end
    
    U --> FE
    FE --> BE
    BE --> CS
    BE --> LS
    CS --> QB
    CS --> LS
    LS --> LM
    CS --> OL
    BE --> CF
```

## フロントエンドアーキテクチャ

```mermaid
graph TB
    subgraph "フロントエンドコンポーネント"
        subgraph "UIコンポーネント"
            CI[ChatInterface]
            LCS[LLMConfigSettings]
            KM[KnowledgeManagement]
            AL[AppLayout]
        end
        
        subgraph "状態管理"
            GS[グローバル状態<br/>Zustand]
            SS[サーバーステート<br/>React Query]
            LS[ローカル状態<br/>useState]
        end
        
        subgraph "サービス層"
            AS[APIサービス<br/>Axios]
            CH[カスタムフック<br/>useApi, useChat]
        end
        
        subgraph "ユーティリティ"
            UT[ユーティリティ関数]
            TP[型定義]
        end
    end
    
    CI --> GS
    CI --> SS
    LCS --> GS
    LCS --> SS
    KM --> GS
    KM --> SS
    AL --> GS
    
    CI --> CH
    LCS --> CH
    KM --> CH
    
    CH --> AS
    AS --> UT
    CH --> TP
```

## バックエンドアーキテクチャ

```mermaid
graph TB
    subgraph "バックエンドモジュール"
        subgraph "APIルート"
            CR[チャットルート<br/>/api/chat]
            LR[LLM設定ルート<br/>/api/llm]
            KR[ナレッジルート<br/>/api/knowledge]
            CFR[設定ルート<br/>/api/config]
        end
        
        subgraph "サービス層"
            CS[ChatService]
            QS[QdrantService]
            CMS[ConfigManagerService]
        end
        
        subgraph "コアモジュール"
            CM[ConfigManager]
            UT[Utils]
            QM[QdrantManager]
            CW[ConfigWatcher]
        end
        
        subgraph "データモデル"
            CDM[チャットモデル]
            LDM[LLMモデル]
            KDM[ナレッジモデル]
            CMM[設定モデル]
        end
    end
    
    CR --> CS
    LR --> CS
    KR --> QS
    CFR --> CMS
    
    CS --> CM
    CS --> UT
    QS --> QM
    QS --> UT
    CMS --> CM
    CMS --> CW
    
    CS --> CDM
    CS --> LDM
    QS --> KDM
    CMS --> CMM
```

## データフロー図

### チャット処理フロー

```mermaid
sequenceDiagram
    participant U as ユーザー
    participant FE as フロントエンド
    participant BE as バックエンド
    participant CS as ChatService
    participant LS as LangChain
    participant QB as Qdrant
    participant LLM as LLM API
    
    U->>FE: メッセージ入力
    FE->>BE: POST /api/chat/send
    BE->>CS: メッセージ処理要求
    CS->>QB: 関連ドキュメント検索
    QB-->>CS: 検索結果
    CS->>LS: LLMへのプロンプト生成
    LS->>LLM: メッセージ送信
    LLM-->>LS: レスポンス生成
    LS-->>CS: 処理結果
    CS-->>BE: チャットレスポンス
    BE-->>FE: JSONレスポンス
    FE-->>U: レスポンス表示
```

### 設定更新フロー

```mermaid
sequenceDiagram
    participant U as ユーザー
    participant FE as フロントエンド
    participant BE as バックエンド
    participant CM as ConfigManager
    participant CF as 設定ファイル
    participant CW as ConfigWatcher
    participant S as サービス
    
    U->>FE: 設定変更
    FE->>BE: POST /api/config/update
    BE->>CM: 設定更新要求
    CM->>CF: 設定ファイル更新
    CF-->>CM: 更新完了
    CM-->>BE: 更新結果
    BE-->>FE: JSONレスポンス
    FE-->>U: 設定更新完了表示
    
    Note over CW,CF: 設定ファイル監視
    CW->>CF: ファイル変更検出
    CW->>CM: 変更通知
    CM->>S: 設定更新通知
    S-->>CM: 更新完了
```

### ナレッジ管理フロー

```mermaid
sequenceDiagram
    participant U as ユーザー
    participant FE as フロントエンド
    participant BE as バックエンド
    participant QS as QdrantService
    participant OL as Ollama
    participant QB as Qdrant
    
    U->>FE: ドキュメントアップロード
    FE->>BE: POST /api/knowledge/upload
    BE->>QS: ドキュメント処理要求
    QS->>QS: ドキュメントのチャンキング
    QS->>OL: 埋め込み生成要求
    OL-->>QS: 埋め込みベクトル
    QS->>QB: ベクトル保存
    QB-->>QS: 保存完了
    QS-->>BE: 処理結果
    BE-->>FE: JSONレスポンス
    FE-->>U: アップロード完了表示
```

## コンポーネント関係図

```mermaid
graph LR
    subgraph "フロントエンド"
        FE[フロントエンド]
        CI[ChatInterface]
        LCS[LLMConfigSettings]
        KM[KnowledgeManagement]
    end
    
    subgraph "バックエンドAPI"
        BE[バックエンド]
        CR[ChatRoutes]
        LCR[LLMConfigRoutes]
        KR[KnowledgeRoutes]
        CFR[ConfigRoutes]
    end
    
    subgraph "バックエンドサービス"
        CS[ChatService]
        QS[QdrantService]
        CMS[ConfigManagerService]
    end
    
    subgraph "コアモジュール"
        CM[ConfigManager]
        QM[QdrantManager]
        UT[Utils]
    end
    
    subgraph "データストア"
        QB[Qdrant]
        CF[設定ファイル]
    end
    
    subgraph "外部サービス"
        LLM[LLM API]
        OL[Ollama]
    end
    
    CI --> CR
    LCS --> LCR
    KM --> KR
    FE --> BE
    
    CR --> CS
    LCR --> CMS
    KR --> QS
    CFR --> CMS
    
    CS --> CM
    CS --> QM
    QS --> QM
    CMS --> CM
    
    CM --> CF
    QM --> QB
    
    CS --> LLM
    QS --> OL
```

## デプロイアーキテクチャ

```mermaid
graph TB
    subgraph "クライアント"
        B[ブラウザ]
    end
    
    subgraph "ロードバランサ"
        LB[ロードバランサ<br/>Nginx]
    end
    
    subgraph "アプリケーションサーバー"
        FE1[フロントエンド1<br/>React]
        FE2[フロントエンド2<br/>React]
        BE1[バックエンド1<br/>FastAPI]
        BE2[バックエンド2<br/>FastAPI]
    end
    
    subgraph "データベース"
        QB[Qdrant<br/>Vector DB]
    end
    
    subgraph "外部サービス"
        OL[Ollama]
        LLM[LLM API]
    end
    
    subgraph "監視"
        M[監視<br/>Prometheus]
        L[ログ<br/>ELK Stack]
    end
    
    B --> LB
    LB --> FE1
    LB --> FE2
    LB --> BE1
    LB --> BE2
    
    BE1 --> QB
    BE2 --> QB
    BE1 --> OL
    BE2 --> OL
    BE1 --> LLM
    BE2 --> LLM
    
    BE1 --> M
    BE2 --> M
    BE1 --> L
    BE2 --> L
```

## 開発環境アーキテクチャ

```mermaid
graph TB
    subgraph "開発者マシン"
        D[開発者]
        IDE[IDE/エディタ]
        GC[Gitクライアント]
    end
    
    subgraph "ローカル環境"
        FE[フロントエンド<br/>React Dev Server]
        BE[バックエンド<br/>FastAPI Dev Server]
        QB[Qdrant<br/>Docker]
        OL[Ollama<br/>Local]
    end
    
    subgraph "バージョン管理"
        GR[GitHubリポジトリ]
    end
    
    subgraph "CI/CD"
        CI[GitHub Actions]
        RG[コンテナレジストリ]
    end
    
    subgraph "テスト環境"
        TE[テスト環境<br/>Docker Compose]
    end
    
    subgraph "ステージング環境"
        SE[ステージング環境<br/>Kubernetes]
    end
    
    subgraph "本番環境"
        PE[本番環境<br/>Kubernetes]
    end
    
    D --> IDE
    D --> GC
    IDE --> FE
    IDE --> BE
    GC --> GR
    
    GR --> CI
    CI --> RG
    CI --> TE
    CI --> SE
    CI --> PE
    
    FE --> BE
    BE --> QB
    BE --> OL
```

これらのアーキテクチャ図は、システムの構造、データフロー、コンポーネント間の関係を視覚的に表現しています。各図は特定の側面に焦点を当てており、システム全体を理解するのに役立ちます。