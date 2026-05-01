import argparse
import getpass
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from .archiver import Archiver
from .config import backend_for, load_config, resolve_destination

logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backup a file or folder to a destination")
    parser.add_argument("-i", "--input", required=False, help="File or folder to archive")
    parser.add_argument("-o", "--output", required=False, help="Output filename without extension")
    parser.add_argument("-d", "--destination", required=False, help="Destination name from config, or an ad-hoc rclone remote")
    parser.add_argument("-e", "--encrypt", action="store_true", help="Encrypt the archive (GPG if available, else passphrase)")
    parser.add_argument("-p", "--passphrase", required=False, help="Force passphrase encryption, skipping GPG")
    parser.add_argument("--gpg-key", required=False, metavar="KEY_ID", help="Override GPG key ID (falls back to config)")
    parser.add_argument("-l", "--list-destinations", action="store_true", help="List configured destinations and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without creating or uploading anything")
    return parser.parse_args()


def _build_output_path(input_path: Path, output_name: str | None) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = output_name if output_name else input_path.name.lower().replace(" ", "_")
    return Path(f"{stem}_{timestamp}.7z")


def _resolve_gpg_key(args: argparse.Namespace, config_gpg_key: str | None) -> str | None:
    key = args.gpg_key or config_gpg_key
    if not key:
        return None
    if not shutil.which("gpg"):
        logger.warning("gpg not found in PATH, falling back to passphrase encryption.")
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
    logging.basicConfig(
        format="%(message)s",
        level=logging.DEBUG if args.verbose else logging.INFO,
    )

    config_path = _default_config_path()
    if not config_path.exists():
        raise SystemExit(
            f"No config file found at {config_path}\n"
            "Create it with your destinations — see README.md for examples."
        )
    destinations, default, config_gpg_key = load_config(config_path)

    if args.list_destinations:
        for d in destinations:
            marker = " (default)" if d["name"] == default else ""
            print(f"{d['name']}{marker}")
        return

    if not args.input:
        raise SystemExit("error: argument -i/--input is required")

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"error: input path does not exist: {args.input}")

    output_path = _build_output_path(input_path, args.output)
    dest = resolve_destination(destinations, default, args.destination)
    backend = backend_for(dest)

    gpg_key = None
    passphrase = None
    if args.passphrase:
        passphrase = args.passphrase
    elif args.encrypt or args.gpg_key or config_gpg_key:
        gpg_key = _resolve_gpg_key(args, config_gpg_key)

    if args.dry_run:
        enc = ("GPG key " + str(gpg_key)) if gpg_key else (
            "passphrase" if (args.passphrase or (not gpg_key and (args.encrypt or args.gpg_key or config_gpg_key)))
            else "none"
        )
        logger.info("[dry-run] Would archive:   %s", input_path)
        logger.info("[dry-run] Would output:    %s", output_path)
        logger.info("[dry-run] Would upload to: %s", backend.name())
        logger.info("[dry-run] Encryption:      %s", enc)
        return

    if not passphrase and not gpg_key and (args.encrypt or args.gpg_key or config_gpg_key):
        passphrase = getpass.getpass("Enter encryption passphrase: ")

    archiver = Archiver.create()
    archive = archiver.create_archive(output_path, input_path, passphrase)
    if gpg_key:
        archive = archiver.encrypt_gpg(archive, gpg_key)
    checksum = archiver.generate_sha256(archive)
    backend.upload(archive, checksum)
    logger.info("Backup complete → %s", backend.name())


if __name__ == "__main__":
    backup_entry_point()
