// Загрузка данных для дашборда
async function loadDashboardData() {
    try {
        // Загрузка статистики
        const statsResponse = await fetch(`${API_BASE_URL}/dashboard/statistics?period=month`);
        const statistics = await statsResponse.json();
        
        updateDashboardStats(statistics);
        updateCharts(statistics);
        
        // Загрузка последних заявок
        const requestsResponse = await fetch(`${API_BASE_URL}/requests/?limit=5`);
        const recentRequests = await requestsResponse.json();
        
        displayRecentRequests(recentRequests);
        
    } catch (error) {
        console.error('Ошибка загрузки дашборда:', error);
    }
}

// Обновление статистических карточек
function updateDashboardStats(statistics) {
    document.getElementById('totalRequests').textContent = statistics.total_requests;
    document.getElementById('completedRequests').textContent = statistics.completed_requests;
    document.getElementById('pendingRequests').textContent = statistics.pending_requests;
    document.getElementById('emergencyRequests').textContent = 
        statistics.requests_by_type?.EMERGENCY || 0;
    
    // Показать/скрыть аварийное уведомление
    const emergencyAlert = document.getElementById('emergencyAlert');
    emergencyAlert.style.display = (statistics.requests_by_type?.EMERGENCY || 0) > 0 ? 'flex' : 'none';
}

// Обновление графиков
function updateCharts(statistics) {
    const ctx = document.getElementById('requestsChart').getContext('2d');
    
    if (window.requestsChart) {
        window.requestsChart.destroy();
    }
    
    const typeLabels = Object.keys(statistics.requests_by_type).map(type => 
        getRequestTypeText(type)
    );
    const typeData = Object.values(statistics.requests_by_type);
    
    window.requestsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: typeLabels,
            datasets: [{
                label: 'Количество заявок',
                data: typeData,
                backgroundColor: [
                    '#3498db',
                    '#2ecc71',
                    '#f39c12',
                    '#e74c3c'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Отображение последних заявок
function displayRecentRequests(requests) {
    const container = document.getElementById('recentRequestsList');
    
    if (requests.length === 0) {
        container.innerHTML = '<p class="no-data">Нет recent заявок</p>';
        return;
    }
    
    container.innerHTML = requests.map(request => `
        <div class="request-item" onclick="viewRequest(${request.id})">
            <div class="request-header">
                <span class="request-number">${request.registration_number}</span>
                ${getStatusBadge(request.status)}
            </div>
            <div class="request-title">${request.title}</div>
            <div class="request-meta">
                <span>${getRequestTypeText(request.request_type)}</span>
                <span>${formatDate(request.created_at)}</span>
            </div>
        </div>
    `).join('');
}

// Загрузка статистики
async function loadStatistics() {
    try {
        const period = document.getElementById('statsPeriod').value;
        const response = await fetch(`${API_BASE_URL}/dashboard/statistics?period=${period}`);
        const statistics = await response.json();
        
        updateStatisticsDisplay(statistics);
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
        showNotification('Ошибка загрузки статистики', 'error');
    }
}

function updateStatisticsDisplay(statistics) {
    // Общая статистика
    document.getElementById('completionRate').textContent = 
        `${statistics.completion_rate.toFixed(1)}%`;
    document.getElementById('statsCompleted').textContent = statistics.completed_requests;
    document.getElementById('statsTotal').textContent = statistics.total_requests;
    document.getElementById('statsPending').textContent = statistics.pending_requests;
    
    // По типам заявок
    const byTypeContainer = document.getElementById('requestsByType');
    byTypeContainer.innerHTML = Object.entries(statistics.requests_by_type)
        .map(([type, count]) => `
            <div class="stats-item">
                <span>${getRequestTypeText(type)}</span>
                <strong>${count}</strong>
            </div>
        `).join('') || '<p>Нет данных</p>';
    
    // По исполнителям
    const byExecutorContainer = document.getElementById('requestsByExecutor');
    byExecutorContainer.innerHTML = Object.entries(statistics.requests_by_executor)
        .map(([executor, count]) => `
            <div class="stats-item">
                <span>${executor}</span>
                <strong>${count}</strong>
            </div>
        `).join('') || '<p>Нет данных</p>';
}