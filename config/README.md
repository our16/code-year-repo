# 配置文件目录

此目录包含项目的所有配置文件。

## 文件说明

### config.yaml
主配置文件，包含：
- Git仓库路径配置
- 报告年份设置
- 作者筛选
- LLM API配置
- 主题颜色设置

### author_mapping.yaml
作者名字映射配置，用于统一不同格式的作者名字，例如：
- "monge" → "Monge(中文名) <monge@example.com>"
- "Monge" → "Monge(中文名) <monge@example.com>"

## 示例文件

- `config.example.yaml` - 配置文件示例
- `author_mapping.example.yaml` - 作者映射示例

## 使用方法

1. 复制示例文件：
   ```bash
   cp config.example.yaml config.yaml
   cp author_mapping.example.yaml author_mapping.yaml
   ```

2. 根据实际情况修改配置

3. 运行程序时会自动读取这些配置

## 注意事项

- 这些配置文件已在 `.gitignore` 中，不会被提交到Git
- 请妥善保管包含API密钥的配置文件
