import asyncio
from typing import Dict, Any

class AlertTrigger:
    def __init__(self):
        self.queue = asyncio.Queue()
        
    async def publish(self, event: Dict[str, Any]):
        await self.queue.put(event)
        
    async def consume_alerts(self):
        while True:
            event = await self.queue.get()
            
            await asyncio.sleep(0.1)
            
            tier = event.get("severity")
            rule = event.get("behavior_class")
            zone = event.get("zone")
            
            print("\n" + "="*50)
            print(f"🚨 LIVE ALERT TRIGGERED 🚨")
            print(f"[{tier}] {rule}")
            print(f"Location: {zone}")
            print("="*50 + "\n")
            
            self.queue.task_done()
