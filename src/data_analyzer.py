#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析器 - 聚合和分析Git数据
"""

import calendar
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Any


class DataAnalyzer:
    """数据分析器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.report_year = config.get('report_year', 2024)

    def analyze(self, projects_data: List[Dict[str, Any]], max_commits: int = None) -> Dict[str, Any]:
        """分析所有项目数据

        Args:
            projects_data: 项目数据列表
            max_commits: 最大提交记录数，用于控制JSON文件大小
        """

        # 聚合数据
        all_commits = []
        language_stats = defaultdict(int)
        project_commits = defaultdict(list)

        for project_data in projects_data:
            project_name = project_data['project_name']
            commits = project_data.get('commits', [])

            # 如果设置了max_commits，只保留最近的提交
            if max_commits and len(commits) > max_commits:
                commits = commits[:max_commits]

            all_commits.extend(commits)
            project_commits[project_name] = commits

            # 聚合语言统计
            for lang, count in project_data.get('language_stats', {}).items():
                language_stats[lang] += count

        # 分析维度
        summary = self._calculate_summary(all_commits)
        time_distribution = self._analyze_time_distribution(all_commits)
        code_quality = self._analyze_code_quality(all_commits)
        language_analysis = self._analyze_languages(language_stats)
        project_analysis = self._analyze_projects(project_commits, language_stats)

        return {
            'year': self.report_year,
            'summary': summary,
            'time_distribution': time_distribution,
            'code_quality': code_quality,
            'languages': language_analysis,
            'projects': project_analysis,
            'raw_data': {
                'total_commits': len(all_commits),
                'language_stats': dict(language_stats),
            }
        }

    def _calculate_summary(self, commits: List[Dict]) -> Dict[str, Any]:
        """计算基础汇总数据"""
        if not commits:
            return {
                'total_commits': 0,
                'total_additions': 0,
                'total_deletions': 0,
                'net_lines': 0,
                'files_changed': 0,
                'avg_commits_per_month': 0,
                'most_active_day': None,
            }

        total_commits = len(commits)
        total_additions = sum(c['additions'] for c in commits)
        total_deletions = sum(c['deletions'] for c in commits)
        net_lines = total_additions - total_deletions
        files_changed = sum(c['files_changed'] for c in commits)

        # 计算平均每月提交数
        month_count = len(set(c['date'][:7] for c in commits))
        avg_commits_per_month = total_commits / month_count if month_count > 0 else 0

        # 找出最活跃的一天
        commit_by_day = Counter(c['date'][:10] for c in commits)
        most_active_day = commit_by_day.most_common(1)[0][0] if commit_by_day else None

        return {
            'total_commits': total_commits,
            'total_additions': total_additions,
            'total_deletions': total_deletions,
            'net_lines': net_lines,
            'files_changed': files_changed,
            'avg_commits_per_month': round(avg_commits_per_month, 1),
            'most_active_day': most_active_day,
        }

    def _analyze_time_distribution(self, commits: List[Dict]) -> Dict[str, Any]:
        """分析时间分布"""
        # 按月统计
        monthly_commits = defaultdict(int)
        for commit in commits:
            month = commit['date'][:7]  # YYYY-MM
            monthly_commits[month] += 1

        # 按星期统计
        weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        weekday_commits = defaultdict(int)
        for commit in commits:
            dt = datetime.fromisoformat(commit['date'])
            weekday_commits[dt.weekday()] += 1

        # 按小时统计
        hourly_commits = defaultdict(int)
        for commit in commits:
            dt = datetime.fromisoformat(commit['date'])
            hourly_commits[dt.hour] += 1

        # 生成日历热力图数据
        calendar_heatmap = self._generate_calendar_heatmap(commits)

        # 找出最高效时段
        best_hour = max(hourly_commits.items(), key=lambda x: x[1])[0] if hourly_commits else 0
        best_weekday = max(weekday_commits.items(), key=lambda x: x[1])[0] if weekday_commits else 0

        return {
            'monthly': dict(monthly_commits),
            'weekday': {weekday_names[i]: weekday_commits[i] for i in range(7)},
            'hourly': dict(hourly_commits),
            'calendar_heatmap': calendar_heatmap,
            'best_period': {
                'hour': f"{best_hour}:00-{best_hour+1}:00",
                'weekday': weekday_names[best_weekday],
            }
        }

    def _generate_calendar_heatmap(self, commits: List[Dict]) -> List[Dict]:
        """生成完整的365天日历热力图数据"""
        from datetime import date, timedelta

        # 按日期统计提交信息
        daily_stats = defaultdict(lambda: {
            'count': 0,
            'additions': 0,
            'deletions': 0,
            'latest_time': None
        })

        for commit in commits:
            date_str = commit['date'][:10]  # YYYY-MM-DD
            time_str = commit['date'][11:19]  # HH:MM:SS

            daily_stats[date_str]['count'] += 1
            daily_stats[date_str]['additions'] += commit.get('additions', 0)
            daily_stats[date_str]['deletions'] += commit.get('deletions', 0)

            # 更新最晚提交时间（晚6点-次日早6点算夜间提交）
            if daily_stats[date_str]['latest_time'] is None or time_str > daily_stats[date_str]['latest_time']:
                daily_stats[date_str]['latest_time'] = time_str

        # 生成完整的365天数据
        start_date = date(self.report_year, 1, 1)
        end_date = date(self.report_year, 12, 31)

        result = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            stats = daily_stats.get(date_str, {'count': 0, 'additions': 0, 'deletions': 0, 'latest_time': None})
            count = stats['count']

            result.append({
                'date': date_str,
                'count': count,
                'additions': stats['additions'],
                'deletions': stats['deletions'],
                'latest_time': stats['latest_time'],
                'level': self._get_heatmap_level(count)
            })
            current_date += timedelta(days=1)

        return result

    def _get_heatmap_level(self, count: int) -> int:
        """计算热力图等级 (0-4)"""
        if count == 0:
            return 0
        elif count <= 2:
            return 1
        elif count <= 5:
            return 2
        elif count <= 10:
            return 3
        else:
            return 4

    def _analyze_code_quality(self, commits: List[Dict]) -> Dict[str, Any]:
        """分析代码质量指标"""
        # 重构贡献：删除代码行数较多的提交
        refactor_commits = [c for c in commits if c['deletions'] > c['additions'] * 1.5]

        # 最大重构
        top_refactor = sorted(
            [c for c in commits if c['deletions'] > c['additions']],
            key=lambda x: x['deletions'] - x['additions'],
            reverse=True
        )[:5]

        # 平均每次提交的代码变更
        avg_additions = sum(c['additions'] for c in commits) / len(commits) if commits else 0
        avg_deletions = sum(c['deletions'] for c in commits) / len(commits) if commits else 0

        return {
            'refactor_commits': len(refactor_commits),
            'refactor_ratio': round(len(refactor_commits) / len(commits) * 100, 1) if commits else 0,
            'top_refactors': [
                {
                    'date': c['date'][:10],
                    'message': c['message'][:50],
                    'net_lines': c['deletions'] - c['additions']
                }
                for c in top_refactor
            ],
            'avg_additions_per_commit': round(avg_additions, 1),
            'avg_deletions_per_commit': round(avg_deletions, 1),
        }

    def _analyze_languages(self, language_stats: Dict[str, int]) -> Dict[str, Any]:
        """分析编程语言使用情况"""
        if not language_stats:
            return {
                'total': 0,
                'top_languages': [],
                'distribution': {},
            }

        total = sum(language_stats.values())
        sorted_languages = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)

        # 取前5种语言
        top_languages = [
            {
                'name': lang,
                'count': count,
                'percentage': round(count / total * 100, 1)
            }
            for lang, count in sorted_languages[:5]
        ]

        return {
            'total': total,
            'top_languages': top_languages,
            'distribution': {lang: round(count / total * 100, 1)
                           for lang, count in sorted_languages},
        }

    def _analyze_projects(self, project_commits: Dict[str, List[Dict]],
                         language_stats: Dict[str, int]) -> List[Dict]:
        """分析项目参与情况"""
        projects = []

        for project_name, commits in project_commits.items():
            if not commits:
                continue

            # 项目语言分布
            project_languages = defaultdict(int)
            for commit in commits:
                # 简化：假设每个项目有一种主要语言
                pass

            total_additions = sum(c['additions'] for c in commits)
            total_deletions = sum(c['deletions'] for c in commits)

            projects.append({
                'name': project_name,
                'commits': len(commits),
                'additions': total_additions,
                'deletions': total_deletions,
                'net_lines': total_additions - total_deletions,
            })

        # 按提交数排序
        projects.sort(key=lambda x: x['commits'], reverse=True)

        return projects
