from __future__ import annotations

from pathlib import Path, PurePosixPath


class LocalStagingStorage:
    def __init__(self, root: str) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        posix = PurePosixPath(key)
        if posix.is_absolute() or ".." in posix.parts:
            raise ValueError("invalid_storage_key")
        path = (self.root / Path(*posix.parts)).resolve()
        if self.root != path and self.root not in path.parents:
            raise ValueError("invalid_storage_key")
        return path

    def put(self, key: str, payload: bytes, *, content_type: str) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_bytes(payload)
        tmp.replace(path)

    def read(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def put_text(self, key: str, payload: str, *, content_type: str = "application/json") -> None:
        self.put(key, payload.encode("utf-8"), content_type=content_type)


class S3StagingStorage:
    def __init__(self, *, bucket: str, endpoint_url: str | None = None, region: str | None = None, prefix: str = "ingestion") -> None:
        import boto3
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.client = boto3.client("s3", endpoint_url=endpoint_url, region_name=region)

    def _key(self, key: str) -> str:
        clean = str(PurePosixPath(key))
        if clean.startswith("/") or ".." in PurePosixPath(clean).parts:
            raise ValueError("invalid_storage_key")
        return f"{self.prefix}/{clean}" if self.prefix else clean

    def put(self, key: str, payload: bytes, *, content_type: str) -> None:
        self.client.put_object(Bucket=self.bucket, Key=self._key(key), Body=payload, ContentType=content_type)

    def read(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=self._key(key))
        return response["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=self._key(key))

    def put_text(self, key: str, payload: str, *, content_type: str = "application/json") -> None:
        self.put(key, payload.encode("utf-8"), content_type=content_type)
