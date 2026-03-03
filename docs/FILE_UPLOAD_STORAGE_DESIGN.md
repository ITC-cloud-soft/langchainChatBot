# フォームファイルアップロード機能 設計書

## 概要

チャット内のARSFlowFormに添付ファイルアップロード機能を実装する。
ユーザーが選択したファイルをオブジェクトストレージ（MinIO / Azurite）に一時保存し、
フォーム送信時に `UPLOAD_FILES` フィールドへ**ファイルの公開URL（サードパーティリンク）**として埋め込む。

### 現状の問題

現在の `renderUploadField` はファイル名のみを `JSON.stringify(['name.pdf'])` として保持しており、
実際のファイルデータはどこにも送信・保存されていない。

---

## 方針

| 項目 | 決定 |
|------|------|
| ストレージ（開発） | MinIO（S3互換）を優先。切替可能な抽象レイヤーを設ける |
| ストレージ（本番移行先） | AWS S3 / Azure Blob Storage（環境変数で切替） |
| アップロードタイミング | ファイル選択直後に即アップロード（presigned URLは使わずサーバー中継） |
| 保存形式 | `UPLOAD_FILES` = `[{"name":"foo.pdf","url":"http://..."}]` の JSON 文字列 |
| 移行容易性 | `StorageService` を抽象クラスとして実装、バックエンドを env で切替 |

---

## アーキテクチャ

```
[ユーザーがファイル選択]
        ↓
[ARSFlowForm] → POST /api/upload/file (multipart/form-data)
        ↓
[UploadRouter] → StorageService.upload()
        ↓
[MinIO / Azurite / S3 / Azure Blob]
        ↓
 戻り値: { url: "http://minio:9000/chatbot/uuid_filename.pdf", name: "filename.pdf" }
        ↓
[ARSFlowForm] UPLOAD_FILES に [{name, url}] を追加保持
        ↓
[フォーム送信] assembleMaintblnameValue() で UPLOAD_FILES をそのまま MainTblName_value に含める
        ↓
[ARS → SSFlow] UPLOAD_FILES フィールドに URL リストが渡される
```

---

## バックエンド設計

### 1. 新規ファイル構成

```
backend/api/
├── services/
│   └── storage_service.py      # 新規：StorageService 抽象 + MinIO / Azurite 実装
├── routes/
│   └── upload.py               # 新規：POST /api/upload/file
```

### 2. `storage_service.py` インターフェース

```python
class StorageService:
    """ストレージ抽象基底クラス（切替可能）"""
    async def upload_file(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        """ファイルをアップロードして公開URLを返す"""
        raise NotImplementedError

class MinioStorageService(StorageService):
    """MinIO (S3互換) 実装"""
    # boto3 (aiobotocore) を使用
    # バケット: chatbot-uploads
    # URL例: http://localhost:9000/chatbot-uploads/{uuid}_{filename}

class AzuriteStorageService(StorageService):
    """Azure Blob Storage / Azurite 実装"""
    # azure-storage-blob を使用
    # コンテナ: chatbot-uploads
    # URL例: http://localhost:9010/devstoreaccount1/chatbot-uploads/{uuid}_{filename}

def get_storage_service() -> StorageService:
    """環境変数 STORAGE_BACKEND で切替: minio (デフォルト) / azurite / s3 / azure"""
    backend = os.getenv("STORAGE_BACKEND", "minio")
    ...
```

### 3. `/api/upload/file` エンドポイント

```
POST /api/upload/file
Content-Type: multipart/form-data

Request:
  file: UploadFile   (必須)

Response 200:
  {
    "name": "document.pdf",
    "url": "http://localhost:9000/chatbot-uploads/a1b2c3_document.pdf"
  }

Response 400: ファイルサイズ超過 / 拡張子不許可
Response 503: ストレージ接続エラー
```

制約:
- 最大ファイルサイズ: **10MB**
- 許可拡張子: pdf, xls, xlsx, doc, docx, png, jpg, jpeg, zip

### 4. 環境変数

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `STORAGE_BACKEND` | `minio` | `minio` / `azurite` / `s3` / `azure` |
| `MINIO_ENDPOINT` | `http://minio:9000` | MinIO エンドポイント |
| `MINIO_ACCESS_KEY` | `admin` | MinIO アクセスキー |
| `MINIO_SECRET_KEY` | `Admin123` | MinIO シークレットキー |
| `MINIO_BUCKET` | `chatbot-uploads` | バケット名 |
| `MINIO_PUBLIC_ENDPOINT` | （MINIO_ENDPOINTと同じ） | クライアントからアクセス可能なURL |
| `AZURITE_CONNECTION_STRING` | `DefaultEndpointsProtocol=http;...` | Azurite 接続文字列 |
| `AZURITE_CONTAINER` | `chatbot-uploads` | コンテナ名 |
| `AZURITE_PUBLIC_ENDPOINT` | `http://localhost:9010` | クライアントからアクセス可能なURL |

---

## フロントエンド設計

### 変更対象: `ARSFlowForm.tsx` → `renderUploadField()`

#### 現状
```typescript
// ファイル名のみ保持（実際のアップロードなし）
handleChange(api_param_name, JSON.stringify(['document.pdf']))
```

#### 変更後
```typescript
// ファイル選択 → 即アップロード → { name, url } を保持
const handleFileChange = async (e) => {
  const file = e.target.files[0];
  // 1. ローディング表示
  // 2. POST /api/upload/file (FormData)
  // 3. 返却 { name, url } を fileList に追加
  // 4. handleChange(api_param_name, JSON.stringify([{name, url}, ...]))
};
```

#### UIの変化

| 状態 | 表示 |
|------|------|
| アップロード中 | CircularProgress + ファイル名 |
| 完了 | ファイル名 + リンクアイコン（URL） + 削除ボタン |
| 読み取り専用 | ファイル名 + リンクアイコン（クリックで開く） |

### `UPLOAD_FILES` の格納形式変更

```typescript
// 変更前（ファイル名のみ）
"[\"document.pdf\"]"

// 変更後（name + url オブジェクト配列）
"[{\"name\":\"document.pdf\",\"url\":\"http://localhost:9000/chatbot-uploads/abc_document.pdf\"}]"
```

---

## docker-compose 対応

`docker-compose.full.dev.yml` に MinIO サービスを追加（3rdtools から移動）、
および chatbot-backend に環境変数を追加:

```yaml
chatbot-backend:
  environment:
    - STORAGE_BACKEND=minio
    - MINIO_ENDPOINT=http://minio:9000
    - MINIO_ACCESS_KEY=admin
    - MINIO_SECRET_KEY=Admin123
    - MINIO_BUCKET=chatbot-uploads
    - MINIO_PUBLIC_ENDPOINT=http://localhost:9000  # ブラウザからアクセス
```

---

## 実装ファイル一覧

### バックエンド（新規・変更）

| ファイル | 種別 | 内容 |
|----------|------|------|
| `backend/api/services/storage_service.py` | 新規 | StorageService抽象 + MinIO/Azurite実装 |
| `backend/api/routes/upload.py` | 新規 | POST /api/upload/file エンドポイント |
| `backend/api/routes/__init__.py` | 変更 | upload ルーター登録 |
| `backend/requirements.txt` | 変更 | `aiobotocore` または `boto3` 追加 |

### フロントエンド（変更）

| ファイル | 内容 |
|----------|------|
| `frontend/src/components/ARSFlowForm.tsx` | renderUploadField をアップロード対応に改修 |

### インフラ（変更）

| ファイル | 内容 |
|----------|------|
| `docker-compose.full.dev.yml` | minio サービス追加 + chatbot-backend env 追加 |

---

## テスト方針

### バックエンドテスト（pytest）

`backend/tests/test_upload.py`:
- MinIO 未起動時の 503 レスポンス
- 正常アップロード → URL 返却
- ファイルサイズ超過 → 400
- 拡張子不許可 → 400

### フロントエンド動作確認

1. フォームでファイル選択 → アップロード中スピナー表示
2. アップロード完了 → ファイル名 + リンク表示
3. フォーム送信 → `UPLOAD_FILES` に URL が含まれることを確認
4. submitted状態での読み取り専用表示 + リンクが開けること

---

## 移行時の変更点（本番: AWS S3 / Azure Blob）

環境変数のみ変更で移行可能:

```bash
# AWS S3 への移行例
STORAGE_BACKEND=s3
AWS_S3_BUCKET=my-chatbot-uploads
AWS_REGION=ap-northeast-1
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
MINIO_PUBLIC_ENDPOINT=https://my-chatbot-uploads.s3.ap-northeast-1.amazonaws.com
```

---

**ドキュメントバージョン**: 1.0
**作成日**: 2026-03-03
