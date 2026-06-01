from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings


@dataclass
class StorageResult:
    storage_provider: str
    storage_key: str
    file_path: str
    public_url: str
    local_path: str
    file_size: int
    content_type: str


class StorageProvider:
    provider_name = "base"

    def save_upload(
        self,
        file: UploadFile,
        filename: str,
        content_type: str,
    ) -> StorageResult:
        raise NotImplementedError

    def get_public_url(self, storage_key: str) -> str:
        raise NotImplementedError

    def delete_file(self, storage_key: str) -> bool:
        raise NotImplementedError


class LocalStorageProvider(StorageProvider):
    provider_name = "local"

    def save_upload(
        self,
        file: UploadFile,
        filename: str,
        content_type: str,
    ) -> StorageResult:
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        storage_key = Path(filename).name
        destination = settings.upload_dir / storage_key
        size = write_upload_to_local(file.file, destination)
        validate_upload_size(size)
        public_url = self.get_public_url(storage_key)
        return StorageResult(
            storage_provider=self.provider_name,
            storage_key=storage_key,
            file_path=public_url,
            public_url=public_url,
            local_path=str(destination),
            file_size=size,
            content_type=content_type,
        )

    def get_public_url(self, storage_key: str) -> str:
        return f"/uploads/{Path(storage_key).name}"

    def delete_file(self, storage_key: str) -> bool:
        target = settings.upload_dir / Path(storage_key).name
        if target.exists():
            target.unlink()
            return True
        return False


class S3CompatibleStorageProvider(StorageProvider):
    provider_name = "s3_compatible"

    @property
    def is_configured(self) -> bool:
        return bool(
            settings.storage_endpoint_url
            and settings.storage_bucket
            and settings.storage_access_key_id
            and settings.storage_secret_access_key
        )

    def save_upload(
        self,
        file: UploadFile,
        filename: str,
        content_type: str,
    ) -> StorageResult:
        if not self.is_configured or not is_boto3_available():
            return LocalStorageProvider().save_upload(file, filename, content_type)

        # Stage 14 reserves the S3-compatible contract. A real deployment can
        # add the vendor SDK dependency and wire bucket upload here.
        return LocalStorageProvider().save_upload(file, filename, content_type)

    def get_public_url(self, storage_key: str) -> str:
        if settings.storage_public_base_url:
            return f"{settings.storage_public_base_url.rstrip('/')}/{storage_key}"
        return LocalStorageProvider().get_public_url(storage_key)

    def delete_file(self, storage_key: str) -> bool:
        return False


class CustomStorageProvider(StorageProvider):
    provider_name = "custom"

    def save_upload(
        self,
        file: UploadFile,
        filename: str,
        content_type: str,
    ) -> StorageResult:
        return LocalStorageProvider().save_upload(file, filename, content_type)

    def get_public_url(self, storage_key: str) -> str:
        return LocalStorageProvider().get_public_url(storage_key)

    def delete_file(self, storage_key: str) -> bool:
        return False


def write_upload_to_local(source: BinaryIO, destination: Path) -> int:
    source.seek(0)
    total = 0
    with destination.open("wb") as buffer:
        while True:
            chunk = source.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > settings.max_upload_size_bytes:
                buffer.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds {settings.max_upload_size_mb} MB upload limit",
                )
            buffer.write(chunk)
    source.seek(0)
    return total


def validate_upload_size(size: int) -> None:
    if size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_size_mb} MB upload limit",
        )


def is_boto3_available() -> bool:
    try:
        import boto3  # noqa: F401
    except Exception:
        return False
    return True


def get_storage_provider() -> StorageProvider:
    if settings.storage_provider == "s3_compatible":
        provider = S3CompatibleStorageProvider()
        if provider.is_configured and is_boto3_available():
            return provider
        return LocalStorageProvider()
    if settings.storage_provider == "custom":
        return LocalStorageProvider()
    return LocalStorageProvider()


def get_storage_status() -> dict:
    active_provider = "local"
    if settings.storage_provider == "s3_compatible":
        provider = S3CompatibleStorageProvider()
        if provider.is_configured and is_boto3_available():
            active_provider = "s3_compatible"
    elif settings.storage_provider == "custom":
        active_provider = "local"

    return {
        "storage_provider": settings.storage_provider,
        "active_provider": active_provider,
        "bucket_configured": bool(settings.storage_bucket),
        "endpoint_configured": bool(settings.storage_endpoint_url),
        "public_base_url_configured": bool(settings.storage_public_base_url),
        "max_upload_size_mb": settings.max_upload_size_mb,
        "allowed_upload_types": settings.allowed_upload_types,
    }
