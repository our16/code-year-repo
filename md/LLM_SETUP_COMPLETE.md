# LLM配置完成

## 配置状态

✅ **LLM配置已完成**

### 当前配置

**配置文件**: [config/config.yaml](../config/config.yaml)

```yaml
llm:
  provider: "openai"
  model: "claude-sonnet-4-5"
  api_key: "sk-not-needed"  # 本地服务可使用任意值
  base_url: "http://0.0.0.0:8090"  # 本地LLM服务地址
```

### 配置说明

1. **Provider**: `openai` - 使用OpenAI兼容API接口
2. **Model**: `claude-sonnet-4-5` - 模型名称
3. **Base URL**: `http://0.0.0.0:8090` - 您的本地LLM服务地址
4. **API Key**: `sk-not-needed` - 本地服务可以使用任意值

### LLM客户端实现

**文件**: [src/llm_client.py:37-70](../src/llm_client.py#L37-L70)

客户端已支持自定义 `base_url`，会自动连接到您的本地服务。

```python
def _generate_with_openai(self, data: Dict[str, Any]) -> str:
    """使用OpenAI生成文案"""
    from openai import OpenAI

    client = OpenAI(
        api_key=self.api_key,
        base_url=self.base_url or None  # 支持自定义base_url
    )

    response = client.chat.completions.create(
        model=self.model,
        messages=[...],
        temperature=0.8,
        max_tokens=2000,
    )

    return response.choices[0].message.content
```

## 使用方式

### 1. 生成报告时自动使用LLM

配置完成后，每次生成报告会自动调用LLM生成个性化文案：

**通过Web界面**：
1. 访问 http://localhost:8000
2. 点击"🔄 生成报告"按钮
3. 系统会自动使用LLM为每个作者生成年度总结文案

**通过命令行**：
```bash
C:\tools\Anaconda3\python.exe src/generate_reports.py
```

### 2. 测试LLM连接

运行测试脚本验证配置是否正确：

```bash
C:\tools\Anaconda3\python.exe test_llm.py
```

**预期输出**：
```
2025-12-28 HH:MM:SS - code-year-report - INFO - LLM配置:
2025-12-28 HH:MM:SS - code-year-report - INFO -   Provider: openai
2025-12-28 HH:MM:SS - code-year-report - INFO -   Model: claude-sonnet-4-5
2025-12-28 HH:MM:SS - code-year-report - INFO -   Base URL: http://0.0.0.0:8090
...
2025-12-28 HH:MM:SS - code-year-report - INFO - [成功] LLM调用成功！
2025-12-28 HH:MM:SS - code-year-report - INFO - 测试通过！LLM连接正常。
```

## LLM功能

### 生成内容

LLM会根据代码数据生成包含以下内容的年度总结文案：

1. **标题** - 吸引人的年度报告标题
2. **开篇** - 温暖的开场白
3. **数字背后的热忱** - 提交量、代码行数的情感化描述
4. **技术的探索之路** - 编程语言和项目经历
5. **时间的足迹** - 提交习惯和高效时段
6. **精简的艺术** - 重构贡献和代码质量追求
7. **结语** - 展望未来的寄语

### 示例输出

```markdown
# 💌 致过去的一年：你的代码，你的诗篇

在冰冷的数字背后，是你一整年的热忱、思考和创造。

## 年初的Flag，是写在晨光里的序章

每一个早起的清晨，每一个静谧的深夜，键盘敲击出的不只是代码，
更是你解决问题的决心。那些 1234 次的提交，是你与复杂问题一次次
交锋的勋章...

## 你的技术栈，是你探索世界的地图

这一年，你在 Python, JavaScript 的世界里探索。参与 1 个不同项目
的经历，证明你不仅是深耕某一领域的专家，更是具备全局视野的团队协作者...

...

*继续用代码书写你的故事吧！*
```

## 注意事项

### 1. 本地服务要求

确保您的LLM服务：
- ✅ 正在运行在 `http://0.0.0.0:8090`
- ✅ 支持OpenAI兼容的 `/v1/chat/completions` 接口
- ✅ 返回标准OpenAI响应格式
- ✅ 支持指定的模型 `claude-sonnet-4-5`

### 2. 依赖安装

确保已安装 `openai` 库：

```bash
C:\tools\Anaconda3\Scripts\pip.exe install openai
```

### 3. 禁用LLM

如果需要禁用LLM功能，将配置留空即可：

```yaml
llm:
  provider: "openai"
  model: ""
  api_key: ""  # 留空
  base_url: ""
```

系统会使用内置的默认模板生成报告。

## 故障排查

### 连接失败

**问题**: 无法连接到 `http://0.0.0.0:8090`

**解决方案**:
1. 确认LLM服务是否正在运行
2. 检查端口号是否正确
3. 尝试使用 `http://localhost:8090` 代替
4. 检查防火墙设置

### 模型不支持

**问题**: 模型 `claude-sonnet-4-5` 不存在

**解决方案**:
修改 `config/config.yaml` 中的模型名称为您的服务支持的模型：

```yaml
llm:
  model: "deepseek-chat"  # 或其他支持的模型
```

### API格式不兼容

**问题**: 响应格式不匹配

**解决方案**:
确认您的LLM服务返回OpenAI格式响应。如果使用其他格式，需要修改 `src/llm_client.py`。

## 测试API格式

使用curl测试您的服务：

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

## 相关文档

- [LLM_CONFIG.md](LLM_CONFIG.md) - 详细的LLM配置指南
- [src/llm_client.py](../src/llm_client.py) - LLM客户端实现
- [config/config.yaml](../config/config.yaml) - 配置文件

## 下一步

1. **测试连接**: 运行 `test_llm.py` 验证配置
2. **生成报告**: 使用Web界面或命令行生成报告
3. **查看结果**: 检查生成的报告文案是否符合预期

如有问题，请检查：
- LLM服务是否正常运行
- 网络连接是否正常
- 配置文件格式是否正确
- 模型名称是否支持
