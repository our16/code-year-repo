#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 生成演示数据并测试报告生成
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from src.report_generator import SimpleReportGenerator
from src.config_loader import ConfigLoader


def generate_demo_data():
    """生成演示数据"""
    # 模拟一年的提交数据
    base_date = datetime(2024, 1, 1)

    # 生成12个月的提交数据
    commits = []
    languages = ['Python', 'JavaScript', 'TypeScript', 'Java', 'Go']
    projects = ['电商平台', '微服务框架', '数据分析平台', 'API网关', '监控系统']

    for month in range(12):
        for day in range(1, 28, 2):  # 每隔一天提交
            # 随机生成多个提交
            num_commits = (month % 3) + 1 + (day % 5)
            for i in range(num_commits):
                commit_date = base_date + timedelta(days=month * 30 + day, hours=i * 2)

                commits.append({
                    'hash': f"commit_{len(commits)}",
                    'short_hash': f"{len(commits):08x}"[:8],
                    'date': commit_date.isoformat(),
                    'timestamp': int(commit_date.timestamp()),
                    'message': f"feat: 实现新功能 {i+1}",
                    'author': "Demo User",
                    'email': "demo@example.com",
                    'files_changed': (day % 5) + 1,
                    'additions': (day * 10) + (i * 5),
                    'deletions': (day * 3) + (i * 2),
                })

    # 语言统计
    language_stats = {
        'Python': 350,
        'JavaScript': 280,
        'TypeScript': 200,
        'Java': 150,
        'Go': 100,
    }

    # 项目数据
    projects_data = []
    for i, project_name in enumerate(projects):
        project_commits = [c for c in commits if hash(c['date']) % 5 == i]
        if not project_commits:
            project_commits = commits[i*10:(i+1)*10]

        total_additions = sum(c['additions'] for c in project_commits)
        total_deletions = sum(c['deletions'] for c in project_commits)

        projects_data.append({
            'name': project_name,
            'commits': len(project_commits),
            'additions': total_additions,
            'deletions': total_deletions,
            'net_lines': total_additions - total_deletions,
        })

    # 计算汇总数据
    total_commits = len(commits)
    total_additions = sum(c['additions'] for c in commits)
    total_deletions = sum(c['deletions'] for c in commits)

    # 生成日历热力图数据
    calendar_heatmap = []
    for month in range(12):
        for day in range(1, 32):
            date_str = f"2024-{(month+1):02d}-{day:02d}"
            # 模拟提交次数
            count = (day + month * 3) % 15
            if count > 0:
                level = min(4, (count // 3) + 1)
                calendar_heatmap.append({
                    'date': date_str,
                    'count': count,
                    'level': level
                })

    # 按月统计
    monthly_commits = {}
    for commit in commits:
        month = commit['date'][:7]
        monthly_commits[month] = monthly_commits.get(month, 0) + 1

    # 按星期统计
    weekday_commits = {i: 0 for i in range(7)}
    for commit in commits:
        dt = datetime.fromisoformat(commit['date'])
        weekday_commits[dt.weekday()] += 1

    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    weekday_commits_named = {weekday_names[i]: weekday_commits[i] for i in range(7)}

    # 按小时统计
    hourly_commits = {i: 0 for i in range(24)}
    for commit in commits:
        dt = datetime.fromisoformat(commit['date'])
        hourly_commits[dt.hour] += 1

    # 语言分布
    total_lang_count = sum(language_stats.values())
    top_languages = [
        {
            'name': lang,
            'count': count,
            'percentage': round(count / total_lang_count * 100, 1)
        }
        for lang, count in sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
    ]

    # 重构数据
    refactor_commits = [c for c in commits if c['deletions'] > c['additions'] * 1.2]
    top_refactors = sorted(
        [c for c in commits if c['deletions'] > c['additions']],
        key=lambda x: x['deletions'] - x['additions'],
        reverse=True
    )[:5]

    demo_data = {
        'year': 2024,
        'summary': {
            'total_commits': total_commits,
            'total_additions': total_additions,
            'total_deletions': total_deletions,
            'net_lines': total_additions - total_deletions,
            'files_changed': sum(c['files_changed'] for c in commits),
            'avg_commits_per_month': round(total_commits / 12, 1),
            'most_active_day': '2024-06-15',
        },
        'time_distribution': {
            'monthly': monthly_commits,
            'weekday': weekday_commits_named,
            'hourly': hourly_commits,
            'calendar_heatmap': calendar_heatmap,
            'best_period': {
                'hour': '14:00-15:00',
                'weekday': '周三',
            }
        },
        'code_quality': {
            'refactor_commits': len(refactor_commits),
            'refactor_ratio': round(len(refactor_commits) / total_commits * 100, 1),
            'top_refactors': [
                {
                    'date': c['date'][:10],
                    'message': c['message'][:50],
                    'net_lines': c['deletions'] - c['additions']
                }
                for c in top_refactors
            ],
            'avg_additions_per_commit': round(total_additions / total_commits, 1),
            'avg_deletions_per_commit': round(total_deletions / total_commits, 1),
        },
        'languages': {
            'total': total_lang_count,
            'top_languages': top_languages,
            'distribution': {lang: round(count / total_lang_count * 100, 1)
                           for lang, count in language_stats.items()},
        },
        'projects': projects_data,
        'raw_data': {
            'total_commits': total_commits,
            'language_stats': language_stats,
        }
    }

    return demo_data


def test_report_generation():
    """测试报告生成"""
    print("=" * 60)
    print("代码年度报告生成器 - 测试模式")
    print("=" * 60)

    # 生成演示数据
    print("\n[1/3] 生成演示数据...")
    demo_data = generate_demo_data()
    print(f"   ✓ 总提交次数: {demo_data['summary']['total_commits']}")
    print(f"   ✓ 净增代码行: {demo_data['summary']['net_lines']}")
    print(f"   ✓ 参与项目数: {len(demo_data['projects'])}")

    # 保存演示数据
    print("\n[2/3] 保存演示数据...")
    output_dir = Path('./reports')
    output_dir.mkdir(parents=True, exist_ok=True)

    data_path = output_dir / 'demo_data.json'
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(demo_data, f, ensure_ascii=False, indent=2)
    print(f"   ✓ 数据已保存: {data_path.absolute()}")

    # 生成报告
    print("\n[3/3] 生成HTML报告...")

    # 使用默认配置
    config = {
        'report_year': 2024,
        'output_dir': './reports',
        'theme': {
            'primary_color': '#667eea',
            'secondary_color': '#764ba2',
            'accent_color': '#f093fb',
        },
        'llm': {
            'provider': 'openai',
            'api_key': '',  # 不使用LLM，使用默认文案
        }
    }

    generator = SimpleReportGenerator(config, use_llm=False)
    report_html = generator.generate(demo_data)

    # 保存报告
    report_path = output_dir / 'demo_report.html'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_html)

    print(f"   ✓ 报告已保存: {report_path.absolute()}")

    print("\n" + "=" * 60)
    print("✓ 测试完成!")
    print("=" * 60)
    print(f"\n请在浏览器中打开报告查看效果:")
    print(f"file:///{report_path.absolute()}\n")


if __name__ == '__main__':
    test_report_generation()
