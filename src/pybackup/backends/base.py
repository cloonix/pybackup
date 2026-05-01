import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from ..exceptions import BackendError


def _run(cmd: list[str]) -> None:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        raise BackendError(f"{cmd[0]!r} not found. Install it and ensure it is in PATH.")
    if result.returncode != 0:
        raise BackendError(f"Command failed: {' '.join(cmd)}\n{result.stderr.strip()}")


class StorageBackend(ABC):
    def upload(self, archive_path: Path, checksum_path: Path) -> None:
        """Upload archive and checksum; deletes local files on success.

        Raises BackendError on failure. Local files are NOT deleted if upload fails.
        """
        self._upload(archive_path, checksum_path)
        archive_path.unlink(missing_ok=True)
        checksum_path.unlink(missing_ok=True)

    @abstractmethod
    def _upload(self, archive_path: Path, checksum_path: Path) -> None:
        ...

    @abstractmethod
    def name(self) -> str:
        ...
