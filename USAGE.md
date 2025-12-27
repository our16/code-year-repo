# 使用指南

## 快速开始

### 方式一：使用演示数据快速体验

如果你想快速查看报告效果，可以使用内置的演示数据：

```bash
python quick_test.py
```

这将生成一份包含演示数据的报告，保存在 `reports/index.html`，直接在浏览器中打开即可查看。

### 方式二：分析真实Git项目

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

需要的依赖包：
- `gitpython` - Git仓库操作
- `pyyaml` - 配置文件解析
- `jinja2` - HTML模板渲染（可选）
- `openai` 或 `anthropic` - AI文案生成（可选）

#### 2. 配置项目

编辑 `config.yaml` 文件：

```yaml
# 要分析的项目列表
projects:
  - path: "C:/path/to/your/project1"
    name: "项目1名称"
  - path: "C:/path/to/your/project2"
    name: "项目2名称"

# 报告年份
report_year: 2024

# 作者信息（用于筛选提交）
authors:
  - "Your Name"
  - "your.email@example.com"

# 输出目录
output_dir: "./reports"

# LLM配置（可选，用于生成个性化文案）
llm:
  provider: "openai"  # 或 "anthropic"
  model: "gpt-4"
  api_key: "sk-your-api-key"

# 主题颜色
theme:
  primary_color: "#667eea"
  secondary_color: "#764ba2"
  accent_color: "#f093fb"
```

#### 3. 运行分析

```bash
# 基础用法
python main.py

# 不使用LLM（使用预设模板）
python main.py --no-llm

# 导出原始JSON数据
python main.py --export-json
```

## 配置说明

### 项目路径配置

支持多个项目同时分析：

```yaml
projects:
  - path: "/absolute/path/to/project1"  # 使用绝对路径
    name: "Project 1"
  - path: "../relative/path/to/project2"  # 或相对路径
    name: "Project 2"
```

**注意事项：**
- 路径必须是Git仓库的根目录（包含`.git`文件夹）
- Windows系统路径示例：`C:/Users/YourName/project`
- Linux/Mac系统路径示例：`/home/user/project`

### 作者信息配置

支持多种格式匹配提交者：

```yaml
authors:
  - "张三"              # 匹配作者名
  - "zhangsan@example.com"  # 匹配邮箱
  - "Zhang San <zhangsan@example.com>"  # 完整格式
```

工具会匹配包含这些字符串的提交记录。

### LLM配置（可选）

#### 使用OpenAI

```yaml
llm:
  provider: "openai"
  model: "gpt-4"  # 或 "gpt-3.5-turbo"
  api_key: "sk-..."
  base_url: ""  # 可选，自定义API端点
```

#### 使用Anthropic Claude

```yaml
llm:
  provider: "anthropic"
  model: "claude-3-sonnet-20240229"
  api_key: "sk-ant-..."
```

**如果不配置LLM**，工具会使用预设的模板文案，同样可以生成完整的报告。

### 主题配置

自定义报告的配色：

```yaml
theme:
  primary_color: "#667eea"    # 主色调
  secondary_color: "#764ba2"  # 辅助色
  accent_color: "#f093fb"     # 强调色
```

## 报告内容说明

生成的报告包含以下内容：

### 1. 核心指标卡片
- **总提交次数**：全年代码提交次数
- **净增代码行**：新增代码减去删除代码
- **参与项目数**：参与的不同项目数量
- **代码删除数**：删除的代码行数（体现重构贡献）

### 2. AI年度总结
根据你的数据生成的个性化年度文案，包含：
- 数字背后的热忱
- 技术探索之路
- 时间足迹分析
- 精简的艺术（重构贡献）

### 3. 编程语言分布
展示你使用的编程语言及其占比

### 4. 提交热力图
类似GitHub的贡献图，展示全年每天的提交活跃度

### 5. 项目贡献详情
列出各个项目的提交次数、代码增删情况

## 高级功能

### 多作者分析

为多个作者生成对比报告：

```yaml
authors:
  - "Alice"
  - "Bob"
```

### 自定义时间范围

在`config.yaml`中添加：

```yaml
date_range:
  start: "2024-01-01"
  end: "2024-12-31"
```

### 导出原始数据

```bash
python main.py --export-json
```

会生成 `data.json` 文件，包含所有采集的原始数据。

## 常见问题

### Q: 提示"无法打开Git仓库"

**A:** 检查以下几点：
1. 路径是否正确
2. 路径是否指向Git仓库根目录
3. 是否有权限访问该目录

### Q: 找不到提交记录

**A:** 检查：
1. `authors`配置是否正确
2. Git提交的作者名/邮箱是否匹配
3. `report_year`是否正确

### Q: LLM调用失败

**A:**
1. 检查API密钥是否正确
2. 检查网络连接
3. 使用 `--no-llm` 参数跳过LLM

### Q: 报告无法显示中文

**A:** 确保HTML文件以UTF-8编码保存，报告生成时已自动处理。

## 性能优化

### 大型仓库优化

如果仓库很大，可以：
1. 使用浅克隆：`git clone --depth 1`
2. 分批分析项目
3. 限制分析的时间范围

### 内存优化

对于大量提交：
- 增加系统内存
- 分开分析不同项目
- 导出JSON后自定义处理

## 报告分享

生成的HTML报告是完全独立的，可以：
- 直接在浏览器中打开
- 发送给他人
- 部署到Web服务器
- 转换为PDF分享

## 示例配置

### 个人开发者

```yaml
projects:
  - path: "~/projects/my-app"
    name: "个人项目"

authors:
  - "John Doe"

report_year: 2024
```

### 团队项目

```yaml
projects:
  - path: "/company/project-a"
    name: "Project A"
  - path: "/company/project-b"
    name: "Project B"

authors:
  - "Alice"
  - "Bob"

report_year: 2024

llm:
  provider: "openai"
  model: "gpt-4"
  api_key: "sk-..."
```

## 下一步

- 查看生成的报告：`reports/index.html`
- 调整配置参数重新生成
- 自定义HTML模板（`templates/report.html`）
- 扩展数据采集维度（修改`src/`下的模块）

## 技术支持

如有问题，请查看：
- GitHub Issues
- 项目文档：`README.md`
- 示例配置：`config.yaml`
