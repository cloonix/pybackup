import pytest
from pybackup.config import load_config, resolve_destination, backend_for, _normalise
from pybackup.exceptions import ConfigError


def test_normalise_rclone_string():
    assert _normalise("remote:Bucket") == {
        "name": "remote:Bucket", "backend": "rclone", "rclone_remote": "remote:Bucket"
    }


def test_normalise_local_string():
    assert _normalise("/backups") == {
        "name": "/backups", "backend": "local", "path": "/backups"
    }


def test_normalise_dict_passthrough():
    d = {"name": "x", "backend": "local", "path": "/tmp"}
    assert _normalise(d) is d


def test_load_config_minimal(tmp_config):
    path = tmp_config({"destinations": [{"name": "x", "backend": "local", "path": "/tmp"}]})
    dests, default, gpg = load_config(path)
    assert len(dests) == 1
    assert dests[0]["name"] == "x"
    assert default is None
    assert gpg is None


def test_load_config_default_and_gpg(tmp_config):
    path = tmp_config({
        "destinations": [{"name": "x", "backend": "local", "path": "/tmp"}],
        "default": "x",
        "gpg_key": "ABCDEF",
    })
    dests, default, gpg = load_config(path)
    assert default == "x"
    assert gpg == "ABCDEF"


def test_load_config_missing_required_field(tmp_config):
    path = tmp_config({"destinations": [{"name": "x", "backend": "local"}]})
    with pytest.raises(ConfigError, match="missing required fields"):
        load_config(path)


def test_load_config_unknown_backend(tmp_config):
    path = tmp_config({"destinations": [{"name": "x", "backend": "ftp", "host": "h"}]})
    with pytest.raises(ConfigError, match="Unknown backend type"):
        load_config(path)


def test_load_config_invalid_json(tmp_path):
    p = tmp_path / "config.json"
    p.write_text("{bad json")
    with pytest.raises(ConfigError, match="Invalid JSON"):
        load_config(p)


def test_load_config_s3_missing_fields(tmp_config):
    path = tmp_config({"destinations": [{"name": "s3", "backend": "s3", "bucket": "b"}]})
    with pytest.raises(ConfigError, match="access_key"):
        load_config(path)


def test_resolve_destination_by_cli_arg(tmp_config):
    path = tmp_config({"destinations": [
        {"name": "a", "backend": "local", "path": "/a"},
        {"name": "b", "backend": "local", "path": "/b"},
    ]})
    dests, _, _ = load_config(path)
    result = resolve_destination(dests, None, "b")
    assert result["path"] == "/b"


def test_resolve_destination_uses_default(tmp_config):
    path = tmp_config({"destinations": [{"name": "main", "backend": "local", "path": "/m"}]})
    dests, _, _ = load_config(path)
    result = resolve_destination(dests, "main", None)
    assert result["name"] == "main"


def test_resolve_destination_adhoc_rclone():
    result = resolve_destination([], None, "myremote:folder")
    assert result["backend"] == "rclone"
    assert result["rclone_remote"] == "myremote:folder"


def test_resolve_destination_adhoc_local():
    result = resolve_destination([], None, "/some/path")
    assert result["backend"] == "local"
    assert result["path"] == "/some/path"


def test_resolve_destination_no_destinations():
    with pytest.raises(ConfigError, match="No destinations"):
        resolve_destination([], None, None)


def test_backend_for_local(tmp_path):
    from pybackup.backends.local import LocalBackend
    b = backend_for({"backend": "local", "path": str(tmp_path)})
    assert isinstance(b, LocalBackend)


def test_backend_for_rclone():
    from pybackup.backends.rclone import RcloneBackend
    b = backend_for({"backend": "rclone", "rclone_remote": "test:Bucket"})
    assert isinstance(b, RcloneBackend)


def test_backend_for_s3():
    from pybackup.backends.s3 import S3Backend
    b = backend_for({"backend": "s3", "access_key": "k", "secret_key": "s", "bucket": "b"})
    assert isinstance(b, S3Backend)


def test_backend_for_ssh():
    from pybackup.backends.ssh import SSHBackend
    b = backend_for({"backend": "ssh", "host": "h", "remote_path": "/r", "user": "u"})
    assert isinstance(b, SSHBackend)


def test_backend_for_unknown():
    with pytest.raises(ConfigError, match="Unknown backend type"):
        backend_for({"backend": "unknown"})
