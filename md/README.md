# 代码年度报告生成器

一个用于生成团队和个人代码年度报告的工具，支持从Git仓库中提取数据并生成精美的可视化报告。

## ✨ 特性

- 📊 自动分析Git仓库数据
- 👥 支持多作者报告生成
- 🎨 精美的可视化展示（类似QQ音乐年度报告）
- 🤖 支持AI生成个性化文案
- 🔗 作者名字映射功能
- 📈 生成进度实时显示
- 💻 纯静态文件+API架构

## 📁 项目结构

```
.
├── start_server.py             # 主程序入口 - 启动Web服务
├── config/                     # 配置文件目录
│   ├── config.yaml            # 主配置文件
│   ├── config.example.yaml    # 配置文件示例
│   ├── author_mapping.yaml    # 作者映射配置
│   └── author_mapping.example.yaml  # 作者映射示例
├── src/                        # Python源代码目录
│   ├── git_collector.py       # Git数据采集
│   ├── data_analyzer.py       # 数据分析
│   ├── llm_client.py          # LLM客户端
│   ├── config_loader.py       # 配置加载
│   ├── server.py              # Web服务器
│   └── report_generator.py    # 报告生成（已废弃）
├── static/                     # 静态资源
│   ├── overview.html          # 总览页面
│   ├── css/
│   │   └── overview.css       # 样式文件
│   └── js/
│       └── overview.js        # JavaScript
├── templates/                  # HTML模板
│   ├── report.html            # 标准报告模板
│   └── report_story.html      # 逐页展示模板（推荐）
└── reports/                    # 生成的报告目录
    ├── report_index.json      # 报告索引
    └── *.json                 # 作者报告数据
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install pyyaml jinja2
```

### 2. 配置文件

复制示例配置并根据实际情况修改：

```bash
cp config/config.example.yaml config/config.yaml
cp config/author_mapping.example.yaml config/author_mapping.yaml
```

编辑 `config/config.yaml`:

```yaml
projects:
  - path: "F:/project/your-project"
    name: "your-project"

report_year: 2025

# 留空表示包含所有作者
authors:

# LLM配置（可选）
llm:
  provider: "openai"
  model: "gpt-4"
  api_key: "your-api-key-here"
```

编辑 `config/author_mapping.yaml`（可选）:

```yaml
# 统一不同格式的作者名字
"Monge" : "Monge(中文名) <monge@example.com>"
"monge" : "Monge(中文名) <monge@example.com>"
```

### 3. 启动Web服务

```bash
python start_server.py
```

或指定端口：

```bash
python start_server.py --port 8080
```

### 4. 访问报告

在浏览器中打开：
- 本地访问：`http://localhost:8000`
- 网络访问：`http://your-ip:8000`

## 📊 数据流程

```
Git仓库 → src/server.py → JSON数据 → Web界面
          (数据采集+API服务)
```

### start_server.py 功能

- 主程序入口
- 启动Web服务器
- 可以通过Web UI触发数据生成

### src/server.py 功能

- 提供HTTP服务
- API接口：
  - `GET /api/authors` - 获取作者列表
  - `GET /api/author/<id>` - 获取作者数据
  - `GET /api/progress` - 获取生成进度
  - `POST /api/generate` - 生成报告数据
- 渲染HTML报告页面
- 提供静态资源服务

## 🎨 UI特性

### 总览页面

- 显示所有贡献者
- 搜索功能
- 进度条显示（如果正在生成）
- 卡片动画效果

### 个人报告（两种模板）

1. **标准模板** (`report.html`)
   - 单页展示所有数据
   - 热力图、图表等可视化

2. **故事模板** (`report_story.html`) - 推荐
   - 逐页展示效果
   - 类似QQ音乐年度报告
   - 滚动动画
   - 章节导航

## 🔧 高级配置

### 作者名字映射

解决同一个作者有多个名字的问题：

```yaml
# config/author_mapping.yaml
"John Doe" : "John Doe <john@example.com>"
"john.doe@example.com" : "John Doe <john@example.com>"
"J. Doe" : "John Doe <john@example.com>"
```

支持多种匹配方式：
- 完全匹配：`"Name <email>"`
- 仅名字：`"Name"`
- 仅邮箱：`"email@example.com"`

### LLM文案生成

在 `config/config.yaml` 中配置：

```yaml
llm:
  provider: "openai"  # 或 "anthropic"
  model: "gpt-4"
  api_key: "sk-..."
  base_url: "https://api.openai.com/v1"  # 可选
```

跳过LLM：

```bash
python main.py --no-llm
```

## 📦 生成的文件

运行 `python main.py` 后，在 `reports/` 目录生成：

```
reports/
├── report_index.json              # 索引文件
├── AuthorName_2025.json          # 作者报告数据
├── AuthorName2_2025.json
└── ...
```

JSON文件结构：

```json
{
  "meta": {
    "author": "作者名",
    "email": "email@example.com",
    "author_id": "作者ID",
    "year": 2025,
    "generated_at": "2025-12-28T..."
  },
  "summary": {
    "total_commits": 1000,
    "net_lines": 50000,
    ...
  },
  "languages": {...},
  "projects": [...],
  "ai_text": "AI生成的文案...",
  "theme": {...}
}
```

## 🎯 使用场景

1. **团队年度总结**
   - 展示团队整体贡献
   - 个人成就展示

2. **个人技术回顾**
   - 查看自己的代码提交
   - 分析编程语言使用
   - 回顾项目参与情况

3. **技术团队建设**
   - 增强团队凝聚力
   - 技术成长可视化

## 📝 注意事项

- `.gitignore` 已配置，不会提交配置文件和生成的报告
- `novels/` 目录是小说内容，禁止分析和修改
- 所有Python代码在 `src/` 目录
- HTML/JS/CSS 在 `static/` 和 `templates/` 目录

## 🔍 故障排查

### 问题：找不到Git仓库

检查 `config/config.yaml` 中的路径是否正确。

### 问题：LLM调用失败

- 检查API key是否正确
- 检查网络连接
- 使用 `--no-llm` 跳过LLM

### 问题：作者名字不统一

配置 `config/author_mapping.yaml` 统一名字。

## 📄 许可证

MIT License
