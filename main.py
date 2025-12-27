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
    print(f"   - 作者数量: {len(config.get('authors', []))}")

    # 2. 采集Git数据
    print("\n[2/5] 采集Git数据...")
    collector = GitDataCollector(config)

    all_data = []
    for project in config.get('projects', []):
        print(f"\n   扫描项目: {project['name']}")
        print(f"   路径: {project['path']}")

        try:
            project_data = collector.collect_project(project)
            all_data.append(project_data)
            print(f"   ✓ 完成: 找到 {len(project_data.get('commits', []))} 条提交记录")
        except Exception as e:
            print(f"   ✗ 失败: {str(e)}")
            continue

    if not all_data:
        print("\n错误: 未能收集到任何数据，请检查配置")
        sys.exit(1)

    # 3. 分析数据
    print("\n[3/5] 分析数据...")
    analyzer = DataAnalyzer(config)
    analyzed_data = analyzer.analyze(all_data)

    print(f"   - 总提交次数: {analyzed_data['summary']['total_commits']}")
    print(f"   - 净增代码行: {analyzed_data['summary']['net_lines']}")
    print(f"   - 参与项目数: {len(analyzed_data['projects'])}")

    # 导出JSON（如果需要）
    if args.export_json:
        json_path = Path(config.get('output_dir', './reports')) / 'data.json'
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(analyzed_data, f, ensure_ascii=False, indent=2)
        print(f"\n   原始数据已导出: {json_path}")

    # 4. 生成报告
    print("\n[4/5] 生成报告...")
    use_llm = not args.no_llm and config.get('llm', {}).get('api_key')
    if use_llm:
        print("   使用LLM生成个性化文案")
    else:
        print("   使用预设模板生成文案")

    generator = ReportGenerator(config, use_llm=use_llm)
    report_html = generator.generate(analyzed_data)

    # 5. 保存报告
    print("\n[5/5] 保存报告...")
    output_dir = Path(config.get('output_dir', './reports'))
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = output_dir / f'index.html'

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_html)

    print("\n" + "=" * 60)
    print("✓ 报告生成完成!")
    print("=" * 60)
    print(f"\n报告路径: {report_path.absolute()}")
    print(f"请在浏览器中打开该文件查看报告\n")


if __name__ == '__main__':
    main()
