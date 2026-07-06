from pathlib import Path
from uuid import uuid4

from app.core.config import settings


class ObjectStore:
    """Local object store adapter. Replace with S3/MinIO in production."""

    def __init__(self, root: str | None = None):
        self.root = Path(root or settings.object_store_root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, tenant_id: str, data: bytes, suffix: str) -> str:
        key = f"{tenant_id}/{uuid4()}{suffix}"
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"local://{key}"

    def resolve_local_path(self, uri: str) -> Path:
        if not uri.startswith("local://"):
            raise ValueError("only local:// URIs are supported by this adapter")
        return self.root / uri.removeprefix("local://")
