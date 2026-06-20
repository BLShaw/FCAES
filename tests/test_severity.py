import pytest
import json
from pathlib import Path

def test_phase3_severity_logic():
    cat_path = Path("outputs/categorized_detections.json")
    assert cat_path.exists(), "Categorized detections should exist"
    
    with open(cat_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        records = data.get("detections", [])
        
    for record in records:
        rule = record["breached_rule"]
        tier = record["severity_tier"]
        
        # Violations with no immediate personnel exposure default to lower tiers
        if rule == "Opened Panel Cover":
            assert tier in ["LOW", "MED"], "Isolated open panels should be tiered LOW/MED"
            
        # High-risk events mapped to HIGH/CRITICAL
        if rule == "Unauthorized Intervention":
            assert tier in ["HIGH", "CRIT"], "Unauthorized intervention must be HIGH/CRIT"
            
        if rule == "Carrying Overload with Forklift":
            assert tier in ["HIGH", "CRIT"], "Forklift overloads must be HIGH/CRIT"
