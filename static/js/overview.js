// 团队总览页面 JavaScript

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadAuthorsData();
    checkProgress();
});

// 生成报告
async function generateReports() {
    const btn = document.getElementById('generateBtn');

    try {
        // 禁用按钮
        btn.disabled = true;
        btn.textContent = '⏳ 生成中...';

        // 发送生成请求
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            alert(result.message);
            // 开始检查进度
            checkProgress();
            // 3秒后刷新页面
            setTimeout(() => {
                location.reload();
            }, 3000);
        } else {
            alert('生成失败: ' + (result.error || '未知错误'));
            btn.disabled = false;
            btn.textContent = '🔄 生成报告';
        }
    } catch (error) {
        console.error('生成失败:', error);
        alert('生成失败，请稍后重试');
        btn.disabled = false;
        btn.textContent = '🔄 生成报告';
    }
}

// 加载作者数据
async function loadAuthorsData() {
    try {
        const response = await fetch('/api/authors');
        const data = await response.json();

        if (data.authors && data.authors.length > 0) {
            displayStats(data);
            displayAuthors(data.authors);
        } else {
            showError('没有找到作者数据');
        }
    } catch (error) {
        console.error('加载失败:', error);
        showError('加载数据失败，请确保服务器正在运行');
    }
}

// 检查生成进度
async function checkProgress() {
    try {
        const response = await fetch('/api/progress');
        const data = await response.json();

        if (data.status !== 'completed') {
            displayProgress(data);
            // 如果未完成，轮询更新进度
            setTimeout(checkProgress, 2000);
        }
    } catch (error) {
        console.error('获取进度失败:', error);
    }
}

// 显示进度
function displayProgress(progress) {
    const progressCard = document.getElementById('progressCard');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    progressCard.style.display = 'block';
    progressBar.style.width = progress.percentage + '%';

    progressText.textContent = `${progress.current} (${progress.completed}/${progress.total}) - ${progress.percentage.toFixed(1)}%`;

    if (progress.status === 'completed') {
        setTimeout(() => {
            progressCard.style.display = 'none';
        }, 3000);
    }
}

// 显示统计信息
function displayStats(data) {
    document.getElementById('total-authors').textContent = data.total;
    document.getElementById('total-commits').textContent =
        data.authors.reduce((sum, author) => sum + author.commits, 0);
}

// 显示作者列表
function displayAuthors(authors) {
    const grid = document.getElementById('authorsGrid');

    // 清空加载提示
    grid.innerHTML = '';

    // 生成作者卡片
    authors.forEach((author, index) => {
        const card = createAuthorCard(author);
        grid.appendChild(card);

        // 延迟动画效果
        setTimeout(() => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.5s, transform 0.5s';

            requestAnimationFrame(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            });
        }, index * 100);
    });
}

// 创建作者卡片
function createAuthorCard(author) {
    const card = document.createElement('a');
    card.className = 'author-card';
    card.href = author.report_url;

    // 创建卡片内容
    card.innerHTML = `
        <h3>${escapeHtml(author.name)}</h3>
        <div class="stats">
            <div class="stat">
                <span>提交次数</span>
                <span class="value">${author.commits}</span>
            </div>
            <div class="stat">
                <span>净增代码</span>
                <span class="value">${formatNumber(author.net_lines)}</span>
            </div>
            <div class="stat">
                <span>参与项目</span>
                <span class="value">${author.projects}</span>
            </div>
        </div>
        <div class="view-btn">查看报告 →</div>
    `;

    return card;
}

// 格式化数字
function formatNumber(num) {
    if (num >= 10000) {
        return (num / 10000).toFixed(1) + 'w';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k';
    }
    return num.toString();
}

// 过滤作者
function filterAuthors() {
    const input = document.getElementById('searchInput');
    const filter = input.value.toLowerCase();
    const cards = document.getElementsByClassName('author-card');

    for (let card of cards) {
        const name = card.getElementsByTagName('h3')[0].textContent.toLowerCase();
        if (name.indexOf(filter) > -1) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    }
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 显示错误信息
function showError(message) {
    const grid = document.getElementById('authorsGrid');
    grid.innerHTML = `<div class="loading">${message}</div>`;
}
