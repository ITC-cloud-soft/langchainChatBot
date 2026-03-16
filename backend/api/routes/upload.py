"""
File Upload API Route

POST /api/upload/file              - ファイルをオブジェクトストレージへアップロードし公開URLを返す
GET  /api/upload/download-url      - ダウンロード用の一時 URL を生成
GET  /api/upload/health            - ストレージ接続確認
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Query
from pydantic import BaseModel

from api.middleware import get_current_user, CurrentUser
from api.services.storage_service import get_storage_service, validate_upload

logger = logging.getLogger(__name__)

router = APIRouter()


class UploadResponse(BaseModel):
    """ファイルアップロードレスポンス"""
    name: str
    url: str


class DownloadUrlResponse(BaseModel):
    """ダウンロード URL レスポンス"""
    download_url: str
    expires_in_hours: int


class HealthResponse(BaseModel):
    """ストレージヘルスチェックレスポンス"""
    status: str
    backend: str


@router.post(
    "/file",
    response_model=UploadResponse,
    summary="ファイルアップロード",
    description="ARSFlowForm からのファイルをオブジェクトストレージにアップロードし、公開URLを返す。",
)
async def upload_file(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
) -> UploadResponse:
    """
    ファイルをストレージにアップロードする。

    - 最大 10MB
    - 許可拡張子: pdf / xls / xlsx / doc / docx / png / jpg / jpeg / zip
    """
    filename = file.filename or "unknown"

    # 拡張子バリデーション（読み込み前に検査）
    try:
        validate_upload(filename, 0)  # サイズ0でまず拡張子だけ検査
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # ストリーミング読み込みでサイズ上限チェック（10MB）
    MAX_SIZE = 10 * 1024 * 1024
    chunks = []
    total = 0
    while True:
        chunk = await file.read(64 * 1024)  # 64KB ずつ読む
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ファイルサイズが上限 ({MAX_SIZE // (1024*1024)}MB) を超えています。",
            )
        chunks.append(chunk)
    file_bytes = b"".join(chunks)

    # アップロード
    storage = get_storage_service()
    try:
        url = await storage.upload_file(
            file_bytes=file_bytes,
            filename=filename,
            content_type=file.content_type or "application/octet-stream",
        )
    except Exception as e:
        logger.error(f"[Upload] Storage error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ストレージへのアップロードに失敗しました: {str(e)}",
        )

    logger.info(f"[Upload] {current_user.username} uploaded '{filename}' -> {url}")
    return UploadResponse(name=filename, url=url)


@router.get(
    "/download-url",
    response_model=DownloadUrlResponse,
    summary="ダウンロード URL 生成",
    description="ファイルのダウンロード用一時 URL（SAS URL）を生成する。",
)
async def generate_download_url(
    blob_name: str = Query(..., description="Blob 名（ファイルパス）"),
    expiry_hours: int = Query(1, ge=1, le=24, description="有効期限（時間、1-24）"),
    current_user: CurrentUser = Depends(get_current_user),
) -> DownloadUrlResponse:
    """
    ファイルのダウンロード用 URL を生成する。
    
    - Azure Storage の場合は SAS URL を生成
    - MinIO の場合は公開 URL をそのまま返す
    """
    storage = get_storage_service()
    try:
        download_url = await storage.generate_download_url(
            blob_name=blob_name,
            expiry_hours=expiry_hours,
        )
    except Exception as e:
        logger.error(f"[Download] URL generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ダウンロード URL の生成に失敗しました: {str(e)}",
        )
    
    logger.info(f"[Download] {current_user.username} generated download URL for '{blob_name}'")
    return DownloadUrlResponse(download_url=download_url, expires_in_hours=expiry_hours)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="ストレージ接続確認",
)
async def storage_health(
    current_user: CurrentUser = Depends(get_current_user),
) -> HealthResponse:
    """ストレージバックエンドへの接続を確認する。"""
    import os
    backend = os.getenv("STORAGE_BACKEND", "minio")
    storage = get_storage_service()
    ok = await storage.health_check()
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ストレージ ({backend}) に接続できません。",
        )
    return HealthResponse(status="ok", backend=backend)
