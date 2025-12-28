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

        # 计算年度寄语的数据特征标签
        avg_commits_per_month = summary.get('avg_commits_per_month', 0)
        commit_feature = '日均提交' if avg_commits_per_month > 100 else '稳健积累'

        refactor_ratio = code_quality.get('refactor_ratio', 0)
        code_style = '追求完美' if refactor_ratio > 20 else '务实高效'

        best_hour = time_dist.get('best_period', {}).get('hour', 12)
        # 处理best_hour可能是字符串的情况
        try:
            best_hour_int = int(best_hour) if isinstance(best_hour, (int, str)) and str(best_hour).isdigit() else 12
        except:
            best_hour_int = 12
        work_habit = '深夜奋斗' if best_hour_int >= 22 or best_hour_int <= 5 else '高效自律'

        project_scope = '多点开花' if project_count >= 5 else '深耕细作'

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

<graph>
<type>年度寄语</type>
<value>致敬</value>
<title>写给明天的你</title>
<content>请根据以下数据特征，生成一段极具个性化和感染力的年度寄语（50字以内）：

【提交特征】{commit_feature}
【代码风格】{code_style}
【工作习惯】{work_habit}
【项目广度】{project_scope}

要求：
1. 结合上述特征，避免模板化
2. 用诗意的语言，但要具体到TA的特点
3. 可以用"星光不问赶路人"、"代码如诗"等比喻，但不要千篇一律
4. 体现对TA这一年的认可和未来的期许
5. 50字以内，精炼有力</content>
</graph>
</graphs>
```

**重要说明：**
1. 必须严格按照上面的XML格式输出
2. 只输出<graphs>...</graphs>部分，不要包含其他文字
3. 每个指标卡片包含type、value、title、content四个字段（不需要icon字段，图标由前端自动匹配）
4. content字段中的文案要温暖、有感染力，避免枯燥的数据罗列
5. title字段要有诗意和感染力
6. type字段的可选值：提交次数、代码行数、项目数量、编程语言、高效时段、重构比例、年度寄语等
7. **年度寄语卡片**的content必须根据实际数据特征生成，避免固定模板，要做到千人千面

现在请根据实际数据，生成上述格式的XML输出：
"""
        return prompt

    def _get_default_text(self, data: Dict[str, Any]) -> str:
        """获取默认文案"""
        summary = data.get('summary', {})
        languages = data.get('languages', {})
        projects = data.get('projects', [])
        time_dist = data.get('time_distribution', {})
        code_quality = data.get('code_quality', {})

        top_lang = languages.get('top_languages', [])[:3]
        lang_names = [l['name'] for l in top_lang]

        project_count = len(projects)
        top_project = projects[0] if projects else {}

        # 个性化结尾语生成
        ending = self._generate_personalized_ending(summary, time_dist, code_quality, project_count, lang_names)

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

特别值得一提的是，你的 **{code_quality.get('refactor_ratio', 0)}%** 的提交用于重构和优化，这展现了你对代码质量的追求和对系统可持续性的思考。

---

{ending}
"""

        return text

    def _generate_personalized_ending(self, summary, time_dist, code_quality, project_count, lang_names):
        """生成个性化结尾语

        根据用户的数据特征生成定制化的结尾语，避免千篇一律
        """
        avg_commits = summary.get('avg_commits_per_month', 0)
        refactor_ratio = code_quality.get('refactor_ratio', 0)
        best_hour = time_dist.get('best_period', {}).get('hour', 12)
        total_commits = summary.get('total_commits', 0)

        endings = []

        # 高产型开发者
        if avg_commits > 100:
            endings.append([
                f"这一年，你用 **{total_commits}** 次提交诠释了什么叫「极致输出」。星光不问赶路人，你的代码早已铺就通往明天的路。",
                f"**{total_commits}** 次提交，是你写给代码最深情的诗行。时光不负有心人，愿你的每一次敲击键盘，都成为点亮未来的星光。",
                f"以 **{avg_commits:.0f}** 次月均提交的节奏，你在代码的世界里一往无前。星光不问赶路人，时光定不负你这份坚持。"
            ])
        elif avg_commits > 50:
            endings.append([
                f"稳健的 **{total_commits}** 次提交，见证了你一年来的成长与突破。代码如诗，你用坚持续写着属于自己的篇章。",
                f"**{avg_commits:.0f}** 次月均提交，不多不少，恰是你的节奏。愿你在代码的世界里继续从容前行，时光终不负你。"
            ])
        else:
            endings.append([
                f"虽然提交次数只有 **{total_commits}** 次，但每一次都凝聚着你的思考与匠心。代码不在多，在于精——你的每一步都算数。",
                f"**{total_commits}** 次提交，少而精。这一年你用代码书写的故事，或许不喧哗，却足够深刻。时光会记得所有用心的创作。"
            ])

        # 完美主义者
        if refactor_ratio > 25:
            endings[-1].append(
                f"**{refactor_ratio}%** 的重构占比，暴露了你作为「代码艺术家」的本色。你在追求完美的路上孤独前行，但时光终将证明——那些被你精心雕琢的代码，会成为他人仰望的星空。"
            )
        elif refactor_ratio > 15:
            endings[-1].extend([
                f"近 **{int(refactor_ratio)}%** 的时间用于重构，这份对完美的执着让人敬佩。你的代码不只是功能实现，更是艺术品——时光不负匠心。",
                f"在 **{refactor_ratio}%** 重构比例背后，是你对代码质量的极致追求。星光不问赶路人，你的每一行精雕细琢的代码，都在为未来铺路。"
            ])

        # 深夜奋斗者
        if best_hour >= 22 or best_hour <= 5:
            endings[-1].extend([
                f"**深夜 {best_hour}点** 是你的创作高峰，静谧的深夜里，只有你和代码在对话。那些深夜敲下的代码，带着特别的温度——星光不问赶路人，时光终不负夜行者。",
                f"当世界沉睡时，你在 **{best_hour}点** 依然在用代码编织梦想。星光不问赶路人，你的每一份深夜坚持，都将成为照亮前路的灯塔。",
            ])
        elif best_hour >= 19:
            endings[-1].append(
                f"**{best_hour}点** 的黄昏与夜晚，见证了你的奋斗时光。星光不问赶路人，愿你每一个夜晚的代码，都成为通往明天的阶梯。"
            )
        else:
            endings[-1].append(
                f"在 **{best_hour}点** 的高效时段，你展现了自律的工作节奏。星光不问赶路人，愿你的每一步都走得坚定而从容。"
            )

        # 多项目达人
        if project_count >= 5:
            endings[-1].extend([
                f"纵横 **{project_count}** 个项目，你是代码世界的「探索者」。星光不问赶路人，愿你在技术的征途上继续乘风破浪。",
                f"一年参与 **{project_count}** 个项目，你的足迹遍布多个领域。时光不负有心人，愿这份广度成为你独特的优势。",
            ])
        elif project_count >= 3:
            ends = [
                f"在 **{project_count}** 个项目中留下你的代码，既有深度又有广度。星光不问赶路人，愿你在每个项目上都收获成长。",
                f"**{project_count}** 个项目的历练，让你成为更全面的开发者。时光会记得你在每个项目中留下的印记。",
            ]
            if len(endings[-1]) < 3:
                endings[-1].extend(ends)
            else:
                endings[-1].extend(ends[:1])

        # 技术专精者
        if len(lang_names) == 1:
            endings[-1].append(
                f"一年深耕 **{lang_names[0]}**，你在单一领域做到了极致。星光不问赶路人，愿你的专业成为最锋利的武器，劈开所有技术难题。"
            )
        elif len(lang_names) >= 3:
            endings[-1].append(
                f"熟练运用 **{len(lang_names)}** 种语言，你是真正的「技术多面手」。星光不问赶路人，愿你的技术栈成为探索世界的罗盘。"
            )

        # 选择最后一个列表，然后随机选择一句
        import random
        if endings:
            options = endings[-1]
            return random.choice(options)

        # 默认结尾
        defaults = [
            "*星光不问赶路人，时光不负有心人。愿你在代码的世界里继续书写精彩！*",
            "*代码如诗，你是最美的诗人。继续用热爱书写你的故事吧！*",
            "*每一行代码都是你成长的脚印。愿星光常伴，时光不负，继续前行！*",
        ]
        return random.choice(defaults)
