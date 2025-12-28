# Server.py 重构完成

## 完成的优化

### 1. 生成逻辑嵌入
**修改前**：调用外部脚本 `src/generate_reports.py`
```python
result = subprocess.run([sys.executable, str(main_script)], ...)
```

**修改后**：直接使用 `ReportGenerator` 类
```python
from report_generator import ReportGenerator

generator = ReportGenerator(project_root)
success = generator.generate_all(progress_callback)
```

### 2. 移除HTML内嵌内容
**修改前**：在Python代码中直接写HTML
```python
html = f"""<!DOCTYPE html>
<html>
...
</html>"""
```

**修改后**：使用静态HTML文件
- 创建 `static/no-data.html`
- 使用302重定向：`self.send_header('Location', '/static/no-data.html?author=...')`

### 3. 新增ReportGenerator类
文件：`src/report_generator.py`

功能：
- 封装所有报告生成逻辑
- 支持进度回调
- 使用全局logger
- 直接读取Git数据并生成JSON

### 4. 日志系统
**server.py中的关键日志**：
- `logger.info("收到生成报告请求")`
- `logger.info(f"进度: {data['current']} - {data['percentage']}%")`
- `logger.info(f"生成完成: {'成功' if success else '失败'}")`

**report_generator.py中的日志**：
- 配置加载日志
- Git扫描日志
- 报告生成日志

## 优势

1. **更简洁**：不需要subprocess调用
2. **更安全**：没有命令注入风险
3. **更易维护**：所有HTML在templates/static目录
4. **更好的日志**：统一的logger配置
5. **更快**：不需要启动新的Python进程

## 使用方式

### 生成报告
1. 访问 `http://localhost:8000`
2. 点击"🔄 生成报告"按钮
3. 查看进度条
4. 自动刷新查看结果

### 查看日志
```bash
# 启动时会看到详细日志
python start_server.py

# 生成时会看到：
# - 收到生成报告请求
# - 扫描项目: xxx
# - 发现 X 位作者
# - [1/N] 生成报告: xxx
# - 生成完成: 成功
```

## 文件变更

**新增**：
- `src/logger_config.py` - 全局logger配置
- `src/report_generator.py` - 报告生成器类
- `static/no-data.html` - 无数据提示页面

**修改**：
- `src/server.py` - 嵌入生成逻辑，移除HTML

**保持不变**：
- `src/generate_reports.py` - 独立脚本仍可用
- `templates/*.html` - 模板文件
