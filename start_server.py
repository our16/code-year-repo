#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web服务器启动脚本
"""

import sys
import os
from pathlib import Path

# 获取项目根目录并切换到该目录
project_root = Path(__file__).parent.absolute()
os.chdir(project_root)

# 添加src目录到Python路径
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

# 初始化logger（必须在导入server之前）
from src.logger_config import setup_logger
setup_logger()
logger = setup_logger()

from src.server import start_server

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='报告Web服务器')
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='端口号 (默认: 8000)'
    )
    parser.add_argument(
        '--dir',
        default='./reports',
        help='报告目录 (默认: ./reports)'
    )

    args = parser.parse_args()

    logger.info("启动Web服务器")
    start_server(port=args.port, reports_dir=args.dir)
