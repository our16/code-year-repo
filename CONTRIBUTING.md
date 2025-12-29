# 贡献指南

感谢你对代码年度报告生成器的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告 Bug

请在 GitHub Issues 中提交 Bug 报告，包含以下信息：

- Python 版本
- 错误信息（完整的 traceback）
- 复现步骤
- 配置文件（脱敏后）

### 提出新功能

请在 GitHub Issues 中提出新功能建议，说明：

- 功能描述
- 使用场景
- 预期效果

### 提交代码

1. Fork 项目
2. 创建分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 遵循 PEP 8 规范
- 使用有意义的变量和函数名
- 添加必要的注释和文档字符串
- 确保代码通过现有测试

#### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

**type 类型**：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行的变动）
- `refactor`: 重构（既不是新增功能，也不是修复 bug）
- `test`: 增加测试
- `chore`: 构建过程或辅助工具的变动

**示例**：
```
feat(llm): add support for Azure OpenAI

- Add AzureOpenAI client
- Update configuration schema
- Add documentation

Closes #123
```

## 开发环境设置

### 安装开发依赖

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black src/
isort src/
```

### 代码检查

```bash
flake8 src/
mypy src/
```

## 项目结构

```
src/
├── git_collector.py      # Git 数据收集
├── data_analyzer.py      # 数据分析
├── llm_client.py         # LLM 客户端
├── generate_reports.py   # 报告生成
├── server.py             # Web 服务器
├── report_generator.py   # 核心逻辑
├── config_loader.py      # 配置加载
└── logger_config.py      # 日志配置
```

## 开发建议

### 添加新功能

1. 先在 Issues 中讨论，避免重复工作
2. 保持功能模块化和可测试
3. 添加必要的文档和注释
4. 更新相关文档

### 修复 Bug

1. 在 Issues 中说明要修复的 Bug
2. 添加测试用例防止回归
3. 确保修复不影响现有功能

### 文档改进

- 修正错别字和语法错误
- 添加使用示例
- 翻译文档
- 改进现有文档的可读性

## 许可证

提交代码即表示你同意将代码以 MIT 许可证发布。

## 联系方式

如有疑问，请在 GitHub Issues 中提问。
