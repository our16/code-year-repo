#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告生成核心逻辑
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Callable

from git_collector import GitDataCollector
from data_analyzer import DataAnalyzer
from llm_client import LLMClient
from config_loader import ConfigLoader
from logger_config import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """报告生成器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_path = project_root / 'config' / 'config.yaml'
        self.mapping_path = project_root / 'config' / 'author_mapping.yaml'
        self.output_dir = project_root / 'reports'
        self.progress_file = self.output_dir / '.progress.json'

        # 清理旧的未完成进度文件（避免误显示）
        self._cleanup_stale_progress()

    def _cleanup_stale_progress(self):
        """清理旧的未完成进度文件"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)

                # 如果状态是generating且超过5分钟，认为是旧任务
                if progress.get('status') == 'generating':
                    import time
                    # 检查文件修改时间
                    file_mtime = self.progress_file.stat().st_mtime
                    if time.time() - file_mtime > 300:  # 5分钟
                        logger.info("清理旧的未完成进度文件")
                        self.progress_file.unlink()
            except Exception as e:
                logger.warning(f"清理进度文件失败: {e}")

    def load_config(self) -> dict:
        """加载配置文件"""
        if not self.config_path.exists():
            logger.error(f"配置文件不存在: {self.config_path}")
            return None
        loader = ConfigLoader(str(self.config_path))
        return loader.load()

    def load_author_mapping(self) -> Dict[str, str]:
        """加载作者映射配置"""
        if not self.mapping_path.exists():
            return {}
        with open(self.mapping_path, 'r', encoding='utf-8') as f:
            mapping = yaml.safe_load(f) or {}
        return mapping

    def apply_author_mapping(self, author_info: str, mapping: Dict[str, str]) -> str:
        """应用作者映射"""
        if not mapping:
            return author_info
        author_name = author_info.split('<')[0].strip()
        author_email = author_info.split('<')[1].replace('>', '').strip() if '<' in author_info else ''
        if author_info in mapping:
            return mapping[author_info]
        if author_name in mapping:
            return mapping[author_name]
        if author_email and author_email in mapping:
            return mapping[author_email]
        return author_info

    def save_progress(self, data: dict):
        """保存进度"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def generate_all(self, progress_callback: Callable = None) -> bool:
        """生成所有报告"""
        logger.info("开始生成报告")
        
        config = self.load_config()
        if not config:
            return False
        
        author_mapping = self.load_author_mapping()
        
        # 采集数据
        collector_config = config.copy()
        collector_config['authors'] = []
        collector = GitDataCollector(collector_config)
        
        all_data = []
        all_authors = set()
        
        for project in config.get('projects', []):
            try:
                project_data = collector.collect_project(project)
                all_data.append(project_data)
                for commit in project_data.get('commits', []):
                    author_info = f"{commit['author']} <{commit['email']}>"
                    all_authors.add(author_info)
            except Exception as e:
                logger.error(f"扫描项目失败: {str(e)}")
        
        if not all_data:
            return False
        
        # 分组数据
        mapped_authors = {}
        for author_info in all_authors:
            mapped_author = self.apply_author_mapping(author_info, author_mapping)
            if mapped_author not in mapped_authors:
                mapped_authors[mapped_author] = []
            mapped_authors[mapped_author].append(author_info)
        
        author_data_map = {}
        for mapped_author, original_authors in mapped_authors.items():
            author_name = mapped_author.split('<')[0].strip()
            author_projects = []
            for project_data in all_data:
                author_commits = []
                for original_author in original_authors:
                    orig_name = original_author.split('<')[0].strip()
                    orig_email = original_author.split('<')[1].replace('>', '').strip() if '<' in original_author else ''
                    commits = [c for c in project_data.get('commits', []) if c['author'] == orig_name and c['email'] == orig_email]
                    author_commits.extend(commits)
                if author_commits:
                    author_projects.append({
                        'project_name': project_data['project_name'],
                        'path': project_data['path'],
                        'commits': author_commits,
                        'total_commits': len(author_commits),
                        'language_stats': project_data.get('language_stats', {}),  # 添加语言统计
                    })
            if author_projects:
                author_data_map[mapped_author] = author_projects
        
        # 生成报告
        analyzer = DataAnalyzer(config)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        report_index = {}
        total = len(author_data_map)

        # 初始化LLM客户端
        use_llm = config.get('llm', {}).get('api_key')
        llm_client = None
        if use_llm:
            try:
                llm_client = LLMClient(config)
                logger.info("LLM客户端初始化成功")
            except Exception as e:
                logger.warning(f"LLM客户端初始化失败: {e}，将使用默认模板")

        for idx, (author_info, author_projects) in enumerate(author_data_map.items(), 1):
            author_name = author_info.split('<')[0].strip()
            logger.info(f"[{idx}/{total}] 生成报告: {author_name}")

            analyzed_data = analyzer.analyze(author_projects)

            # 生成AI文案
            ai_text = None
            if llm_client:
                try:
                    logger.info(f"  正在调用LLM生成文案...")
                    ai_text = llm_client.generate_report_text(analyzed_data)
                    if ai_text and len(ai_text) > 100:
                        logger.info(f"  ✓ AI文案生成成功 (长度: {len(ai_text)} 字符)")
                    else:
                        logger.warning(f"  ✗ AI文案生成失败或内容过短，使用默认模板")
                        ai_text = None
                except Exception as e:
                    logger.warning(f"  ✗ AI文案生成失败: {str(e)}，使用默认模板")

            # 构建报告
            safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in author_name)
            json_filename = f"{safe_name}_{config.get('report_year', 2025)}.json"

            report_data = {
                'meta': {
                    'author': author_name,
                    'author_id': author_info,
                    'year': config.get('report_year', 2025),
                    'generated_at': datetime.now().isoformat(),
                    'json_file': json_filename,
                },
                'ai_text': ai_text,  # 添加AI生成的文案
                'theme': config.get('theme', {}),
                **analyzed_data
            }

            with open(self.output_dir / json_filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            report_index[author_info] = {
                'id': author_info,
                'name': author_name,
                'json_file': json_filename,
                'commits': report_data['summary']['total_commits'],
                'net_lines': report_data['summary']['net_lines'],
                'projects': len(report_data['projects']),
            }

            # 每生成一个报告就更新进度文件（支持前端实时检测）
            progress_data = {
                'status': 'generating',
                'total': total,
                'completed': idx,
                'current': f'正在生成 {author_name}',
                'percentage': round(idx / total * 100, 1),
                'latest_author': author_name,
                'latest_file': json_filename
            }
            self.save_progress(progress_data)

            # 调用回调函数
            if progress_callback:
                progress_callback(progress_data)
        
        # 保存索引
        with open(self.output_dir / 'report_index.json', 'w', encoding='utf-8') as f:
            json.dump(report_index, f, ensure_ascii=False, indent=2)
        
        self.save_progress({'status': 'completed', 'total': total, 'completed': total, 'percentage': 100})
        logger.info(f"生成完成: {len(report_index)} 个报告")
        return True
