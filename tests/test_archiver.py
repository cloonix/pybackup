import hashlib
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pybackup.archiver import Archiver
from pybackup.exceptions import ArchiveError


def test_create_raises_if_7zip_not_found():
    with patch("pybackup.archiver._find_7zip_binary", return_value=None):
        with pytest.raises(ArchiveError, match="7zip binary not found"):
            Archiver.create()


def test_generate_sha256(tmp_path):
    archive = tmp_path / "test.7z"
    content = b"hello world"
    archive.write_bytes(content)
    archiver = Archiver(binary="7z")
    checksum_path = archiver.generate_sha256(archive)
    expected = hashlib.sha256(content).hexdigest()
    assert checksum_path.exists()
    assert expected in checksum_path.read_text()
    assert archive.name in checksum_path.read_text()


def test_create_archive_cleans_up_temp_on_failure(tmp_path):
    archiver = Archiver(binary="/fake/7z")
    source = tmp_path / "data"
    source.mkdir()
    output = tmp_path / "output.7z"

    mock_result = MagicMock(returncode=2, stderr="fatal error")
    with patch("subprocess.run", return_value=mock_result):
        with pytest.raises(ArchiveError):
            archiver.create_archive(output, source)

    temp_output = Path(tempfile.gettempdir()) / output.name
    assert not temp_output.exists()


def test_create_archive_success(tmp_path):
    archiver = Archiver(binary="/fake/7z")
    source = tmp_path / "data"
    source.mkdir()
    output = tmp_path / "output.7z"
    temp_output = Path(tempfile.gettempdir()) / output.name

    def fake_run(cmd, **kwargs):
        temp_output.write_bytes(b"fake archive")
        return MagicMock(returncode=0, stderr="")

    with patch("subprocess.run", side_effect=fake_run):
        result = archiver.create_archive(output, source)

    assert result == output
    assert output.exists()
    assert not temp_output.exists()
