# LLM配置指南

## 配置说明

### 本地LLM服务配置

项目已配置为使用本地LLM服务，地址为 `http://0.0.0.0:8090`

#### 当前配置 (config/config.yaml)

```yaml
llm:
  provider: "openai"  # 使用OpenAI兼容接口
  model: "claude-sonnet-4-5"
  api_key: "sk-not-needed"  # 本地服务可以填写任意值
  base_url: "http://0.0.0.0:8090"  # 本地LLM服务地址
```

### 配置项说明

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| `provider` | LLM提供商 | `openai` (本地服务通常使用OpenAI兼容接口) |
| `model` | 模型名称 | `claude-sonnet-4-5`, `gpt-4`, `deepseek-chat` 等 |
| `api_key` | API密钥 | 本地服务可以使用任意值，如 `sk-not-needed` |
| `base_url` | API基础URL | `http://0.0.0.0:8090` |

### 支持的LLM服务

#### 1. OpenAI兼容接口（推荐）

本地LLM服务通常提供OpenAI兼容的API接口：

```yaml
llm:
  provider: "openai"
  model: "your-model-name"
  api_key: "any-value"
  base_url: "http://0.0.0.0:8090"
```

**常用本地LLM服务**：
- **Ollama**: `http://localhost:11434`
- **vLLM**: `http://localhost:8000`
- **LM Studio**: `http://localhost:1234`
- **LocalAI**: `http://localhost:8080`
- **自定义服务**: `http://0.0.0.0:8090` (您的配置)

#### 2. OpenAI官方API

```yaml
llm:
  provider: "openai"
  model: "gpt-4"
  api_key: "sk-your-real-openai-key"
  base_url: ""  # 留空使用官方端点
```

#### 3. Anthropic Claude

```yaml
llm:
  provider: "anthropic"
  model: "claude-3-sonnet-20240229"
  api_key: "sk-ant-your-real-key"
  base_url: ""
```

#### 4. Azure OpenAI

```yaml
llm:
  provider: "azure"
  model: "gpt-4"
  api_key: "your-azure-key"
  base_url: "https://your-resource.openai.azure.com"
```

## API兼容性要求

### OpenAI兼容接口规范

您的本地LLM服务需要实现以下OpenAI API端点：

#### POST /v1/chat/completions

**请求格式**:
```json
{
  "model": "claude-sonnet-4-5",
  "messages": [
    {"role": "system", "content": "系统提示词"},
    {"role": "user", "content": "用户消息"}
  ],
  "temperature": 0.8,
  "max_tokens": 2000
}
```

**响应格式**:
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "claude-sonnet-4-5",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "生成的回复内容"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

### 测试您的LLM服务

使用curl测试服务是否正常：

```bash
curl -X POST http://0.0.0.0:8090/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "messages": [
      {"role": "user", "content": "Say Hello, World!"}
    ],
    "stream": false
  }'
```

**期望响应**：
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "claude-sonnet-4-5",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello, World!"
      },
      "finish_reason": "stop"
    }
  ]
}
```

## 测试步骤

### 1. 使用测试脚本

```bash
C:\tools\Anaconda3\python.exe test_llm.py
```

**预期输出**：
```
2025-12-28 HH:MM:SS - code-year-report - INFO - Logger initialized
2025-12-28 HH:MM:SS - code-year-report - INFO - ============================================================
2025-12-28 HH:MM:SS - code-year-report - INFO - 开始测试LLM连接
2025-12-28 HH:MM:SS - code-year-report - INFO - ============================================================
2025-12-28 HH:MM:SS - code-year-report - INFO - LLM配置:
2025-12-28 HH:MM:SS - code-year-report - INFO -   Provider: openai
2025-12-28 HH:MM:SS - code-year-report - INFO -   Model: claude-sonnet-4-5
2025-12-28 HH:MM:SS - code-year-report - INFO -   Base URL: http://0.0.0.0:8090
2025-12-28 HH:MM:SS - code-year-report - INFO -   API Key: sk-not-ne...
...
2025-12-28 HH:MM:SS - code-year-report - INFO - ✅ LLM调用成功！
```

### 2. 在报告中生成LLM文案

配置完成后，生成报告时会自动使用LLM：

```bash
# 方式1：通过Web界面
访问 http://localhost:8000
点击"生成报告"按钮

# 方式2：直接运行生成脚本
C:\tools\Anaconda3\python.exe src/generate_reports.py
```

## 故障排查

### 问题1：连接被拒绝

**错误信息**：
```
Connection refused: http://0.0.0.0:8090
```

**解决方法**：
1. 确认LLM服务是否正在运行
2. 检查端口号是否正确
3. 尝试使用 `localhost` 代替 `0.0.0.0`：
   ```yaml
   base_url: "http://localhost:8090"
   ```

### 问题2：API返回错误

**错误信息**：
```
OpenAI调用失败: 404 Not Found
```

**解决方法**：
1. 检查API路径是否包含 `/v1` 前缀
2. 确认服务支持OpenAI兼容接口
3. 查看服务日志确认请求格式

### 问题3：模型不支持

**错误信息**：
```
Model 'claude-sonnet-4-5' not found
```

**解决方法**：
1. 检查您的LLM服务支持的模型列表
2. 修改配置文件中的模型名称：
   ```yaml
   model: "deepseek-chat"  # 或其他支持的模型
   ```

### 问题4：响应格式不兼容

**错误信息**：
```
KeyError: 'choices'
```

**解决方法**：
确认您的LLM服务返回OpenAI格式的响应。如果服务使用其他格式，需要修改 `src/llm_client.py` 中的响应解析逻辑。

## 禁用LLM功能

如果不需要使用LLM生成文案，可以：

### 方式1：清空API密钥

```yaml
llm:
  provider: "openai"
  model: "gpt-4"
  api_key: ""  # 留空
  base_url: ""
```

系统会使用内置的默认模板生成报告。

### 方式2：完全删除配置

```yaml
# llm:  # 注释掉整个配置块
```

## 高级配置

### 自定义提示词

如需修改LLM生成的提示词，编辑 `src/llm_client.py` 的 `_build_prompt` 方法：

```python
def _build_prompt(self, data: Dict[str, Any]) -> str:
    # 自定义您的提示词
    prompt = f"请根据以下数据生成年度报告：{data}"
    return prompt
```

### 调整生成参数

修改 `src/llm_client.py` 中的生成参数：

```python
response = client.chat.completions.create(
    model=self.model,
    messages=[...],
    temperature=0.8,    # 调整创造性 (0.0-1.0)
    max_tokens=2000,    # 调整最大长度
    top_p=0.9,         # 添加采样参数
)
```

## 支持的本地LLM服务推荐

### 1. Ollama
- **下载**: https://ollama.ai
- **端点**: `http://localhost:11434`
- **配置**:
  ```yaml
  base_url: "http://localhost:11434/v1"
  model: "llama2"
  ```

### 2. LM Studio
- **下载**: https://lmstudio.ai
- **端点**: `http://localhost:1234/v1`
- **特点**: 图形界面，易用

### 3. vLLM
- **GitHub**: https://github.com/vllm-project/vllm
- **特点**: 高性能，支持并发

### 4. LocalAI
- **GitHub**: https://github.com/mudler/LocalAI
- **特点**: OpenAI API完全兼容

## 参考资源

- OpenAI API文档: https://platform.openai.com/docs/api-reference
- Anthropic API文档: https://docs.anthropic.com
- 本地LLM服务列表: https://github.com/OpenAccess-AI-Collective/awesome-llm-local
