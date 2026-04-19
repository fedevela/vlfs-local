import os
import json

DEFAULT_CONFIG_FILENAME = "vlfs_config.json"

def load_config() -> dict:
    """
    Loads configuration from vlfs_config.json in the current working directory,
    falling back to environment variables or defaults if not provided.
    """
    config_path = os.path.abspath(DEFAULT_CONFIG_FILENAME)
    config = {
        "storage": {
            "resources": os.environ.get("VLFS_RESOURCES_DIR", os.getcwd()),
            "skills": os.environ.get("VLFS_SKILLS_DIR"),
            "memories": os.environ.get("VLFS_MEMORIES_DIR")
        },
        "embedding": {
            "provider": os.environ.get("EMBEDDING_PROVIDER", "google"),
            "model": os.environ.get("EMBEDDING_MODEL", "gemini-embedding-001"),
            "api_key": os.environ.get("GEMINI_API_KEY", "")
        },
        "vlm": {
            "provider": os.environ.get("VLM_PROVIDER", "google"),
            "model": os.environ.get("VLM_MODEL", "gemini-2.5-flash"),
            "api_key": os.environ.get("GEMINI_API_KEY", "")
        }
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            # Deep merge file config into default config
            if "storage" in file_config:
                config["storage"].update(file_config["storage"])
            if "embedding" in file_config:
                config["embedding"].update(file_config["embedding"])
            if "vlm" in file_config:
                config["vlm"].update(file_config["vlm"])
        except Exception as e:
            print(f"Warning: Failed to load {DEFAULT_CONFIG_FILENAME}: {e}")
            
    # Resolve storage paths
    resources = config["storage"].get("resources", os.getcwd())
    resources_abs = os.path.abspath(os.path.expanduser(resources))
    config["storage"]["resources"] = resources_abs
    
    # If env var provided None or empty string, fallback to default relative paths
    memories_path = config["storage"].get("memories")
    if not memories_path:
        memories_path = os.path.join(resources_abs, ".viking", "user", "memories")
    config["storage"]["memories"] = os.path.abspath(os.path.expanduser(memories_path))
    
    skills_path = config["storage"].get("skills")
    if not skills_path:
        skills_path = os.path.join(resources_abs, ".viking", "skills")
    config["storage"]["skills"] = os.path.abspath(os.path.expanduser(skills_path))
    
    return config

def get_resources_root_dir() -> str:
    config = load_config()
    return config["storage"]["resources"]

def get_storage_paths() -> dict:
    return load_config()["storage"]
