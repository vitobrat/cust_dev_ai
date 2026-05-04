"""Unit tests for the Minio object storage client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import BinaryIO

from src.infrastructure.object_storage.client import MinioObjectStorageClient


@dataclass(frozen=True)
class PutObjectCall:
    """Recorded Minio put_object call."""

    bucket_name: str
    object_name: str
    payload: bytes
    length: int
    content_type: str


class FakeMinioResponse:
    """Minimal Minio response double used by download tests."""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self.closed = False
        self.released = False

    def read(self) -> bytes:
        """Return response payload."""
        return self._payload

    def close(self) -> None:
        """Record response close."""
        self.closed = True

    def release_conn(self) -> None:
        """Record connection release."""
        self.released = True


class FakeMinioSdk:
    """Small in-memory Minio SDK double."""

    def __init__(self) -> None:
        self.created_buckets: list[str] = []
        self.put_object_calls: list[PutObjectCall] = []
        self.presigned_calls: list[tuple[str, str, timedelta]] = []
        self.response = FakeMinioResponse(b"# Stored report")

    def bucket_exists(self, bucket_name: str) -> bool:
        """Return True only after the bucket was created."""
        return bucket_name in self.created_buckets

    def make_bucket(self, bucket_name: str, location: str | None = None) -> None:
        """Record bucket creation."""
        self.created_buckets.append(bucket_name)

    def put_object(
        self,
        bucket_name: str,
        object_name: str,
        payload_stream: BinaryIO,
        length: int,
        content_type: str,
    ) -> None:
        """Record object upload."""
        self.put_object_calls.append(
            PutObjectCall(
                bucket_name=bucket_name,
                object_name=object_name,
                payload=payload_stream.read(),
                length=length,
                content_type=content_type,
            ),
        )

    def get_object(self, bucket_name: str, object_name: str) -> FakeMinioResponse:
        """Return the configured response."""
        return self.response

    def presigned_get_object(
        self,
        bucket_name: str,
        object_name: str,
        expires: timedelta,
    ) -> str:
        """Record presigned URL generation."""
        self.presigned_calls.append((bucket_name, object_name, expires))
        return "http://storage.local/presigned"


async def test_minio_client_uploads_text_and_returns_stable_object_uri() -> None:
    """Text upload should ensure bucket existence and return a stable object URI."""
    sdk = FakeMinioSdk()
    storage_client = MinioObjectStorageClient(
        endpoint="minio:9000",
        access_key="access",
        secret_key="secret",
        bucket_name="custdev-reports",
        secure=False,
        region="us-east-1",
        presigned_url_expire_seconds=3600,
        offload_sync_calls=False,
        client=sdk,
    )

    stored_object = await storage_client.upload_text(
        object_key="interviews/report.md",
        report_content="# Report",
        content_type="text/markdown; charset=utf-8",
    )

    assert stored_object.object_key == "interviews/report.md"
    assert stored_object.object_uri == "minio://custdev-reports/interviews/report.md"
    assert sdk.created_buckets == ["custdev-reports"]
    assert sdk.put_object_calls == [
        PutObjectCall(
            bucket_name="custdev-reports",
            object_name="interviews/report.md",
            payload=b"# Report",
            length=8,
            content_type="text/markdown; charset=utf-8",
        ),
    ]


async def test_minio_client_downloads_text_and_releases_response() -> None:
    """Text download should accept stored object URI and release the SDK response."""
    sdk = FakeMinioSdk()
    storage_client = MinioObjectStorageClient(
        endpoint="minio:9000",
        access_key="access",
        secret_key="secret",
        bucket_name="custdev-reports",
        secure=False,
        region="us-east-1",
        presigned_url_expire_seconds=3600,
        offload_sync_calls=False,
        client=sdk,
    )

    stored_content = await storage_client.download_text("minio://custdev-reports/interviews/report.md")

    assert stored_content.report_content == "# Stored report"
    assert stored_content.content_type == "text/markdown; charset=utf-8"
    assert sdk.response.closed is True
    assert sdk.response.released is True


async def test_minio_client_builds_presigned_report_url() -> None:
    """Presigned URLs should use the configured expiration and object reference."""
    sdk = FakeMinioSdk()
    storage_client = MinioObjectStorageClient(
        endpoint="minio:9000",
        access_key="access",
        secret_key="secret",
        bucket_name="custdev-reports",
        secure=False,
        region="us-east-1",
        presigned_url_expire_seconds=900,
        offload_sync_calls=False,
        client=sdk,
    )

    presigned_url = await storage_client.get_presigned_get_url("minio://custdev-reports/interviews/report.md")

    assert presigned_url == "http://storage.local/presigned"
    assert sdk.presigned_calls == [("custdev-reports", "interviews/report.md", timedelta(seconds=900))]
