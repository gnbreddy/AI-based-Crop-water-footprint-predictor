"""
AquaCrop AI - Google Drive to Local Data Sync Utility
================================================================================
Scans your Google Drive folder or local Downloads directory for exported GEE files
(e.g., cwf_epoch_2000.csv, cwf_epoch_2001.csv, ...), validates row counts (>= 10,000),
and moves/copies them into the project data/ directory ready for model training.
================================================================================
"""

import os
import sys
import shutil
import argparse
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

def find_candidate_directories():
    """Identifies common local locations where Google Drive or browser downloads land."""
    candidates = []
    
    # 1. Check for local Google Drive desktop sync paths
    user_home = os.path.expanduser("~")
    common_drive_paths = [
        os.path.join(user_home, "Google Drive", "GEE_CWF_Data"),
        os.path.join(user_home, "Google Drive"),
        os.path.join("G:", "My Drive", "GEE_CWF_Data"),
        os.path.join("G:", "My Drive"),
        os.path.join(user_home, "Downloads"),
        os.path.join(user_home, "Downloads", "GEE_CWF_Data")
    ]
    for p in common_drive_paths:
        if os.path.exists(p):
            candidates.append(p)
            
    return candidates

def sync_files(source_dir):
    """Copies all cwf_epoch_*.csv files from source_dir into data/ with validation."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        return 0

    print(f"\nScanning '{source_dir}' for GEE exported epoch files...")
    matched_files = []
    for f in os.listdir(source_dir):
        if f.startswith("cwf_epoch_") and f.endswith(".csv"):
            matched_files.append(os.path.join(source_dir, f))

    if not matched_files:
        print("No 'cwf_epoch_<year>.csv' files found in this directory.")
        return 0

    print(f"Found {len(matched_files)} epoch files. Validating and syncing into {DATA_DIR}...")
    synced_count = 0
    total_records = 0

    for src_path in sorted(matched_files):
        fname = os.path.basename(src_path)
        dest_path = os.path.join(DATA_DIR, fname)
        
        try:
            df = pd.read_csv(src_path)
            row_count = len(df)
            shutil.copy2(src_path, dest_path)
            synced_count += 1
            total_records += row_count
            valid_flag = "PASS (>= 10,000)" if row_count >= 10000 else f"NOTE ({row_count} rows)"
            print(f" -> Synced: {fname} | {row_count:,} records [{valid_flag}]")
        except Exception as e:
            print(f" -> Error reading {fname}: {e}")

    print(f"\n[Sync Complete] Successfully stored {synced_count} epoch datasets ({total_records:,} total records) in {DATA_DIR}.")
    return synced_count

def main():
    parser = argparse.ArgumentParser(description="Sync GEE Drive exports into data/ folder")
    parser.add_argument('--source', type=str, default=None, help="Path to your Google Drive or Downloads folder containing the GEE CSVs")
    args = parser.parse_args()

    print("=" * 80)
    print(" AQUACROP AI: GOOGLE DRIVE TO DATA/ STORAGE SYNCHRONIZER")
    print("=" * 80)

    if args.source:
        sync_files(args.source)
    else:
        candidates = find_candidate_directories()
        print("Searching common Google Drive and Downloads paths on your system:")
        for c in candidates:
            print(f" - Found directory: {c}")
            
        synced_any = False
        for c in candidates:
            count = sync_files(c)
            if count > 0:
                synced_any = True

        if not synced_any:
            print("\nUsage tips:")
            print("1. If you downloaded the files from Google Drive manually, specify the folder:")
            print("   python sync_drive_data.py --source \"C:\\Users\\gopav\\Downloads\"")
            print("2. If your Google Drive desktop app syncs to a specific folder:")
            print("   python sync_drive_data.py --source \"path/to/Google Drive/GEE_CWF_Data\"")

if __name__ == '__main__':
    main()
