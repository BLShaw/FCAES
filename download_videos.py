import os
from huggingface_hub import hf_hub_download, HfApi
import random

def main():
    print("Connecting to Hugging Face Hub...")
    api = HfApi()
    repo_id = "Voxel51/Safe_and_Unsafe_Behaviours"
    
    files = api.list_repo_files(repo_id, repo_type='dataset')
    mp4_files = [f for f in files if f.endswith('.mp4') and f != 'data/3_tr12.mp4']
    
    from collections import defaultdict
    grouped_files = defaultdict(list)
    for f in mp4_files:
        filename = f.split('/')[-1]
        prefix = filename.split('_')[0]
        grouped_files[prefix].append(f)
        
    random.seed(42)
    selected_files = []
    for prefix, files_list in grouped_files.items():
        num_to_grab = min(2, len(files_list))
        selected_files.extend(random.sample(files_list, num_to_grab))
        
    print(f"Downloading {len(selected_files)} highly diverse videos...")
    out_dir = "data/data"
    os.makedirs(out_dir, exist_ok=True)
    
    for f in selected_files:
        print(f"Downloading {f}...")
        hf_hub_download(repo_id=repo_id, repo_type='dataset', filename=f, local_dir="data")
        
    print("Download complete!")

if __name__ == "__main__":
    main()
