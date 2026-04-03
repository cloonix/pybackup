from dataclasses import dataclass
from pathlib import Path

from .base import StorageBackend
from .rclone import _run


@dataclass
class SSHBackend(StorageBackend):
    host: str
    remote_path: str        # absolute path on the remote, e.g. "/backup/dumps"
    user: str
    port: int = 22
    key_path: str | None = None  # path to private key; None = use SSH agent / default keys

    def name(self) -> str:
        return f"ssh → {self.user}@{self.host}:{self.remote_path}"

    def _upload(self, archive_path: Path, checksum_path: Path) -> None:
        remote_dir = self.remote_path.rstrip("/")
        for f in (archive_path, checksum_path):
            cmd = ["scp", "-P", str(self.port)]
            if self.key_path:
                cmd += ["-i", self.key_path]
            cmd += [str(f), f"{self.user}@{self.host}:{remote_dir}/{f.name}"]
            _run(cmd)
