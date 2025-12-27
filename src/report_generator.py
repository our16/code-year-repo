#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告生成器 - 生成HTML报告
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
from jinja2 import Template

from src.llm_client import LLMClient


class ReportGenerator:
    """报告生成器"""

    def __init__(self, config: Dict[str, Any], use_llm: bool = True):
        self.config = config
        self.use_llm = use_llm
        self.theme = config.get('theme', {})
        self.llm_client = LLMClient(config) if use_llm else None

    def generate(self, data: Dict[str, Any]) -> str:
        """生成HTML报告"""

        # 生成AI文案
        if self.use_llm:
            ai_text = self.llm_client.generate_report_text(data)
        else:
            ai_text = self.llm_client._get_default_text(data)

        # 读取HTML模板
        template_path = Path(__file__).parent.parent / 'templates' / 'report.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # 渲染模板
        template = Template(template_content)
        html = template.render(
            data=data,
            ai_text=ai_text,
            theme=self.theme,
            year=data.get('year', 2024),
        )

        return html


class SimpleReportGenerator:
    """简单报告生成器（不使用Jinja2）"""

    def __init__(self, config: Dict[str, Any], use_llm: bool = True):
        self.config = config
        self.use_llm = use_llm
        self.theme = config.get('theme', {})
        self.llm_client = LLMClient(config) if use_llm else None

    def generate(self, data: Dict[str, Any]) -> str:
        """生成HTML报告"""

        # 生成AI文案
        if self.use_llm:
            ai_text = self.llm_client.generate_report_text(data)
        else:
            ai_text = self.llm_client._get_default_text(data)

        # 读取HTML模板
        template_path = Path(__file__).parent.parent / 'templates' / 'report.html'
        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 简单的模板替换
        html_content = html_content.replace('{{ data_json }}', json.dumps(data, ensure_ascii=False))
        html_content = html_content.replace('{{ ai_text }}', ai_text)
        html_content = html_content.replace('{{ year }}', str(data.get('year', 2024)))

        # 主题颜色
        primary_color = self.theme.get('primary_color', '#667eea')
        secondary_color = self.theme.get('secondary_color', '#764ba2')
        accent_color = self.theme.get('accent_color', '#f093fb')

        html_content = html_content.replace('{{ primary_color }}', primary_color)
        html_content = html_content.replace('{{ secondary_color }}', secondary_color)
        html_content = html_content.replace('{{ accent_color }}', accent_color)

        return html_content
