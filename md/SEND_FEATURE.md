# 报告链接发送功能

## 功能概述

在总览页面添加批量发送报告链接的功能，支持：
1. ✅ 批量勾选作者
2. ✅ 一键发送报告链接
3. ✅ 预留消息工具接口
4. ✅ 详细的日志记录

## 界面功能

### 1. 批量选择

#### 每个作者卡片添加复选框
```html
<div class="card-header">
    <label class="author-checkbox">
        <input type="checkbox" class="author-select" value="${author.id}">
    </label>
    <a href="${author.report_url}">
        <h3>${author.name}</h3>
    </a>
</div>
```

#### 全选功能
搜索框旁边添加"全选"复选框：
```html
<label class="select-all-checkbox">
    <input type="checkbox" id="selectAllCheckbox" onchange="toggleSelectAll()">
    <span>全选</span>
</label>
```

**特性**：
- 只全选可见的卡片（搜索后不会选中隐藏的）
- 支持indeterminate状态（部分选中）

### 2. 批量操作栏

选择作者后自动显示操作栏：

```html
<div class="bulk-actions">
    <div class="selection-info">
        已选择 <strong>3</strong> 位作者
    </div>
    <div class="action-buttons">
        <button class="action-btn btn-send" onclick="sendSelectedReports()">
            📤 发送报告链接
        </button>
        <button class="action-btn btn-cancel" onclick="clearSelection()">
            取消选择
        </button>
    </div>
</div>
```

**样式**：
- 白色半透明背景
- 渐入动画效果
- 发送按钮：紫色渐变
- 取消按钮：灰色

## API接口

### POST /api/send-reports

**请求格式**：
```json
{
  "authors": [
    {
      "id": "monge <mongezheng@gmail.com>",
      "name": "monge",
      "reportUrl": "http://localhost:8000/report/monge%20%3Cmongezheng@gmail.com%3E"
    },
    {
      "id": "john <john@example.com>",
      "name": "john",
      "reportUrl": "http://localhost:8000/report/john%20%3Cjohn@example.com%3E"
    }
  ],
  "timestamp": "2025-12-28T15:30:00.000Z"
}
```

**响应格式**：
```json
{
  "success": true,
  "message": "已记录 2 份报告的发送信息",
  "authors_count": 2,
  "timestamp": "2025-12-28T15:30:00.000Z"
}
```

## 服务器日志

### 日志输出示例

```
2025-12-28 15:30:00 - src.server - INFO - ============================================================
2025-12-28 15:30:00 - src.server - INFO - 📤 发送报告链接请求
2025-12-28 15:30:00 - src.server - INFO - ============================================================
2025-12-28 15:30:00 - src.server - INFO - 发送时间: 2025-12-28T15:30:00.000Z
2025-12-28 15:30:00 - src.server - INFO - 发送数量: 3
2025-12-28 15:30:00 - src.server - INFO - 接收者列表:
2025-12-28 15:30:00 - src.server - INFO -   1. monge
2025-12-28 15:30:00 - src.server - INFO -      ID: monge <mongezheng@gmail.com>
2025-12-28 15:30:00 - src.server - INFO -      报告链接: http://localhost:8000/report/monge%20%3Cmongezheng@gmail.com%3E
2025-12-28 15:30:00 - src.server - INFO -   2. john
2025-12-28 15:30:00 - src.server - INFO -      ID: john <john@example.com>
2025-12-28 15:30:00 - src.server - INFO -      报告链接: http://localhost:8000/report/john%20%3Cjohn@example.com%3E
2025-12-28 15:30:00 - src.server - INFO -   3. alice
2025-12-28 15:30:00 - src.server - INFO -      ID: alice <alice@example.com>
2025-12-28 15:30:00 - src.server - INFO -      报告链接: http://localhost:8000/report/alice%20%3Calice@example.com%3E
2025-12-28 15:30:00 - src.server - INFO - ============================================================
2025-12-28 15:30:00 - src.server - INFO - 💡 提示: 您可以在这里接入消息发送工具
2025-12-28 15:30:00 - src.server - INFO -    支持的工具: 钉钉机器人、企业微信、飞书、Slack等
2025-12-28 15:30:00 - src.server - INFO - ============================================================
```

## 预留接口说明

### 当前实现

**文件**: [src/server.py:95-147](src/server.py#L95-L147)

当前实现仅记录日志，不发送实际消息：
```python
def send_reports(self):
    """发送报告链接API - 预留接口，目前只打印日志"""
    # ... 记录日志 ...

    # 预留接口：未来可以在这里接入实际的发送逻辑
    # 例如：
    # - 钉钉机器人 webhook
    # - 企业微信应用消息
    # - 邮件发送
    # - 短信通知
```

### 后续集成方案

#### 方案1：钉钉机器人

```python
def send_to_dingtalk(webhook_url, message):
    """发送到钉钉机器人"""
    import requests

    data = {
        "msgtype": "text",
        "text": {
            "content": message
        }
    }

    response = requests.post(webhook_url, json=data)
    return response.json()
```

**配置** (config/config.yaml):
```yaml
notification:
  dingtalk:
    webhook_url: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
```

#### 方案2：企业微信

```python
def send_to_wechat_work(corpid, corpsecret, agentid, message):
    """发送到企业微信"""
    import requests

    # 获取access_token
    token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corpsecret}&corpsecret={corpsecret}"
    token_resp = requests.get(token_url)
    access_token = token_resp.json()['access_token']

    # 发送消息
    send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
    data = {
        "touser": "@all",
        "msgtype": "text",
        "agentid": agentid,
        "text": {
            "content": message
        }
    }

    response = requests.post(send_url, json=data)
    return response.json()
```

#### 方案3：邮件发送

```python
def send_email(smtp_config, to_emails, subject, body):
    """发送邮件"""
    import smtplib
    from email.mime.text import MIMEText

    msg = MIMEText(body, 'html', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = smtp_config['from']
    msg['To'] = ', '.join(to_emails)

    with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
        server.starttls()
        server.login(smtp_config['username'], smtp_config['password'])
        server.send_message(msg)
```

#### 方案4：Slack

```python
def send_to_slack(webhook_url, message):
    """发送到Slack"""
    import requests

    data = {
        "text": message,
        "username": "代码年度报告",
        "icon_emoji": ":chart_with_upwards_trend:"
    }

    response = requests.post(webhook_url, json=data)
    return response.json()
```

## 使用流程

### 1. 选择作者

1. 访问总览页面 `http://localhost:8000`
2. 勾选需要发送报告的作者
3. 或点击"全选"复选框

### 2. 发送报告

1. 点击"📤 发送报告链接"按钮
2. 浏览器控制台输出详细信息
3. 服务器日志记录发送详情
4. 弹窗确认发送成功

### 3. 查看日志

服务器日志会输出：
- 发送时间
- 发送数量
- 每位作者的详细信息
- 报告链接

## 文件变更清单

### 修改的文件

1. **[static/overview.html](static/overview.html)**
   - 添加批量操作栏 HTML
   - 添加全选复选框
   - 修改搜索框布局

2. **[static/js/overview.js](static/js/overview.js)**
   - 添加批量选择逻辑
   - 添加全选/取消功能
   - 添加发送报告函数
   - 添加前端日志输出

3. **[static/css/overview.css](static/css/overview.css)**
   - 添加批量操作栏样式
   - 添加复选框样式
   - 修改卡片布局
   - 添加动画效果

4. **[src/server.py:95-147](src/server.py#L95-L147)**
   - 添加 `/api/send-reports` POST 端点
   - 添加详细日志记录
   - 预留消息工具集成接口

## 数据流程

```
用户操作
    ↓
选择作者（复选框）
    ↓
点击发送按钮
    ↓
前端收集数据
    ↓
POST /api/send-reports
    ↓
后端接收请求
    ↓
输出详细日志 ← 当前实现
    ↓
[预留] 调用消息工具API
    ↓
返回响应
    ↓
前端提示成功
```

## 测试方法

### 1. 启动服务器

```bash
C:\tools\Anaconda3\python.exe start_server.py
```

### 2. 访问页面

```
http://localhost:8000
```

### 3. 测试批量选择

1. 勾选几位作者
2. 观察"批量操作栏"是否显示
3. 查看选中数量是否正确

### 4. 测试全选

1. 点击"全选"复选框
2. 确认所有可见作者都被选中
3. 取消全选，再次勾选
4. 确认indeterminate状态正常

### 5. 测试发送功能

1. 勾选几位作者
2. 点击"📤 发送报告链接"
3. 打开浏览器控制台查看输出：
   ```
   ========== 发送报告链接 ==========
   发送数量: 2
   接收者: monge, john

   报告链接列表:
   1. monge
      链接: http://localhost:8000/report/monge%20%3Cmongezheng@gmail.com%3E
   2. john
      链接: http://localhost:8000/report/john%20%3Cjohn@example.com%3E
   ====================================
   ```

4. 查看服务器日志输出

### 6. 测试搜索

1. 输入搜索关键词
2. 点击"全选"
3. 确认只选中过滤后的作者

## 后续集成示例

### 集成钉钉机器人

修改 `src/server.py` 的 `send_reports` 方法：

```python
def send_reports(self):
    """发送报告链接"""
    # ... 现有代码 ...

    # 新增：调用钉钉机器人
    try:
        dingtalk_webhook = self.config.get('notification', {}).get('dingtalk_webhook')
        if dingtalk_webhook:
            message = f"代码年度报告已生成\n\n"
            for author in authors:
                message += f"{author['name']}: {author['reportUrl']}\n"

            self._send_to_dingtalk(dingtalk_webhook, message)
    except Exception as e:
        logger.error(f"钉钉发送失败: {str(e)}")

def _send_to_dingtalk(self, webhook_url, message):
    """发送到钉钉"""
    import requests

    data = {
        "msgtype": "text",
        "text": {"content": message}
    }

    response = requests.post(webhook_url, json=data)
    logger.info(f"钉钉响应: {response.json()}")
```

### 集成邮件发送

```python
def send_reports(self):
    """发送报告链接"""
    # ... 现有代码 ...

    # 新增：发送邮件
    smtp_config = self.config.get('notification', {}).get('smtp')
    if smtp_config:
        subject = "您的代码年度报告已生成"

        body = "<h2>代码年度报告</h2>"
        for author in authors:
            body += f"<p>{author['name']}: <a href='{author['reportUrl']}'>查看报告</a></p>"

        self._send_email(smtp_config, authors, subject, body)

def _send_email(self, smtp_config, authors, subject, body):
    """发送邮件"""
    import smtplib
    from email.mime.text import MIMEText

    # 收集邮件地址
    to_emails = [author.get('email') for author in authors if author.get('email')]

    msg = MIMEText(body, 'html', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = smtp_config['from']
    msg['To'] = ', '.join(to_emails)

    with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
        server.starttls()
        server.login(smtp_config['username'], smtp_config['password'])
        server.send_message(msg)
```

## 注意事项

### 1. 隐私和安全

- 确保报告链接是安全的（HTTPS）
- 考虑添加访问权限验证
- 避免在日志中记录敏感信息

### 2. 性能考虑

- 批量发送时使用异步操作
- 避免一次发送过多消息
- 考虑使用消息队列

### 3. 用户体验

- 发送前确认提示
- 显示发送进度
- 提供发送结果反馈

## 总结

### 当前实现

✅ **已完成**：
- 批量选择功能
- 全选/取消功能
- 批量操作界面
- 详细日志记录
- 前端/后端API对接

⏳ **待集成**：
- 实际消息发送工具
- 钉钉/企业微信/邮件/短信等

### 预留接口

所有集成点都已预留：
- 前端：`sendSelectedReports()` 函数
- 后端：`send_reports()` 方法
- 配置：`config/config.yaml`

只需在对应位置添加具体的消息发送代码即可。
