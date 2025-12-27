#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件加载器
"""

import os
import yaml
from typing import Dict, Any, List


class ConfigLoader:
    """配置文件加载器"""

    def __init__(self, config_path: str):
        self.config_path = config_path

    def discover_git_repos(self, root_path: str, max_depth: int = 3) -> List[Dict[str, str]]:
        """
        自动发现目录下的所有Git仓库

        Args:
            root_path: 根目录路径
            max_depth: 最大扫描深度

        Returns:
            发现的Git仓库列表 [{'path': '...', 'name': '...'}, ...]
        """
        if not os.path.exists(root_path):
            raise ValueError(f"目录不存在: {root_path}")

        discovered_repos = []

        # 遍历目录
        for root, dirs, files in os.walk(root_path):
            # 计算当前深度
            current_depth = root[len(root_path):].count(os.sep)
            if current_depth > max_depth:
                # 跳过更深层的目录
                dirs[:] = []
                continue

            # 检查是否是Git仓库
            if '.git' in dirs or '.git' in files:
                # 使用文件夹名作为项目名
                project_name = os.path.basename(root)
                discovered_repos.append({
                    'path': os.path.abspath(root),
                    'name': project_name,
                    'auto_discovered': True
                })

                # 跳过Git仓库的子目录
                dirs[:] = []

        return discovered_repos

    def load(self) -> Dict[str, Any]:
        """加载并验证配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 设置默认值
        config.setdefault('report_year', 2024)
        config.setdefault('output_dir', './reports')
        config.setdefault('language', 'zh-CN')
        config.setdefault('theme', {})

        # 处理项目配置：支持自动发现
        if 'projects' in config and config['projects']:
            processed_projects = []

            for project in config['projects']:
                if isinstance(project, dict):
                    path = project.get('path')

                    # 检查是否配置了自动发现
                    if path and os.path.isdir(path):
                        git_dir = os.path.join(path, '.git')
                        if os.path.exists(git_dir):
                            # 这是一个Git仓库，直接添加
                            processed_projects.append(project)
                        else:
                            # 不是Git仓库，尝试自动发现子目录中的Git仓库
                            print(f"\n正在扫描目录: {path}")
                            discovered = self.discover_git_repos(path)
                            if discovered:
                                print(f"发现 {len(discovered)} 个Git仓库:")
                                for repo in discovered:
                                    print(f"  - {repo['name']}: {repo['path']}")
                                processed_projects.extend(discovered)
                            else:
                                print(f"警告: 在 {path} 中未发现任何Git仓库")
                    else:
                        # 路径不存在或无效，但仍保留配置（可能稍后会手动添加）
                        processed_projects.append(project)

            config['projects'] = processed_projects

        # 验证项目配置
        if 'projects' not in config or not config['projects']:
            raise ValueError("配置文件中缺少有效的 'projects' 配置，或指定的目录中未发现Git仓库")

        # authors 可以为空，表示包含所有作者
        if 'authors' not in config:
            config['authors'] = []

        return config

    def validate_projects(self) -> bool:
        """验证项目路径是否存在"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        for project in config.get('projects', []):
            path = project.get('path')
            if not path or not os.path.exists(path):
                return False
            git_dir = os.path.join(path, '.git')
            if not os.path.exists(git_dir):
                return False
        return True
