# 快速开始 - 代码年度报告生成器

## 一分钟快速体验

### 方式1：查看演示报告（推荐）

我们已经为你生成了一份演示报告！

```bash
# 直接打开报告
cd reports
start index.html  # Windows
# 或
open index.html   # Mac/Linux
```

**演示报告包含：**
- 648次提交记录
- 66,912行净增代码
- 5个项目
- 多种编程语言分布
- 完整的年度总结文案

### 方式2：重新生成演示报告

```bash
python quick_test.py
```

这将重新生成演示报告，无需任何配置和依赖。

## 分析自己的代码

### 步骤1：安装依赖（可选）

如果要分析真实Git项目，需要安装：

```bash
pip install gitpython pyyaml
```

### 步骤2：配置项目

编辑 `config.yaml`：

```yaml
projects:
  - path: "C:/your/project/path"
    name: "My Project"

authors:
  - "Your Name"

report_year: 2024
```

### 步骤3：运行分析

```bash
python main.py
```

### 步骤4：查看报告

打开 `reports/index.html` 即可查看！

## 报告预览

### 报告包含以下内容：

1. **统计卡片**
   - 总提交次数
   - 净增代码行
   - 参与项目数
   - 代码删除数

2. **AI年度总结**
   - 个性化的年度回顾文案
   - 分析你的代码贡献
   - 展现技术成长

3. **编程语言分布**
   - 你使用的语言及占比
   - 精美的标签云展示

4. **提交热力图**
   - 全年每一天的提交情况
   - 类似GitHub贡献图

5. **项目贡献详情**
   - 每个项目的贡献统计
   - 代码增删情况

## 界面截图

报告特点：
- 🎨 深色渐变主题
- ✨ 流畅的动画效果
- 📱 响应式设计
- 🖱️ 交互式体验

## 常用命令

```bash
# 快速测试（演示数据）
python quick_test.py

# 完整分析（真实Git项目）
python main.py

# 不使用AI（使用预设模板）
python main.py --no-llm

# 导出原始数据
python main.py --export-json
```

## 配置示例

### 个人项目
```yaml
projects:
  - path: "~/my-project"
    name: "个人项目"

authors:
  - "张三"

report_year: 2024
```

### 多项目
```yaml
projects:
  - path: "C:/projects/project-a"
    name: "Project A"
  - path: "C:/projects/project-b"
    name: "Project B"

authors:
  - "Your Name"
  - "your@email.com"
```

### 带AI生成
```yaml
llm:
  provider: "openai"
  model: "gpt-4"
  api_key: "sk-your-api-key"
```

### 自定义主题
```yaml
theme:
  primary_color: "#ff6b6b"
  secondary_color: "#4ecdc4"
  accent_color: "#ffe66d"
```

## 问题排查

### 问题：找不到Python
```bash
# 使用完整路径
C:/tools/Anaconda3/python.exe quick_test.py
```

### 问题：无法打开Git仓库
- 检查路径是否正确
- 确保是Git仓库根目录
- 检查文件夹权限

### 问题：没有提交记录
- 检查authors配置
- 检查report_year是否正确
- 确认Git提交的作者信息

### 问题：LLM调用失败
- 检查API密钥
- 检查网络连接
- 使用 --no-llm 跳过

## 下一步

- 📖 阅读完整文档：[USAGE.md](USAGE.md)
- 🏗️ 了解架构：[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
- 📊 查看项目总结：[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- 🔧 自定义报告模板：[templates/report.html](templates/report.html)

## 反馈与支持

如有问题或建议，欢迎反馈！

---

**现在就开始生成你的年度代码报告吧！** 🚀
