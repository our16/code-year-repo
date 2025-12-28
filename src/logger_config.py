#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志配置模块
"""

import logging
import sys
from pathlib import Path


def setup_logger(name: str = 'code-year-report', level=logging.INFO):
    """
    配置全局日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 创建控制台handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)

    # 创建格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # 添加handler到日志记录器
    logger.addHandler(console_handler)

    # 测试日志输出
    logger.info("Logger initialized")

    return logger


def get_logger(name: str = None):
    """获取日志记录器"""
    # 确保全局logger已初始化
    global logger
    if not logger.handlers:
        setup_logger()

    if name:
        # 返回命名logger或子logger
        child_logger = logging.getLogger(name)
        # 确保子logger也有handler（继承父logger）
        if not child_logger.handlers:
            child_logger.parent = logger
        child_logger.setLevel(logger.level)
        return child_logger
    return logger


# 初始化全局日志记录器
logger = setup_logger()
