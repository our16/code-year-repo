# XML格式AI文案解析功能说明

## 问题描述

LLM输出的XML格式文案在经典报告页面（report.html）中直接显示为XML标签，而不是渲染成美观的卡片。

## 解决方案

实现了XML解析功能，将LLM输出的XML格式转换为HTML卡片，在经典报告页面中美观地展示。

## 实现的功能

### 1. XML解析（后端）

**文件：[src/server.py](src/server.py)**

#### 添加XML检测逻辑（第950-953行）
```python
# 检查是否是XML格式
if '<graphs>' in ai_text and '<graph>' in ai_text:
    # 解析XML格式
    ai_text_html = self._parse_xml_ai_text(ai_text, data)
```

#### 新增XML解析函数（第974-1074行）
```python
def _parse_xml_ai_text(self, ai_text: str, data: dict) -> str:
    """解析XML格式的AI文案"""
    # 1. 提取<graphs>标签内容
    # 2. 提取所有<graph>标签
    # 3. 解析每个字段的type、value、title、content
    # 4. 自动匹配图标
    # 5. 生成HTML卡片
```

**功能特点：**
- 支持XML和Markdown两种格式
- 自动匹配图标（无需LLM输出）
- 解析失败时回退到默认文案
- 安全的异常处理

### 2. 卡片样式（前端）

**文件：[templates/report.html](templates/report.html)**

#### 添加卡片CSS样式（第291-378行）

```css
.metric-card {
    background: var(--card-bg);
    border-radius: 20px;
    padding: 30px;
    margin-bottom: 30px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
}

.metric-header {
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 25px;
    padding-bottom: 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.metric-icon {
    font-size: 3rem;
    animation: float 3s ease-in-out infinite;
}

.metric-value {
    font-size: 2.5rem;
    font-weight: bold;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.metric-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--accent-color);
}

.metric-description {
    font-size: 1.1rem;
    line-height: 2;
    color: var(--text-primary);
}
```

**样式特点：**
- 渐变色数值显示
- 浮动动画图标
- 悬停提升效果
- 引号装饰标题
- 响应式设计

## XML格式示例

### 输入格式（LLM输出）
```xml
<graphs>
<graph>
<type>提交次数</type>
<value>1234</value>
<title>数字中的热忱</title>
<content>这一年，你用1234次提交在编程的世界里书写了一段传奇...</content>
</graph>
<graph>
<type>代码行数</type>
<value>50000</value>
<title>代码长城的筑造</title>
<content>这是你技术成长的巍峨丰碑...</content>
</graph>
</graphs>
```

### 输出格式（渲染后的HTML）
```html
<div class="metric-card">
    <div class="metric-header">
        <span class="metric-icon">💫</span>
        <span class="metric-value">1234</span>
        <span class="metric-label">提交次数</span>
    </div>
    <div class="metric-content">
        <h4 class="metric-title">数字中的热忱</h4>
        <p class="metric-description">这一年，你用1234次提交在编程的世界里书写了一段传奇...</p>
    </div>
</div>
```

## 图标自动映射

**支持的指标类型及对应图标：**

| 指标类型 | 图标 | 匹配关键词 |
|---------|------|-----------|
| 提交次数 | 💫 | 提交、提交次数 |
| 代码行数 | 🌈 | 代码、代码行数、净增代码 |
| 项目数量 | 🚀 | 项目、项目数量、参与项目 |
| 编程语言 | 💻 | 编程语言、语言、主要语言 |
| 高效时段 | 🌙 | 高效时段、时段、时间、黄金时段 |
| 重构比例 | 🎯 | 重构比例、重构、精简 |
| 默认 | 📊 | 其他 |

## 兼容性

### 向后兼容
- 如果AI文案不是XML格式，使用原有的Markdown解析逻辑
- 如果XML解析失败，回退到默认文案

### 支持的格式
1. **XML格式**（推荐）
   - 结构化数据
   - 自动卡片渲染
   - 图标自动匹配

2. **Markdown格式**（向后兼容）
   - 简单的文本处理
   - 标题和段落转换
   - 粗体和斜体支持

3. **默认文案**（兜底）
   - 无AI文案时使用
   - 基于实际数据生成
   - 保证基本展示效果

## 使用场景

### 1. LLM配置
确保LLM按照XML格式输出（参考[llm_client.py](src/llm_client.py:112-169)中的提示词）：

```python
prompt = """
必须严格按照以下XML格式输出，每个<graph>标签代表一个独立的指标卡片：

<graphs>
<graph>
<type>提交次数</type>
<value>1234</value>
<title>数字中的热忱</title>
<content>...</content>
</graph>
</graphs>
"""
```

### 2. 报告访问
- **照片墙模式**：`/report/author?style=scroll` - 已有XML解析
- **经典模式**：`/report/author?style=classic` - **新增XML解析**

## 测试建议

1. **XML格式测试**
   - 生成报告并访问经典模板
   - 验证XML被正确解析为卡片
   - 检查图标是否正确匹配

2. **Markdown格式测试**
   - 使用旧版LLM输出（Markdown格式）
   - 验证向后兼容性
   - 检查文本渲染效果

3. **异常处理测试**
   - 不完整的XML标签
   - 空的AI文案
   - 验证回退到默认文案

## 性能优化

- 使用正则表达式快速解析XML（无需完整XML解析器）
- 缓存图标映射结果
- 一次性生成所有卡片HTML
- 最小化DOM操作

## 注意事项

1. **LLM输出要求**
   - 必须包含`<graphs>`和`<graph>`标签
   - 每个graph必须包含完整的四个字段
   - 不要在XML中输出`<icon>`字段

2. **前端渲染**
   - 卡片在服务端渲染，无需前端JavaScript
   - CSS动画在浏览器中执行
   - 响应式设计适配移动端

3. **扩展性**
   - 添加新指标类型只需更新图标映射
   - 支持自定义卡片样式
   - 可轻松添加新的XML字段

## 相关文件

- **XML解析**：[src/server.py:974-1074](src/server.py#L974-L1074)
- **格式检测**：[src/server.py:950-953](src/server.py#L950-L953)
- **卡片样式**：[templates/report.html:291-378](templates/report.html#L291-L378)
- **LLM提示词**：[src/llm_client.py:112-169](src/llm_client.py#L112-L169)
