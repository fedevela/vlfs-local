import os
import sys
from dotenv import load_dotenv

# Enforce loading .env exclusively from the project root ./.env
env_path = os.path.join(os.getcwd(), ".env")
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)  # pragma: no cover

from vlfs_mcp import run as run_mcp

def main():
    run_mcp()

if __name__ == "__main__":  # pragma: no cover
    main()
