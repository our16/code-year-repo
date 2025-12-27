# 项目结构说明

```
code-year-report/
├── main.py                 # 主程序入口
├── config.yaml            # 配置文件
├── requirements.txt       # Python依赖
├── README.md             # 项目说明
├── USAGE.md              # 使用指南
├── .gitignore           # Git忽略文件
├── quick_test.py        # 快速测试脚本（无需依赖）
├── test_generator.py    # 完整测试脚本
├── 年报项目.md          # 需求文档
│
├── src/                 # 核心模块
│   ├── __init__.py
│   ├── config_loader.py      # 配置加载器
│   ├── git_collector.py      # Git数据采集器
│   ├── data_analyzer.py      # 数据分析器
│   ├── llm_client.py         # LLM客户端
│   └── report_generator.py   # 报告生成器
│
├── templates/           # HTML模板
│   └── report.html      # 报告模板
│
└── reports/            # 输出目录
    ├── index.html      # 生成的报告
    └── demo_data.json  # 演示数据
```

## 核心模块说明

### 1. main.py - 主程序
程序的入口，负责：
- 解析命令行参数
- 协调各模块工作
- 显示进度信息
- 保存最终报告

**主要流程：**
```
1. 加载配置 (config_loader)
2. 采集Git数据 (git_collector)
3. 分析数据 (data_analyzer)
4. 生成报告 (report_generator)
5. 保存报告文件
```

### 2. src/config_loader.py - 配置加载器
负责加载和验证配置文件。

**功能：**
- 读取YAML配置
- 设置默认值
- 验证配置合法性
- 检查项目路径

**配置项：**
- `projects`: 项目列表
- `authors`: 作者列表
- `report_year`: 报告年份
- `llm`: LLM配置
- `theme`: 主题颜色

### 3. src/git_collector.py - Git数据采集器
从Git仓库采集原始数据。

**采集内容：**
- 提交记录（hash、日期、消息）
- 代码变更（新增/删除行数）
- 文件变更统计
- 编程语言检测
- 分支信息

**核心方法：**
- `collect_project()`: 采集单个项目
- `collect_all()`: 采集所有项目
- `_is_target_author()`: 判断是否目标作者
- `_is_target_year()`: 判断是否目标年份
- `_detect_language()`: 检测编程语言

### 4. src/data_analyzer.py - 数据分析器
对采集的数据进行聚合和分析。

**分析维度：**
- 基础汇总（提交次数、代码行数）
- 时间分布（按月、星期、小时）
- 日历热力图
- 代码质量（重构分析）
- 语言分布
- 项目贡献

**核心方法：**
- `analyze()`: 综合分析
- `_calculate_summary()`: 计算汇总数据
- `_analyze_time_distribution()`: 时间分布分析
- `_analyze_code_quality()`: 代码质量分析
- `_analyze_languages()`: 语言分析

### 5. src/llm_client.py - LLM客户端
使用大语言模型生成个性化文案。

**功能：**
- 支持OpenAI
- 支持Anthropic Claude
- 构建Prompt模板
- 降级到预设模板

**核心方法：**
- `generate_report_text()`: 生成文案
- `_build_prompt()`: 构建Prompt
- `_get_default_text()`: 获取默认文案

### 6. src/report_generator.py - 报告生成器
将数据和文案组合成HTML报告。

**功能：**
- 加载HTML模板
- 注入数据
- 渲染模板
- 生成HTML文件

**核心方法：**
- `generate()`: 生成HTML报告

## HTML模板说明

### templates/report.html
报告的前端模板，包含：

**样式设计：**
- 深色主题
- 渐变色彩
- 响应式布局
- 悬停动效

**主要组件：**
1. **Hero区域**：标题和年份
2. **统计卡片**：核心指标展示
3. **AI文案区**：个性化总结
4. **语言分布**：语言标签云
5. **热力图**：提交活跃度
6. **项目列表**：项目贡献详情

**JavaScript功能：**
- 数据渲染
- 数字格式化
- 动画效果
- 响应式交互

## 数据流程

```
Git仓库
  ↓
git_collector (原始数据)
  ↓
data_analyzer (聚合分析)
  ↓
llm_client (生成文案)
  ↓
report_generator (HTML渲染)
  ↓
最终报告
```

## 数据结构

### 原始提交数据
```json
{
  "hash": "commit_hash",
  "short_hash": "abc12345",
  "date": "2024-01-01T10:00:00",
  "message": "commit message",
  "author": "Author Name",
  "email": "author@example.com",
  "additions": 100,
  "deletions": 50,
  "files_changed": 3
}
```

### 分析结果数据
```json
{
  "year": 2024,
  "summary": {
    "total_commits": 500,
    "net_lines": 10000,
    ...
  },
  "time_distribution": {...},
  "code_quality": {...},
  "languages": {...},
  "projects": [...]
}
```

## 扩展开发

### 添加新的数据指标

1. 在 `git_collector.py` 中采集数据
2. 在 `data_analyzer.py` 中添加分析方法
3. 在 `report.html` 中添加展示组件

### 自定义报告样式

修改 `templates/report.html` 中的CSS变量：

```css
:root {
  --primary-color: #667eea;
  --secondary-color: #764ba2;
  ...
}
```

### 集成新的LLM

在 `src/llm_client.py` 中添加新的provider方法：

```python
def _generate_with_new_provider(self, data):
    # 实现新的LLM调用
    pass
```

## 测试

### 单元测试
```bash
python test_generator.py
```

### 快速测试（无需依赖）
```bash
python quick_test.py
```

## 性能考虑

- **大仓库处理**：使用Git的增量读取
- **内存管理**：分批处理提交记录
- **缓存优化**：可添加缓存层避免重复采集
- **并行处理**：多项目可并行采集

## 安全性

- API密钥通过配置文件管理
- 不上传任何代码内容
- 仅采集Git元数据
- 本地处理，隐私安全
