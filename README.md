# pybackup

Archive a file or folder with 7-Zip and upload it to a remote destination.

## Install

Requires [uv](https://docs.astral.sh/uv/) and [7-Zip](https://www.7-zip.org/).

| OS | 7-Zip install |
|----|---------------|
| macOS | `brew install 7zip` |
| Linux | `apt install p7zip-full` |
| Windows | `choco install 7zip` or `scoop install 7zip` or [installer](https://www.7-zip.org/) |

**From git:**
```sh
uv tool install "git+https://github.com/cloonix/pybackup"
```

**From a local checkout:**
```sh
uv tool install .
```

**Upgrade:**
```sh
uv tool upgrade pybackup          # from git
uv tool install --reinstall .     # from local checkout
```

## Configure endpoints

Create the config file for your platform:

| OS | Config path |
|----|-------------|
| Linux / macOS | `~/.config/pybackup/config.json` |
| Windows | `%APPDATA%\pybackup\config.json` |

```sh
# Linux / macOS
mkdir -p ~/.config/pybackup && $EDITOR ~/.config/pybackup/config.json

# Windows (PowerShell)
New-Item -ItemType Directory -Force "$env:APPDATA\pybackup"
notepad "$env:APPDATA\pybackup\config.json"
```

This file is **never part of the repository** — credentials are safe here.

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
      "name": "local-win",
      "backend": "local",
      "path": "D:\\Backup\\pybackup"
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

| Field | Required | Notes |
|-------|----------|-------|
| `default` | — | destination used when `-d` is not passed; prompts if unset |
| `gpg_key` | — | GPG key ID/fingerprint; enables automatic GPG encryption |
| `path` | local | absolute path; supports `~` and env vars like `$HOME` / `%USERPROFILE%` |
| `rclone_remote` | rclone | any configured rclone remote, e.g. `storagebox:Backup` |
| `endpoint_url` | s3 | omit for AWS S3; set to your MinIO URL otherwise |
| `access_key` / `secret_key` | s3 | MinIO/S3 credentials |
| `bucket` | s3 | target bucket |
| `prefix` | s3 | optional key prefix / subfolder |
| `host`, `user`, `remote_path` | ssh | SFTP target; SSH key auth only |
| `key_path` | ssh | optional; defaults to SSH agent / `~/.ssh` |
| `port` | ssh | optional; defaults to `22` |

## Encryption

If `gpg_key` is set in config (or `--gpg-key` is passed), GPG encryption is used automatically — no passphrase needed at backup time. If `gpg` is not in PATH, it falls back to prompting for a passphrase.

**Windows:** Install [Gpg4win](https://www.gpg4win.org/) to get `gpg` in PATH.

```sh
# GPG used automatically when gpg_key is in config
pybackup -i /path/to/folder

# force passphrase encryption, ignoring GPG config
pybackup -i /path/to/folder -p mysecret
```

## SSH backend

Uses `scp`, which is built into Windows 10 / 11 (OpenSSH client). No extra software needed.

## Decrypt a backup

```sh
# decrypt and extract in one step
gpg --decrypt archive_20260329_120000.7z.gpg | 7z x -si -o/path/to/restore

# or decrypt to a .7z first, then extract
gpg --decrypt archive_20260329_120000.7z.gpg > archive.7z
7z x archive.7z -o/path/to/restore
```

Verify integrity before extracting:
```sh
sha256sum -c archive_20260329_120000.7z.gpg.sha256
```

## Usage

```sh
pybackup -i /path/to/folder                      # upload to default destination
pybackup -i /path/to/folder -d nas               # destination by name (from config)
pybackup -i /path/to/folder -d storagebox:Backup # ad-hoc rclone remote (contains ":")
pybackup -i /path/to/folder -d /tmp/out          # ad-hoc local path (no ":")
pybackup -i /path/to/folder -o archive_name      # custom archive name
pybackup -i /path/to/folder -e                   # encrypt (GPG if available, else passphrase)
pybackup -i /path/to/folder -p mysecret          # force passphrase encryption
pybackup -i /path/to/folder --gpg-key KEYID      # override GPG key
```

`-d` resolves in this order:
1. **Named destination** — looks up the name in `config.json`
2. **Ad-hoc rclone remote** — if the value contains `:` (e.g. `storagebox:Backup`)
3. **Ad-hoc local path** — otherwise treated as a local directory

| Flag | Description |
|------|-------------|
| `-i` / `--input` | File or folder to archive (required) |
| `-o` / `--output` | Output filename without extension (default: input name) |
| `-d` / `--destination` | Named destination from config, ad-hoc rclone remote (`remote:path`), or local path |
| `-e` / `--encrypt` | Encrypt — uses GPG if available/configured, else prompts for passphrase |
| `-p` / `--passphrase` | Force 7-Zip passphrase encryption, skipping GPG |
| `--gpg-key KEY_ID` | Override the GPG key from config |

Each run uploads `<name>_<YYYYMMDD_HHMMSS>.7z` (or `.7z.gpg`) and a `.sha256` checksum, then deletes both local copies on success.
