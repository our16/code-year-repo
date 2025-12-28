#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地Web服务器 - 提供报告访问服务
功能：读取JSON数据，通过API和前端页面展示
"""

import os
import json
import logging
import socket
import sys
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 导入日志配置和报告生成器
from logger_config import get_logger
from report_generator import ReportGenerator

logger = get_logger(__name__)


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
            from urllib.parse import unquote
            author_id = unquote(author_id)
            self.serve_author_report(author_id)
            return

        # 其他请求：尝试从静态目录提供
        self.serve_static_file(path.lstrip('/'))

    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # API：生成报告
        if path == '/api/generate':
            self.generate_report()
            return

        # API：发送报告链接
        if path == '/api/send-reports':
            self.send_reports()
            return

    def send_reports(self):
        """发送报告链接API - 预留接口，目前只打印日志"""
        try:
            # 读取请求数据
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))
            else:
                request_data = {}

            authors = request_data.get('authors', [])
            timestamp = request_data.get('timestamp', '')

            logger.info("=" * 60)
            logger.info("📤 发送报告链接请求")
            logger.info("=" * 60)
            logger.info(f"发送时间: {timestamp}")
            logger.info(f"发送数量: {len(authors)}")
            logger.info(f"接收者列表:")

            for idx, author in enumerate(authors, 1):
                logger.info(f"  {idx}. {author.get('name', 'Unknown')}")
                logger.info(f"     ID: {author.get('id', 'N/A')}")
                logger.info(f"     报告链接: {author.get('reportUrl', 'N/A')}")

            logger.info("=" * 60)
            logger.info("💡 提示: 您可以在这里接入消息发送工具")
            logger.info("   支持的工具: 钉钉机器人、企业微信、飞书、Slack等")
            logger.info("=" * 60)

            # 预留接口：未来可以在这里接入实际的发送逻辑
            # 例如：
            # - 钉钉机器人 webhook
            # - 企业微信应用消息
            # - 邮件发送
            # - 短信通知

            response = {
                'success': True,
                'message': f'已记录 {len(authors)} 份报告的发送信息',
                'authors_count': len(authors),
                'timestamp': timestamp
            }

        except Exception as e:
            logger.error(f"发送报告失败: {str(e)}", exc_info=True)
            response = {
                'success': False,
                'error': str(e)
            }

        self.send_json_response(response)

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
        """发送作者列表API - 实时加载报告数据"""
        # 实时重新加载报告数据
        reports_dir = Path(self.directory)
        report_data = load_report_data(reports_dir)
        # logger.info(f"API调用：实时加载了 {len(report_data)} 个报告")

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
        """发送生成进度API - 实时加载"""
        # 读取进度文件（如果存在）
        project_root = Path(__file__).parent.parent
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

    def generate_report(self):
        """生成报告数据 - 直接嵌入逻辑"""
        try:
            logger.info("收到生成报告请求")

            def run_generation():
                project_root = Path(__file__).parent.parent
                generator = ReportGenerator(project_root)

                def progress_callback(data):
                    """进度回调"""
                    logger.info(f"进度: {data['current']} - {data['percentage']}%")
                    # 进度会自动保存到文件

                success = generator.generate_all(progress_callback)
                logger.info(f"生成完成: {'成功' if success else '失败'}")

            # 启动后台线程
            thread = threading.Thread(target=run_generation, daemon=True)
            thread.start()

            # 返回成功响应
            response = {
                'success': True,
                'message': '报告生成已启动，请稍后刷新页面查看结果'
            }
            self.send_json_response(response)
            logger.info("生成报告请求已处理")

        except Exception as e:
            logger.error(f"生成报告失败: {str(e)}", exc_info=True)
            response = {
                'success': False,
                'error': str(e)
            }
            self.send_json_response(response)

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

        if not author_info:
            self.send_error(404, "Author not found")
            return

        # 查找JSON文件
        json_file = author_info.get('json_file')

        if json_file:
            json_path = Path(self.directory) / json_file
            if json_path.exists():
                # 读取JSON数据并渲染
                with open(json_path, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                html = self.render_report_html(report_data)
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
                return

        # 没有JSON文件，显示无数据提示页面
        author_name = author_info.get('name', 'Unknown')
        # 使用302重定向到静态HTML页面
        self.send_response(302)
        self.send_header('Location', f'/static/no-data.html?author={author_name}')
        self.end_headers()

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

        # 将JSON数据直接输出到script标签中（作为textContent）
        # 不需要转义，因为不是JavaScript字符串字面量
        json_str = json.dumps(data, ensure_ascii=False, indent=2)

        html = template.replace('{{ data_json | default(\'{}\') }}', json_str)
        html = html.replace('{{ data_json }}', json_str)
        html = html.replace('{{ primary_color | default(\'#667eea\') }}', primary_color)
        html = html.replace('{{ primary_color }}', primary_color)
        html = html.replace('{{ secondary_color | default(\'#764ba2\') }}', secondary_color)
        html = html.replace('{{ secondary_color }}', secondary_color)
        html = html.replace('{{ accent_color | default(\'#f093fb\') }}', accent_color)
        html = html.replace('{{ accent_color }}', accent_color)
        html = html.replace('{{ year }}', str(data.get('year', 2024)))

        # AI文案 - 需要处理 markdown
        ai_text = data.get('ai_text', None)
        if ai_text:
            # 将markdown转换为HTML（简单处理）
            import re
            # 转换换行
            ai_text_html = ai_text.replace('\n\n', '</p><p>').replace('\n', '<br>')
            ai_text_html = f'<p>{ai_text_html}</p>'
            # 处理标题
            ai_text_html = re.sub(r'<p># (.*?)</p>', r'<h3>\1</h3>', ai_text_html)
            ai_text_html = re.sub(r'<p>## (.*?)</p>', r'<h4>\1</h4>', ai_text_html)
            ai_text_html = re.sub(r'<p>### (.*?)</p>', r'<h5>\1</h5>', ai_text_html)
        else:
            # 使用默认文案
            ai_text_html = self._get_default_ai_text(data)

        html = html.replace('{{ ai_text | safe }}', ai_text_html)
        html = html.replace('{{ ai_text }}', ai_text_html)

        return html

    def _get_default_ai_text(self, data: dict) -> str:
        """生成默认AI文案"""
        summary = data.get('summary', {})
        languages = data.get('languages', {})
        projects = data.get('projects', [])

        top_lang = languages.get('top_languages', [])[:3]
        lang_names = [l['name'] for l in top_lang] if top_lang else ['多种语言']

        project_count = len(projects)
        top_project = projects[0] if projects else {}

        text = f"""
        <h3>💌 致过去的一年：你的代码，你的诗篇</h3>

        <p>在冰冷的数字背后，是你一整年的热忱、思考和创造。</p>

        <h4>年初的Flag，是写在晨光里的序章</h4>

        <p>每一个早起的清晨，每一个静谧的深夜，键盘敲击出的不只是代码，更是你解决问题的决心。那些 <strong>{summary.get('total_commits', 0)}</strong> 次的提交，是你与复杂问题一次次交锋的勋章。新增的 <strong>{summary.get('total_additions', 0)}</strong> 行代码，构筑起产品的血肉；而删除的 <strong>{summary.get('total_deletions', 0)}</strong> 行，更是你追求优雅与简洁的证明。</p>

        <h4>你的技术栈，是你探索世界的地图</h4>

        <p>这一年，你在 <strong>{', '.join(lang_names)}</strong> 的世界里探索。参与 <strong>{project_count}</strong> 个不同项目的经历，证明你不仅是深耕某一领域的专家，更是具备全局视野的团队协作者。在 <strong>{top_project.get('name', '核心项目')}</strong> 中的 <strong>{top_project.get('commits', 0)}</strong> 次提交，记录了你在这个项目上的深度投入。</p>

        <h4>精简的艺术</h4>

        <p>特别值得一提的是，你的重构提交展现了你对代码质量的追求和对系统可持续性的思考。</p>

        <p><em>继续用代码书写你的故事吧！</em></p>
        """
        return text

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
        """自定义日志输出 - 使用logger"""
        # 使用logger记录访问日志
        if 'GET' in format or 'POST' in format:
            logger.info(f"[访问] {args[0] if args else format}")


def load_report_data(reports_dir: Path) -> dict:
    """加载报告索引数据 - 扫描所有作者JSON文件"""
    report_data = {}

    # 排除的文件：进度文件和索引文件
    excluded_files = {'.progress.json', 'report_index.json'}

    # 扫描所有JSON文件
    for json_file in reports_dir.glob('*.json'):
        # 跳过排除的文件
        if json_file.name in excluded_files:
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
                # logger.info(f"加载报告: {author_id} ({json_file.name})")
        except Exception as e:
            logger.warning(f"无法读取 {json_file.name}: {str(e)}")

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
        logger.error(f"报告目录不存在: {reports_path}")
        sys.exit(1)

    logger.info(f"报告目录: {reports_path}")

    # 加载报告数据
    logger.info("加载报告数据...")
    report_data = load_report_data(reports_path)
    logger.info(f"找到 {len(report_data)} 个报告")

    if not report_data:
        logger.warning("没有找到任何报告数据，请通过Web界面生成报告")
        # 不退出，继续启动服务器

    # 创建请求处理器
    def handler(*args):
        return ReportHTTPRequestHandler(*args, report_data=report_data, directory=str(reports_path))

    # 启动服务器
    server_address = ('', port)
    httpd = HTTPServer(server_address, handler)

    local_ip = get_local_ip()

    logger.info("=" * 60)
    logger.info("Web服务器已启动")
    logger.info("=" * 60)
    logger.info(f"本地访问: http://localhost:{port}")
    logger.info(f"网络访问: http://{local_ip}:{port}")
    logger.info(f"报告目录: {reports_path}")
    logger.info("API端点:")
    logger.info("  GET /api/authors - 获取作者列表")
    logger.info("  GET /api/author/<id> - 获取特定作者数据")
    logger.info("  GET /api/progress - 获取生成进度")
    logger.info("  POST /api/generate - 生成报告数据")
    logger.info("  GET /report/<id> - 查看个人报告页面")
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
