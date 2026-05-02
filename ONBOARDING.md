# Onboarding Guide: pybackup

## Overview
pybackup is a CLI tool that archives files/folders with 7-Zip and uploads them to remote destinations (rclone, S3/MinIO, SSH, or local filesystem). It supports optional GPG or passphrase encryption, and generates SHA256 checksums for verification.

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Language | Python | >=3.11 |
| Build | hatchling | - |
| Package Manager | uv | - |
| HTTP/Cloud | boto3 | latest |
| Compression | 7-Zip | external |
| Encryption | GPG | external |
| Sync | rclone | external |

## Architecture

**Pattern**: Strategy pattern for storage backends

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI (cli.py)                               │
├─────────────────────────────────────────────────────────────────┤
│  - Parse arguments (-i input, -d destination, -e encrypt, etc.)    │
│  - Load config from ~/.config/pybackup/config.json               │
│  - Resolve destination → Backend instance                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Config (config.py)                            │
├─────────────────────────────────────────────────────────────────┤
│  - load_config(): Read JSON config, normalize destinations         │
│  - resolve_destination(): Match CLI arg to config entry            │
│  - backend_for(): Factory method → StorageBackend subclass        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Archiver (archiver.py)                         │
├─────────────────────────────────────────────────────────────────┤
│  - create_archive(): 7z a <source> <output.7z> [-p<pass>]         │
│  - encrypt_gpg(): gpg --encrypt --recipient <key>                 │
│  - generate_sha256(): Create .sha256 checksum file                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   StorageBackend (backends/*.py)                  │
├─────────────────────────────────────────────────────────────────┤
│  - LocalBackend: shutil.move to local path                        │
│  - RcloneBackend: rclone copyto <file> <remote>/<file>             │
│  - S3Backend: boto3.client("s3").upload_file()                   │
│  - SSHBackend: scp -P <port> [-i <key>] <file> user@host:path      │
└─────────────────────────────────────────────────────────────────┘
```

## Key Entry Points

| Purpose | Location | Description |
|---------|----------|-------------|
| Main CLI entry | `src/pybackup/cli.py:backup_entry_point()` | Argument parsing, orchestrates backup flow |
| Config loading | `src/pybackup/config.py:load_config()` | Reads and validates config.json |
| Backend factory | `src/pybackup/config.py:backend_for()` | Creates backend instance based on config |
| Archive creation | `src/pybackup/archiver.py:Archiver.create_archive()` | 7-Zip wrapper with encryption support |
| Base backend interface | `src/pybackup/backends/base.py:StorageBackend` | Abstract base class for all backends |

## Directory Map

```
.
├── pyproject.toml          # Project metadata, build config, entry points
├── README.md               # User documentation with examples
├── install.sh              # Self-contained installation script
├── LICENSE                 # MIT License
├── .python-version         # Python version constraint (3.13)
├── .gitignore              # Standard Python .gitignore
├── uv.lock                 # uv dependency lockfile
└── src/
    └── pybackup/
        ├── __init__.py     # Empty (namespace package)
        ├── cli.py          # CLI: argument parsing, main workflow
        ├── config.py       # Configuration loading and destination resolution
        ├── archiver.py     # 7-Zip archive creation, GPG/passphrase encryption
        └── backends/
            ├── __init__.py # Empty
            ├── base.py     # StorageBackend abstract base class
            ├── local.py    # Local filesystem storage
            ├── rclone.py   # rclone remote storage
            ├── s3.py       # S3/MinIO storage (requires boto3)
            └── ssh.py      # SSH/SCP storage
```

## Request Lifecycle

1. **CLI Input**: User runs `pybackup -i /path/to/folder -d my-nas`
2. **Config Load**: `config.py:load_config()` reads `~/.config/pybackup/config.json`
3. **Destination Resolution**: `config.py:resolve_destination()` matches `-d my-nas` to config entry
4. **Backend Creation**: `config.py:backend_for()` instantiates `RcloneBackend(remote="storagebox:Backup")`
5. **Archiver Setup**: `archiver.py:Archiver.create()` finds 7z binary
6. **Archive Creation**: `archiver.create_archive()` runs `7z a archive_20240101_120000.7z <folder> -spf`
7. **Encryption (optional)**: `archiver.encrypt_gpg()` or passphrase via 7z `-p` flag
8. **Checksum**: `archiver.generate_sha256()` creates `.sha256` file
9. **Upload**: `backend.upload()` calls `_upload()` for backend-specific transfer
10. **Cleanup**: Local archive and checksum files are deleted on success

## Conventions

### Code Patterns
- Use `@dataclass` for data-heavy classes (backends)
- Use `ABC` + `@abstractmethod` for interfaces (StorageBackend)
- Use `subprocess.run()` with `capture_output=True` for external commands
- Wrap external commands in try/except FileNotFoundError with helpful error messages
- Use `pathlib.Path` for all filesystem operations
- Raise `RuntimeError` with user-friendly messages for recoverable errors
- Use `shutil.which()` to check for external binary availability

### Naming
- Files: snake_case.py
- Classes: PascalCase
- Functions/Methods: snake_case()
- Variables: snake_case
- Constants: UPPER_SNAKE_CASE (rarely used)

### Error Handling
- External command not found → `ArchiveError` or `BackendError` (e.g. `"{binary} not found. Install it..."`)
- Subprocess failure → `ArchiveError` or `BackendError` with stderr detail
- Config errors → `ConfigError` with descriptive message
- Upload failures → `BackendError` raised by backend; local files preserved on failure
- All custom exceptions in `src/pybackup/exceptions.py`, all extend `PybackupError`

### Git Conventions
- Commit messages: Short, imperative (e.g., "add --list-destinations flag")
- No specific branching strategy detected
- Single author project (cloonix)

## Common Tasks

| I want to... | Look at... |
|--------------|-----------|
| Add a new storage backend | Create file in `src/pybackup/backends/` extending `StorageBackend` |
| Add a CLI flag | `src/pybackup/cli.py` `_parse_args()` method |
| Change archive format | `src/pybackup/archiver.py` `create_archive()` method |
| Modify encryption | `src/pybackup/archiver.py` `encrypt_gpg()` method |
| Change config schema | `src/pybackup/config.py` `_normalise()` function |
| Fix a backend bug | Corresponding file in `src/pybackup/backends/` |
| Change default config path | `src/pybackup/cli.py` `_default_config_path()` |
| Update dependencies | `pyproject.toml` |

## Development Commands

```bash
# Install the package locally
uv tool install "git+https://github.com/cloonix/pybackup"

# Or install in development mode
uv pip install -e .

# Run directly
python -m pybackup.cli -i /path/to/test -d /tmp/backup

# Build a wheel
uv build

# List configured destinations
pybackup -l

# Create a backup
pybackup -i /path/to/folder -d my-destination

# Create encrypted backup
pybackup -i /path/to/folder -d my-destination -e

# Force passphrase encryption
pybackup -i /path/to/folder -d my-destination -p mysecret
```

## External Dependencies

The tool relies on external binaries that must be installed and in PATH:

| Binary | Purpose | Install Command |
|--------|---------|-----------------|
| 7z | Archive creation | `apt install p7zip-full` / `brew install 7zip` |
| gpg | GPG encryption | `apt install gnupg` / `brew install gnupg` |
| rclone | rclone backend | See https://rclone.org/install/ |
| scp | SSH backend | Usually pre-installed with SSH |
| ssh | SSH backend | Usually pre-installed |

## Configuration

Config file locations:
- Linux/macOS: `~/.config/pybackup/config.json`
- Windows: `%APPDATA%\pybackup\config.json`

Example config structure:
```json
{
  "default": "my-nas",
  "gpg_key": "ABCD1234",
  "destinations": [
    {
      "name": "local",
      "backend": "local",
      "path": "/path/to/backups"
    }
  ]
}
```
