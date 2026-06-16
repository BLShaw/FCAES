import json
import argparse
from pathlib import Path
from src.policy_parser.parser import PolicyParser

def main():
    parser = argparse.ArgumentParser(description="Parse FCAES Compliance Policy document into JSON schema.")
    parser.add_argument("--input", type=str, default="docs/compliance_policy.md", help="Path to input document (PDF or Markdown)")
    parser.add_argument("--output", type=str, default="outputs/policy_schema.json", help="Path to output JSON file")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found. Please ensure the document is placed in the correct location.")
        return
        
    print(f"Parsing policy document from {input_path}...")
    policy_parser = PolicyParser(str(input_path))
    schema = policy_parser.parse()
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(schema.model_dump_json(indent=2))
        
    print(f"Successfully extracted {len(schema.behavior_pairs)} behavior domains.")
    print(f"Schema written to {output_path}")

if __name__ == "__main__":
    main()
