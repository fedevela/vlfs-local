import os
from fastmcp import FastMCP
from dotenv import load_dotenv
from vlfs_core import sync_memories, process_file

# Configure the working directory. It can be passed via environment variable VLFS_ROOT_DIR.
# If not provided, it defaults to the directory from which the MCP server was launched.
WORKING_ROOT_DIR = os.environ.get("VLFS_ROOT_DIR", os.getcwd())

# Load environment variables (like GEMINI_API_KEY) from a .env file in the working directory
env_path = os.path.join(WORKING_ROOT_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv() # Fallback to standard location

# Initialize FastMCP server
mcp = FastMCP("vlfs-mcp")

@mcp.tool()
def sync_all_memories() -> str:
    """
    Scans the configured working directory for any new or modified Markdown (.md) memory files
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
