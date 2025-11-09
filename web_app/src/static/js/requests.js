const API_URL = '/api/v1/request/view';
const API_BASE_URL = '/api/v1/request';

let currentRejectId = null;
let currentEvent = null;

// Функция для открытия модального окна отклонения
function openRejectModal(e, id) {
    currentRejectId = id;
    currentEvent = e;

    const modal = document.getElementById('rejectModal');
    const textarea = document.getElementById('rejectReason');

    // Сброс формы
    textarea.value = '';
    modal.style.display = 'block';

    // Фокус на текстовом поле
    setTimeout(() => textarea.focus(), 100);
}

// Функция для закрытия модального окна
function closeRejectModal() {
    const modal = document.getElementById('rejectModal');
    modal.style.display = 'none';
    currentRejectId = null;
    currentEvent = null;
}

async function ExecuteRequest(e, id) {
    try {
        const response = await fetch(`${API_BASE_URL}/execute/${id}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.status !== 'success') {
            throw new Error(data.message || 'Ошибка запроса');
        }

        const buttonContainer = e.target.closest('div');
        const buttons = buttonContainer.querySelectorAll('a, button');

        buttons.forEach(button => {
            if (!button.classList.contains('btn-view-details')) {
                button.style.display = 'none';
            }
        });

        showNotification('Заявка успешно выполнена', 'success');
        document.location.reload();

    } catch (error) {
        console.error('Ошибка выполнения заявки:', error);
        showNotification('Ошибка выполнения заявки', 'error');
    }
}

async function ConfirmRequest(e, id) {
    try {
        const response = await fetch(`${API_BASE_URL}/approve/${id}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.status !== 'success') {
            throw new Error(data.message || 'Ошибка запроса');
        }

        const buttonContainer = e.target.closest('div');
        const buttons = buttonContainer.querySelectorAll('a, button');

        buttons.forEach(button => {
            if (!button.classList.contains('btn-view-details')) {
                button.style.display = 'none';
            }
        });

        showNotification('Заявка успешно утверждена', 'success');
        document.location.reload();

    } catch (error) {
        console.error('Ошибка утверждения заявки:', error);
        showNotification('Ошибка утверждения заявки', 'error');
    }
}

// Основная функция отклонения заявки
async function RejectRequest(reason) {
    try {
        const response = await fetch(`${API_BASE_URL}/reject/${currentRejectId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ comment: reason })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.status !== 'success') {
            throw new Error(data.message || 'Ошибка запроса');
        }

        // Скрываем кнопки (как в оригинальной функции)
        const buttonContainer = currentEvent.target.closest('div');
        const buttons = buttonContainer.querySelectorAll('a, button');

        buttons.forEach(button => {
            if (!button.classList.contains('btn-view-details')) {
                button.style.display = 'none';
            }
        });

        showNotification('Заявка отклонена', 'success');
        closeRejectModal();
        document.location.reload();
    } catch (error) {
        console.error('Ошибка при отклонении заявки:', error);
        showNotification('Ошибка при отклонении заявки', 'error');
    }
}

async function loadViewInfo() {
    try {
        const response = await fetch(`${API_URL}/filter/info`);
        const data = await response.json();
        const request_type_data = data.request_type;
		const status_data = data.status;

        const select_type_filter = document.getElementById('typeFilter');
        request_type_data.forEach(request_type => {
            const option = document.createElement('option');
            option.value = request_type.id;
            option.textContent = request_type.name;
            select_type_filter.appendChild(option);
        });

        const select_status_filter = document.getElementById('statusFilter');
        status_data.forEach(status => {
            const option = document.createElement('option');
            option.value = status.id
            option.textContent = status.name;
            select_status_filter.appendChild(option);
        });

    } catch (error) {
        console.error('Ошибка загрузки информации:', error);
        showNotification('Ошибка загрузки информации', 'error');
    }
}

// Загрузка списка заявок
async function loadRequests() {
    try {
        const statusFilter = document.getElementById('statusFilter').value;
        const typeFilter = document.getElementById('typeFilter').value;

        const response = await fetch(`${API_URL}/list/requests?status=${statusFilter}&request_type=${typeFilter}`);
        const data = await response.json();

        displayRequests(data);
    } catch (error) {
        console.error('Ошибка загрузки заявок:', error);
        showNotification('Ошибка загрузки заявок', 'error');
    }
}

// Отображение заявок в таблице
function displayRequests(data) {
    const tbody = document.getElementById('requestsTableBody');
    tbody.innerHTML = '';
    const requests = data.requests;
    const rights = data.rights;

    if (requests.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">Заявки не найдены</td></tr>';
        return;
    }

    requests.forEach(request => {
        const row = document.createElement('tr');
		row.classList.add(`tr-${request.actual_status}`);
        row.innerHTML = `
            <td>${request.registration_number}</td>
            <td>${request.request_type.value}</td>
            <td>
                <span class="status-badge status-${request.status.name.toLowerCase()}">
                    ${request.status.value}
                </span>
            </td>
            <td>${request.is_emergency ? '<span class="emergency-badge">Аварийная</span>' : 'Обычная'}</td>
            <td>${formatDate(request.created_at)}</td>
            <td>
                <div style="display: flex; flex-direction: column; gap: 5px; width: max-content; text-align: center;">
                    ${rights.view && request.rights.view ? `
                        <a class="btn-view-details" href="/request/${request.registration_number}">
                            <i class="fas fa-eye"></i> Просмотр
                        </a>` : ''}
                    ${rights.edit && request.rights.edit ? `
                        <a class="btn-edit" href="/request/${request.registration_number}/edit">
                            <i class="fa-solid fa-pen-to-square"></i> Редактировать
                        </a>` : ''}
                    ${rights.approve && request.rights.approve ? `
                        <button class="btn-approve" onclick="ConfirmRequest(event, '${request.registration_number}')">
                            <i class="fa-solid fa-thumbs-up"></i> Утвердить
                        </button>` : ''}
                    ${rights.redirect_management_department && request.rights.redirect_management_department ? `
                        <a class="btn-redirect" href="/request/${request.registration_number}/redirect/management">
                            <i class="fa-solid fa-calendar-check"></i> Назначить сотрудника управления
                        </a> ` : ''}
                    ${(rights.reject_after && request.rights.reject_after) || (rights.reject_before && request.rights.reject_before) ? `
                        <button class="btn-reject" onclick="openRejectModal(event, '${request.registration_number}')">
                            <i class="fa-solid fa-xmark"></i> Отклонить
                        </button> ` : ''}
                    ${rights.ready && request.rights.ready ? `
                        <button class="btn-ready" onclick="ExecuteRequest(event, '${request.registration_number}')">
                            <i class="fa-solid fa-thumbs-up"></i> Готово
                        </button> ` : ''}
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Экспорт в Excel
async function exportToExcel() {
    try {
        const response = await fetch(`${API_URL}/dashboard/export/excel`);
        const blob = await response.blob();

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `заявки_${new Date().toISOString().split('T')[0]}.xlsx`;

        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showNotification('Данные экспортированы в Excel');
    } catch (error) {
        console.error('Ошибка экспорта:', error);
        showNotification('Ошибка экспорта данных', 'error');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    loadViewInfo();
    loadRequests();
    const rejectModal = document.getElementById('rejectModal');
    const rejectForm = document.getElementById('rejectForm');
    const cancelReject = document.getElementById('cancelReject');
    const closeBtn = rejectModal.querySelector('.close');

    // Обработчик отправки формы
    rejectForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const reason = document.getElementById('rejectReason').value.trim();

        if (!reason) {
            showNotification('Пожалуйста, укажите причину отклонения', 'warning');
            return;
        }

        RejectRequest(reason);
    });

    // Обработчики закрытия модального окна
    cancelReject.addEventListener('click', closeRejectModal);
    closeBtn.addEventListener('click', closeRejectModal);

    // Закрытие при клике вне модального окна
    window.addEventListener('click', function(e) {
        if (e.target === rejectModal) {
            closeRejectModal();
        }
    });
});


