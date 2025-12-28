# Web服务器使用指南

## 快速开始

### 1. 生成报告

```bash
python main.py --no-llm
```

这会生成：
- 个人报告（每位作者一个HTML文件）
- 总览报告（index.html）
- 报告索引（report_index.json）

### 2. 启动Web服务

```bash
# 默认端口8000
python server.py

# 或指定端口
python server.py --port 8080
```

### 3. 访问报告

服务器启动后会显示访问地址：

```
============================================================
Web服务器已启动!
============================================================

访问地址:
  本地访问: http://localhost:8000
  网络访问: http://192.168.1.100:8000

报告目录: F:\project\code-year-report\reports

按 Ctrl+C 停止服务器
```

在浏览器中打开显示的地址即可查看报告。

## 功能特性

### 1. 团队总览页面

- 显示所有贡献者
- 统计总提交次数
- 搜索作者功能
- 点击查看个人报告

### 2. 个人报告页面

- 作者专属的统计数据
- 代码贡献详情
- 项目参与情况
- 提交热力图
- 语言分布

### 3. 持久化存储

- 所有报告以HTML文件保存
- report_index.json保存元数据
- 可随时重新启动服务

### 4. 独立链接

每位作者有唯一的报告链接：
```
http://localhost:8000/report/monge
http://localhost:8000/report/张三
```

## 高级用法

### 自定义端口

```bash
python server.py --port 9000
```

### 自定义报告目录

```bash
python server.py --dir /path/to/reports
```

### 网络共享

1. 启动服务器
2. 记下显示的网络IP地址
3. 将地址分享给团队成员
4. 团队成员在浏览器中访问即可

## 数据安全

- 只提供HTTP访问（不支持HTTPS）
- 适合内网使用
- 不建议暴露到公网
- 报告文件是静态的，无后端逻辑

## 故障排查

### 端口被占用

```
OSError: [Errno 48] Address already in use
```

**解决方法：**
- 使用其他端口：`python server.py --port 8001`
- 或关闭占用8000端口的程序

### 报告无法访问

1. 检查报告目录是否正确
2. 查看服务器日志（访问记录）
3. 确认防火墙设置

### 数据显示为0

- 重新生成报告：`python main.py --no-llm`
- 检查Git仓库数据完整性

## 示例场景

### 场景1：团队年度回顾会议

```bash
# 1. 生成报告
python main.py --no-llm

# 2. 启动服务
python server.py --port 8080

# 3. 在会议大屏上打开
# http://192.168.1.100:8080

# 4. 演示团队概况和个人贡献
```

### 场景2：发送个人报告链接

```bash
# 启动服务
python server.py

# 每个人的报告链接格式：
# http://your-server:8000/report/作者名
```

发送给团队成员：
- 张三：`http://192.168.1.100:8000/report/张三`
- 李四：`http://192.168.1.100:8000/report/李四`

### 场景3：持续运行服务

```bash
# 后台运行（Linux/Mac）
nohup python server.py --port 8000 &

# 或使用screen/tmux保持会话
screen -S report-server
python server.py --port 8000
# Ctrl+A+D 退出screen
```

## 性能优化

### 静态文件缓存

服务器使用Python的SimpleHTTPRequestHandler，会自动处理静态文件。

### 并发访问

默认情况下，服务器是单线程的。如需支持更多并发：
1. 使用生产级服务器（如Nginx）
2. 或使用多线程服务器库

## 总结

Web服务器提供：
- ✅ 团队总览
- ✅ 个人报告
- ✅ 独立链接
- ✅ 持久化存储
- ✅ 网络共享

快速命令：
```bash
# 生成报告
python main.py --no-llm

# 启动服务
python server.py

# 访问
# http://localhost:8000
```
