# Logger配置说明

## 已完成的logger更新

### 1. 创建全局logger配置
文件：`src/logger_config.py`

功能：
- 配置全局日志记录器
- 支持日志级别设置
- 统一的日志格式

### 2. 更新server.py
- 导入logger配置
- 所有print替换为logger调用
- 修复subprocess编码问题（encoding='utf-8'）
- 添加详细的日志输出

关键更新：
```python
from logger_config import get_logger
logger = get_logger(__name__)

# 生成报告时的日志
logger.info("收到生成报告请求")
logger.info(f"开始执行生成脚本: {main_script}")
logger.info(f"生成脚本执行完成，返回码: {result.returncode}")
```

### 3. 部分更新generate_reports.py
- 导入logger配置
- 主要步骤已使用logger

## 日志格式

```
YYYY-MM-DD HH:MM:SS - 模块名 - 级别 - 消息
```

例如：
```
2025-12-28 14:00:00 - src.server - INFO - 收到生成报告请求
2025-12-28 14:00:05 - src.generate_reports - INFO - 发现 5 位作者
```

## 日志级别

- DEBUG: 详细信息
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息
- CRITICAL: 严重错误

## 使用示例

```python
from logger_config import get_logger

logger = get_logger(__name__)

logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息", exc_info=True)  # 包含堆栈跟踪
```

## 待完成

generate_reports.py中还有一些print语句需要替换为logger，但不影响核心功能。

已替换的部分：
- 配置加载
- Git数据采集开始
- 作者映射加载

保持print的部分（用于控制台显示）：
- 进度条显示
- 成功/失败信息
