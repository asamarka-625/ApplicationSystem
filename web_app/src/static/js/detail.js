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

    // Элементы модального окна
    const userModal = document.getElementById('userModal');
    const userInfo = document.getElementById('userInfo');
    const closeModal = document.getElementById('closeModal');
    const closeBtn = document.querySelector('.close');

    // Функция для открытия модального окна с информацией о пользователе
    async function openUserModal(userId) {
        try {
            // Показываем индикатор загрузки
            userInfo.innerHTML = '<div class="loading">Загрузка...</div>';
            userModal.style.display = 'block';

            // Делаем запрос к API
            const response = await fetch(`/user/${userId}`);

            if (!response.ok) {
                throw new Error('Ошибка при получении данных пользователя');
            }

            const userData = await response.json();

            // Отображаем данные пользователя
            displayUserInfo(userData);

        } catch (error) {
            console.error('Ошибка:', error);
            userInfo.innerHTML = `<div class="error">Ошибка при загрузке данных: ${error.message}</div>`;
        }
    }

    // Функция для отображения информации о пользователе
    function displayUserInfo(user) {
        userInfo.innerHTML = `
            <div class="user-info-item">
                <span class="user-info-label">ID:</span>
                <span class="user-info-value">${user.id || '—'}</span>
            </div>
            <div class="user-info-item">
                <span class="user-info-label">Имя:</span>
                <span class="user-info-value">${user.name || '—'}</span>
            </div>
            <div class="user-info-item">
                <span class="user-info-label">Email:</span>
                <span class="user-info-value">${user.email || '—'}</span>
            </div>
            <div class="user-info-item">
                <span class="user-info-label">Статус:</span>
                <span class="user-info-value">${user.status || '—'}</span>
            </div>
            <div class="user-info-item">
                <span class="user-info-label">Дата регистрации:</span>
                <span class="user-info-value">${user.created_at ? formatDate(user.created_at) : '—'}</span>
            </div>
            ${user.additional_info ? `
            <div class="user-info-item">
                <span class="user-info-label">Дополнительная информация:</span>
                <span class="user-info-value">${user.additional_info}</span>
            </div>
            ` : ''}
        `;
    }

    // Закрытие модального окна
    function closeUserModal() {
        userModal.style.display = 'none';
    }

    // Обработчики событий
    closeBtn.addEventListener('click', closeUserModal);
    closeModal.addEventListener('click', closeUserModal);

    // Закрытие при клике вне модального окна
    window.addEventListener('click', (event) => {
        if (event.target === userModal) {
            closeUserModal();
        }
    });
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
    document.getElementById('secretary_name').textContent = request.secretary.name;
    document.getElementById('judge_name').textContent = request.judge.name;
    document.getElementById('management_name').textContent = request.management.name ? request.management.name : 'Не назанчен';
    document.getElementById('executor_name').textContent = request.executor.name ? request.executor.name : 'Не назанчен';
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

    document.getElementById(...)
}

function displayRequestHistory(history) {
    const historyBody = document.getElementById('historyBody');

    if (!history || history.length === 0) {
        historyBody.innerHTML = '<tr><td colspan="4" style="text-align: center;">История изменений отсутствует</td></tr>';
        return;
    }

    historyBody.innerHTML = history
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .map(item => `
        <tr>
            <td>${formatDate(item.created_at)}</td>
            <td>
                <span class="status-badge status-${item.action.name.toLowerCase()}">
                    ${item.action.value}
                </span>
            </td>
            <td>${(item.description || '—').replace(/\n/g, '<br>')}</td>
            <td>${item.user.name || 'Система'}</td>
        </tr>
    `).join('');
}

