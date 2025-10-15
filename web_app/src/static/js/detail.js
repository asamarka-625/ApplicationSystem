const API_BASE_URL = 'http://localhost:8000/api/v1/request/view';

function getRegistrationNumberFromUrl() {
    const url = window.location.href;

    const parts = url.split('/');
    const registrationNumber = parts[parts.length - 1];

    return registrationNumber;
}

// Загружаем детали заявки
document.addEventListener('DOMContentLoaded', function() {
    const registrationNumber = getRegistrationNumberFromUrl()
    if (registrationNumber) {
        loadRequestDetails(registrationNumber);

    } else {
        showNotification('Номер заявки не указан', 'error');
    }
});

async function loadRequestDetails(id) {
    try {
        const response = await fetch(`${API_BASE_URL}/detail/${id}`);
        if (!response.ok) {
            showNotification('Заявка не найдена', 'error');
        }

        const request = await response.json();
        displayRequestDetails(request);

    } catch (error) {
        console.error('Ошибка загрузки:', error);
        showNotification('Ошибка загрузки', 'error');
    }
}

function displayRequestDetails(request) {
    document.getElementById('requestDetails').style.display = 'block';

    // Заполняем данные
    document.getElementById('registrationNumber').textContent = request.registration_number;
    document.getElementById('regNumber').textContent = request.registration_number;
    document.getElementById('requestType').textContent = request.request_type.value;
    document.getElementById('items').innerHTML = request.items.join('<br>');
    document.getElementById('description').textContent = request.description;
    document.getElementById('department').textContent = request.department_name;
    document.getElementById('secretary_name').textContent = request.secretary_name;
    document.getElementById('judge_name').textContent = request.judge_name;
    document.getElementById('management_name').textContent = request.management_name ? request.management_name : 'Не назанчен';
    document.getElementById('executor_name').textContent = request.executor_name ? request.executor_name : 'Не назанчен';
    document.getElementById('createdAt').textContent = formatDate(request.created_at);
    document.getElementById('deadline').textContent = request.deadline ? formatDate(request.deadline) : 'Не задан';
    document.getElementById('completedAt').textContent = request.completed_at ? formatDate(request.completed_at) : 'Не выполнена';
    document.getElementById('updatedAt').textContent = request.updated_at ? formatDate(request.updated_at) : 'Не обновлялась';

    // Статус
    const statusBadge = document.getElementById('statusBadge');
    statusBadge.textContent = request.status.value;
    statusBadge.className = `status-badge status-${request.status.name.toLowerCase()}`;

    // Срочность
    document.getElementById('emergency').innerHTML = request.is_emergency ?
        '<span class="emergency-badge">Аварийная</span>' : '<span>Обычная</span>';

    displayRequestHistory(request.history);
}

function displayRequestHistory(history) {
    const historyBody = document.getElementById('historyBody');

    if (!history || history.length === 0) {
        historyBody.innerHTML = '<tr><td colspan="4" style="text-align: center;">История изменений отсутствует</td></tr>';
        return;
    }

    historyBody.innerHTML = history.map(item => `
        <tr>
            <td>${formatDate(item.created_at)}</td>
            <td>
                <span class="status-badge status-${item.action.name.toLowerCase()}">
                    ${item.action.value}
                </span>
            </td>
            <td>${(item.description || '—').replace(/\n/g, '<br>')}</td>
            <td>${item.user || 'Система'}</td>
        </tr>
    `).join('');
}

