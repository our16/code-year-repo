#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 ReportGenerator 的 LLM 集成
"""

import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from report_generator import ReportGenerator

def test_llm_integration():
    """测试LLM集成"""
    print("=" * 70)
    print("测试 ReportGenerator LLM 集成")
    print("=" * 70)

    project_root = Path(__file__).parent
    generator = ReportGenerator(project_root)

    # 检查LLM客户端
    print(f"\n1. 检查配置")
    config = generator.load_config()
    if config:
        llm_config = config.get('llm', {})
        print(f"   - LLM Provider: {llm_config.get('provider', 'N/A')}")
        print(f"   - Model: {llm_config.get('model', 'N/A')}")
        print(f"   - API Key: {llm_config.get('api_key', 'N/A')[:10]}...")
        print(f"   - Base URL: {llm_config.get('base_url', 'N/A')}")

        # 检查是否启用了LLM
        use_llm = llm_config.get('api_key')
        if use_llm:
            print(f"\n2. ✓ LLM已启用，Web服务将调用LLM生成个性化文案")
            print(f"   生成报告时会:")
            print(f"   - 调用LLM生成年度总结文案")
            print(f"   - 保存到报告JSON的ai_text字段")
            print(f"   - 前端展示AI生成的文案")
        else:
            print(f"\n2. ✗ LLM未启用，将使用默认模板")

    print(f"\n" + "=" * 70)
    print(f"测试完成")
    print(f"=" * 70)

if __name__ == '__main__':
    test_llm_integration()
