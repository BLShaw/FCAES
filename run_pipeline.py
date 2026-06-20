import subprocess
import sys
import time

def run_command(command, description):
    print(f"\n{'='*60}")
    print(f"[RUNNING] Step: {description}")
    print(f"[COMMAND] {command}")
    print(f"{'='*60}\n")
    
    process = subprocess.Popen(command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    process.communicate()
    
    if process.returncode != 0:
        print(f"\n[ERROR] Pipeline failed during: {description}")
        sys.exit(1)
        
    print(f"\n[SUCCESS] Step Complete: {description}")

def main():
    print("=== FCAES END-TO-END PIPELINE ===")
    
    run_command("python download_videos.py", "Pre-requisite: Download Camera Feeds from HuggingFace")
    
    run_command("python -m src.policy_parser.main --input docs/compliance_policy.pdf", "Module 1: Policy Parser Engine")
    
    run_command("python -m src.detection.main --video data/data --weights outputs/yolo_classifier/weights/best.pt", "Module 1: Computer Vision Detection Pipeline")
    
    run_command("python -m src.severity.main", "Module 2: Severity Categorization Matrix")
    
    run_command("python -m src.escalation.router", "Module 3: Escalation Pipeline & Real-Time Alerting")
    
    run_command("python -m src.reports.generator", "Module 4: Automated Report Generator")
    
    print(f"\n{'='*60}")
    print("[COMPLETED] ALL BACKEND MODULES COMPLETED SUCCESSFULLY!")
    print("Launching Module 5: Operations Dashboard in your browser...")
    print(f"{'='*60}\n")
    
    time.sleep(2)
    subprocess.run("streamlit run src/dashboard/app.py --server.address=0.0.0.0", shell=True)

if __name__ == "__main__":
    main()
