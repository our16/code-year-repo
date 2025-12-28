# 前端代码分离说明

## 静态文件结构

```
static/
├── overview.html          # 团队总览页面（HTML）
├── css/
│   └── overview.css       # 总览页面样式
└── js/
    └── overview.js        # 总览页面逻辑
```

## 文件说明

### 1. HTML文件（static/overview.html）

**作用：** 页面结构

**特点：**
- 纯HTML标记
- 不包含样式
- 不包含逻辑
- 引用外部CSS和JS

```html
<link rel="stylesheet" href="css/overview.css">
<script src="js/overview.js"></script>
```

### 2. CSS文件（static/css/overview.css）

**作用：** 页面样式

**包含：**
- 重置样式
- 布局样式（Grid/Flexbox）
- 组件样式（卡片、按钮等）
- 响应式设计
- 动画效果

**优势：**
- 样式集中管理
- 易于主题定制
- 可被缓存

### 3. JS文件（static/js/overview.js）

**作用：** 页面逻辑

**功能：**
- 数据加载（fetch API）
- DOM操作
- 事件处理
- 搜索过滤
- 错误处理

**优势：**
- 逻辑集中
- 易于调试
- 可被缓存

## 使用方式

### 开发模式

编辑相应的文件：
- 修改结构：`static/overview.html`
- 修改样式：`static/css/overview.css`
- 修改逻辑：`static/js/overview.js`

刷新浏览器即可看到效果。

### 生产模式

静态文件会被缓存，加载更快：
- CSS文件可以缓存
- JS文件可以缓存
- 减少HTML大小

## API接口

### 获取作者列表

```javascript
fetch('/api/authors')
  .then(response => response.json())
  .then(data => {
    console.log(data.authors);
  });
```

**返回格式：**
```json
{
  "total": 44,
  "authors": [
    {
      "id": "monge <mongezheng@gmail.com>",
      "name": "monge",
      "email": "mongezheng@gmail.com",
      "commits": 27,
      "report_url": "/report/monge"
    }
  ]
}
```

### 获取特定作者数据

```javascript
fetch('/api/author/' + authorId)
  .then(response => response.json())
  .then(data => {
    console.log(data);
  });
```

## 优势对比

### 原方式（内联）

```html
<html>
<head>
  <style>
    /* 大量CSS代码 */
  </style>
</head>
<body>
  <!-- HTML -->
  <script>
    /* 大量JS代码 */
  </script>
</body>
</html>
```

**缺点：**
- 文件体积大
- 难以维护
- 无法缓存
- 混杂在一起

### 新方式（分离）

```html
<html>
<head>
  <link rel="stylesheet" href="css/overview.css">
</head>
<body>
  <!-- HTML -->
  <script src="js/overview.js"></script>
</body>
</html>
```

**优点：**
- 文件小
- 易维护
- 可缓存
- 职责分离

## 扩展指南

### 添加新的页面

1. 创建HTML文件：`static/newpage.html`
2. 创建CSS文件：`static/css/newpage.css`
3. 创建JS文件：`static/js/newpage.js`
4. 在HTML中引用

### 修改样式

只需编辑 `static/css/overview.css`：
- 修改颜色
- 调整布局
- 添加动画

### 修改逻辑

只需编辑 `static/js/overview.js`：
- 添加新功能
- 修改API调用
- 优化性能

## 浏览器缓存

静态文件会被浏览器缓存：

**首次访问：**
```
overview.html  (5KB)
overview.css  (10KB)  <- 缓存
overview.js   (8KB)   <- 缓存
```

**再次访问：**
```
overview.html  (5KB)
overview.css  (from cache)
overview.js   (from cache)
```

**优势：**
- 加载更快
- 节省带宽
- 改善体验

## 版本控制（可选）

如需更新静态文件时强制刷新：

```html
<link rel="stylesheet" href="css/overview.css?v=2">
<script src="js/overview.js?v=2"></script>
```

## 总结

前端代码分离后：

- ✅ 更易维护
- ✅ 更好的性能
- ✅ 更清晰的代码
- ✅ 更好的缓存
- ✅ 更容易扩展

**文件结构清晰，职责分明！**
