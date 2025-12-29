# UUID访问改造设计文档

## 改造概述

将报告访问方式从使用用户名改为使用UUID，提升安全性和用户体验。

### 改造前
- 访问URL: `/report/张三 <zhangsan@example.com>`
- JSON文件名: `张三_2025.json`
- 问题: URL中暴露用户信息，包含特殊字符，不够美观和安全

### 改造后
- 访问URL: `/report/a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d`
- JSON文件名: `a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d.json`
- 优势: 隐藏用户信息，URL简洁，安全性更高

## 数据结构变更

### 1. 报告JSON文件结构

新增 `uuid` 字段:

```json
{
  "meta": {
    "author": "张三",
    "email": "zhangsan@example.com",
    "author_id": "张三 <zhangsan@example.com>",
    "uuid": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
    "year": 2025,
    "generated_at": "2025-01-01T12:00:00"
  },
  ...
}
```

### 2. 索引文件结构 (report_index.json)

使用UUID作为key:

```json
{
  "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d": {
    "uuid": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
    "id": "张三 <zhangsan@example.com>",
    "name": "张三",
    "email": "zhangsan@example.com",
    "commits": 1234,
    "net_lines": 5678,
    "projects": 3,
    "json_file": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d.json",
    "generated_at": "2025-01-01T12:00:00"
  }
}
```

### 3. UUID映射文件 (uuid_mapping.json)

新增映射文件，便于管理员查看:

```json
{
  "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d": {
    "author_info": "张三 <zhangsan@example.com>",
    "author_name": "张三",
    "author_email": "zhangsan@example.com"
  }
}
```

## 代码变更

### 1. 生成报告逻辑 (src/generate_reports.py)

**变更内容:**
- 导入 `uuid` 模块
- 为每个作者生成唯一的UUID
- JSON文件名使用UUID而非用户名
- 报告数据中添加 `uuid` 字段
- 生成 `uuid_mapping.json` 文件

**关键代码:**
```python
# 生成UUID
author_uuid = str(uuid.uuid4())

# JSON文件名使用UUID
json_filename = f"{author_uuid}.json"

# 添加UUID到报告数据
report_data = {
    'meta': {
        'author': author_name,
        'email': author_email,
        'author_id': author_info,
        'uuid': author_uuid,  # 新增
        ...
    },
    ...
}
```

### 2. Web服务器逻辑 (src/server.py)

**变更内容:**
- `load_report_data()`: 只加载有UUID的报告，使用UUID作为key
- `send_authors_api()`: API返回UUID，使用UUID生成访问URL
- `send_author_data()`: 通过UUID直接查找作者数据
- `serve_author_report()`: 通过UUID访问报告页面

**重要变更:**
- **不再兼容**旧的author_id访问方式
- 只支持UUID，代码更简洁清晰
- 没有UUID的报告文件会被跳过并记录警告

**关键代码:**
```python
# API返回UUID
for author_uuid, data in report_data.items():
    authors.append({
        'uuid': author_uuid,  # UUID作为主要标识
        'name': data.get('name', 'Unknown'),
        'report_url': f"/report/{author_uuid}",  # 使用UUID访问
    })

# 通过UUID直接查找
author_info = report_data.get(author_uuid)
```

### 3. 前端代码 (static/js/overview.js)

**无需修改:**
- 前端通过API获取 `report_url`，已经自动使用UUID
- 点击跳转直接使用API返回的URL

## 使用方式

### 用户访问报告

1. 在总览页面点击作者卡片
2. 自动跳转到 `/report/{uuid}`
3. 页面正常显示报告内容

### 管理员查看映射

查看 `reports/uuid_mapping.json` 文件，了解UUID与作者的对应关系:

```bash
cat reports/uuid_mapping.json | jq
```

### 分享报告链接

直接分享 `/report/{uuid}` 链接，无需担心暴露用户信息。

## 数据流程

### 生成阶段

```
作者信息 → 生成UUID → 创建{uuid}.json → 更新索引文件
           ↓
    保存uuid_mapping.json
```

### 访问阶段

```
用户访问 /report/{uuid}
    ↓
服务器通过UUID查找对应JSON文件
    ↓
加载并渲染报告页面
```

## 优势总结

1. **隐私保护**: URL中不暴露用户名和邮箱
2. **安全性**: UUID难以猜测，防止未授权访问
3. **简洁性**: URL格式统一，避免特殊字符问题
4. **可维护性**: 代码更简洁，UUID映射文件方便管理
5. **规范性**: 统一使用UUID作为唯一标识

## 注意事项

1. **映射管理**: `uuid_mapping.json` 文件应妥善保管，便于查找对应关系
2. **重新生成**: 每次生成报告会生成新的UUID，旧UUID会失效
3. **链接分享**: 重新生成报告后，需要更新分享的链接
4. **旧报告**: 没有UUID的旧报告需要重新生成才能访问

## 技术细节

### UUID格式
- 使用Python标准库 `uuid.uuid4()` 生成
- 格式: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`
- 示例: `a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d`

### 文件命名
- JSON文件: `{uuid}.json`
- 长度固定: 36字符（包含4个连字符）
- 无需转义，避免中文和特殊字符问题

### 查找性能
- 使用字典直接查找: O(1)
- UUID作为key，无需遍历
- 比原来的字符串匹配更高效
