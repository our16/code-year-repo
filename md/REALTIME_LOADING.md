# 实时数据加载实现

## 更新时间
2025-12-28

## 修改说明

将报告数据从**启动时一次性加载**改为**每次请求实时加载**，确保数据始终是最新的。

## 修改的方法

### 1. `/api/authors` - 获取作者列表
**文件**: [src/server.py:121-149](../src/server.py#L121-L149)

```python
def send_authors_api(self):
    """发送作者列表API - 实时加载报告数据"""
    # 实时重新加载报告数据
    reports_dir = Path(self.directory)
    report_data = load_report_data(reports_dir)
    logger.info(f"API调用：实时加载了 {len(report_data)} 个报告")

    authors = []
    for author_id, data in report_data.items():
        authors.append({
            'id': author_id,
            'name': data.get('name', 'Unknown'),
            'email': data.get('email', ''),
            'commits': data.get('commits', 0),
            'net_lines': data.get('net_lines', 0),
            'projects': data.get('projects', 0),
            'report_url': f"/report/{author_id}",
        })

    # 按提交数排序
    authors.sort(key=lambda x: x['commits'], reverse=True)

    response = {
        'total': len(authors),
        'authors': authors
    }

    self.send_json_response(response)
```

**改进**：
- ✅ 每次API调用时重新扫描 `reports/*.json`
- ✅ 自动获取最新的作者列表
- ✅ 新生成的报告立即可见

### 2. `/api/author/<id>` - 获取特定作者数据
**文件**: [src/server.py:151-182](../src/server.py#L151-L182)

```python
def send_author_data(self, author_id):
    """发送特定作者的JSON数据 - 实时加载"""
    # 实时重新加载报告数据
    reports_dir = Path(self.directory)
    report_data = load_report_data(reports_dir)

    # 查找作者的JSON文件
    author_info = None
    for aid, data in report_data.items():
        if aid == author_id or data.get('name') == author_id:
            author_info = data
            break
    ...
```

**改进**：
- ✅ 实时查找作者报告
- ✅ 支持新增作者的热加载

### 3. `/api/progress` - 获取生成进度
**文件**: [src/server.py:184-212](../src/server.py#L184-L212)

```python
def send_progress_api(self):
    """发送生成进度API - 实时加载"""
    # 读取进度文件（如果存在）
    progress_file = project_root / 'reports' / '.progress.json'

    if progress_file.exists():
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            self.send_json_response(progress)
            return
        except:
            pass

    # 实时加载当前报告数量
    reports_dir = Path(self.directory)
    report_data = load_report_data(reports_dir)
    total_reports = len(report_data)

    # 默认返回完成状态
    response = {
        'status': 'completed',
        'total': total_reports,
        'completed': total_reports,
        'current': 'All reports generated',
        'percentage': 100
    }
    self.send_json_response(response)
```

**改进**：
- ✅ 优先读取进度文件（生成中）
- ✅ 实时统计已完成的报告数量
- ✅ 准确反映当前状态

### 4. `/report/<id>` - 查看个人报告页面
**文件**: [src/server.py:251-293](../src/server.py#L251-L293)

```python
def serve_author_report(self, author_id):
    """提供个人报告页面 - 实时加载"""
    # URL解码
    from urllib.parse import unquote
    author_id = unquote(author_id)

    # 实时重新加载报告数据
    reports_dir = Path(self.directory)
    report_data = load_report_data(reports_dir)

    # 查找作者信息
    author_info = None
    for aid, data in report_data.items():
        if aid == author_id or data.get('name') == author_id or data.get('id') == author_id:
            author_info = data
            break
    ...
```

**改进**：
- ✅ 每次访问报告页面时重新加载数据
- ✅ 重新生成报告后无需刷新即可看到最新内容

## 工作流程

### 报告生成流程

1. **用户点击"生成报告"按钮**
   - 前端调用 `POST /api/generate`
   - 后端启动后台生成线程

2. **生成过程中**
   - 前端每秒轮询 `GET /api/progress`
   - 后端实时读取 `.progress.json`
   - 进度条实时更新

3. **生成完成后**
   - 新报告JSON文件保存到 `reports/` 目录
   - 前端自动刷新页面
   - 调用 `GET /api/authors` 获取最新列表
   - **此时会扫描并包含新生成的报告**

### 数据访问流程

```
用户请求 → API调用 → 实时扫描reports目录 → 加载所有JSON → 返回最新数据
```

**每次请求都会**：
1. 扫描 `reports/*.json`
2. 排除 `.progress.json` 和 `report_index.json`
3. 加载每个作者的数据
4. 返回给前端

## 性能考虑

### 优点
- ✅ 数据始终最新
- ✅ 无需重启服务器
- ✅ 支持热更新
- ✅ 代码简单，无需缓存机制

### 缺点
- ⚠️ 每次请求都扫描文件系统
- ⚠️ 报告数量多时可能有延迟

### 优化建议（如果需要）

如果报告数量超过100个，可以考虑：

1. **缓存机制**：缓存5-10秒
   ```python
   import time
   cache_timeout = 10  # 秒
   if time.time() - last_load_time < cache_timeout:
       return cached_data
   ```

2. **文件监控**：使用 `watchdog` 监控文件变化
   ```python
   from watchdog.observers import Observer
   from watchdog.events import FileSystemEventHandler
   ```

3. **增量更新**：记录文件修改时间，只重新加载变化的文件

**当前实现**：适合报告数量在50个以内的场景，性能完全够用。

## 测试验证

### 测试步骤

1. **启动服务器**
   ```bash
   C:\tools\Anaconda3\python.exe start_server.py --port 8000
   ```

2. **访问总览页面**
   ```
   http://localhost:8000
   ```
   - 查看现有报告列表

3. **生成新报告**
   - 点击"🔄 生成报告"按钮
   - 观察进度条
   - 等待生成完成

4. **验证实时加载**
   - 生成完成后页面自动刷新
   - **新报告立即出现在列表中**
   - 无需重启服务器

5. **查看日志**
   ```
   2025-12-28 HH:MM:SS - src.server - INFO - API调用：实时加载了 2 个报告
   ```
   每次API调用都会输出加载的报告数量

### 预期日志输出

```
# 启动时
2025-12-28 14:36:09 - src.server - INFO - 加载报告数据...
2025-12-28 14:36:09 - src.server - INFO - 加载报告: monge <mongezheng@gmail.com> (monge_2025.json)
2025-12-28 14:36:09 - src.server - INFO - 找到 1 个报告

# 访问页面时
2025-12-28 14:36:15 - src.server - INFO - API调用：实时加载了 1 个报告

# 生成新报告后
2025-12-28 14:38:20 - src.server - INFO - API调用：实时加载了 2 个报告
2025-12-28 14:38:20 - src.server - INFO - 加载报告: monge <mongezheng@gmail.com> (monge_2025.json)
2025-12-28 14:38:20 - src.server - INFO - 加载报告: john <john@example.com> (john_2025.json)
```

## 与之前的区别

### 之前的实现（启动时加载）

```python
def start_server(port: int = 8000, reports_dir: str = './reports'):
    # 启动时加载一次
    report_data = load_report_data(reports_path)

    def handler(*args):
        # 使用启动时加载的数据
        return ReportHTTPRequestHandler(*args, report_data=report_data)
```

**问题**：
- ❌ 生成新报告后需要重启服务器
- ❌ 数据不是最新的
- ❌ 需要手动刷新

### 现在的实现（实时加载）

```python
def send_authors_api(self):
    # 每次API调用时重新加载
    reports_dir = Path(self.directory)
    report_data = load_report_data(reports_dir)
    ...
```

**优势**：
- ✅ 无需重启服务器
- ✅ 数据始终最新
- ✅ 自动热更新

## 总结

通过将数据加载从**启动时**改为**每次请求时**，实现了：

1. **实时性**：数据始终是最新的
2. **便捷性**：生成报告后无需重启
3. **可靠性**：每次请求都获取最新状态

所有API端点和页面请求都已实现实时加载，确保用户看到的数据始终是最新的。
