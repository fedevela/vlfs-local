import os
import pathspec

def get_ignore_spec(working_root_dir: str):
    gitignore_path = os.path.join(working_root_dir, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, f)
    return None

def is_ignored(filepath: str, working_root_dir: str, spec: pathspec.PathSpec) -> bool:
    if not spec:
        return False
    rel_path = os.path.relpath(filepath, working_root_dir)
    return spec.match_file(rel_path)
