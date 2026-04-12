import os

def get_working_root_dir() -> str:
    """
    Returns the configured working directory for VLFS.
    It can be passed via environment variable VLFS_ROOT_DIR.
    If not provided, it defaults to the directory from which the MCP server was launched.
    We use expanduser to ensure paths like ~/Documents/... are resolved correctly.
    """
    return os.path.abspath(os.path.expanduser(os.environ.get("VLFS_ROOT_DIR", os.getcwd())))
