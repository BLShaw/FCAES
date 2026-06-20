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
        # 2. Custom Classifier for State Checking
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
        # Point polygon test
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
        if not cap.isOpened():
            print(f"Error: Could not open video at path {video_path}")
            return []
            
        clip_id = Path(video_path).stem
        
        # Initialize VideoWriter
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        out_path = f"outputs/annotated_{clip_id}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out_writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
        
        records = []
        frame_idx = 0
        
        # State for smoothing annotations between processed frames
        current_annotations = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            
            if frame_idx % 30 == 0:
                current_annotations = []
                
                # 1. Run the custom classifier on the FULL frame to determine the behavioral state of the room
                cls_results = self.classifier(frame, verbose=False)
                top_class = int(cls_results[0].probs.top1)
                
                # 2. Run the base detector to find objects for localization
                det_results = self.detector(frame, classes=[0, 2, 7], verbose=False) # 0=person, 2=car, 7=truck 
                
                # Helper to find the largest bounding box for a given class list
                def get_largest_box(target_classes):
                    largest_area = 0
                    best_box = None
                    for box in det_results[0].boxes:
                        if int(box.cls[0]) in target_classes:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            area = (x2 - x1) * (y2 - y1)
                            if area > largest_area:
                                largest_area = area
                                best_box = (x1, y1, x2, y2)
                    return best_box
                    
                def get_center(box):
                    if not box: return None
                    return ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2)
                    
                # Class 1: Safe Walkway Violation
                if top_class == 1:
                    domain = self._get_schema_domain("Pedestrian Movement")
                    box = get_largest_box([0])
                    loc = get_center(box)
                    zone = f"Zone-X{loc[0]}-Y{loc[1]}" if loc else "Floor"
                    
                    if box:
                        current_annotations.append({
                            "box": box, "text": f"{domain['severity_signal']}: {domain['unsafe_behavior']['name']}", "color": (0, 0, 255)
                        })
                        
                    records.append({
                        "clip_id": clip_id,
                        "timestamp": round(timestamp, 2),
                        "zone": zone,
                        "breached_rule": domain["unsafe_behavior"]["name"],
                        "description": domain["unsafe_behavior"]["observable_indicator"],
                        "severity": domain["severity_signal"]
                    })
                
                # Class 3: Unauthorized Intervention
                elif top_class == 3:
                    domain = self._get_schema_domain("Equipment Interaction")
                    box = get_largest_box([0])
                    loc = get_center(box)
                    zone = f"Equipment Proximity {loc}" if loc else "Equipment Zone"
                    
                    if box:
                        current_annotations.append({
                            "box": box, "text": f"{domain['severity_signal']}: {domain['unsafe_behavior']['name']}", "color": (0, 0, 255)
                        })
                        
                    records.append({
                        "clip_id": clip_id,
                        "timestamp": round(timestamp, 2),
                        "zone": zone,
                        "breached_rule": domain["unsafe_behavior"]["name"],
                        "description": domain["unsafe_behavior"]["observable_indicator"],
                        "severity": domain["severity_signal"]
                    })
                    
                # Class 5: Opened Panel Cover
                elif top_class == 5:
                    domain = self._get_schema_domain("Electrical Safety")
                    
                    # Assume static panel location for visualization if no explicit box
                    current_annotations.append({
                        "box": (1500, 300, 1700, 600), "text": f"{domain['severity_signal']}: {domain['unsafe_behavior']['name']}", "color": (0, 165, 255)
                    })
                        
                    records.append({
                        "clip_id": clip_id,
                        "timestamp": round(timestamp, 2),
                        "zone": "Electrical Panel Board",
                        "breached_rule": domain["unsafe_behavior"]["name"],
                        "description": domain["unsafe_behavior"]["observable_indicator"],
                        "severity": domain["severity_signal"]
                    })
                    
                # Class 7: Carrying Overload with Forklift
                elif top_class == 7:
                    domain = self._get_schema_domain("Forklift Load")
                    box = get_largest_box([2, 7])
                    loc = get_center(box)
                    zone = f"Transit Route {loc}" if loc else "Transit Route"
                    
                    if box:
                        current_annotations.append({
                            "box": box, "text": f"{domain['severity_signal']}: {domain['unsafe_behavior']['name']}", "color": (0, 0, 255)
                        })
                        
                    records.append({
                        "clip_id": clip_id,
                        "timestamp": round(timestamp, 2),
                        "zone": zone,
                        "breached_rule": domain["unsafe_behavior"]["name"],
                        "description": domain["unsafe_behavior"]["observable_indicator"],
                        "severity": domain["severity_signal"]
                    })
                    
            # Draw annotations on the current frame
            for ann in current_annotations:
                x1, y1, x2, y2 = ann["box"]
                cv2.rectangle(frame, (x1, y1), (x2, y2), ann["color"], 4)
                cv2.putText(frame, ann["text"], (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, ann["color"], 3)
                
            out_writer.write(frame)
            frame_idx += 1
            
        cap.release()
        out_writer.release()
        return records
