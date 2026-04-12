import os
from fastmcp import FastMCP
from vlfs_core import sync_memories, process_file, get_ignore_spec, is_ignored

# Configure the working directory. It can be passed via environment variable VLFS_ROOT_DIR.
# If not provided, it defaults to the directory from which the MCP server was launched.
WORKING_ROOT_DIR = os.environ.get("VLFS_ROOT_DIR", os.getcwd())

# Initialize FastMCP server
mcp = FastMCP("vlfs-mcp")

@mcp.tool()
def sync_all_memories() -> str:
    """
    Scans the configured working directory for any new or modified memory files
    and synchronizes them into the VLFS state, generating abstracts and vector embeddings.
    """
    try:
        count = sync_memories(WORKING_ROOT_DIR)
        return f"Successfully synchronized {count} memories in {WORKING_ROOT_DIR}."
    except Exception as e:
        return f"Error synchronizing memories: {str(e)}"

@mcp.tool()
def ingest_memory_file(relative_filepath: str) -> str:
    """
    Forces the ingestion and synchronization of a specific memory file.
    The filepath should be relative to the configured working root directory.
    """
    absolute_filepath = os.path.join(WORKING_ROOT_DIR, relative_filepath)
    if not os.path.exists(absolute_filepath):
        return f"Error: File not found at {absolute_filepath}"
        
    spec = get_ignore_spec(WORKING_ROOT_DIR)
    if is_ignored(absolute_filepath, WORKING_ROOT_DIR, spec):
        return f"Skipped: {relative_filepath} is ignored by .gitignore."
        
    try:
        process_file(WORKING_ROOT_DIR, absolute_filepath)
        return f"Successfully ingested memory: {relative_filepath}"
    except Exception as e:
        return f"Error ingesting memory: {str(e)}"

def run():
    print(f"Starting VLFS MCP Server. Working root directory: {WORKING_ROOT_DIR}")
    mcp.run()

if __name__ == "__main__":
    run()
