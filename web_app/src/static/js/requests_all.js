const API_BASE_URL = 'http://localhost:8000/api/v1/request/view';

async function loadViewInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/info?departament=true`);
        const data = await response.json();
        const request_type_data = data.request_type;
		const status_data = data.status;
        const departament_data = data.departament;

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

        const select_departament_filter = document.getElementById('departamentFilter');
        departament_data.forEach(departament => {
            const option = document.createElement('option');
            option.value = departament.id
            option.textContent = departament.name;
            select_departament_filter.appendChild(option);
        });

    } catch (error) {
        console.error('Ошибка загрузки информации:', error);
        showNotification('Ошибка загрузки информации', 'error');
    }
}

// Загрузка списка заявок
async function loadRequests() {
    try {
        const departamentFilter = document.getElementById('departamentFilter').value;
        const statusFilter = document.getElementById('statusFilter').value;
        const typeFilter = document.getElementById('typeFilter').value;

        const response = await fetch(`
            ${API_BASE_URL}/list/all/?departament=${departamentFilter}&status=${statusFilter}&request_type=${typeFilter}
        `);
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
                    ${rights.view ? `
                        <a class="btn-view-details" href="/request/${request.registration_number}">
                            <i class="fas fa-eye"></i> Просмотр
                        </a>` : ''}
                    ${rights.approve ? `
                        <a class="btn-approve" href="/request/${request.registration_number}">
                            <i class="fa-solid fa-thumbs-up"></i> Утвердить
                        </a>` : ''}
                    ${rights.redirect ? `
                        <a class="btn-redirect" href="/request/${request.registration_number}">
                            <i class="fa-solid fa-calendar-check"></i> Перенаправить
                        </a> ` : ''}
                    ${rights.deadline ? `
                        <a class="btn-deadline" href="/request/${request.registration_number}">
                            <i class="fa-solid fa-alarm-clock"></i> Назначить сроки
                        </a> ` : ''}
                    ${rights.reject ? `
                        <a class="btn-reject" href="/request/${request.registration_number}">
                            <i class="fa-solid fa-xmark"></i> Отклонить
                        </a> ` : ''}
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Экспорт в Excel
async function exportToExcel() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/export/excel`);
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
});