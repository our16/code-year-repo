#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码年度报告生成器 - 主程序入口
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

from src.git_collector import GitDataCollector
from src.data_analyzer import DataAnalyzer
from src.report_generator import ReportGenerator
from src.config_loader import ConfigLoader


def generate_overview_html(reports: list, config: dict) -> str:
    """生成总览报告HTML"""
    theme = config.get('theme', {})
    year = config.get('report_year', 2024)

    primary_color = theme.get('primary_color', '#667eea')
    secondary_color = theme.get('secondary_color', '#764ba2')
    accent_color = theme.get('accent_color', '#f093fb')

    total_commits = sum(r['commits'] for r in reports)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>团队代码年度报告 {year} - 总览</title>
    <style>
        :root {{
            --primary-color: {primary_color};
            --secondary-color: {secondary_color};
            --accent-color: {accent_color};
            --bg-color: #0f0f1e;
            --card-bg: rgba(255, 255, 255, 0.05);
            --text-primary: #ffffff;
            --text-secondary: #a0a0b0;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 60px 20px;
        }}

        .header {{
            text-align: center;
            padding: 80px 20px;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border-radius: 20px;
            margin-bottom: 60px;
        }}

        .header h1 {{
            font-size: 3em;
            margin-bottom: 20px;
        }}

        .header .subtitle {{
            font-size: 1.3em;
            opacity: 0.9;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 60px;
        }}

        .stat-card {{
            background: var(--card-bg);
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}

        .stat-card .label {{
            color: var(--text-secondary);
        }}

        .reports-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 30px;
        }}

        .report-card {{
            background: var(--card-bg);
            border-radius: 15px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s, box-shadow 0.3s;
            text-decoration: none;
            color: inherit;
            display: block;
        }}

        .report-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        }}

        .report-card h3 {{
            font-size: 1.5em;
            margin-bottom: 15px;
            color: var(--primary-color);
        }}

        .report-card .stats {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}

        .report-card .stat {{
            display: flex;
            justify-content: space-between;
            color: var(--text-secondary);
        }}

        .report-card .stat .value {{
            color: var(--text-primary);
            font-weight: bold;
        }}

        .report-card .view-btn {{
            margin-top: 20px;
            padding: 10px 20px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border-radius: 10px;
            text-align: center;
            font-weight: bold;
        }}

        .footer {{
            text-align: center;
            padding: 40px 20px;
            color: var(--text-secondary);
            margin-top: 60px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>团队代码年度报告 {year}</h1>
            <div class="subtitle">总览</div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="value">{len(reports)}</div>
                <div class="label">贡献者</div>
            </div>
            <div class="stat-card">
                <div class="value">{total_commits}</div>
                <div class="label">总提交次数</div>
            </div>
        </div>

        <h2 style="margin-bottom: 30px; font-size: 2em;">个人报告</h2>

        <div class="reports-grid">
"""

    for report in reports:
        html += f"""
            <a href="{report['path'].name}" class="report-card">
                <h3>{report['author']}</h3>
                <div class="stats">
                    <div class="stat">
                        <span>提交次数</span>
                        <span class="value">{report['commits']}</span>
                    </div>
                </div>
                <div class="view-btn">查看报告 →</div>
            </a>
"""

    html += f"""
        </div>

        <div class="footer">
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    return html


def load_config(config_path: str) -> dict:
    """加载配置文件"""
    if not os.path.exists(config_path):
        print(f"错误: 配置文件 {config_path} 不存在")
        sys.exit(1)

    loader = ConfigLoader(config_path)
    return loader.load()


def main():
    parser = argparse.ArgumentParser(description='代码年度报告生成器')
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='配置文件路径 (默认: config.yaml)'
    )
    parser.add_argument(
        '--export-json',
        action='store_true',
        help='导出原始数据为JSON格式'
    )
    parser.add_argument(
        '--no-llm',
        action='store_true',
        help='不使用LLM生成文案'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("代码年度报告生成器")
    print("=" * 60)

    # 1. 加载配置
    print(f"\n[1/5] 加载配置文件: {args.config}")
    config = load_config(args.config)
    print(f"   - 分析年份: {config.get('report_year', 2024)}")
    print(f"   - 项目数量: {len(config.get('projects', []))}")

    authors = config.get('authors') or []
    print(f"   - 作者模式: {'所有作者' if not authors else f'指定{len(authors)}个作者'}")

    # 2. 采集Git数据（采集所有作者的数据）
    print("\n[2/6] 采集Git数据...")
    # 临时设置authors为空，采集所有作者的数据
    collector_config = config.copy()
    collector_config['authors'] = []  # 采集所有作者
    collector = GitDataCollector(collector_config)

    all_data = []
    all_authors = set()  # 收集所有作者

    for project in config.get('projects', []):
        print(f"\n   扫描项目: {project['name']}")
        print(f"   路径: {project['path']}")

        try:
            project_data = collector.collect_project(project)
            all_data.append(project_data)

            # 收集所有作者
            for commit in project_data.get('commits', []):
                author_info = f"{commit['author']} <{commit['email']}>"
                all_authors.add(author_info)

            print(f"   [OK] 完成: 找到 {len(project_data.get('commits', []))} 条提交记录")
        except Exception as e:
            print(f"   [FAIL] 失败: {str(e)}")
            continue

    if not all_data:
        print("\n错误: 未能收集到任何数据，请检查配置")
        sys.exit(1)

    print(f"\n   发现 {len(all_authors)} 位作者:")

    # 3. 按作者分组数据
    print("\n[3/6] 按作者分组数据...")

    # 为每个作者创建数据分组
    author_data_map = {}
    for author_info in all_authors:
        author_name = author_info.split('<')[0].strip()
        author_email = author_info.split('<')[1].replace('>', '').strip() if '<' in author_info else ''

        # 筛选该作者的提交
        author_projects = []
        for project_data in all_data:
            author_commits = [
                commit for commit in project_data.get('commits', [])
                if commit['author'] == author_name and commit['email'] == author_email
            ]

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
            author_data_map[author_info] = author_projects
            print(f"   - {author_name}: {sum(p['total_commits'] for p in author_projects)} 次提交")

    # 如果配置中指定了authors，则只生成这些作者的报告
    target_authors = config.get('authors', [])
    if target_authors:
        # 筛选指定的作者
        filtered_data_map = {}
        for author_info in author_data_map:
            author_name = author_info.split('<')[0].strip()
            author_email = author_info.split('<')[1].replace('>', '').strip() if '<' in author_info else ''

            # 检查是否匹配指定的作者
            for target in target_authors:
                target_lower = target.lower()
                if target_lower in author_name.lower() or target_lower in author_email.lower():
                    filtered_data_map[author_info] = author_data_map[author_info]
                    break

        author_data_map = filtered_data_map
        if not author_data_map:
            print("\n错误: 没有找到匹配指定作者的提交记录")
            sys.exit(1)
        print(f"\n   筛选后生成 {len(author_data_map)} 位作者的报告")

    # 4. 为每个作者生成报告
    print("\n[4/6] 生成报告...")
    use_llm = not args.no_llm and config.get('llm', {}).get('api_key')
    if use_llm:
        print("   使用LLM生成个性化文案")
    else:
        print("   使用预设模板生成文案")

    generator = ReportGenerator(config, use_llm=use_llm)
    analyzer = DataAnalyzer(config)

    output_dir = Path(config.get('output_dir', './reports'))
    output_dir.mkdir(parents=True, exist_ok=True)

    # 5. 分析每个作者的数据并生成报告
    print("\n[5/6] 分析数据并生成报告...")

    generated_reports = []

    for idx, (author_info, author_projects) in enumerate(author_data_map.items(), 1):
        author_name = author_info.split('<')[0].strip()
        author_email = author_info.split('<')[1].replace('>', '').strip() if '<' in author_info else ''

        print(f"\n   [{idx}/{len(author_data_map)}] 分析作者: {author_name}")

        # 分析该作者的数据
        analyzed_data = analyzer.analyze(author_projects)

        print(f"      - 总提交次数: {analyzed_data['summary']['total_commits']}")
        print(f"      - 净增代码行: {analyzed_data['summary']['net_lines']}")
        print(f"      - 参与项目数: {len(analyzed_data['projects'])}")

        # 生成报告
        report_html = generator.generate(analyzed_data)

        # 生成文件名（安全的文件名）
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in author_name)
        report_filename = f"{safe_name}_{config.get('report_year', 2024)}.html"
        report_path = output_dir / report_filename

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_html)

        generated_reports.append({
            'author': author_name,
            'email': author_email,
            'path': report_path,
            'commits': analyzed_data['summary']['total_commits']
        })

        print(f"      [OK] 报告已生成: {report_filename}")

    # 6. 生成总览报告
    print("\n[6/6] 生成总览报告...")

    # 创建总览HTML
    overview_html = generate_overview_html(generated_reports, config)

    overview_path = output_dir / 'index.html'
    with open(overview_path, 'w', encoding='utf-8') as f:
        f.write(overview_html)

    print(f"   [OK] 总览报告: index.html")

    # 完成
    print("\n" + "=" * 60)
    print("[SUCCESS] 报告生成完成!")
    print("=" * 60)
    print(f"\n生成了 {len(generated_reports)} 个个人报告和 1 个总览报告")
    print(f"\n报告目录: {output_dir.absolute()}")
    print(f"\n文件列表:")
    print(f"  - index.html (总览报告)")
    for report in generated_reports:
        print(f"  - {report['path'].name} ({report['author']})")

    print(f"\n请在浏览器中打开 index.html 查看总览报告\n")


if __name__ == '__main__':
    main()
