from dataclasses import dataclass
from pathlib import Path

from .base import StorageBackend
from ..exceptions import BackendError


@dataclass
class S3Backend(StorageBackend):
    endpoint_url: str | None  # e.g. "https://minio.example.com"; None = AWS S3
    access_key: str
    secret_key: str
    bucket: str
    prefix: str = ""          # optional key prefix / "folder" inside the bucket
    region: str = "us-east-1"

    def name(self) -> str:
        base = self.endpoint_url or "https://s3.amazonaws.com"
        prefix_part = f"/{self.prefix.strip('/')}" if self.prefix else ""
        return f"s3 → {base}/{self.bucket}{prefix_part}"

    def _key(self, filename: str) -> str:
        if self.prefix:
            return f"{self.prefix.rstrip('/')}/{filename}"
        return filename

    def _upload(self, archive_path: Path, checksum_path: Path) -> None:
        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
        except ImportError:
            raise BackendError(
                "boto3 is required for the S3 backend. "
                "Install it with: uv add boto3"
            )

        kwargs = dict(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
        )
        if self.endpoint_url:
            kwargs["endpoint_url"] = self.endpoint_url
        client = boto3.client("s3", **kwargs)

        try:
            for f in (archive_path, checksum_path):
                client.upload_file(str(f), self.bucket, self._key(f.name))
        except (BotoCoreError, ClientError) as exc:
            raise BackendError(f"S3 upload failed: {exc}") from exc
