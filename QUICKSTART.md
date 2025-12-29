# 快速启动指南

## 5 分钟快速上手

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置项目

编辑 `config/config.yaml`，修改项目路径：

```yaml
projects:
  - path: "F:/project"  # 改为你的 Git 仓库路径
    name: "my-repo"

report_year: 2025  # 报告年份
```

### 3. 启动服务

```bash
python src/server.py
```

### 4. 访问界面

打开浏览器访问：http://localhost:8000

- 默认账号：`admin`
- 默认密码：`admin`

### 5. 生成报告

登录后点击"生成报告"按钮，等待生成完成即可。

## 常用命令

### 生成报告

```bash
# 直接生成（不启动 Web 服务）
python src/generate_reports.py
```

### 自定义端口启动

```bash
python src/server.py --port 8080
```

### 查看日志

```bash
# 日志文件位置
tail -f logs/server.log
tail -f logs/generate_reports.log
```

## 配置 LLM（可选）

如果不配置 LLM，系统会使用预设模板生成报告。

### 使用 OpenAI

```yaml
llm:
  provider: "openai"
  model: "gpt-4"
  api_key: "sk-..."
  base_url: "https://api.openai.com/v1"
```

### 使用本地 Ollama

```yaml
llm:
  provider: "openai"
  model: "llama2"
  api_key: "not-needed"
  base_url: "http://localhost:11434/v1"
```

## 故障排查

### 问题：找不到 Git 仓库

**原因**：路径配置错误或不是 Git 仓库

**解决**：
1. 检查路径是否正确
2. 确保目录包含 `.git` 文件夹

### 问题：LLM 请求失败

**原因**：API 配置错误或网络问题

**解决**：
1. 检查 API key 是否正确
2. 尝试增加 `timeout` 配置
3. 或者不使用 LLM（使用预设模板）

### 问题：端口被占用

**错误**：`OSError: [Errno 48] Address already in use`

**解决**：
```bash
# 使用其他端口
python src/server.py --port 8080
```

## 下一步

- 查看 [完整文档](README.md)
- 查看 [设计文档](md/)
- 自定义主题和模板
