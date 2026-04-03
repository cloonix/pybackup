import subprocess
from dataclasses import dataclass
from pathlib import Path

from .base import StorageBackend


def _run(cmd: list[str]) -> None:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        raise RuntimeError(
            f"{cmd[0]!r} not found. Install it and ensure it is in PATH."
        )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\n{result.stderr.strip()}"
        )


@dataclass
class RcloneBackend(StorageBackend):
    remote: str  # e.g. "storagebox:Backup"

    def name(self) -> str:
        return f"rclone → {self.remote}"

    def _upload(self, archive_path: Path, checksum_path: Path) -> None:
        for f in (archive_path, checksum_path):
            _run(["rclone", "copyto", str(f), f"{self.remote}/{f.name}"])
