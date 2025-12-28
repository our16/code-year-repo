#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM客户端 - 生成个性化报告文案
"""

import os
from typing import Dict, Any


class LLMClient:
    """LLM客户端基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('llm', {})
        self.provider = self.config.get('provider', 'openai')
        self.api_key = self.config.get('api_key', '')
        self.model = self.config.get('model', 'gpt-4')
        self.base_url = self.config.get('base_url', '')

    def generate_report_text(self, data: Dict[str, Any]) -> str:
        """生成报告文案"""
        if not self.api_key:
            return self._get_default_text(data)

        try:
            return self._generate_with_anthropic(data)
        except Exception as e:
            print(f"LLM生成失败，使用默认文案: {str(e)}")
            return self._get_default_text(data)

    def _generate_with_anthropic(self, data: Dict[str, Any]) -> str:
        """使用Anthropic生成文案"""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            prompt = self._build_prompt(data)

            response = client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.8,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return response.content[0].text

        except ImportError:
            raise Exception("请安装 anthropic 库: pip install anthropic")
        except Exception as e:
            raise Exception(f"Anthropic调用失败: {str(e)}")

    def _build_prompt(self, data: Dict[str, Any]) -> str:
        """构建LLM提示词"""
        summary = data.get('summary', {})
        languages = data.get('languages', {})
        projects = data.get('projects', [])
        time_dist = data.get('time_distribution', {})
        code_quality = data.get('code_quality', {})

        # 获取主要语言
        top_lang = languages.get('top_languages', [])[:2]
        lang_names = [l['name'] for l in top_lang]

        # 获取主要项目
        top_project = projects[0] if projects else {}
        project_count = len(projects)

        prompt = f"""
请根据以下代码年度数据，生成一份温暖、富有感染力的年度总结文案。文案应该包含以下几个部分，每个部分都要有情感色彩，避免枯燥的数据罗列：

**数据概览：**
- 总提交次数: {summary.get('total_commits', 0)}
- 净增代码行: {summary.get('net_lines', 0)}
- 删除代码行: {summary.get('total_deletions', 0)}
- 新增代码行: {summary.get('total_additions', 0)}
- 主要编程语言: {', '.join(lang_names) if lang_names else '未知'}
- 参与项目数: {project_count}
- 最活跃项目: {top_project.get('name', '未知')} ({top_project.get('commits', 0)} 次提交)
- 平均每月提交: {summary.get('avg_commits_per_month', 0)}
- 高效时段: {time_dist.get('best_period', {}).get('hour', '未知')}
- 重构提交占比: {code_quality.get('refactor_ratio', 0)}%

**要求：**
1. 标题：吸引人的年度报告标题
2. 开篇：温暖的开场白，营造回顾氛围
3. 第一部分：数字背后的热忱（提交量、代码行数）
4. 第二部分：技术的探索之路（语言、项目）
5. 第三部分：时间的足迹（提交习惯、高效时段）
6. 第四部分：精简的艺术（重构贡献）
7. 结语：展望未来的寄语

请用中文撰写，语言要优美、有感染力，避免过于技术化的表达。每个段落之间用空行分隔。
"""
        return prompt

    def _get_default_text(self, data: Dict[str, Any]) -> str:
        """获取默认文案"""
        summary = data.get('summary', {})
        languages = data.get('languages', {})
        projects = data.get('projects', [])

        top_lang = languages.get('top_languages', [])[:3]
        lang_names = [l['name'] for l in top_lang]

        project_count = len(projects)
        top_project = projects[0] if projects else {}

        text = f"""
# 💌 致过去的一年：你的代码，你的诗篇

在冰冷的数字背后，是你一整年的热忱、思考和创造。

## 年初的Flag，是写在晨光里的序章

每一个早起的清晨，每一个静谧的深夜，键盘敲击出的不只是代码，更是你解决问题的决心。那些 **{summary.get('total_commits', 0)}** 次的提交，是你与复杂问题一次次交锋的勋章。新增的 **{summary.get('total_additions', 0)}** 行代码，构筑起产品的血肉；而删除的 **{summary.get('total_deletions', 0)}** 行，更是你追求优雅与简洁的证明——真正的大师，不仅乐于创造，更勇于做减法。

## 你的技术栈，是你探索世界的地图

这一年，你在 **{', '.join(lang_names) if lang_names else '多种技术栈'}** 的世界里探索。参与 **{project_count}** 个不同项目的经历，证明你不仅是深耕某一领域的专家，更是具备全局视野的团队协作者。在 **{top_project.get('name', '核心项目')}** 中的 **{top_project.get('commits', 0)}** 次提交，记录了你在这个项目上的深度投入。

## 提交时间分布，是你奋斗时刻的剪影

热力图上的每一个色块，都是你辛勤付出的坐标。它记录了你为攻克难题的坚守，也记录了你高效工作日的专注流程。找到自己的节奏，比盲目追赶更重要。

## 精简的艺术

特别值得一提的是，你的 **{data.get('code_quality', {}).get('refactor_ratio', 0)}%** 的提交用于重构和优化，这展现了你对代码质量的追求和对系统可持续性的思考。

---

*继续用代码书写你的故事吧！*
"""

        return text
