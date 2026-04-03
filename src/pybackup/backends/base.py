from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    def upload(self, archive_path: Path, checksum_path: Path) -> None:
        """Upload archive and checksum; deletes local files on success.

        Raises RuntimeError (or subprocess.CalledProcessError) on failure.
        Local files are NOT deleted if the upload fails.
        """
        self._upload(archive_path, checksum_path)
        archive_path.unlink(missing_ok=True)
        checksum_path.unlink(missing_ok=True)

    @abstractmethod
    def _upload(self, archive_path: Path, checksum_path: Path) -> None:
        """Perform the upload. Raise on failure; must not delete local files."""
        ...

    @abstractmethod
    def name(self) -> str:
        """Human-readable label shown in log output."""
        ...
