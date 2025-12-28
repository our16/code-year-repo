// 团队总览页面 JavaScript

// 选中的作者集合
const selectedAuthors = new Set();

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 重置生成按钮状态（防止页面刷新后按钮仍处于禁用状态）
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.disabled = false;
        generateBtn.textContent = '🔄 生成报告';
    }

    loadAuthorsData();
    // 页面加载时不检查进度，避免显示旧的进度条
    // checkProgress();
});

// 生成报告
async function generateReports() {
    const btn = document.getElementById('generateBtn');

    try {
        // 首先检查是否有历史任务
        const progressResponse = await fetch('/api/progress');
        const progressData = await progressResponse.json();

        // 如果有未完成的任务，让用户选择
        if (progressData.status === 'generating') {
            const historyInfo = {
                current: progressData.current || '未知',
                percentage: progressData.percentage || 0,
                completed: progressData.completed || 0,
                total: progressData.total || 0
            };

            const userChoice = confirm(
                `发现未完成的生成任务:\n` +
                `当前进度: ${historyInfo.current}\n` +
                `完成度: ${historyInfo.completed}/${historyInfo.total} (${historyInfo.percentage}%)\n\n` +
                `点击"确定"继续生成\n` +
                `点击"取消"重新开始`
            );

            if (!userChoice) {
                // 用户选择重新开始
                const restartResponse = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ action: 'restart' })
                });

                const restartResult = await restartResponse.json();
                if (restartResult.success) {
                    alert(restartResult.message);
                    startGeneration(btn);
                } else {
                    alert('操作失败: ' + (restartResult.error || '未知错误'));
                }
                return;
            } else {
                // 用户选择继续
                const continueResponse = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ action: 'continue' })
                });

                const continueResult = await continueResponse.json();
                if (continueResult.success) {
                    alert(continueResult.message);
                    startGeneration(btn);
                } else {
                    alert('操作失败: ' + (continueResult.error || '未知错误'));
                }
                return;
            }
        }

        // 没有历史任务，直接开始生成
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            alert(result.message);
            startGeneration(btn);
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

// 开始生成后的通用处理
function startGeneration(btn) {
    btn.disabled = true;
    btn.textContent = '⏳ 生成中...';

    // 开始检查进度
    checkProgress();

    // 提示用户
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 15px 25px;
        border-radius: 10px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.3);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    toast.textContent = '✨ 报告生成中，请稍候...';
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
        location.reload();
    }, 3000);
}

// 加载作者数据
async function loadAuthorsData() {
    try {
        const response = await fetch('/api/authors');
        const data = await response.json();

        if (data.authors && data.authors.length > 0) {
            displayStats(data);
            displayAuthors(data.authors);
            // 开始轮询更新（检测新生成的报告）
            startPollingForUpdates();
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
    const card = document.createElement('div');
    card.className = 'author-card';
    card.dataset.authorId = author.id;
    card.dataset.authorName = author.name;

    // 创建卡片内容
    card.innerHTML = `
        <div class="card-header">
            <label class="author-checkbox">
                <input type="checkbox" class="author-select"
                       value="${author.id}"
                       data-author-name="${escapeHtml(author.name)}"
                       onchange="updateSelection()">
                <span></span>
            </label>
            <a href="${author.report_url}" class="card-link">
                <h3>${escapeHtml(author.name)}</h3>
            </a>
        </div>
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
        const name = card.dataset.authorName.toLowerCase();
        if (name.indexOf(filter) > -1) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    }
}

// 更新选择状态
function updateSelection() {
    const checkboxes = document.querySelectorAll('.author-select:checked');
    const bulkActions = document.getElementById('bulkActions');
    const selectedCount = document.getElementById('selectedCount');

    // 更新选中集合
    selectedAuthors.clear();
    checkboxes.forEach(cb => {
        selectedAuthors.add(cb.value);
    });

    // 更新计数
    selectedCount.textContent = selectedAuthors.size;

    // 显示/隐藏批量操作栏
    if (selectedAuthors.size > 0) {
        bulkActions.style.display = 'flex';
    } else {
        bulkActions.style.display = 'none';
    }

    // 更新全选复选框状态
    const allCheckboxes = document.querySelectorAll('.author-select');
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    selectAllCheckbox.checked = allCheckboxes.length > 0 && selectedAuthors.size === allCheckboxes.length;
    selectAllCheckbox.indeterminate = selectedAuthors.size > 0 && selectedAuthors.size < allCheckboxes.length;
}

// 全选/取消全选
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const allCheckboxes = document.querySelectorAll('.author-select');

    allCheckboxes.forEach(cb => {
        // 只操作可见的复选框
        const card = cb.closest('.author-card');
        if (card.style.display !== 'none') {
            cb.checked = selectAllCheckbox.checked;
        }
    });

    updateSelection();
}

// 清除选择
function clearSelection() {
    const allCheckboxes = document.querySelectorAll('.author-select');
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');

    allCheckboxes.forEach(cb => {
        cb.checked = false;
    });

    selectAllCheckbox.checked = false;
    selectAllCheckbox.indeterminate = false;

    updateSelection();
}

// 发送选中的报告
async function sendSelectedReports() {
    if (selectedAuthors.size === 0) {
        alert('请先选择要发送的报告');
        return;
    }

    // 收集选中的作者信息
    const selectedAuthorsData = [];
    const checkboxes = document.querySelectorAll('.author-select:checked');

    checkboxes.forEach(cb => {
        const authorId = cb.value;
        const authorName = cb.dataset.authorName;
        const reportUrl = window.location.origin + '/report/' + encodeURIComponent(authorId);

        selectedAuthorsData.push({
            id: authorId,
            name: authorName,
            reportUrl: reportUrl
        });
    });

    console.log('========== 发送报告链接 ==========');
    console.log('发送数量:', selectedAuthorsData.length);
    console.log('接收者:', selectedAuthorsData.map(a => a.name).join(', '));
    console.log('');
    console.log('报告链接列表:');
    selectedAuthorsData.forEach((author, index) => {
        console.log(`${index + 1}. ${author.name}`);
        console.log(`   链接: ${author.reportUrl}`);
    });
    console.log('====================================');

    // 调用后端API记录发送日志（预留接口）
    try {
        const response = await fetch('/api/send-reports', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                authors: selectedAuthorsData,
                timestamp: new Date().toISOString()
            })
        });

        const result = await response.json();

        if (result.success) {
            alert(`已准备发送 ${selectedAuthorsData.length} 份报告链接\n\n请查看服务器日志获取详细信息`);
        } else {
            alert(`操作已记录\n\n服务器日志中已输出详细信息，您可以稍后接入消息发送工具`);
        }
    } catch (error) {
        console.error('发送失败:', error);
        alert(`操作已记录（网络错误）\\n\n已将 ${selectedAuthorsData.length} 份报告信息输出到控制台和服务器日志`);
    }

    // 清除选择
    clearSelection();
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 轮询更新（检测新生成的报告）
let pollingInterval = null;

function startPollingForUpdates() {
    // 清除之前的轮询
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }

    // 每3秒检查一次是否有新报告
    pollingInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/authors');
            const data = await response.json();

            if (data.authors && data.authors.length > 0) {
                // 检查是否有新增的作者
                const currentCards = document.querySelectorAll('.author-card');
                const currentCount = currentCards.length;

                if (data.authors.length > currentCount) {
                    console.log(`发现新报告: ${data.authors.length - currentCount} 个`);
                    // 更新统计
                    displayStats(data);
                    // 增量添加新卡片
                    const newAuthors = data.authors.slice(currentCount);
                    newAuthors.forEach((author, index) => {
                        const card = createAuthorCard(author);
                        document.getElementById('authorsGrid').appendChild(card);

                        // 添加动画
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
            }
        } catch (error) {
            console.error('轮询更新失败:', error);
        }
    }, 3000);
}

// 停止轮询
function stopPollingForUpdates() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

// 显示错误信息
function showError(message) {
    const grid = document.getElementById('authorsGrid');
    grid.innerHTML = `<div class="loading">${message}</div>`;
}
