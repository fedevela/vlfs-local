from fastmcp import FastMCP
from .config import get_working_root_dir
from .memory_tools import memory_recall, memory_store, memory_forget, memory_sync, memory_find
from .fs_tools import fs_ls, fs_grep, fs_tree, fs_cat
from .resources import register_resources

mcp = FastMCP("vlfs-mcp")

mcp.tool()(memory_recall)
mcp.tool()(memory_find)
mcp.tool()(memory_store)
mcp.tool()(memory_forget)
mcp.tool()(memory_sync)
mcp.tool()(fs_ls)
mcp.tool()(fs_tree)
mcp.tool()(fs_grep)
mcp.tool()(fs_cat)

# Register native MCP resources
register_resources(mcp)

def run():
    print(f"Starting VLFS MCP Server (OpenViking Standard). Working root directory: {get_working_root_dir()}")
    mcp.run()
