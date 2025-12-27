#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 不依赖外部库，直接生成演示报告
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path


def generate_demo_data():
    """生成演示数据"""
    base_date = datetime(2024, 1, 1)

    # 生成提交数据
    commits = []
    for month in range(12):
        for day in range(1, 28, 2):
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
    language_stats = {'Python': 350, 'JavaScript': 280, 'TypeScript': 200, 'Java': 150, 'Go': 100}

    # 项目数据
    projects = ['电商平台', '微服务框架', '数据分析平台', 'API网关', '监控系统']
    projects_data = []
    for i, project_name in enumerate(projects):
        project_commits = commits[i*10:(i+1)*10] if (i+1)*10 <= len(commits) else commits[i*10:]
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
            count = (day + month * 3) % 15
            if count > 0:
                level = min(4, (count // 3) + 1)
                calendar_heatmap.append({'date': date_str, 'count': count, 'level': level})

    # 按月统计
    monthly_commits = {}
    for commit in commits:
        month = commit['date'][:7]
        monthly_commits[month] = monthly_commits.get(month, 0) + 1

    # 按星期统计
    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    weekday_commits_named = {weekday_names[i]: (i + 1) * 25 for i in range(7)}

    # 按小时统计
    hourly_commits = {i: (i % 3 + 1) * 15 for i in range(24)}

    # 语言分布
    total_lang_count = sum(language_stats.values())
    top_languages = [
        {'name': lang, 'count': count, 'percentage': round(count / total_lang_count * 100, 1)}
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
            'best_period': {'hour': '14:00-15:00', 'weekday': '周三'}
        },
        'code_quality': {
            'refactor_commits': len(refactor_commits),
            'refactor_ratio': round(len(refactor_commits) / total_commits * 100, 1),
            'top_refactors': [
                {'date': c['date'][:10], 'message': c['message'][:50], 'net_lines': c['deletions'] - c['additions']}
                for c in top_refactors
            ],
            'avg_additions_per_commit': round(total_additions / total_commits, 1),
            'avg_deletions_per_commit': round(total_deletions / total_commits, 1),
        },
        'languages': {
            'total': total_lang_count,
            'top_languages': top_languages,
            'distribution': {lang: round(count / total_lang_count * 100, 1) for lang, count in language_stats.items()},
        },
        'projects': projects_data,
        'raw_data': {'total_commits': total_commits, 'language_stats': language_stats}
    }
    return demo_data


def load_template():
    """加载HTML模板并替换变量"""
    template_path = Path(__file__).parent / 'templates' / 'report.html'
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def generate_report(data):
    """生成HTML报告"""
    html = load_template()

    # 生成默认文案
    ai_text = f"""
# 💌 致过去的一年：你的代码，你的诗篇

在冰冷的数字背后，是你一整年的热忱、思考和创造。

## 年初的Flag，是写在晨光里的序章

每一个早起的清晨，每一个静谧的深夜，键盘敲击出的不只是代码，更是你解决问题的决心。那些 **{data['summary']['total_commits']}** 次的提交，是你与复杂问题一次次交锋的勋章。

## 你的技术栈，是你探索世界的地图

这一年，你在 **Python, JavaScript, TypeScript** 等技术栈中探索。参与 **{len(data['projects'])}** 个不同项目的经历，证明你不仅是深耕某一领域的专家，更是具备全局视野的团队协作者。

## 提交时间分布，是你奋斗时刻的剪影

热力图上的每一个色块，都是你辛勤付出的坐标。找到自己的节奏，比盲目追赶更重要。

## 精简的艺术

特别值得一提的是，你的 **{data['code_quality']['refactor_ratio']}%** 的提交用于重构和优化，这展现了你对代码质量的追求。

---

*继续用代码书写你的故事吧！*
"""

    # 替换模板变量
    html = html.replace('{{ data_json }}', json.dumps(data, ensure_ascii=False))
    html = html.replace('{{ ai_text }}', ai_text)
    html = html.replace('{{ year }}', str(data['year']))
    html = html.replace('{{ primary_color | default(\'#667eea\') }}', '#667eea')
    html = html.replace('{{ secondary_color | default(\'#764ba2\') }}', '#764ba2')
    html = html.replace('{{ accent_color | default(\'#f093fb\') }}', '#f093fb')
    html = html.replace('{{ data_json | default(\'{}\') }}', json.dumps(data, ensure_ascii=False))

    return html


def main():
    print("=" * 60)
    print("代码年度报告生成器 - 快速测试")
    print("=" * 60)

    # 生成演示数据
    print("\n[1/3] Generating demo data...")
    demo_data = generate_demo_data()
    print(f"   [OK] Total commits: {demo_data['summary']['total_commits']}")
    print(f"   [OK] Net lines: {demo_data['summary']['net_lines']}")
    print(f"   [OK] Projects: {len(demo_data['projects'])}")

    # 保存演示数据
    print("\n[2/3] Saving demo data...")
    output_dir = Path('./reports')
    output_dir.mkdir(parents=True, exist_ok=True)

    data_path = output_dir / 'demo_data.json'
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(demo_data, f, ensure_ascii=False, indent=2)
    print(f"   [OK] Data saved: {data_path.absolute()}")

    # 生成报告
    print("\n[3/3] Generating HTML report...")
    report_html = generate_report(demo_data)

    # 保存报告
    report_path = output_dir / 'index.html'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_html)

    print(f"   [OK] Report saved: {report_path.absolute()}")

    print("\n" + "=" * 60)
    print("[SUCCESS] Test completed!")
    print("=" * 60)
    print(f"\n请在浏览器中打开报告查看效果:")
    print(f"file:///{report_path.absolute()}\n")


if __name__ == '__main__':
    main()
