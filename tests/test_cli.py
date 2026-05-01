import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pybackup.cli import _parse_args, _resolve_gpg_key, _build_output_path


# --- _parse_args ---

def test_parse_args_input():
    with patch("sys.argv", ["pybackup", "-i", "/foo"]):
        args = _parse_args()
    assert args.input == "/foo"
    assert not args.encrypt
    assert not args.list_destinations
    assert not args.verbose
    assert not args.dry_run


def test_parse_args_list_destinations():
    with patch("sys.argv", ["pybackup", "--list-destinations"]):
        args = _parse_args()
    assert args.list_destinations


def test_parse_args_encrypt_and_verbose():
    with patch("sys.argv", ["pybackup", "-i", "/foo", "-e", "-v"]):
        args = _parse_args()
    assert args.encrypt
    assert args.verbose


def test_parse_args_dry_run():
    with patch("sys.argv", ["pybackup", "-i", "/foo", "--dry-run"]):
        args = _parse_args()
    assert args.dry_run


def test_parse_args_gpg_key():
    with patch("sys.argv", ["pybackup", "-i", "/foo", "--gpg-key", "ABCDEF"]):
        args = _parse_args()
    assert args.gpg_key == "ABCDEF"


# --- _resolve_gpg_key ---

def test_resolve_gpg_key_none_when_no_key():
    with patch("sys.argv", ["pybackup", "-i", "/foo"]):
        args = _parse_args()
    assert _resolve_gpg_key(args, None) is None


def test_resolve_gpg_key_none_when_gpg_missing():
    with patch("sys.argv", ["pybackup", "-i", "/foo", "--gpg-key", "KEY"]):
        args = _parse_args()
    with patch("shutil.which", return_value=None):
        assert _resolve_gpg_key(args, None) is None


def test_resolve_gpg_key_returns_key_when_gpg_found():
    with patch("sys.argv", ["pybackup", "-i", "/foo", "--gpg-key", "KEY"]):
        args = _parse_args()
    with patch("shutil.which", return_value="/usr/bin/gpg"):
        assert _resolve_gpg_key(args, None) == "KEY"


def test_resolve_gpg_key_prefers_cli_over_config():
    with patch("sys.argv", ["pybackup", "-i", "/foo", "--gpg-key", "CLI_KEY"]):
        args = _parse_args()
    with patch("shutil.which", return_value="/usr/bin/gpg"):
        assert _resolve_gpg_key(args, "CONFIG_KEY") == "CLI_KEY"


# --- _build_output_path ---

def test_build_output_path_uses_input_name():
    path = _build_output_path(Path("/data/my folder"), None)
    assert path.name.startswith("my_folder_")
    assert path.suffix == ".7z"


def test_build_output_path_uses_output_name():
    path = _build_output_path(Path("/data/src"), "custom")
    assert path.name.startswith("custom_")


# --- input path validation ---

def test_input_path_not_found_raises(tmp_path):
    config = {"destinations": [{"name": "t", "backend": "local", "path": str(tmp_path)}]}
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))
    with patch("pybackup.cli._default_config_path", return_value=config_file):
        with patch("sys.argv", ["pybackup", "-i", str(tmp_path / "nonexistent"), "-d", "t"]):
            with pytest.raises(SystemExit, match="does not exist"):
                from pybackup.cli import backup_entry_point
                backup_entry_point()


# --- dry-run ---

def test_dry_run_does_not_create_archive(tmp_path):
    source = tmp_path / "data.txt"
    source.write_text("hello")
    config = {"destinations": [{"name": "t", "backend": "local", "path": str(tmp_path / "dest")}]}
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))
    with patch("pybackup.cli._default_config_path", return_value=config_file):
        with patch("sys.argv", ["pybackup", "-i", str(source), "-d", "t", "--dry-run"]):
            from pybackup.cli import backup_entry_point
            backup_entry_point()
    assert not list((tmp_path / "dest").glob("*.7z")) if (tmp_path / "dest").exists() else True


def test_dry_run_does_not_prompt_passphrase(tmp_path):
    source = tmp_path / "data.txt"
    source.write_text("hello")
    config = {"destinations": [{"name": "t", "backend": "local", "path": str(tmp_path / "dest")}]}
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config))
    with patch("pybackup.cli._default_config_path", return_value=config_file):
        with patch("sys.argv", ["pybackup", "-i", str(source), "-d", "t", "--dry-run", "-e"]):
            with patch("getpass.getpass") as mock_getpass:
                from pybackup.cli import backup_entry_point
                backup_entry_point()
    mock_getpass.assert_not_called()
