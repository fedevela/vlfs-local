import os
from fastmcp import FastMCP
from .utils import resolve_viking_uri

def register_resources(mcp: FastMCP):
    
    @mcp.resource("viking://resources/{domain}")
    def get_resource(domain: str) -> str:
        """Serve external, static knowledge."""
        target_path = resolve_viking_uri(f"viking://resources/{domain}")
        if os.path.exists(target_path) and os.path.isfile(target_path):
            with open(target_path, 'r', encoding='utf-8') as f:
                return f.read()
        return f"Resource not found: {domain}"

    @mcp.resource("viking://user/memories/{session_id}")
    def get_user_memory(session_id: str) -> str:
        """Serve the agent's cognition layer for a specific session."""
        target_dir = resolve_viking_uri(f"viking://user/memories/{session_id}")
        if not os.path.exists(target_dir):
            return f"Session memory not found: {session_id}"
            
        output = [f"Session: {session_id}"]
        try:
            for filename in sorted(os.listdir(target_dir)):
                filepath = os.path.join(target_dir, filename)
                if os.path.isfile(filepath) and filename.endswith(".md"):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        output.append(f"\n--- {filename} ---")
                        output.append(f.read())
        except Exception as e:
            return f"Error reading memories: {e}"
        return "\n".join(output)

    @mcp.resource("viking://skills/{tool_name}")
    def get_skill(tool_name: str) -> str:
        """Serve callable capabilities or static instructions."""
        target_path = resolve_viking_uri(f"viking://skills/{tool_name}.md")
        if os.path.exists(target_path) and os.path.isfile(target_path):
            with open(target_path, 'r', encoding='utf-8') as f:
                return f.read()
        return f"Skill not found: {tool_name}"
