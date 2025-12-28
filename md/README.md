# 代码年度报告生成器

一个基于Git历史数据的个人年度代码报告生成工具，通过分析Git仓库自动生成精美的年度代码报告。

## 功能特性

- ✨ **智能项目发现**：支持指定目录自动发现Git仓库，或手动指定具体项目
- 👥 **灵活的作者筛选**：可指定特定作者，或包含所有提交者
- 📊 **丰富的数据维度**：提交量、代码行数、语言分布、时间热力图等
- 🤖 **AI驱动的文案**：使用LLM自动生成个性化年度总结
- 🎨 **精美的可视化**：基于HTML+JS的交互式报告
- ⚡ **纯前端展示**：生成的报告无需后端，可直接在浏览器打开

## 快速开始

### 方式1：快速体验（推荐）

无需配置，直接查看演示报告：

```bash
python quick_test.py
# 打开 reports/index.html 查看
```

### 方式2：分析真实项目

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置项目

编辑 `config.yaml` 文件。支持三种配置方式：

**方式A：自动发现目录下的所有Git仓库（最简单）**
```yaml
projects:
  - path: "F:/project"  # 指定项目根目录
    name: "所有项目"    # 自动发现子目录中的Git仓库

authors:                # 留空表示包含所有作者
```

**方式B：指定具体的Git仓库**
```yaml
projects:
  - path: "F:/project/my-repo-1"
    name: "项目1"
  - path: "F:/project/my-repo-2"
    name: "项目2"

authors:
  - "Your Name"
```

**方式C：混合使用**
```yaml
projects:
  - path: "F:/project"          # 自动发现
    name: "自动发现的项目"
  - path: "F:/other-repo"       # 手动指定
    name: "特定仓库"

authors:  # 留空=所有作者，或指定特定作者
```

#### 3. 生成报告

```bash
python main.py
```

系统会自动扫描指定的目录，发现Git仓库并生成报告。

#### 4. 查看报告

在浏览器中打开 `./reports/index.html` 即可查看报告。

## 项目结构

```
code-year-report/
├── main.py                 # 主程序入口
├── config.yaml            # 配置文件
├── requirements.txt       # Python依赖
├── README.md             # 项目说明
├── src/
│   ├── __init__.py
│   ├── git_collector.py  # Git数据采集
│   ├── data_analyzer.py  # 数据分析
│   ├── report_generator.py # 报告生成
│   └── llm_client.py     # LLM客户端
├── templates/
│   └── report.html       # HTML报告模板
└── reports/              # 输出目录
    └── index.html        # 生成的报告
```

## 报告内容

报告包含以下核心指标：

### 基础产出
- 总提交次数
- 新增/删除/净增代码行数
- 平均提交频率

### 代码质量
- 代码异味趋势
- 漏洞修复统计
- 重复率变化

### 代码审查
- MR/PR数量
- 评论次数
- 被采纳的建议数

### 项目参与
- 完成任务数
- 参与项目数量
- 技术栈分布

### 效率与模式
- 提交时间分布热力图
- 高效时段分析
- 重构贡献统计

## 配置说明

### LLM配置（可选）

如果需要使用AI生成个性化文案，配置LLM：

```yaml
llm:
  provider: "openai"  # 或 "anthropic"
  model: "gpt-4"
  api_key: "sk-..."
```

如果不配置LLM，将使用预设模板生成报告。

### 主题定制

可以自定义报告的配色方案：

```yaml
theme:
  primary_color: "#667eea"
  secondary_color: "#764ba2"
  accent_color: "#f093fb"
```

## 高级功能

### 多作者分析

支持为多个作者生成独立或合并报告：

```yaml
authors:
  - "Alice <alice@example.com>"
  - "Bob <bob@example.com>"
```

### 自定义时间范围

```yaml
date_range:
  start: "2024-01-01"
  end: "2024-12-31"
```

### 数据导出

支持导出原始数据为JSON格式：

```bash
python main.py --export-json
```

## 常见问题

**Q: 支持哪些Git平台？**
A: 支持所有Git仓库，包括GitHub、GitLab、Gitee、本地仓库等。

**Q: 如何识别提交者？**
A: 通过配置的authors字段，匹配Git提交的作者名和邮箱。

**Q: 报告可以离线查看吗？**
A: 可以，生成的HTML文件是完全独立的，可以离线打开。

**Q: 数据安全吗？**
A: 所有数据在本地处理，不会上传到任何服务器（LLM调用除外）。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
