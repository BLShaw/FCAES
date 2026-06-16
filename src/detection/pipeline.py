import cv2
import json
from pathlib import Path
from typing import Dict, Any, List
from ultralytics import YOLO

class VisionPipeline:
    def __init__(self, schema_path: str, classifier_weights: str = "yolov8n-cls.pt"):
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)["behavior_pairs"]
            
        # 1. Base Object Detector (Pre-trained) for Action Tracking
        self.detector = YOLO("yolov8n.pt")
        # 2. Custom Classifier (Fine-tuned on Voxel51) for State Checking
        self.classifier = YOLO(classifier_weights)
        
        # Static OpenCV Zones (Example coordinates for a 1920x1080 fixed camera)
        self.zones = {
            "walkway": [(100, 100), (400, 100), (400, 900), (100, 900)],
            "equipment": [(500, 200), (900, 200), (900, 800), (500, 800)],
            "electrical_panel": [(1500, 300), (1700, 300), (1700, 600), (1500, 600)]
        }

    def _get_schema_domain(self, name: str) -> Dict[str, Any]:
        for pair in self.schema:
            if pair["domain"] == name:
                return pair
        return {}

    def is_inside_polygon(self, center_x: int, center_y: int, zone_points: List) -> bool:
        # Mock point polygon test
        x_min = min(p[0] for p in zone_points)
        x_max = max(p[0] for p in zone_points)
        y_min = min(p[1] for p in zone_points)
        y_max = max(p[1] for p in zone_points)
        return x_min <= center_x <= x_max and y_min <= center_y <= y_max

    def check_state(self, crop, expected_class_idx: int) -> bool:
        # Runs the custom classifier on a cropped ROI to check the state
        results = self.classifier(crop, verbose=False)
        top_class = results[0].probs.top1
        return top_class == expected_class_idx

    def process_video(self, video_path: str) -> List[Dict[str, Any]]:
        cap = cv2.VideoCapture(video_path)
        records = []
        frame_idx = 0
        clip_id = Path(video_path).stem
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            
            # Detect base objects (person=0, forklift/truck=7)
            results = self.detector(frame, classes=[0, 7], verbose=False)
            
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                
                # 1. Pedestrian Movement (Action: Person outside walkway)
                if cls_id == 0:
                    if not self.is_inside_polygon(cx, cy, self.zones["walkway"]):
                        domain = self._get_schema_domain("Pedestrian Movement")
                        records.append({
                            "clip_id": clip_id,
                            "timestamp": round(timestamp, 2),
                            "zone": "Floor",
                            "breached_rule": domain["unsafe_behavior"]["name"],
                            "description": domain["unsafe_behavior"]["observable_indicator"],
                            "severity": domain["severity_signal"]
                        })
                        
                # 2. Equipment Interaction (Action: Person in equipment zone -> check vest state)
                if cls_id == 0:
                    if self.is_inside_polygon(cx, cy, self.zones["equipment"]):
                        crop = frame[y1:y2, x1:x2]
                        # Assume class 1 in custom model is "Unauthorized Intervention" (Red/Black Vest)
                        if crop.size > 0 and self.check_state(crop, 1):
                            domain = self._get_schema_domain("Equipment Interaction")
                            records.append({
                                "clip_id": clip_id,
                                "timestamp": round(timestamp, 2),
                                "zone": "Equipment Zone A",
                                "breached_rule": domain["unsafe_behavior"]["name"],
                                "description": domain["unsafe_behavior"]["observable_indicator"],
                                "severity": domain["severity_signal"]
                            })
                            
                # 3. Forklift Load (Action: Forklift detected -> check load state)
                if cls_id == 7:
                    crop = frame[y1:y2, x1:x2]
                    # Assume class 3 in custom model is "Carrying Overload with Forklift"
                    if crop.size > 0 and self.check_state(crop, 3):
                        domain = self._get_schema_domain("Forklift Load")
                        records.append({
                            "clip_id": clip_id,
                            "timestamp": round(timestamp, 2),
                            "zone": "Transit Route",
                            "breached_rule": domain["unsafe_behavior"]["name"],
                            "description": domain["unsafe_behavior"]["observable_indicator"],
                            "severity": domain["severity_signal"]
                        })
                        
            # 4. Electrical Safety (State-based, fixed panel ROI)
            if frame_idx % 30 == 0: # Check static state once per second
                px1, py1 = self.zones["electrical_panel"][0]
                px2, py2 = self.zones["electrical_panel"][2]
                panel_crop = frame[py1:py2, px1:px2]
                # Assume class 2 in custom model is "Opened Panel Cover"
                if panel_crop.size > 0 and self.check_state(panel_crop, 2):
                    domain = self._get_schema_domain("Electrical Safety")
                    records.append({
                        "clip_id": clip_id,
                        "timestamp": round(timestamp, 2),
                        "zone": "Panel Board C",
                        "breached_rule": domain["unsafe_behavior"]["name"],
                        "description": domain["unsafe_behavior"]["observable_indicator"],
                        "severity": domain["severity_signal"]
                    })
                        
            frame_idx += 1
            
        cap.release()
        return records
