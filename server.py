#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地Web服务器 - 提供报告访问服务
"""

import os
import json
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socket

import sys


class ReportHTTPRequestHandler(SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器"""

    def __init__(self, *args, report_data=None, **kwargs):
        self.report_data = report_data or {}
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # 根路径：显示总览页面（使用静态文件）
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
            self.send_author_data(author_id)
            return

        # 静态资源：CSS、JS等
        if path.startswith('/static/'):
            self.serve_static_file(path.lstrip('/'))
            return

        # 个人报告HTML文件
        if path.endswith('.html'):
            # 检查文件是否存在
            file_path = Path(self.directory) / path.lstrip('/')
            if file_path.exists():
                return super().do_GET()
            else:
                self.send_error(404, "Report not found")
                return

        # 其他请求
        return super().do_GET()

    def serve_static_file(self, relative_path):
        """提供静态文件服务"""
        # 首先尝试从static目录提供
        static_file = Path(__file__).parent / relative_path
        if static_file.exists():
            with open(static_file, 'rb') as f:
                content = f.read()

            # 确定内容类型
            content_type = 'text/html; charset=utf-8'
            if relative_path.endswith('.css'):
                content_type = 'text/css; charset=utf-8'
            elif relative_path.endswith('.js'):
                content_type = 'application/javascript; charset=utf-8'

            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404, "File not found")

    def send_overview_page(self):
        """发送总览页面"""
        html = self.generate_overview_html()

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def send_authors_api(self):
        """发送作者列表API"""
        authors = []

        for author_id, data in self.report_data.items():
            # 使用实际的报告文件名
            report_file = data.get('report_file', f"{author_id}.html")

            authors.append({
                'id': author_id,
                'name': data.get('name', 'Unknown'),
                'email': data.get('email', ''),
                'commits': data.get('commits', 0),
                'report_url': f"/{report_file}",
            })

        # 按提交数排序
        authors.sort(key=lambda x: x['commits'], reverse=True)

        response = {
            'total': len(authors),
            'authors': authors
        }

        self.send_json_response(response)

    def send_author_data(self, author_id):
        """发送特定作者的数据"""
        if author_id not in self.report_data:
            self.send_error(404, "Author not found")
            return

        author_data = self.report_data[author_id]
        self.send_json_response(author_data)

    def send_json_response(self, data):
        """发送JSON响应"""
        response = json.dumps(data, ensure_ascii=False, indent=2)

        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def generate_overview_html(self):
        """生成总览HTML页面"""
        authors = []

        for author_id, data in self.report_data.items():
            authors.append({
                'id': author_id,
                'name': data.get('name', 'Unknown'),
                'email': data.get('email', ''),
                'commits': data.get('commits', 0),
                'net_lines': data.get('net_lines', 0),
                'projects': data.get('projects', 0),
            })

        authors.sort(key=lambda x: x['commits'], reverse=True)
        total_commits = sum(a['commits'] for a in authors)

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>团队代码年度报告 - 在线查看</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            color: white;
            margin-bottom: 60px;
        }}

        .header h1 {{
            font-size: 3em;
            margin-bottom: 20px;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}

        .stat-card .value {{
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 10px;
        }}

        .stat-card .label {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .authors-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }}

        .author-card {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s, box-shadow 0.3s;
            text-decoration: none;
            color: inherit;
            display: block;
        }}

        .author-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
        }}

        .author-card h3 {{
            color: #667eea;
            font-size: 1.5em;
            margin-bottom: 15px;
        }}

        .author-card .stats {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}

        .author-card .stat {{
            display: flex;
            justify-content: space-between;
            color: #666;
        }}

        .author-card .stat .value {{
            color: #333;
            font-weight: bold;
        }}

        .author-card .view-btn {{
            margin-top: 20px;
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-radius: 10px;
            text-align: center;
            font-weight: bold;
        }}

        .search-box {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }}

        .search-box input {{
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            outline: none;
        }}

        .search-box input:focus {{
            border-color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 团队代码年度报告</h1>
            <p style="font-size: 1.2em;">在线查看系统</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="value">{len(authors)}</div>
                <div class="label">贡献者</div>
            </div>
            <div class="stat-card">
                <div class="value">{total_commits}</div>
                <div class="label">总提交次数</div>
            </div>
        </div>

        <div class="search-box">
            <input type="text" id="searchInput" placeholder="搜索作者姓名..." onkeyup="filterAuthors()">
        </div>

        <div class="authors-grid" id="authorsGrid">
"""

        for author in authors:
            safe_id = author['id'].replace('<', '').replace('>', '').replace(' ', '_')
            html += f"""
            <a href="/report/{safe_id}" class="author-card">
                <h3>{author['name']}</h3>
                <div class="stats">
                    <div class="stat">
                        <span>提交次数</span>
                        <span class="value">{author['commits']}</span>
                    </div>
                    <div class="stat">
                        <span>净增代码</span>
                        <span class="value">{author['net_lines']} 行</span>
                    </div>
                    <div class="stat">
                        <span>参与项目</span>
                        <span class="value">{author['projects']} 个</span>
                    </div>
                </div>
                <div class="view-btn">查看报告 →</div>
            </a>
"""

        html += f"""
        </div>
    </div>

    <script>
        function filterAuthors() {{
            const input = document.getElementById('searchInput');
            const filter = input.value.toLowerCase();
            const cards = document.getElementsByClassName('author-card');

            for (let card of cards) {{
                const name = card.getElementsByTagName('h3')[0].textContent.toLowerCase();
                if (name.indexOf(filter) > -1) {{
                    card.style.display = '';
                }} else {{
                    card.style.display = 'none';
                }}
            }}
        }}
    </script>
</body>
</html>
"""
        return html

    def log_message(self, format, *args):
        """自定义日志输出"""
        # 只显示重要信息
        if 'GET' in format or 'POST' in format:
            print(f"  [访问] {args[0]}")


def load_report_data(reports_dir: Path) -> dict:
    """加载报告数据"""
    report_data = {}
    index_file = reports_dir / 'report_index.json'

    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
    else:
        # 从HTML文件中提取数据
        for html_file in reports_dir.glob('*.html'):
            if html_file.name == 'index.html':
                continue

            # 从文件名提取作者名
            author_name = html_file.stem.replace('_2025', '').replace('_', ' ')

            report_data[author_name] = {
                'name': author_name,
                'report_file': html_file.name,
            }

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

    # 切换到报告目录
    reports_path = Path(reports_dir).absolute()
    if not reports_path.exists():
        print(f"错误: 报告目录不存在: {reports_path}")
        sys.exit(1)

    os.chdir(reports_path)

    # 加载报告数据
    print(f"加载报告数据...")
    report_data = load_report_data(reports_path)
    print(f"找到 {len(report_data)} 个报告")

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
