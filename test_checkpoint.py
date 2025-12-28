#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test resume checkpoint functionality
"""

import json
from pathlib import Path

def main():
    project_root = Path(__file__).parent
    output_dir = project_root / 'reports'
    checkpoint_file = output_dir / '.resume_checkpoint.json'
    progress_file = output_dir / '.progress.json'

    print("=" * 60)
    print("Test Resume Checkpoint Functionality")
    print("=" * 60)

    # 1. Check checkpoint file
    print("\n1. Check checkpoint file...")
    if checkpoint_file.exists():
        print(f"[OK] Checkpoint file exists")
        print(f"  Size: {checkpoint_file.stat().st_size} bytes")

        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)

        print(f"  Content:")
        print(f"    - total: {checkpoint.get('total')}")
        print(f"    - author_data_map entries: {len(checkpoint.get('author_data_map', {}))}")
        print(f"    - timestamp: {checkpoint.get('timestamp')}")
    else:
        print("[ERROR] Checkpoint file does NOT exist")

    # 2. Check progress file
    print("\n2. Check progress file...")
    if progress_file.exists():
        print(f"[OK] Progress file exists")
        print(f"  Size: {progress_file.stat().st_size} bytes")

        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)

        print(f"  Content:")
        print(f"    - status: {progress.get('status')}")
        print(f"    - total: {progress.get('total')}")
        print(f"    - completed: {progress.get('completed')}")
        print(f"    - current: {progress.get('current')}")
        print(f"    - percentage: {progress.get('percentage')}%")
    else:
        print("[ERROR] Progress file does NOT exist")

    # 3. Verify resume logic
    print("\n3. Verify resume logic...")
    if checkpoint_file.exists() and progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)

        if progress.get('status') == 'generating':
            print("[OK] Resume conditions met")
            print(f"  - Progress status: generating")
            print(f"  - Completed: {progress.get('completed')}/{progress.get('total')}")
            print(f"  - Should resume from author #{progress.get('completed') + 1}")

            # Check checkpoint content
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)

            total = checkpoint.get('total', 0)
            completed = progress.get('completed', 0)

            print(f"\n4. Simulated resume behavior:")
            print(f"  - Checkpoint total authors: {total}")
            print(f"  - Progress completed: {completed}")
            print(f"  - Will skip Git collection: YES")
            print(f"  - Will start from author: #{completed + 1}")
            print(f"  - Remaining authors: {total - completed}")
        else:
            print(f"[ERROR] Resume conditions NOT met")
            print(f"  - Progress status: {progress.get('status')}")
    else:
        print("[ERROR] Resume conditions NOT met (missing files)")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == '__main__':
    main()
