#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM连接测试 - 独立测试脚本
"""

import sys
import os
import json
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def test_openai_connection():
    """测试OpenAI-compatible API连接"""
    print("=" * 70)
    print("LLM连接测试")
    print("=" * 70)

    # 加载配置
    config_path = Path(__file__).parent / 'config' / 'config.yaml'
    print(f"\n1. 加载配置文件: {config_path}")

    try:
        from src.config_loader import ConfigLoader
        loader = ConfigLoader(str(config_path))
        config = loader.load()
        print(f"   ✓ 配置加载成功")
    except Exception as e:
        print(f"   ✗ 配置加载失败: {e}")
        return

    # 获取LLM配置
    llm_config = config.get('llm', {})
    print(f"\n2. LLM配置:")
    print(f"   - provider: {llm_config.get('provider', 'N/A')}")
    print(f"   - model: {llm_config.get('model', 'N/A')}")
    print(f"   - api_key: {llm_config.get('api_key', 'N/A')[:10]}...")
    print(f"   - base_url: {llm_config.get('base_url', 'N/A')}")

    # 测试导入
    print(f"\n3. 测试依赖库导入")
    try:
        from openai import OpenAI
        print(f"   ✓ openai库导入成功")
    except ImportError as e:
        print(f"   ✗ openai库导入失败: {e}")
        print(f"   请运行: pip install openai")
        return

    # 创建客户端
    print(f"\n4. 创建OpenAI客户端")
    try:
        client_kwargs = {
            'api_key': llm_config.get('api_key', 'sk-not-needed')
        }
        base_url = llm_config.get('base_url', '')
        if base_url:
            client_kwargs['base_url'] = base_url

        print(f"   客户端参数: {json.dumps(client_kwargs, indent=6)}")

        client = OpenAI(**client_kwargs)
        print(f"   ✓ 客户端创建成功")

    except Exception as e:
        print(f"   ✗ 客户端创建失败: {e}")
        print(f"   错误类型: {type(e).__name__}")
        import traceback
        print(f"   详细错误:")
        traceback.print_exc()
        return

    # 测试简单调用
    print(f"\n5. 测试简单聊天完成")
    try:
        print(f"   发送请求...")
        response = client.chat.completions.create(
            model=llm_config.get('model', 'gpt-4'),
            messages=[
                {"role": "user", "content": "Hello, please reply with 'OK'"}
            ],
            max_tokens=50,
            temperature=0.7,
        )

        print(f"   ✓ API调用成功")
        print(f"   - Response ID: {response.id}")
        print(f"   - Model: {response.model}")
        print(f"   - Content: {response.choices[0].message.content}")

    except Exception as e:
        print(f"   ✗ API调用失败: {e}")
        print(f"   错误类型: {type(e).__name__}")
        import traceback
        print(f"   详细错误:")
        traceback.print_exc()

        # 额外诊断
        print(f"\n6. 额外诊断")
        print(f"   检查base_url格式...")
        if base_url:
            print(f"   - 原始base_url: '{base_url}'")
            print(f"   - 是否包含/v1: {'/v1' in base_url}")

            # 测试不同的URL格式
            import urllib.parse
            parsed = urllib.parse.urlparse(base_url)
            print(f"   - 解析结果:")
            print(f"     scheme: {parsed.scheme}")
            print(f"   - netloc: {parsed.netloc}")
            print(f"     path: {parsed.path}")

    # 测试完整的LLMClient
    print(f"\n7. 测试LLMClient类")
    try:
        from src.llm_client import LLMClient

        llm_client = LLMClient(config)
        print(f"   ✓ LLMClient创建成功")

        # 准备测试数据
        test_data = {
            'summary': {
                'total_commits': 100,
                'total_additions': 5000,
                'total_deletions': 2000,
                'net_lines': 3000,
            },
            'languages': {
                'top_languages': [
                    {'name': 'Python', 'percentage': 60},
                    {'name': 'JavaScript', 'percentage': 40}
                ]
            },
            'projects': [
                {'name': 'test-project', 'commits': 100}
            ],
            'time_distribution': {
                'best_period': {'hour': '14:00-15:00'}
            },
            'code_quality': {
                'refactor_ratio': 10
            }
        }

        print(f"   生成测试文案...")
        result = llm_client.generate_report_text(test_data)

        if result and len(result) > 100:
            print(f"   ✓ 文案生成成功")
            print(f"   - 文案长度: {len(result)} 字符")
            print(f"   - 文案预览: {result[:100]}...")
        else:
            print(f"   ✗ 文案生成失败或内容过短")
            print(f"   - 返回内容: {result}")

    except Exception as e:
        print(f"   ✗ LLMClient测试失败: {e}")
        print(f"   错误类型: {type(e).__name__}")
        import traceback
        print(f"   详细错误:")
        traceback.print_exc()

    print(f"\n" + "=" * 70)
    print(f"测试完成")
    print(f"=" * 70)


if __name__ == '__main__':
    test_openai_connection()
