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
import uuid
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 导入日志配置和报告生成器
from logger_config import get_logger
from report_generator import ReportGenerator

logger = get_logger(__name__)

# 会话存储（生产环境应使用Redis等）
SESSION_STORE = {}
SESSION_TIMEOUT = 3600 * 24  # 24小时


class ReportHTTPRequestHandler(SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器"""

    def __init__(self, *args, report_data=None, **kwargs):
        self.report_data = report_data or {}
        super().__init__(*args, **kwargs)

    def create_session(self, username):
        """创建会话"""
        session_id = str(uuid.uuid4())
        expiry_time = datetime.now() + timedelta(seconds=SESSION_TIMEOUT)

        SESSION_STORE[session_id] = {
            'username': username,
            'created_at': datetime.now(),
            'expiry_time': expiry_time
        }

        logger.info(f"创建会话: {username} - {session_id}")
        return session_id

    def validate_session(self, session_id):
        """验证会话"""
        if not session_id or session_id not in SESSION_STORE:
            return False

        session = SESSION_STORE[session_id]

        # 检查是否过期
        if datetime.now() > session['expiry_time']:
            del SESSION_STORE[session_id]
            logger.info(f"会话已过期: {session_id}")
            return False

        # 更新过期时间
        session['expiry_time'] = datetime.now() + timedelta(seconds=SESSION_TIMEOUT)
        return True

    def check_session(self):
        """检查请求的会话"""
        # 从Cookie中获取sessionId
        cookie_header = self.headers.get('Cookie')
        if not cookie_header:
            return False

        # 解析Cookie
        cookies = {}
        for cookie in cookie_header.split(';'):
            cookie = cookie.strip()
            if '=' in cookie:
                key, value = cookie.split('=', 1)
                cookies[key.strip()] = value.strip()

        session_id = cookies.get('sessionId')
        return self.validate_session(session_id)

    def require_login(self):
        """要求登录，返回False表示需要重定向到登录页"""
        # 如果是report路径，不需要登录
        if self.path.startswith('/report/'):
            return True

        # 检查会话
        return self.check_session()

    def check_admin_auth(self):
        """检查admin认证"""
        # 获取Authorization头
        auth_header = self.headers.get('Authorization')

        if not auth_header:
            return False

        # 检查Basic Auth
        if auth_header.startswith('Basic '):
            import base64
            try:
                # 解码base64
                encoded = auth_header.split(' ')[1]
                decoded = base64.b64decode(encoded).decode('utf-8')
                username, password = decoded.split(':', 1)

                # 从配置文件读取admin账号密码
                from pathlib import Path
                config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
                if config_path.exists():
                    import yaml
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)

                    admin_config = config.get('admin', {})
                    admin_username = admin_config.get('username', 'admin')
                    admin_password = admin_config.get('password', 'admin')

                    return username == admin_username and password == admin_password
            except Exception as e:
                logger.warning(f"认证检查失败: {e}")

        return False

    def is_referer_from_report(self):
        """检查请求是否来自report页面"""
        referer = self.headers.get('Referer')

        if not referer:
            return False

        # 检查referer是否包含/report/
        return '/report/' in referer

    def can_access_without_auth(self, path):
        """判断是否可以在无认证的情况下访问"""
        # 报告页面本身不需要认证
        if path.startswith('/report/'):
            return True

        # 如果请求来自report页面，允许访问静态资源
        if self.is_referer_from_report():
            # 静态资源（CSS, JS, favicon等）
            if path.startswith('/static/'):
                return True
            # 模板文件
            if path.startswith('/templates/'):
                return True

        return False

    def send_auth_required(self):
        """发送需要认证的响应"""
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Code Report Admin"')
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html_content = """
<html>
<head><title>401 Unauthorized</title></head>
<body>
<h1>401 Unauthorized</h1>
<p>需要管理员权限访问此页面</p>
</body>
</html>
        """.encode('utf-8')
        self.wfile.write(html_content)

    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)

        # 登录页面不需要认证
        if path == '/login' or path == '/login.html':
            self.serve_static_file('static/login.html')
            return

        # 检查登录态（除了report路径和静态资源）
        if not self.require_login():
            # 未登录，重定向到登录页
            self.send_response(302)
            redirect_url = f'/login?redirect={path}'
            self.send_header('Location', redirect_url)
            self.end_headers()
            return

        # 根路径 - 重定向到总览页
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

        # API：获取系统状态
        if path == '/api/system-status':
            self.send_system_status_api()
            return

        # 静态资源：CSS、JS等
        if path.startswith('/static/'):
            self.serve_static_file(path.lstrip('/'))
            return

        # 个人报告页面（渲染HTML）- 不需要登录
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

        # 登录API不需要认证
        if path == '/api/login':
            self.handle_login()
            return

        # 验证会话API不需要认证
        if path == '/api/validate-session':
            self.handle_validate_session()
            return

        # 其他POST请求需要登录
        if not self.require_login():
            self.send_json_response({
                'success': False,
                'message': '请先登录'
            })
            return

        # API：生成报告
        if path == '/api/generate':
            self.generate_report()
            return

        # API：完全重跑
        if path == '/api/completely-rerun':
            self.completely_rerun()
            return

        # API：发送报告链接
        if path == '/api/send-reports':
            self.send_reports()
            return

    def handle_login(self):
        """处理登录请求"""
        try:
            # 读取请求数据
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))
            else:
                request_data = {}

            username = request_data.get('username', '')
            password = request_data.get('password', '')

            # 从配置文件读取admin账号密码
            from pathlib import Path
            import yaml
            config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'

            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                admin_config = config.get('admin', {})
                admin_username = admin_config.get('username', 'admin')
                admin_password = admin_config.get('password', 'admin')
            else:
                admin_username = 'admin'
                admin_password = 'admin'

            # 验证用户名和密码
            if username == admin_username and password == admin_password:
                # 创建会话
                session_id = self.create_session(username)

                # 设置Cookie
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Set-Cookie', f'sessionId={session_id}; Path=/; HttpOnly; SameSite=Lax')
                self.end_headers()

                response = {
                    'success': True,
                    'message': '登录成功',
                    'sessionId': session_id,
                    'username': username
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                logger.info(f"用户登录成功: {username}")
            else:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()

                response = {
                    'success': False,
                    'message': '用户名或密码错误'
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                logger.warning(f"登录失败: {username}")

        except Exception as e:
            logger.error(f"登录处理错误: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'success': False,
                'message': '服务器错误'
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

    def handle_validate_session(self):
        """验证会话"""
        try:
            # 读取请求数据
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))
            else:
                request_data = {}

            session_id = request_data.get('sessionId', '')

            if self.validate_session(session_id):
                session = SESSION_STORE.get(session_id, {})
                self.send_json_response({
                    'success': True,
                    'valid': True,
                    'username': session.get('username', '')
                })
            else:
                self.send_json_response({
                    'success': True,
                    'valid': False
                })

        except Exception as e:
            logger.error(f"会话验证错误: {e}")
            self.send_json_response({
                'success': False,
                'valid': False
            })

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

        for author_uuid, data in report_data.items():
            authors.append({
                'uuid': author_uuid,  # UUID作为主要标识
                'name': data.get('name', 'Unknown'),
                'email': data.get('email', ''),
                'commits': data.get('commits', 0),
                'net_lines': data.get('net_lines', 0),
                'projects': data.get('projects', 0),
                'report_url': f"/report/{author_uuid}",  # 使用UUID访问
            })

        # 按提交数排序
        authors.sort(key=lambda x: x['commits'], reverse=True)

        response = {
            'total': len(authors),
            'authors': authors
        }

        self.send_json_response(response)

    def send_author_data(self, author_uuid):
        """发送特定作者的JSON数据 - 通过UUID查询"""
        # 实时重新加载报告数据
        reports_dir = Path(self.directory)
        report_data = load_report_data(reports_dir)

        # 通过UUID查找作者
        author_info = report_data.get(author_uuid)
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

    def send_system_status_api(self):
        """发送系统状态API - 检查任务状态和文件状态"""
        project_root = Path(__file__).parent.parent
        progress_file = project_root / 'reports' / '.progress.json'
        reports_dir = project_root / 'reports'

        # 检查进度文件
        has_progress = False
        task_status = None
        if progress_file.exists():
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                task_status = progress.get('status')
                if task_status == 'generating':
                    has_progress = True
            except:
                pass

        # 检查是否有旧的报告文件
        has_old_reports = False
        old_report_count = 0
        if reports_dir.exists():
            # 统计JSON报告文件数量（排除.开头的隐藏文件）
            json_files = list(reports_dir.glob('*.json'))
            old_report_count = len([f for f in json_files if not f.name.startswith('.')])
            has_old_reports = old_report_count > 0

        response = {
            'task_status': task_status,  # 'generating', 'completed', 或 None
            'has_progress': has_progress,
            'has_old_reports': has_old_reports,
            'old_report_count': old_report_count,
            'can_generate': not has_progress  # 只有在没有任务进行时才能生成
        }
        self.send_json_response(response)

    def generate_report(self):
        """生成报告数据 - 支持续跑功能"""
        try:
            logger.info("收到生成报告请求")

            # 读取请求数据
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))
            else:
                request_data = {}

            # 获取操作类型：restart 或 continue
            action = request_data.get('action', 'restart')

            # 检查是否有历史进度
            project_root = Path(__file__).parent.parent
            progress_file = project_root / 'reports' / '.progress.json'

            has_history = False
            history_info = None

            if progress_file.exists():
                try:
                    with open(progress_file, 'r', encoding='utf-8') as f:
                        history_info = json.load(f)

                    # 只处理未完成的任务
                    if history_info.get('status') == 'generating':
                        has_history = True
                        logger.info(f"发现历史生成任务: {history_info.get('current', 'Unknown')}")
                except Exception as e:
                    logger.warning(f"读取历史进度失败: {e}")

            # 根据操作类型处理
            if has_history and action == 'continue':
                # 继续历史任务
                logger.info("继续历史生成任务")

                response = {
                    'success': True,
                    'message': '正在继续历史生成任务',
                    'has_history': True,
                    'history_info': {
                        'current': history_info.get('current', 'Unknown'),
                        'percentage': history_info.get('percentage', 0),
                        'total': history_info.get('total', 0),
                        'completed': history_info.get('completed', 0)
                    }
                }
                self.send_json_response(response)

                # 启动继续生成线程
                def continue_generation():
                    generator = ReportGenerator(project_root)
                    def progress_callback(data):
                        logger.info(f"进度: {data['current']} - {data['percentage']}%")

                    generator.generate_all(progress_callback)

                thread = threading.Thread(target=continue_generation, daemon=True)
                thread.start()

            elif has_history and action == 'restart':
                # 重新开始，删除历史进度和旧报告文件
                logger.info("重新开始生成，清除历史进度和旧报告文件")

                # 删除进度文件
                if progress_file.exists():
                    progress_file.unlink()

                # 删除旧的报告文件
                reports_dir = project_root / 'reports'
                if reports_dir.exists():
                    # 删除所有JSON报告文件（但保留隐藏文件如.progress.json）
                    json_files = list(reports_dir.glob('*.json'))
                    deleted_count = 0
                    for json_file in json_files:
                        if not json_file.name.startswith('.'):
                            try:
                                json_file.unlink()
                                deleted_count += 1
                            except Exception as e:
                                logger.warning(f"删除旧报告文件失败 {json_file}: {e}")
                    logger.info(f"已删除 {deleted_count} 个旧报告文件")

                def run_generation():
                    generator = ReportGenerator(project_root)
                    def progress_callback(data):
                        logger.info(f"进度: {data['current']} - {data['percentage']}%")

                    generator.generate_all(progress_callback)

                thread = threading.Thread(target=run_generation, daemon=True)
                thread.start()

                response = {
                    'success': True,
                    'message': '已清除历史进度和旧报告，重新开始生成',
                    'has_history': True,
                    'action': 'restarted'
                }
                self.send_json_response(response)

            else:
                # 没有历史任务，开始新任务（需要删除旧报告文件）
                logger.info("开始新的生成任务")

                # 删除旧的报告文件
                reports_dir = project_root / 'reports'
                if reports_dir.exists():
                    # 删除所有JSON报告文件（但保留隐藏文件）
                    json_files = list(reports_dir.glob('*.json'))
                    deleted_count = 0
                    for json_file in json_files:
                        if not json_file.name.startswith('.'):
                            try:
                                json_file.unlink()
                                deleted_count += 1
                            except Exception as e:
                                logger.warning(f"删除旧报告文件失败 {json_file}: {e}")
                    if deleted_count > 0:
                        logger.info(f"已删除 {deleted_count} 个旧报告文件")

                def run_generation():
                    generator = ReportGenerator(project_root)
                    def progress_callback(data):
                        logger.info(f"进度: {data['current']} - {data['percentage']}%")

                    generator.generate_all(progress_callback)

                thread = threading.Thread(target=run_generation, daemon=True)
                thread.start()

                response = {
                    'success': True,
                    'message': '报告生成已启动',
                    'has_history': False
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

    def completely_rerun(self):
        """完全重跑 - 清除所有进度、检查点和缓存，从头开始生成"""
        try:
            logger.info("=" * 60)
            logger.info("收到完全重跑请求")
            logger.info("=" * 60)

            project_root = Path(__file__).parent.parent
            reports_dir = project_root / 'reports'

            # 1. 删除进度文件
            progress_file = reports_dir / '.progress.json'
            deleted_files = []

            if progress_file.exists():
                try:
                    progress_file.unlink()
                    deleted_files.append('.progress.json')
                    logger.info("已删除进度文件")
                except Exception as e:
                    logger.warning(f"删除进度文件失败: {e}")

            # 2. 删除续跑检查点文件
            checkpoint_file = reports_dir / '.resume_checkpoint.json'
            if checkpoint_file.exists():
                try:
                    checkpoint_file.unlink()
                    deleted_files.append('.resume_checkpoint.json')
                    logger.info("已删除续跑检查点文件")
                except Exception as e:
                    logger.warning(f"删除检查点文件失败: {e}")

            # 3. 删除Git扫描缓存
            cache_dir = project_root / '.git_scan_cache'
            if cache_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(cache_dir)
                    deleted_files.append('Git扫描缓存')
                    logger.info(f"已删除Git扫描缓存: {cache_dir}")
                except Exception as e:
                    logger.warning(f"删除Git扫描缓存失败: {e}")

            # 4. 删除所有旧报告文件
            if reports_dir.exists():
                json_files = list(reports_dir.glob('*.json'))
                report_count = 0
                for json_file in json_files:
                    if not json_file.name.startswith('.'):
                        try:
                            json_file.unlink()
                            report_count += 1
                        except Exception as e:
                            logger.warning(f"删除报告文件失败 {json_file}: {e}")

                if report_count > 0:
                    deleted_files.append(f"{report_count} 个报告文件")
                    logger.info(f"已删除 {report_count} 个报告文件")

            logger.info("=" * 60)
            logger.info("完全重跑：已清除所有历史数据和缓存")
            logger.info(f"删除的文件: {', '.join(deleted_files)}")
            logger.info("=" * 60)

            # 启动全新生成任务
            def run_generation():
                generator = ReportGenerator(project_root)
                def progress_callback(data):
                    logger.info(f"进度: {data['current']} - {data['percentage']}%")

                generator.generate_all(progress_callback)

            thread = threading.Thread(target=run_generation, daemon=True)
            thread.start()

            response = {
                'success': True,
                'message': '已清除所有进度和报告，从头开始生成',
                'deleted_files': deleted_files
            }
            self.send_json_response(response)

        except Exception as e:
            logger.error(f"完全重跑失败: {str(e)}", exc_info=True)
            response = {
                'success': False,
                'error': str(e)
            }
            self.send_json_response(response)

    def serve_author_report(self, author_uuid):
        """提供个人报告页面 - 通过UUID访问

        支持的URL格式:
        - /report/<uuid>                    - 使用UUID访问
        - /report/<uuid>?style=interactive  - 使用交互式滚动模板
        - /report/<uuid>?style=story        - 使用故事模板
        - /report/<uuid>?style=scroll       - 使用照片墙滚动模板（推荐）
        """
        # URL解码
        from urllib.parse import unquote
        author_uuid = unquote(author_uuid)

        # 解析查询参数
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        style = query_params.get('style', ['default'])[0]

        # 根据style参数选择模板
        template_map = {
            'default': 'report_story_scroll.html',  # 默认使用照片墙滚动模板
            'interactive': 'report_interactive.html',
            'story': 'report_story.html',
            'scroll': 'report_story_scroll.html',
            'classic': 'report.html'  # 经典模板
        }
        template_name = template_map.get(style, 'report_story_scroll.html')

        # 实时重新加载报告数据
        reports_dir = Path(self.directory)
        report_data = load_report_data(reports_dir)

        # 通过UUID查找作者信息
        author_info = report_data.get(author_uuid)
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
                html = self.render_report_html(report_data, template_name)
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

    def render_report_html(self, data: dict, template_name: str = 'report.html') -> str:
        """渲染报告HTML页面

        Args:
            data: 报告数据
            template_name: 模板文件名，支持 'report.html', 'report_interactive.html', 'report_story.html', 'report_story_scroll.html'
        """
        # 读取模板（从项目根目录）
        project_root = Path(__file__).parent.parent
        template_path = project_root / 'templates' / template_name
        if not template_path.exists():
            # 如果指定模板不存在，尝试使用默认模板
            template_path = project_root / 'templates' / 'report.html'
            if not template_path.exists():
                # 如果默认模板也不存在，使用内嵌模板
                return self.generate_embedded_report(data)

        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # 简单的模板替换
        theme = data.get('theme', {})
        primary_color = theme.get('primary_color', '#667eea')
        secondary_color = theme.get('secondary_color', '#764ba2')
        accent_color = theme.get('accent_color', '#f093fb')

        # 获取作者信息
        meta = data.get('meta', {})
        author = meta.get('author', '开发者')
        year = data.get('year', 2025)
        summary = data.get('summary', {})

        # 将JSON数据直接输出到script标签中（作为textContent）
        # 不需要转义，因为不是JavaScript字符串字面量
        json_str = json.dumps(data, ensure_ascii=False, indent=2)

        # 模板变量替换
        html = template.replace('{{ author }}', author)
        html = html.replace('{{ year }}', str(year))
        html = html.replace('{{ data_json | default(\'{}\') }}', json_str)
        html = html.replace('{{ data_json }}', json_str)
        html = html.replace('{{ primary_color | default(\'#667eea\') }}', primary_color)
        html = html.replace('{{ primary_color }}', primary_color)
        html = html.replace('{{ secondary_color | default(\'#764ba2\') }}', secondary_color)
        html = html.replace('{{ secondary_color }}', secondary_color)
        html = html.replace('{{ accent_color | default(\'#f093fb\') }}', accent_color)
        html = html.replace('{{ accent_color }}', accent_color)

        # AI文案 - 需要处理 markdown 或 XML
        ai_text = data.get('ai_text', None)
        if ai_text:
            import re

            # 检查是否是XML格式
            if '<graphs>' in ai_text and '<graph>' in ai_text:
                # 解析XML格式
                ai_text_html = self._parse_xml_ai_text(ai_text, data)
            else:
                # 将markdown转换为HTML（简单处理）
                # 转换换行
                ai_text_html = ai_text.replace('\n\n', '</p><p>').replace('\n', '<br>')
                ai_text_html = f'<p>{ai_text_html}</p>'
                # 处理标题
                ai_text_html = re.sub(r'<p># (.*?)</p>', r'<h3>\1</h3>', ai_text_html)
                ai_text_html = re.sub(r'<p>## (.*?)</p>', r'<h4>\1</h4>', ai_text_html)
                ai_text_html = re.sub(r'<p>### (.*?)</p>', r'<h5>\1</h5>', ai_text_html)
                # 处理粗体
                ai_text_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', ai_text_html)
        else:
            # 使用默认文案
            ai_text_html = self._get_default_ai_text(data)

        html = html.replace('{{ ai_text | safe }}', ai_text_html)
        html = html.replace('{{ ai_text }}', ai_text_html)

        return html

    def _parse_xml_ai_text(self, ai_text: str, data: dict) -> str:
        """解析XML格式的AI文案

        Args:
            ai_text: XML格式的AI文案
            data: 报告数据

        Returns:
            HTML格式的文案
        """
        import re

        try:
            # 提取<graphs>标签内容
            graphs_match = re.search(r'<graphs>([\s\S]*?)</graphs>', ai_text)
            if not graphs_match:
                # 如果解析失败，返回默认文案
                return self._get_default_ai_text(data)

            graphs_content = graphs_match.group(1)

            # 提取所有<graph>标签
            graph_matches = re.findall(r'<graph>([\s\S]*?)</graph>', graphs_content)

            if not graph_matches:
                return self._get_default_ai_text(data)

            # 图标映射
            icon_map = {
                '提交次数': '💫',
                '提交': '💫',
                '代码行数': '🌈',
                '代码': '🌈',
                '净增代码': '🌈',
                '项目数量': '🚀',
                '项目': '🚀',
                '参与项目': '🚀',
                '编程语言': '💻',
                '语言': '💻',
                '主要语言': '💻',
                '高效时段': '🌙',
                '时段': '🌙',
                '时间': '🌙',
                '黄金时段': '🌙',
                '重构比例': '🎯',
                '重构': '🎯',
                '精简': '🎯'
            }

            def get_icon_for_type(type_text):
                """根据type自动匹配图标"""
                for key, icon in icon_map.items():
                    if key in type_text:
                        return icon
                return '📊'

            html_parts = []

            for graph_xml in graph_matches:
                # 解析每个字段
                type_match = re.search(r'<type>(.*?)</type>', graph_xml)
                value_match = re.search(r'<value>(.*?)</value>', graph_xml)
                title_match = re.search(r'<title>(.*?)</title>', graph_xml)
                content_match = re.search(r'<content>(.*?)</content>', graph_xml, re.DOTALL)

                if type_match and value_match and title_match and content_match:
                    metric_type = type_match.group(1).strip()
                    value = value_match.group(1).strip()
                    title = title_match.group(1).strip()
                    content = content_match.group(1).strip()

                    # 获取图标
                    icon = get_icon_for_type(metric_type)

                    # 转换content中的换行为<br>
                    content_html = content.replace('\n\n', '</p><p>').replace('\n', '<br>')

                    # 生成HTML卡片
                    card_html = f'''
                    <div class="metric-card">
                        <div class="metric-header">
                            <span class="metric-icon">{icon}</span>
                            <span class="metric-value">{value}</span>
                            <span class="metric-label">{metric_type}</span>
                        </div>
                        <div class="metric-content">
                            <h4 class="metric-title">{title}</h4>
                            <p class="metric-description">{content_html}</p>
                        </div>
                    </div>
                    '''
                    html_parts.append(card_html)

            if html_parts:
                return '\n'.join(html_parts)
            else:
                return self._get_default_ai_text(data)

        except Exception as e:
            logger.warning(f"XML解析失败: {e}")
            return self._get_default_ai_text(data)

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
    """加载报告索引数据 - 扫描所有作者JSON文件，使用UUID作为key"""
    report_data = {}

    # 排除的文件：进度文件、索引文件和检查点文件
    excluded_files = {'.progress.json', 'report_index.json', '.resume_checkpoint.json', 'uuid_mapping.json'}

    # 扫描所有JSON文件
    for json_file in reports_dir.glob('*.json'):
        # 跳过排除的文件
        if json_file.name in excluded_files:
            continue

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                meta = data.get('meta', {})

                # 获取UUID
                author_uuid = meta.get('uuid', '')
                if not author_uuid:
                    logger.warning(f"跳过没有UUID的文件: {json_file.name}")
                    continue

                # 使用UUID作为key
                report_data[author_uuid] = {
                    'name': meta.get('author', 'Unknown'),
                    'email': meta.get('email', ''),
                    'commits': data.get('summary', {}).get('total_commits', 0),
                    'net_lines': data.get('summary', {}).get('net_lines', 0),
                    'projects': len(data.get('projects', [])),
                    'json_file': json_file.name,
                }
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

    # 检查是否有未完成的任务，自动续跑
    progress_file = reports_path / '.progress.json'
    if progress_file.exists():
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)

            if progress.get('status') == 'generating':
                logger.info("=" * 60)
                logger.info("检测到未完成的生成任务，自动续跑")
                logger.info("=" * 60)
                logger.info(f"任务进度: {progress.get('completed', 0)}/{progress.get('total', 0)}")

                # 在后台线程中自动续跑
                def auto_resume():
                    try:
                        project_root = Path(__file__).parent.parent
                        generator = ReportGenerator(project_root)
                        generator.generate_all()
                    except Exception as e:
                        logger.error(f"自动续跑失败: {e}")

                resume_thread = threading.Thread(target=auto_resume, daemon=True)
                resume_thread.start()
                logger.info("已在后台启动自动续跑任务")
        except Exception as e:
            logger.warning(f"检查进度文件失败: {e}")

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
