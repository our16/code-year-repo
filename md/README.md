# Code Year Report Generator

团队代码年度报告生成和查看系统

## 快速开始

### 方式一：使用批处理脚本（推荐）

双击 `start.bat` 启动服务器：
- 自动停止占用8000端口的旧进程
- 使用Anaconda Python启动服务器
- 打开浏览器访问 http://localhost:8000

### 方式二：命令行启动

```bash
# 使用Anaconda Python（推荐）
C:\tools\Anaconda3\python.exe start_server.py

# 或指定端口
C:\tools\Anaconda3\python.exe start_server.py --port 8001

# 或指定报告目录
C:\tools\Anaconda3\python.exe start_server.py --dir ./reports
```

### 访问地址

启动后可以通过以下地址访问：
- 本地访问：http://localhost:8000
- 网络访问：http://192.168.3.31:8000

## 功能说明

### Web界面功能

1. **查看总览页面** - 访问根路径显示所有作者的报告列表
2. **生成报告** - 点击"🔄 生成报告"按钮自动生成所有作者的年度报告
3. **查看个人报告** - 点击作者卡片查看详细的年度代码报告
4. **实时进度** - 报告生成过程中显示实时进度条

### API端点

- `GET /api/authors` - 获取所有作者列表
- `GET /api/author/<id>` - 获取特定作者的详细数据
- `GET /api/progress` - 获取报告生成进度
- `POST /api/generate` - 触发报告生成
- `GET /report/<id>` - 查看个人报告页面

## 项目结构

```
code-year-report/
├── start_server.py          # Web服务器启动脚本（唯一根目录Python文件）
├── start.bat                 # Windows批处理启动脚本
├── src/                      # 所有Python源代码
│   ├── server.py            # Web服务器核心逻辑
│   ├── logger_config.py     # 全局日志配置
│   ├── report_generator.py  # 报告生成器
│   ├── git_collector.py     # Git数据采集
│   ├── data_analyzer.py     # 数据分析
│   └── llm_client.py        # LLM集成
├── static/                   # 静态资源
│   ├── overview.html        # 总览页面
│   ├── report.html          # 报告页面模板
│   └── css/, js/            # 样式和脚本
├── templates/                # HTML模板
├── config/                   # 配置文件目录
│   ├── config.yaml          # 主配置（项目路径、年份、API密钥等）
│   ├── author_mapping.yaml  # 作者名称映射
│   └── *.example.yaml       # 配置示例文件
└── reports/                  # 生成的报告目录
    ├── *.json               # 各作者的年度报告（JSON格式）
    └── .progress.json       # 生成进度文件（被系统自动排除）
```

## 配置说明

### 1. 主配置文件 (config/config.yaml)

```yaml
# 报告年份
report_year: 2025

# Git项目列表
projects:
  - path: "F:/project/project1"
    name: "Project 1"
  - path: "F:/project/project2"
    name: "Project 2"

# 可选：LLM配置（用于生成年度总结）
llm:
  provider: "openai"  # 或 "anthropic"
  api_key: "your-api-key"
  model: "gpt-4"

# 可选：作者过滤
authors:
  - "John Doe <john@example.com>"
```

### 2. 作者映射配置 (config/author_mapping.yaml)

将不同的作者名称格式统一为标准格式：

```yaml
"Monge": "Monge(中文名) <monge@example.com>"
"monge": "Monge(中文名) <monge@example.com>"
"monge@example.com": "Monge(中文名) <monge@example.com>"
```

## 工作原理

### 报告数据加载

系统会自动扫描 `reports/*.json` 目录：
1. 读取所有JSON文件（个人报告）
2. 排除系统文件（`.progress.json`、`report_index.json`）
3. 动态构建作者列表和索引

### 报告生成流程

1. 点击"生成报告"按钮
2. 系统扫描配置的Git仓库
3. 收集所有提交记录
4. 按作者分组并应用名称映射
5. 分析代码变更数据（提交次数、代码行数等）
6. 生成每人一份的JSON报告
7. 实时显示生成进度

### 日志输出

所有日志输出到 `stderr`，包括：
- 系统启动日志
- 报告加载日志（每个加载的报告都会显示）
- 报告生成进度
- 错误和警告信息

## 常见问题

### 问题：访问 http://localhost:8000 返回 404

**原因**：旧的服务进程还在运行，端口被占用

**解决**：
1. 双击 `start.bat`（会自动清理旧进程）
2. 或手动运行：
   ```bash
   netstat -ano | findstr :8000
   taskkill /F /PID <进程ID>
   ```

### 问题：日志输出中文乱码

**原因**：Windows控制台编码问题

**影响**：仅影响终端显示，不影响实际功能。系统功能正常，JSON数据和Web页面中文显示正常。

### 问题：生成的报告不显示

**原因**：报告目录为空或没有JSON文件

**解决**：
1. 检查 `config/config.yaml` 中的项目路径是否正确
2. 检查Git仓库是否有提交记录
3. 点击"生成报告"按钮重新生成

## 技术栈

- **后端**：Python 3.13+ (http.server)
- **前端**：原生HTML/CSS/JavaScript
- **数据格式**：JSON
- **版本控制**：Git
- **日志系统**：Python logging (stderr)
- **可选**：LLM集成（OpenAI/Anthropic API）

## 更新日志

### 最新更新 (2025-12-28)

1. **修复数据加载逻辑**
   - 从固定的 `report_index.json` 改为动态扫描所有 `*.json` 文件
   - 自动排除 `.progress.json` 和 `report_index.json`
   - 每个作者一份独立的JSON报告

2. **修复日志输出**
   - 使用 `stderr` 而非 `stdout` 避免缓冲问题
   - 添加报告加载日志
   - 完善错误处理

3. **简化启动流程**
   - 提供 `start.bat` 批处理脚本
   - 自动清理占用端口的旧进程
   - 支持Anaconda Python

## 开发文档

更多技术文档请查看 `md/` 目录：
- `UI交互优化方案.md` - UI优化方案
- `STRUCTURE_FINAL.md` - 项目结构说明
- `SERVER_GUIDE.md` - 服务器开发指南
- `LOGGER_FIX.md` - 日志系统修复说明

## 许可证

内部项目 - 仅供团队使用
