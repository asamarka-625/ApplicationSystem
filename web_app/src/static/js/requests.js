const API_URL = 'http://localhost:8000/api/v1/request/view';
const API_BASE_URL = 'http://localhost:8000/api/v1/request';

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

        // В реальном приложении - запрос к API с фильтрами
        const response = await fetch(`${API_URL}/list/?status=${statusFilter}&request_type=${typeFilter}`);
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
            <td>${request.deadline ? formatDate(request.deadline) : 'Не задан'}</td>
            <td>
                <div style="display: flex; flex-direction: column; gap: 5px;">
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
                    ${rights.redirect && request.rights.redirect ? `
                        <a class="btn-redirect" href="/request/${request.registration_number}/redirect">
                            <i class="fa-solid fa-calendar-check"></i> Назначить исполнителя
                        </a> ` : ''}
                    ${rights.deadline && request.rights.deadline ? `
                        <button class="btn-deadline" data-reg-id="${request.registration_number}">
                            <i class="fa-solid fa-clock"></i> Назначить сроки
                        </button> ` : ''}
                    ${rights.reject && request.rights.reject ? `
                        <button class="btn-reject" onclick="openRejectModal(event, '${request.registration_number}')">
                            <i class="fa-solid fa-xmark"></i> Отклонить
                        </button> ` : ''}
                    ${rights.ready && request.rights.ready ? `
                        <button class="btn-ready" onclick="ExecuteRequest(event, '${request.registration_number}')">
                            <i class="fa-solid fa-thumbs-up"></i> Готово
                        </button> ` : ''}
                    ${rights.planning && request.rights.planning ? `
                        <a class="btn-planning" href="/request/${request.registration_number}">
                            <i class="fa-solid fa-calendar-days"></i> Планирование
                        </a> ` : ''}
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
    initDateTimePicker();
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

// Глобальные переменные
let selectedDateTime = null;

// Инициализация datetime picker
function initDateTimePicker() {
    const modal = document.getElementById('dateTimeModal');
    const listOpenBtn = document.querySelectorAll('.btn-deadline');
    const cancelBtn = document.getElementById('cancelDateTime');
    const confirmBtn = document.getElementById('confirmDateTime');
    const closeBtn = modal.querySelector('.close');
    const dateInput = document.getElementById('dateInput');
    const timeSelect = document.getElementById('timeSelect');
    const selectedDisplay = document.getElementById('selectedDisplay');

    // Устанавливаем минимальную дату (сегодня)
    const today = new Date().toISOString().split('T')[0];
    dateInput.min = today;

    // Заполняем варианты времени
    populateTimeOptions();

    // Открытие модального окна
    listOpenBtn.forEach(openBtn => {
        openBtn.addEventListener('click', () => {
            openDateTimeModal(openBtn.dataset.regId);
        });
    });

    // Закрытие модального окна
    cancelBtn.addEventListener('click', closeDateTimeModal);
    closeBtn.addEventListener('click', closeDateTimeModal);

    // Закрытие при клике вне модального окна
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeDateTimeModal();
        }
    });

    // Обработчики изменений
    dateInput.addEventListener('change', updateDateTimeSelection);
    timeSelect.addEventListener('change', updateDateTimeSelection);

    // Подтверждение выбора
    confirmBtn.addEventListener('click', confirmDateTimeSelection);
}

// Заполнение вариантов времени
function populateTimeOptions() {
    const timeSelect = document.getElementById('timeSelect');
    const times = [];

    // Создаем временные интервалы с 8:00 до 20:00 с шагом 30 минут
    for (let hour = 8; hour <= 20; hour++) {
        for (let minute = 0; minute < 60; minute += 30) {
            const timeString = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
            times.push(timeString);
        }
    }

    // Очищаем и заполняем select
    timeSelect.innerHTML = '<option value="">Выберите время</option>';
    times.forEach(time => {
        const option = document.createElement('option');
        option.value = time;
        option.textContent = time;
        timeSelect.appendChild(option);
    });
}

// Открытие модального окна
function openDateTimeModal(registration_number) {
    const modal = document.getElementById('dateTimeModal');
    modal.setAttribute('data-reg-id', registration_number);
    modal.style.display = 'block';

    // Сброс выбора
    document.getElementById('dateInput').value = '';
    document.getElementById('timeSelect').value = '';
    document.getElementById('selectedDisplay').textContent = '—';
    document.getElementById('confirmDateTime').disabled = true;

    selectedDateTime = null;
}

// Закрытие модального окна
function closeDateTimeModal() {
    const modal = document.getElementById('dateTimeModal');
    modal.style.display = 'none';
}

// Обновление выбора даты и времени
function updateDateTimeSelection() {
    const dateInput = document.getElementById('dateInput');
    const timeSelect = document.getElementById('timeSelect');
    const selectedDisplay = document.getElementById('selectedDisplay');
    const confirmBtn = document.getElementById('confirmDateTime');

    const date = dateInput.value;
    const time = timeSelect.value;

    if (date && time) {
        selectedDateTime = `${date}T${time}:00`;
        selectedDisplay.textContent = `${formatDisplayDate(date)} в ${time}`;
        confirmBtn.disabled = false;
    } else {
        selectedDateTime = null;
        selectedDisplay.textContent = '—';
        confirmBtn.disabled = true;
    }
}

// Форматирование даты для отображения
function formatDisplayDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });
}

// Подтверждение выбора и отправка на сервер
async function confirmDateTimeSelection() {
    if (!selectedDateTime) {
        showNotification('Пожалуйста, выберите дату и время', 'warning');
        return;
    }

    const modal = document.getElementById('dateTimeModal');
    const registration_number = modal.dataset.regId;

    try {
        // Отправка данных на сервер
        const response = await sendDateTimeToServer(selectedDateTime, registration_number);

        if (response.status === 'success') {
            showNotification('Дата и время успешно сохранены', 'success');
            closeDateTimeModal();

            // Обновляем скрытые поля
            document.getElementById('selectedDate').value = selectedDateTime.split('T')[0];
            document.getElementById('selectedTime').value = selectedDateTime.split('T')[1];

            document.location.reload();
        } else {
            throw new Error(response.message || 'Ошибка сервера');
        }

    } catch (error) {
        console.error('Ошибка при отправке даты и времени:', error);
        showNotification('Ошибка при сохранении даты и времени', 'error');
    }
}

// Функция отправки на сервер
async function sendDateTimeToServer(dateTime, registration_number) {
    const response = await fetch(`${API_BASE_URL}/deadline/${registration_number}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            scheduled_datetime: dateTime
        })
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
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


