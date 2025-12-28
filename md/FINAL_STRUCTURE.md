# 项目最终结构

## 根目录文件

只有一个Python入口文件：

- **start_server.py** - 主程序入口

所有其他Python代码都在 `src/` 目录下。

## 完整目录结构

```
.
├── start_server.py              # 唯一的主程序入口
│
├── config/                      # 配置文件目录
│   ├── README.md
│   ├── config.yaml
│   ├── config.example.yaml
│   ├── author_mapping.yaml
│   └── author_mapping.example.yaml
│
├── src/                         # 所有Python源代码
│   ├── __init__.py
│   ├── git_collector.py         # Git数据采集
│   ├── data_analyzer.py         # 数据分析
│   ├── llm_client.py            # LLM客户端
│   ├── config_loader.py         # 配置加载
│   ├── server.py                # Web服务器
│   └── report_generator.py      # 报告生成（已废弃）
│
├── static/                      # 静态资源
│   ├── overview.html
│   ├── css/
│   │   └── overview.css
│   └── js/
│       └── overview.js
│
├── templates/                   # HTML模板
│   ├── report.html
│   └── report_story.html
│
├── reports/                     # 生成的报告
│   ├── report_index.json
│   └── *.json
│
├── novels/                      # 小说内容（禁止修改）
│
├── README.md                    # 项目文档
├── PROJECT_STRUCTURE.md         # 结构优化说明
├── FINAL_STRUCTURE.md           # 本文件
└── .gitignore
```

## 启动方式

```bash
# 启动Web服务（数据生成可通过Web UI触发）
python start_server.py

# 或指定端口
python start_server.py --port 8080
```

## 设计原则

1. **根目录极简** - 只保留一个入口文件
2. **src目录纯净** - 所有Python代码集中管理
3. **config目录统一** - 配置文件集中管理
4. **static/templates分离** - 前端资源独立管理
5. **reports目录隔离** - 生成的数据独立存放
6. **单一入口** - 通过Web UI统一管理所有功能

## 文件职责

### start_server.py
- 主程序入口
- 启动Web服务器
- 导入src.server模块
- 解析命令行参数

### src/server.py
- HTTP服务器
- API接口（包括数据生成接口）
- 模板渲染
- 静态资源服务
- Git数据采集（通过API触发）

## 使用流程

1. 配置 `config/config.yaml`
2. 运行 `python start_server.py`
3. 访问 `http://localhost:8000`
4. 通过Web界面触发数据生成
5. 查看生成的报告
