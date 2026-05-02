# Project Instructions

## Tech Stack
- **Language**: Python 3.11+
- **Build**: hatchling (pyproject.toml)
- **Dependencies**: boto3 (optional, for S3 backend)
- **External tools**: 7-Zip (7z), GPG, rclone, scp/ssh

## Code Style
- **File naming**: snake_case.py
- **Class naming**: PascalCase
- **Function naming**: snake_case
- **Data classes**: Use `@dataclass` decorator for backend configurations
- **Abstract base**: Use `ABC` with `@abstractmethod` for interfaces (see backends/base.py)
- **Error handling**: Raise typed exceptions from `src/pybackup/exceptions.py` (`ConfigError`, `BackendError`, `ArchiveError`) — all extend `PybackupError`

## Testing
- Framework: pytest (configured in `pyproject.toml`, 41 tests)
- Run: `uv run pytest`

## Build & Run
- **Install**: `uv tool install "git+https://github.com/cloonix/pybackup"`
- **Run dev**: `python -m pybackup.cli` or `pybackup` (after install)
- **Build wheel**: `uv build`

## Project Structure

```
pybackup/
├── pyproject.toml    # Project metadata, dependencies, entry point
├── README.md         # Documentation
├── install.sh        # Installation script
└── src/
    └── pybackup/
        ├── __init__.py
        ├── cli.py          # CLI argument parsing and main entry point
        ├── config.py       # Config loading and destination resolution
        ├── archiver.py     # 7-Zip archive creation and encryption
        └── backends/
            ├── __init__.py
            ├── base.py      # StorageBackend ABC
            ├── local.py     # Local filesystem backend
            ├── rclone.py    # rclone backend
            ├── s3.py        # S3/MinIO backend (requires boto3)
            └── ssh.py       # SSH/SCP backend
```

## Conventions
- **Commit style**: Short, imperative messages (e.g., "add --list-destinations flag")
- **CLI flags**: Use `-` for single letter, `--` for multi-word (e.g., `--list-destinations`)
- **Backend pattern**: Each backend extends StorageBackend with `_upload()` and `name()` methods
- **Subprocess**: Use `_run()` helper pattern for external commands with error handling
- **Path handling**: Use `pathlib.Path` consistently
- **GPG check**: Verify `gpg` is in PATH before attempting GPG operations (fallback to passphrase)

## Common Tasks
| Task | Command/Location |
|------|------------------|
| Add new backend | Create new file in `src/pybackup/backends/` extending `StorageBackend` |
| Add CLI flag | Edit `cli.py` `_parse_args()` method |
| Change archive format | Edit `archiver.py` (currently 7-Zip) |
| Update config schema | Edit `config.py` `_normalise()` function |
