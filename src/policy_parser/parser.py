import re
from typing import List
from pypdf import PdfReader
from src.policy_parser.schema import BehaviorClass, BehaviorPair, PolicySchema

class PolicyParser:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def extract_text(self) -> str:
        """Extract text from the document (PDF or Markdown)."""
        try:
            if self.file_path.endswith('.md'):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                reader = PdfReader(self.file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from {self.file_path}: {e}")

    def parse(self) -> PolicySchema:
        """Parse the extracted text and output the dynamic schema."""
        text = self.extract_text()
        
        text = re.sub(r'\s+', ' ', text)
        
        pairs: List[BehaviorPair] = []
        
        domains = [
            ("Pedestrian Movement", r"SECTION 3.*?(?=SECTION 4)"),
            ("Equipment Interaction", r"SECTION 4.*?(?=SECTION 5)"),
            ("Electrical Safety", r"SECTION 5.*?(?=SECTION 6)"),
            ("Forklift Load", r"SECTION 6.*?(?=SECTION 7)"), 
            ("General Pedestrian", r"SECTION 8.*?(?=SECTION 8)"), 
        ]
        
        for domain_name, section_regex in domains:
            section_match = re.search(section_regex, text, flags=re.IGNORECASE | re.DOTALL)
            if not section_match:
                continue
            section_text = section_match.group(0)
            
            clean_text = re.sub(r'[\*#>]', '', section_text)
            
            safe_match = re.search(r"Required Behavior\s*(?:[—\-]\s*)?([A-Za-z\s]+?)\s*\(Compliant\)", clean_text, re.IGNORECASE)
            safe_name = safe_match.group(1).strip() if safe_match else "Unknown Safe"
            
            unsafe_match = re.search(r"Non-Compliant (?:Behavior|Condition)\s*(?:[—\-]\s*)?([A-Za-z\s]+?)(?:\n|\(|is defined|A\s+|An\s+)", clean_text, re.IGNORECASE)
            unsafe_name = unsafe_match.group(1).strip() if unsafe_match else "Unknown Unsafe"
            unsafe_name = unsafe_name.replace("(Unsafe)", "").strip()
            words = unsafe_name.split()
            half = len(words) // 2
            if half > 0 and words[:half] == words[half:]:
                unsafe_name = " ".join(words[:half])
            
            # Extract Severity Signal
            severity_signal = "UNKNOWN"
            if "CRITICAL SAFETY NOTICE" in section_text:
                severity_signal = "CRITICAL SAFETY NOTICE"
            elif "WARNING" in section_text:
                severity_signal = "WARNING"
                
            indicator = f"Performs {unsafe_name}"
            clean_full_text = re.sub(r'[\*#>]', '', text)
            
            row_pattern = rf"{re.escape(domain_name)}\s*\|\s*{re.escape(unsafe_name)}\s*\|\s*{re.escape(safe_name)}\s*\|\s*(.*?)\s*\|"
            row_match = re.search(row_pattern, text, re.IGNORECASE)
            if row_match:
                indicator = row_match.group(1).strip()
            else:
                collapsed_text = re.sub(r'\s+', ' ', clean_full_text)
                fallback_pattern = rf"{re.escape(domain_name)}\s+{re.escape(unsafe_name)}\s+{re.escape(safe_name)}\s+(.*?)(?=\s+\d\s+[A-Z]|\s+IMPORTANT)"
                fb_match = re.search(fallback_pattern, collapsed_text, re.IGNORECASE)
                if fb_match:
                    indicator = fb_match.group(1).strip()
            
            pairs.append(BehaviorPair(
                domain=domain_name,
                safe_behavior=BehaviorClass(name=safe_name, observable_indicator=f"Performs {safe_name}"),
                unsafe_behavior=BehaviorClass(name=unsafe_name, observable_indicator=indicator),
                severity_signal=severity_signal
            ))
            
        return PolicySchema(behavior_pairs=pairs)
