#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试logger配置"""

import sys
from pathlib import Path

# 添加src目录到路径
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from logger_config import setup_logger, get_logger

# 测试logger
logger = setup_logger()
logger.info("测试消息：这是一条info日志")
logger.warning("测试消息：这是一条warning日志")
logger.error("测试消息：这是一条error日志")

# 测试子logger
child_logger = get_logger('test.module')
child_logger.info("子logger测试消息")

print("\n如果看到上面的日志，说明logger配置成功！")
