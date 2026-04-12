import pytest
import os
import shutil
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

def test_e2e_vlfs_lifecycle():
    print("\n--- Starting E2E VLFS Lifecycle Test ---")
    
    # 1. Ingestion: Trigger L1 and L0 generation
    print("[1/4] Triggering memory synchronization...")
    sync_result = vlfs_mcp.sync_all_memories()
    print(f"      Result: {sync_result}")
    assert "Successfully synchronized" in sync_result
    
    # 2. L1 Abstract Search: Does the LLM follow the "42" instruction?
    print("[2/4] Testing L1 Abstract Search (grep) for '42'...")
    l1_result = vlfs_mcp.search_l1_grep("42")
    print(f"      Result: {l1_result.strip()}")
    assert "Found" in l1_result
    assert "predictable_concept.md" in l1_result
    
    # 3. L0 Raw Search: Posix find/grep for filename
    print("[3/4] Testing L0 Raw Filename Search for 'predictable'...")
    l0_result = vlfs_mcp.search_l0_memory("predictable")
    print(f"      Result: {l0_result.strip()}")
    assert "predictable_concept.md" in l0_result
    
    # 4. L2 Reflection Lifecycle
    print("[4/4] Testing L2 Reflection Lifecycle (save and read)...")
    save_result = vlfs_mcp.save_l2_memory("test_reflection", "This is an e2e test reflection.", workspace_subpath="test_artifacts")
    print(f"      Save Result: {save_result}")
    assert "Successfully saved" in save_result
    
    read_result = vlfs_mcp.read_l2_memory("test_reflection", workspace_subpath="test_artifacts")
    print(f"      Read Result: {read_result}")
    assert read_result == "This is an e2e test reflection."
    
    # 5. Targeted File Ingestion
    print("[5/6] Testing Targeted File Ingestion...")
    new_file_path = os.path.join(WORKSPACE_DIR, "targeted.md")
    with open(new_file_path, "w") as f:
        f.write("A newly created file to test specific ingestion.")
    ingest_result = vlfs_mcp.ingest_memory_file("targeted.md")
    print(f"      Ingest Result: {ingest_result}")
    assert "Successfully ingested" in ingest_result
    
    # 6. L1 Semantic Search
    print("[6/6] Testing L1 Semantic Search...")
    semantic_result = vlfs_mcp.search_l1_semantic("ultimate answer to life", limit=2)
    print(f"      Semantic Result:\n{semantic_result}")
    assert "Top" in semantic_result
    assert "predictable_concept.md" in semantic_result
    
    print("--- E2E VLFS Lifecycle Test Completed Successfully ---\n")