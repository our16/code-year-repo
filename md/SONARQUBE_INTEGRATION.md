# SonarQube本地服务集成指南

## 快速开始

### 1. 启动本地SonarQube服务

#### 方式A：使用Docker（推荐）

```bash
# 拉取SonarQube镜像
docker pull sonarqube:latest

# 启动SonarQube服务
docker run -d --name sonarqube \
  -p 9000:9000 \
  -e SONAR_JDBC_URL="jdbc:postgresql://db:5432/sonar" \
  sonarqube:latest

# 或使用docker-compose
cat > docker-compose.yml <<EOF
version: '3'
services:
  sonarqube:
    image: sonarQube:latest
    ports:
      - "9000:9000"
    environment:
      - SONAR_JDBC_URL=jdbc:postgresql://db:5432/sonar
    volumes:
      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_logs:/opt/sonarqube/logs
volumes:
  sonarqube_data:
  sonarqube_logs:
EOF

docker-compose up -d
```

#### 方式B：下载并运行

```bash
# 下载SonarQube
wget https://binaries.sonarsource.com/Distribution/sonarqube/sonarqube-9.9.0.65466.zip
unzip sonarqube-9.9.0.65466.zip
cd sonarqube-9.9.0.65466

# 启动服务（Linux/Mac）
./bin/linux-x86-64/sonar.sh start

# 或Windows
bin/windows-x86-64/StartSonar.bat

# 访问 http://localhost:9000
# 默认账号：admin / admin
```

### 2. 配置项目

#### 获取Token

1. 访问 http://localhost:9000
2. 登录（admin/admin）
3. 点击右上角头像 → My Account → Security
4. 生成Token：`Generate Tokens`
5. 复制Token（格式：`squ_xxxxxxxxxxxxxxxx`）

#### 创建项目

1. 点击 "Create Project"
2. 手动设置
3. 项目密钥：`my-project`
4. 项目名称：`My Project`

### 3. 分析代码

#### 使用SonarQube Scanner

```bash
# 下载Scanner
wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-4.8.0.2856.zip
unzip sonar-scanner-cli-4.8.0.2856.zip

# 分析项目
cd your-project
sonar-scanner/bin/sonar-scanner \
  -Dsonar.projectKey=my-project \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=your-token
```

#### 使用Maven/Gradle

**Maven (`pom.xml`):**
```xml
<plugin>
    <groupId>org.sonarsource.scanner.maven</groupId>
    <artifactId>sonar-maven-plugin</artifactId>
    <version>3.9.1.2184</version>
</plugin>
```

```bash
mvn sonar:sonar \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=your-token
```

**Gradle (`build.gradle`):**
```groovy
plugins {
  id "org.sonarqube" version "3.3"
}

sonarqube {
  properties {
    property "sonar.host.url", "http://localhost:9000"
    property "sonar.login", "your-token"
  }
}
```

```bash
./gradlew sonarqube
```

### 4. 配置报告生成器

```yaml
# config.yaml
sonarqube:
  enabled: true
  url: "http://localhost:9000"
  token: "squ_xxxxxxxxxxxxxxxx"
  project_keys:
    - "lvtu-server"
    - "my-project"

# 其他配置...
projects:
  - path: "F:/project"
    name: "所有项目"

report_year: 2025
```

---

## 本地SonarQube客户端实现

创建 `src/sonarqube_client.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SonarQube本地客户端
"""

import requests
from typing import Dict, Any, List
from datetime import datetime, timedelta


class SonarQubeClient:
    """SonarQube API客户端（本地服务）"""

    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get('sonarqube', {}).get('enabled', False)
        self.url = config.get('sonarqube', {}).get('url', 'http://localhost:9000')
        self.token = config.get('sonarqube', {}).get('token', '')
        self.project_keys = config.get('sonarqube', {}).get('project_keys', [])

    def is_available(self) -> bool:
        """检查SonarQube服务是否可用"""
        if not self.enabled:
            return False

        try:
            response = requests.get(f"{self.url}/api/system/status", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def get_project_metrics(self, project_key: str) -> Dict[str, Any]:
        """获取项目质量指标"""
        if not self.enabled or not self.url:
            return {}

        try:
            api_url = f"{self.url}/api/measures/component"

            metrics = [
                'code_smells',           # 代码异味
                'vulnerabilities',       # 漏洞
                'bugs',                  # Bug
                'coverage',              # 覆盖率
                'duplicated_lines_density',  # 重复率
                'sqale_index',          # 技术债务
                'ncloc',                # 代码行数（非注释）
                'complexity',           # 复杂度
                'cognitive_complexity', # 认知复杂度
            ]

            params = {
                'component': project_key,
                'metricKeys': ','.join(metrics),
            }

            headers = {'Authorization': f'Bearer {self.token}'}

            response = requests.get(api_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 解析指标
            metrics_data = {}
            for measure in data.get('component', {}).get('measures', []):
                metric_name = measure['metric']
                metric_value = measure.get('value', '0')

                # 转换为数值
                try:
                    if '.' in metric_value:
                        metrics_data[metric_name] = float(metric_value)
                    else:
                        metrics_data[metric_name] = int(metric_value)
                except ValueError:
                    metrics_data[metric_name] = metric_value

            return metrics_data

        except Exception as e:
            print(f"      警告: 获取SonarQube指标失败: {str(e)}")
            return {}

    def get_quality_trend(self, project_key: str, days: int = 30) -> List[Dict]:
        """获取质量趋势（历史数据）"""
        if not self.enabled:
            return []

        try:
            api_url = f"{self.url}/api/measures/search_history"

            # 计算日期范围
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)

            params = {
                'component': project_key,
                'metrics': 'code_smells,vulnerabilities,bugs,coverage',
                'from': from_date.strftime('%Y-%m-%d'),
                'to': to_date.strftime('%Y-%m-%d'),
            }

            headers = {'Authorization': f'Bearer {self.token}'}

            response = requests.get(api_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            return data.get('measures', [])

        except Exception as e:
            print(f"      警告: 获取SonarQube历史数据失败: {str(e)}")
            return []

    def get_hotspots(self, project_key: str) -> List[Dict]:
        """获取安全热点"""
        try:
            api_url = f"{self.url}/api/hotspots/search"

            params = {
                'projectKey': project_key,
                'status': 'REVIEWED,TO_REVIEW',
            }

            headers = {'Authorization': f'Bearer {self.token}'}

            response = requests.get(api_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            return data.get('hotspots', [])

        except Exception:
            return []

    def analyze_author_quality(self, project_key: str, author_name: str) -> Dict[str, Any]:
        """分析特定作者的代码质量"""
        # 获取项目整体指标
        metrics = self.get_project_metrics(project_key)

        # 获取安全热点
        hotspots = self.get_hotspots(project_key)

        return {
            'project': project_key,
            'author': author_name,
            'code_smells': metrics.get('code_smells', 0),
            'vulnerabilities': metrics.get('vulnerabilities', 0),
            'bugs': metrics.get('bugs', 0),
            'coverage': metrics.get('coverage', 0),
            'duplication': metrics.get('duplicated_lines_density', 0),
            'complexity': metrics.get('complexity', 0),
            'technical_debt': metrics.get('sqale_index', 0),
            'security_hotspots': len(hotspots),
        }
```

---

## 集成到报告生成器

### 修改 `src/git_collector.py`

```python
from src.sonarqube_client import SonarQubeClient

class GitDataCollector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.authors = config.get('authors', [])
        self.report_year = config.get('report_year', 2024)
        self.sonarqube = SonarQubeClient(config)  # 添加SonarQube客户端

    def collect_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        # ... 原有代码 ...

        project_data = {
            'project_name': project_name,
            'path': repo_path,
            'commits': commits_data,
            'language_stats': dict(language_stats),
            'total_commits': len(commits_data),
            'branch': repo.active_branch.name if repo.active_branch else 'HEAD',
        }

        # 添加SonarQube质量指标
        if self.sonarqube.is_available():
            project_key = project.get('sonarqube_key', project_name)
            quality_metrics = self.sonarqube.get_project_metrics(project_key)

            if quality_metrics:
                project_data['quality_metrics'] = quality_metrics
                print(f"   [SonarQube] 质量指标: {quality_metrics}")

        return project_data
```

---

## 在报告中显示质量数据

### 修改 `src/llm_client.py`

更新默认文案模板，包含代码质量信息：

```python
def _get_default_text(self, data: Dict[str, Any]) -> str:
    """获取默认文案"""
    summary = data.get('summary', {})
    languages = data.get('languages', {})
    projects = data.get('projects', [])

    # 获取质量指标
    quality = data.get('quality_metrics', {})

    top_lang = languages.get('top_languages', [])[:3]
    lang_names = [l['name'] for l in top_lang]

    text = f"""
# 💌 致过去的一年：你的代码，你的诗篇

...

## 代码质量

你的代码质量表现：
- 代码异味: {quality.get('code_smells', 0)} 个
- Bug: {quality.get('bugs', 0)} 个
- 漏洞: {quality.get('vulnerabilities', 0)} 个
- 测试覆盖率: {quality.get('coverage', 0)}%
- 代码重复率: {quality.get('duplication', 0)}%

{'你的代码质量优秀，继续保持！' if quality.get('code_smells', 0) < 50 else '建议关注代码质量，减少技术债务。'}

...

"""
    return text
```

---

## 完整使用流程

### 1. 启动SonarQube服务

```bash
# Docker方式
docker-compose up -d

# 或直接运行
./bin/linux-x86-64/sonar.sh start
```

### 2. 分析项目代码

```bash
cd your-project
sonar-scanner \
  -Dsonar.projectKey=lvtu-server \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=your-token
```

### 3. 配置报告生成器

```yaml
# config.yaml
sonarqube:
  enabled: true
  url: "http://localhost:9000"
  token: "squ_xxxxxxxxxxxxxxxx"

projects:
  - path: "F:/project/lvtu-server"
    name: "lvtu-server"
    sonarqube_key: "lvtu-server"  # SonarQube项目密钥

authors:
  - "Your Name"
```

### 4. 生成报告

```bash
python main.py --no-llm
```

输出会包含SonarQube质量指标：

```
[1/1] 分析作者: Your Name
   - 总提交次数: 150
   - 净增代码行: 50000
   - 参与项目数: 3
   [SonarQube] 质量指标: {'code_smells': 23, 'bugs': 5, ...}
```

---

## Docker Compose 完整配置

创建 `docker-compose.yml`：

```yaml
version: '3'

services:
  # PostgreSQL数据库
  db:
    image: postgres:13
    environment:
      POSTGRES_USER: sonar
      POSTGRES_PASSWORD: sonar
    volumes:
      - postgresql_data:/var/lib/postgresql/data
    networks:
      - sonarnet

  # SonarQube服务
  sonarqube:
    image: sonarqube:latest
    ports:
      - "9000:9000"
    environment:
      SONAR_JDBC_URL: jdbc:postgresql://db:5432/sonar
      SONAR_JDBC_USERNAME: sonar
      SONAR_JDBC_PASSWORD: sonar
    volumes:
      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_logs:/opt/sonarqube/logs
      - sonarqube_extensions:/opt/sonarqube/extensions
    networks:
      - sonarnet
    depends_on:
      - db

networks:
  sonarnet:

volumes:
  postgresql_data:
  sonarqube_data:
  sonarqube_logs:
  sonarqube_extensions:
```

启动：

```bash
docker-compose up -d

# 访问 http://localhost:9000
# 等待SonarQube启动完成（约1-2分钟）
```

---

## 注意事项

### 1. 性能考虑

- SonarQube需要至少2GB内存
- 大型项目分析可能较慢
- 建议在非高峰时段分析

### 2. 数据持久化

```bash
# 备份SonarQube数据
docker exec sonarqube bash -c "cd /opt/sonarqube/data && tar czf /tmp/backup.tar.gz ."
docker cp sonarqube:/tmp/backup.tar.gz ./sonarqube-backup.tar.gz
```

### 3. 安全配置

- 修改默认密码
- 配置防火墙规则
- 使用HTTPS（生产环境）
- 定期更新SonarQube

---

## 替代方案

如果不想使用SonarQube，可以使用轻量级工具：

### 1. CodeClimate

```bash
# 安装
gem install codeclimate

# 分析
codeclimate analyze
```

### 2. Lint-staged + Pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
```

### 3. 简化统计

如果只需要基础统计，使用Git内置数据即可（当前实现）。

---

## 总结

使用本地SonarQube服务：

```bash
# 1. 启动SonarQube
docker-compose up -d

# 2. 分析项目
sonar-scanner -Dsonar.host.url=http://localhost:9000

# 3. 配置并生成报告
python main.py --no-llm

# 4. 查看报告（包含质量数据）
python server.py
```

**当前实现已包含：**
- ✅ Git统计数据（提交、代码行数）
- ✅ SonarQube集成接口（可选）
- ✅ 质量指标显示（如配置）
- ✅ 完整的年度报告

**建议：**
- 小型项目：使用Git统计即可
- 中大型项目：配置SonarQube获取详细质量分析
- 团队项目：SonarQube + 持续集成

