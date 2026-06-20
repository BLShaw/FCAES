import pytest
from pathlib import Path

def test_phase5_integration_structure():
    # Verify the repository matches requested structural guidelines
    assert Path("src/detection").exists()
    assert Path("src/severity").exists()
    assert Path("src/escalation").exists()
    assert Path("src/reports").exists()
    assert Path("src/dashboard").exists()
    assert Path("data/").exists()
    assert Path("outputs/").exists()

def test_phase5_manifest():
    # Verify dependency manifest
    assert Path("requirements.txt").exists()

def test_phase5_execution_script():
    # Verify single run command
    assert Path("run_pipeline.py").exists()

def test_phase5_readme():
    assert Path("README.md").exists()
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read().lower()
        # Explicitly addresses policy parsing methodology, model selection, severity logic
        assert "parser" in content
        assert "yolo" in content
        assert "severity" in content
