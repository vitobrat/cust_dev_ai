"""Minio-backed object storage client."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from io import BytesIO
from typing import BinaryIO, Callable, Protocol, TypeVar, cast

from minio import Minio

from src.configs.log.logger import get_logger

_SyncResult = TypeVar("_SyncResult")


@dataclass(frozen=True)
class StoredObject:
    """Metadata for an uploaded object."""

    bucket_name: str
    object_key: str
    object_uri: str
    content_type: str


@dataclass(frozen=True)
class StoredObjectContent:
    """Downloaded text object content."""

    object_key: str
    report_content: str
    content_type: str


class ObjectStorageClientProtocol(Protocol):
    """Protocol used by domain services that need object storage."""

    async def upload_text(self, object_key: str, report_content: str, content_type: str) -> StoredObject:
        """Upload a UTF-8 text object and return storage metadata."""
        ...

    async def download_text(self, object_reference: str) -> StoredObjectContent:
        """Download a UTF-8 text object by key or object URI."""
        ...

    async def get_presigned_get_url(self, object_reference: str) -> str:
        """Return a temporary GET URL for a stored object."""
        ...


class MinioObjectStorageError(RuntimeError):
    """Raised when Minio object storage operation fails."""


class _MinioResponseProtocol(Protocol):
    """Small protocol for Minio get_object responses."""

    def read(self) -> bytes:
        """Read response payload."""
        ...

    def close(self) -> None:
        """Close response body."""
        ...

    def release_conn(self) -> None:
        """Release response connection."""
        ...


class _MinioSdkProtocol(Protocol):
    """Typed subset of the Minio SDK used by the application."""

    def bucket_exists(self, bucket_name: str) -> bool:
        """Return whether a bucket exists."""
        ...

    def make_bucket(self, bucket_name: str, location: str | None = None) -> None:
        """Create a bucket."""
        ...

    def put_object(
        self,
        bucket_name: str,
        object_name: str,
        payload_stream: BinaryIO,
        length: int,
        content_type: str,
    ) -> None:
        """Upload an object."""
        ...

    def get_object(self, bucket_name: str, object_name: str) -> _MinioResponseProtocol:
        """Download an object."""
        ...

    def presigned_get_object(
        self,
        bucket_name: str,
        object_name: str,
        expires: timedelta,
    ) -> str:
        """Build a presigned GET URL."""
        ...


class MinioObjectStorageClient:
    """Async wrapper around the official synchronous Minio SDK."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool,
        region: str,
        presigned_url_expire_seconds: int,
        offload_sync_calls: bool = True,
        client: _MinioSdkProtocol | None = None,
    ) -> None:
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")

        self._bucket_name = bucket_name
        self._region = region
        self._presigned_url_expires = timedelta(seconds=presigned_url_expire_seconds)
        self._offload_sync_calls = offload_sync_calls
        self._bucket_ready = False
        self._bucket_lock = asyncio.Lock()
        self._client = client or self._build_client(endpoint, access_key, secret_key, secure, region)

    async def upload_text(self, object_key: str, report_content: str, content_type: str) -> StoredObject:
        """Upload text content to Minio."""
        await self._ensure_bucket()
        return await self._run_sync(lambda: self._upload_text_sync(object_key, report_content, content_type))

    async def download_text(self, object_reference: str) -> StoredObjectContent:
        """Download text content from Minio."""
        object_key = self._get_object_key(object_reference)
        report_content = await self._run_sync(lambda: self._download_text_sync(object_key))
        return StoredObjectContent(
            object_key=object_key,
            report_content=report_content,
            content_type="text/markdown; charset=utf-8",
        )

    async def get_presigned_get_url(self, object_reference: str) -> str:
        """Build a temporary presigned GET URL for a stored object."""
        object_key = self._get_object_key(object_reference)
        return await self._run_sync(
            lambda: self._client.presigned_get_object(
                self._bucket_name,
                object_key,
                self._presigned_url_expires,
            ),
        )

    async def _ensure_bucket(self) -> None:
        """Create the configured bucket once per process if it does not exist."""
        async with self._bucket_lock:
            if not self._bucket_ready:
                await self._run_sync(self._ensure_bucket_sync)
                self._bucket_ready = True

    async def _run_sync(self, callback: Callable[[], _SyncResult]) -> _SyncResult:
        """Run blocking SDK calls directly or through a threadpool."""
        if self._offload_sync_calls:
            return await asyncio.to_thread(callback)
        return callback()

    def _ensure_bucket_sync(self) -> None:
        """Synchronous bucket existence check."""
        if not self._client.bucket_exists(self._bucket_name):
            self._client.make_bucket(self._bucket_name, location=self._region)

    def _upload_text_sync(self, object_key: str, report_content: str, content_type: str) -> StoredObject:
        """Synchronous object upload."""
        payload = report_content.encode("utf-8")
        self._client.put_object(
            self._bucket_name,
            object_key,
            BytesIO(payload),
            len(payload),
            content_type,
        )
        return StoredObject(
            bucket_name=self._bucket_name,
            object_key=object_key,
            object_uri=self._build_object_uri(object_key),
            content_type=content_type,
        )

    def _download_text_sync(self, object_key: str) -> str:
        """Synchronous object download."""
        response = self._client.get_object(self._bucket_name, object_key)
        try:
            payload = response.read()
        except Exception as exc:
            self._logger.error("Error occurred while downloading object: %s", exc)
        finally:
            response.close()
            response.release_conn()
        return payload.decode("utf-8")

    def _get_object_key(self, object_reference: str) -> str:
        """Normalize an object key or minio://bucket/key reference to object key."""
        clean_reference = object_reference.strip()
        prefix = f"minio://{self._bucket_name}/"
        if clean_reference.startswith(prefix):
            clean_reference = clean_reference.removeprefix(prefix)
        if clean_reference.startswith("minio://"):
            raise MinioObjectStorageError("Object reference points to a different Minio bucket.")
        if not clean_reference:
            raise MinioObjectStorageError("Object reference is empty.")
        return clean_reference

    def _build_object_uri(self, object_key: str) -> str:
        """Build a stable internal URI for an object."""
        return f"minio://{self._bucket_name}/{object_key}"

    @staticmethod
    def _build_client(
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool,
        region: str,
    ) -> _MinioSdkProtocol:
        """Instantiate the official Minio SDK client."""
        return cast(
            _MinioSdkProtocol,
            Minio(
                endpoint=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
                region=region,
            ),
        )
