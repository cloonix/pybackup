import argparse
import getpass
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from .archiver import Archiver
from .config import backend_for, load_config, resolve_destination


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backup a file or folder to a destination")
    parser.add_argument("-i", "--input", required=True, help="File or folder to archive")
    parser.add_argument("-o", "--output", required=False, help="Output filename without extension")
    parser.add_argument("-d", "--destination", required=False, help="Destination name from config, or an ad-hoc rclone remote")
    parser.add_argument("-e", "--encrypt", action="store_true", help="Encrypt the archive (GPG if available, else passphrase)")
    parser.add_argument("-p", "--passphrase", required=False, help="Force passphrase encryption, skipping GPG")
    parser.add_argument("--gpg-key", required=False, metavar="KEY_ID", help="Override GPG key ID (falls back to config)")
    return parser.parse_args()


def _build_output_path(args: argparse.Namespace) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = args.output if args.output else Path(args.input).name.lower().replace(" ", "_")
    return Path(f"{stem}_{timestamp}.7z")


def _resolve_gpg_key(args: argparse.Namespace, config_gpg_key: str | None) -> str | None:
    """Return the GPG key to use, or None if GPG should not be used."""
    key = args.gpg_key or config_gpg_key
    if not key:
        return None
    if not shutil.which("gpg"):
        print("Warning: gpg not found in PATH, falling back to passphrase encryption.")
        return None
    return key


def _default_config_path() -> Path:
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "pybackup" / "config.json"
        return Path.home() / "AppData" / "Roaming" / "pybackup" / "config.json"
    return Path.home() / ".config" / "pybackup" / "config.json"


def backup_entry_point() -> None:
    args = _parse_args()
    output_path = _build_output_path(args)

    config_path = _default_config_path()
    if not config_path.exists():
        raise SystemExit(
            f"No config file found at {config_path}\n"
            "Create it with your destinations — see README.md for examples."
        )
    destinations, default, config_gpg_key = load_config(config_path)
    dest = resolve_destination(destinations, default, args.destination)
    backend = backend_for(dest)

    gpg_key = None
    passphrase = None
    if args.passphrase:
        passphrase = args.passphrase
    elif args.encrypt:
        gpg_key = _resolve_gpg_key(args, config_gpg_key)
        if not gpg_key:
            passphrase = getpass.getpass("Enter encryption passphrase: ")
    elif args.gpg_key or config_gpg_key:
        # GPG key configured — encrypt by default without needing -e
        gpg_key = _resolve_gpg_key(args, config_gpg_key)
        if not gpg_key:
            passphrase = getpass.getpass("Enter encryption passphrase: ")

    archiver = Archiver.create()
    archive = archiver.create_archive(output_path, Path(args.input), passphrase)
    if gpg_key:
        archive = archiver.encrypt_gpg(archive, gpg_key)
    checksum = archiver.generate_sha256(archive)
    backend.upload(archive, checksum)
    print(f"Backup complete → {backend.name()}")


if __name__ == "__main__":
    backup_entry_point()
