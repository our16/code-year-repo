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
            # 使用 OpenAI-compatible API（支持所有兼容 OpenAI 协议的服务）
            return self._generate_with_openai_compatible(data)
        except Exception as e:
            print(f"LLM生成失败，使用默认文案: {str(e)}")
            return self._get_default_text(data)

    def _generate_with_openai_compatible(self, data: Dict[str, Any]) -> str:
        """使用 OpenAI-compatible API 生成文案（支持本地LLM服务）"""
        try:
            from openai import OpenAI

            # 创建客户端，支持自定义 base_url
            client_kwargs = {'api_key': self.api_key}
            if self.base_url:
                # 确保base_url包含/v1路径
                base_url = self.base_url.rstrip('/')
                if not base_url.endswith('/v1'):
                    base_url = f"{base_url}/v1"
                client_kwargs['base_url'] = base_url

            print(f"client_kwargs:{client_kwargs}")
            client = OpenAI(**client_kwargs)

            prompt = self._build_prompt(data)

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位专业的技术写作专家，擅长用温暖、富有感染力的语言描述程序员的工作成果。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,
                max_tokens=2000,
            )

            return response.choices[0].message.content

        except ImportError:
            raise Exception("请安装 openai 库: pip install openai")
        except Exception as e:
            raise Exception(f"OpenAI-compatible API 调用失败: {str(e)}")

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

        # 获取当前时间
        from datetime import datetime
        current_date = datetime.now().strftime('%Y年%m月%d日')

        prompt = f"""
请根据以下代码年度数据，生成一份温暖、富有感染力的年度总结文案。

**当前时间：** {current_date}

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

**输出格式要求：**

必须严格按照以下XML格式输出，每个<graph>标签代表一个独立的指标卡片：

```xml
<graphs>
<graph>
<type>提交次数</type>
<value>{summary.get('total_commits', 0)}</value>
<title>数字中的热忱</title>
<content>这一年，你用{summary.get('total_commits', 0)}次提交在编程的世界里书写了一段传奇。新增{summary.get('total_additions', 0)}行代码，删除{summary.get('total_deletions', 0)}行过往，净增长{summary.get('net_lines', 0)}行的积累——每一行都承载着你的创意与智慧。</content>
</graph>

<graph>
<type>代码行数</type>
<value>{summary.get('net_lines', 0)}</value>
<title>代码长城的筑造</title>
<content>这是你技术成长的巍峨丰碑。{summary.get('total_additions', 0)}行新增的代码，构筑起产品的血肉；而{summary.get('total_deletions', 0)}行的删除，更是你追求优雅与简洁的证明。大规模创造与勇敢舍弃的结合，正是大师级程序员的标志。</content>
</graph>

<graph>
<type>项目数量</type>
<value>{project_count}</value>
<title>技术探索的足迹</title>
<content>在{project_count}个不同项目的广阔天地中纵横驰骋，证明你不仅是深耕某一领域的专家，更是具备全局视野的团队协作者。多点开花，重点突破，这种开发模式让你既能在核心项目上达到足够的深度，又能保持对多个项目的广度视野。</content>
</graph>

<graph>
<type>编程语言</type>
<value>{lang_names[0] if lang_names else '未知'}</value>
<title>技术的武器库</title>
<content>以{lang_names[0] if lang_names else '多种语言'}为主要武器，在编程的世界里探索。你的技术栈，是你探索世界的地图，每一次提交都是对技术边界的勇敢突破。</content>
</graph>

<graph>
<type>高效时段</type>
<value>{time_dist.get('best_period', {}).get('hour', '未知')}</value>
<title>深夜的代码骑士</title>
<content>{time_dist.get('best_period', {}).get('hour', '未知')}是你创作的高峰时段。这个黄金时段的选择，展现了你对技术的热爱——即使在一天中最安静的时刻，你依然选择用代码来创造价值。那些在深夜里敲下的代码，带着特别的温度与诗意。</content>
</graph>

<graph>
<type>重构比例</type>
<value>{code_quality.get('refactor_ratio', 0)}%</value>
<title>精简的艺术</title>
<content>你的重构比例达到{code_quality.get('refactor_ratio', 0)}%，这震撼的数字透露出你作为顶级程序员的核心理念——极致的完美主义。你不满足于"能用就行"，而是执着追求"用得完美"。近四分之一的时间用于重构，说明你不仅在创造价值，更在用心雕琢每一个细节。</content>
</graph>
</graphs>
```

**重要说明：**
1. 必须严格按照上面的XML格式输出
2. 只输出<graphs>...</graphs>部分，不要包含其他文字
3. 每个指标卡片包含type、value、title、content四个字段（不需要icon字段，图标由前端自动匹配）
4. content字段中的文案要温暖、有感染力，避免枯燥的数据罗列
5. title字段要有诗意和感染力
6. type字段的可选值：提交次数、代码行数、项目数量、编程语言、高效时段、重构比例等

现在请根据实际数据，生成上述格式的XML输出：
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
