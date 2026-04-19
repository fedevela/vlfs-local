import pytest
import os
import shutil
from vlfs_core import sync_memories
import vlfs_mcp

E2E_DIR = os.path.abspath(os.path.dirname(__file__))
FIXTURE_DIR = os.path.join(E2E_DIR, "workspace-fixture")
WORKSPACE_DIR = os.path.abspath(os.path.join(E2E_DIR, "..", "..", ".workspace"))

@pytest.fixture(autouse=True)
def setup_teardown_workspace(monkeypatch):
    # SETUP: Wipe .workspace before the test starts and copy fixture
    if os.path.exists(WORKSPACE_DIR):
        shutil.rmtree(WORKSPACE_DIR)
    shutil.copytree(FIXTURE_DIR, WORKSPACE_DIR)
    
    # Set VLFS_ROOT_DIR so the config module uses the test workspace
    monkeypatch.setenv("VLFS_ROOT_DIR", WORKSPACE_DIR)
    
    # Disable async ingestion thread for deterministic testing
    monkeypatch.setenv("VLFS_SYNC_ASYNC", "false")
    
    yield # Let the test run

def test_e2e_openviking_lifecycle():
    print("\n--- Starting E2E OpenViking Lifecycle Test ---")
    
    # 0. Pre-sync the fixture to ensure DB is initialized for recall across all 3 partitions
    print("[0/6] Pre-syncing fixture partitions...")
    sync_res = vlfs_mcp.memory_sync("viking://resources/")
    assert "Successfully synchronized" in sync_res
    
    sync_skills = vlfs_mcp.memory_sync("viking://skills/")
    assert "Successfully synchronized" in sync_skills
    
    sync_mems = vlfs_mcp.memory_sync("viking://user/memories/")
    assert "Successfully synchronized" in sync_mems

    # 1. FS LS Search (Directory Listing / Tree Traversal)
    print("[1/6] Testing fs_ls across partitions...")
    # Resources
    fs_res = vlfs_mcp.fs_ls("viking://resources/", recursive=True)
    assert "predictable_concept.md" in fs_res
    
    # Skills
    fs_skills = vlfs_mcp.fs_ls("viking://skills/", recursive=True)
    assert "test_skill.md" in fs_skills
    
    # Memories
    fs_mems = vlfs_mcp.fs_ls("viking://user/memories/", recursive=True)
    assert "old_memory.md" in fs_mems

    # 2. FS Grep (Exact Text Search)
    print("[2/6] Testing fs_grep across partitions...")
    grep_res = vlfs_mcp.fs_grep("Meaning of Life", path="viking://resources/")
    assert "predictable_concept.md" in grep_res
    
    grep_skills = vlfs_mcp.fs_grep("supercalifragilisticexpialidocious", path="viking://skills/")
    assert "test_skill.md" in grep_skills
    
    grep_mems = vlfs_mcp.fs_grep("sky is blue", path="viking://user/memories/")
    assert "old_memory.md" in grep_mems

    # 3. Memory Store (Save New Context) across partitions
    print("[3/6] Testing memory_store across partitions...")
    store_mem = vlfs_mcp.memory_store("This is an e2e test reflection for OpenViking.", targetUri="viking://user/memories/test_session/mem.md")
    assert "Successfully stored memory" in store_mem
    
    store_skill = vlfs_mcp.memory_store("A new skill procedure.", targetUri="viking://skills/new_skill.md")
    assert "Successfully stored memory" in store_skill
    
    store_res = vlfs_mcp.memory_store("A new document.", targetUri="viking://resources/new_doc.md")
    assert "Successfully stored memory" in store_res
    
    # 4. Memory Recall (Semantic Search) across partitions
    print("[4/6] Testing memory_recall across partitions...")
    recall_mem = vlfs_mcp.memory_recall("test reflection", limit=2, targetUri="viking://user/memories/")
    assert "Recall Results" in recall_mem
    assert "test_session" in recall_mem
    
    recall_skill = vlfs_mcp.memory_recall("skill procedure", targetUri="viking://skills/")
    assert "new_skill.md" in recall_skill
    
    recall_res = vlfs_mcp.memory_recall("new document", targetUri="viking://resources/")
    assert "new_doc.md" in recall_res

    # 5. Memory Forget (Delete Memory) across partitions
    print("[5/6] Testing memory_forget across partitions...")
    forget_mem = vlfs_mcp.memory_forget(query="test reflection", targetUri="viking://user/memories/")
    assert "Successfully forgot" in forget_mem
    
    forget_skill = vlfs_mcp.memory_forget(uri="viking://skills/new_skill.md")
    assert "Successfully forgot" in forget_skill
    
    forget_res = vlfs_mcp.memory_forget(uri="viking://resources/new_doc.md")
    assert "Successfully forgot" in forget_res

    print("--- E2E OpenViking Lifecycle Test Completed Successfully ---\n")
