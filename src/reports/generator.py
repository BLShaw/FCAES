import json
from collections import Counter
from datetime import datetime
from pathlib import Path

class ShiftReportGenerator:
    """Reads the persistent database and outputs a human-readable Markdown summary."""
    def __init__(self, db_path: str = "outputs/database.jsonl"):
        self.db_path = Path(db_path)
        
    def generate_report(self, out_path: str = "outputs/shift_summary.md"):
        if not self.db_path.exists():
            print(f"Error: Database file not found at {self.db_path}")
            return
            
        records = []
        with open(self.db_path, "r", encoding="utf-8") as f:
            for line in f:
                records.append(json.loads(line))
                
        if not records:
            print("Database is empty. No report to generate.")
            return
            
        total_events = len(records)
        
        # Calculate Severity Distribution
        severities = Counter([r.get("severity", "UNKNOWN") for r in records])
        
        # Calculate Rule Breaches
        rules = Counter([r.get("behavior_class", "UNKNOWN") for r in records])
        top_rule = rules.most_common(1)[0]
        
        report_content = f"""# FCAES Shift Safety Report
**Generated On:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📊 High-Level Metrics
- **Total Safety Events Logged:** {total_events}
- **Most Frequently Breached Rule:** {top_rule[0]} ({top_rule[1]} occurrences)

## ⚠️ Severity Breakdown
- **CRIT (Critical Safety Notice):** {severities.get("CRIT", 0)}
- **HIGH:** {severities.get("HIGH", 0)}
- **MED:** {severities.get("MED", 0)}
- **LOW:** {severities.get("LOW", 0)}

## 🚨 Critical Action Items
*The following events require immediate Management review due to CRITICAL severity classification:*

"""
        # Append Critical Events
        crit_events = [r for r in records if r.get("severity_tier") == "CRIT"]
        if not crit_events:
            report_content += "*(No CRITICAL events recorded during this shift)*\n"
        else:
            for e in crit_events:
                report_content += f"- **[{e['timestamp']}]** {e['behavior_class']} at {e['zone']}: *{e['event_description']}*\n"
                
        out_file = Path(out_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        print(f"Shift report successfully generated at {out_path}")

if __name__ == "__main__":
    generator = ShiftReportGenerator()
    generator.generate_report()
