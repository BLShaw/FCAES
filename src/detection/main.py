import argparse
import json
from pathlib import Path
from src.detection.pipeline import VisionPipeline

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=str, required=True, help="Path to input video")
    parser.add_argument("--schema", type=str, default="outputs/policy_schema.json")
    parser.add_argument("--weights", type=str, default="yolov8n-cls.pt")
    parser.add_argument("--output", type=str, default="outputs/detections.json")
    args = parser.parse_args()

    print(f"Initializing Vision Pipeline for {args.video}...")
    pipeline = VisionPipeline(schema_path=args.schema, classifier_weights=args.weights)
    
    input_path = Path(args.video)
    if input_path.is_dir():
        videos = list(input_path.glob("*.mp4"))
    else:
        videos = [input_path]
        
    all_records = []
    
    for vid in videos:
        print(f"Processing frames for {vid} (this may take a moment)...")
        records = pipeline.process_video(str(vid))
        
        # Deduplicate records that occur on the same timestamp/rule to avoid spamming
        unique_records = []
        seen = set()
        for r in records:
            key = (int(r["timestamp"]), r["breached_rule"])
            if key not in seen:
                seen.add(key)
                unique_records.append(r)
                
        all_records.extend(unique_records)
            
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"detections": all_records}, f, indent=2)
        
    print(f"Found {len(all_records)} distinct violations across {len(videos)} videos.")
    print(f"Detection records saved to {out_path}")

if __name__ == "__main__":
    main()
