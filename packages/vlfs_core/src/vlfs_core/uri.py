import os
from .config import get_storage_paths

def resolve_viking_uri(uri: str) -> str:
    """
    Resolves a viking:// URI to an absolute filesystem path based on configured storage roots.
    Returns 'VIRTUAL_ROOT' if the exact root URI is requested.
    """
    paths = get_storage_paths()
    
    if uri == "viking://":
        return "VIRTUAL_ROOT"
    elif uri.startswith("viking://resources/"):
        rel_path = uri.replace("viking://resources/", "", 1)
        return os.path.abspath(os.path.join(paths["workspace"], rel_path))
    elif uri.startswith("viking://user/memories/"):
        rel_path = uri.replace("viking://user/memories/", "", 1)
        return os.path.abspath(os.path.join(paths["memories"], rel_path))
    elif uri.startswith("viking://skills/"):
        rel_path = uri.replace("viking://skills/", "", 1)
        return os.path.abspath(os.path.join(paths["skills"], rel_path))
    else:
        # Not a known viking root, treat as relative to resources for backward compatibility
        if uri.startswith("viking://"):
            rel_path = uri.replace("viking://", "", 1)
            return os.path.abspath(os.path.join(paths["workspace"], rel_path))
        return os.path.abspath(os.path.join(paths["workspace"], uri))

def uri_from_path(abs_path: str) -> str:
    """
    Converts an absolute filesystem path back to a viking:// URI.
    """
    paths = get_storage_paths()
    
    # Check memories first, then skills, then workspace (resources)
    if abs_path.startswith(paths["memories"]):
        try:
            rel = os.path.relpath(abs_path, paths["memories"])
            if rel == ".":
                return "viking://user/memories/"
            return "viking://user/memories/" + rel
        except ValueError:
            pass
            
    if abs_path.startswith(paths["skills"]):
        try:
            rel = os.path.relpath(abs_path, paths["skills"])
            if rel == ".":
                return "viking://skills/"
            return "viking://skills/" + rel
        except ValueError:
            pass

    if abs_path.startswith(paths["workspace"]):
        try:
            rel = os.path.relpath(abs_path, paths["workspace"])
            if rel == ".":
                return "viking://resources/"
            return "viking://resources/" + rel
        except ValueError:
            pass
            
    # Fallback if path doesn't match any configured root
    return f"viking://resources/{abs_path}"
