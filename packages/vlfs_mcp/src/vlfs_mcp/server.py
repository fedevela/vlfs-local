from fastmcp import FastMCP
from .config import get_working_root_dir
from .ingestion_tools import sync_all_memories, ingest_memory_file
from .search_tools import search_l0_memory, search_l1_grep, search_l1_semantic
from .l2_tools import save_l2_memory, read_l2_memory

mcp = FastMCP("vlfs-mcp")

mcp.tool()(sync_all_memories)
mcp.tool()(ingest_memory_file)
mcp.tool()(search_l0_memory)
mcp.tool()(search_l1_grep)
mcp.tool()(search_l1_semantic)
mcp.tool()(save_l2_memory)
mcp.tool()(read_l2_memory)

def run():
    print(f"Starting VLFS MCP Server. Working root directory: {get_working_root_dir()}")
    mcp.run()
