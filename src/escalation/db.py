import json
import logging
from pathlib import Path
from typing import Dict, Any

class DatabaseLogger:
    def __init__(self, db_path: str = "outputs/database.jsonl"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        self.logger = logging.getLogger("DatabaseLogger")
        
    def log_event(self, event: Dict[str, Any]):
        with open(self.db_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
            
        self.logger.info(f"DB PERSIST: Logged {event.get('severity')} event '{event.get('behavior_class')}' at {event.get('timestamp')}")
