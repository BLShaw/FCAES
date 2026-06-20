import argparse
import json
from pathlib import Path
from src.severity.categorizer import SeverityCategorizer

def main():
    parser = argparse.ArgumentParser(description="Assign severity tiers to detection records.")
    parser.add_argument("--detections", type=str, default="outputs/detections.json", help="Path to input detections")
    parser.add_argument("--schema", type=str, default="outputs/policy_schema.json", help="Path to policy schema")
    parser.add_argument("--output", type=str, default="outputs/categorized_detections.json", help="Path to output file")
    args = parser.parse_args()

    print(f"Loading detections from {args.detections}...")
    try:
        with open(args.detections, "r", encoding="utf-8") as f:
            data = json.load(f)
            records = data.get("detections", [])
    except FileNotFoundError:
        print(f"Error: Could not find detections file at {args.detections}")
        return

    if not records:
        print("No detection records found to process.")
        return

    print("Initializing Severity Categorization Matrix...")
    categorizer = SeverityCategorizer(schema_path=args.schema)
    
    print("Assigning risk tiers...")
    enriched_records = categorizer.process_records(records)
    
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"detections": enriched_records}, f, indent=2)
        
    print(f"Successfully processed {len(enriched_records)} records.")
    print(f"Categorized records saved to {out_path}")

if __name__ == "__main__":
    main()
