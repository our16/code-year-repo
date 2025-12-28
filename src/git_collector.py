#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git数据采集器
"""

import os
import git
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class GitDataCollector:
    """Git数据采集器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.authors = config.get('authors', [])
        self.report_year = config.get('report_year', 2024)
        # 并发配置：从配置文件读取最大并发数，默认为4
        self.max_workers = config.get('max_workers', 4)
        # 线程锁，用于保护日志输出
        self.log_lock = threading.Lock()

    def _is_target_author(self, commit: git.Commit) -> bool:
        """判断提交是否属于目标作者"""
        # 如果没有配置authors，则包含所有作者
        if not self.authors:
            return True

        author_name = commit.author.name.lower()
        author_email = commit.author.email.lower()

        for author in self.authors:
            author_lower = author.lower()
            if author_lower in author_name or author_lower in author_email:
                return True
        return False

    def _is_target_year(self, commit: git.Commit) -> bool:
        """判断提交是否属于目标年份"""
        commit_date = datetime.fromtimestamp(commit.committed_date)
        return commit_date.year == self.report_year

    def _get_file_stats(self, diff) -> Dict[str, int]:
        """获取文件变更统计"""
        additions = 0
        deletions = 0

        try:
            for diff_item in diff:
                # 获取新增和删除的行数
                if diff_item.a_blob and diff_item.b_blob:
                    # 文件被修改
                    additions += diff_item.diff.count(b'+') - diff_item.diff.count(b'+++')
                    deletions += diff_item.diff.count(b'-') - diff_item.diff.count(b'---')
                elif diff_item.a_blob is None and diff_item.b_blob:
                    # 新文件
                    additions += len(diff_item.diff.split(b'\n'))
                elif diff_item.a_blob and diff_item.b_blob is None:
                    # 删除文件
                    deletions += len(diff_item.diff.split(b'\n'))
        except Exception:
            pass

        return {'additions': max(0, additions), 'deletions': max(0, deletions)}

    def _detect_language(self, file_path: str) -> str:
        """根据文件扩展名检测编程语言"""
        ext_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sql': 'SQL',
            '.sh': 'Shell',
            '.md': 'Markdown',
        }

        _, ext = os.path.splitext(file_path.lower())
        return ext_map.get(ext, 'Other')

    def collect_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """采集单个项目的Git数据"""
        repo_path = project['path']
        project_name = project['name']

        try:
            repo = git.Repo(repo_path)
        except Exception as e:
            raise Exception(f"无法打开Git仓库: {str(e)}")

        # 数据结构
        commits_data = []
        language_stats = defaultdict(int)
        file_changes = defaultdict(int)

        # 遍历提交记录
        for commit in repo.iter_commits():
            # 筛选目标作者和年份
            if not self._is_target_author(commit):
                continue
            if not self._is_target_year(commit):
                continue

            commit_date = datetime.fromtimestamp(commit.committed_date)

            # 获取提交的文件变更
            additions = 0
            deletions = 0
            files_changed = 0

            try:
                if commit.parents:
                    # 获取与父提交的差异
                    parent = commit.parents[0]
                    diff = parent.diff(commit, create_patch=True, **{'unified': 0})

                    for diff_item in diff:
                        files_changed += 1
                        file_path = diff_item.a_path if diff_item.a_path else diff_item.b_path

                        # 检测语言
                        if file_path:
                            lang = self._detect_language(file_path)
                            language_stats[lang] += 1
                            file_changes[file_path] += 1

                        # 更准确的行数统计
                        try:
                            diff_text = diff_item.diff.decode('utf-8', errors='ignore')
                            lines = diff_text.split('\n')

                            for line in lines:
                                # 统计新增行（以+开头，但不是+++）
                                if line.startswith('+') and not line.startswith('+++'):
                                    additions += 1
                                # 统计删除行（以-开头，但不是---）
                                elif line.startswith('-') and not line.startswith('---'):
                                    deletions += 1
                        except Exception:
                            pass
                else:
                    # 初始提交（没有父提交）
                    try:
                        # 统计所有新增文件
                        for item in commit.tree.traverse():
                            if item.type == 'blob':
                                try:
                                    data = item.data_stream.read()
                                    # 简单估算：假设平均每行40个字符
                                    lines = max(1, len(data.decode('utf-8', errors='ignore')) // 40)
                                    additions += lines
                                    files_changed += 1
                                except Exception:
                                    pass
                    except Exception:
                        pass
            except Exception as e:
                # 如果diff解析失败，尝试从stats中获取
                try:
                    stats = commit.stats.total
                    additions += stats['insertions']
                    deletions += stats['deletions']
                    files_changed += stats['files']
                except Exception:
                    print(f"      警告: 无法解析提交 {commit.hexsha[:8]} 的差异: {str(e)}")
                    continue

            # 保存提交数据
            commits_data.append({
                'hash': commit.hexsha,
                'short_hash': commit.hexsha[:8],
                'date': commit_date.isoformat(),
                'timestamp': commit.committed_date,
                'message': commit.message.strip(),
                'author': commit.author.name,
                'email': commit.author.email,
                'files_changed': files_changed,
                'additions': max(0, additions),
                'deletions': max(0, deletions),
            })

        # 获取分支名（处理detached HEAD状态）
        try:
            branch = repo.active_branch.name
        except Exception:
            # detached HEAD状态，尝试从HEAD获取
            try:
                branch = repo.head.commit.hexsha[:8]
            except Exception:
                branch = 'HEAD'

        return {
            'project_name': project_name,
            'path': repo_path,
            'commits': commits_data,
            'language_stats': dict(language_stats),
            'total_commits': len(commits_data),
            'branch': branch,
        }

    def collect_all(self) -> List[Dict[str, Any]]:
        """采集所有项目的数据（串行模式）"""
        all_data = []

        for project in self.config.get('projects', []):
            try:
                project_data = self.collect_project(project)
                all_data.append(project_data)
            except Exception as e:
                print(f"错误: 采集项目 {project.get('name')} 失败: {str(e)}")
                continue

        return all_data

    def collect_all_parallel(self) -> List[Dict[str, Any]]:
        """并发采集所有项目的数据

        使用线程池并发处理多个项目，提升大型仓库的扫描速度。
        每个项目的扫描在独立线程中执行，充分利用多核CPU和IO等待时间。

        Returns:
            所有项目的采集数据列表
        """
        projects = self.config.get('projects', [])
        if not projects:
            return []

        # 如果项目数量少，使用串行模式
        if len(projects) <= 1:
            return self.collect_all()

        all_data = []
        failed_projects = []

        # 使用线程池并发采集
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有采集任务
            future_to_project = {
                executor.submit(self.collect_project, project): project
                for project in projects
            }

            # 使用as_completed按完成顺序处理结果
            for future in as_completed(future_to_project):
                project = future_to_project[future]
                try:
                    project_data = future.result()
                    with self.log_lock:
                        print(f"✓ 完成扫描: {project.get('name', project.get('path'))}")
                    all_data.append(project_data)
                except Exception as e:
                    with self.log_lock:
                        print(f"✗ 扫描失败: {project.get('name', project.get('path'))} - {str(e)}")
                    failed_projects.append(project)

        # 输出失败的项目
        if failed_projects:
            print(f"\n警告: {len(failed_projects)} 个项目扫描失败:")
            for project in failed_projects:
                print(f"  - {project.get('name', project.get('path'))}")

        print(f"\n并发扫描完成: 成功 {len(all_data)}/{len(projects)} 个项目")
        return all_data
