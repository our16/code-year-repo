#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试续跑功能
"""

import json
from pathlib import Path
from src.report_generator import ReportGenerator

def main():
    project_root = Path(__file__).parent
    generator = ReportGenerator(project_root)

    print("=" * 60)
    print("测试续跑功能")
    print("=" * 60)

    # 1. 检查是否有续跑检查点
    print("\n1. 检查续跑检查点...")
    resume_data = generator._check_resume_progress()

    if resume_data:
        print(f"✓ 发现续跑检查点")
        print(f"  - 总作者数: {resume_data.get('total')}")
        print(f"  - 已完成: {resume_data.get('completed')}")
        print(f"  - author_data_map条目数: {len(resume_data.get('author_data_map', {}))}")
    else:
        print("✗ 未发现续跑检查点")
        # 手动加载检查点文件用于调试
        checkpoint_file = project_root / 'reports' / '.resume_checkpoint.json'
        if checkpoint_file.exists():
            print(f"  但检查点文件存在！大小: {checkpoint_file.stat().st_size} bytes")
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
                print(f"  检查点内容:")
                print(f"    - total: {checkpoint.get('total')}")
                print(f"    - author_data_map keys: {len(checkpoint.get('author_data_map', {}))}")

        progress_file = project_root / 'reports' / '.progress.json'
        if progress_file.exists():
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                print(f"  进度文件状态: {progress.get('status')}")

    # 2. 测试续跑
    print("\n2. 测试续跑逻辑...")
    print(f"   调用 generate_all()...")

    def progress_callback(data):
        print(f"   进度: {data['current']} ({data['completed']}/{data['total']}) - {data['percentage']}%")

    # 不真正执行，只打印日志
    print(f"   (暂停，不真正执行)")

    print("\n3. 检查文件状态...")
    checkpoint_file = project_root / 'reports' / '.resume_checkpoint.json'
    progress_file = project_root / 'reports' / '.progress.json'

    print(f"   检查点文件: {'存在' if checkpoint_file.exists() else '不存在'}")
    if checkpoint_file.exists():
        print(f"   大小: {checkpoint_file.stat().st_size} bytes")

    print(f"   进度文件: {'存在' if progress_file.exists() else '不存在'}")
    if progress_file.exists():
        print(f"   大小: {progress_file.stat().st_size} bytes")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    main()
