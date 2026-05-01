class PybackupError(Exception):
    pass

class ConfigError(PybackupError):
    pass

class BackendError(PybackupError):
    pass

class ArchiveError(PybackupError):
    pass
