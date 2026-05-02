# pybackup

Archive a file or folder with 7-Zip and upload it to a remote destination.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- [7-Zip](https://www.7-zip.org/) — `apt install p7zip-full` / `brew install 7zip` / `choco install 7zip`
- [boto3](https://pypi.org/project/boto3/) — only for S3/MinIO backend; install via `uv tool install "[s3]"` (see below)

## Install

```sh
# one-liner
curl -fsSL https://raw.githubusercontent.com/cloonix/pybackup/main/install.sh | bash

# or manually
uv tool install "git+https://github.com/cloonix/pybackup"

# with S3/MinIO support
uv tool install "git+https://github.com/cloonix/pybackup[s3]"
```

**Upgrade:**
```sh
uv tool upgrade pybackup
```

The install script creates a starter `config.json` with a local destination at `~/backups/pybackup` (or `%APPDATA%\pybackup\config.json` on Windows).

## Configure

Config file location:

| OS | Path |
|----|------|
| Linux / macOS | `~/.config/pybackup/config.json` |
| Windows | `%APPDATA%\pybackup\config.json` |

```json
{
  "default": "my-nas",
  "gpg_key": "YOUR_GPG_KEY_FINGERPRINT",
  "destinations": [
    {
      "name": "local",
      "backend": "local",
      "path": "/Volumes/Backup/pybackup"
    },
    {
      "name": "my-nas",
      "backend": "rclone",
      "rclone_remote": "storagebox:Backup"
    },
    {
      "name": "minio",
      "backend": "s3",
      "endpoint_url": "https://minio.example.com",
      "access_key": "KEY",
      "secret_key": "SECRET",
      "bucket": "backups",
      "prefix": "pybackup/"
    },
    {
      "name": "aws",
      "backend": "s3",
      "access_key": "KEY",
      "secret_key": "SECRET",
      "bucket": "my-bucket",
      "region": "eu-central-1"
    },
    {
      "name": "homeserver",
      "backend": "ssh",
      "host": "backup.example.com",
      "user": "backupuser",
      "remote_path": "/backup/dumps",
      "key_path": "~/.ssh/id_ed25519"
    }
  ]
}
```

| Field | Backend | Notes |
|-------|---------|-------|
| `default` | all | destination used when `-d` is omitted; prompts if unset |
| `gpg_key` | all | GPG key ID/fingerprint; enables automatic encryption |
| `path` | local | absolute path; supports `~` and env vars |
| `rclone_remote` | rclone | any configured rclone remote, e.g. `storagebox:Backup` |
| `endpoint_url` | s3 | omit for AWS S3; required for MinIO/custom endpoints |
| `access_key` / `secret_key` | s3 | credentials |
| `bucket` | s3 | target bucket |
| `prefix` | s3 | optional key prefix |
| `region` | s3 | defaults to `us-east-1` |
| `host`, `user`, `remote_path` | ssh | SFTP target |
| `key_path` | ssh | optional; defaults to SSH agent / `~/.ssh` |
| `port` | ssh | optional; defaults to `22` |

## Usage

```sh
pybackup -l                                       # list configured destinations
pybackup -i /path/to/folder                      # upload to default destination
pybackup -i /path/to/folder -d nas               # named destination from config
pybackup -i /path/to/folder -d storagebox:Backup # ad-hoc rclone remote
pybackup -i /path/to/folder -d /tmp/out          # ad-hoc local path
pybackup -i /path/to/folder -o archive_name      # custom archive name
pybackup -i /path/to/folder -e                   # encrypt (GPG if configured, else passphrase)
pybackup -i /path/to/folder -p mysecret          # force passphrase encryption
pybackup -i /path/to/folder --gpg-key KEYID      # override GPG key
pybackup -i /path/to/folder --dry-run            # preview without creating or uploading
pybackup -i /path/to/folder -v                   # verbose / debug output
```

If no `-d` flag is provided and no `default` is set in config, pybackup prompts to select from available destinations.

| Flag | Description |
|------|-------------|
| `-l` / `--list-destinations` | Print configured destinations and exit |
| `-i` / `--input` | File or folder to archive (required for backup) |
| `-o` / `--output` | Output filename without extension (default: input name) |
| `-d` / `--destination` | Named destination, ad-hoc rclone remote (`remote:path`), or local path |
| `-e` / `--encrypt` | Encrypt — uses GPG if available/configured, else prompts for passphrase |
| `-p` / `--passphrase` | Force 7-Zip passphrase encryption, skipping GPG |
| `--gpg-key KEY_ID` | Override the GPG key from config |
| `--dry-run` | Show what would be archived and where without writing anything |
| `-v` / `--verbose` | Enable debug-level logging |

Each run uploads `<name>_<YYYYMMDD_HHMMSS>.7z` (or `.7z.gpg`) and a `.sha256` checksum, then deletes both local copies on success.

## Encryption

If `gpg_key` is set in config, GPG encryption runs automatically. Without it, `-e` prompts for a passphrase, or `-p` sets one directly.

**Windows:** Install [Gpg4win](https://www.gpg4win.org/) to get `gpg` in PATH.

For Windows Explorer context menu integration, double-click `windows_context_menu.reg` (included in the repository).

## Decrypt

```sh
# decrypt and extract in one step
gpg --decrypt archive_20260329_120000.7z.gpg | 7z x -si -o/path/to/restore

# verify checksum first
sha256sum -c archive_20260329_120000.7z.gpg.sha256
```
