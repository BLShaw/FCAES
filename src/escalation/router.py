import asyncio
import argparse
import json
from src.escalation.db import DatabaseLogger
from src.escalation.alerts import AlertTrigger
import uuid
from datetime import datetime, timedelta

async def async_main():
    parser = argparse.ArgumentParser(description="Run the Escalation Pipeline.")
    parser.add_argument("--input", type=str, default="outputs/categorized_detections.json", help="Categorized records")
    args = parser.parse_args()
    
    print(f"Loading categorized detections from {args.input}...")
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            records = json.load(f).get("detections", [])
    except FileNotFoundError:
        print(f"Error: Could not find input file at {args.input}")
        return
        
    if not records:
        print("No records found to route.")
        return
        
    db = DatabaseLogger()
    alert_system = AlertTrigger()
    
    consumer_task = asyncio.create_task(alert_system.consume_alerts())
    
    print(f"Routing {len(records)} events through the Escalation Pipeline...\n")
    
    base_time = datetime.now()
    
    for record in records:
        tier = record.get("severity_tier", "LOW")
        breached_rule = record.get("breached_rule", "Unknown")
        
        escalation_action = "Real-time alert triggered + DB log" if tier in ["HIGH", "CRIT"] else "Logged to DB"
        
        policy_rule_ref = "Section 2.2"
        if "Walkway" in breached_rule:
            policy_rule_ref = "Section 3.1"
        elif "Forklift" in breached_rule or "Overload" in breached_rule:
            policy_rule_ref = "Section 4.1"
        elif "Panel" in breached_rule:
            policy_rule_ref = "Section 3.2"
            
        video_time = record.get("timestamp", 0.0)
        event_time = base_time + timedelta(seconds=video_time)
        
        compliant_record = {
            "event_id": str(uuid.uuid4()),
            "timestamp": event_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "clip_id": record.get("clip_id", "Unknown"),
            "zone": record.get("zone", "Unknown"),
            "behavior_class": breached_rule,
            "policy_rule_ref": policy_rule_ref,
            "event_description": record.get("description", ""),
            "severity": tier,
            "escalation_action": escalation_action
        }
        
        db.log_event(compliant_record)
        
        if tier in ["HIGH", "CRIT"]:
            await alert_system.publish(compliant_record)
            
    # Wait for the queue to drain completely before exiting
    await alert_system.queue.join()
    consumer_task.cancel()
    
    print("\nEscalation Pipeline completed successfully.")

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
