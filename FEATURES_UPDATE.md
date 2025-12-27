# 功能更新说明

## 新增功能

### 1. 自动发现Git仓库 🎉

现在支持指定一个目录，系统会自动扫描并发现该目录下所有的Git仓库！

**使用方法：**

```yaml
# config.yaml
projects:
  - path: "F:/project"  # 指定项目根目录
    name: "所有项目"
```

**特性：**
- ✅ 自动扫描最多3层深度的子目录
- ✅ 智能识别Git仓库（包含`.git`目录）
- ✅ 使用文件夹名作为项目名称
- ✅ 跳过非Git目录，提高效率
- ✅ 扫描过程中显示进度信息

**示例输出：**
```
正在扫描目录: F:/project
发现 5 个Git仓库:
  - ai-orchestrator: F:/project/ai-orchestrator
  - lvtu-server: F:/project/lvtu-server
  - web-app: F:/project/web-app
  - api-gateway: F:/project/api-gateway
  - monitoring: F:/project/monitoring
```

### 2. 支持所有作者模式 👥

现在`authors`配置可以为空，表示包含仓库的所有提交者！

**使用方法：**

```yaml
# config.yaml
authors:
  # 留空，表示包含所有作者
```

**应用场景：**
- 📊 生成团队整体报告
- 🏢 统计整个项目的贡献
- 📈 分析项目整体活跃度
- 🔍 了解团队提交分布

**对比：**
| 模式 | authors配置 | 适用场景 |
|------|------------|---------|
| 个人模式 | 填写具体作者名 | 个人年度总结 |
| 团队模式 | 留空 | 团队报告 |

### 3. 混合配置模式 🔀

支持同时使用自动发现和手动指定：

```yaml
projects:
  - path: "F:/project"        # 自动发现这个目录
    name: "自动发现的项目"
  - path: "F:/special-repo"   # 手动指定这个仓库
    name: "特殊项目"
```

---

## 配置示例

### 示例1：个人开发者

```yaml
projects:
  - path: "F:/my-projects"
    name: "我的项目"

authors:
  - "张三"

report_year: 2025
```

**效果：**
- 扫描`F:/my-projects`下所有Git仓库
- 只统计"张三"的提交
- 适合个人年度总结

### 示例2：团队报告

```yaml
projects:
  - path: "F:/team-projects"
    name: "团队项目"

authors:  # 留空

report_year: 2025
```

**效果：**
- 扫描所有Git仓库
- 统计所有团队成员的提交
- 适合团队年度回顾

### 示例3：特定项目筛选

```yaml
projects:
  - path: "F:/project-a"
    name: "项目A"
  - path: "F:/project-b"
    name: "项目B"

authors:
  - "Alice"
  - "Bob"
```

**效果：**
- 只分析指定的2个项目
- 只统计Alice和Bob的提交
- 适合特定成员或项目分析

---

## 技术实现

### 自动发现算法

```python
def discover_git_repos(root_path: str, max_depth: int = 3):
    """
    1. 遍历目录（限制深度为3层）
    2. 检查每个子目录是否包含.git
    3. 发现Git仓库后，跳过其子目录
    4. 返回发现的仓库列表
    """
```

### 作者筛选逻辑

```python
def _is_target_author(commit: git.Commit) -> bool:
    """
    如果 authors 为空：
        → 返回 True（包含所有作者）

    如果 authors 不为空：
        → 匹配作者名或邮箱
        → 返回匹配结果
    """
```

---

## 常见问题

### Q1: 如何只分析某些特定项目？

**A:** 使用手动指定方式：
```yaml
projects:
  - path: "F:/project/project-a"
    name: "项目A"
  - path: "F:/project/project-b"
    name: "项目B"
```

### Q2: 如何分析整个团队的贡献？

**A:** 将`authors`留空：
```yaml
authors:  # 留空
```

### Q3: 扫描深度可以调整吗？

**A:** 可以修改代码中的`max_depth`参数（默认为3）：
```python
# src/config_loader.py
discovered = self.discover_git_repos(path, max_depth=5)  # 改为5层
```

### Q4: 如何排除某些仓库？

**A:** 目前不支持排除，可以：
1. 将不需要的仓库移出扫描目录
2. 或使用手动指定方式，只添加需要的仓库

### Q5: 扫描会很慢吗？

**A:** 不会，因为：
- 最多只扫描3层深度
- 发现Git仓库后跳过其子目录
- 只检查`.git`目录存在性，不读取内容

---

## 迁移指南

### 从旧版本升级

如果你之前使用的是手动指定方式，无需修改配置，继续兼容使用。

如果想使用自动发现功能：

**旧配置：**
```yaml
projects:
  - path: "F:/project/repo1"
    name: "repo1"
  - path: "F:/project/repo2"
    name: "repo2"
```

**新配置：**
```yaml
projects:
  - path: "F:/project"  # 一行搞定
    name: "所有项目"
```

### authors配置变更

**旧版本（必须配置）：**
```yaml
authors:
  - "Your Name"  # 必须填写
```

**新版本（可选）：**
```yaml
authors:  # 可以留空了！
```

---

## 性能对比

| 配置方式 | 配置行数 | 适用场景 | 维护成本 |
|---------|---------|---------|---------|
| 自动发现 | 1行 | 项目在同一目录 | 极低 |
| 手动指定 | N行（N=项目数） | 项目分散 | 中等 |
| 混合模式 | 1+N行 | 复杂场景 | 低 |

---

## 下一步计划

可能的增强功能：
- [ ] 支持排除特定仓库
- [ ] 支持配置扫描深度
- [ ] 支持按作者分组统计
- [ ] 支持作者别名映射
- [ ] 支持并行扫描加速

---

**享受更便捷的代码年度报告生成体验！** 🚀
