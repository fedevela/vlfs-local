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
        return os.path.abspath(os.path.join(paths["resources"], rel_path))
    elif uri.startswith("viking://user/memories/"):
        rel_path = uri.replace("viking://user/memories/", "", 1)
        return os.path.abspath(os.path.join(paths["memories"], rel_path))
    elif uri.startswith("viking://skills/"):
        rel_path = uri.replace("viking://skills/", "", 1)
        return os.path.abspath(os.path.join(paths["skills"], rel_path))
    else:
        # Not a known viking root, return error or handle as invalid
        if uri.startswith("viking://"):
            raise ValueError(f"Invalid or unknown viking URI partition: {uri}")
        # If it doesn't start with viking://, assume it's a relative path to resources
        return os.path.abspath(os.path.join(paths["resources"], uri))

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

    if abs_path.startswith(paths["resources"]):
        try:
            rel = os.path.relpath(abs_path, paths["resources"])
            if rel == ".":
                return "viking://resources/"
            return "viking://resources/" + rel
        except ValueError:
            pass
            
    # If the path doesn't match any configured root, it is outside the virtual filesystem
    raise ValueError(f"Path is outside of OpenViking partitions: {abs_path}")
