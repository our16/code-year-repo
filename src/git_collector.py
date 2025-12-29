#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git数据采集器
"""

import os
import git
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from pathlib import Path
from logger_config import get_logger

logger = get_logger(__name__)


class GitDataCollector:
    """Git数据采集器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.authors = config.get('authors', [])
        self.report_year = config.get('report_year', 2024)

        # 并发配置：从配置文件读取并发参数
        concurrency_config = config.get('concurrency', {})
        self.repo_workers = concurrency_config.get('repo_workers', 4)  # 仓库扫描并发数
        self.commit_workers = concurrency_config.get('commit_workers', 8)  # 提交分析并发数
        self.max_workers = concurrency_config.get('max_workers', 16)  # 总体最大并发数

        # 线程锁，用于保护日志输出和文件写入
        self.log_lock = threading.Lock()
        self.file_lock = threading.Lock()
        # 增量持久化目录
        self.cache_dir = Path(config.get('cache_dir', './.git_scan_cache'))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_project_cache_path(self, project_name: str, year: int) -> Path:
        """获取项目缓存文件路径"""
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in project_name)
        return self.cache_dir / f"{safe_name}_{year}.json"

    def _save_project_cache(self, project: Dict[str, Any], project_data: Dict[str, Any]):
        """保存项目扫描结果到缓存文件"""
        try:
            cache_path = self._get_project_cache_path(project.get('name', project.get('path')), self.report_year)

            with self.file_lock:
                cache_data = {
                    'project': project,
                    'data': project_data,
                    'scan_time': datetime.now().isoformat(),
                    'report_year': self.report_year
                }

                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)

                with self.log_lock:
                    logger.info(f"  ✓ 已保存缓存: {cache_path.name}")
        except Exception as e:
            with self.log_lock:
                logger.warning(f"  ✗ 保存缓存失败: {e}")

    def _load_project_cache(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """从缓存加载项目扫描结果"""
        try:
            cache_path = self._get_project_cache_path(project.get('name', project.get('path')), self.report_year)

            if not cache_path.exists():
                return None

            with self.file_lock:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                # 验证缓存年份是否匹配
                if cache_data.get('report_year') != self.report_year:
                    logger.info(f"  缓存年份不匹配，将重新扫描")
                    return None

                with self.log_lock:
                    logger.info(f"  ✓ 从缓存加载: {cache_path.name}")

                return cache_data.get('data')
        except Exception as e:
            with self.log_lock:
                logger.warning(f"  ✗ 加载缓存失败: {e}")
            return None

    def _clear_all_cache(self):
        """清空所有缓存"""
        try:
            import shutil
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"已清空缓存目录: {self.cache_dir}")
        except Exception as e:
            logger.warning(f"清空缓存失败: {e}")

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

    def _analyze_commit(self, commit: git.Commit, repo) -> Dict[str, Any]:
        """分析单个提交（用于并发处理）"""
        commit_date = datetime.fromtimestamp(commit.committed_date)

        # 获取提交的文件变更
        additions = 0
        deletions = 0
        files_changed = 0
        languages = []
        changed_files = []

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
                        languages.append(lang)
                        changed_files.append(file_path)

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
                with self.log_lock:
                    logger.warning(f"警告: 无法解析提交 {commit.hexsha[:8]} 的差异: {str(e)}")

        return {
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
            'languages': languages,
            'changed_files': changed_files,
        }

    def collect_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """采集单个项目的Git数据（支持并发）"""
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

        # 优化：根据年份确定时间范围，减少遍历的提交数量
        # GitPython的iter_commits支持since和until参数进行时间范围过滤
        since_date = None
        until_date = None

        try:
            if self.report_year:
                # 设置目标年份的时间范围（从年初到年末）
                since_date = datetime(self.report_year, 1, 1)
                until_date = datetime(self.report_year + 1, 1, 1)  # 下一年1月1日

                with self.log_lock:
                    logger.info(f"  时间范围: {since_date.strftime('%Y-%m-%d')} ~ {until_date.strftime('%Y-%m-%d')}")
        except Exception as e:
            with self.log_lock:
                logger.warning(f"  时间范围设置失败: {e}, 将遍历所有提交")
            since_date = None
            until_date = None

        # 遍历提交记录（使用时间范围过滤）
        if since_date and until_date:
            # 使用Git的时间范围过滤，大幅减少遍历的提交数
            commit_iterator = repo.iter_commits(since=since_date, until=until_date)
        else:
            # 无时间范围限制，遍历所有提交
            commit_iterator = repo.iter_commits()

        # 先收集符合条件的提交（不进行分析）
        target_commits = []
        for commit in commit_iterator:
            # 筛选目标作者和年份
            if not self._is_target_author(commit):
                continue
            if not self._is_target_year(commit):
                continue
            target_commits.append(commit)

        if not target_commits:
            with self.log_lock:
                logger.info(f"  没有找到符合条件的提交")
            return {
                'project_name': project_name,
                'path': repo_path,
                'commits': [],
                'language_stats': {},
                'total_commits': 0,
                'branch': 'HEAD',
            }

        with self.log_lock:
            logger.info(f"  找到 {len(target_commits)} 个符合条件的提交，开始并发分析...")

        # 使用线程池并发分析提交
        commits_data = []
        with ThreadPoolExecutor(max_workers=self.commit_workers) as executor:
            # 提交所有任务
            future_to_commit = {
                executor.submit(self._analyze_commit, commit, repo): commit
                for commit in target_commits
            }

            # 收集结果
            completed = 0
            for future in as_completed(future_to_commit):
                try:
                    result = future.result()
                    commits_data.append(result)

                    completed += 1
                    if completed % 100 == 0 or completed == len(target_commits):
                        with self.log_lock:
                            logger.info(f"    进度: {completed}/{len(target_commits)}")
                except Exception as exc:
                    commit = future_to_commit[future]
                    with self.log_lock:
                        logger.warning(f"    分析提交 {commit.hexsha[:8]} 时出错: {exc}")

        # 按时间排序
        commits_data.sort(key=lambda x: x['timestamp'], reverse=True)

        # 汇总语言统计和文件变更
        for commit_data in commits_data:
            for lang in commit_data.get('languages', []):
                language_stats[lang] += 1
            for file_path in commit_data.get('changed_files', []):
                file_changes[file_path] += 1

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

    def collect_all(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """采集所有项目的数据（串行模式）

        Args:
            use_cache: 是否使用缓存（默认True）

        Returns:
            所有项目的采集数据列表
        """
        all_data = []
        cached_count = 0

        # 尝试从缓存加载
        if use_cache:
            with self.log_lock:
                logger.info(f"检查缓存...")

            projects_to_scan = []
            for project in self.config.get('projects', []):
                cached_data = self._load_project_cache(project)
                if cached_data:
                    all_data.append(cached_data)
                    cached_count += 1
                else:
                    projects_to_scan.append(project)

            if cached_count > 0:
                with self.log_lock:
                    logger.info(f"从缓存加载了 {cached_count}/{len(self.config.get('projects', []))} 个项目")

            if not projects_to_scan:
                with self.log_lock:
                    logger.info(f"所有项目均来自缓存，扫描完成！")
                return all_data
        else:
            projects_to_scan = self.config.get('projects', [])
            self._clear_all_cache()

        # 扫描未缓存的项目
        for project in projects_to_scan:
            try:
                with self.log_lock:
                    logger.info(f"  扫描项目: {project.get('name', project.get('path'))}")

                project_data = self.collect_project(project)

                # 立即保存到缓存
                if use_cache:
                    self._save_project_cache(project, project_data)

                all_data.append(project_data)
            except Exception as e:
                with self.log_lock:
                    logger.error(f"扫描项目失败: {str(e)}")
                continue

        return all_data

    def collect_all_parallel(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """并发采集所有项目的数据

        使用线程池并发处理多个项目，提升大型仓库的扫描速度。
        每个项目的扫描在独立线程中执行，充分利用多核CPU和IO等待时间。
        支持增量持久化，扫描完每个项目后立即保存到缓存文件。

        Args:
            use_cache: 是否使用缓存（默认True）

        Returns:
            所有项目的采集数据列表
        """
        projects = self.config.get('projects', [])
        if not projects:
            return []

        # 如果项目数量少，使用串行模式
        if len(projects) <= 1:
            return self.collect_all(use_cache)

        all_data = []
        failed_projects = []
        cached_count = 0

        # 尝试从缓存加载已扫描的项目
        if use_cache:
            with self.log_lock:
                logger.info(f"检查缓存...")

            projects_to_scan = []
            for project in projects:
                cached_data = self._load_project_cache(project)
                if cached_data:
                    all_data.append(cached_data)
                    cached_count += 1
                else:
                    projects_to_scan.append(project)

            if cached_count > 0:
                with self.log_lock:
                    logger.info(f"从缓存加载了 {cached_count}/{len(projects)} 个项目")

            if not projects_to_scan:
                with self.log_lock:
                    logger.info(f"所有项目均来自缓存，扫描完成！")
                return all_data
        else:
            projects_to_scan = projects
            # 清空缓存
            self._clear_all_cache()

        # 使用线程池并发采集未缓存的项目（使用repo_workers配置）
        with ThreadPoolExecutor(max_workers=self.repo_workers) as executor:
            # 提交所有采集任务
            future_to_project = {
                executor.submit(self.collect_project, project): project
                for project in projects_to_scan
            }

            # 使用as_completed按完成顺序处理结果
            for future in as_completed(future_to_project):
                project = future_to_project[future]
                try:
                    project_data = future.result()

                    # 立即保存到缓存（增量持久化）
                    if use_cache:
                        self._save_project_cache(project, project_data)

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

        total_success = len(all_data)
        total_from_cache = cached_count
        total_from_scan = total_success - total_from_cache

        print(f"\n并发扫描完成: 成功 {total_success}/{len(projects)} 个项目")
        print(f"  - 从缓存加载: {total_from_cache} 个")
        print(f"  - 新扫描: {total_from_scan} 个")
        return all_data
