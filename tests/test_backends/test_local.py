import pytest
from pathlib import Path
from pybackup.backends.local import LocalBackend


def test_name(tmp_path):
    b = LocalBackend(path=tmp_path)
    assert str(tmp_path) in b.name()


def test_upload_creates_dest_dir(tmp_path):
    dest = tmp_path / "backups" / "sub"
    archive = tmp_path / "archive.7z"
    checksum = tmp_path / "archive.7z.sha256"
    archive.write_bytes(b"data")
    checksum.write_text("abc  archive.7z")
    LocalBackend(path=dest).upload(archive, checksum)
    assert (dest / "archive.7z").exists()
    assert (dest / "archive.7z.sha256").exists()


def test_upload_removes_local_files(tmp_path):
    dest = tmp_path / "dest"
    archive = tmp_path / "archive.7z"
    checksum = tmp_path / "archive.7z.sha256"
    archive.write_bytes(b"data")
    checksum.write_text("abc  archive.7z")
    LocalBackend(path=dest).upload(archive, checksum)
    assert not archive.exists()
    assert not checksum.exists()


def test_upload_moves_files(tmp_path):
    dest = tmp_path / "dest"
    archive = tmp_path / "archive.7z"
    checksum = tmp_path / "archive.7z.sha256"
    archive.write_bytes(b"hello")
    checksum.write_text("abc  archive.7z")
    LocalBackend(path=dest).upload(archive, checksum)
    assert (dest / "archive.7z").read_bytes() == b"hello"
