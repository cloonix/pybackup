import shutil
from dataclasses import dataclass
from pathlib import Path

from .base import StorageBackend


@dataclass
class LocalBackend(StorageBackend):
    path: Path

    def name(self) -> str:
        return f"local → {self.path}"

    def _upload(self, archive_path: Path, checksum_path: Path) -> None:
        self.path.mkdir(parents=True, exist_ok=True)
        for f in (archive_path, checksum_path):
            shutil.move(str(f), self.path / f.name)
