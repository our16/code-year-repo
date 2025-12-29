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
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

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


def generate_single_report(author_info, author_projects, author_data_map, config, analyzer, llm_client, output_dir, max_file_size_mb=1):
    """生成单个作者的报告（用于并发处理）

    Returns:
        tuple: (author_info, report_data, uuid_mapping_info)
    """
    author_name = author_info.split('<')[0].strip()
    author_email = author_info.split('<')[1].replace('>', '').strip() if '<' in author_info else ''

    print(f"   分析作者: {author_name}")

    # 生成UUID作为访问标识
    author_uuid = str(uuid.uuid4())

    # 分析数据（限制详细提交记录数量以控制文件大小）
    analyzed_data = analyzer.analyze(author_projects, max_commits=1000)

    # 生成AI文案
    ai_text = None
    if llm_client:
        try:
            ai_text = llm_client.generate_report_text(analyzed_data)
            print(f"      AI文案生成成功")
        except Exception as e:
            print(f"      警告: AI文案生成失败 - {str(e)}")

    # 构建报告数据
    report_data = {
        'meta': {
            'author': author_name,
            'email': author_email,
            'author_id': author_info,
            'uuid': author_uuid,  # 添加UUID
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

    # 保存JSON文件（使用UUID命名，避免中文和特殊字符）
    json_filename = f"{author_uuid}.json"
    json_path = output_dir / json_filename

    # 先写入临时文件检查大小
    temp_path = output_dir / f"{author_uuid}.json.tmp"
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    # 检查文件大小
    file_size_mb = temp_path.stat().st_size / (1024 * 1024)
    max_file_size_bytes = max_file_size_mb * 1024 * 1024

    # 如果文件超过1MB，分片存储
    if temp_path.stat().st_size > max_file_size_bytes:
        print(f"      警告: JSON文件过大 ({file_size_mb:.2f}MB)，启用分片存储...")

        # 创建分片：将每个项目的commits单独存储
        chunk_files = []

        for project_idx, project in enumerate(report_data.get('projects', [])):
            commits = project.get('commits', [])

            if not commits:
                continue

            # 计算这个项目的commits大小
            project_data = {
                'project_name': project.get('name', ''),
                'commits': commits
            }
            project_json = json.dumps(project_data, ensure_ascii=False, indent=2)
            project_size = len(project_json.encode('utf-8'))

            # 如果单个项目的commits也很大，进一步分片
            if project_size > max_file_size_bytes:
                # 将commits分成多个文件，每个文件不超过限制
                commits_per_chunk = max_commits or 500
                num_chunks = (len(commits) + commits_per_chunk - 1) // commits_per_chunk

                for chunk_idx in range(num_chunks):
                    start_idx = chunk_idx * commits_per_chunk
                    end_idx = min(start_idx + commits_per_chunk, len(commits))
                    chunk_commits = commits[start_idx:end_idx]

                    chunk_data = {
                        'project_name': project.get('name', ''),
                        'chunk_index': chunk_idx,
                        'total_chunks': num_chunks,
                        'commits': chunk_commits
                    }

                    chunk_filename = f"{author_uuid}_p{project_idx}_c{chunk_idx}.json"
                    chunk_path = output_dir / chunk_filename

                    with open(chunk_path, 'w', encoding='utf-8') as f:
                        json.dump(chunk_data, f, ensure_ascii=False, indent=2)

                    chunk_files.append(chunk_filename)
                    chunk_size_mb = chunk_path.stat().st_size / (1024 * 1024)
                    print(f"      分片 {chunk_filename}: {chunk_size_mb:.2f}MB ({len(chunk_commits)} commits)")

                # 在主文件中标记已分片
                project['commits_chunked'] = True
                project['commits_chunks'] = [
                    f"{author_uuid}_p{project_idx}_c{i}.json"
                    for i in range(num_chunks)
                ]
                project['commits'] = []  # 清空主文件中的commits
            else:
                # 单个项目大小合适，单独存储
                chunk_filename = f"{author_uuid}_p{project_idx}.json"
                chunk_path = output_dir / chunk_filename

                with open(chunk_path, 'w', encoding='utf-8') as f:
                    json.dump(project_data, f, ensure_ascii=False, indent=2)

                chunk_files.append(chunk_filename)
                chunk_size_mb = chunk_path.stat().st_size / (1024 * 1024)
                print(f"      分片 {chunk_filename}: {chunk_size_mb:.2f}MB ({len(commits)} commits)")

                # 在主文件中标记
                project['commits_chunked'] = True
                project['commits_chunk_file'] = chunk_filename
                project['commits'] = []

        # 更新主文件的meta信息
        report_data['meta']['chunked'] = True
        report_data['meta']['chunk_files'] = chunk_files
        report_data['meta']['total_chunks'] = len(chunk_files)

        # 重新写入主文件（现在应该很小了）
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        file_size_mb = temp_path.stat().st_size / (1024 * 1024)
        print(f"      主文件 {json_filename}: {file_size_mb:.2f}MB (包含 {len(chunk_files)} 个分片)")

    # 重命名为正式文件
    temp_path.rename(json_path)

    report_data['meta']['json_file'] = json_filename
    report_data['meta']['file_size_mb'] = round(file_size_mb, 2)

    # UUID映射信息
    uuid_mapping_info = {
        'author_info': author_info,
        'author_name': author_name,
        'author_email': author_email,
    }

    # 索引信息
    index_info = {
        'uuid': author_uuid,
        'id': author_info,  # 保留原始author_id用于兼容
        'name': report_data['meta']['author'],
        'email': report_data['meta']['email'],
        'commits': report_data['summary']['total_commits'],
        'net_lines': report_data['summary']['net_lines'],
        'projects': len(report_data['projects']),
        'json_file': report_data['meta']['json_file'],
        'generated_at': report_data['meta']['generated_at'],
    }

    print(f"      报告已生成: {json_filename}")

    return author_uuid, report_data, uuid_mapping_info, index_info


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

    # 5. 为每个作者生成JSON报告（支持LLM并发）
    print(f"\n[5/6] 生成JSON报告...")

    analyzer = DataAnalyzer(config)
    output_dir.mkdir(parents=True, exist_ok=True)

    report_index = {}
    uuid_mapping = {}  # UUID与作者信息的映射
    generated_reports = []

    # 获取LLM并发配置
    concurrency_config = config.get('concurrency', {})
    llm_workers = concurrency_config.get('llm_workers', 3)
    use_llm_parallel = llm_client is not None and llm_workers > 1

    if use_llm_parallel and len(author_data_map) > 1:
        # 并发生成报告
        print(f"   使用LLM并发生成报告（并发数: {llm_workers}）...")

        with ThreadPoolExecutor(max_workers=llm_workers) as executor:
            # 提交所有生成任务
            future_to_author = {
                executor.submit(
                    generate_single_report,
                    author_info,
                    author_projects,
                    author_data_map,
                    config,
                    analyzer,
                    llm_client,
                    output_dir
                ): author_info
                for author_info, author_projects in author_data_map.items()
            }

            # 收集结果
            completed = 0
            for future in as_completed(future_to_author):
                try:
                    author_uuid, report_data, uuid_info, index_info = future.result()

                    # 保存到索引
                    report_index[author_uuid] = index_info
                    uuid_mapping[author_uuid] = uuid_info
                    generated_reports.append(report_data)

                    completed += 1
                    save_progress(progress_file, {
                        'status': 'generating',
                        'total': total_authors,
                        'completed': completed,
                        'current': f'已完成 {completed}/{total_authors}',
                        'percentage': round(completed / total_authors * 100, 1)
                    })

                except Exception as exc:
                    author_info = future_to_author[future]
                    print(f"      警告: 生成报告失败 {author_info}: {exc}")
    else:
        # 串行生成报告
        for idx, (author_info, author_projects) in enumerate(author_data_map.items(), 1):
            # 更新进度
            save_progress(progress_file, {
                'status': 'generating',
                'total': total_authors,
                'completed': idx - 1,
                'current': f'正在分析 {author_info.split("<")[0].strip()}',
                'percentage': round((idx - 1) / total_authors * 100, 1)
            })

            author_uuid, report_data, uuid_info, index_info = generate_single_report(
                author_info, author_projects, author_data_map,
                config, analyzer, llm_client, output_dir
            )

            # 保存到索引
            report_index[author_uuid] = index_info
            uuid_mapping[author_uuid] = uuid_info
            generated_reports.append(report_data)

    # 6. 生成总索引文件和UUID映射文件
    print(f"\n[6/6] 生成总索引文件和UUID映射...")

    index_path = output_dir / 'report_index.json'
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(report_index, f, ensure_ascii=False, indent=2)
    print(f"   [OK] 索引文件: report_index.json")

    # 保存UUID映射关系（便于管理员查看）
    uuid_mapping_path = output_dir / 'uuid_mapping.json'
    with open(uuid_mapping_path, 'w', encoding='utf-8') as f:
        json.dump(uuid_mapping, f, ensure_ascii=False, indent=2)
    print(f"   [OK] UUID映射: uuid_mapping.json")

    # 统计文件大小
    total_size = sum(
        (output_dir / info['json_file']).stat().st_size
        for info in report_index.values()
        if (output_dir / info['json_file']).exists()
    )
    print(f"   [OK] JSON文件: {len(generated_reports)} 个文件，总大小 {total_size / (1024*1024):.2f}MB")

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
