# Novu通知システム テストスイート

このディレクトリには、Novu通知システムの統合テストが含まれています。

## 📁 ファイル構成

```
test/
├── run_tests.py                   # 統合テストスイート（メイン）
├── create_test_notifications.py   # テスト通知作成スクリプト
├── test_welcome_workflow.py       # Welcome通知ワークフローテスト
├── test_api_workflow.py           # API作成ワークフローテスト
└── README.md                      # このファイル
```

## 🚀 使用方法

### 1. 全機能テスト（推奨）

すべての通知機能を包括的にテストします：

```bash
python run_tests.py
```

**テスト内容:**
- ✅ 通知送信（Novu API）
- ✅ 通知リスト取得
- ✅ 未読数取得
- ✅ 単一通知既読マーク
- ✅ 全通知一括既読マーク
- ✅ 通知削除

---

### 2. クイックテスト

基本的な通知機能のみを素早くテストします：

```bash
python run_tests.py --quick
```

**テスト内容:**
- ✅ 通知リスト取得
- ✅ 未読数取得
- ✅ 単一通知既読マーク

---

### 3. テスト通知の作成

開発やテスト用に複数の通知を素早く作成できます：

```bash
python create_test_notifications.py
```

**作成される通知:**
- 📘 情報通知（INFO）- 新機能のお知らせ
- ✅ 成功通知（SUCCESS）- 処理完了メッセージ
- ⚠️ 警告通知（WARNING）- 注意喚起
- ❌ エラー通知（ERROR）- エラー報告
- 📘 追加情報通知（INFO）

このスクリプトは自動的に5種類の異なる通知を作成し、フロントエンドでの表示確認に便利です。

**カスタマイズ方法:**

スクリプト内の以下の部分を編集することで、通知内容をカスタマイズできます：

```python
# ユーザー情報の変更
subscriber_id = "1"  # 対象ユーザーID
user_name = "Admin User"  # 表示名

# 通知タイプの追加・変更
notifications = [
    ("info", "カスタム情報"),
    ("success", "カスタム成功"),
    # 必要に応じて追加...
]
```

---

### 4. ワークフローテスト

特定のワークフローをテストする場合は、個別のスクリプトを使用します：

#### Welcome通知ワークフロー
```bash
python test_welcome_workflow.py
```

複数のテストケースで`welcome-notification`ワークフローをテストします。

#### API作成ワークフロー
```bash
python test_api_workflow.py
```

API経由で作成した`welcome-notification-api`ワークフローをテストします。

---

## 📋 前提条件

### 必要なサービス

以下のサービスが起動している必要があります：

1. **Novu API** - `http://localhost:3000`
2. **Backend API** - `http://localhost:8000`
3. **MySQL Database**
4. **Qdrant Vector DB**

### サービス起動方法

```bash
# プロジェクトルートで実行
cd c:\Users\dev002\OneDrive\Documents\projects\github\aiportal.chatbot

# 全サービスを起動
docker compose -f docker-compose.full.dev.yml up -d
```

### 認証情報

テストは以下の認証情報を使用します：

- **Username**: `admin`
- **Password**: `admin123`
- **Novu API Key**: `c47cfb7a083c4e27f9d1b523a20ed59f`

---

## 🎯 テスト結果の見方

### 成功例

```
======================================================================
Novu通知システム - 全機能テスト
======================================================================

🔐 ログイン中...
✅ ログイン成功

【テスト1】通知リスト取得
✅ 成功: 5件の通知を取得

【テスト2】未読数取得
✅ 成功: 未読数 3件

...

======================================================================
テスト結果サマリー
======================================================================

総テスト数: 6
✅ 成功: 6
❌ 失敗: 0
⚠️  スキップ: 0

🎉 全てのテストが成功しました！
```

### 失敗時のトラブルシューティング

#### ログイン失敗
```
❌ ログイン失敗: 401
```
**解決方法**: バックエンドが起動しているか確認
```bash
docker logs chatbot-backend --tail 20
```

#### 通知取得失敗
```
❌ 通知取得失敗: 500
```
**解決方法**: バックエンドログを確認
```bash
docker logs chatbot-backend --tail 50
```

#### Novu API接続エラー
```
❌ 接続エラー: Novu API に接続できません
```
**解決方法**: Novuサービスが起動しているか確認
```bash
docker ps | grep novu
```

---

## 🔧 カスタマイズ

### API URLの変更

テストスクリプト内の定数を変更します：

```python
BACKEND_URL = "http://localhost:8000"
NOVU_API_URL = "http://localhost:3000"
NOVU_API_KEY = "your-api-key-here"
```

### テストケースの追加

`run_tests.py`の`TestRunner`クラスに新しいテストメソッドを追加：

```python
def test_your_feature(self) -> bool:
    """あなたの機能テスト"""
    print("\n【テストN】あなたの機能")
    try:
        # テストロジック
        response = requests.get(...)
        
        if response.status_code == 200:
            print("✅ 成功")
            self.test_results.append(("あなたの機能", True, "OK"))
            return True
        else:
            print(f"❌ 失敗: {response.status_code}")
            self.test_results.append(("あなたの機能", False, response.status_code))
            return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        self.test_results.append(("あなたの機能", False, str(e)))
        return False
```

---

## 📊 テストカバレッジ

| 機能 | テスト済み | スクリプト |
|------|-----------|-----------|
| 通知リスト取得 | ✅ | `run_tests.py` |
| 未読数取得 | ✅ | `run_tests.py` |
| 単一通知既読マーク | ✅ | `run_tests.py` |
| 全通知一括既読マーク | ✅ | `run_tests.py` |
| 通知削除 | ✅ | `run_tests.py` |
| 通知送信 | ✅ | `run_tests.py` |
| テスト通知作成 | ✅ | `create_test_notifications.py` |
| Welcomeワークフロー | ✅ | `test_welcome_workflow.py` |
| APIワークフロー | ✅ | `test_api_workflow.py` |

---

## 🔗 関連ドキュメント

- **SubscriberApi分析**: `../../SUBSCRIBER_API_ANALYSIS.md`
- **Novuフレームワークガイド**: `../../NOVU_FRAMEWORK_GUIDE.md`
- **バックエンドAPI**: `http://localhost:8000/docs`
- **Novu Dashboard**: `http://localhost:4200`

---

## 💡 ヒント

1. **初回テスト前**: 必ずワークフローが作成されているか確認
   - Novu Dashboard → Workflows → `welcome-notification`

2. **テスト失敗時**: まずバックエンドログを確認
   ```bash
   docker logs chatbot-backend --tail 50
   ```

3. **通知が表示されない**: Novu Activity Feedで確認
   - `http://localhost:4200` → Activity Feed

4. **定期的なテスト**: CI/CDパイプラインに統合可能
   ```bash
   python run_tests.py --quick  # 高速チェック
   ```

---

## 📝 更新履歴

- **2026-01-22**: テストスイート統合・整理
  - 重複テストファイルを削除
  - `run_tests.py`に統合
  - ワークフローテストを独立化
  - `create_test_notifications.py`追加（テスト通知作成機能）
  - localhost硬編码削除と環境変数必須化
