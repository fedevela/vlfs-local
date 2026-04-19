import os
import subprocess
import shlex
from .config import get_working_root_dir
from .utils import resolve_viking_uri, uri_from_path

def fs_ls(path: str, recursive: bool = False) -> str:
    """
    Navigates the OpenViking virtual filesystem directory tree to discover available context.
    Uses standard POSIX CLI tools (e.g. find, ls) to traverse and query the directory structure.
    """
    working_root_dir = get_working_root_dir()
    
    # Resolve the viking:// URI to an absolute local path
    target_path = resolve_viking_uri(path)
    
    if not target_path.startswith(working_root_dir):
        return f"Error: Path {path} is outside of the configured workspace."
        
    if not os.path.exists(target_path):
        return f"Path not found: {path}"
        
    try:
        if recursive:
            cmd = f"find {shlex.quote(target_path)} -type f"
        else:
            cmd = f"ls -la {shlex.quote(target_path)}"
            
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            out = result.stdout
            
            # Map absolute paths back to viking URIs
            processed_lines = []
            for line in out.split('\n'):
                if target_path in line:
                    line = line.replace(target_path, uri_from_path(target_path))
                processed_lines.append(line)
                
            out = '\n'.join(processed_lines)
            
            return out[:4000] + ("\n...[truncated]" if len(out) > 4000 else "")
        else:
            return f"Error running {'find' if recursive else 'ls'}: {result.stderr}"
    except Exception as e:
        return f"Error: {e}"

def fs_grep(query: str, path: str = "viking://resources/") -> str:
    """
    Exact Text Search (Keyword matching) across the virtual filesystem.
    Utilizes grep to find specific string matches inside files.
    """
    working_root_dir = get_working_root_dir()
    target_path = resolve_viking_uri(path)
    
    if not os.path.exists(target_path):
        return f"Path not found: {path}"
        
    try:
        # grep -rn "query" path
        cmd = f"grep -rn {shlex.quote(query)} {shlex.quote(target_path)} | head -n 100"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            out = result.stdout
            
            # Map absolute paths back to viking URIs
            processed_lines = []
            for line in out.split('\n'):
                if line:
                    parts = line.split(':', 2)
                    if len(parts) >= 3 and target_path in parts[0]:
                        parts[0] = uri_from_path(parts[0])
                        line = ':'.join(parts)
                    processed_lines.append(line)
                    
            return '\n'.join(processed_lines)
        elif result.returncode == 1:
            return "No matches found."
        else:
            return f"Error running grep: {result.stderr}"
    except Exception as e:
        return f"Error: {e}"
