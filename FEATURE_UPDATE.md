# 功能更新总结

## 新增功能

### 1. 生成报告按钮
- 在总览页面顶部添加"🔄 生成报告"按钮
- 点击后调用 `/api/generate` API
- 按钮在生成过程中会显示"⏳ 生成中..."并禁用

### 2. 报告生成API
**端点**: `POST /api/generate`

功能：
- 在后台运行生成脚本 `src/generate_reports.py`
- 实时更新进度文件 `reports/.progress.json`
- 返回生成状态消息

### 3. 进度跟踪
- 自动轮询 `/api/progress` 接口
- 显示实时进度条
- 完成后3秒自动刷新页面

### 4. 生成脚本
**文件**: `src/generate_reports.py`

功能：
- 扫描Git仓库
- 应用作者映射
- 为每个作者生成JSON文件
- 更新报告索引
- 实时保存进度

### 5. 优化报告页面
- 移除"返回首页"链接
- 适合直接分享给他人查看
- 无数据时显示友好提示

## 使用流程

### 生成报告
1. 访问 `http://localhost:8000`
2. 点击"🔄 生成报告"按钮
3. 等待进度条完成
4. 页面自动刷新，显示生成的报告

### 查看报告
- 点击作者卡片查看个人报告
- 报告URL可以直接分享给他人
- 无需返回首页，适合独立查看

## 技术细节

### API接口
- `GET /api/authors` - 获取作者列表
- `GET /api/author/<id>` - 获取作者数据
- `GET /api/progress` - 获取生成进度
- `POST /api/generate` - 生成报告

### 进度文件
- 位置: `reports/.progress.json`
- 格式:
  ```json
  {
    "status": "generating",
    "total": 10,
    "completed": 5,
    "current": "正在分析 xxx",
    "percentage": 50.0
  }
  ```

### 生成的文件
- `reports/<author>_<year>.json` - 作者报告数据
- `reports/report_index.json` - 报告索引

## 配置要求

确保 `config/config.yaml` 配置正确：
- 项目路径
- 年份设置
- 作者筛选（可选）
- LLM配置（可选）
