# 404问题修复说明

## 问题描述
访问 http://192.168.3.31:8000/ 返回404错误

## 原因分析
1. 服务器启动时切换到了 `reports/` 目录
2. 导致 `static/overview.html` 的相对路径查找失败

## 修复内容

### 1. src/server.py
- 移除了 `os.chdir(reports_path)` 目录切换
- 修改 `serve_static_file()` 使用项目根目录的绝对路径
- 修改 `render_report_html()` 从项目根目录读取模板

### 2. start_server.py
- 启动时切换到项目根目录
- 确保所有相对路径都基于项目根目录

## 测试方法

```bash
# 重启服务器
python start_server.py

# 访问
http://localhost:8000
http://192.168.3.31:8000
```

## 预期结果
- 根路径 `/` 应该显示总览页面
- `/api/authors` 应该返回作者列表
- `/static/overview.html` 应该正确加载
