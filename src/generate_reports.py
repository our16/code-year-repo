#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成报告数据 - 从Git仓库生成JSON格式报告
"""

import json
import os
import sys
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from git_collector import GitDataCollector
from data_analyzer import DataAnalyzer
from llm_client import LLMClient
from config_loader import ConfigLoader
from logger_config import get_logger

# 获取logger
logger = get_logger(__name__)


def load_config(config_path: str) -> dict:
    """加载配置文件"""
    if not os.path.exists(config_path):
        logger.error(f"配置文件不存在: {config_path}")
        return None

    loader = ConfigLoader(config_path)
    return loader.load()


def load_author_mapping(mapping_path: str) -> Dict[str, str]:
    """加载作者映射配置"""
    if not os.path.exists(mapping_path):
        return {}

    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping = yaml.safe_load(f) or {}

    return mapping


def apply_author_mapping(author_info: str, mapping: Dict[str, str]) -> str:
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


def save_progress(progress_file: Path, data: dict):
    """保存进度"""
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # 配置文件路径
    config_path = project_root / 'config' / 'config.yaml'
    mapping_path = project_root / 'config' / 'author_mapping.yaml'
    output_dir = project_root / 'reports'
    progress_file = output_dir / '.progress.json'

    logger.info("=" * 60)
    logger.info("代码年度报告生成器")
    logger.info("=" * 60)

    # 1. 加载配置
    logger.info("[1/6] 加载配置文件...")
    config = load_config(str(config_path))
    if not config:
        sys.exit(1)

    logger.info(f"   - 分析年份: {config.get('report_year', 2025)}")
    logger.info(f"   - 项目数量: {len(config.get('projects', []))}")

    # 加载作者映射
    author_mapping = load_author_mapping(str(mapping_path))
    if author_mapping:
        logger.info(f"   - 作者映射: 已加载 {len(author_mapping)} 条映射规则")

    # 初始化进度
    save_progress(progress_file, {
        'status': 'initializing',
        'total': 0,
        'completed': 0,
        'current': '初始化中...',
        'percentage': 0
    })

    # 2. 采集Git数据
    print("\n[2/6] 采集Git数据...")
    collector_config = config.copy()
    collector_config['authors'] = []
    collector = GitDataCollector(collector_config)

    all_data = []
    all_authors = set()

    for project in config.get('projects', []):
        print(f"\n   扫描项目: {project['name']}")

        try:
            project_data = collector.collect_project(project)
            all_data.append(project_data)

            for commit in project_data.get('commits', []):
                author_info = f"{commit['author']} <{commit['email']}>"
                all_authors.add(author_info)

            print(f"   [OK] 完成: 找到 {len(project_data.get('commits', []))} 条提交记录")
        except Exception as e:
            print(f"   [FAIL] 失败: {str(e)}")
            continue

    if not all_data:
        print("\n错误: 未能收集到任何数据")
        sys.exit(1)

    print(f"\n   发现 {len(all_authors)} 位作者")

    # 3. 应用作者映射并按作者分组
    print("\n[3/6] 按作者分组数据...")

    mapped_authors = {}
    for author_info in all_authors:
        mapped_author = apply_author_mapping(author_info, author_mapping)
        if mapped_author not in mapped_authors:
            mapped_authors[mapped_author] = []
        mapped_authors[mapped_author].append(author_info)

    author_data_map = {}
    for mapped_author, original_authors in mapped_authors.items():
        author_name = mapped_author.split('<')[0].strip()
        author_email = mapped_author.split('<')[1].replace('>', '').strip() if '<' in mapped_author else ''

        author_projects = []
        for project_data in all_data:
            author_commits = []
            for original_author in original_authors:
                orig_name = original_author.split('<')[0].strip()
                orig_email = original_author.split('<')[1].replace('>', '').strip() if '<' in original_author else ''

                commits = [
                    commit for commit in project_data.get('commits', [])
                    if commit['author'] == orig_name and commit['email'] == orig_email
                ]
                author_commits.extend(commits)

            if author_commits:
                author_projects.append({
                    'project_name': project_data['project_name'],
                    'path': project_data['path'],
                    'commits': author_commits,
                    'language_stats': project_data.get('language_stats', {}),
                    'total_commits': len(author_commits),
                    'branch': project_data.get('branch', 'HEAD'),
                })

        if author_projects:
            author_data_map[mapped_author] = author_projects
            total_commits = sum(p['total_commits'] for p in author_projects)
            mapping_info = f" (映射自 {len(original_authors)} 个名字)" if len(original_authors) > 1 else ""
            print(f"   - {author_name}: {total_commits} 次提交{mapping_info}")

    # 更新进度
    total_authors = len(author_data_map)
    save_progress(progress_file, {
        'status': 'collecting',
        'total': total_authors,
        'completed': 0,
        'current': '开始生成报告...',
        'percentage': 0
    })

    # 筛选指定的作者
    target_authors = config.get('authors', [])
    if target_authors:
        filtered_data_map = {}
        for author_info in author_data_map:
            author_name = author_info.split('<')[0].strip()
            author_email = author_info.split('<')[1].replace('>', '').strip() if '<' in author_info else ''

            for target in target_authors:
                target_lower = target.lower()
                if target_lower in author_name.lower() or target_lower in author_email.lower():
                    filtered_data_map[author_info] = author_data_map[author_info]
                    break

        author_data_map = filtered_data_map
        if not author_data_map:
            print("\n错误: 没有找到匹配指定作者的提交记录")
            sys.exit(1)

    # 4. 初始化LLM
    print("\n[4/6] 初始化LLM...")
    use_llm = config.get('llm', {}).get('api_key')
    llm_client = None
    if use_llm:
        try:
            llm_client = LLMClient(config)
            print("   使用LLM生成个性化文案")
        except:
            print("   LLM初始化失败，使用预设模板")
    else:
        print("   使用预设模板生成文案")

    # 5. 为每个作者生成JSON报告
    print(f"\n[5/6] 生成JSON报告...")

    analyzer = DataAnalyzer(config)
    output_dir.mkdir(parents=True, exist_ok=True)

    report_index = {}
    generated_reports = []

    for idx, (author_info, author_projects) in enumerate(author_data_map.items(), 1):
        # 更新进度
        save_progress(progress_file, {
            'status': 'generating',
            'total': total_authors,
            'completed': idx - 1,
            'current': f'正在分析 {author_info.split("<")[0].strip()}',
            'percentage': round((idx - 1) / total_authors * 100, 1)
        })

        author_name = author_info.split('<')[0].strip()
        author_email = author_info.split('<')[1].replace('>', '').strip() if '<' in author_info else ''

        print(f"   [{idx}/{total_authors}] 分析作者: {author_name}")

        # 分析数据
        analyzed_data = analyzer.analyze(author_projects)

        # 生成AI文案
        ai_text = None
        if llm_client:
            try:
                ai_text = llm_client.generate_report_text(analyzed_data)
            except Exception as e:
                print(f"      警告: AI文案生成失败 - {str(e)}")

        # 构建报告数据
        report_data = {
            'meta': {
                'author': author_name,
                'email': author_email,
                'author_id': author_info,
                'year': config.get('report_year', 2025),
                'generated_at': datetime.now().isoformat(),
            },
            'summary': analyzed_data['summary'],
            'time_distribution': analyzed_data['time_distribution'],
            'code_quality': analyzed_data['code_quality'],
            'languages': analyzed_data['languages'],
            'projects': analyzed_data['projects'],
            'ai_text': ai_text,
            'theme': config.get('theme', {}),
        }

        # 保存JSON文件
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in author_name)
        json_filename = f"{safe_name}_{config.get('report_year', 2025)}.json"
        json_path = output_dir / json_filename

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        report_data['meta']['json_file'] = json_filename

        # 保存到索引
        report_index[author_info] = {
            'id': author_info,
            'name': report_data['meta']['author'],
            'email': report_data['meta']['email'],
            'commits': report_data['summary']['total_commits'],
            'net_lines': report_data['summary']['net_lines'],
            'projects': len(report_data['projects']),
            'json_file': report_data['meta']['json_file'],
            'generated_at': report_data['meta']['generated_at'],
        }

        generated_reports.append(report_data)

        print(f"      [OK] 报告已生成: {json_filename}")

    # 6. 生成总索引文件
    print(f"\n[6/6] 生成总索引文件...")

    index_path = output_dir / 'report_index.json'
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(report_index, f, ensure_ascii=False, indent=2)

    print(f"   [OK] 索引文件: report_index.json")

    # 更新进度为完成
    save_progress(progress_file, {
        'status': 'completed',
        'total': total_authors,
        'completed': total_authors,
        'current': '报告生成完成',
        'percentage': 100
    })

    # 完成
    print("\n" + "=" * 60)
    print("[SUCCESS] JSON数据生成完成!")
    print("=" * 60)
    print(f"\n生成了 {len(generated_reports)} 个作者报告")
    print(f"\n数据目录: {output_dir.absolute()}")


if __name__ == '__main__':
    main()
