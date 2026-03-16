"""
Storage Service Module

ファイルアップロード用ストレージ抽象レイヤー。
環境変数 STORAGE_BACKEND で実装を切り替え可能:
  - minio    : MinIO (S3互換) ※デフォルト
  - azurite  : Azure Blob Storage / Azurite
  - s3       : AWS S3 (boto3)
  - azure    : Azure Blob Storage (azure-storage-blob)
"""

import os
import uuid
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 許可するファイル拡張子・最大サイズ
# ──────────────────────────────────────────────
def _get_allowed_extensions() -> set:
    """環境変数から許可する拡張子を取得"""
    default_exts = "pdf,doc,docx,xls,xlsx,csv,png,jpg,jpeg,txt,json,xml,md,zip"
    exts_str = os.getenv("ALLOWED_FILE_EXTENSIONS", default_exts)
    return {ext.strip().lower() for ext in exts_str.split(",") if ext.strip()}

def _get_max_file_size() -> int:
    """環境変数から最大ファイルサイズ（バイト）を取得"""
    max_mb = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    return max_mb * 1024 * 1024

ALLOWED_EXTENSIONS = _get_allowed_extensions()
MAX_FILE_SIZE_BYTES = _get_max_file_size()


def validate_upload(filename: str, size: int) -> None:
    """
    ファイル名・サイズを検証する。
    問題がある場合は ValueError を送出。
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"拡張子 '{ext}' は許可されていません。"
            f"許可: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    if size > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"ファイルサイズが上限 {MAX_FILE_SIZE_BYTES // (1024*1024)}MB を超えています。"
        )


def _unique_key(filename: str) -> str:
    """UUID プレフィックス付きのストレージキーを生成する。"""
    safe = filename.replace(" ", "_")
    return f"{uuid.uuid4().hex}_{safe}"


# ──────────────────────────────────────────────
# 抽象基底クラス
# ──────────────────────────────────────────────

class StorageService(ABC):
    """ストレージ操作の抽象基底クラス"""

    @abstractmethod
    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        ファイルをアップロードし、公開 URL を返す。

        Args:
            file_bytes  : ファイルの生バイト列
            filename    : 元のファイル名
            content_type: MIME タイプ

        Returns:
            str: 公開アクセス可能な URL
        """
        ...

    @abstractmethod
    async def generate_download_url(
        self,
        blob_name: str,
        expiry_hours: int = 1,
    ) -> str:
        """
        ダウンロード用の一時 URL を生成する。

        Args:
            blob_name    : Blob 名（ファイルパス）
            expiry_hours : 有効期限（時間）

        Returns:
            str: ダウンロード可能な URL
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """ストレージへの接続確認。接続可能なら True。"""
        ...


# ──────────────────────────────────────────────
# MinIO 実装（S3互換 / boto3）
# ──────────────────────────────────────────────

class MinioStorageService(StorageService):
    """
    MinIO / AWS S3 互換ストレージ実装。
    boto3 を使用。

    環境変数:
      MINIO_ENDPOINT        : MinIO エンドポイント (例: http://minio:9000)
      MINIO_ACCESS_KEY      : アクセスキー
      MINIO_SECRET_KEY      : シークレットキー
      MINIO_BUCKET          : バケット名 (デフォルト: chatbot-uploads)
      MINIO_PUBLIC_ENDPOINT : ブラウザからアクセス可能なURL (未設定時は MINIO_ENDPOINT)
    """

    def __init__(self) -> None:
        self.endpoint        = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
        self.access_key      = os.getenv("MINIO_ACCESS_KEY", "admin")
        self.secret_key      = os.getenv("MINIO_SECRET_KEY", "Admin123")
        self.bucket          = os.getenv("MINIO_BUCKET", "chatbot-uploads")
        self.public_endpoint = os.getenv("MINIO_PUBLIC_ENDPOINT", self.endpoint)

    def _get_client(self):
        """boto3 S3 クライアントを生成する。"""
        try:
            import boto3
            from botocore.client import Config
        except ImportError as e:
            raise RuntimeError(
                "boto3 が未インストールです。`pip install boto3` を実行してください。"
            ) from e

        return boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version="s3v4"),
        )

    def _ensure_bucket(self, client) -> None:
        """バケットが存在しない場合は作成し、パブリックポリシーを設定する。"""
        import json as _json
        try:
            client.head_bucket(Bucket=self.bucket)
        except Exception:
            client.create_bucket(Bucket=self.bucket)
            policy = _json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self.bucket}/*"],
                }],
            })
            client.put_bucket_policy(Bucket=self.bucket, Policy=policy)

    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        import asyncio
        import io

        key = _unique_key(filename)

        def _upload():
            client = self._get_client()
            self._ensure_bucket(client)
            client.upload_fileobj(
                io.BytesIO(file_bytes),
                self.bucket,
                key,
                ExtraArgs={"ContentType": content_type},
            )

        await asyncio.get_event_loop().run_in_executor(None, _upload)

        url = f"{self.public_endpoint}/{self.bucket}/{key}"
        logger.info(f"[MinIO] Uploaded: {url}")
        return url

    async def generate_download_url(
        self,
        blob_name: str,
        expiry_hours: int = 1,
    ) -> str:
        """MinIO は公開 URL なので、そのまま返す"""
        url = f"{self.public_endpoint}/{self.bucket}/{blob_name}"
        logger.info(f"[MinIO] Download URL: {url}")
        return url

    async def health_check(self) -> bool:
        import asyncio

        def _check():
            try:
                client = self._get_client()
                client.list_buckets()
                return True
            except Exception as e:
                logger.warning(f"[MinIO] health_check failed: {e}")
                return False

        return await asyncio.get_event_loop().run_in_executor(None, _check)


# ──────────────────────────────────────────────
# Azurite 実装（Azure Blob Storage）
# ──────────────────────────────────────────────

class AzuriteStorageService(StorageService):
    """
    Azure Blob Storage / Azurite 実装。
    azure-storage-blob を使用。

    環境変数:
      AZURE_CONNECTION_STRING   : 接続文字列（本番用）
      AZURE_CONTAINER           : コンテナ名 (デフォルト: chatbot)
      AZURE_STORAGE_ACCOUNT_URL : ストレージアカウント URL
      
      または開発環境用:
      AZURITE_CONNECTION_STRING : 接続文字列（Azurite用）
      AZURITE_CONTAINER         : コンテナ名
      AZURITE_PUBLIC_ENDPOINT   : ブラウザからアクセス可能なURL
    """

    _DEFAULT_CONN = (
        "DefaultEndpointsProtocol=http;"
        "AccountName=devstoreaccount1;"
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tiqIHTWh3AGHInFVQ==;"
        "BlobEndpoint=http://azurite:10000/devstoreaccount1;"
    )

    def __init__(self) -> None:
        self.conn_str = os.getenv("AZURE_CONNECTION_STRING") or os.getenv("AZURITE_CONNECTION_STRING", self._DEFAULT_CONN)
        self.container = os.getenv("AZURE_CONTAINER") or os.getenv("AZURITE_CONTAINER", "chatbot")
        self.account_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL", "http://localhost:9010")
        self.is_production = bool(os.getenv("AZURE_CONNECTION_STRING"))

    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        import asyncio
        from datetime import datetime

        key = _unique_key(filename)

        def _upload():
            try:
                from azure.storage.blob import BlobServiceClient, ContentSettings
            except ImportError as e:
                raise RuntimeError(
                    "azure-storage-blob が未インストールです。"
                    "`pip install azure-storage-blob` を実行してください。"
                ) from e

            client = BlobServiceClient.from_connection_string(self.conn_str)
            container_client = client.get_container_client(self.container)
            
            try:
                container_client.create_container()
                logger.info(f"[Azure] コンテナを作成しました: {self.container}")
            except Exception:
                pass
            
            blob_client = container_client.get_blob_client(key)
            blob_client.upload_blob(
                file_bytes,
                content_settings=ContentSettings(content_type=content_type),
                overwrite=True,
            )
            
            return blob_client.url

        blob_url = await asyncio.get_event_loop().run_in_executor(None, _upload)
        
        backend_name = "Azure" if self.is_production else "Azurite"
        logger.info(f"[{backend_name}] Uploaded: {blob_url}")
        return blob_url

    async def generate_download_url(
        self,
        blob_name: str,
        expiry_hours: int = 1,
    ) -> str:
        """SAS URL を生成してダウンロード用の一時 URL を返す"""
        import asyncio
        from datetime import datetime, timedelta

        def _generate():
            try:
                from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
            except ImportError as e:
                raise RuntimeError(
                    "azure-storage-blob が未インストールです。"
                ) from e

            client = BlobServiceClient.from_connection_string(self.conn_str)
            blob_client = client.get_blob_client(container=self.container, blob=blob_name)
            
            account_name = client.account_name
            account_key = None
            
            for part in self.conn_str.split(';'):
                if part.startswith('AccountKey='):
                    account_key = part.split('=', 1)[1]
                    break
            
            if not account_key:
                logger.warning("[Azure] AccountKey not found, returning direct URL")
                return blob_client.url
            
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=self.container,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours),
            )
            
            sas_url = f"{blob_client.url}?{sas_token}"
            return sas_url

        sas_url = await asyncio.get_event_loop().run_in_executor(None, _generate)
        
        backend_name = "Azure" if self.is_production else "Azurite"
        logger.info(f"[{backend_name}] Generated SAS URL (expires in {expiry_hours}h)")
        return sas_url

    async def health_check(self) -> bool:
        import asyncio

        def _check():
            try:
                from azure.storage.blob import BlobServiceClient
                client = BlobServiceClient.from_connection_string(self.conn_str)
                list(client.list_containers(max_results=1))
                return True
            except Exception as e:
                backend_name = "Azure" if self.is_production else "Azurite"
                logger.warning(f"[{backend_name}] health_check failed: {e}")
                return False

        return await asyncio.get_event_loop().run_in_executor(None, _check)


# ──────────────────────────────────────────────
# ファクトリ関数
# ──────────────────────────────────────────────

_instance: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """
    環境変数 STORAGE_BACKEND に応じた StorageService インスタンスを返す。
    シングルトンとしてキャッシュ。

    STORAGE_BACKEND:
      minio   (デフォルト) → MinioStorageService
      azurite              → AzuriteStorageService
      s3                   → MinioStorageService (エンドポイントは AWS)
      azure                → AzuriteStorageService (接続文字列を本番用に設定)
    """
    global _instance
    if _instance is not None:
        return _instance

    backend = os.getenv("STORAGE_BACKEND", "minio").lower()
    if backend in ("minio", "s3"):
        _instance = MinioStorageService()
    elif backend in ("azurite", "azure"):
        _instance = AzuriteStorageService()
    else:
        logger.warning(f"不明な STORAGE_BACKEND '{backend}' → MinIO をデフォルトで使用")
        _instance = MinioStorageService()

    logger.info(f"[Storage] Backend: {backend} ({type(_instance).__name__})")
    return _instance
