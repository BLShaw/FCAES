import pytest
from src.policy_parser.parser import PolicyParser
from pathlib import Path

def test_phase1_pdf_ingestion():
    parser = PolicyParser("docs/compliance_policy.pdf")
    text = parser.extract_text()
    assert len(text) > 100, "PDF text extraction failed or returned empty."

def test_phase1_schema_generation():
    parser = PolicyParser("docs/compliance_policy.pdf")
    schema = parser.parse()
    # The output schema accurately defines the compliant/non-compliant behavior pairs
    assert len(schema.behavior_pairs) >= 4, "Schema should define at least 4 behavior pairs."
    
    # Check for specific observable indicators
    unsafe_names = [pair.unsafe_behavior.name for pair in schema.behavior_pairs]
    
    assert "Carrying Overload with Forklift" in unsafe_names
    assert "Safe Walkway Violation" in unsafe_names
    assert "Unauthorized Intervention" in unsafe_names
    assert "Opened Panel Cover" in unsafe_names

def test_phase1_hazard_context():
    parser = PolicyParser("docs/compliance_policy.pdf")
    schema = parser.parse()
    
    # Check severity signals mapped to behavior classes
    signals = [pair.severity_signal for pair in schema.behavior_pairs]
    assert "CRITICAL SAFETY NOTICE" in signals, "Hazard context signal missing."
    assert "WARNING" in signals, "Hazard context signal missing."
