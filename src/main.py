import os
import sys
from dotenv import load_dotenv

# Enforce loading .env exclusively from the project root ./.env
env_path = os.path.join(os.getcwd(), ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)  # pragma: no cover

from vlfs_mcp import run as run_mcp, mcp

def main():
    # Validate required environment variables
    missing_vars = []
    if not os.environ.get("GEMINI_API_KEY"):
        missing_vars.append("GEMINI_API_KEY")
    if not os.environ.get("VLFS_ROOT_DIR"):
        missing_vars.append("VLFS_ROOT_DIR")
        
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please configure them in your .env file at the project root.")
        sys.exit(1)

    run_mcp()

if __name__ == "__main__":  # pragma: no cover
    main()
