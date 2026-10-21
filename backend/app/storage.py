"""Private local media adapter for development and single-host deployments."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4


class PrivateLocalMediaStore:
    """Store normalized images outside the web root using opaque object keys."""

    def __init__(self, root: str | Path):
        self._root = Path(root).expanduser().resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def save_image(self, content: bytes) -> str:
        object_key = f"{uuid4().hex}.jpg"
        destination = self._path_for(object_key)
        try:
            with destination.open("xb") as image_file:
                image_file.write(content)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return object_key

    def read_image(self, object_key: str) -> bytes:
        return self._path_for(object_key).read_bytes()

    def delete(self, object_key: str) -> None:
        try:
            self._path_for(object_key).unlink(missing_ok=True)
        except FileNotFoundError:
            pass

    def _path_for(self, object_key: str) -> Path:
        if len(object_key) != 36 or not object_key.endswith(".jpg"):
            raise ValueError("Invalid private media key")
        stem = object_key[:-4]
        if len(stem) != 32 or any(char not in "0123456789abcdef" for char in stem):
            raise ValueError("Invalid private media key")
        path = (self._root / object_key).resolve()
        if path.parent != self._root:
            raise ValueError("Invalid private media key")
        return path
