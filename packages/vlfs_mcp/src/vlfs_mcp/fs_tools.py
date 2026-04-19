import os
import subprocess
import shlex
from vlfs_core import get_storage_paths
from .config import get_resources_root_dir
from .utils import resolve_viking_uri, uri_from_path

def fs_ls(path: str, recursive: bool = False) -> str:
    """
    L0 Layer (Discovery & Metadata): Navigates the OpenViking virtual filesystem directory tree to discover available context.
    Returns structural map without loading context, respecting .gitignore.
    """
    working_root_dir = get_resources_root_dir()
    
    # Resolve the viking:// URI to an absolute local path
    target_path = resolve_viking_uri(path)
    
    if target_path == "VIRTUAL_ROOT":
        from vlfs_core import get_storage_paths
        import datetime
        paths = get_storage_paths()
        
        output = []
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        
        if not recursive:
            output.append(f"d        0 {now} viking://resources/")
            output.append(f"d        0 {now} viking://skills/")
            output.append(f"d        0 {now} viking://user/memories/")
            return '\n'.join(output)
        else:
            # For recursive virtual root, we append results of all three partitions
            full_out = []
            for sub_uri in ["viking://resources/", "viking://skills/", "viking://user/memories/"]:
                sub_target_path = resolve_viking_uri(sub_uri)
                if not os.path.exists(sub_target_path):
                    os.makedirs(sub_target_path, exist_ok=True)
                res = fs_ls(sub_uri, recursive=True)
                if not res.startswith("Error"):
                    full_out.append(res)
            return '\n'.join(full_out)
    
    if not target_path.startswith(working_root_dir) and not any(target_path.startswith(p) for p in get_storage_paths().values()):
        return f"Error: Path {path} is outside of the configured workspace."
        
    if not os.path.exists(target_path):
        return f"Path not found: {path}"
        
    try:
        from vlfs_core import get_ignore_spec, is_ignored
        import datetime
        spec = get_ignore_spec(working_root_dir)
        hard_excludes = {'.git', '.viking', '__pycache__', 'node_modules'}
        
        output = []
        
        if recursive:
            for root, dirs, files in os.walk(target_path):
                dirs[:] = sorted([d for d in dirs if d not in hard_excludes and not is_ignored(os.path.join(root, d), working_root_dir, spec)])
                for f in sorted(files):
                    if f in hard_excludes:
                        continue
                    file_path = os.path.join(root, f)
                    if not is_ignored(file_path, working_root_dir, spec):
                        output.append(uri_from_path(file_path))
        else:
            for item in sorted(os.listdir(target_path)):
                if item in hard_excludes:
                    continue
                file_path = os.path.join(target_path, item)
                if not is_ignored(file_path, working_root_dir, spec):
                    stat = os.stat(file_path)
                    is_dir = os.path.isdir(file_path)
                    type_char = 'd' if is_dir else '-'
                    size = stat.st_size
                    mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                    output.append(f"{type_char} {size:>8} {mtime} {uri_from_path(file_path)}")
                    
        out = '\n'.join(output)
        return out[:4000] + ("\n...[truncated]" if len(out) > 4000 else "")
    except Exception as e:
        return f"Error: {e}"

def fs_grep(query: str, path: str = "viking://resources/") -> str:
    """
    L2 Layer (Exact Matching): Exact Text Search (Keyword matching) across the virtual filesystem.
    Utilizes grep to force a literal string search across raw text rather than relying on the L1 vector index.
    """
    working_root_dir = get_resources_root_dir()
    target_path = resolve_viking_uri(path)
    
    if target_path == "VIRTUAL_ROOT":
        full_out = []
        for sub_uri in ["viking://resources/", "viking://skills/", "viking://user/memories/"]:
            sub_target_path = resolve_viking_uri(sub_uri)
            if not os.path.exists(sub_target_path):
                continue
            res = fs_grep(query, sub_uri)
            if not res.startswith("Error") and res != "No matches found.":
                full_out.append(res)
        if not full_out:
            return "No matches found."
        # Limit overall output and join
        joined_out = '\n'.join(full_out)
        return '\n'.join(joined_out.split('\n')[:100])
        
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
def fs_tree(path: str = "viking://resources/") -> str:
    """
    L0 Layer (Discovery & Metadata): Returns the structural map of the directory tree.
    Uses minimal tokens to see file names and structure without loading content. Start here.
    """
    working_root_dir = get_resources_root_dir()
    target_path = resolve_viking_uri(path)
    
    if target_path == "VIRTUAL_ROOT":
        output = ["viking://"]
        for sub_uri in ["viking://resources/", "viking://skills/", "viking://user/memories/"]:
            sub_target_path = resolve_viking_uri(sub_uri)
            if not os.path.exists(sub_target_path):
                os.makedirs(sub_target_path, exist_ok=True)
            res = fs_tree(sub_uri)
            if not res.startswith("Error") and not res.startswith("Path not found"):
                lines = res.split('\n')
                if lines:
                    output.append(f"    ├── {lines[0].replace('viking://', '')}")
                    for line in lines[1:]:
                        if line:
                            output.append(f"    {line}")
        return '\n'.join(output)
    
    if not target_path.startswith(working_root_dir) and not any(target_path.startswith(p) for p in get_storage_paths().values()):
        return f"Error: Path {path} is outside of the configured workspace."
        
    if not os.path.exists(target_path):
        return f"Path not found: {path}"
        
    try:
        from vlfs_core import get_ignore_spec, is_ignored
        spec = get_ignore_spec(working_root_dir)
        
        output = [f"{path}"]
        
        for root, dirs, files in os.walk(target_path):
            # Always exclude our critical internals regardless of gitignore
            hard_excludes = {'.git', '.viking', '__pycache__', 'node_modules'}
            
            # Filter directories in-place to prevent os.walk from descending into ignored ones
            dirs[:] = sorted([
                d for d in dirs 
                if d not in hard_excludes 
                and not is_ignored(os.path.join(root, d), working_root_dir, spec)
            ])
            
            # Calculate depth relative to the target_path
            rel_path = os.path.relpath(root, target_path)
            if rel_path == '.':
                level = 0
            else:
                level = rel_path.count(os.sep) + 1
                
            indent = ' ' * 4 * level
            if level > 0:
                output.append(f"{indent}├── {os.path.basename(root)}/")
            
            sub_indent = ' ' * 4 * (level + 1 if level > 0 else 1)
            for f in sorted(files):
                if f in hard_excludes:
                    continue
                file_path = os.path.join(root, f)
                if not is_ignored(file_path, working_root_dir, spec):
                    output.append(f"{sub_indent}├── {f}")
                    
        out = '\n'.join(output)
        return out[:4000] + ("\n...[truncated]" if len(out) > 4000 else "")
    except Exception as e:
        return f"Error: {e}"

def fs_cat(path: str) -> str:
    """
    L2 Layer (Deep Reading): Forces the system to access and load the raw, unadulterated file contents into your context window.
    Use only when you have identified a specific file via L0/L1.
    """
    working_root_dir = get_resources_root_dir()
    target_path = resolve_viking_uri(path)
    
    if not target_path.startswith(working_root_dir):
        return f"Error: Path {path} is outside of the configured workspace."
        
    if not os.path.exists(target_path):
        return f"Path not found: {path}"
        
    if not os.path.isfile(target_path):
        return f"Error: Path {path} is a directory, not a file. Use fs_ls or fs_tree."
        
    try:
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return content[:15000] + ("\n...[truncated to 15000 chars]" if len(content) > 15000 else "")
    except UnicodeDecodeError:
        return f"Error: Cannot read {path} as UTF-8 text. It might be a binary file."
    except Exception as e:
        return f"Error reading file: {e}"
