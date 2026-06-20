import pytest
import json
from pathlib import Path

def test_phase2_vision_records():
    detections_path = Path("outputs/detections.json")
    assert detections_path.exists(), "Pipeline should have generated detections.json"
    
    with open(detections_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        records = data.get("detections", [])
        
    assert len(records) > 0, "Vision pipeline should detect at least one violation across the sample videos"
    
    # Check structure of the first record
    record = records[0]
    assert "clip_id" in record
    assert "timestamp" in record
    assert "breached_rule" in record
    assert "description" in record
    assert "zone" in record

    # Check that specific behaviors are detected correctly
    rules_detected = [r["breached_rule"] for r in records]
    
    # The models should detect these behaviors across the 27 videos
    assert "Safe Walkway Violation" in rules_detected
    assert "Carrying Overload with Forklift" in rules_detected
    assert "Unauthorized Intervention" in rules_detected
    assert "Opened Panel Cover" in rules_detected
