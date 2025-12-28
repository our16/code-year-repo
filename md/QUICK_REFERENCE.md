# 快速参考卡片

## 🚀 一分钟开始

```bash
# 1. 生成报告
python main.py --no-llm

# 2. 启动服务
python server.py

# 3. 访问
# http://localhost:8000
```

---

## 📝 配置文件

```yaml
# config.yaml
projects:
  - path: "F:/project"    # 自动发现
    name: "所有项目"

authors:                    # 留空=所有人
report_year: 2025
```

---

## 🎯 三种配置方式

### 1. 自动发现（推荐）
```yaml
projects:
  - path: "F:/project"
    name: "所有项目"
authors:  # 所有人
```

### 2. 手动指定
```yaml
projects:
  - path: "F:/project/repo1"
    name: "项目1"
authors:
  - "张三"
```

### 3. 混合使用
```yaml
projects:
  - path: "F:/project"      # 自动发现
  - path: "F:/special-repo" # 手动指定
```

---

## 🔧 常用命令

```bash
# 生成报告（所有人）
python main.py --no-llm

# 生成报告（指定作者）
# 编辑 config.yaml 的 authors

# 导出原始数据
python main.py --export-json

# 使用LLM生成文案
python main.py

# 启动Web服务
python server.py

# 自定义端口
python server.py --port 8080

# 快速测试
python quick_test.py
```

---

## 📂 输出文件

```
reports/
├── index.html              # 总览页面
├── report_index.json       # 报告索引
├── 作者1_2025.html
├── 作者2_2025.html
└── ...
```

---

## 🌐 Web服务

```bash
# 启动
python server.py

# 访问
http://localhost:8000

# 网络访问
http://your-ip:8000

# API接口
http://localhost:8000/api/authors
http://localhost:8000/api/author/作者ID
```

---

## 🔍 SonarQube（可选）

```bash
# 1. 启动SonarQube
docker-compose up -d

# 2. 分析项目
sonar-scanner \
  -Dsonar.projectKey=my-project \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://localhost:9000

# 3. 配置config.yaml
sonarqube:
  enabled: true
  url: "http://localhost:9000"
  token: "squ_xxx"

# 4. 生成报告
python main.py --no-llm
```

---

## 📊 报告内容

### 个人报告包含：
- ✅ 总提交次数
- ✅ 净增代码行
- ✅ 参与项目数
- ✅ 代码删除数
- ✅ 编程语言分布
- ✅ 提交热力图
- ✅ 项目贡献详情
- ✅ AI年度总结

### 总览页面包含：
- ✅ 团队统计
- ✅ 作者列表
- ✅ 搜索功能
- ✅ 个人报告链接

---

## ⚙️ 主题配置

```yaml
theme:
  primary_color: "#667eea"
  secondary_color: "#764ba2"
  accent_color: "#f093fb"
```

---

## 🛠️ 故障排查

### 端口被占用
```bash
python server.py --port 8001
```

### 没有提交记录
```yaml
# 检查authors配置
# 检查report_year
# 检查Git历史
```

### 数据为0
```bash
# 重新生成报告
python main.py --no-llm
```

---

## 📚 文档索引

- [README.md](README.md) - 项目介绍
- [GETTING_STARTED.md](GETTING_STARTED.md) - 快速开始
- [USAGE.md](USAGE.md) - 详细使用
- [FEATURE_GROUPED_REPORTS.md](FEATURE_GROUPED_REPORTS.md) - 分组报告
- [SERVER_GUIDE.md](SERVER_GUIDE.md) - Web服务
- [SONARQUBE_INTEGRATION.md](SONARQUBE_INTEGRATION.md) - 代码质量
- [FINAL_SUMMARY.md](FINAL_SUMMARY.md) - 完整总结

---

## 💡 最佳实践

### 个人使用
```yaml
authors:
  - "Your Name"
```

### 团队使用
```yaml
authors:  # 留空
```

### 大型项目
```bash
# 先测试单个项目
# 再扫描全部
python quick_test.py
```

---

## 🎉 快速检查清单

- [ ] 配置 `config.yaml`
- [ ] 检查项目路径
- [ ] 设置 `report_year`
- [ ] 配置 `authors`（可选）
- [ ] 运行 `python main.py --no-llm`
- [ ] 启动 `python server.py`
- [ ] 访问 `http://localhost:8000`

---

**完成！** ✅

需要帮助？查看完整文档或运行 `python --help`
