# 报告页面显示优化

## 问题描述

用户反馈两个问题：

1. **编程语言分布没有展示数据**
   - `languages.top_languages` 为空数组
   - 页面显示"暂无数据"

2. **提交热力图只显示几个点**
   - 只显示有提交的日期
   - 需要显示完整的365天，并标记有提交的天

## 根本原因分析

### 问题1：编程语言数据缺失

**原因排查**：
1. `git_collector.py` 已经收集 `language_stats`
2. `data_analyzer.py` 正确聚合了语言统计
3. 但实际数据中 `language_stats` 为空：`{"total": 0, "top_languages": []}`

**可能原因**：
- Git仓库中的提交可能没有文件变更信息
- 或者文件检测逻辑没有正确执行
- 需要检查实际的Git日志

### 问题2：热力图不完整

**原始实现**：
```python
def _generate_calendar_heatmap(self, commits: List[Dict]) -> List[Dict]:
    heatmap = defaultdict(int)
    for commit in commits:
        date = commit['date'][:10]
        heatmap[date] += 1

    # 只返回有提交的日期
    result = []
    for date, count in sorted(heatmap.items()):
        result.append({'date': date, 'count': count, 'level': self._get_heatmap_level(count)})
    return result
```

**问题**：
- 只包含有提交的日期
- 大部分日期缺失，无法看到完整的年度概览
- 热力图效果不好

## 修复方案

### 修复1：完整365天热力图

**文件**: [src/data_analyzer.py:135-161](../src/data_analyzer.py#L135-L161)

**修改后**:
```python
def _generate_calendar_heatmap(self, commits: List[Dict]) -> List[Dict]:
    """生成完整的365天日历热力图数据"""
    from datetime import date, timedelta

    # 统计每天的提交数
    heatmap_dict = defaultdict(int)
    for commit in commits:
        date_str = commit['date'][:10]  # YYYY-MM-DD
        heatmap_dict[date_str] += 1

    # 生成完整的365天数据
    start_date = date(self.report_year, 1, 1)
    end_date = date(self.report_year, 12, 31)

    result = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.isoformat()
        count = heatmap_dict.get(date_str, 0)  # 没有提交的日期count=0
        result.append({
            'date': date_str,
            'count': count,
            'level': self._get_heatmap_level(count)  # level=0 for no commits
        })
        current_date += timedelta(days=1)

    return result
```

**改进**：
- ✅ 生成完整的365天数据
- ✅ 没有提交的日期 `count=0`, `level=0`
- ✅ 有提交的日期正常显示
- ✅ 热力图完整显示全年

### 修复2：语言统计调试

**数据流分析**：
1. `git_collector.py` 收集每个项目的 `language_stats`
2. `data_analyzer.py` 聚合所有项目的语言统计
3. 生成 `languages.top_languages`

**验证方法**：
```python
# 在 git_collector.py 中添加日志
logger.info(f"项目 {project_name} 语言统计: {dict(language_stats)}")

# 在 data_analyzer.py 中添加日志
logger.info(f"聚合语言统计: {dict(language_stats)}")
logger.info(f"分析结果: {language_analysis}")
```

## 数据结构

### 热力图数据结构

```json
{
  "time_distribution": {
    "calendar_heatmap": [
      {
        "date": "2025-01-01",
        "count": 0,
        "level": 0
      },
      {
        "date": "2025-01-02",
        "count": 0,
        "level": 0
      },
      {
        "date": "2025-10-13",
        "count": 5,
        "level": 2
      },
      {
        "date": "2025-10-18",
        "count": 21,
        "level": 4
      },
      ...
      // 共365天
    ]
  }
}
```

### 热力图等级定义

```python
def _get_heatmap_level(self, count: int) -> int:
    """计算热力图等级 (0-4)"""
    if count == 0:
        return 0      # 无提交
    elif count <= 2:
        return 1      # 1-2次提交
    elif count <= 5:
        return 2      # 3-5次提交
    elif count <= 10:
        return 3      # 6-10次提交
    else:
        return 4      # 10+次提交
```

### 语言数据结构

```json
{
  "languages": {
    "total": 150,
    "top_languages": [
      {
        "name": "Python",
        "count": 100,
        "percentage": 66.7
      },
      {
        "name": "JavaScript",
        "count": 30,
        "percentage": 20.0
      },
      {
        "name": "HTML",
        "count": 20,
        "percentage": 13.3
      }
    ],
    "distribution": {
      "Python": 66.7,
      "JavaScript": 20.0,
      "HTML": 13.3
    }
  }
}
```

## 前端显示

### 热力图渲染

**文件**: [templates/report.html:365-371](../templates/report.html#L365-L371)

```html
<!-- Calendar Heatmap -->
<div class="chart-section">
    <h2>📅 提交热力图</h2>
    <div class="heatmap" id="heatmap">
        <div class="loading">加载中...</div>
    </div>
</div>
```

**JavaScript渲染**:
```javascript
function initHeatmap() {
    const timeDist = data.time_distribution || {};
    const heatmapData = timeDist.calendar_heatmap || [];

    const container = document.getElementById('heatmap');

    if (heatmapData.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">暂无数据</p>';
        return;
    }

    // 渲染365天的热力图
    container.innerHTML = heatmapData.map(cell => `
        <div class="heatmap-cell level-${cell.level}"
             title="${cell.date}: ${cell.count} 次提交">
        </div>
    `).join('');
}
```

**CSS样式**:
```css
.heatmap {
    display: grid;
    grid-template-columns: repeat(53, 1fr);  /* 53列（约53周）*/
    gap: 3px;
    margin-top: 20px;
}

.heatmap-cell {
    aspect-ratio: 1;
    border-radius: 2px;
    transition: transform 0.2s;
    cursor: pointer;
}

.heatmap-cell:hover {
    transform: scale(1.3);
}

/* 等级颜色 */
.heatmap-cell.level-0 { background: rgba(255, 255, 255, 0.05); }
.heatmap-cell.level-1 { background: rgba(102, 126, 234, 0.3); }
.heatmap-cell.level-2 { background: rgba(102, 126, 234, 0.5); }
.heatmap-cell.level-3 { background: rgba(102, 126, 234, 0.7); }
.heatmap-cell.level-4 { background: rgba(102, 126, 234, 1); }
```

### 语言列表渲染

**JavaScript**:
```javascript
function initLanguages() {
    const languages = data.languages || {};
    const topLanguages = languages.top_languages || [];

    const container = document.getElementById('language-list');
    container.innerHTML = topLanguages.map(lang => `
        <div class="language-tag">
            <span>${lang.name}</span>
            <span class="percentage">${lang.percentage}%</span>
        </div>
    `).join('');

    if (topLanguages.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">暂无数据</p>';
    }
}
```

## 测试验证

### 测试步骤

1. **重新生成报告**
   ```bash
   C:\tools\Anaconda3\python.exe src/generate_reports.py
   ```

2. **检查JSON数据**
   ```bash
   cat reports/monge_2025.json | grep -A 5 "calendar_heatmap"
   cat reports/monge_2025.json | grep -A 10 "top_languages"
   ```

3. **访问报告页面**
   ```
   http://localhost:8000/report/monge%20%3Cmongezheng@gmail.com%3E
   ```

### 预期结果

#### 热力图
- ✅ 显示完整的365天（53列 x 7行）
- ✅ 无提交的天显示为半透明白色（level-0）
- ✅ 有提交的天显示不同深度的紫色（level-1到4）
- ✅ 鼠标悬停显示日期和提交次数

#### 语言分布
- ✅ 如果有语言数据，显示语言标签
- ✅ 如果没有数据，显示"暂无数据"

## 语言数据调试

### 检查语言收集

如果语言数据仍然为空，检查以下几点：

1. **Git仓库是否有文件变更**
   ```bash
   cd /path/to/repo
   git log --name-only --oneline | head -20
   ```

2. **文件扩展名是否被识别**
   - 检查 `_detect_language` 方法的扩展名映射
   - 添加更多扩展名

3. **添加调试日志**
   在 `git_collector.py` 的收集循环中：
   ```python
   if file_path:
       lang = self._detect_language(file_path)
       language_stats[lang] += 1
       logger.debug(f"文件: {file_path}, 语言: {lang}")
   ```

### 手动添加语言统计

如果Git收集不到语言数据，可以手动配置：

**config/config.yaml**:
```yaml
projects:
  - path: "F:/project/my-repo"
    name: "My Project"
    language: "Python"  # 手动指定主要语言
```

然后在 `data_analyzer.py` 中使用这个配置。

## 性能考虑

### 数据量

- **热力图数据**: 365条记录 × 3个字段 ≈ 10KB
- **JSON大小**: 可控，不影响性能

### 渲染性能

- **DOM节点**: 365个div
- **浏览器渲染**: 流畅，现代浏览器可轻松处理
- **优化建议**:
  - 使用 `requestAnimationFrame` 分批渲染
  - 使用虚拟滚动（如果需要）

## 后续优化建议

### 1. 热力图交互

- 点击日期查看该日的所有提交
- 筛选特定月份
- 导出热力图为图片

### 2. 语言可视化

- 饼图显示语言占比
- 按项目分组显示语言
- 语言使用趋势图

### 3. 数据缓存

- 缓存热力图渲染结果
- 避免重复计算

## 总结

### 修复内容

1. ✅ **完整365天热力图** - 从只有几个点改为完整的年度视图
2. ✅ **语言统计准备** - 数据收集逻辑已就绪，等待实际数据验证

### 文件变更

- [src/data_analyzer.py:135-161](../src/data_analyzer.py#L135-L161) - 热力图生成逻辑

### 测试状态

- ⏳ 需要重新生成报告以验证语言统计
- ✅ 热力图逻辑已修复，等待数据验证

### 下一步

1. 重新生成报告查看热力图效果
2. 检查语言统计数据
3. 如语言数据仍为空，需要调试Git收集逻辑
