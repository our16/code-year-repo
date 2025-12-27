#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试自动发现功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config_loader import ConfigLoader


def test_auto_discovery():
    """测试自动发现Git仓库功能"""
    print("=" * 60)
    print("测试自动发现功能")
    print("=" * 60)

    # 测试1：扫描当前项目目录
    print("\n[测试1] 扫描当前项目目录...")
    loader = ConfigLoader('config.yaml')

    test_path = os.path.dirname(os.path.abspath(__file__))
    print(f"扫描路径: {test_path}")

    try:
        discovered = loader.discover_git_repos(test_path, max_depth=1)
        print(f"发现 {len(discovered)} 个Git仓库:")
        for repo in discovered:
            print(f"  - {repo['name']}: {repo['path']}")
    except Exception as e:
        print(f"错误: {str(e)}")

    # 测试2：扫描父目录
    print("\n[测试2] 扫描父目录（如果存在）...")
    parent_path = os.path.dirname(test_path)

    if os.path.exists(parent_path):
        print(f"扫描路径: {parent_path}")
        try:
            discovered = loader.discover_git_repos(parent_path, max_depth=2)
            print(f"发现 {len(discovered)} 个Git仓库:")
            for repo in discovered[:10]:  # 只显示前10个
                print(f"  - {repo['name']}: {repo['path']}")
            if len(discovered) > 10:
                print(f"  ... 还有 {len(discovered) - 10} 个仓库")
        except Exception as e:
            print(f"错误: {str(e)}")
    else:
        print("父目录不存在，跳过测试")

    # 测试3：配置加载
    print("\n[测试3] 测试配置加载（自动发现模式）...")
    try:
        config = loader.load()
        print(f"配置加载成功!")
        print(f"  项目数量: {len(config.get('projects', []))}")
        print(f"  Authors: {config.get('authors', [])}")
        print(f"  报告年份: {config.get('report_year', 2024)}")
    except Exception as e:
        print(f"配置加载失败: {str(e)}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == '__main__':
    test_auto_discovery()
