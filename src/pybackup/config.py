import json
import os
from pathlib import Path

from .backends.base import StorageBackend


def _normalise(dest: str | dict) -> dict:
    if isinstance(dest, str):
        if ":" in dest:
            return {"name": dest, "backend": "rclone", "rclone_remote": dest}
        return {"name": dest, "backend": "local", "path": dest}
    return dest


def _find_destination(destinations: list[dict], name: str) -> dict | None:
    return next((d for d in destinations if d["name"] == name), None)


def load_config(config_path: Path) -> tuple[list[dict], str | None, str | None]:
    data = json.loads(config_path.read_text())
    destinations = [_normalise(d) for d in data.get("destinations", [])]
    default = data.get("default")
    gpg_key = data.get("gpg_key")
    return destinations, default, gpg_key


def resolve_destination(
    destinations: list[dict], default: str | None, cli_arg: str | None
) -> dict:
    if cli_arg:
        return _find_destination(destinations, cli_arg) or _normalise(cli_arg)

    if default:
        match = _find_destination(destinations, default)
        if match:
            print(f"Using default destination: {default}")
            return match
        return _normalise(default)

    if not destinations:
        raise ValueError("No destinations found in config.json")

    print("Available destinations:")
    for i, d in enumerate(destinations, 1):
        print(f"  {i}: {d['name']}")
    choice = int(input("Select a destination by number: "))
    if choice < 1 or choice > len(destinations):
        raise ValueError("Invalid choice")
    return destinations[choice - 1]


def backend_for(dest: dict) -> StorageBackend:
    backend_type = dest.get("backend", "rclone")
    if backend_type == "rclone":
        from .backends.rclone import RcloneBackend
        return RcloneBackend(remote=dest["rclone_remote"])
    elif backend_type == "s3":
        from .backends.s3 import S3Backend
        return S3Backend(
            endpoint_url=dest.get("endpoint_url"),
            access_key=dest["access_key"],
            secret_key=dest["secret_key"],
            bucket=dest["bucket"],
            prefix=dest.get("prefix", ""),
            region=dest.get("region", "us-east-1"),
        )
    elif backend_type == "ssh":
        from .backends.ssh import SSHBackend
        return SSHBackend(
            host=dest["host"],
            remote_path=dest["remote_path"],
            user=dest["user"],
            port=dest.get("port", 22),
            key_path=dest.get("key_path"),
        )
    elif backend_type == "local":
        from .backends.local import LocalBackend
        return LocalBackend(path=Path(os.path.expandvars(dest["path"])).expanduser())
    raise ValueError(f"Unknown backend type: {backend_type!r}")
