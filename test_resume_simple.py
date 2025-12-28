#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试续跑功能
"""

import json
from pathlib import Path

def main():
    project_root = Path(__file__).parent
    output_dir = project_root / 'reports'
    checkpoint_file = output_dir / '.resume_checkpoint.json'
    progress_file = output_dir / '.progress.json'

    print("=" * 60)
    print("测试续跑检查点功能")
    print("=" * 60)

    # 1. 检查检查点文件
    print("\n1. Check checkpoint file...")
    if checkpoint_file.exists():
        print(f"[OK] Checkpoint file exists")
        print(f"  Size: {checkpoint_file.stat().st_size} bytes")

        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)

        print(f"  内容:")
        print(f"    - total: {checkpoint.get('total')}")
        print(f"    - author_data_map条目数: {len(checkpoint.get('author_data_map', {}))}")
        print(f"    - timestamp: {checkpoint.get('timestamp')}")
    else:
        print("✗ 检查点文件不存在")

    # 2. 检查进度文件
    print("\n2. 检查进度文件...")
    if progress_file.exists():
        print(f"✓ 进度文件存在")
        print(f"  大小: {progress_file.stat().st_size} bytes")

        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)

        print(f"  内容:")
        print(f"    - status: {progress.get('status')}")
        print(f"    - total: {progress.get('total')}")
        print(f"    - completed: {progress.get('completed')}")
        print(f"    - current: {progress.get('current')}")
        print(f"    - percentage: {progress.get('percentage')}%")
    else:
        print("✗ 进度文件不存在")

    # 3. 验证续跑逻辑
    print("\n3. 验证续跑逻辑...")
    if checkpoint_file.exists() and progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)

        if progress.get('status') == 'generating':
            print("✓ 续跑条件满足")
            print(f"  - 进度状态: generating")
            print(f"  - 已完成: {progress.get('completed')}/{progress.get('total')}")
            print(f"  - 应从第 {progress.get('completed') + 1} 个作者继续")
        else:
            print(f"✗ 续跑条件不满足")
            print(f"  - 进度状态: {progress.get('status')}")
    else:
        print("✗ 续跑条件不满足（文件缺失）")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    main()
