from dataclasses import dataclass
from pathlib import Path

from .base import StorageBackend, _run


@dataclass
class RcloneBackend(StorageBackend):
    remote: str  # e.g. "storagebox:Backup"

    def name(self) -> str:
        return f"rclone → {self.remote}"

    def _upload(self, archive_path: Path, checksum_path: Path) -> None:
        for f in (archive_path, checksum_path):
            _run(["rclone", "copyto", str(f), f"{self.remote}/{f.name}"])
