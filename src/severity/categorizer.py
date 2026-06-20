import json
from typing import Dict, Any, List

class SeverityCategorizer:
    """
    Evaluates detected behavioral violations and assigns a standardized risk severity tier.
    The logic is grounded in the policy schema parsed from the compliance document.
    """
    
    def __init__(self, schema_path: str):
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)["behavior_pairs"]
            
        self.TIERS = {
            "LOW": "LOW",
            "MED": "MED", 
            "HIGH": "HIGH",
            "CRIT": "CRIT"
        }

    def _get_schema_domain(self, breached_rule: str) -> Dict[str, Any]:
        """Finds the policy rules associated with a specific behavior violation."""
        for pair in self.schema:
            if pair["unsafe_behavior"]["name"] == breached_rule:
                return pair
        return {}

    def categorize(self, detection: Dict[str, Any]) -> str:
        """
        Assigns a severity tier (LOW/MED/HIGH/CRIT) based on the policy signal
        and the context inferred from the behavior class.
        """
        breached_rule = detection.get("breached_rule", "")
        domain = self._get_schema_domain(breached_rule)
        
        signal = domain.get("severity_signal", "UNKNOWN")
        
        if signal == "CRITICAL SAFETY NOTICE":
            if breached_rule == "Unauthorized Intervention":
                return self.TIERS["CRIT"]
            elif breached_rule == "Carrying Overload with Forklift":
                return self.TIERS["HIGH"]
                
        elif signal == "WARNING":
            if breached_rule == "Opened Panel Cover":
                return self.TIERS["LOW"]
            elif breached_rule == "Safe Walkway Violation":
                return self.TIERS["MED"]
                
        return self.TIERS["LOW"]

    def process_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Augments a list of detection records with calculated severity tiers."""
        enriched_records = []
        for record in records:
            tier = self.categorize(record)
            
            enriched = record.copy()
            enriched["severity_tier"] = tier
            enriched_records.append(enriched)
            
        return enriched_records
