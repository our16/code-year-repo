# server.py 重构说明

## 重构目标
1. 将生成逻辑直接嵌入，不再调用外部脚本
2. 移除所有内嵌HTML内容

## 具体修改

### 1. 导入report_generator
在文件顶部添加：
```python
from report_generator import ReportGenerator
```

### 2. 重写generate_report方法
```python
def generate_report(self):
    """生成报告数据"""
    try:
        logger.info("收到生成报告请求")

        def run_generation():
            project_root = Path(__file__).parent.parent
            generator = ReportGenerator(project_root)

            def progress_callback(data):
                self.save_progress(data)

            success = generator.generate_all(progress_callback)
            logger.info(f"生成完成: {success}")

        thread = threading.Thread(target=run_generation, daemon=True)
        thread.start()

        response = {'success': True, 'message': '报告生成已启动'}
        self.send_json_response(response)

    except Exception as e:
        logger.error(f"生成失败: {str(e)}", exc_info=True)
        response = {'success': False, 'error': str(e)}
        self.send_json_response(response)
```

### 3. 移除HTML内容

#### 删除"暂无数据"页面的HTML（第281-316行）
替换为：
```python
# 没有JSON文件，显示无数据提示
author_name = author_info.get('name', 'Unknown')
self.redirect(f'/static/no-data.html?author={author_name}')
```

#### 删除generate_embedded_report方法（第364-443行）
这个方法生成内嵌HTML，完全移除，改用模板

### 4. 修改render_report_html方法
```python
def render_report_html(self, data: dict) -> str:
    """渲染报告HTML页面"""
    project_root = Path(__file__).parent.parent
    template_path = project_root / 'templates' / 'report.html'

    if not template_path.exists():
        # 返回简单提示
        return f"<html><body><h1>模板不存在</h1></body></html>"

    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # 模板替换
    return template.replace('{{ data_json }}', json.dumps(data, ensure_ascii=False))
```

## 优势
1. 代码更简洁
2. 不依赖外部脚本
3. 所有HTML在templates目录
4. 更好的可维护性
