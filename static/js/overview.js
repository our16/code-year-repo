// 团队总览页面 JavaScript

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadAuthorsData();
});

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
    authors.forEach(author => {
        const card = createAuthorCard(author);
        grid.appendChild(card);
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
        </div>
        <div class="view-btn">查看报告 →</div>
    `;

    return card;
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
