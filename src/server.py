#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地Web服务器 - 提供报告访问服务
功能：读取JSON数据，通过API和前端页面展示
"""

import os
import json
import socket
import sys
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


class ReportHTTPRequestHandler(SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器"""

    def __init__(self, *args, report_data=None, **kwargs):
        self.report_data = report_data or {}
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)

        # 根路径：显示总览页面
        if path == '/' or path == '/index.html':
            self.serve_static_file('static/overview.html')
            return

        # API：获取作者列表
        if path == '/api/authors':
            self.send_authors_api()
            return

        # API：获取特定作者的数据
        if path.startswith('/api/author/'):
            author_id = path.split('/')[-1]
            # URL解码
            author_id = author_id.replace('%20', ' ').replace('%3C', '<').replace('%3E', '>').replace('%40', '@')
            self.send_author_data(author_id)
            return

        # API：获取生成进度
        if path == '/api/progress':
            self.send_progress_api()
            return

        # 静态资源：CSS、JS等
        if path.startswith('/static/'):
            self.serve_static_file(path.lstrip('/'))
            return

        # 个人报告页面（渲染HTML）
        if path.startswith('/report/'):
            author_id = path.split('/')[-1]
            # URL解码
            author_id = author_id.replace('%20', ' ').replace('%3C', '<').replace('%3E', '>').replace('%40', '@')
            self.serve_author_report(author_id)
            return

        # 其他请求：尝试从静态目录提供
        self.serve_static_file(path.lstrip('/'))

    def serve_static_file(self, relative_path):
        """提供静态文件服务"""
        # 首先尝试从项目根目录的static目录提供
        project_root = Path(__file__).parent.parent
        static_file = project_root / relative_path
        if static_file.exists() and static_file.is_file():
            with open(static_file, 'rb') as f:
                content = f.read()

            # 确定内容类型
            content_type = 'text/html; charset=utf-8'
            if relative_path.endswith('.css'):
                content_type = 'text/css; charset=utf-8'
            elif relative_path.endswith('.js'):
                content_type = 'application/javascript; charset=utf-8'
            elif relative_path.endswith('.json'):
                content_type = 'application/json; charset=utf-8'
            elif relative_path.endswith('.png'):
                content_type = 'image/png'
            elif relative_path.endswith('.jpg') or relative_path.endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif relative_path.endswith('.svg'):
                content_type = 'image/svg+xml'

            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404, "File not found")

    def send_authors_api(self):
        """发送作者列表API"""
        authors = []

        for author_id, data in self.report_data.items():
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

    def send_author_data(self, author_id):
        """发送特定作者的JSON数据"""
        # 查找作者的JSON文件
        author_info = None
        for aid, data in self.report_data.items():
            if aid == author_id or data.get('name') == author_id:
                author_info = data
                break

        if not author_info:
            self.send_error(404, "Author not found")
            return

        # 读取完整的JSON文件
        json_file = author_info.get('json_file')
        if not json_file:
            self.send_error(404, "Report file not found")
            return

        json_path = Path(self.directory) / json_file
        if not json_path.exists():
            self.send_error(404, "JSON file not found")
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        self.send_json_response(report_data)

    def send_progress_api(self):
        """发送生成进度API（静态数据，实际应从进度文件读取）"""
        response = {
            'status': 'completed',
            'total': len(self.report_data),
            'completed': len(self.report_data),
            'current': 'All reports generated',
            'percentage': 100
        }
        self.send_json_response(response)

    def serve_author_report(self, author_id):
        """提供个人报告页面"""
        # 查找作者信息
        author_info = None
        for aid, data in self.report_data.items():
            if aid == author_id or data.get('name') == author_id:
                author_info = data
                break

        if not author_info:
            self.send_error(404, "Author not found")
            return

        # 读取JSON数据
        json_file = author_info.get('json_file')
        if not json_file:
            self.send_error(404, "Report file not found")
            return

        json_path = Path(self.directory) / json_file
        if not json_path.exists():
            self.send_error(404, "JSON file not found")
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        # 渲染HTML模板
        html = self.render_report_html(report_data)

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def render_report_html(self, data: dict) -> str:
        """渲染报告HTML页面"""
        # 读取模板（从项目根目录）
        project_root = Path(__file__).parent.parent
        template_path = project_root / 'templates' / 'report.html'
        if not template_path.exists():
            # 如果模板不存在，使用内嵌模板
            return self.generate_embedded_report(data)

        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # 简单的模板替换
        theme = data.get('theme', {})
        primary_color = theme.get('primary_color', '#667eea')
        secondary_color = theme.get('secondary_color', '#764ba2')
        accent_color = theme.get('accent_color', '#f093fb')

        html = template.replace('{{ data_json }}', json.dumps(data, ensure_ascii=False))
        html = html.replace('{{ primary_color }}', primary_color)
        html = html.replace('{{ secondary_color }}', secondary_color)
        html = html.replace('{{ accent_color }}', accent_color)
        html = html.replace('{{ year }}', str(data.get('year', 2024)))

        # AI文案
        ai_text = data.get('ai_text') or '暂无AI文案'
        html = html.replace('{{ ai_text }}', ai_text)

        return html

    def generate_embedded_report(self, data: dict) -> str:
        """生成内嵌的HTML报告"""
        theme = data.get('theme', {})
        primary_color = theme.get('primary_color', '#667eea')
        secondary_color = theme.get('secondary_color', '#764ba2')

        summary = data.get('summary', {})
        languages = data.get('languages', {})
        projects = data.get('projects', [])

        top_languages = languages.get('top_languages', [])[:5]

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代码年度报告 - {data.get('year', 2024)}</title>
    <style>
        :root {{
            --primary-color: {primary_color};
            --secondary-color: {secondary_color};
            --bg-color: #0f0f1e;
            --card-bg: rgba(255, 255, 255, 0.05);
            --text-primary: #ffffff;
            --text-secondary: #a0a0b0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .hero {{
            text-align: center;
            padding: 80px 20px;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border-radius: 20px;
            margin-bottom: 60px;
        }}
        .hero h1 {{
            font-size: 3em;
            margin-bottom: 20px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
            margin-bottom: 60px;
        }}
        .stat-card {{
            background: var(--card-bg);
            border-radius: 15px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .stat-card h3 {{
            color: var(--text-secondary);
            margin-bottom: 15px;
        }}
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .chart-section {{
            background: var(--card-bg);
            border-radius: 15px;
            padding: 40px;
            margin-bottom: 40px;
        }}
        .chart-section h2 {{
            margin-bottom: 30px;
        }}
        .language-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
        }}
        .language-tag {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            padding: 10px 20px;
            border-radius: 20px;
        }}
        .project-item {{
            background: rgba(255, 255, 255, 0.03);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>🎨 你的代码年度报告</h1>
            <p>{data.get('year', 2024)}年度回顾</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>总提交次数</h3>
                <div class="value">{summary.get('total_commits', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>净增代码行</h3>
                <div class="value">{summary.get('net_lines', 0)}</div>
            </div>
            <div class="stat-card">
                <h3>参与项目</h3>
                <div class="value">{len(projects)}</div>
            </div>
        </div>

        <div class="chart-section">
            <h2>💻 编程语言分布</h2>
            <div class="language-list">
                {"".join(f'<div class="language-tag">{lang["name"]} ({lang["percentage"]}%)</div>' for lang in top_languages)}
            </div>
        </div>

        <div class="chart-section">
            <h2>🚀 项目贡献</h2>
            {"".join(f'<div class="project-item"><h4>{p["name"]}</h4><p>{p["commits"]} 次提交, {p["net_lines"]} 行净增</p></div>' for p in projects[:5])}
        </div>
    </div>
</body>
</html>
"""

    def send_json_response(self, data):
        """发送JSON响应"""
        response = json.dumps(data, ensure_ascii=False, indent=2)

        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def log_message(self, format, *args):
        """自定义日志输出"""
        # 只显示重要信息
        if 'GET' in format or 'POST' in format:
            print(f"  [访问] {args[0]}")


def load_report_data(reports_dir: Path) -> dict:
    """加载报告索引数据"""
    report_data = {}
    index_file = reports_dir / 'report_index.json'

    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
    else:
        # 如果没有索引文件，扫描JSON文件
        for json_file in reports_dir.glob('*.json'):
            if json_file.name == 'report_index.json':
                continue

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    meta = data.get('meta', {})
                    author_id = meta.get('author_id', meta.get('author', json_file.stem))

                    report_data[author_id] = {
                        'id': author_id,
                        'name': meta.get('author', 'Unknown'),
                        'email': meta.get('email', ''),
                        'commits': data.get('summary', {}).get('total_commits', 0),
                        'net_lines': data.get('summary', {}).get('net_lines', 0),
                        'projects': len(data.get('projects', [])),
                        'json_file': json_file.name,
                    }
            except Exception as e:
                print(f"警告: 无法读取 {json_file.name}: {str(e)}")

    return report_data


def get_local_ip():
    """获取本机IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def start_server(port: int = 8000, reports_dir: str = './reports'):
    """启动Web服务器"""

    # 获取报告目录（不切换当前目录）
    reports_path = Path(reports_dir).absolute()
    if not reports_path.exists():
        print(f"错误: 报告目录不存在: {reports_path}")
        sys.exit(1)

    # 加载报告数据
    print(f"加载报告数据...")
    report_data = load_report_data(reports_path)
    print(f"找到 {len(report_data)} 个报告")

    if not report_data:
        print("\n警告: 没有找到任何报告数据")
        print("请通过Web界面生成报告")
        # 不退出，继续启动服务器

    # 创建请求处理器
    def handler(*args):
        return ReportHTTPRequestHandler(*args, report_data=report_data, directory=str(reports_path))

    # 启动服务器
    server_address = ('', port)
    httpd = HTTPServer(server_address, handler)

    local_ip = get_local_ip()

    print("\n" + "=" * 60)
    print("Web服务器已启动！")
    print("=" * 60)
    print(f"\n访问地址:")
    print(f"  本地访问: http://localhost:{port}")
    print(f"  网络访问: http://{local_ip}:{port}")
    print(f"\n报告目录: {reports_path}")
    print(f"\nAPI端点:")
    print(f"  GET /api/authors - 获取作者列表")
    print(f"  GET /api/author/<id> - 获取特定作者数据")
    print(f"  GET /report/<id> - 查看个人报告页面")
    print(f"\n按 Ctrl+C 停止服务器\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
        httpd.server_close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='报告Web服务器')
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='端口号 (默认: 8000)'
    )
    parser.add_argument(
        '--dir',
        default='./reports',
        help='报告目录 (默认: ./reports)'
    )

    args = parser.parse_args()

    start_server(port=args.port, reports_dir=args.dir)
