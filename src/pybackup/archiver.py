import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


def _run(cmd: list[str], label: str, cwd: str | None = None, ok_codes: tuple[int, ...] = (0,)) -> None:
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    except FileNotFoundError:
        raise RuntimeError(
            f"{cmd[0]!r} not found. Install it and ensure it is in PATH."
        )
    if result.returncode not in ok_codes:
        raise RuntimeError(f"{label} failed:\n{result.stderr.strip()}")
    if result.returncode != 0 and result.stderr.strip():
        print(f"Warning: {result.stderr.strip()}")


def _find_7zip_binary() -> str | None:
    for name in ("7z", "7za", "7zr", "7zz"):
        path = shutil.which(name)
        if path:
            return path

    if sys.platform == "win32":
        _userprofile = os.environ.get("USERPROFILE", "")
        candidates = [
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
            r"C:\ProgramData\chocolatey\bin\7z.exe",
            str(Path(_userprofile) / "scoop" / "apps" / "7-zip" / "current" / "7z.exe"),
        ]
    elif sys.platform == "darwin":
        candidates = ["/usr/local/bin/7z", "/usr/bin/7z", "/opt/local/bin/7z"]
    elif sys.platform == "linux":
        candidates = ["/usr/bin/7z", "/usr/local/bin/7z", "/opt/local/bin/7z"]
    else:
        candidates = []

    for path in candidates:
        if Path(path).exists():
            return path

    return None


@dataclass
class Archiver:
    binary: str

    @classmethod
    def create(cls) -> "Archiver":
        path = _find_7zip_binary()
        if not path:
            raise RuntimeError(
                "7zip binary not found. Install 7-Zip and ensure it is in PATH."
            )
        return cls(binary=path)

    def create_archive(
        self,
        output: Path,
        source: Path,
        encryption_key: str | None = None,
    ) -> Path:
        temp_output = Path(tempfile.gettempdir()) / output.name

        cmd = [self.binary, "a", str(temp_output), source.name, "-spf"]
        if encryption_key:
            cmd += [f"-p{encryption_key}", "-mhe=on"]

        _run(cmd, "7zip", cwd=str(source.parent), ok_codes=(0, 1))
        shutil.move(str(temp_output), str(output))
        return output

    def encrypt_gpg(self, archive: Path, key_id: str) -> Path:
        output = archive.parent / (archive.name + ".gpg")
        _run(
            ["gpg", "--encrypt", "--recipient", key_id,
             "--trust-model", "always", "--batch",
             "--output", str(output), str(archive)],
            "GPG encryption",
        )
        archive.unlink()
        return output

    def generate_sha256(self, archive: Path) -> Path:
        sha256 = hashlib.sha256()
        with archive.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                sha256.update(chunk)
        checksum_path = archive.parent / (archive.name + ".sha256")
        checksum_path.write_text(f"{sha256.hexdigest()}  {archive.name}")
        return checksum_path
